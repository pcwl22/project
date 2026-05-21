from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .routes.detections import router as detections_router
from .routes.auth import router as auth_router
from .routes.admin import router as admin_router
from .routes.config import router as config_router
import os

app = FastAPI(title="Shelf Monitor API", version="0.1.0")

# 添加 CORS 中间件
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# 添加静态文件服务（支持多个目录）
# 注意：更具体的路径要先挂载，否则会被通用路径拦截
if os.path.exists(settings.image_output_dir):
	app.mount("/static/照片", StaticFiles(directory=settings.image_output_dir), name="static_image")

if os.path.exists(settings.video_output_dir):
	app.mount("/static/视频", StaticFiles(directory=settings.video_output_dir), name="static_video")

if os.path.exists(settings.camera_output_dir):
	app.mount("/static/摄像头", StaticFiles(directory=settings.camera_output_dir), name="static_camera")

# 兼容旧路径（放在最后，避免拦截具体路径）
if os.path.exists(settings.output_dir):
	app.mount("/static", StaticFiles(directory=settings.output_dir), name="static")

app.include_router(auth_router)
app.include_router(detections_router)
app.include_router(admin_router)
app.include_router(config_router)


@app.get("/health")
def health_check():
	return {"status": "ok", "model_path": settings.yolo_weights}
