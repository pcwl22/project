import os
from typing import List, Tuple
import cv2
import numpy as np
from ultralytics import YOLO
from ..config import settings


class YoloService:
	_model = None

	@classmethod
	def load_model(cls):
		if cls._model is None:
			cls._model = YOLO(settings.yolo_weights)
		return cls._model

	@classmethod
	def predict_on_image(cls, image_path: str, save_dir: str) -> Tuple[str, List[Tuple[str, float, float, float, float, float]]]:
		model = cls.load_model()
		os.makedirs(save_dir, exist_ok=True)
		results = model.predict(source=image_path, conf=0.25, iou=0.45, save=False, verbose=False)
		if not results:
			raise ValueError("No result returned by model")

		r = results[0]
		img = r.orig_img
		boxes = r.boxes.xyxy.cpu().numpy()
		scores = r.boxes.conf.cpu().numpy()
		classes = r.boxes.cls.cpu().numpy()
		names = model.names

		# draw
		overlay = img.copy()
		for box, score, cls_idx in zip(boxes, scores, classes):
			x1, y1, x2, y2 = map(int, box)
			cls_idx_i = int(cls_idx)
			color = (0, 255, 0) if cls_idx_i == 0 else ((0, 0, 255) if cls_idx_i == 1 else (255, 255, 0))
			cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
			label = f"{names[cls_idx_i]} {float(score):.2f}"
			(tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
			cv2.rectangle(overlay, (x1, y1 - th - 4), (x1 + tw, y1), color, -1)
			cv2.putText(overlay, label, (x1, y1 - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
		vis_img = cv2.addWeighted(overlay, 0.4, img, 0.6, 0)

		img_name = os.path.basename(getattr(r, "path", image_path))
		save_path = os.path.join(save_dir, img_name)
		cv2.imwrite(save_path, vis_img)

		out = []
		for b, s, c in zip(boxes, scores, classes):
			cls_name = names[int(c)]
			x1, y1, x2, y2 = map(float, b.tolist())
			out.append((cls_name, x1, y1, x2, y2, float(s)))
		return save_path, out

