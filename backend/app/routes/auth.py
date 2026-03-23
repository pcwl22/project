from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..db import get_db
from ..models import User
import hashlib


router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
	username: str
	password: str


class RegisterRequest(BaseModel):
	username: str
	password: str
	confirmPassword: str
	captcha: str
	email: str = None
	security_question: str  # 必填
	security_answer: str    # 必填


class ForgotPasswordRequest(BaseModel):
	username: str


class ResetPasswordRequest(BaseModel):
	username: str
	security_answer: str
	new_password: str
	confirm_password: str


class LoginResponse(BaseModel):
	success: bool
	message: str
	user_id: int
	username: str
	is_admin: bool = False


class ForgotPasswordResponse(BaseModel):
	success: bool
	message: str
	security_question: str = None


def hash_password(password: str) -> str:
	"""简单的密码哈希（实际项目应使用更安全的方法）"""
	return hashlib.md5(password.encode()).hexdigest()


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
	user = db.query(User).filter(User.username == req.username).first()
	
	if not user:
		raise HTTPException(status_code=401, detail="用户名或密码错误")
	
	# 检查密码（支持明文和哈希两种方式）
	if user.password != req.password and user.password != hash_password(req.password):
		raise HTTPException(status_code=401, detail="用户名或密码错误")
	
	# 判断是否为管理员（简单规则：用户名包含admin）
	is_admin = "admin" in user.username.lower()
	
	return LoginResponse(
		success=True,
		message="登录成功",
		user_id=user.id,
		username=user.username,
		is_admin=is_admin
	)


@router.post("/register", response_model=LoginResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
	# 检查用户名是否已存在
	existing_user = db.query(User).filter(User.username == req.username).first()
	if existing_user:
		raise HTTPException(status_code=400, detail="用户名已存在")
	
	# 检查密码确认
	if req.password != req.confirmPassword:
		raise HTTPException(status_code=400, detail="两次输入密码不一致")
	
	# 验证安全问题和答案
	if not req.security_question or not req.security_question.strip():
		raise HTTPException(status_code=400, detail="请设置安全问题")
	
	if not req.security_answer or not req.security_answer.strip():
		raise HTTPException(status_code=400, detail="请设置安全答案")
	
	# 创建新用户
	new_user = User(
		username=req.username,
		password=req.password,  # 实际项目中应该哈希密码
		email=req.email,
		security_question=req.security_question.strip(),
		security_answer=req.security_answer.strip()
	)
	
	db.add(new_user)
	db.commit()
	db.refresh(new_user)
	
	# 判断是否为管理员
	is_admin = "admin" in new_user.username.lower()
	
	return LoginResponse(
		success=True,
		message="注册成功",
		user_id=new_user.id,
		username=new_user.username,
		is_admin=is_admin
	)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
	"""
	忘记密码 - 第一步：验证用户名并返回安全问题
	"""
	user = db.query(User).filter(User.username == req.username).first()
	
	if not user:
		raise HTTPException(status_code=404, detail="用户不存在")
	
	if not user.security_question or not user.security_answer:
		raise HTTPException(status_code=400, detail="该用户未设置安全问题，请联系管理员重置密码")
	
	return ForgotPasswordResponse(
		success=True,
		message="请回答安全问题",
		security_question=user.security_question
	)


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
	"""
	重置密码 - 第二步：验证安全答案并重置密码
	"""
	user = db.query(User).filter(User.username == req.username).first()
	
	if not user:
		raise HTTPException(status_code=404, detail="用户不存在")
	
	# 验证安全答案（不区分大小写）
	if user.security_answer.lower() != req.security_answer.lower():
		raise HTTPException(status_code=401, detail="安全答案错误")
	
	# 检查新密码确认
	if req.new_password != req.confirm_password:
		raise HTTPException(status_code=400, detail="两次输入密码不一致")
	
	# 更新密码
	user.password = req.new_password
	db.commit()
	
	return {
		"success": True,
		"message": "密码重置成功，请使用新密码登录"
	}
