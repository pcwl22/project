from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..db import get_db
from ..models import User


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
	username: str
	password: str


class LoginResponse(BaseModel):
	success: bool
	message: str
	username: str = None


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
	user = db.query(User).filter(User.username == req.username).first()
	
	if not user:
		raise HTTPException(status_code=401, detail="用户名或密码错误")
	
	# 直接比对明文密码（实际项目应使用哈希）
	if user.password != req.password:
		raise HTTPException(status_code=401, detail="用户名或密码错误")
	
	return LoginResponse(
		success=True,
		message="登录成功",
		username=user.username
	)
