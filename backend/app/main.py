from fastapi import FastAPI
from .config import settings
from .routes.detections import router as detections_router
from .routes.auth import router as auth_router

app = FastAPI(title="Shelf Monitor API", version="0.1.0")

app.include_router(auth_router)
app.include_router(detections_router)


@app.get("/health")
def health_check():
	return {"status": "ok", "model_path": settings.yolo_weights}
