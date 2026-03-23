from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..db import get_db
from ..models import User, DetectionResult
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/api/admin", tags=["admin"])


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_admin: bool
    detection_count: int
    created_at: datetime

    class Config:
        from_attributes = True


def verify_admin(is_admin: bool = Query(...)):
    """验证管理员权限"""
    if not is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return True


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """
    获取所有用户列表（仅管理员）
    """
    # 查询所有用户
    users = db.query(User).all()
    
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': 'admin' in user.username.lower(),
            'detection_count': 0,  # 暂时设为0，因为 detection_results 表没有 user_id
            'created_at': user.created_at
        })
    
    return result


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """
    删除用户（仅管理员，不能删除管理员账号）
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查是否为管理员账号
    if 'admin' in user.username.lower():
        raise HTTPException(status_code=403, detail="不能删除管理员账号")
    
    # 删除用户（级联删除相关的检测记录）
    db.delete(user)
    db.commit()
    
    return {"success": True, "message": f"用户 {user.username} 已删除"}


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """
    获取系统统计信息（仅管理员）
    """
    total_users = db.query(func.count(User.id)).scalar()
    total_detections = db.query(func.count(DetectionResult.id)).scalar()
    
    return {
        "total_users": total_users,
        "total_detections": total_detections
    }
