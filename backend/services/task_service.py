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
from models.task_node_partition import TaskNodePartition, TestResultPercentile
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

            # 打印每个节点详情
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

            # =============================================
            # 阶段 1: 初始化写入
            # =============================================
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

            # =============================================
            # 阶段 2: FIO 测试执行
            # =============================================
            print(f"[Task {task_id}] [STEP 2] ========== 阶段2: FIO测试执行 开始 ==========")
            await self._log_info(db, task_id, "========== 阶段2: FIO测试执行 ==========")
            print(f"[Task {task_id}] [STEP 2] 创建 {len(task_nodes)} 个节点执行协程...")

            # 每个节点一个独立协程，各自管理自己的 db session
            coros = [
                self._execute_node_task(task_id, tn.id) for tn in task_nodes
            ]
            print(f"[Task {task_id}] [STEP 2] 开始并行执行所有节点测试 (asyncio.gather)...")
            await asyncio.gather(*coros, return_exceptions=True)
            print(f"[Task {task_id}] [STEP 2] 所有节点测试协程执行完成")

            # =============================================
            # 阶段 3: 任务收尾
            # =============================================
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
        """在单个节点上执行测试（自建 session）"""
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
            # 支持多分区：优先使用 partitions 字段
            partition_paths = task_node.partitions.split(',') if task_node.partitions else []
            test_case = task_node.task.test_case
            node_name = node.node_name
            partition_display = task_node.partitions or (f"{partition.partition_name}({partition.mount_point})" if partition else "无分区")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.1] 节点: {node_name}, 分区: {partition_display}")

            await self._log_info(db, task_id, f"========== 开始在节点 {node_name} 上执行测试 ==========")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.2] 建立 SSH 连接...")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.2]   主机: {node.host}:{node.port}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.2]   用户名: {node.username}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.2]   登录方式: {node.login_type}")

            # 建立 SSH 并探测系统
            ssh_service = SSHService()
            print(f"[Task {task_id}] [Node {task_node_id}] [2.2] 调用 SSHService.connect()...")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.2]   工具目录: {node.tool_path or '(系统默认)'}")
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
            print(f"[Task {task_id}] [Node {task_node_id}] [2.3] 系统信息:")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.3]   OS: {fingerprint['os_family']}/{fingerprint['distro']}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.3]   fio版本: {fingerprint['fio_version']}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.3]   iostat版本: {fingerprint['iostat_version']}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.3]   libaio: {'yes' if fingerprint['has_libaio'] else 'no'}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.3]   fio安装: {'yes' if fingerprint['has_fio'] else 'no'}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.3]   工具目录: {ssh_service.tool_path or '(系统默认)'}")

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

            # 获取可用的 ioengine
            print(f"[Task {task_id}] [Node {task_node_id}] [2.4] 检查 io_engine 可用性...")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.4]   请求的io_engine: {test_case.io_engine}")
            chosen_engine = ssh_service.best_fio_ioengine(test_case.io_engine)
            print(f"[Task {task_id}] [Node {task_node_id}] [2.4]   实际使用的io_engine: {chosen_engine}")
            if chosen_engine != test_case.io_engine:
                print(f"[Task {task_id}] [Node {task_node_id}] [2.4]   警告: 不支持请求的io_engine，已切换")
                await self._log_warning(
                    db, task_id,
                    f"节点 {node_name} 不支持 io_engine={test_case.io_engine}，"
                    f"已自动切换为 {chosen_engine}"
                )

            # 检查挂载点、确保可写
            # 检查所有分区是否可写
            print(f"[Task {task_id}] [Node {task_node_id}] [2.5] 检查挂载点是否可写...")
            for mp in partition_paths:
                print(f"[Task {task_id}] [Node {task_node_id}] [2.5]   检查分区: {mp}")
                mount_ok = await self._ensure_writable_mount(
                    db, task_id, ssh_service, mp, node_name
                )
                if not mount_ok:
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.5] 错误: 挂载点不可写: {mp}!")
                    await self._update_task_node_status(
                        db, task_node_id, "failed", f"挂载点不可写: {mp}"
                    )
                    return
            print(f"[Task {task_id}] [Node {task_node_id}] [2.5] 挂载点检查通过!")

            # 测试文件路径
            # 重要：对于设备文件(如/dev/vdb)，直接用它作为测试文件，不能再加子路径
            # 支持多分区：逗号分隔所有分区路径
            if all(mount_point.startswith("/dev/") for mount_point in partition_paths):
                # 所有分区都是设备文件，并行测试所有设备
                test_filename = ','.join(partition_paths)
                print(f"[Task {task_id}] [Node {task_node_id}] [2.6] 检测到多个设备文件，并行测试: {test_filename}")
            elif len(partition_paths) == 1:
                # 单一分区
                mount_point = partition_paths[0]
                if mount_point.startswith("/dev/"):
                    test_filename = mount_point
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.6] 检测到设备文件，使用设备本身作为测试文件: {test_filename}")
                else:
                    # 普通目录使用子目录
                    test_filename = posixpath.normpath(
                        posixpath.join(mount_point, "diskbench_fio_test.dat")
                    )
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.6] 普通目录，使用子路径作为测试文件: {test_filename}")
            else:
                # 混合场景（不应该发生），使用第一个
                mount_point = partition_paths[0]
                test_filename = mount_point
                print(f"[Task {task_id}] [Node {task_node_id}] [2.6] 混合分区场景，使用: {test_filename}")
            # JSON 直接从 stdout 捕获，不再需要临时文件
            output_json = f"/tmp/diskbench_{task_id}_{task_node_id}_{uuid.uuid4().hex[:8]}.json"
            print(f"[Task {task_id}] [Node {task_node_id}] [2.6] 准备FIO测试命令...")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.6]   测试文件: {test_filename}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.6]   JSON从stdout捕获")

            # 获取 fio 路径（优先使用工具目录）
            fio_path = await ssh_service.get_tool_path("fio", ssh_service.tool_path)
            print(f"[Task {task_id}] [Node {task_node_id}] [2.6]   fio路径: {fio_path}")

            # 构建 fio 命令（带 LD_LIBRARY_PATH 支持自定义库）
            fio_command = test_case.generate_fio_command(
                filename=test_filename,
                ioengine_override=chosen_engine,
                output_file=output_json,
                fio_path_override=fio_path,
            )
            # 如果工具目录有自定义库，包装命令设置 LD_LIBRARY_PATH
            if ssh_service.tool_path:
                lib_path = ssh_service.get_lib_path()
                if lib_path:
                    fio_command = f"LD_LIBRARY_PATH={lib_path}:$LD_LIBRARY_PATH {fio_command}"
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.6]   已添加LD_LIBRARY_PATH: {lib_path}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.6] FIO完整命令: {fio_command}")

            # 启动监控（如果 partition 为 None，使用第一个分区路径）
            print(f"[Task {task_id}] [Node {task_node_id}] [2.7] 启动性能监控任务...")
            monitor_target = partition if partition else type('Partition', (), {'mount_point': partition_paths[0] if partition_paths else '/dev/sda'})()
            monitor_task = asyncio.create_task(
                self._monitor_node_performance(task_id, task_node_id, ssh_service, monitor_target)
            )
            print(f"[Task {task_id}] [Node {task_node_id}] [2.7] 性能监控任务已启动")

            try:
                print(f"[Task {task_id}] [Node {task_node_id}] [2.8] 开始执行FIO测试...")
                await self._execute_fio_test(
                    db, task_id, task_node_id, ssh_service,
                    fio_command, output_json, test_filename, test_case.runtime
                )
                print(f"[Task {task_id}] [Node {task_node_id}] [2.8] FIO测试执行完成!")
                await self._update_task_node_status(db, task_node_id, "completed")
                await self._log_info(db, task_id, f"节点 {node_name} 测试完成")
                print(f"[Task {task_id}] [Node {task_node_id}] [2.8] 节点状态已更新为completed")
            finally:
                print(f"[Task {task_id}] [Node {task_node_id}] [2.9] 停止性能监控任务...")
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
                print(f"[Task {task_id}] [Node {task_node_id}] [2.9] 性能监控已停止")

            print(f"[Task {task_id}] [Node {task_node_id}] ========== 节点任务执行完成 ==========")

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
                print(f"[Task {task_id}] [Node {task_node_id}] 关闭SSH连接...")
                ssh_service.close()
            db.close()
            print(f"[Task {task_id}] [Node {task_node_id}] 节点Session已关闭")

    async def _ensure_writable_mount(
        self, db: Session, task_id: int, ssh_service: SSHService,
        mount_point: str, node_name: str
    ) -> bool:
        """确保挂载点存在且可写

        注意：对于设备文件(如/dev/vdb)，test -d返回失败，但test -w可能成功。
        所以这里直接检查可写性，不检查是否是目录。
        """
        safe_mp = shlex.quote(mount_point)
        print(f"[Task {task_id}] [Node {node_name}] [2.5.1] 检查挂载点是否可写: {mount_point}")

        # 检查是否可写（使用退出码判断）
        # 对于设备文件如 /dev/vdb，test -w 不输出内容，需要用 ; echo $? 获取退出码
        print(f"[Task {task_id}] [Node {node_name}] [2.5.1] 执行: test -w {safe_mp}; echo $?")
        r = await ssh_service.execute_command(f"test -w {safe_mp}; echo $?", timeout=15)
        stdout = r.get("stdout", "").strip()
        print(f"[Task {task_id}] [Node {node_name}] [2.5.1] 命令结果: stdout='{stdout}'")

        # 退出码为0表示可写，echo $?会输出0; 非0表示不可写
        # 取最后一行（退出码）
        lines = stdout.strip().split('\n')
        exit_code = lines[-1] if lines else "1"
        is_writable = (exit_code == "0")
        print(f"[Task {task_id}] [Node {node_name}] [2.5.1] 退出码: {exit_code}, 可写: {is_writable}")

        if not is_writable:
            print(f"[Task {task_id}] [Node {node_name}] [2.5.1] 挂载点不可写!")
            await self._log_error(
                db, task_id,
                f"节点 {node_name} 挂载点 {mount_point} 不可写 (exit_code={exit_code})"
            )
            return False

        print(f"[Task {task_id}] [Node {node_name}] [2.5.1] 挂载点可写检查通过!")
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
        """
        执行 FIO 测试
        关键修复：
        - 超时 = runtime + 60s 缓冲（原来固定 3600s）
        - fio JSON 直接从 stdout 捕获（不再写文件，避免警告混入）
        - 测试结束后清理测试文件
        """
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.1] 执行FIO测试...")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.1] FIO命令: {fio_command}")
        await self._log_info(db, task_id, f"执行FIO命令: {fio_command}")

        # 超时 = runtime + ramp + 缓冲
        fio_timeout = max(60, (runtime or 60) + 60)
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.1] 设置超时: {fio_timeout}秒 (runtime={runtime})")

        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.2] 开始执行FIO命令 (这可能需要 {fio_timeout} 秒)...")
        result = await ssh_service.execute_command(fio_command, timeout=fio_timeout)
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.2] FIO命令执行完成!")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.2] 结果: success={result.get('success')}")

        # stderr 包含警告信息（如 clock setaffinity failed），可以忽略
        if result.get('stderr'):
            stderr_preview = result.get('stderr')[:200]
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.2] stderr警告: {stderr_preview}")

        if not result.get("success"):
            # 即使退出码非 0，也尝试从 stdout 解析 JSON（fio 有时中途完成但退出码怪异）
            err = result.get("stderr") or result.get("error") or "unknown"
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.2] 警告: FIO退出码异常，尝试从stdout解析...")
            await self._log_warning(db, task_id, f"FIO 命令退出异常: {err[:500]}")

        # JSON 直接从 stdout 获取（不再读取文件，避免警告混入）
        fio_json_text = result.get("stdout", "").strip()
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.3] JSON从stdout获取: 长度={len(fio_json_text)}")

        # 清理远端测试文件（不再有 JSON 文件需要清理）
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.4] 清理远端临时文件...")
        try:
            cleanup_cmd = f"rm -f {shlex.quote(test_filename)}"
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.4] 清理命令: {cleanup_cmd}")
            await ssh_service.execute_command(
                f"rm -f {shlex.quote(test_filename)}",
                timeout=30,
            )
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.4] 临时文件清理完成")
        except Exception as e:
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.4] 清理临时文件失败: {e!s}")

        if not fio_json_text:
            error_msg = f"FIO 执行失败，没有产生有效输出。stderr: {(result.get('stderr') or result.get('error', ''))[:500]}"
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5] 错误: {error_msg}")
            raise Exception(error_msg)

        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5] 开始解析FIO JSON结果...")
        await self._parse_fio_results(db, task_id, task_node_id, fio_json_text)
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5] FIO结果解析完成!")

    # ---------------------------------------------------------- FIO 解析 ----

    async def _parse_fio_results(
        self, db: Session, task_id: int, task_node_id: int, fio_output: str
    ):
        """
        解析 FIO JSON 输出
        关键修复：兼容 fio 2.x / 3.x 字段差异（lat vs lat_ns）
        """
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] 开始解析FIO JSON...")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] JSON内容前200字符: {fio_output[:200]}")

        # 解析JSON（纯计算，不需要db）
        data = json.loads(fio_output)
        jobs = data.get("jobs", [])
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] 解析到 {len(jobs)} 个job")
        if not jobs:
            raise ValueError("fio 输出中没有 jobs")

        # group_reporting=True 时 jobs[0] 是聚合结果
        # 否则需要汇总所有 jobs
        job = jobs[0] if len(jobs) == 1 else self._aggregate_jobs(jobs)

        read_stats = job.get("read", {}) or {}
        write_stats = job.get("write", {}) or {}

        # Debug: 打印 read stats 的 key 和 lat 相关字段
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] read_stats keys: {list(read_stats.keys())}")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] write_stats keys: {list(write_stats.keys())}")
        if "lat_ns" in read_stats:
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] read lat_ns: {read_stats['lat_ns']}")
        if "lat" in read_stats:
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] read lat: {read_stats['lat']}")

        total_iops = float(read_stats.get("iops", 0)) + float(write_stats.get("iops", 0))
        # fio bw 单位是 KB/s，转成 MB/s
        total_bw_mbs = (
            float(read_stats.get("bw", 0)) + float(write_stats.get("bw", 0))
        ) / 1024.0

        # 延迟：兼容 fio 2.x / 3.x
        read_lat_us = self._extract_latency_us(read_stats)
        write_lat_us = self._extract_latency_us(write_stats)
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.1] read_lat_us={read_lat_us:.3f}, write_lat_us={write_lat_us:.3f}")

        # 非零方取均值
        nonzero = [x for x in (read_lat_us, write_lat_us) if x > 0]
        avg_lat_ms = (sum(nonzero) / len(nonzero) / 1000.0) if nonzero else 0.0

        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2] 解析结果:")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2]   读IOPS: {read_stats.get('iops', 0):.2f}")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2]   写IOPS: {write_stats.get('iops', 0):.2f}")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2]   总IOPS: {total_iops:.2f}")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2]   读带宽: {float(read_stats.get('bw', 0))/1024:.2f} MB/s")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2]   写带宽: {float(write_stats.get('bw', 0))/1024:.2f} MB/s")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2]   总带宽: {total_bw_mbs:.2f} MB/s")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2]   读延迟: {read_lat_us/1000:.3f} ms")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2]   写延迟: {write_lat_us/1000:.3f} ms")
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2]   平均延迟: {avg_lat_ms:.3f} ms")

        # ============================================================
        # 写库操作：使用 asyncio.to_thread 丢到独立线程执行
        # 彻底避免 async 函数中同步 DB 操作导致的连接争抢问题
        # ============================================================
        ws_data = await asyncio.to_thread(
            _save_results_sync,
            task_id, task_node_id, total_iops, total_bw_mbs, avg_lat_ms,
            read_stats, write_stats, read_lat_us, write_lat_us, job
        )

        # WebSocket通知（在async上下文中发送）
        if ws_data:
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.3] 发送WebSocket性能更新...")
            await self.socket_manager.broadcast_to_task(
                str(task_id),
                "performance_update",
                ws_data
            )
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.3] WebSocket通知已发送")


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

        # 2. 保存 IOPerformanceData
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
        db.refresh(perf)
        perf_id_val = perf.id
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.2] 性能数据已保存到数据库, perf_id={perf_id_val}")

        # 3. 保存百分位数延迟数据
        _save_percentile_data_sync(db, task_id, task_node_id, job)

        # 4. 获取node_name用于WebSocket通知
        from models.node import Node
        node_name = db.query(Node).filter(Node.id == task_node.node_id).first().node_name

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

def _save_percentile_data_sync(db: Session, task_id: int, task_node_id: int, job: dict):
    """同步函数：在已有session中保存百分位数数据"""
    try:
        for test_type in ("read", "write"):
            stats = job.get(test_type, {}) or {}
            lat_ns = stats.get("lat_ns", {})

            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.4] {test_type}: stats keys={list(stats.keys())}")
            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.4] {test_type}: lat_ns={lat_ns}, keys={list(lat_ns.keys()) if lat_ns else 'empty'}")

            if not lat_ns:
                clat_ns = stats.get("clat_ns", {})
                if clat_ns:
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.4] {test_type}: 使用 clat_ns 代替 lat_ns")
                    lat_ns = clat_ns
                else:
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.4] {test_type}: 无 lat_ns/clat_ns 数据，跳过百分位数保存")
                    continue

            perc_values = lat_ns.get("perc", [])
            percentile_mapping = {
                "p1": 0, "p50": 1, "p75": 2, "p90": 3, "p95": 4,
                "p99": 5, "p999": 6, "p9999": 7, "p99999": 8
            }

            for name, idx in percentile_mapping.items():
                if idx < len(perc_values):
                    latency_us = float(perc_values[idx])
                    print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.4] {test_type} {name}= {latency_us} us (idx={idx})")

                    existing = db.query(TestResultPercentile).filter(
                        TestResultPercentile.task_node_id == task_node_id,
                        TestResultPercentile.percentile_name == name,
                        TestResultPercentile.test_type == test_type
                    ).first()

                    if existing:
                        existing.latency_us = latency_us
                    else:
                        percentile = TestResultPercentile(
                            task_node_id=task_node_id,
                            percentile_name=name,
                            latency_us=latency_us,
                            test_type=test_type
                        )
                        db.add(percentile)

            print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.4] {test_type} 百分位延迟已保存")

        db.commit()
    except Exception as e:
        print(f"[Task {task_id}] [Node {task_node_id}] [2.8.5.4] 保存百分位延迟失败: {e!s}")
        db.rollback()
    finally:
        db.close()

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
        print(f"[Task {task_id}] [STEP 3.1] 开始任务收尾处理...")
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"[Task {task_id}] [STEP 3.1] 错误: 任务不存在")
            return
        print(f"[Task {task_id}] [STEP 3.1] 任务: {task.task_name}")

        task_nodes = db.query(TaskNode).filter(TaskNode.task_id == task_id).all()
        print(f"[Task {task_id}] [STEP 3.2] 查询到 {len(task_nodes)} 个任务节点")

        total_iops = total_lat = total_bw = 0.0
        total_io_ops = 0
        completed = 0
        print(f"[Task {task_id}] [STEP 3.3] 汇总各节点结果:")
        for tn in task_nodes:
            node_name = tn.node.node_name if tn.node else "unknown"
            print(f"[Task {task_id}] [STEP 3.3]   节点: {node_name}, 状态: {tn.status}, IOPS: {tn.iops}, 带宽: {tn.bandwidth}, 延迟: {tn.latency}")
            if tn.status == "completed":
                total_iops += float(tn.iops or 0)
                total_lat += float(tn.latency or 0)
                total_bw += float(tn.bandwidth or 0)
                total_io_ops += int(tn.io_ops or 0)
                completed += 1

        print(f"[Task {task_id}] [STEP 3.4] 汇总结果:")
        print(f"[Task {task_id}] [STEP 3.4]   完成节点数: {completed}/{len(task_nodes)}")
        print(f"[Task {task_id}] [STEP 3.4]   总IOPS: {total_iops:.2f}")
        print(f"[Task {task_id}] [STEP 3.4]   平均IOPS: {total_iops/completed if completed > 0 else 0:.2f}")
        print(f"[Task {task_id}] [STEP 3.4]   平均延迟: {total_lat/completed if completed > 0 else 0:.2f} ms")
        print(f"[Task {task_id}] [STEP 3.4]   平均带宽: {total_bw/completed if completed > 0 else 0:.2f} MB/s")
        print(f"[Task {task_id}] [STEP 3.4]   总IO操作数: {total_io_ops}")

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
        print(f"[Task {task_id}] [STEP 3.5] 确定最终状态: failed={failed}, cancelled={cancelled}")

        if failed == len(task_nodes):
            task.status = "failed"
            print(f"[Task {task_id}] [STEP 3.5] 最终状态: failed (全部节点失败)")
        elif cancelled > 0:
            task.status = "cancelled"
            print(f"[Task {task_id}] [STEP 3.5] 最终状态: cancelled (有节点取消)")
        else:
            task.status = "completed"
            print(f"[Task {task_id}] [STEP 3.5] 最终状态: completed")

        print(f"[Task {task_id}] [STEP 3.5] 任务持续时间: {task.duration} 秒")
        db.commit()
        print(f"[Task {task_id}] [STEP 3.5] 数据库已提交")

        print(f"[Task {task_id}] [STEP 3.6] 记录任务完成日志...")
        await self._log_info(
            db, task_id, f"========== 任务 {task.task_name} 执行完成，状态: {task.status} =========="
        )
        await self._log_info(
            db, task_id, f"汇总结果 - 平均IOPS: {total_iops/completed if completed > 0 else 0:.2f}, "
            f"平均延迟: {total_lat/completed if completed > 0 else 0:.2f}ms, "
            f"平均带宽: {total_bw/completed if completed > 0 else 0:.2f}MB/s, "
            f"总耗时: {task.duration}秒"
        )

        print(f"[Task {task_id}] [STEP 3.7] 发送任务完成WebSocket通知...")
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
        print(f"[Task {task_id}] [STEP 3.7] WebSocket通知已发送")
        print(f"[Task {task_id}] [STEP 3] ========== 任务收尾完成 ==========")

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
