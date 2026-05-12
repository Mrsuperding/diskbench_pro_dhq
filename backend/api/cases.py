from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.security import get_current_user, get_admin_user
from models.user import User
from models.case import TestCase
from schemas.case import (
    TestCaseCreate, 
    TestCaseUpdate, 
    TestCaseResponse, 
    TestCaseListResponse,
    TestCaseTemplate,
    FIOCommandResponse
)

router = APIRouter()

@router.get("/", response_model=List[TestCaseListResponse])
async def get_test_cases(
    skip: int = 0,
    limit: int = 100,
    template_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取测试用例列表"""
    query = db.query(TestCase)
    
    # 普通用户只能看到自己的用例和公开用例
    if current_user.role != "admin":
        query = query.filter(
            (TestCase.created_by == current_user.id) | (TestCase.is_public == True)
        )
    
    # 模板筛选
    if template_only:
        query = query.filter(TestCase.is_template == True)
    
    test_cases = query.offset(skip).limit(limit).all()
    return test_cases

@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_test_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取测试用例详情"""
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试用例不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and test_case.created_by != current_user.id and not test_case.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此测试用例"
        )
    
    return test_case

@router.post("/", response_model=TestCaseResponse)
async def create_test_case(
    case_data: TestCaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建测试用例"""
    # 检查用例名称是否已存在
    if db.query(TestCase).filter(TestCase.case_name == case_data.case_name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用例名称已存在"
        )
    
    # 创建测试用例
    db_case = TestCase(
        **case_data.dict(),
        created_by=current_user.id
    )
    
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    
    return db_case

@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_test_case(
    case_id: int,
    case_update: TestCaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新测试用例"""
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试用例不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and test_case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此测试用例"
        )
    
    # 检查名称冲突（如果修改了名称）
    if case_update.case_name and case_update.case_name != test_case.case_name:
        if db.query(TestCase).filter(TestCase.case_name == case_update.case_name).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用例名称已存在"
            )
    
    # 更新字段
    update_data = case_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(test_case, field, value)
    
    db.commit()
    db.refresh(test_case)
    
    return test_case

@router.delete("/{case_id}")
async def delete_test_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除测试用例"""
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试用例不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and test_case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此测试用例"
        )
    
    db.delete(test_case)
    db.commit()
    
    return {"message": "测试用例删除成功"}

@router.get("/{case_id}/fio-command", response_model=FIOCommandResponse)
async def get_fio_command(
    case_id: int,
    filename: Optional[str] = "testfile",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取FIO命令"""
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试用例不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and test_case.created_by != current_user.id and not test_case.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此测试用例"
        )
    
    command = test_case.generate_fio_command(filename)
    
    return FIOCommandResponse(
        command=command,
        case_name=test_case.case_name,
        parameters=test_case.to_dict()
    )

@router.post("/{case_id}/clone", response_model=TestCaseResponse)
async def clone_test_case(
    case_id: int,
    new_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """克隆测试用例"""
    original_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not original_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试用例不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and original_case.created_by != current_user.id and not original_case.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此测试用例"
        )
    
    # 检查新名称是否已存在
    if db.query(TestCase).filter(TestCase.case_name == new_name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用例名称已存在"
        )
    
    # 创建克隆用例
    cloned_case = TestCase(
        case_name=new_name,
        description=f"克隆自: {original_case.case_name}\n{original_case.description or ''}",
        io_engine=original_case.io_engine,
        block_size=original_case.block_size,
        queue_depth=original_case.queue_depth,
        io_size=original_case.io_size,
        runtime=original_case.runtime,
        rw_mode=original_case.rw_mode,
        rw_ratio=original_case.rw_ratio,
        compression_ratio=original_case.compression_ratio,
        direct_io=original_case.direct_io,
        numjobs=original_case.numjobs,
        time_based=original_case.time_based,
        verify=original_case.verify,
        verify_fatal=original_case.verify_fatal,
        group_reporting=original_case.group_reporting,
        created_by=current_user.id,
        is_public=False,
        is_template=False
    )
    
    db.add(cloned_case)
    db.commit()
    db.refresh(cloned_case)
    
    return cloned_case

@router.get("/templates/", response_model=List[TestCaseTemplate])
async def get_case_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用例模板"""
    query = db.query(TestCase).filter(TestCase.is_template == True)
    
    # 普通用户只能看到公开模板
    if current_user.role != "admin":
        query = query.filter(TestCase.is_public == True)
    
    templates = query.all()
    return templates

@router.post("/{case_id}/set-template")
async def set_as_template(
    case_id: int,
    is_template: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """设置用例为模板"""
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试用例不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and test_case.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此测试用例"
        )
    
    test_case.is_template = is_template
    db.commit()
    
    return {"message": f"已{'设置' if is_template else '取消'}模板标记"}

@router.get("/search/")
async def search_test_cases(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索测试用例"""
    search_query = db.query(TestCase).filter(
        TestCase.case_name.contains(query) | 
        TestCase.description.contains(query)
    )
    
    # 普通用户只能搜索自己的用例和公开用例
    if current_user.role != "admin":
        search_query = search_query.filter(
            (TestCase.created_by == current_user.id) | (TestCase.is_public == True)
        )
    
    results = search_query.limit(limit).all()
    return results