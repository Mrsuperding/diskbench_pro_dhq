# -*- coding: utf-8 -*-
"""
管理后台接口
- 用户管理
- 系统配置热重载
- 数据库维护命令
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List

from core.database import get_db as get_session   # 名字统一
from models.user import User
from sqlalchemy.orm import Session

router = APIRouter(tags=["admin"], prefix="/admin")


# -------------------- 请求/响应 --------------------
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_superuser: bool

    class Config:
        orm_mode = True


class ToggleOut(BaseModel):
    ok: bool


# -------------------- 依赖：简单鉴权 --------------------
def must_admin(sess: Session = Depends(get_session)):
    """TODO：接入真实 JWT，这里先硬编码一个超级用户 id=1"""
    admin = sess.query(User).filter_by(id=1).first()
    if not admin or not admin.is_superuser:
        raise HTTPException(403, "需要管理员权限")
    return admin


# -------------------- 接口 --------------------
@router.get("/users", response_model=List[UserOut], summary="用户列表")
def list_users(sess: Session = Depends(get_session), _=Depends(must_admin)):
    return sess.query(User).all()


@router.post("/user/{user_id}/toggle", response_model=ToggleOut, summary="切换超级用户")
def toggle_super(
    user_id: int,
    sess: Session = Depends(get_session),
    _=Depends(must_admin),
):
    user = sess.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.is_superuser = not user.is_superuser
    sess.commit()
    return ToggleOut(ok=True)


@router.post("/reload_config", summary="热重载配置文件（示例）")
def reload_config(_=Depends(must_admin)):
    # 这里可以发信号给 config.py 重新加载 yaml
    return {"ok": True, "msg": "配置已热重载（伪）"}