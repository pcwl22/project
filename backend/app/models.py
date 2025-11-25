from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
	__tablename__ = "users"

	id = Column(Integer, primary_key=True, index=True)
	username = Column(String(64), unique=True, nullable=False, index=True)
	password = Column(String(255), nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DetectionResult(Base):
	__tablename__ = "detection_results"

	id = Column(Integer, primary_key=True, index=True)
	image_path = Column(String(512), nullable=False)
	saved_image_path = Column(String(512), nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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
