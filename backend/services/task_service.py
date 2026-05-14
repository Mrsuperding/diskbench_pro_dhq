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
        self.socket_manager = socket_manager
        self.active_tasks = {}

    # ---------------------------------------------------------- 任务入口 ----
    async def execute_task(self, task_id: int):
        db = SessionLocal()
        print(f"[Task {task_id}] ========== 任务开始执行 ==========")
        try:
            print(f"[Task {task_id}] [STEP 0] 查询任务信息...")
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                print(f"[Task {task_id}] [STEP 0] 错误: 任务不存在")
                return

            print(f"[Task {task_id}] [STEP 0] 任务名称: {task.task_name}, 当前状态: {task.status}")

            test_case = task.test_case
            if not test_case:
                print(f"[Task {task_id}] [STEP 0] 错误: 测试用例不存在")
                await self._log_error(db, task_id, "测试用例不存在")
                await self._update_task_status(db, task_id, "failed")
                return
            print(f"[Task {task_id}] [STEP 0] 测试用例: {test_case.case_name}")

            print(f"[Task {task_id}] [STEP 0] 查询任务节点配置...")
            task_nodes = db.query(TaskNode).filter(TaskNode.task_id == task_id).all()
            if not task_nodes:
                print(f"[Task {task_id}] [STEP 0] 错误: 任务没有配置节点")
                await self._log_error(db, task_id, "任务没有配置节点")
                await self._update_task_status(db, task_id, "failed")
                return
            print(f"[Task {task_id}] [STEP 0] 找到 {len(task_nodes)} 个任务节点")

            for i, tn in enumerate(task_nodes):
                node = tn.node
                partition = tn.partition
                partition_info = tn.partitions or (partition.mount_point if partition else "无分区")
                print(f"[Task {task_id}] [STEP 0]   节点{i+1}: {node.node_name} ({node.host}), 分区: {partition_info}")

            self.active_tasks[task_id] = {
                "start_time": datetime.utcnow(),
                "should_stop": False,
            }

            print(f"[Task {task_id}] [STEP 0] 记录任务开始日志...")
            await self._log_info(db, task_id, f"========== 开始执行任务: {task.task_name} ==========")
            await self._log_info(db, task_id, f"使用测试用例: {test_case.case_name}")
            await self._log_info(db, task_id, f"目标节点数: {len(task_nodes)}")

            print(f"[Task {task_id}] [STEP 1] ========== 阶段1: 初始化写入 开始 ==========")
            await self._log_info(db, task_id, "========== 阶段1: 初始化写入 ==========")
            init_service = InitWriteService(self.socket_manager)
            print(f"[Task {task_id}] [STEP 1] 调用 InitWriteService.execute_init_write...")
            init_results = await init_service.execute_init_write(task_id)
            print(f"[Task {task_id}] [STEP 1] 初始化写入完成，结果: {init_results}")

            failed_init_count = sum(1 for v in init_results.values() if not v)
            if failed_init_count > 0:
                print(f"[Task {task_id}] [STEP 1] 警告: {failed_init_count} 个分区初始化失败")
                await self._log_warning(
                    db, task_id,
                    f"初始化写入完成: {len(init_results) - failed_init_count} 成功, {failed_init_count} 失败"
                )
            else:
                print(f"[Task {task_id}] [STEP 1] 成功: {len(init_results)} 个分区全部初始化成功")
                await self._log_info(db, task_id, f"初始化写入完成: {len(init_results)} 个分区全部成功")
            print(f"[Task {task_id}] [STEP 1] ========== 阶段1: 初始化写入 结束 ==========")

            print(f"[Task {task_id}] [STEP 2] ========== 阶段2: FIO测试执行 开始 ==========")
            await self._log_info(db, task_id, "========== 阶段2: FIO测试执行 ==========")
            print(f"[Task {task_id}] [STEP 2] 创建 {len(task_nodes)} 个节点执行协程...")

            coros = [
                self._execute_node_task(task_id, tn.id) for tn in task_nodes
            ]
            print(f"[Task {task_id}] [STEP 2] 开始并行执行所有节点测试 (asyncio.gather)...")
            await asyncio.gather(*coros, return_exceptions=True)
            print(f"[Task {task_id}] [STEP 2] 所有节点测试协程执行完成")

            print(f"[Task {task_id}] [STEP 3] ========== 阶段3: 任务收尾 开始 ==========")
            await self._log_info(db, task_id, "========== 阶段3: 任务收尾 ==========")
            await self._finalize_task(db, task_id)
            print(f"[Task {task_id}] [STEP 3] ========== 任务执行完成 ==========")

        except Exception as e:
            print(f"[Task {task_id}] [ERROR] 任务执行异常: {e!s}")
            import traceback
            traceback.print_exc()
            try:
                await self._log_error(db, task_id, f"任务执行失败: {e!s}")
                await self._update_task_status(db, task_id, "failed")
            except Exception:
                pass
        finally:
            self.active_tasks.pop(task_id, None)
            db.close()
            print(f"[Task {task_id}] 任务资源已清理，Session已关闭")

    # --------------------------------------------------------- 单节点执行 ----
    async def _execute_node_task(self, task_id: int, task_node_id: int):
        db = SessionLocal()
        ssh_service: Optional[SSHService] = None
        node_name = f"#{task_node_id}"
        print(f"[Task {task_id}] [Node {task_node_id}] ========== 开始执行节点任务 ==========")
        try:
            print(f"[Task {task_id}] [Node {task_node_id}] [2.1] 查询 TaskNode 信息...")
            task_node = db.query(TaskNode).filter(TaskNode.id == task_node_id).first()
            if not task_node:
                print(f"[Task {task_id}] [Node {task_node_id}] [2.1] 错误: TaskNode 不存在")
                return
            node = task_node.node
            partition = task_node.partition
            partition_paths = task_node.partitions.split(',') if task_node.partitions else []
            test_case = task_node.task.test_case
            node_name = node.node_name
            partition_display = task_node.partitions or (f"{partition.partition_name}({partition.mount_point})" if partition else "无分区")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.1] 节点: {node_name}, 分区: {partition_display}")

            await self._log_info(db, task_id, f"========== 开始在节点 {node_name} 上执行测试 ==========")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.2] 建立 SSH 连接...")

            ssh_service = SSHService()
            ok = await ssh_service.connect(
                host=node.host,
                port=node.port,
                username=node.username,
                password=node.password,
                private_key=node.private_key,
                tool_path=node.tool_path,
            )
            if not ok:
                print(f"[Task {task_id}] [Node {task_node_id}] [2.2] 错误: SSH 连接失败!")
                await self._log_error(db, task_id, f"节点 {node_name} SSH 连接失败")
                await self._update_task_node_status(db, task_node_id, "failed", "SSH连接失败")
                return
            print(f"[Task {task_id}] [Node {task_node_id}] [2.2] SSH 连接成功!")

            print(f"[Task {task_id}] [Node {task_node_id}] [2.3] 获取系统指纹...")
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
                print(f"[Task {task_id}] [Node {task_node_id}] [2.3] 错误: fio 未安装!")
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

            print(f"[Task {task_id}] [Node {task_node_id}] [2.4] 检查 io_engine 可用性...")
            chosen_engine = ssh_service.best_fio_ioengine(test_case.io_engine)
            if chosen_engine != test_case.io_engine:
                await self._log_warning(
                    db, task_id,
                    f"节点 {node_name} 不支持 io_engine={test_case.io_engine}，"
                    f"已自动切换为 {chosen_engine}"
                )

            print(f"[Task {task_id}] [Node {task_node_id}] [2.5] 检查挂载点是否可写...")
            for mp in partition_paths:
                mount_ok = await self._ensure_writable_mount(
                    db, task_id, ssh_service, mp, node_name
                )
                if not mount_ok:
                    await self._update_task_node_status(
                        db, task_node_id, "failed", f"挂载点不可写: {mp}"
                    )
                    return
            print(f"[Task {task_id}] [Node {task_node_id}] [2.5] 挂载点检查通过!")

            if all(mount_point.startswith("/dev/") for mount_point in partition_paths):
                test_filename = ','.join(partition_paths)
                print(f"[Task {task_id}] [Node {task_node_id}] [2.6] 检测到多个设备文件，并行测试: {test_filename}")
            elif len(partition_paths) == 1:
                mount_point = partition_paths[0]
                if mount_point.startswith("/dev/"):
                    test_filename = mount_point
                else:
                    test_filename = posixpath.normpath(
                        posixpath.join(mount_point, "diskbench_fio_test.dat")
                    )
            else:
                mount_point = partition_paths[0]
                test_filename = mount_point

            output_json = f"/tmp/diskbench_{task_id}_{task_node_id}_{uuid.uuid4().hex[:8]}.json"
            fio_path = await ssh_service.get_tool_path("fio", ssh_service.tool_path)

            fio_command = test_case.generate_fio_command(
                filename=test_filename,
                ioengine_override=chosen_engine,
                output_file=output_json,
                fio_path_override=fio_path,
            )
            if ssh_service.tool_path:
                lib_path = ssh_service.get_lib_path()
                if lib_path:
                    fio_command = f"LD_LIBRARY_PATH={lib_path}:$LD_LIBRARY_PATH {fio_command}"

            monitor_target = partition if partition else type('Partition', (), {'mount_point': partition_paths[0] if partition_paths else '/dev/sda'})()
            monitor_task = asyncio.create_task(
                self._monitor_node_performance(task_id, task_node_id, ssh_service, monitor_target)
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
            print(f"[Task {task_id}] [Node {task_node_id}] [ERROR] 节点任务异常: {e!s}")
            import traceback
            traceback.print_exc()
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
        safe_mp = shlex.quote(mount_point)
        r = await ssh_service.execute_command(f"test -w {safe_mp}; echo $?", timeout=15)
        stdout = r.get("stdout", "").strip()
        lines = stdout.strip().split('\n')
        exit_code = lines[-1] if lines else "1"
        is_writable = (exit_code == "0")

        if not is_writable:
            await self._log_error(
                db, task_id,
                f"节点 {node_name} 挂载点 {mount_point} 不可写 (exit_code={exit_code})"
            )
            return False
        return True

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
        await self._log_info(db, task_id, f"执行FIO命令: {fio_command}")
        fio_timeout = max(60, (runtime or 60) + 60)
        result = await ssh_service.execute_command(fio_command, timeout=fio_timeout)

        if not result.get("success"):
            err = result.get("stderr") or result.get("error") or "unknown"
            await self._log_warning(db, task_id, f"FIO 命令退出异常: {err[:500]}")

        fio_json_text = result.get("stdout", "").strip()
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.3] stdout长度={len(fio_json_text)}, stderr长度={len(result.get('stderr',''))}")
        if not fio_json_text:
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.3] stdout为空，打印stderr前200: {result.get('stderr','')[:200]}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.3] 完整命令: {fio_command}")

        try:
            await ssh_service.execute_command(
                f"rm -f {shlex.quote(test_filename)}", timeout=30
            )
        except Exception:
            pass

        if not fio_json_text:
            error_msg = f"FIO 执行失败，没有产生有效输出"
            raise Exception(error_msg)

        await self._parse_fio_results(db, task_id, task_node_id, fio_json_text, result)

    # ---------------------------------------------------------- FIO 解析 ----
    async def _parse_fio_results(
        self, db: Session, task_id: int, task_node_id: int, fio_output: str, ssh_result: dict = None
    ):
        data = None
        # 优先从 stdout 解析：跳过开头的 warning 文本，找到第一个 '{'
        if fio_output:
            json_start = fio_output.find('{')
            if json_start >= 0:
                json_text = fio_output[json_start:]
                try:
                    data = json.loads(json_text)
                except json.JSONDecodeError as e:
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] stdout解析失败: {e}, 跳过{json_start}个字符")
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] stdout前300: {fio_output[:300]}")
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] stdout末300: {fio_output[-300:]}")
        if data is None:
            raise ValueError(
                f"FIO JSON 解析失败 (stdout长度={len(fio_output)}, "
                f"stderr前200: {ssh_result.get('stderr','')[:200]})"
            )
        jobs = data.get("jobs", [])
        if not jobs:
            raise ValueError("fio 输出中没有 jobs")

        job = jobs[0] if len(jobs) == 1 else self._aggregate_jobs(jobs)
        read_stats = job.get("read", {}) or {}
        write_stats = job.get("write", {}) or {}

        total_iops = float(read_stats.get("iops", 0)) + float(write_stats.get("iops", 0))
        total_bw_mbs = (float(read_stats.get("bw", 0)) + float(write_stats.get("bw", 0))) / 1024.0
        read_lat_us = self._extract_latency_us(read_stats)
        write_lat_us = self._extract_latency_us(write_stats)
        nonzero = [x for x in (read_lat_us, write_lat_us) if x > 0]
        avg_lat_ms = (sum(nonzero) / len(nonzero) / 1000.0) if nonzero else 0.0

        ws_data = await asyncio.to_thread(
            _save_results_sync,
            task_id, task_node_id, total_iops, total_bw_mbs, avg_lat_ms,
            read_stats, write_stats, read_lat_us, write_lat_us, job
        )

        if ws_data:
            await self.socket_manager.broadcast_to_task(
                str(task_id), "performance_update", ws_data
            )

    @staticmethod
    def _aggregate_jobs(jobs: list) -> dict:
        agg = {"read": {"iops": 0, "bw": 0, "total_ios": 0},
               "write": {"iops": 0, "bw": 0, "total_ios": 0}}
        lat_accum = {"read": [], "write": []}
        for j in jobs:
            for k in ("read", "write"):
                s = j.get(k, {}) or {}
                agg[k]["iops"] += float(s.get("iops", 0))
                agg[k]["bw"] += float(s.get("bw", 0))
                agg[k]["total_ios"] += int(s.get("total_ios", 0))
                if "lat_ns" in s:
                    lat_accum[k].append(("lat_ns", s["lat_ns"]))
                elif "lat" in s:
                    lat_accum[k].append(("lat", s["lat"]))
        for k in ("read", "write"):
            if lat_accum[k]:
                means = []
                for kind, v in lat_accum[k]:
                    mean = float(v.get("mean", 0))
                    if kind == "lat_ns":
                        mean /= 1000.0
                    means.append(mean)
                if means:
                    agg[k]["lat"] = {"mean": sum(means) / len(means)}
        return agg

    @staticmethod
    def _extract_latency_us(stats: dict) -> float:
        if not stats:
            return 0.0
        if "lat_ns" in stats:
            return float(stats["lat_ns"].get("mean", 0)) / 1000.0
        if "clat_ns" in stats:
            return float(stats["clat_ns"].get("mean", 0)) / 1000.0
        if "lat" in stats:
            return float(stats["lat"].get("mean", 0))
        if "clat" in stats:
            return float(stats["clat"].get("mean", 0))
        return 0.0

    # -------------------------------------------------------- 性能监控 ----
    async def _monitor_node_performance(
        self, task_id: int, task_node_id: int,
        ssh_service: SSHService, partition
    ):
        db = SessionLocal()
        try:
            device = await ssh_service.get_device_by_mountpoint(partition.mount_point)
            if not device:
                device = (partition.partition_name or "").lstrip("/").replace("dev/", "")

            while True:
                if task_id in self.active_tasks and self.active_tasks[task_id]["should_stop"]:
                    break

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
                except Exception:
                    pass

                try:
                    usage = await ssh_service.get_cpu_mem_usage()
                    perf = IOPerformanceData(
                        task_node_id=task_node_id,
                        source="monitor",
                        iops=0, bandwidth=0, latency=0,
                        cpu_usage=usage["cpu_usage"],
                        memory_usage=usage["memory_usage"],
                    )
                    db.add(perf)
                    db.commit()
                except Exception:
                    pass

                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
        finally:
            db.close()

    # ------------------------------------------------- 任务收尾 & 日志工具（已修复缩进！）
    async def _finalize_task(self, db: Session, task_id: int):
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        task_nodes = db.query(TaskNode).filter(TaskNode.task_id == task_id).all()
        total_iops = total_lat = total_bw = 0.0
        completed = 0

        for tn in task_nodes:
            if tn.status == "completed":
                total_iops += float(tn.iops or 0)
                total_lat += float(tn.latency or 0)
                total_bw += float(tn.bandwidth or 0)
                completed += 1

        task.end_time = datetime.utcnow()
        if task.start_time:
            task.duration = int((task.end_time - task.start_time).total_seconds())

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
            db, task_id, f"========== 任务 {task.task_name} 执行完成，状态: {task.status} =========="
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

def _save_results_sync(
    task_id: int, task_node_id: int,
    total_iops: float, total_bw_mbs: float, avg_lat_ms: float,
    read_stats: dict, write_stats: dict,
    read_lat_us: float, write_lat_us: float, job: dict
) -> dict:
    """
    同步函数：在独立线程中执行所有数据库操作
    避免 async 上下文中同步 DB 操作导致的连接争抢和数据包乱序问题
    返回 WebSocket 通知所需的数据
    """
    db = SessionLocal()
    try:
        # 1. 更新 TaskNode
        task_node = db.query(TaskNode).filter(TaskNode.id == task_node_id).first()
        if not task_node:
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2] 警告: TaskNode不存在")
            return {}

        task_node.iops = total_iops
        task_node.bandwidth = total_bw_mbs
        task_node.latency = avg_lat_ms
        task_node.io_ops = int(
            (read_stats.get("total_ios") or 0) + (write_stats.get("total_ios") or 0)
        )
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2] 更新TaskNode数据库记录...")

        # 2. 保存 IOPerformanceData（包含百分位数据）
        percents = _extract_percentiles(job, task_id, task_node_id)
        perf = IOPerformanceData(
            task_node_id=task_node_id,
            source="fio",
            test_type="read",
            iops=total_iops,
            bandwidth=total_bw_mbs,
            latency=avg_lat_ms,
            read_iops=float(read_stats.get("iops", 0)),
            write_iops=float(write_stats.get("iops", 0)),
            read_bw=float(read_stats.get("bw", 0)) / 1024.0,
            write_bw=float(write_stats.get("bw", 0)) / 1024.0,
            read_lat=read_lat_us / 1000.0,
            write_lat=write_lat_us / 1000.0,
            p50_lat_us=percents["read"].get("p50", 0),
            p75_lat_us=percents["read"].get("p75", 0),
            p90_lat_us=percents["read"].get("p90", 0),
            p95_lat_us=percents["read"].get("p95", 0),
            p99_lat_us=percents["read"].get("p99", 0),
            p999_lat_us=percents["read"].get("p999", 0),
            p9999_lat_us=percents["read"].get("p9999", 0),
            max_lat_us=percents["read"].get("max_lat_us", 0),
        )
        db.add(perf)
        db.commit()
        db.refresh(perf)
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2] 性能数据已保存, perf_id={perf.id}")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2] read百分位: {percents['read']}")

        # 3. 获取 node_node_id
        node_node_id = task_node.node_id

        # 4. 获取 node_name 用于 WebSocket 通知
        from models.node import Node
        node_name = db.query(Node).filter(Node.id == node_node_id).first().node_name

        return {
            "task_node_id": task_node_id,
            "node_name": node_name,
            "iops": total_iops,
            "bandwidth": total_bw_mbs,
            "latency": avg_lat_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.ERROR] 保存结果失败: {e!s}")
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except Exception:
            pass
        return {}
    finally:
        db.close()


def _extract_percentiles(job: dict, task_id: int, task_node_id: int) -> dict:
    """从 fio job 数据中提取 read/write 的百分位延迟（微秒）"""
    result = {"read": {}, "write": {}}
    perc_mapping = {
        "p50": 1, "p75": 2, "p90": 3, "p95": 4,
        "p99": 5, "p999": 6, "p9999": 7
    }
    for test_type in ("read", "write"):
        stats = job.get(test_type, {}) or {}
        for key in ("lat_ns", "clat_ns", "lat"):
            lat_data = stats.get(key, {})
            perc_values = lat_data.get("perc", [])
            if perc_values:
                result[test_type]["max_lat_us"] = float(lat_data.get("max", 0))
                for name, idx in perc_mapping.items():
                    if idx < len(perc_values):
                        result[test_type][name] = float(perc_values[idx])
                break
    return result
