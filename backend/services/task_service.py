import asyncio
import json
import os
import shlex
import posixpath
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.task import Task, TaskNode, IOPerformanceData, IOStatData, TaskLog
from models.task_node_partition import TaskNodePartition
from services.ssh_service import SSHService
from services.init_write_service import InitWriteService
from services.histogram_aggregator import HistogramAggregator
from services.baseline_comparator import BaselineComparator


class TaskService:
    """
    任务执行服务（已修复跨平台问题）

    关键修改：
    1. 不依赖注入的 db 会话（避免后台任务跑时 session 已关闭）
       —— 每个任务内部自己 new/close SessionLocal
    2. FIO 执行前先探测远端系统，选择合适的 ioengine
    3. FIO JSON 输出写到远端文件（避免 stderr 污染）
    4. iostat 解析改为按列名索引，iostat -y 跳过累计值
    5. CPU/内存采集走 /proc 差分，不再解析 top 文本
    6. 设备名白名单扩充（vd* / xvd* / dm-* 等）
    """

    def __init__(self, socket_manager):
        # 不再注入 db；后台任务自行创建
        self.socket_manager = socket_manager
        self.active_tasks = {}

    # ---------------------------------------------------------- 任务入口 ----

    async def execute_task(self, task_id: int):
        """
        后台执行 IO 测试任务
        注意：被 BackgroundTasks 调用时原请求的 db session 已关闭，
        这里必须自己建 session
        """
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                print(f"[Task {task_id}] task not found")
                return

            test_case = task.test_case
            if not test_case:
                await self._log_error(db, task_id, "测试用例不存在")
                await self._update_task_status(db, task_id, "failed")
                return

            task_nodes = db.query(TaskNode).filter(TaskNode.task_id == task_id).all()
            if not task_nodes:
                await self._log_error(db, task_id, "任务没有配置节点")
                await self._update_task_status(db, task_id, "failed")
                return

            self.active_tasks[task_id] = {
                "start_time": datetime.utcnow(),
                "should_stop": False,
            }

            await self._log_info(db, task_id, f"开始执行任务: {task.task_name}")
            await self._log_info(db, task_id, f"使用测试用例: {test_case.case_name}")
            await self._log_info(db, task_id, f"目标节点数: {len(task_nodes)}")

            # =============================================
            # 阶段 1: 初始化写入
            # =============================================
            init_service = InitWriteService(self.socket_manager)
            await self._log_info(db, task_id, "开始初始化写入阶段...")
            init_results = await init_service.execute_init_write(task_id)

            failed_init_count = sum(1 for v in init_results.values() if not v)
            if failed_init_count > 0:
                await self._log_warning(
                    db, task_id,
                    f"初始化写入完成: {len(init_results) - failed_init_count} 成功, {failed_init_count} 失败"
                )
            else:
                await self._log_info(db, task_id, f"初始化写入完成: {len(init_results)} 个分区全部成功")

            # =============================================
            # 阶段 2: FIO 测试执行
            # =============================================

            # 每个节点一个独立协程，各自管理自己的 db session
            coros = [
                self._execute_node_task(task_id, tn.id) for tn in task_nodes
            ]
            await asyncio.gather(*coros, return_exceptions=True)

            await self._finalize_task(db, task_id)

        except Exception as e:
            try:
                await self._log_error(db, task_id, f"任务执行失败: {e!s}")
                await self._update_task_status(db, task_id, "failed")
            except Exception:
                pass
        finally:
            self.active_tasks.pop(task_id, None)
            db.close()

    # --------------------------------------------------------- 单节点执行 ----

    async def _execute_node_task(self, task_id: int, task_node_id: int):
        """在单个节点上执行测试（自建 session）"""
        db = SessionLocal()
        ssh_service: Optional[SSHService] = None
        node_name = f"#{task_node_id}"
        try:
            task_node = db.query(TaskNode).filter(TaskNode.id == task_node_id).first()
            if not task_node:
                return
            node = task_node.node
            partition = task_node.partition
            test_case = task_node.task.test_case
            node_name = node.node_name

            await self._log_info(db, task_id, f"开始在节点 {node_name} 上执行测试")

            # 建立 SSH 并探测系统
            ssh_service = SSHService()
            ok = await ssh_service.connect(
                host=node.host,
                port=node.port,
                username=node.username,
                password=node.password,
                private_key=node.private_key,
            )
            if not ok:
                await self._log_error(db, task_id, f"节点 {node_name} SSH 连接失败")
                await self._update_task_node_status(db, task_node_id, "failed", "SSH连接失败")
                return

            fingerprint = ssh_service.get_system_fingerprint()
            await self._log_info(
                db, task_id,
                f"节点 {node_name} 系统指纹: "
                f"{fingerprint['os_family']}/{fingerprint['distro']}, "
                f"fio={fingerprint['fio_version']}, "
                f"iostat_ver={fingerprint['iostat_version']}, "
                f"libaio={'yes' if fingerprint['has_libaio'] else 'no'}"
            )

            if not fingerprint["has_fio"]:
                await self._log_error(
                    db, task_id,
                    f"节点 {node_name} 未安装 fio，请执行：\n"
                    f"  - Ubuntu/Debian: apt-get install -y fio\n"
                    f"  - CentOS/RHEL: yum install -y fio\n"
                    f"  - Alpine: apk add fio\n"
                    f"  - macOS: brew install fio",
                )
                await self._update_task_node_status(db, task_node_id, "failed", "fio 未安装")
                return

            # 获取可用的 ioengine
            chosen_engine = ssh_service.best_fio_ioengine(test_case.io_engine)
            if chosen_engine != test_case.io_engine:
                await self._log_warning(
                    db, task_id,
                    f"节点 {node_name} 不支持 io_engine={test_case.io_engine}，"
                    f"已自动切换为 {chosen_engine}"
                )

            # 检查挂载点、确保可写
            if not await self._ensure_writable_mount(
                db, task_id, ssh_service, partition.mount_point, node_name
            ):
                await self._update_task_node_status(
                    db, task_node_id, "failed", f"挂载点不可写: {partition.mount_point}"
                )
                return

            # 测试文件路径（用 posixpath 避免重复斜杠）
            test_filename = posixpath.normpath(
                posixpath.join(partition.mount_point, "diskbench_fio_test.dat")
            )
            # 远端 JSON 输出文件（避免 stderr 污染）
            output_json = f"/tmp/diskbench_{task_id}_{task_node_id}_{uuid.uuid4().hex[:8]}.json"

            fio_command = test_case.generate_fio_command(
                filename=test_filename,
                ioengine_override=chosen_engine,
                output_file=output_json,
            )

            # 启动监控
            monitor_task = asyncio.create_task(
                self._monitor_node_performance(task_id, task_node_id, ssh_service, partition)
            )

            try:
                await self._execute_fio_test(
                    db, task_id, task_node_id, ssh_service,
                    fio_command, output_json, test_filename, test_case.runtime
                )
                await self._update_task_node_status(db, task_node_id, "completed")
                await self._log_info(db, task_id, f"节点 {node_name} 测试完成")
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            await self._log_error(db, task_id, f"节点 {node_name} 测试失败: {e!s}")
            try:
                await self._update_task_node_status(db, task_node_id, "failed", str(e))
            except Exception:
                pass
        finally:
            if ssh_service:
                ssh_service.close()
            db.close()

    async def _ensure_writable_mount(
        self, db: Session, task_id: int, ssh_service: SSHService,
        mount_point: str, node_name: str
    ) -> bool:
        """确保挂载点存在且可写"""
        safe_mp = shlex.quote(mount_point)
        # 探测：存在 + 可写
        r = await ssh_service.execute_command(
            f"test -d {safe_mp} && test -w {safe_mp} && echo OK || echo NO",
            timeout=15,
        )
        if r.get("success") and r.get("stdout", "").strip() == "OK":
            return True

        # 尝试创建
        r = await ssh_service.execute_command(f"mkdir -p {safe_mp}", timeout=15)
        if not r.get("success"):
            await self._log_error(
                db, task_id,
                f"节点 {node_name} 无法创建挂载点 {mount_point}: {r.get('stderr', '')}"
            )
            return False
        r = await ssh_service.execute_command(
            f"test -w {safe_mp} && echo OK || echo NO", timeout=10
        )
        return r.get("success") and r.get("stdout", "").strip() == "OK"

    # ----------------------------------------------------------- FIO 执行 ----

    async def _execute_fio_test(
        self,
        db: Session,
        task_id: int,
        task_node_id: int,
        ssh_service: SSHService,
        fio_command: str,
        output_json: str,
        test_filename: str,
        runtime: int,
    ):
        """
        执行 FIO 测试
        关键修复：
        - 超时 = runtime + 60s 缓冲（原来固定 3600s）
        - fio JSON 输出写到远端文件，读文件而非 stdout（防 stderr 污染）
        - 测试结束后清理测试文件和 JSON 文件
        """
        await self._log_info(db, task_id, f"执行FIO命令: {fio_command}")

        # 超时 = runtime + ramp + 缓冲
        fio_timeout = max(60, (runtime or 60) + 60)

        result = await ssh_service.execute_command(fio_command, timeout=fio_timeout)

        if not result.get("success"):
            # 即使退出码非 0，也试着读一下 JSON 文件（fio 有时中途完成但退出码怪异）
            err = result.get("stderr") or result.get("error") or "unknown"
            await self._log_warning(db, task_id, f"FIO 命令退出异常: {err[:500]}")

        # 读取远端 JSON 文件
        cat_result = await ssh_service.execute_command(
            f"cat {shlex.quote(output_json)}", timeout=30
        )
        fio_json_text = cat_result.get("stdout", "").strip() if cat_result.get("success") else ""

        # 清理远端临时文件（JSON 输出 + 测试数据文件）
        try:
            await ssh_service.execute_command(
                f"rm -f {shlex.quote(output_json)} {shlex.quote(test_filename)}",
                timeout=30,
            )
        except Exception:
            pass

        if not fio_json_text:
            raise Exception(
                f"FIO 执行失败，没有产生有效输出。stderr: "
                f"{(result.get('stderr') or result.get('error', ''))[:500]}"
            )

        await self._parse_fio_results(db, task_id, task_node_id, fio_json_text)

    # ---------------------------------------------------------- FIO 解析 ----

    async def _parse_fio_results(
        self, db: Session, task_id: int, task_node_id: int, fio_output: str
    ):
        """
        解析 FIO JSON 输出
        关键修复：兼容 fio 2.x / 3.x 字段差异（lat vs lat_ns）
        """
        try:
            # fio 可能在 JSON 前打印 terse-output 或 debug 信息，找到第一个 { 开始解析
            brace_idx = fio_output.find("{")
            if brace_idx > 0:
                fio_output = fio_output[brace_idx:]

            data = json.loads(fio_output)
            jobs = data.get("jobs", [])
            if not jobs:
                raise ValueError("fio 输出中没有 jobs")

            # group_reporting=True 时 jobs[0] 是聚合结果
            # 否则需要汇总所有 jobs
            job = jobs[0] if len(jobs) == 1 else self._aggregate_jobs(jobs)

            read_stats = job.get("read", {}) or {}
            write_stats = job.get("write", {}) or {}

            total_iops = float(read_stats.get("iops", 0)) + float(write_stats.get("iops", 0))
            # fio bw 单位是 KB/s，转成 MB/s
            total_bw_mbs = (
                float(read_stats.get("bw", 0)) + float(write_stats.get("bw", 0))
            ) / 1024.0

            # 延迟：兼容 fio 2.x / 3.x
            read_lat_us = self._extract_latency_us(read_stats)
            write_lat_us = self._extract_latency_us(write_stats)

            # 非零方取均值
            nonzero = [x for x in (read_lat_us, write_lat_us) if x > 0]
            avg_lat_ms = (sum(nonzero) / len(nonzero) / 1000.0) if nonzero else 0.0

            task_node = db.query(TaskNode).filter(TaskNode.id == task_node_id).first()
            if not task_node:
                return

            task_node.iops = total_iops
            task_node.bandwidth = total_bw_mbs
            task_node.latency = avg_lat_ms
            task_node.io_ops = int(
                (read_stats.get("total_ios") or 0) + (write_stats.get("total_ios") or 0)
            )

            perf = IOPerformanceData(
                task_node_id=task_node_id,
                iops=total_iops,
                bandwidth=total_bw_mbs,
                latency=avg_lat_ms,
                read_iops=float(read_stats.get("iops", 0)),
                write_iops=float(write_stats.get("iops", 0)),
                read_bw=float(read_stats.get("bw", 0)) / 1024.0,
                write_bw=float(write_stats.get("bw", 0)) / 1024.0,
                read_lat=read_lat_us / 1000.0,
                write_lat=write_lat_us / 1000.0,
            )
            db.add(perf)
            db.commit()

            await self.socket_manager.broadcast_to_task(
                str(task_id),
                "performance_update",
                {
                    "task_node_id": task_node_id,
                    "node_name": task_node.node.node_name,
                    "iops": total_iops,
                    "bandwidth": total_bw_mbs,
                    "latency": avg_lat_ms,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            await self._log_warning(db, task_id, f"解析FIO结果失败: {e!s}")

    @staticmethod
    def _aggregate_jobs(jobs: list) -> dict:
        """没有 group_reporting 时合并多 job 统计"""
        agg = {"read": {"iops": 0, "bw": 0, "total_ios": 0},
               "write": {"iops": 0, "bw": 0, "total_ios": 0}}
        lat_accum = {"read": [], "write": []}
        for j in jobs:
            for k in ("read", "write"):
                s = j.get(k, {}) or {}
                agg[k]["iops"] += float(s.get("iops", 0))
                agg[k]["bw"] += float(s.get("bw", 0))
                agg[k]["total_ios"] += int(s.get("total_ios", 0))
                # 保留 lat_ns/lat 结构给 _extract_latency_us 处理
                if "lat_ns" in s:
                    lat_accum[k].append(("lat_ns", s["lat_ns"]))
                elif "lat" in s:
                    lat_accum[k].append(("lat", s["lat"]))
        # 把延迟结构拼回去（取平均）
        for k in ("read", "write"):
            if lat_accum[k]:
                means = []
                for kind, v in lat_accum[k]:
                    mean = float(v.get("mean", 0))
                    if kind == "lat_ns":
                        mean = mean / 1000.0  # ns -> us
                    means.append(mean)
                if means:
                    agg[k]["lat"] = {"mean": sum(means) / len(means)}  # 单位 us
        return agg

    @staticmethod
    def _extract_latency_us(stats: dict) -> float:
        """
        从 fio 读/写统计中提取平均延迟（微秒）
        fio 3.x: lat_ns (纳秒)
        fio 2.x / 老版: lat (微秒)
        clat_ns / clat 作为备选
        """
        if not stats:
            return 0.0
        # 优先 lat_ns (fio 3.x)
        if "lat_ns" in stats:
            return float(stats["lat_ns"].get("mean", 0)) / 1000.0
        if "clat_ns" in stats:
            return float(stats["clat_ns"].get("mean", 0)) / 1000.0
        # fio 2.x: lat / clat 单位 us
        if "lat" in stats:
            return float(stats["lat"].get("mean", 0))
        if "clat" in stats:
            return float(stats["clat"].get("mean", 0))
        return 0.0

    # -------------------------------------------------------- 性能监控采集 ----

    async def _monitor_node_performance(
        self, task_id: int, task_node_id: int,
        ssh_service: SSHService, partition
    ):
        """
        监控采集
        关键修复：
        - iostat 用 SSHService.get_partition_iostat，已按列名取数
        - CPU/内存用 /proc 差分，不再解析 top
        - 按设备名采集而不是全量扫描，减少干扰
        """
        db = SessionLocal()
        try:
            # 得到设备名
            device = await ssh_service.get_device_by_mountpoint(partition.mount_point)
            if not device:
                # 降级：用 partition.device 字段
                device = (partition.partition_name or "").lstrip("/").replace("dev/", "")

            while True:
                if (
                    task_id in self.active_tasks
                    and self.active_tasks[task_id]["should_stop"]
                ):
                    break

                # iostat（失败不中断）
                try:
                    iostat = await ssh_service.get_partition_iostat(device, interval=1)
                    if iostat.get("success"):
                        io = IOStatData(
                            task_node_id=task_node_id,
                            device=device,
                            tps=iostat.get("tps", 0),
                            kB_read_s=iostat.get("read_bw_mbs", 0) * 1024,
                            kB_wrtn_s=iostat.get("write_bw_mbs", 0) * 1024,
                            await_time=iostat.get("await_ms", 0),
                            aqu_sz=iostat.get("aqu_sz", 0),
                            util=iostat.get("util_percent", 0),
                        )
                        db.add(io)
                        db.commit()
                except Exception as e:
                    await self._log_warning(db, task_id, f"iostat 采集失败: {e!s}")

                # CPU/内存（失败不中断）
                try:
                    usage = await ssh_service.get_cpu_mem_usage()
                    # 新建独立的性能点记录，不再覆盖 fio 结果
                    perf = IOPerformanceData(
                        task_node_id=task_node_id,
                        iops=0, bandwidth=0, latency=0,
                        cpu_usage=usage["cpu_usage"],
                        memory_usage=usage["memory_usage"],
                    )
                    db.add(perf)
                    db.commit()
                except Exception as e:
                    await self._log_warning(db, task_id, f"CPU/内存采集失败: {e!s}")

                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
        finally:
            db.close()

    # ------------------------------------------------- 任务收尾 & 日志工具 ----

    async def _finalize_task(self, db: Session, task_id: int):
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        task_nodes = db.query(TaskNode).filter(TaskNode.task_id == task_id).all()

        total_iops = total_lat = total_bw = 0.0
        total_io_ops = 0
        completed = 0
        for tn in task_nodes:
            if tn.status == "completed":
                total_iops += float(tn.iops or 0)
                total_lat += float(tn.latency or 0)
                total_bw += float(tn.bandwidth or 0)
                total_io_ops += int(tn.io_ops or 0)
                completed += 1

        task.end_time = datetime.utcnow()
        task.duration = (
            int((task.end_time - task.start_time).total_seconds()) if task.start_time else 0
        )
        task.total_io_ops = total_io_ops
        if completed > 0:
            task.avg_iops = total_iops / completed
            task.avg_latency = total_lat / completed
            task.avg_bw = total_bw / completed

        failed = sum(1 for t in task_nodes if t.status == "failed")
        cancelled = sum(1 for t in task_nodes if t.status == "cancelled")
        if failed == len(task_nodes):
            task.status = "failed"
        elif cancelled > 0:
            task.status = "cancelled"
        else:
            task.status = "completed"

        db.commit()

        await self._log_info(
            db, task_id, f"任务 {task.task_name} 执行完成，状态: {task.status}"
        )
        await self.socket_manager.broadcast_to_task(
            str(task_id), "task_completed",
            {
                "task_id": task_id, "task_name": task.task_name,
                "status": task.status, "duration": task.duration,
                "avg_iops": float(task.avg_iops or 0),
                "avg_latency": float(task.avg_latency or 0),
                "avg_bw": float(task.avg_bw or 0),
                "end_time": task.end_time.isoformat(),
            },
        )

    async def _update_task_status(self, db: Session, task_id: int, status: str):
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            task.updated_at = datetime.utcnow()
            db.commit()

    async def _update_task_node_status(
        self, db: Session, task_node_id: int, status: str, err: str = None
    ):
        tn = db.query(TaskNode).filter(TaskNode.id == task_node_id).first()
        if not tn:
            return
        tn.status = status
        if err:
            tn.error_message = err
        if status == "completed":
            tn.end_time = datetime.utcnow()
            if tn.start_time:
                tn.duration = int((tn.end_time - tn.start_time).total_seconds())
        db.commit()

    async def _add_log(self, db: Session, task_id: int, level: str, message: str, source="system"):
        entry = TaskLog(task_id=task_id, log_level=level, message=message, source=source)
        db.add(entry)
        db.commit()
        try:
            await self.socket_manager.broadcast_to_task(
                str(task_id),
                "log_update",
                {
                    "level": level, "message": message,
                    "source": source, "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception:
            pass

    async def _log_info(self, db, task_id, msg):
        await self._add_log(db, task_id, "info", msg)

    async def _log_warning(self, db, task_id, msg):
        await self._add_log(db, task_id, "warning", msg)

    async def _log_error(self, db, task_id, msg):
        await self._add_log(db, task_id, "error", msg)

    def stop_task(self, task_id: int) -> bool:
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["should_stop"] = True
            return True
        return False
