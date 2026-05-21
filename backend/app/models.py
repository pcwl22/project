from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
from .db import Base


# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def get_beijing_time():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String(64), unique=True, nullable=False, index=True)
	password = Column(String(255), nullable=False)
	email = Column(String(255), nullable=True)  # 邮箱（可选）
	security_question = Column(String(255), nullable=True)  # 安全问题
	security_answer = Column(String(255), nullable=True)  # 安全答案
	created_at = Column(DateTime, default=get_beijing_time, nullable=False)


class DetectionResult(Base):
	__tablename__ = "detection_results"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # 关联用户
	image_path = Column(String(512), nullable=False)  # 原始文件路径（图片或视频）
	saved_image_path = Column(String(512), nullable=True)  # 处理后的文件路径
	file_type = Column(String(20), default="image", nullable=False)  # "image" 或 "video" 或 "camera"
	max_empty_count = Column(Integer, default=0, nullable=False)  # 视频/摄像头检测时的空货架最大值
	created_at = Column(DateTime, default=get_beijing_time, nullable=False)

	user = relationship("User", backref="detection_results")  # 关联到用户
	detections = relationship("DetectionBox", back_populates="result", cascade="all, delete-orphan")


class DetectionBox(Base):
	__tablename__ = "detection_boxes"

	id = Column(Integer, primary_key=True, index=True)
	result_id = Column(Integer, ForeignKey("detection_results.id", ondelete="CASCADE"), nullable=False)
	cls_name = Column(String(64), nullable=False)
	x1 = Column(Float, nullable=False)
	y1 = Column(Float, nullable=False)
	x2 = Column(Float, nullable=False)
	y2 = Column(Float, nullable=False)
	score = Column(Float, nullable=False)
	extra = Column(Text, nullable=True)

	result = relationship("DetectionResult", back_populates="detections")
