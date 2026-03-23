from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO
from PIL import Image, ImageDraw
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, LargeBinary, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, relationship
import numpy as np
import io, os, shutil

# ===============================
# 配置
# ===============================
DB_URL = "mysql+pymysql://root:202217@localhost:3306/ultralytics_auth"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
RESULT_IMG_DIR = os.path.join(BASE_DIR, "testtp")

os.makedirs(WEIGHTS_DIR, exist_ok=True)
os.makedirs(RESULT_IMG_DIR, exist_ok=True)

DEFAULT_MODEL_PATH = r"E:\bysj\ultralytics-8.2.27\runs\detect\best.pt"

# ===============================
# 数据库
# ===============================
engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True)
    password = Column(String(255))
    detections = relationship("DetectionHistory", back_populates="user")

class DetectionHistory(Base):
    __tablename__ = "detection_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    filename = Column(String(255))
    result_image_url = Column(String(512))
    original_image = Column(LargeBinary(length=(2**32)-1))
    result_image_data = Column(LargeBinary(length=(2**32)-1))
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="detections")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===============================
# FastAPI
# ===============================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/testtp", StaticFiles(directory=RESULT_IMG_DIR), name="static")

# ===============================
# 加载模型
# ===============================
try:
    current_model = YOLO(DEFAULT_MODEL_PATH)
    print("✅ 模型加载成功")
except:
    current_model = YOLO("yolov8n.pt")
    print("⚠️ 使用默认模型")

# ===============================
# ⭐论文级空货架检测算法
# ===============================
def smart_empty_detect(detections):

    if len(detections) < 3:
        return [], 0, 0

    boxes = np.array([[d['x1'], d['y1'], d['x2'], d['y2']] for d in detections])
    centers_y = (boxes[:,1] + boxes[:,3]) / 2

    # 1️⃣ 货架分层
    rows = []
    for y in centers_y:
        placed = False
        for row in rows:
            if abs(np.mean(row) - y) < 60:
                row.append(y)
                placed = True
                break
        if not placed:
            rows.append([y])

    row_centers = [np.mean(r) for r in rows]

    empty_boxes = []
    total_slots = 0

    # 2️⃣ 每层分析
    for rc in row_centers:

        row_items = []
        for d in detections:
            cy = (d['y1'] + d['y2']) / 2
            if abs(cy - rc) < 60:
                row_items.append(d)

        if len(row_items) < 2:
            continue

        row_items = sorted(row_items, key=lambda x: x['x1'])

        widths = [(d['x2']-d['x1']) for d in row_items]
        avg_width = np.mean(widths)

        # 估算槽位数
        shelf_width = row_items[-1]['x2'] - row_items[0]['x1']
        slots = int(shelf_width / avg_width)
        total_slots += slots

        # 3️⃣ 空位检测
        for i in range(len(row_items)-1):

            d1 = row_items[i]
            d2 = row_items[i+1]

            gap = d2['x1'] - d1['x2']

            if gap > max(avg_width * 0.6, 15):

                empty_boxes.append({
                    "x1": d1['x2'],
                    "y1": min(d1['y1'], d2['y1']),
                    "x2": d2['x1'],
                    "y2": max(d1['y2'], d2['y2']),
                    "class_name": "empty_shelf"
                })

    empty_count = len(empty_boxes)
    return empty_boxes, empty_count, total_slots


# ===============================
# 接口
# ===============================
@app.post("/detect")
async def detect(
    file: UploadFile = File(...),
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):

    content = await file.read()
    image = Image.open(io.BytesIO(content)).convert("RGB")

    results = current_model.predict(
        source=image,
        conf=0.5   # ⭐关键优化
    )

    names = current_model.names
    detections = []

    # ⭐过滤噪声框
    for r in results[0].boxes.data.tolist():

        x1,y1,x2,y2,conf,cls = r

        if (x2-x1)<25 or (y2-y1)<25:
            continue

        detections.append({
            "x1":x1,
            "y1":y1,
            "x2":x2,
            "y2":y2,
            "class_name":names[int(cls)]
        })

    # ⭐空货架检测
    empty_boxes, empty_count, total_slots = smart_empty_detect(detections)
    detections.extend(empty_boxes)

    # ⭐缺货率
    empty_rate = 0
    if total_slots > 0:
        empty_rate = round(empty_count / total_slots, 3)

    # ===============================
    # 可视化
    # ===============================
    draw = ImageDraw.Draw(image)

    for d in detections:
        color = (255,0,0) if "empty" in d['class_name'] else (0,255,0)
        draw.rectangle([d['x1'], d['y1'], d['x2'], d['y2']], outline=color, width=3)

    # 保存图片
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    name = f"res_{ts}.jpg"
    path = os.path.join(RESULT_IMG_DIR, name)
    image.save(path)

    # 存数据库
    if user_id:
        img_byte = io.BytesIO()
        image.save(img_byte, format='JPEG')

        db.add(DetectionHistory(
            user_id=user_id,
            filename=file.filename,
            result_image_url=f"/static/testtp/{name}",
            original_image=content,
            result_image_data=img_byte.getvalue()
        ))
        db.commit()

    return {
        "success": True,
        "url": f"/static/testtp/{name}",
        "empty_count": empty_count,
        "total_slots": total_slots,
        "empty_rate": empty_rate,
        "detections": detections
    }


# ===============================
# 启动
# ===============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8800)