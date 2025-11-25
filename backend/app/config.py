import os
from pydantic import BaseModel


class Settings(BaseModel):
	# MySQL DSN example: mysql+pymysql://user:password@localhost:3306/ultralytics_auth
	database_url: str = os.getenv("DATABASE_URL", "mysql+pymysql://root:202217@localhost:3306/ultralytics_auth")

	# YOLO model weights
	yolo_weights: str = os.getenv(
		"YOLO_WEIGHTS",
		r"E:\\bysj\\ultralytics-8.2.27\\runs\\detect\\huojia\\train\\weights\\best.pt",
	)

	# Directory to save annotated images and JSON outputs
	output_dir: str = os.getenv(
		"OUTPUT_DIR",
		r"E:\\bysj\\ultralytics-8.2.27\\test\\api",
	)


settings = Settings()
