import paramiko
import asyncio
import json
import socket
import shlex
import re
from typing import Optional, Dict, List, Any, Tuple
from io import StringIO


class SSHService:
    """
    跨平台 SSH 执行服务

    关键设计：
    1. 连接后探测远端系统指纹（OS、iostat 版本、top 类型、fio 版本等），缓存到实例上
    2. 所有命令按指纹分流，选择合适参数
    3. execute_command 正确阻塞到命令结束并读完全部输出（修复原先 recv 只读一次的 bug）
    4. 所有 paramiko 同步调用放到 executor 中，不阻塞事件循环
    """

    # 已知 iostat 列模板（sysstat 版本差异）
    # sysstat < 11 (CentOS 6):   Device: tps kB_read/s kB_wrtn/s kB_read kB_wrtn
    # sysstat 11-12 (CentOS 7):  Device r/s w/s rkB/s wkB/s rrqm/s wrqm/s %rrqm %wrqm r_await w_await aqu-sz rareq-sz wareq-sz svctm %util
    # sysstat >= 12.5 (新版):    Device r/s w/s rkB/s wkB/s (+discard列) ... %util

    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.connected = False

        # 远端系统指纹（connect 成功后探测填充）
        self.os_family: str = "unknown"     # linux / bsd / darwin / unknown
        self.distro: str = "unknown"        # centos / ubuntu / alpine / freebsd / macos
        self.is_busybox: bool = False       # Alpine 等精简系统用 BusyBox 而非 procps
        self.has_iostat: bool = False
        self.iostat_version: Tuple[int, int] = (0, 0)
        self.iostat_columns: List[str] = []  # 探测到的 iostat -x 实际列名
        self.has_fio: bool = False
        self.fio_version: Tuple[int, int] = (0, 0)
        self.has_lsblk_json: bool = False
        self.has_libaio: bool = False

    # ---------------------------------------------------------------- 连接 ----

    async def test_connection(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        timeout: int = 10,
    ) -> bool:
        """测试 SSH 连接"""
        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            loop = asyncio.get_event_loop()

            if private_key:
                pkey = paramiko.RSAKey.from_private_key(StringIO(private_key))
                await loop.run_in_executor(
                    None,
                    lambda: client.connect(host, port, username, pkey=pkey, timeout=timeout),
                )
            else:
                await loop.run_in_executor(
                    None,
                    lambda: client.connect(
                        host, port, username, password=password, timeout=timeout
                    ),
                )

            stdin, stdout, stderr = await loop.run_in_executor(
                None, client.exec_command, "echo connection_ok"
            )
            result = (await loop.run_in_executor(None, stdout.read)).decode().strip()
            return result == "connection_ok"
        except Exception as e:
            print(f"[SSH] test_connection failed: {e}")
            return False
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    async def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
    ) -> bool:
        """建立 SSH 连接并探测远端系统"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # TCP_KEEPIDLE 仅 Linux 支持，用 getattr 防 macOS 后端崩
            if hasattr(socket, "TCP_KEEPIDLE"):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            if hasattr(socket, "TCP_KEEPINTVL"):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            if hasattr(socket, "TCP_KEEPCNT"):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            sock.connect((host, port))

            loop = asyncio.get_event_loop()

            if private_key:
                pkey = paramiko.RSAKey.from_private_key(StringIO(private_key))
                await loop.run_in_executor(
                    None,
                    lambda: self.client.connect(
                        host, port, username, pkey=pkey, sock=sock, timeout=15
                    ),
                )
            else:
                await loop.run_in_executor(
                    None,
                    lambda: self.client.connect(
                        host, port, username, password=password, sock=sock, timeout=15
                    ),
                )

            # 启用 transport 级 keepalive
            transport = self.client.get_transport()
            if transport:
                transport.set_keepalive(30)

            self.connected = True

            # 连接成功后立刻探测远端系统
            await self._probe_system()
            return True

        except Exception as e:
            print(f"[SSH] connect failed: {e}")
            self.connected = False
            if self.client:
                try:
                    self.client.close()
                except Exception:
                    pass
                self.client = None
            return False

    def close(self):
        """关闭连接"""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.client = None
        self.connected = False

    # ---------------------------------------------------------- 命令执行核心 ----

    async def execute_command(
        self, command: str, timeout: int = 3600
    ) -> Dict[str, Any]:
        """
        执行远程命令，阻塞到命令完全结束，读取完整 stdout / stderr
        所有 paramiko 同步调用放到 executor，不阻塞事件循环
        """
        if not self.connected or not self.client:
            return {"error": "Not connected", "success": False, "stdout": "", "stderr": ""}

        loop = asyncio.get_event_loop()

        def _run_sync() -> Dict[str, Any]:
            channel = None
            try:
                transport = self.client.get_transport()
                if transport is None or not transport.is_active():
                    return {"error": "Transport inactive", "success": False,
                            "stdout": "", "stderr": ""}

                channel = transport.open_session()
                channel.settimeout(timeout)
                # 合并 stderr 到 stdout 会让 FIO JSON 被污染，这里**必须分离**
                channel.set_combine_stderr(False)
                channel.exec_command(command)

                stdout_chunks: List[bytes] = []
                stderr_chunks: List[bytes] = []

                # 读取直到命令结束 + 两边管道都 EOF
                # 关键：不能只调用一次 recv，必须循环
                while True:
                    got_data = False
                    if channel.recv_ready():
                        data = channel.recv(65536)
                        if data:
                            stdout_chunks.append(data)
                            got_data = True
                    if channel.recv_stderr_ready():
                        data = channel.recv_stderr(65536)
                        if data:
                            stderr_chunks.append(data)
                            got_data = True

                    if channel.exit_status_ready():
                        # 命令结束后再把管道里残留的数据排干
                        while channel.recv_ready():
                            data = channel.recv(65536)
                            if not data:
                                break
                            stdout_chunks.append(data)
                        while channel.recv_stderr_ready():
                            data = channel.recv_stderr(65536)
                            if not data:
                                break
                            stderr_chunks.append(data)
                        break

                    if not got_data:
                        # 没数据就让出 CPU，避免忙等
                        # 不能太长否则响应变慢
                        import time as _t
                        _t.sleep(0.05)

                exit_status = channel.recv_exit_status()
                stdout_data = b"".join(stdout_chunks).decode("utf-8", errors="replace")
                stderr_data = b"".join(stderr_chunks).decode("utf-8", errors="replace")

                return {
                    "stdout": stdout_data,
                    "stderr": stderr_data,
                    "exit_status": exit_status,
                    "success": exit_status == 0,
                }
            except socket.timeout:
                return {"error": "Command execution timeout", "success": False,
                        "stdout": "", "stderr": ""}
            except Exception as e:
                return {"error": str(e), "success": False,
                        "stdout": "", "stderr": ""}
            finally:
                if channel is not None:
                    try:
                        channel.close()
                    except Exception:
                        pass

        return await loop.run_in_executor(None, _run_sync)

    # ------------------------------------------------------------- 系统探测 ----

    async def _probe_system(self) -> None:
        """探测远端系统特性，结果缓存到 self"""
        # 1) 操作系统
        r = await self.execute_command("uname -s", timeout=10)
        uname_s = r.get("stdout", "").strip().lower() if r.get("success") else ""

        if "linux" in uname_s:
            self.os_family = "linux"
        elif "darwin" in uname_s:
            self.os_family = "darwin"
            self.distro = "macos"
        elif "bsd" in uname_s:
            self.os_family = "bsd"
            self.distro = "freebsd"
        else:
            self.os_family = "unknown"

        # 2) Linux 发行版
        if self.os_family == "linux":
            r = await self.execute_command(
                ". /etc/os-release 2>/dev/null && echo \"$ID\" || echo unknown",
                timeout=10,
            )
            self.distro = (r.get("stdout", "").strip() or "unknown").lower()

            # BusyBox 检测（Alpine 等）
            r = await self.execute_command("readlink -f $(command -v sh) 2>/dev/null || true", timeout=10)
            shell_path = r.get("stdout", "").strip()
            if "busybox" in shell_path.lower():
                self.is_busybox = True
            else:
                # 再通过 ls -l 兜底
                r2 = await self.execute_command(
                    "ls -l /bin/ls 2>/dev/null | grep -i busybox || true", timeout=10
                )
                if r2.get("stdout", "").strip():
                    self.is_busybox = True

        # 3) iostat（来自 sysstat 包）
        r = await self.execute_command(self._which_cmd("iostat"), timeout=10)
        iostat_path = r.get("stdout", "").strip()
        if iostat_path and "not found" not in iostat_path.lower():
            self.has_iostat = True

            # 探测 iostat 版本
            r = await self.execute_command("iostat -V 2>&1 | head -1", timeout=10)
            ver_line = r.get("stdout", "")
            m = re.search(r"(\d+)\.(\d+)", ver_line)
            if m:
                self.iostat_version = (int(m.group(1)), int(m.group(2)))

            # 探测 iostat -x 的实际列名（关键！不再硬编码列索引）
            probe_cmd = "LC_ALL=C iostat -x 1 1 2>/dev/null | awk 'NF && $1==\"Device\" || $1==\"Device:\"'"
            r = await self.execute_command(probe_cmd, timeout=15)
            header = r.get("stdout", "").strip().split("\n")
            if header:
                # 取最后一行（iostat 可能输出多段）
                cols = header[-1].split()
                # 去掉首列的 "Device" 或 "Device:"
                if cols and cols[0].rstrip(":") == "Device":
                    self.iostat_columns = [c.strip() for c in cols]

        # 4) fio
        r = await self.execute_command(self._which_cmd("fio"), timeout=10)
        fio_path = r.get("stdout", "").strip()
        if fio_path and "not found" not in fio_path.lower():
            self.has_fio = True
            r = await self.execute_command("fio --version 2>&1 | head -1", timeout=10)
            ver = r.get("stdout", "")
            m = re.search(r"fio-?(\d+)\.(\d+)", ver)
            if m:
                self.fio_version = (int(m.group(1)), int(m.group(2)))

            # 检测 libaio 是否可用（FIO 的可用 io engine 列表）
            r = await self.execute_command("fio --enghelp 2>&1", timeout=10)
            engines = r.get("stdout", "")
            if "libaio" in engines.lower():
                self.has_libaio = True

        # 5) lsblk JSON 支持（util-linux >= 2.27）
        if self.os_family == "linux":
            r = await self.execute_command("lsblk --help 2>&1 | grep -q -- ' -J' && echo yes || echo no", timeout=10)
            self.has_lsblk_json = r.get("stdout", "").strip() == "yes"

    def _which_cmd(self, binary: str) -> str:
        """
        跨平台的 which 命令
        command -v 是 POSIX 标准，在 bash/dash/ash/zsh/ksh 中都支持
        相比 which 更可靠
        """
        # 用 shlex.quote 防注入
        binary = shlex.quote(binary)
        return f"command -v {binary} 2>/dev/null || echo 'NOT_FOUND'"

    def get_system_fingerprint(self) -> Dict[str, Any]:
        """返回探测到的系统指纹（用于日志和调试）"""
        return {
            "os_family": self.os_family,
            "distro": self.distro,
            "is_busybox": self.is_busybox,
            "has_iostat": self.has_iostat,
            "iostat_version": f"{self.iostat_version[0]}.{self.iostat_version[1]}",
            "iostat_columns": self.iostat_columns,
            "has_fio": self.has_fio,
            "fio_version": f"{self.fio_version[0]}.{self.fio_version[1]}",
            "has_lsblk_json": self.has_lsblk_json,
            "has_libaio": self.has_libaio,
        }

    # --------------------------------------------------------------- 工具函数 ----

    def best_fio_ioengine(self, requested: Optional[str] = None) -> str:
        """
        根据远端系统选择合适的 io engine
        优先级：用户指定 > libaio(Linux) > posixaio(BSD) > psync(通用兜底)
        """
        if requested:
            # 用户指定了但远端可能不支持
            if requested == "libaio" and not self.has_libaio:
                return "psync"
            return requested

        if self.os_family == "linux" and self.has_libaio:
            return "libaio"
        if self.os_family in ("bsd", "darwin"):
            return "posixaio"
        return "psync"

    # ----------------------------------------------------------- 系统信息查询 ----

    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息（跨平台）"""
        info: Dict[str, Any] = {"fingerprint": self.get_system_fingerprint()}

        r = await self.execute_command("uname -a")
        if r.get("success"):
            info["os_info"] = r["stdout"].strip()

        if self.os_family == "linux":
            r = await self.execute_command(
                "lscpu 2>/dev/null | grep 'Model name' || grep 'model name' /proc/cpuinfo | head -1"
            )
            if r.get("success"):
                info["cpu_info"] = r["stdout"].strip()
            r = await self.execute_command("free -h 2>/dev/null | grep -i '^mem' || true")
            if r.get("success"):
                info["memory_info"] = r["stdout"].strip()
        elif self.os_family == "darwin":
            r = await self.execute_command("sysctl -n machdep.cpu.brand_string")
            if r.get("success"):
                info["cpu_info"] = r["stdout"].strip()
            r = await self.execute_command("vm_stat | head -5")
            if r.get("success"):
                info["memory_info"] = r["stdout"].strip()
        elif self.os_family == "bsd":
            r = await self.execute_command("sysctl -n hw.model")
            if r.get("success"):
                info["cpu_info"] = r["stdout"].strip()

        return info

    async def get_disk_partitions(self) -> List[Dict[str, Any]]:
        """获取磁盘分区（跨平台）"""
        partitions: List[Dict[str, Any]] = []

        # Linux 首选 lsblk -J
        if self.os_family == "linux" and self.has_lsblk_json:
            result = await self.execute_command(
                "lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT,TYPE -J -b"
            )
            if result.get("success"):
                try:
                    data = json.loads(result["stdout"])
                    partitions = self._parse_lsblk_tree(data.get("blockdevices", []))
                except json.JSONDecodeError:
                    pass

        # 兜底：df，兼容 Linux / macOS / BSD
        if not partitions:
            if self.os_family == "darwin":
                df_cmd = "df -k | awk 'NR>1 && $1 ~ /^\\/dev/'"
                block_size = 1024
            elif self.os_family == "bsd":
                df_cmd = "df -k | awk 'NR>1 && $1 ~ /^\\/dev/'"
                block_size = 1024
            else:
                df_cmd = "df -B1 2>/dev/null | awk 'NR>1 && $1 ~ /^\\/dev/' || df -k | awk 'NR>1 && $1 ~ /^\\/dev/'"
                block_size = 1  # -B1 已是字节

            r = await self.execute_command(df_cmd)
            if r.get("success"):
                for line in r["stdout"].strip().split("\n"):
                    parts = line.split()
                    if len(parts) < 6:
                        continue
                    try:
                        total = int(parts[1]) * block_size // (1024 * 1024)
                        avail = int(parts[3]) * block_size // (1024 * 1024)
                        mountpoint = parts[-1]  # 挂载点在最后，路径含空格时不会拆
                        partitions.append(
                            {
                                "device": parts[0],
                                "fstype": "",
                                "mountpoint": mountpoint,
                                "total_size_mb": total,
                                "available_size_mb": avail,
                                "used_percentage": (
                                    round(((total - avail) / total) * 100, 2) if total > 0 else 0
                                ),
                            }
                        )
                    except (ValueError, IndexError):
                        continue

        return partitions

    def _parse_lsblk_tree(self, blockdevices: List[Dict]) -> List[Dict[str, Any]]:
        """递归解析 lsblk JSON 树，兼容 LVM / 嵌套分区"""
        result = []

        def _walk(node: Dict):
            # -b 模式下 size 是字节数
            mp = node.get("mountpoint") or node.get("mountpoints", [None])[0]
            if mp:
                size_bytes = node.get("size")
                try:
                    size_bytes = int(size_bytes) if size_bytes is not None else 0
                except (ValueError, TypeError):
                    size_bytes = 0
                result.append(
                    {
                        "device": f"/dev/{node.get('name', '')}",
                        "fstype": node.get("fstype") or "",
                        "mountpoint": mp,
                        "total_size_mb": size_bytes // (1024 * 1024),
                        "available_size_mb": 0,  # lsblk 不给可用空间，稍后可再调 df 补
                        "used_percentage": 0,
                    }
                )
            for child in node.get("children", []) or []:
                _walk(child)

        for dev in blockdevices:
            _walk(dev)
        return result

    # --------------------------------------------------------------- iostat ----

    # 设备名前缀白名单（跨虚拟化 / 容器 / RAID / NVMe / SD 卡）
    _DEVICE_PREFIXES = (
        "sd", "hd", "nvme",      # 物理磁盘
        "vd", "xvd",             # 虚拟化（KVM / Xen）
        "md",                    # 软 RAID
        "dm-",                   # LVM / dmcrypt
        "mmcblk",                # SD / eMMC
        "loop",                  # 容器 / squashfs
        "rbd",                   # Ceph
        "dasd",                  # IBM Z
    )

    @classmethod
    def is_block_device(cls, name: str) -> bool:
        return name.startswith(cls._DEVICE_PREFIXES)

    async def get_partition_iostat(
        self, device: str, interval: int = 1
    ) -> Dict[str, Any]:
        """
        获取指定设备的 iostat 数据
        关键：
        - 用 `-y` 跳过首次累计值，拿到真实瞬时采样
        - 按探测到的实际列名取数，不再硬编码索引
        - macOS/BSD 降级到 iostat 不同语法
        """
        if not self.has_iostat:
            return self._iostat_fallback(device)

        # Linux sysstat
        if self.os_family == "linux":
            # -y 跳过第一次（累计自启动），-x 扩展统计，采 2 次取最后一次
            # LC_ALL=C 防本地化列名
            # 部分老 sysstat 不支持 -y，用两次采样 + 取最后一次兜底
            supports_y = self.iostat_version >= (10, 0)
            if supports_y:
                cmd = f"LC_ALL=C iostat -x -y -d {shlex.quote(device)} {interval} 1 2>/dev/null"
            else:
                cmd = f"LC_ALL=C iostat -x -d {shlex.quote(device)} {interval} 2 2>/dev/null"

            result = await self.execute_command(cmd, timeout=interval + 30)

            if not result.get("success") or not result.get("stdout", "").strip():
                # 个别系统 -d <device> 不生效，回退到全量采集后过滤
                cmd2 = f"LC_ALL=C iostat -x {'--human' if False else ''} {interval} {2 if not supports_y else 1} 2>/dev/null"
                cmd2 = f"LC_ALL=C iostat -x {interval} {2 if not supports_y else 1} 2>/dev/null"
                result = await self.execute_command(cmd2, timeout=interval + 30)

            if not result.get("success"):
                return self._iostat_fallback(device)

            return self._parse_iostat_by_header(result["stdout"], device)

        # macOS: iostat 不支持 -x，列完全不同
        if self.os_family == "darwin":
            # iostat -d -I disk0 interval count
            short = device.split("/")[-1]  # disk0
            cmd = f"iostat -d -I {shlex.quote(short)} {interval} 2"
            result = await self.execute_command(cmd, timeout=interval + 30)
            if result.get("success"):
                return self._parse_macos_iostat(result["stdout"], device)

        # FreeBSD
        if self.os_family == "bsd":
            cmd = f"iostat -x -d {interval} 2"
            result = await self.execute_command(cmd, timeout=interval + 30)
            if result.get("success"):
                return self._parse_bsd_iostat(result["stdout"], device)

        return self._iostat_fallback(device)

    def _parse_iostat_by_header(self, output: str, target_device: str) -> Dict[str, Any]:
        """
        按列名索引解析 Linux iostat -x 输出（不再硬编码下标）
        支持 sysstat 11 / 12 / 13 各版本差异
        """
        lines = [ln for ln in output.strip().split("\n") if ln.strip()]
        header_cols: List[str] = []
        target_short = target_device.split("/")[-1]

        data_rows: List[List[str]] = []
        for line in lines:
            parts = line.split()
            if not parts:
                continue
            if parts[0].rstrip(":") == "Device":
                header_cols = [c.rstrip(":") for c in parts]
                continue
            if not header_cols:
                continue
            if parts[0] == target_short or parts[0] == target_device:
                data_rows.append(parts)

        if not header_cols or not data_rows:
            return {"success": False, "error": f"Device {target_device} not found in iostat", "device": target_device}

        # 多次采样取最后一次（真实时值）
        row = data_rows[-1]
        col_idx = {name: i for i, name in enumerate(header_cols)}

        def get(*candidates: str, default: float = 0.0) -> float:
            """按候选列名列表取值，兼容不同 sysstat 版本字段重命名"""
            for name in candidates:
                if name in col_idx and col_idx[name] < len(row):
                    try:
                        return float(row[col_idx[name]])
                    except (ValueError, IndexError):
                        continue
            return default

        # 字段名兼容表
        # 新版: r/s w/s rkB/s wkB/s r_await w_await aqu-sz %util
        # 旧版: rrqm/s wrqm/s r/s w/s rsec/s wsec/s 或 rkB/s wkB/s avgqu-sz await %util
        r_s = get("r/s")
        w_s = get("w/s")
        rkB_s = get("rkB/s", "rsec/s")  # rsec/s 单位是扇区(512B)，下面要换算
        wkB_s = get("wkB/s", "wsec/s")

        # 如果是 sec/s，需要 / 2 得到 kB/s（1 sector = 512B）
        if "rkB/s" not in col_idx and "rsec/s" in col_idx:
            rkB_s = rkB_s / 2
        if "wkB/s" not in col_idx and "wsec/s" in col_idx:
            wkB_s = wkB_s / 2

        r_await = get("r_await", "await")
        w_await = get("w_await", "await")
        await_ms = (r_await + w_await) / 2 if (r_await or w_await) else get("await")
        aqu_sz = get("aqu-sz", "avgqu-sz")
        util = get("%util")

        return {
            "success": True,
            "device": target_device,
            "read_iops": r_s,
            "write_iops": w_s,
            "total_iops": r_s + w_s,
            "read_bw_mbs": rkB_s / 1024,
            "write_bw_mbs": wkB_s / 1024,
            "total_bw_mbs": (rkB_s + wkB_s) / 1024,
            "await_ms": await_ms,
            "aqu_sz": aqu_sz,
            "util_percent": util,
            "tps": r_s + w_s,
        }

    def _parse_macos_iostat(self, output: str, device: str) -> Dict[str, Any]:
        """解析 macOS iostat 输出（KB/t tps MB/s）"""
        lines = [ln for ln in output.strip().split("\n") if ln.strip()]
        # 取最后一行数字行
        for line in reversed(lines):
            parts = line.split()
            if len(parts) >= 3:
                try:
                    kb_per_t = float(parts[0])
                    tps = float(parts[1])
                    mb_s = float(parts[2])
                    return {
                        "success": True,
                        "device": device,
                        "read_iops": 0,  # macOS iostat 不分读写
                        "write_iops": 0,
                        "total_iops": tps,
                        "read_bw_mbs": 0,
                        "write_bw_mbs": 0,
                        "total_bw_mbs": mb_s,
                        "await_ms": 0,
                        "aqu_sz": 0,
                        "util_percent": 0,
                        "tps": tps,
                    }
                except ValueError:
                    continue
        return {"success": False, "error": "Failed to parse macOS iostat", "device": device}

    def _parse_bsd_iostat(self, output: str, device: str) -> Dict[str, Any]:
        """解析 FreeBSD iostat -x 输出"""
        # FreeBSD iostat -x: device r/s w/s kr/s kw/s qlen svc_t %b
        lines = [ln for ln in output.strip().split("\n") if ln.strip()]
        for line in reversed(lines):
            parts = line.split()
            if len(parts) >= 8 and (parts[0] == device or parts[0] == device.split("/")[-1]):
                try:
                    r_s = float(parts[1])
                    w_s = float(parts[2])
                    kr_s = float(parts[3])
                    kw_s = float(parts[4])
                    qlen = float(parts[5])
                    svc_t = float(parts[6])
                    busy = float(parts[7])
                    return {
                        "success": True,
                        "device": device,
                        "read_iops": r_s,
                        "write_iops": w_s,
                        "total_iops": r_s + w_s,
                        "read_bw_mbs": kr_s / 1024,
                        "write_bw_mbs": kw_s / 1024,
                        "total_bw_mbs": (kr_s + kw_s) / 1024,
                        "await_ms": svc_t,
                        "aqu_sz": qlen,
                        "util_percent": busy,
                        "tps": r_s + w_s,
                    }
                except ValueError:
                    continue
        return {"success": False, "error": "Failed to parse BSD iostat", "device": device}

    def _iostat_fallback(self, device: str) -> Dict[str, Any]:
        """iostat 不可用时返回空数据，调用方应记录告警"""
        return {
            "success": False,
            "error": "iostat unavailable on remote host",
            "device": device,
            "read_iops": 0, "write_iops": 0, "total_iops": 0,
            "read_bw_mbs": 0, "write_bw_mbs": 0, "total_bw_mbs": 0,
            "await_ms": 0, "aqu_sz": 0, "util_percent": 0, "tps": 0,
        }

    # ------------------------------------------------------------ CPU/内存 ----

    async def get_cpu_mem_usage(self) -> Dict[str, float]:
        """
        跨平台采集 CPU / 内存使用率
        返回 {"cpu_usage": %, "memory_usage": %}
        """
        cpu = 0.0
        mem = 0.0

        if self.os_family == "linux":
            # CPU：用 /proc/stat 采样差分算，对所有发行版（含 BusyBox）都管用
            cpu = await self._linux_cpu_from_proc()
            # 内存：优先 /proc/meminfo（最可靠），BusyBox/procps 都能读
            mem = await self._linux_mem_from_proc()

        elif self.os_family == "darwin":
            # macOS
            r = await self.execute_command(
                "top -l 1 -n 0 | awk '/CPU usage/ {gsub(\"%\",\"\"); print 100-$(NF-1)}'",
                timeout=15,
            )
            if r.get("success"):
                try:
                    cpu = float(r["stdout"].strip())
                except ValueError:
                    cpu = 0.0
            # macOS 内存：vm_stat
            r = await self.execute_command(
                "vm_stat | awk '"
                "/page size of/ {ps=$(NF-1)} "
                "/Pages free/ {free=$NF} "
                "/Pages active/ {act=$NF} "
                "/Pages inactive/ {inact=$NF} "
                "/Pages wired/ {wired=$NF} "
                "END {gsub(/\\./,\"\",free); gsub(/\\./,\"\",act); gsub(/\\./,\"\",inact); gsub(/\\./,\"\",wired); "
                "total=(free+act+inact+wired); used=(act+wired); if(total>0) print used/total*100}'",
                timeout=15,
            )
            if r.get("success"):
                try:
                    mem = float(r["stdout"].strip())
                except ValueError:
                    mem = 0.0

        elif self.os_family == "bsd":
            r = await self.execute_command(
                "top -b -d 1 | awk '/CPU:/ {gsub(\"%\",\"\"); print 100-$(NF-1); exit}'",
                timeout=15,
            )
            if r.get("success"):
                try:
                    cpu = float(r["stdout"].strip())
                except ValueError:
                    cpu = 0.0
            r = await self.execute_command(
                "top -b -d 1 | awk '/Mem:/ {print $0; exit}'", timeout=15
            )
            # BSD top 格式：Mem: xxM Active, yyM Inact, ...   不同版本差异大，先置 0
            mem = 0.0

        return {"cpu_usage": max(0.0, min(100.0, cpu)),
                "memory_usage": max(0.0, min(100.0, mem))}

    async def _linux_cpu_from_proc(self) -> float:
        """
        用 /proc/stat 两次采样差分计算 CPU 利用率
        对 procps / BusyBox / 各发行版都稳定可靠
        比解析 top 输出强得多
        """
        cmd = (
            "awk '/^cpu / {print $2\" \"$3\" \"$4\" \"$5\" \"$6\" \"$7\" \"$8}' /proc/stat; "
            "sleep 1; "
            "awk '/^cpu / {print $2\" \"$3\" \"$4\" \"$5\" \"$6\" \"$7\" \"$8}' /proc/stat"
        )
        r = await self.execute_command(cmd, timeout=15)
        if not r.get("success"):
            return 0.0
        lines = r["stdout"].strip().split("\n")
        if len(lines) < 2:
            return 0.0
        try:
            a = list(map(int, lines[0].split()))
            b = list(map(int, lines[1].split()))
            total_a = sum(a)
            total_b = sum(b)
            idle_a = a[3]  # idle
            idle_b = b[3]
            dt = total_b - total_a
            di = idle_b - idle_a
            if dt <= 0:
                return 0.0
            return (1 - di / dt) * 100
        except (ValueError, IndexError):
            return 0.0

    async def _linux_mem_from_proc(self) -> float:
        """从 /proc/meminfo 读内存用量，对所有 Linux 稳定"""
        cmd = "awk '/^MemTotal:/ {t=$2} /^MemAvailable:/ {a=$2} END {if(t>0) print (t-a)/t*100; else print 0}' /proc/meminfo"
        r = await self.execute_command(cmd, timeout=10)
        if not r.get("success"):
            return 0.0
        try:
            return float(r["stdout"].strip())
        except ValueError:
            return 0.0

    # ------------------------------------------------------- 设备名查询工具 ----

    async def get_device_by_mountpoint(self, mountpoint: str) -> Optional[str]:
        """通过挂载点反查设备名（跨平台）"""
        safe_mp = shlex.quote(mountpoint)
        # 注意：awk '{print $1}' 的花括号要双层 {{ }} 才能在 f-string 中正确转义
        if self.os_family == "linux":
            r = await self.execute_command(
                f"df {safe_mp} 2>/dev/null | tail -1 | awk '{{print $1}}'"
            )
        else:
            r = await self.execute_command(
                f"df {safe_mp} | tail -1 | awk '{{print $1}}'"
            )
        if not r.get("success"):
            return None
        device = r.get("stdout", "").strip()
        if device.startswith("/dev/"):
            return device[5:]
        return device or None
