from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, Text, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import shlex
import posixpath
from typing import Optional

from core.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    io_engine = Column(String(50), default="libaio", nullable=False)
    block_size = Column(String(20), default="4k", nullable=False)
    queue_depth = Column(Integer, default=32, nullable=False)
    io_size = Column(String(20), default="1G", nullable=False)
    runtime = Column(Integer, default=60, nullable=False)
    rw_mode = Column(
        Enum("read", "write", "randread", "randwrite", "rw", "randrw"),
        default="read",
        nullable=False,
    )
    rw_ratio = Column(String(10), default="50/50", nullable=False)
    compression_ratio = Column(DECIMAL(3, 2), default=0.00, nullable=False)
    direct_io = Column(Boolean, default=True, nullable=False)
    numjobs = Column(Integer, default=1, nullable=False)
    time_based = Column(Boolean, default=True, nullable=False)
    verify = Column(String(20), nullable=True)
    verify_fatal = Column(Boolean, default=False, nullable=False)
    group_reporting = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User", backref="test_cases")
    tasks = relationship("Task", back_populates="test_case")

    def __repr__(self):
        return f"<TestCase(id={self.id}, name={self.case_name}, rw_mode={self.rw_mode})>"

    def to_dict(self):
        return {
            "id": self.id,
            "case_name": self.case_name,
            "description": self.description,
            "io_engine": self.io_engine,
            "block_size": self.block_size,
            "queue_depth": self.queue_depth,
            "io_size": self.io_size,
            "runtime": self.runtime,
            "rw_mode": self.rw_mode,
            "rw_ratio": str(self.rw_ratio),
            "compression_ratio": float(self.compression_ratio),
            "direct_io": self.direct_io,
            "numjobs": self.numjobs,
            "time_based": self.time_based,
            "verify": self.verify,
            "verify_fatal": self.verify_fatal,
            "group_reporting": self.group_reporting,
            "created_by": self.created_by,
            "is_public": self.is_public,
            "is_template": self.is_template,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def generate_fio_command(
        self,
        filename: str = "testfile",
        ioengine_override: Optional[str] = None,
        output_file: Optional[str] = None,
        fio_path_override: Optional[str] = None,
        extra_options: Optional[list] = None,
    ) -> str:
        """
        生成 fio 命令（跨平台）

        Args:
            filename: 测试文件路径（会做路径规范化和 shell 转义）
                       可以是单个文件路径，也可以是多个逗号分隔的路径
            ioengine_override: 由 SSHService.best_fio_ioengine() 探测得到的
                               实际可用 io engine，优先级高于 self.io_engine
            output_file: 如果指定，fio 会把 JSON 输出写到该文件（避免 stderr 污染）
            fio_path_override: fio 可执行文件路径，默认使用系统 PATH 中的 fio
            extra_options: 额外的 fio 选项列表

        Returns:
            拼装好的 fio 命令字符串，所有用户输入均经过 shlex 转义防注入
        """
        # 路径规范化：去除多余斜线（/ + /foo → /foo）
        # 如果是多个文件（逗号分隔），分别处理每个
        if ',' in filename:
            filenames = [posixpath.normpath(f.strip()) for f in filename.split(',')]
        else:
            filenames = [posixpath.normpath(filename)]

        name_q = shlex.quote(self.case_name or "fio_test")
        engine = ioengine_override or self.io_engine or "psync"
        engine_q = shlex.quote(engine)
        bs_q = shlex.quote(self.block_size or "4k")
        size_q = shlex.quote(self.io_size or "1G")
        rw_q = shlex.quote(self.rw_mode or "read")
        fio_binary = shlex.quote(fio_path_override) if fio_path_override else "fio"

        cmd_parts = [
            fio_binary,
            f"--name={name_q}",
            f"--ioengine={engine_q}",
            f"--bs={bs_q}",
            f"--iodepth={int(self.queue_depth or 1)}",
            f"--size={size_q}",
            f"--runtime={int(self.runtime or 60)}",
            f"--rw={rw_q}",
        ]

        # 读写混合比例
        if self.rw_mode in ("rw", "randrw"):
            try:
                read_pct = int(str(self.rw_ratio).split("/")[0])
                read_pct = max(0, min(100, read_pct))
                cmd_parts.append(f"--rwmixread={read_pct}")
            except (ValueError, IndexError):
                cmd_parts.append("--rwmixread=50")

        # 压缩比
        try:
            cr = float(self.compression_ratio or 0)
            if cr > 0:
                cmd_parts.append(f"--buffer_compress_percentage={int(cr * 100)}")
        except (ValueError, TypeError):
            pass

        # Direct IO：仅 Linux 支持 O_DIRECT，非 Linux 引擎应自动关闭
        if self.direct_io and engine in ("libaio", "io_uring"):
            cmd_parts.append("--direct=1")

        cmd_parts.append(f"--numjobs={int(self.numjobs or 1)}")

        if self.time_based:
            cmd_parts.append("--time_based")

        if self.verify:
            cmd_parts.append(f"--verify={shlex.quote(self.verify)}")
            if self.verify_fatal:
                cmd_parts.append("--verify_fatal=1")

        if self.group_reporting:
            cmd_parts.append("--group_reporting")

        # 每个文件单独指定 --filename
        for f in filenames:
            cmd_parts.append(f"--filename={shlex.quote(f)}")

        # 额外选项
        if extra_options:
            cmd_parts.extend(extra_options)

        # 关键修复：
        # 1. 用 --output 指定文件，避免 stderr 警告（如 engine fallback、
        #    参数 deprecated 警告）污染 JSON
        # 2. 让 fio 把 JSON 直接写入文件，由调用方读取该文件
        cmd_parts.append("--output-format=json")
        if output_file:
            cmd_parts.append(f"--output={shlex.quote(output_file)}")

        return " ".join(cmd_parts)
