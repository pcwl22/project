import os
from pydantic import BaseModel


class Settings(BaseModel):
	# MySQL 数据库配置
	database_url: str = os.getenv("DATABASE_URL", "mysql+pymysql://root:202217@localhost:3306/ultralytics_auth")

	# YOLO 模型权重路径
	yolo_weights: str = os.getenv(
		"YOLO_WEIGHTS",
		r"E:\\bysj\\ultralytics-8.2.27\\runs\\detect\\best.pt",
	)

	# 检测结果输出目录
	output_dir: str = os.getenv(
		"OUTPUT_DIR",
		r"E:\\bysj\\ultralytics-8.2.27\\test\\api",
	)

	# 空货架检测算法参数
	gap_threshold: float = 0.5  # 间隙阈值：商品宽度的倍数
	row_threshold: float = 0.6  # 行聚类阈值：商品高度的倍数
	min_gap_pixels: int = 20    # 最小间隙像素
	edge_detection: bool = True  # 是否检测货架边缘空位
	min_products_per_row: int = 2  # 每行最少商品数才进行空位检测


settings = Settings()