import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, Base, engine
from ..models import DetectionResult, DetectionBox
from ..schemas import DetectionResultOut
from ..services.yolo_service import YoloService
from ..config import settings

# 确保数据库表已初始化
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api", tags=["detections"])


# 修复 404：新增模型上传接口
@router.post("/upload_model")
async def upload_model(file: UploadFile = File(...)):
    if not file.filename.endswith('.pt'):
        raise HTTPException(status_code=400, detail="仅支持 .pt 格式权重文件")

    # 将模型存放在 output_dir 同级的 weights 文件夹下
    weights_dir = os.path.join(os.path.dirname(settings.output_dir), "weights")
    os.makedirs(weights_dir, exist_ok=True)

    file_path = os.path.join(weights_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"success": True, "message": "模型上传成功", "filename": file.filename}


# 图片/视频上传与检测接口
@router.post("/detect")
def upload_and_detect(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        conf: float = 0.25,
        iou: float = 0.45,
        model: str = "best.pt",
        mode: str = "image",  # "image" 或 "video"
        user_id: int = 0
):
    # 保存上传文件
    os.makedirs(settings.output_dir, exist_ok=True)
    src_path = os.path.join(settings.output_dir, file.filename)
    with open(src_path, "wb") as f:
        f.write(file.file.read())

    # 根据模式选择处理方式
    if mode == "video":
        # 视频检测
        from fastapi.responses import FileResponse
        
        # 调用视频检测服务
        output_path = YoloService.predict_on_video(
            src_path,
            settings.output_dir,
            conf_threshold=conf,
            iou_threshold=iou
        )
        
        # 返回处理后的视频文件
        from urllib.parse import quote
        
        # 使用 ASCII 安全的文件名
        safe_filename = f"result_{int(os.path.getmtime(output_path))}.mp4"
        
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=safe_filename,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Disposition": f'inline; filename="{safe_filename}"'
            }
        )
    
    else:
        # 图片检测（原有逻辑）
        # 调用服务进行检测（含空货架推算逻辑）
        annotated_path, boxes = YoloService.predict_on_image(
            src_path,
            settings.output_dir,
            conf_threshold=conf,
            iou_threshold=iou
        )

        # 转换为前端期望的格式
        detections = []
        for cls_name, x1, y1, x2, y2, score in boxes:
            detections.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "confidence": score,
                "class_name": cls_name
            })

        # 始终记录到数据库
        result = DetectionResult(image_path=src_path, saved_image_path=annotated_path)
        db.add(result)
        db.flush()

        for cls_name, x1, y1, x2, y2, score in boxes:
            box = DetectionBox(
                result_id=result.id,
                cls_name=cls_name,
                x1=x1, y1=y1, x2=x2, y2=y2,
                score=score,
            )
            db.add(box)

        db.commit()
        db.refresh(result)

        # 返回前端期望的格式
        return {
            "success": True,
            "detections": detections,
            "url": f"/static/{os.path.basename(annotated_path)}",
            "empty_count": len([d for d in detections if "empty" in d["class_name"].lower()]),
            "total_slots": len(detections),
            "empty_rate": len([d for d in detections if "empty" in d["class_name"].lower()]) / max(len(detections), 1)
        }



# 获取检测历史记录列表
@router.get("/detections/")
def get_detection_history(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 20,
        user_id: int = None,
        is_admin: bool = False
):
    """
    获取检测历史记录
    - 普通用户只能看到自己的记录（如果实现了用户关联）
    - 管理员可以看到所有记录
    """
    query = db.query(DetectionResult).order_by(DetectionResult.created_at.desc())
    
    # 如果不是管理员且指定了user_id，可以在这里添加过滤逻辑
    # 目前简化处理，返回所有记录
    
    total = query.count()
    results = query.offset(skip).limit(limit).all()
    
    # 转换为前端需要的格式
    history_list = []
    for result in results:
        # 统计检测框信息
        total_detections = len(result.detections)
        empty_count = sum(1 for box in result.detections if "empty" in box.cls_name.lower())
        product_count = total_detections - empty_count
        
        history_list.append({
            "id": result.id,
            "image_path": result.image_path,
            "saved_image_path": result.saved_image_path,
            "created_at": result.created_at.isoformat(),
            "total_detections": total_detections,
            "product_count": product_count,
            "empty_count": empty_count,
            "empty_rate": empty_count / max(total_detections, 1) if total_detections > 0 else 0
        })
    
    return {
        "success": True,
        "total": total,
        "records": history_list
    }


# 获取单条检测记录详情
@router.get("/detections/{record_id}")
def get_detection_detail(
        record_id: int,
        db: Session = Depends(get_db),
        user_id: int = None,
        is_admin: bool = False
):
    """获取检测记录详情，包括所有检测框"""
    result = db.query(DetectionResult).filter(DetectionResult.id == record_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 转换检测框数据
    detections = []
    for box in result.detections:
        detections.append({
            "id": box.id,
            "class_name": box.cls_name,
            "x1": box.x1,
            "y1": box.y1,
            "x2": box.x2,
            "y2": box.y2,
            "confidence": box.score
        })
    
    return {
        "success": True,
        "id": result.id,
        "image_path": result.image_path,
        "saved_image_path": result.saved_image_path,
        "created_at": result.created_at.isoformat(),
        "detections": detections
    }


# 删除检测记录
@router.delete("/detections/{record_id}")
def delete_detection_record(
        record_id: int,
        db: Session = Depends(get_db),
        user_id: int = None,
        is_admin: bool = False
):
    """删除检测记录"""
    result = db.query(DetectionResult).filter(DetectionResult.id == record_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 删除关联的图片文件
    try:
        if result.image_path and os.path.exists(result.image_path):
            os.remove(result.image_path)
        if result.saved_image_path and os.path.exists(result.saved_image_path):
            os.remove(result.saved_image_path)
    except Exception as e:
        print(f"删除文件失败: {e}")
    
    # 删除数据库记录（级联删除检测框）
    db.delete(result)
    db.commit()
    
    return {
        "success": True,
        "message": "删除成功"
    }


# 获取检测记录的图片（原图或标注图）
@router.get("/detections/{record_id}/{image_type}")
def get_detection_image(
        record_id: int,
        image_type: str,  # "original" 或 "annotated"
        db: Session = Depends(get_db),
        user_id: int = None,
        is_admin: bool = False
):
    """获取检测记录的图片"""
    from fastapi.responses import FileResponse
    
    result = db.query(DetectionResult).filter(DetectionResult.id == record_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    if image_type == "original":
        image_path = result.image_path
    elif image_type == "annotated":
        image_path = result.saved_image_path
    else:
        raise HTTPException(status_code=400, detail="无效的图片类型")
    
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="图片文件不存在")
    
    return FileResponse(image_path)
