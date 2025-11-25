from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from ultralytics import YOLO
from PIL import Image
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, LargeBinary, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, relationship
from pydantic import BaseModel
import io, os, cv2, numpy as np, tempfile, json, shutil

app = FastAPI()

# 数据库配置
DATABASE_URL = "mysql+pymysql://root:202217@localhost:3306/ultralytics_auth"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关联
    detections = relationship("DetectionHistory", back_populates="user", cascade="all, delete-orphan")

class DetectionHistory(Base):
    __tablename__ = "detection_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    model = Column(String(100), nullable=False)
    mode = Column(String(20), nullable=False)  # image or video
    total = Column(Integer, nullable=False, default=0)
    stats = Column(Text, nullable=True)  # JSON string
    confidence = Column(Float, nullable=False, default=0.25)
    iou = Column(Float, nullable=False, default=0.45)
    result_image = Column(String(512), nullable=True)  # 文件路径(兼容)
    original_image = Column(LargeBinary(length=(2**32)-1), nullable=True)  # 原始图片 BLOB
    result_image_data = Column(LargeBinary(length=(2**32)-1), nullable=True)  # 结果图片 BLOB
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关联
    user = relationship("User", back_populates="detections")

# 确保表存在
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic 模型
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    username: str = None
    user_id: int = None
    is_admin: bool = False

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
    expose_headers=["*"]  # 暴露所有响应头
)

# 基础目录（当前文件所在目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 创建必要的目录（使用绝对路径以避免当前工作目录差异）
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
HISTORY_ROOT = os.path.join(BASE_DIR, "history")
os.makedirs(WEIGHTS_DIR, exist_ok=True)
os.makedirs(HISTORY_ROOT, exist_ok=True)

# 默认模型权重路径
DEFAULT_WEIGHT = r"E:\bysj\ultralytics-8.2.27\runs\detect\huojia\train\weights\best.pt"

# 加载 YOLOv8 模型
current_model_path = DEFAULT_WEIGHT
model = YOLO(current_model_path)
names = model.names

# 检测历史文件夹（绝对路径）
HISTORY_DIR = os.path.join(HISTORY_ROOT, "detections")
os.makedirs(HISTORY_DIR, exist_ok=True)

# 存放带检测框的结果图片（绝对路径）
RESULT_IMG_DIR = os.path.join(BASE_DIR, "testtp")
os.makedirs(RESULT_IMG_DIR, exist_ok=True)

def save_detection_history(data, db: Session = None, original_img_bytes=None, result_img_bytes=None, user_id=None):
    """保存检测记录到数据库和 JSON 文件（兼容）"""
    # 保存到数据库
    if db:
        try:
            history_record = DetectionHistory(
                user_id=user_id,
                filename=data.get('filename'),
                model=data.get('model'),
                mode=data.get('mode'),
                total=data.get('total', 0),
                stats=json.dumps(data.get('stats', {})),
                confidence=data.get('confidence', 0.25),
                iou=data.get('iou', 0.45),
                result_image=data.get('result_image'),
                original_image=original_img_bytes,
                result_image_data=result_img_bytes
            )
            db.add(history_record)
            db.commit()
            db.refresh(history_record)
            print(f"历史记录已保存到数据库, ID: {history_record.id}")
        except Exception as e:
            print(f"保存到数据库失败: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
    
    # 兼容：仍然保存 JSON 文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{data['filename'].replace('.','_')}.json"
    filepath = os.path.join(HISTORY_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename


# 登录接口
@app.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or user.password != req.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return LoginResponse(success=True, message="登录成功", username=user.username, user_id=user.id, is_admin=user.is_admin)

# 管理员获取所有用户
@app.get("/admin/users")
def get_all_users(is_admin: bool = False, db: Session = Depends(get_db)):
    if not is_admin:
        raise HTTPException(status_code=403, detail="无权限访问")
    
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [{
        "id": u.id,
        "username": u.username,
        "is_admin": u.is_admin,
        "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "detection_count": len(u.detections)
    } for u in users]

# 管理员删除用户
@app.delete("/admin/users/{user_id}")
def delete_user(user_id: int, is_admin: bool = False, db: Session = Depends(get_db)):
    if not is_admin:
        raise HTTPException(status_code=403, detail="无权限访问")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.is_admin:
        raise HTTPException(status_code=403, detail="不能删除管理员账号")
    
    db.delete(user)
    db.commit()
    return {"message": "用户已删除", "id": user_id}

# 注册接口
@app.post("/auth/register", response_model=LoginResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户
    new_user = User(username=req.username, password=req.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return LoginResponse(success=True, message="注册成功", username=new_user.username, user_id=new_user.id, is_admin=False)

# Detections 接口（兼容新前端）
@app.get("/detections/")
def list_detections(limit: int = 100, offset: int = 0, user_id: int = None, is_admin: bool = False, db: Session = Depends(get_db)):
    try:
        # 从数据库读取
        query = db.query(DetectionHistory)
        # 非管理员只能看自己的记录
        if not is_admin and user_id is not None:
            query = query.filter(DetectionHistory.user_id == user_id)
        
        total = query.count()
        records = query.order_by(DetectionHistory.created_at.desc()).limit(limit).offset(offset).all()
        
        items = []
        for rec in records:
            img_path = None
            if rec.result_image:
                try:
                    img_path = "/history/image/" + os.path.basename(rec.result_image)
                except Exception:
                    img_path = None
            
            # 解析 JSON 字符串为字典
            stats_dict = {}
            try:
                stats_dict = json.loads(rec.stats) if rec.stats else {}
            except Exception:
                pass
            
            items.append({
                "id": rec.id,
                "image_path": rec.filename,
                "saved_image_path": img_path,
                "created_at": rec.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "detection_count": rec.total,
                "stats": stats_dict,
                "confidence": rec.confidence,
                "iou": rec.iou
            })
        
        return {"items": items, "total": total}
    except Exception as e:
        print(f"Error loading detections: {e}")
        import traceback
        traceback.print_exc()
        return {"items": [], "total": 0}

@app.get("/history/image/{img_name}")
def get_history_image(img_name: str):
    """返回保存的带检测框的结果图片（从文件）"""
    safe_name = os.path.basename(img_name)
    file_path = os.path.join(RESULT_IMG_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(file_path, media_type="image/jpeg")

@app.get("/detections/{record_id}/original")
def get_original_image(record_id: int, user_id: int = None, is_admin: bool = False, db: Session = Depends(get_db)):
    """从数据库获取原始图片"""
    from fastapi.responses import Response
    query = db.query(DetectionHistory).filter(DetectionHistory.id == record_id)
    # 非管理员需要验证权限
    if not is_admin and user_id is not None:
        query = query.filter(DetectionHistory.user_id == user_id)
    record = query.first()
    if not record or not record.original_image:
        raise HTTPException(status_code=404, detail="图片不存在或无权限访问")
    return Response(content=record.original_image, media_type="image/jpeg")

@app.get("/detections/{record_id}/result")
def get_result_image(record_id: int, user_id: int = None, is_admin: bool = False, db: Session = Depends(get_db)):
    """从数据库获取结果图片"""
    from fastapi.responses import Response
    query = db.query(DetectionHistory).filter(DetectionHistory.id == record_id)
    # 非管理员需要验证权限
    if not is_admin and user_id is not None:
        query = query.filter(DetectionHistory.user_id == user_id)
    record = query.first()
    if not record or not record.result_image_data:
        raise HTTPException(status_code=404, detail="图片不存在或无权限访问")
    return Response(content=record.result_image_data, media_type="image/jpeg")

async def process_image(file_content, file_name, conf_threshold=0.25, iou_threshold=0.45, db: Session = None, user_id: int = None):
    """处理图片检测"""
    detections = []
    record = None
    history_file = None
    original_image_bytes = file_content  # 保存原始图片字节
    result_image_bytes = None
    
    try:
        print(f"开始处理图片, 文件大小: {len(file_content)} bytes, conf={conf_threshold}, iou={iou_threshold}")
        
        # 打开并处理图片
        try:
            image = Image.open(io.BytesIO(file_content))
            print(f"图片格式: {image.format}, 模式: {image.mode}")
            image = image.convert("RGB")
            print(f"图片转换为RGB完成, 大小: {image.size}")
        except Exception as img_error:
            print(f"图片打开或转换失败: {str(img_error)}")
            raise HTTPException(status_code=400, detail=f"图片格式错误: {str(img_error)}")
        
        # 运行检测
        print("开始执行模型检测...")
        try:
            results = model.predict(source=image, conf=conf_threshold, iou=iou_threshold, save=False)
            
            # 验证检测结果
            if not results or len(results) == 0:
                raise Exception("模型没有返回任何结果")
            if not hasattr(results[0], 'boxes'):
                raise Exception("检测结果中没有找到boxes属性")
            if len(results[0].boxes) == 0:
                print("未检测到任何物体")
                
            print(f"检测完成, 找到 {len(results[0].boxes)} 个目标")
            
        except Exception as model_error:
            print(f"模型检测失败: {str(model_error)}")
            raise HTTPException(status_code=500, detail=f"模型检测失败: {str(model_error)}")
        
        # 处理检测结果
        for r in results[0].boxes.data.tolist():
            try:
                x1, y1, x2, y2, conf, cls = r
                cls_index = int(cls)
                if cls_index < 0 or cls_index >= len(names):
                    print(f"警告: 类别索引 {cls_index} 超出范围, 跳过此检测框")
                    continue
                    
                # 确保所有数值都被正确转换为浮点数并四舍五入到2位小数
                detection = {
                    "x1": round(float(x1), 2),
                    "y1": round(float(y1), 2),
                    "x2": round(float(x2), 2),
                    "y2": round(float(y2), 2),
                    "confidence": round(float(conf), 2),
                    "class": cls_index,
                    "class_name": str(names[cls_index])  # 确保类名是字符串
                }
                print(f"处理检测框: {detection}")  # 输出每个检测框的信息
                detections.append(detection)
            except Exception as box_error:
                print(f"处理单个检测框时出错: {str(box_error)}")
                continue
        
        print(f"成功处理 {len(detections)} 个检测结果")
        
        # 创建历史记录
        try:
            stats = {}
            for det in detections:
                cls_name = det["class_name"]
                stats[cls_name] = stats.get(cls_name, 0) + 1
                
            record = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "filename": file_name,
                "model": os.path.basename(current_model_path),
                "mode": "image",
                "stats": stats,
                "total": len(detections),
                "confidence": conf_threshold,
                "iou": iou_threshold
            }
            
            # 生成并保存带检测框的结果图片
            try:
                from PIL import ImageDraw, ImageFont

                annotated = image.copy()
                draw = ImageDraw.Draw(annotated)
                # 尝试加载系统字体，若失败使用默认
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except Exception:
                    font = ImageFont.load_default()

                for det in detections:
                    x1 = int(max(0, det["x1"]))
                    y1 = int(max(0, det["y1"]))
                    x2 = int(max(0, det["x2"]))
                    y2 = int(max(0, det["y2"]))
                    label = f"{det['class_name']} {det['confidence']:.2f}"
                    # 绿色 for non-empty, red for 'empty' class
                    color = (255, 0, 0) if 'empty' in det['class_name'].lower() else (0, 255, 0)
                    draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                    text_pos = (x1, max(0, y1 - 18))
                    draw.rectangle([text_pos, (text_pos[0] + draw.textlength(label, font=font) + 6, text_pos[1] + 18)], fill=color)
                    draw.text((text_pos[0] + 3, text_pos[1] + 2), label, fill=(255, 255, 255), font=font)

                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                base = os.path.splitext(os.path.basename(file_name))[0]
                img_filename = f"{ts}_{base}_result.jpg"
                img_path = os.path.join(RESULT_IMG_DIR, img_filename)
                annotated.save(img_path, format="JPEG")
                
                # 将结果图片转为字节
                result_buffer = io.BytesIO()
                annotated.save(result_buffer, format="JPEG")
                result_image_bytes = result_buffer.getvalue()
                
                # 在记录中加入可访问的图片 URL（前端可直接使用）
                record['result_image'] = f"http://localhost:8000/history/image/{img_filename}"
            except Exception as img_save_err:
                print(f"保存带框图片失败: {img_save_err}")
                record['result_image'] = None

            history_file = save_detection_history(record, db, original_image_bytes, result_image_bytes, user_id)
            print(f"历史记录已保存: {history_file}, 统计结果: {stats}")
            
        except Exception as hist_error:
            print(f"保存历史记录失败: {str(hist_error)}")
            # 不中断处理，继续返回检测结果
        
        # 构建并验证返回结果
        response_data = {
            "detections": detections,
            "history": record,
            "history_file": history_file
        }
        
        # 输出返回结果用于调试
        print(f"返回数据示例 (前5个检测框):")
        if detections:
            for i, det in enumerate(detections[:5]):
                print(f"检测框 {i+1}: {det}")
        
        # 验证数据格式
        if not isinstance(detections, list):
            raise ValueError("detections 必须是列表类型")
        if not detections:
            print("警告: 未检测到任何目标")
            
        return response_data
        
    except HTTPException as http_error:
        error_response = {
            "code": http_error.status_code,
            "success": False,
            "message": str(http_error.detail),
            "data": None
        }
        print(f"HTTP错误: {error_response}")
        return JSONResponse(
            status_code=http_error.status_code,
            content=error_response,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )
    except Exception as e:
        print(f"图片处理过程中发生未知错误: {str(e)}")
        error_response = {
            "code": 500,
            "success": False,
            "message": f"图片处理失败: {str(e)}",
            "data": None
        }
        print(f"处理错误: {error_response}")
        return JSONResponse(
            status_code=500,
            content=error_response,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )
        
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": file_name,
            "model": os.path.basename(current_model_path),
            "mode": "image",
            "stats": stats,
            "total": len(detections)
        }
        
        history_file = save_detection_history(record)
        print(f"历史记录已保存: {history_file}")
        
        return {
            "detections": detections,
            "history": record,
            "history_file": history_file
        }
        
    except Exception as e:
        print(f"图片处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")

async def process_video(file_content, file_name):
    """处理视频检测"""
    tmp_input = None
    tmp_output = None
    
    try:
        # 创建临时文件
        tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        
        # 保存上传的视频
        tmp_input.write(file_content)
        tmp_input.close()
        
        # 打开视频文件
        cap = cv2.VideoCapture(tmp_input.name)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="无法打开视频文件")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 创建输出视频
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(tmp_output.name, fourcc, fps, (width, height))
        
        # 处理每一帧
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            if frame_count % 10 == 0:  # 每10帧打印一次进度
                print(f"处理第 {frame_count} 帧")
            
            # 转为RGB并检测
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = model.predict(source=img, conf=0.3, save=False)
            
            # 绘制检测框
            for r in results[0].boxes.data.tolist():
                x1, y1, x2, y2, conf, cls = r
                color = (0,255,0) if names[int(cls)].lower().find("empty")<0 else (0,0,255)
                cv2.rectangle(frame, (int(x1),int(y1)), (int(x2),int(y2)), color, 2)
                cv2.putText(frame, f"{names[int(cls)]} {conf:.2f}", (int(x1), int(y1)-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            out.write(frame)
        
        # 清理资源
        cap.release()
        out.release()
        
        # 记录视频检测历史
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": file_name,
            "model": os.path.basename(current_model_path),
            "mode": "video",
            "stats": {"frames": frame_count},
            "total": frame_count
        }
        save_detection_history(record)
        print(f"视频检测历史已保存, 共处理 {frame_count} 帧")
        
        # 删除输入临时文件
        if os.path.exists(tmp_input.name):
            os.unlink(tmp_input.name)
        
        return tmp_output.name
        
    except Exception as e:
        # 清理临时文件
        if tmp_input and os.path.exists(tmp_input.name):
            os.unlink(tmp_input.name)
        if tmp_output and os.path.exists(tmp_output.name):
            os.unlink(tmp_output.name)
        print(f"视频处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"视频处理失败: {str(e)}")

@app.post("/detect")
async def detect(
    file: UploadFile = File(...), 
    mode: str = Form("image"),
    conf: float = 0.25,
    iou: float = 0.45,
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):
    """处理检测请求"""
    print(f"收到{mode}检测请求, 文件名: {file.filename}, Content-Type: {file.content_type}, conf={conf}, iou={iou}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")
        
    if mode not in ["image", "video"]:
        raise HTTPException(status_code=400, detail="不支持的检测模式")
    
    # 读取文件内容
    try:
        file_content = await file.read()
        print(f"成功读取文件内容, 大小: {len(file_content)} bytes")
    except Exception as e:
        print(f"读取文件失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"读取文件失败: {str(e)}")
        
    if not file_content:
        raise HTTPException(status_code=400, detail="文件内容为空")
    
    try:
        if mode == "image":
            # 处理并直接返回前端期望的字段（compat for existing frontend）
            result = await process_image(file_content, file.filename, conf, iou, db, user_id)
            # 直接返回 detections/history/history_file 在 response.data 下前端访问为 response.data.detections
            response = {
                "detections": result.get("detections", []),
                "history": result.get("history"),
                "history_file": result.get("history_file")
            }

            print(f"返回响应: total_detections={len(response['detections'])}")
            return JSONResponse(
                content=response,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
            )
        else:
            output_path = await process_video(file_content, file.filename)
            return FileResponse(
                output_path,
                media_type='video/mp4',
                filename="result.mp4",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取当前模型信息
@app.get("/model")
def get_model_info():
    global current_model_path
    return {
        "current_model": os.path.basename(current_model_path),
        "available_models": [f for f in os.listdir(WEIGHTS_DIR) if f.endswith(".pt")] + [os.path.basename(DEFAULT_WEIGHT)]
    }

# 上传新的模型权重
@app.post("/model/upload")
async def upload_model(file: UploadFile = File(...)):
    if not file.filename.endswith('.pt'):
        raise HTTPException(status_code=400, detail="只接受 .pt 格式的模型文件")
    
    file_path = os.path.join(WEIGHTS_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"message": "模型上传成功", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 切换模型
@app.post("/model/switch")
async def switch_model(filename: str = Form(...)):
    global model, names, current_model_path
    
    if filename == os.path.basename(DEFAULT_WEIGHT):
        model_path = DEFAULT_WEIGHT
    else:
        model_path = os.path.join(WEIGHTS_DIR, filename)
    
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="模型文件不存在")
    
    try:
        new_model = YOLO(model_path)
        model = new_model
        names = model.names
        current_model_path = model_path
        return {"message": "模型切换成功", "model": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取检测历史
@app.get("/history")
def get_history():
    try:
        history = []
        for filename in sorted(os.listdir(HISTORY_DIR), reverse=True):
            if filename.endswith('.json'):
                with open(os.path.join(HISTORY_DIR, filename), 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    record['id'] = filename  # 添加文件名作为ID
                    history.append(record)
        return history
    except Exception as e:
        print(f"Error loading history: {e}")
        return []

# 删除单个历史记录
@app.delete("/history/{file_id}")
def delete_history(file_id: str):
    try:
        # 支持传入完整文件名或部分 id（如前端可能传入不带扩展名的标识）
        file_path = os.path.join(HISTORY_DIR, file_id)
        target_file = None
        if os.path.exists(file_path):
            target_file = file_path
        else:
            # 尝试在 HISTORY_DIR 中查找匹配的文件名
            candidates = [f for f in os.listdir(HISTORY_DIR) if f.endswith('.json')]
            # 优先按完全匹配，再按包含，再按以传入 id 结尾
            for f in candidates:
                if f == file_id:
                    target_file = os.path.join(HISTORY_DIR, f)
                    break
            if not target_file:
                for f in candidates:
                    if file_id in f:
                        target_file = os.path.join(HISTORY_DIR, f)
                        break
            if not target_file:
                for f in candidates:
                    if f.endswith(file_id):
                        target_file = os.path.join(HISTORY_DIR, f)
                        break

        if target_file and os.path.exists(target_file):
            # 尝试读取 JSON，删除关联的 result_image 文件（如果存在）
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    rec = json.load(f)
                    result_image = rec.get('result_image')
                    if result_image:
                        # 支持完整 URL 或相对路径，提取 basename
                        img_name = os.path.basename(result_image)
                        img_path = os.path.join(RESULT_IMG_DIR, img_name)
                        if os.path.exists(img_path):
                            try:
                                os.remove(img_path)
                            except Exception as e:
                                print(f"删除关联图片失败: {e}")
            except Exception as read_err:
                print(f"读取历史记录文件失败: {read_err}")

            try:
                os.remove(target_file)
            except Exception as e:
                print(f"删除历史文件失败: {e}")
                raise HTTPException(status_code=500, detail=f"删除历史文件失败: {e}")

            return {"message": "记录已删除", "id": os.path.basename(target_file)}
        else:
            raise HTTPException(status_code=404, detail="记录不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 为前端兼容，提供 /detections/{id} 删除接口
@app.delete("/detections/{record_id}")
def delete_detection_by_id(record_id: int, user_id: int = None, is_admin: bool = False, db: Session = Depends(get_db)):
    try:
        query = db.query(DetectionHistory).filter(DetectionHistory.id == record_id)
        # 非管理员需要验证权限
        if not is_admin and user_id is not None:
            query = query.filter(DetectionHistory.user_id == user_id)
        
        record = query.first()
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在或无权限访问")
        
        # 删除关联的图片文件
        if record.result_image:
            try:
                img_name = os.path.basename(record.result_image)
                img_path = os.path.join(RESULT_IMG_DIR, img_name)
                if os.path.exists(img_path):
                    os.remove(img_path)
            except Exception as e:
                print(f"删除图片失败: {e}")
        
        db.delete(record)
        db.commit()
        return {"message": "记录已删除", "id": record_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 清除所有历史记录
@app.post("/history/clear")
def clear_history():
    try:
        # 删除所有历史 JSON 文件并尝试删除对应的 result_image
        for filename in os.listdir(HISTORY_DIR):
            if filename.endswith('.json'):
                fullpath = os.path.join(HISTORY_DIR, filename)
                try:
                    with open(fullpath, 'r', encoding='utf-8') as f:
                        rec = json.load(f)
                        result_image = rec.get('result_image')
                        if result_image:
                            img_name = os.path.basename(result_image)
                            img_path = os.path.join(RESULT_IMG_DIR, img_name)
                            if os.path.exists(img_path):
                                try:
                                    os.remove(img_path)
                                except Exception as e:
                                    print(f"删除关联图片失败: {e}")
                except Exception as e:
                    print(f"读取历史记录失败: {e}")
                finally:
                    try:
                        os.remove(fullpath)
                    except Exception as e:
                        print(f"删除历史文件失败: {e}")

        # 可选：也清理 RESULT_IMG_DIR 中的孤立文件（如果需要），但当前仅删除与历史关联的图片
        return {"message": "所有历史记录已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 首页
@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse("static/index.html")