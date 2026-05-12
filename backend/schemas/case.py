from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class TestCaseBase(BaseModel):
    case_name: str
    description: Optional[str] = None
    io_engine: str = "libaio"
    block_size: str = "4k"
    queue_depth: int = 32
    io_size: str = "1G"
    runtime: int = 60
    rw_mode: str = "read"
    rw_ratio: str = "50/50"
    compression_ratio: float = 0.00
    direct_io: bool = True
    numjobs: int = 1
    time_based: bool = True
    verify: Optional[str] = None
    verify_fatal: bool = False
    group_reporting: bool = True
    is_public: bool = False
    is_template: bool = False
    
    @validator('case_name')
    def validate_case_name(cls, v):
        if len(v) < 1 or len(v) > 200:
            raise ValueError('用例名称长度必须在1-200个字符之间')
        return v
    
    @validator('io_engine')
    def validate_io_engine(cls, v):
        valid_engines = ["sync", "psync", "vsync", "pvsync", "libaio", "posixaio", 
                        "solarisaio", "windowsaio", "mmap", "splice", "null", 
                        "net", "netsplice", "cpuio", "guasi", "rdma"]
        if v not in valid_engines:
            raise ValueError(f'无效的IO引擎，支持的引擎: {", ".join(valid_engines)}')
        return v
    
    @validator('block_size')
    def validate_block_size(cls, v):
        # 支持格式: 4k, 4K, 4096, 1M, 1G 等
        import re
        if not re.match(r'^\d+[kKmMgG]?$', v):
            raise ValueError('块大小格式无效，支持格式如: 4k, 4096, 1M')
        return v
    
    @validator('queue_depth')
    def validate_queue_depth(cls, v):
        if v < 1 or v > 1024:
            raise ValueError('队列深度必须在1-1024之间')
        return v
    
    @validator('io_size')
    def validate_io_size(cls, v):
        import re
        if not re.match(r'^\d+[kKmMgGtTpP]?$', v):
            raise ValueError('IO大小格式无效，支持格式如: 1G, 100M, 1024')
        return v
    
    @validator('runtime')
    def validate_runtime(cls, v):
        if v < 1 or v > 86400:  # 最大24小时
            raise ValueError('运行时间必须在1-86400秒之间')
        return v
    
    @validator('rw_mode')
    def validate_rw_mode(cls, v):
        valid_modes = ["read", "write", "randread", "randwrite", "rw", "randrw"]
        if v not in valid_modes:
            raise ValueError(f'无效的读写模式，支持的模式: {", ".join(valid_modes)}')
        return v
    
    @validator('rw_ratio')
    def validate_rw_ratio(cls, v):
        import re
        if not re.match(r'^\d+/\d+$', v):
            raise ValueError('读写比例格式无效，应为 读/写 格式，如: 50/50')
        
        parts = v.split('/')
        read_ratio = int(parts[0])
        write_ratio = int(parts[1])
        
        if read_ratio < 0 or read_ratio > 100 or write_ratio < 0 or write_ratio > 100:
            raise ValueError('读写比例必须在0-100之间')
        
        if read_ratio + write_ratio != 100:
            raise ValueError('读写比例之和必须为100')
        
        return v
    
    @validator('compression_ratio')
    def validate_compression_ratio(cls, v):
        if v < 0 or v > 1:
            raise ValueError('压缩比必须在0-1之间')
        return v
    
    @validator('numjobs')
    def validate_numjobs(cls, v):
        if v < 1 or v > 128:
            raise ValueError('作业数必须在1-128之间')
        return v

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseUpdate(BaseModel):
    case_name: Optional[str] = None
    description: Optional[str] = None
    io_engine: Optional[str] = None
    block_size: Optional[str] = None
    queue_depth: Optional[int] = None
    io_size: Optional[str] = None
    runtime: Optional[int] = None
    rw_mode: Optional[str] = None
    rw_ratio: Optional[str] = None
    compression_ratio: Optional[float] = None
    direct_io: Optional[bool] = None
    numjobs: Optional[int] = None
    time_based: Optional[bool] = None
    verify: Optional[str] = None
    verify_fatal: Optional[bool] = None
    group_reporting: Optional[bool] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None

class TestCaseResponse(TestCaseBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TestCaseListResponse(BaseModel):
    id: int
    case_name: str
    description: Optional[str] = None
    rw_mode: str
    io_size: str
    runtime: int
    created_by: Optional[int] = None
    is_public: bool
    is_template: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TestCaseTemplate(BaseModel):
    id: int
    case_name: str
    description: Optional[str] = None
    rw_mode: str
    is_template: bool
    
    class Config:
        from_attributes = True

class FIOCommandResponse(BaseModel):
    command: str
    case_name: str
    parameters: dict
    
    class Config:
        from_attributes = True