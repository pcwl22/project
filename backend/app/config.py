import os
from pydantic import BaseModel


class Settings(BaseModel):
	# MySQL 数据库配置
	database_url: str = os.getenv("DATABASE_URL", "mysql+pymysql://root:202217@localhost:3306/ultralytics_auth")

	# YOLO 模型权重路径
	yolo_weights: str = os.getenv(
		"YOLO_WEIGHTS",
		r"E:\bysj\ultralytics-8.2.27\runs\best.pt",
	)
	
	# 模型存储目录（用于上传的模型）
	model_dir: str = os.getenv(
		"MODEL_DIR",
		r"E:\bysj\ultralytics-8.2.27\runs",
	)

	# 检测结果输出目录
	output_dir: str = os.getenv(
		"OUTPUT_DIR",
		r"E:\bysj\ultralytics-8.2.27\test",
	)
	
	# 分类存储目录
	image_output_dir: str = os.path.join(output_dir, "照片")
	video_output_dir: str = os.path.join(output_dir, "视频")
	camera_output_dir: str = os.path.join(output_dir, "摄像头")

	# 空货架检测算法参数
	enable_empty_detection: bool = True  # 是否启用空货架检测
	gap_threshold: float = 0.5  # 间隙阈值：商品宽度的倍数
	row_threshold: float = 0.6  # 行聚类阈值：商品高度的倍数
	min_gap_pixels: int = 20    # 最小间隙像素
	edge_detection: bool = True  # 是否检测货架边缘空位
	min_products_per_row: int = 2  # 每行最少商品数才进行空位检测
	black_edge_threshold: int = 30  # 黑边检测阈值：平均亮度低于此值认为是黑边（0-255）
	
	# 检测参数（用户可调整）
	default_conf_threshold: float = 0.25  # 默认置信度阈值
	default_iou_threshold: float = 0.45   # 默认IOU阈值
	
	# 视频检测性能优化参数
	video_skip_frames: int = 4  # 跳帧间隔（每N帧检测一次，建议 3-5）
	video_process_width: int = 640  # 处理分辨率宽度（建议 640 或 1280）
	video_direct_draw: bool = True  # 直接绘制检测框（不使用半透明效果）
	video_use_gpu: bool = True  # 是否尝试使用 GPU 加速（如果可用）
	video_enable_ffmpeg: bool = False  # 是否使用 FFmpeg 二次编码（提高兼容性但增加时间）


settings = Settings()