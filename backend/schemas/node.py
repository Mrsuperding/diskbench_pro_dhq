from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class NodeBase(BaseModel):
    node_name: str
    host: str
    port: int = 22
    login_type: str = "password"
    username: str
    os_type: Optional[str] = None
    is_public: bool = False
    tool_path: Optional[str] = None
    
    @validator('node_name')
    def validate_node_name(cls, v):
        if len(v) < 1 or len(v) > 100:
            raise ValueError('节点名称长度必须在1-100个字符之间')
        return v
    
    @validator('host')
    def validate_host(cls, v):
        if len(v) < 1 or len(v) > 255:
            raise ValueError('主机地址长度必须在1-255个字符之间')
        return v
    
    @validator('port')
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('端口号必须在1-65535之间')
        return v
    
    @validator('login_type')
    def validate_login_type(cls, v):
        if v not in ["password", "key"]:
            raise ValueError('登录方式必须是password或key')
        return v

class NodeCreate(NodeBase):
    password: Optional[str] = None
    private_key: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v, values):
        login_type = values.get('login_type')
        if login_type == 'password' and not v:
            raise ValueError('密码登录方式必须提供密码')
        return v
    
    @validator('private_key')
    def validate_private_key(cls, v, values):
        login_type = values.get('login_type')
        if login_type == 'key' and not v:
            raise ValueError('密钥登录方式必须提供私钥')
        return v

class NodeUpdate(BaseModel):
    node_name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    os_type: Optional[str] = None
    is_public: Optional[bool] = None
    tool_path: Optional[str] = None

class NodeResponse(BaseModel):
    id: int
    node_name: str
    host: str
    port: int
    login_type: str
    username: str
    status: str
    os_type: Optional[str] = None
    cpu_info: Optional[str] = None
    memory_info: Optional[str] = None
    disk_info: Optional[str] = None
    created_by: Optional[int] = None
    is_public: bool
    tool_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    partitions: List[dict] = []
    
    class Config:
        from_attributes = True

class NodeListResponse(BaseModel):
    id: int
    node_name: str
    host: str
    port: int
    status: str
    os_type: Optional[str] = None
    cpu_info: Optional[str] = None
    memory_info: Optional[str] = None
    created_by: Optional[int] = None
    is_public: bool
    tool_path: Optional[str] = None
    created_at: datetime
    partition_count: int = 0
    
    class Config:
        from_attributes = True

class NodePartitionBase(BaseModel):
    partition_name: str
    mount_point: str
    filesystem: Optional[str] = None
    total_size: Optional[int] = None
    available_size: Optional[int] = None
    is_active: bool = True
    
    @validator('partition_name')
    def validate_partition_name(cls, v):
        if len(v) < 1 or len(v) > 100:
            raise ValueError('分区名称长度必须在1-100个字符之间')
        return v
    
    @validator('mount_point')
    def validate_mount_point(cls, v):
        if len(v) < 1 or len(v) > 255:
            raise ValueError('挂载点长度必须在1-255个字符之间')
        return v

class NodePartitionCreate(NodePartitionBase):
    pass

class NodePartitionUpdate(BaseModel):
    partition_name: Optional[str] = None
    mount_point: Optional[str] = None
    filesystem: Optional[str] = None
    total_size: Optional[int] = None
    available_size: Optional[int] = None
    is_active: Optional[bool] = None

class NodePartitionResponse(NodePartitionBase):
    id: int
    node_id: int
    created_at: datetime
    used_percentage: float = 0
    
    class Config:
        from_attributes = True

class NodeStatusUpdate(BaseModel):
    status: str
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ["online", "offline", "testing"]:
            raise ValueError('状态必须是online、offline或testing')
        return v

class NodeTestConnection(BaseModel):
    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    private_key: Optional[str] = None
    login_type: str = "password"
    
    @validator('login_type')
    def validate_login_type(cls, v):
        if v not in ["password", "key"]:
            raise ValueError('登录方式必须是password或key')
        return v