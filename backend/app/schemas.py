from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DetectionBoxOut(BaseModel):
	id: int
	cls_name: str
	x1: float
	y1: float
	x2: float
	y2: float
	score: float

	class Config:
		from_attributes = True


class DetectionResultOut(BaseModel):
	id: int
	image_path: str
	saved_image_path: Optional[str]
	created_at: datetime
	detections: List[DetectionBoxOut]

	class Config:
		from_attributes = True
