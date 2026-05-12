from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class TaskBase(BaseModel):
    task_name: str
    description: Optional[str] = None
    test_case_id: int
    is_public: bool = False
    
    @validator('task_name')
    def validate_task_name(cls, v):
        if len(v) < 1 or len(v) > 200:
            raise ValueError('任务名称长度必须在1-200个字符之间')
        return v

class TaskCreate(TaskBase):
    node_ids: List[int]  # 节点ID列表
    partition_mappings: Dict[int, int] = Field(default_factory=dict)  # 节点ID到分区ID的映射

class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class TaskResponse(TaskBase):
    id: int
    status: str
    created_by: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int
    total_io_ops: int
    avg_iops: float
    avg_latency: float
    avg_bw: float
    created_at: datetime
    updated_at: datetime
    test_case: Optional[Dict[str, Any]] = None
    task_nodes: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True

class TaskListResponse(BaseModel):
    id: int
    task_name: str
    status: str
    created_by: int
    test_case_name: str
    node_count: int
    is_public: bool
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int
    avg_iops: float
    avg_latency: float
    avg_bw: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class TaskNodeBase(BaseModel):
    node_id: int
    partition_id: Optional[int] = None
    partition_path: Optional[str] = None  # 逗号分隔的分区路径

class TaskNodeCreate(TaskNodeBase):
    pass

class TaskNodeUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None

class TaskNodeResponse(TaskNodeBase):
    id: int
    task_id: int
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int
    io_ops: int
    iops: float
    latency: float
    bandwidth: float
    error_message: Optional[str] = None
    created_at: datetime
    node: Optional[Dict[str, Any]] = None
    partition: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class TaskStatusUpdate(BaseModel):
    status: str
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ["pending", "running", "completed", "failed", "cancelled"]:
            raise ValueError('状态必须是pending、running、completed、failed或cancelled')
        return v

class TaskNodeStatusUpdate(BaseModel):
    status: str
    error_message: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ["pending", "running", "completed", "failed", "cancelled"]:
            raise ValueError('状态必须是pending、running、completed、failed或cancelled')
        return v

class IOPerformanceDataCreate(BaseModel):
    iops: float
    bandwidth: float
    latency: float
    read_iops: Optional[float] = 0
    write_iops: Optional[float] = 0
    read_bw: Optional[float] = 0
    write_bw: Optional[float] = 0
    read_lat: Optional[float] = 0
    write_lat: Optional[float] = 0
    cpu_usage: Optional[float] = 0
    memory_usage: Optional[float] = 0

class IOPerformanceDataResponse(IOPerformanceDataCreate):
    id: int
    task_node_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class IOStatDataCreate(BaseModel):
    device: str
    tps: float
    kB_read_s: float
    kB_wrtn_s: float
    kB_dscd_s: Optional[float] = 0
    kB_read: Optional[int] = 0
    kB_wrtn: Optional[int] = 0
    kB_dscd: Optional[int] = 0
    rqmps: Optional[float] = 0
    await_time: Optional[float] = 0
    aqu_sz: Optional[float] = 0
    util: Optional[float] = 0

class IOStatDataResponse(IOStatDataCreate):
    id: int
    task_node_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class TaskLogCreate(BaseModel):
    log_level: str = "info"
    message: str
    source: Optional[str] = None
    
    @validator('log_level')
    def validate_log_level(cls, v):
        if v not in ["debug", "info", "warning", "error"]:
            raise ValueError('日志级别必须是debug、info、warning或error')
        return v

class TaskLogResponse(TaskLogCreate):
    id: int
    task_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TaskCloneRequest(BaseModel):
    new_name: str
    
    @validator('new_name')
    def validate_new_name(cls, v):
        if len(v) < 1 or len(v) > 200:
            raise ValueError('新任务名称长度必须在1-200个字符之间')
        return v

class TaskStatistics(BaseModel):
    total_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_duration: float
    total_io_ops: int

    class Config:
        from_attributes = True


# ============== TaskNodePartition Schemas ==============

class TaskNodePartitionBase(BaseModel):
    task_id: int
    node_id: int
    partition_id: int
    capacity_limit: int = 0


class TaskNodePartitionCreate(TaskNodePartitionBase):
    pass


class TaskNodePartitionUpdate(BaseModel):
    capacity_limit: Optional[int] = None
    init_status: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None


class TaskNodePartitionResponse(TaskNodePartitionBase):
    id: int
    init_status: str
    init_start_time: Optional[datetime] = None
    init_end_time: Optional[datetime] = None
    init_error: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int
    io_ops: int
    iops: float
    latency: float
    bandwidth: float
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    node: Optional[Dict[str, Any]] = None
    partition: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ============== Baseline Schemas ==============

class BaselineMetricBase(BaseModel):
    metric_name: str
    value: float
    unit: Optional[str] = None


class BaselineMetricCreate(BaselineMetricBase):
    baseline_id: int


class BaselineMetricResponse(BaselineMetricBase):
    id: int
    baseline_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BaselineBase(BaseModel):
    name: str
    description: Optional[str] = None
    test_type: Optional[str] = None
    block_size: Optional[str] = None
    config_json: Optional[str] = None
    is_active: bool = True


class BaselineCreate(BaselineBase):
    pass


class BaselineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    test_type: Optional[str] = None
    block_size: Optional[str] = None
    config_json: Optional[str] = None
    is_active: Optional[bool] = None


class BaselineResponse(BaselineBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    metrics: List[BaselineMetricResponse] = []

    class Config:
        from_attributes = True


# ============== TestResultPercentile Schemas ==============

class TestResultPercentileBase(BaseModel):
    task_node_id: int
    percentile_name: str
    latency_us: float
    test_type: Optional[str] = None


class TestResultPercentileCreate(TestResultPercentileBase):
    pass


class TestResultPercentileResponse(TestResultPercentileBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True