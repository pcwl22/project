import os
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, Base, engine
from ..models import DetectionResult, DetectionBox
from ..schemas import DetectionResultOut
from ..services.yolo_service import YoloService
from ..config import settings


# Ensure tables exist
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/detections", tags=["detections"])


@router.post("/upload", response_model=DetectionResultOut)
def upload_and_detect(file: UploadFile = File(...), db: Session = Depends(get_db)):
	if not file.content_type or not file.content_type.startswith("image/"):
		raise HTTPException(status_code=400, detail="Only image uploads are supported")

	os.makedirs(settings.output_dir, exist_ok=True)
	src_path = os.path.join(settings.output_dir, file.filename)
	with open(src_path, "wb") as f:
		f.write(file.file.read())

	annotated_path, boxes = YoloService.predict_on_image(src_path, settings.output_dir)

	result = DetectionResult(image_path=src_path, saved_image_path=annotated_path)
	db.add(result)
	db.flush()

	for cls_name, x1, y1, x2, y2, score in boxes:
		box = DetectionBox(
			result_id=result.id,
			cls_name=cls_name,
			x1=x1,
			y1=y1,
			x2=x2,
			y2=y2,
			score=score,
		)
		db.add(box)

	db.commit()
	db.refresh(result)
	return result


@router.get("/", response_model=List[DetectionResultOut])
def list_detections(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
	results = db.query(DetectionResult).order_by(DetectionResult.id.desc()).limit(limit).offset(offset).all()
	return results


@router.get("/{result_id}", response_model=DetectionResultOut)
def get_detection(result_id: int, db: Session = Depends(get_db)):
	result = db.query(DetectionResult).filter(DetectionResult.id == result_id).first()
	if not result:
		raise HTTPException(status_code=404, detail="Result not found")
	return result
