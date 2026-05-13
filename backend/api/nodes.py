from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import paramiko
import json

from core.database import get_db
from core.security import get_current_user, get_admin_user
from models.user import User
from models.node import Node, NodePartition
from schemas.node import (
    NodeCreate, 
    NodeUpdate, 
    NodeResponse, 
    NodeListResponse,
    NodePartitionCreate,
    NodePartitionUpdate,
    NodePartitionResponse,
    NodeStatusUpdate,
    NodeTestConnection
)
from services.ssh_service import SSHService

router = APIRouter()

@router.get("/", response_model=List[NodeListResponse])
async def get_nodes(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取节点列表"""
    query = db.query(Node)
    
    # 普通用户只能看到自己的节点和公开节点
    if current_user.role != "admin":
        query = query.filter(
            (Node.created_by == current_user.id) | (Node.is_public == True)
        )
    
    # 状态筛选
    if status_filter:
        query = query.filter(Node.status == status_filter)
    
    nodes = query.offset(skip).limit(limit).all()
    
    # 添加分区数量信息
    result = []
    for node in nodes:
        partition_count = db.query(NodePartition).filter(
            NodePartition.node_id == node.id
        ).count()
        
        node_data = {
            **node.to_dict(),
            "partition_count": partition_count
        }
        result.append(node_data)
    
    return result

@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取节点详情"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id and not node.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此节点"
        )
    
    return node.to_dict()

@router.post("/", response_model=NodeResponse)
async def create_node(
    node_data: NodeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建节点"""
    # 检查节点名称是否已存在
    if db.query(Node).filter(Node.node_name == node_data.node_name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="节点名称已存在"
        )
    
    # 创建节点
    db_node = Node(
        node_name=node_data.node_name,
        host=node_data.host,
        port=node_data.port,
        login_type=node_data.login_type,
        username=node_data.username,
        password=node_data.password,
        private_key=node_data.private_key,
        os_type=node_data.os_type,
        created_by=current_user.id,
        is_public=node_data.is_public
    )
    
    db.add(db_node)
    db.commit()
    db.refresh(db_node)

    return db_node.to_dict()

@router.put("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: int,
    node_update: NodeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新节点"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此节点"
        )
    
    # 更新字段
    update_data = node_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(node, field, value)
    
    db.commit()
    db.refresh(node)

    return node.to_dict()

@router.delete("/{node_id}")
async def delete_node(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除节点"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此节点"
        )
    
    db.delete(node)
    db.commit()
    
    return {"message": "节点删除成功"}

@router.post("/{node_id}/test-connection")
async def test_node_connection(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """测试节点连接"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id and not node.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权测试此节点"
        )
    
    try:
        ssh_service = SSHService()
        is_connected = await ssh_service.test_connection(
            host=node.host,
            port=node.port,
            username=node.username,
            password=node.password,
            private_key=node.private_key
        )
        
        if is_connected:
            # 更新节点状态为在线
            node.status = "online"
            db.commit()
            
            # 获取系统信息
            system_info = await ssh_service.get_system_info()
            
            return {
                "message": "连接成功",
                "status": "online",
                "system_info": system_info
            }
        else:
            node.status = "offline"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="连接失败"
            )
            
    except Exception as e:
        node.status = "offline"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"连接失败: {str(e)}"
        )

@router.post("/test-connection")
async def test_connection(
    conn_data: NodeTestConnection,
    current_user: User = Depends(get_current_user)
):
    """测试连接（不保存节点）"""
    try:
        ssh_service = SSHService()
        is_connected = await ssh_service.test_connection(
            host=conn_data.host,
            port=conn_data.port,
            username=conn_data.username,
            password=conn_data.password,
            private_key=conn_data.private_key
        )
        
        if is_connected:
            system_info = await ssh_service.get_system_info()
            return {
                "message": "连接成功",
                "status": "success",
                "system_info": system_info
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="连接失败"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"连接失败: {str(e)}"
        )

@router.put("/{node_id}/status")
async def update_node_status(
    node_id: int,
    status_update: NodeStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新节点状态"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此节点状态"
        )
    
    node.status = status_update.status
    db.commit()
    
    return {"message": "节点状态更新成功"}

# 节点分区管理
@router.get("/{node_id}/partitions", response_model=List[NodePartitionResponse])
async def get_node_partitions(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取节点分区列表"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id and not node.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此节点"
        )
    
    partitions = db.query(NodePartition).filter(
        NodePartition.node_id == node_id
    ).all()
    
    return partitions

@router.post("/{node_id}/partitions", response_model=NodePartitionResponse)
async def create_node_partition(
    node_id: int,
    partition_data: NodePartitionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建节点分区"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此节点"
        )
    
    # 检查分区名称是否已存在
    if db.query(NodePartition).filter(
        NodePartition.node_id == node_id,
        NodePartition.partition_name == partition_data.partition_name
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分区名称已存在"
        )
    
    db_partition = NodePartition(
        node_id=node_id,
        **partition_data.dict()
    )
    
    db.add(db_partition)
    db.commit()
    db.refresh(db_partition)
    
    return db_partition

@router.put("/{node_id}/partitions/{partition_id}", response_model=NodePartitionResponse)
async def update_node_partition(
    node_id: int,
    partition_id: int,
    partition_update: NodePartitionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新节点分区"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    partition = db.query(NodePartition).filter(
        NodePartition.id == partition_id,
        NodePartition.node_id == node_id
    ).first()
    
    if not partition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分区不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此节点"
        )
    
    # 更新字段
    update_data = partition_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(partition, field, value)
    
    db.commit()
    db.refresh(partition)
    
    return partition

@router.delete("/{node_id}/partitions/{partition_id}")
async def delete_node_partition(
    node_id: int,
    partition_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除节点分区"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    partition = db.query(NodePartition).filter(
        NodePartition.id == partition_id,
        NodePartition.node_id == node_id
    ).first()
    
    if not partition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分区不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此节点"
        )
    
    db.delete(partition)
    db.commit()
    
    return {"message": "分区删除成功"}

@router.post("/{node_id}/sync-partitions")
async def sync_node_partitions(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """同步节点分区信息"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id and not node.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此节点"
        )
    
    try:
        ssh_service = SSHService()
        is_connected = await ssh_service.test_connection(
            host=node.host,
            port=node.port,
            username=node.username,
            password=node.password,
            private_key=node.private_key
        )
        
        if not is_connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法连接到节点"
            )
        
        # 获取分区信息
        partitions_info = await ssh_service.get_disk_partitions()
        
        # 删除现有分区信息
        db.query(NodePartition).filter(NodePartition.node_id == node_id).delete()
        
        # 添加新的分区信息
        for partition_info in partitions_info:
            db_partition = NodePartition(
                node_id=node_id,
                partition_name=partition_info.get('device', 'unknown'),
                mount_point=partition_info.get('mountpoint', ''),
                filesystem=partition_info.get('fstype', ''),
                total_size=partition_info.get('total_size_mb', 0),
                available_size=partition_info.get('available_size_mb', 0)
            )
            db.add(db_partition)
        
        db.commit()
        
        return {
            "message": "分区信息同步成功",
            "partitions_count": len(partitions_info)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"同步失败: {str(e)}"
        )

@router.post("/{node_id}/upload-tools")
async def upload_tools(
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传工具到节点"""
    from fastapi import UploadFile, File
    import os
    import tempfile

    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )

    # 权限检查
    if current_user.role != "admin" and node.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此节点"
        )

    # 如果没有设置 tool_path，返回错误
    if not node.tool_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先在节点配置中设置工具目录路径 (tool_path)"
        )

    try:
        ssh_service = SSHService()
        is_connected = await ssh_service.connect(
            host=node.host,
            port=node.port,
            username=node.username,
            password=node.password,
            private_key=node.private_key
        )

        if not is_connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法连接到节点"
            )

        # 确保远程工具目录存在
        await ssh_service.ensure_dir_exists(node.tool_path)

        return {
            "message": "工具上传功能已就绪，请使用文件上传接口",
            "tool_path": node.tool_path
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"连接失败: {str(e)}"
        )
    finally:
        ssh_service.close()


@router.post("/{node_id}/upload-tool-bundle")
async def upload_tool_bundle(
    node_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传工具包到节点（支持包含 fio 和依赖库的压缩包）
    压缩包格式：.tar.gz, .tgz, .zip
    自动解压到节点的 tool_path 目录
    """
    import os
    import tempfile
    import tarfile
    import zipfile
    import shutil

    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="节点不存在")

    if current_user.role != "admin" and node.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此节点")

    if not node.tool_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先在节点配置中设置工具目录路径 (tool_path)"
        )

    try:
        ssh_service = SSHService()
        if not await ssh_service.connect(
            host=node.host, port=node.port,
            username=node.username, password=node.password,
            private_key=node.private_key, tool_path=node.tool_path
        ):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法连接到节点")

        # 确保远程目录存在
        await ssh_service.ensure_dir_exists(node.tool_path)

        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # 解压到临时目录
            extract_dir = tempfile.mkdtemp()
            if file.filename.endswith(('.tar.gz', '.tgz')):
                with tarfile.open(tmp_path, 'r:gz') as tar:
                    tar.extractall(extract_dir)
            elif file.filename.endswith('.zip'):
                with zipfile.ZipFile(tmp_path, 'r') as zf:
                    zf.extractall(extract_dir)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不支持的压缩格式，请使用 .tar.gz, .tgz 或 .zip")

            # 递归上传到远程
            success = await ssh_service.upload_dir(extract_dir, node.tool_path)
            if not success:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="上传失败")

            # 尝试配置 LD_LIBRARY_PATH
            await ssh_service.configure_ld_library_path()

            return {
                "message": "工具包上传并解压成功",
                "tool_path": node.tool_path,
                "file": file.filename
            }
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)
            os.unlink(tmp_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"上传失败: {str(e)}")
    finally:
        ssh_service.close()


@router.post("/{node_id}/upload-libs")
async def upload_libs(
    node_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传依赖库文件到节点的 lib 目录
    用于离线环境上传 libaio.so.1 等库文件
    """
    import os
    import tempfile

    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="节点不存在")

    if current_user.role != "admin" and node.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此节点")

    if not node.tool_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先在节点配置中设置工具目录路径 (tool_path)"
        )

    try:
        ssh_service = SSHService()
        if not await ssh_service.connect(
            host=node.host, port=node.port,
            username=node.username, password=node.password,
            private_key=node.private_key, tool_path=node.tool_path
        ):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法连接到节点")

        # 创建 lib 子目录
        lib_dir = os.path.join(node.tool_path, "lib")
        await ssh_service.ensure_dir_exists(lib_dir)

        uploaded = []
        for file in files:
            if not file.filename.endswith('.so'):
                continue  # 跳过非库文件

            # 保存到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.so') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                remote_path = os.path.join(lib_dir, os.path.basename(file.filename))
                success = await ssh_service.upload_file(tmp_path, remote_path)
                if success:
                    uploaded.append(file.filename)
                    # 设置可执行权限
                    await ssh_service.execute_command(f"chmod 755 {remote_path}", timeout=10)
            finally:
                os.unlink(tmp_path)

        # 配置 LD_LIBRARY_PATH
        await ssh_service.configure_ld_library_path()

        return {
            "message": f"成功上传 {len(uploaded)} 个库文件",
            "uploaded": uploaded,
            "lib_path": lib_dir
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"上传失败: {str(e)}")
    finally:
        ssh_service.close()
