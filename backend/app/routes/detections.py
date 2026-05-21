import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db, Base, engine
from ..models import DetectionResult, DetectionBox
from ..schemas import DetectionResultOut
from ..services.yolo_service import YoloService
from ..config import settings
from .admin import verify_admin  # 导入管理员权限验证
from typing import List

# 确保数据库表已初始化
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api", tags=["detections"])


# 获取可用模型列表
@router.get("/models")
def get_available_models():
    """
    获取模型目录下所有可用的 .pt 模型文件
    
    Returns:
        模型文件名列表
    """
    try:
        weights_dir = settings.model_dir
        
        # 确保目录存在
        if not os.path.exists(weights_dir):
            os.makedirs(weights_dir, exist_ok=True)
            return {"models": []}
        
        # 扫描目录下的所有 .pt 文件
        model_files = []
        for file in os.listdir(weights_dir):
            if file.endswith('.pt'):
                model_files.append(file)
        
        # 按文件名排序
        model_files.sort()
        
        # 如果没有模型文件，返回默认列表
        if not model_files:
            model_files = ['best.pt', 'yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt']
        
        return {"models": model_files}
    
    except Exception as e:
        print(f"获取模型列表失败: {e}")
        # 返回默认模型列表
        return {"models": ['best.pt', 'yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt']}


# 修复 404：新增模型上传接口（仅管理员）
@router.post("/upload_model")
async def upload_model(
    file: UploadFile = File(...),
    _: bool = Depends(verify_admin)  # 添加管理员权限验证
):
    """
    上传YOLO模型文件（仅管理员）
    
    Args:
        file: .pt 格式的模型文件
        _: 管理员权限验证（通过 is_admin 查询参数）
        
    Returns:
        上传结果信息
        
    Raises:
        HTTPException 400: 文件格式不正确
        HTTPException 403: 非管理员用户
    """
    if not file.filename.endswith('.pt'):
        raise HTTPException(status_code=400, detail="仅支持 .pt 格式权重文件")

    # 将模型存放在 runs 目录下
    weights_dir = settings.model_dir
    os.makedirs(weights_dir, exist_ok=True)

    file_path = os.path.join(weights_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    return {
        "success": True, 
        "message": "模型上传成功", 
        "filename": file.filename, 
        "path": file_path
    }


# 图片/视频上传与检测接口
@router.post("/detect")
def upload_and_detect(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        conf: float = 0.25,
        iou: float = 0.45,
        model: str = "best.pt",
        mode: str = "image",  # "image", "video", 或 "camera"
        user_id: int = 0,
        max_empty_count: int = 0,  # 摄像头模式下传入的空货架最大值
        detections_json: str = None  # 摄像头模式下传入的检测框数据（JSON字符串）
):
    # 根据模式选择输出目录
    if mode == "video":
        save_dir = settings.video_output_dir
    elif mode == "camera":
        save_dir = settings.camera_output_dir
    else:  # image
        save_dir = settings.image_output_dir
    
    # 确保目录存在
    os.makedirs(save_dir, exist_ok=True)
    
    # 保存上传文件
    src_path = os.path.join(save_dir, file.filename)
    with open(src_path, "wb") as f:
        f.write(file.file.read())

    # 根据模式选择处理方式
    if mode == "video":
        # 视频检测
        from fastapi.responses import FileResponse
        
        # 调用视频检测服务，返回视频路径、空货架最大值和检测框
        output_path, max_empty_count, boxes = YoloService.predict_on_video(
            src_path,
            save_dir,
            conf_threshold=conf,
            iou_threshold=iou,
            model_path=model  # 传递模型参数
        )
        
        # 保存视频检测记录到数据库，包含空货架最大值和用户ID
        result = DetectionResult(
            user_id=user_id if user_id > 0 else None,
            image_path=src_path,
            saved_image_path=output_path,
            file_type="video",
            max_empty_count=max_empty_count
        )
        db.add(result)
        db.flush()
        
        # 保存空货架最多的那一帧的检测框
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
    
    elif mode == "camera":
        # 摄像头检测：保存最后一帧截图和空货架最大值
        # 调用服务进行检测（获取检测框数据）
        annotated_path, boxes = YoloService.predict_on_image(
            src_path,
            save_dir,
            conf_threshold=conf,
            iou_threshold=iou,
            model_path=model  # 传递模型参数
        )
        
        # 保存摄像头检测记录到数据库，包含用户ID
        result = DetectionResult(
            user_id=user_id if user_id > 0 else None,
            image_path=src_path,
            saved_image_path=annotated_path,
            file_type="camera",
            max_empty_count=max_empty_count  # 使用前端传入的空货架最大值
        )
        db.add(result)
        db.flush()
        
        # 如果前端传递了检测框数据（空货架最多的那一帧），保存到数据库
        if detections_json:
            import json
            try:
                detections_data = json.loads(detections_json)
                for det in detections_data:
                    box = DetectionBox(
                        result_id=result.id,
                        cls_name=det.get('class_name', 'unknown'),
                        x1=det.get('x1', 0),
                        y1=det.get('y1', 0),
                        x2=det.get('x2', 0),
                        y2=det.get('y2', 0),
                        score=det.get('confidence', 0),
                    )
                    db.add(box)
            except json.JSONDecodeError:
                print(f"警告：无法解析检测框数据: {detections_json}")
        
        db.commit()
        db.refresh(result)
        
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
        
        # 添加时间戳参数避免浏览器缓存
        import time
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        
        return {
            "success": True,
            "detections": detections,
            "url": f"/static/摄像头/{os.path.basename(annotated_path)}?t={timestamp}",  # 添加时间戳
            "empty_count": len([d for d in detections if "empty" in d["class_name"].lower()]),
            "total_slots": len(detections),
            "empty_rate": len([d for d in detections if "empty" in d["class_name"].lower()]) / max(len(detections), 1),
            "max_empty_count": max_empty_count
        }
    
    else:
        # 图片检测（原有逻辑）
        # 调用服务进行检测（含空货架推算逻辑，使用对应的输出目录）
        annotated_path, boxes = YoloService.predict_on_image(
            src_path,
            save_dir,
            conf_threshold=conf,
            iou_threshold=iou,
            model_path=model  # 传递模型参数
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

        # 只有当 user_id > 0 时才记录到数据库（避免摄像头实时检测时保存每一帧）
        if user_id > 0:
            result = DetectionResult(
                user_id=user_id,
                image_path=src_path,
                saved_image_path=annotated_path,
                file_type="image"
            )
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
        # 添加时间戳参数避免浏览器缓存
        import time
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        
        return {
            "success": True,
            "detections": detections,
            "url": f"/static/照片/{os.path.basename(annotated_path)}?t={timestamp}",  # 添加时间戳
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
        # 获取文件类型
        file_type = getattr(result, 'file_type', 'image')
        
        # 对于视频和摄像头，不统计检测框（因为没有保存检测框数据）
        if file_type in ['video', 'camera']:
            history_list.append({
                "id": result.id,
                "image_path": result.image_path,
                "saved_image_path": result.saved_image_path,
                "file_type": file_type,
                "created_at": result.created_at.isoformat(),
                "total_detections": 0,  # 视频/摄像头不统计
                "product_count": 0,
                "empty_count": getattr(result, 'max_empty_count', 0),  # 显示空货架最大值
                "empty_rate": 0,
                "max_empty_count": getattr(result, 'max_empty_count', 0)  # 空货架最大值
            })
        else:
            # 图片类型：统计检测框信息
            total_detections = len(result.detections)
            empty_count = sum(1 for box in result.detections if "empty" in box.cls_name.lower())
            product_count = total_detections - empty_count
            
            history_list.append({
                "id": result.id,
                "image_path": result.image_path,
                "saved_image_path": result.saved_image_path,
                "file_type": file_type,
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
    """获取检测记录详情，包括所有检测框和统计信息"""
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
    
    # 统计检测信息
    file_type = getattr(result, 'file_type', 'image')
    
    if file_type in ['video', 'camera']:
        # 视频/摄像头类型：使用空货架最大值
        max_empty_count = getattr(result, 'max_empty_count', 0)
        return {
            "success": True,
            "id": result.id,
            "image_path": result.image_path,
            "saved_image_path": result.saved_image_path,
            "file_type": file_type,
            "created_at": result.created_at.isoformat(),
            "detections": detections,
            "detection_count": 0,
            "total_detections": 0,
            "product_count": 0,
            "empty_count": max_empty_count,
            "max_empty_count": max_empty_count,
            "empty_rate": 0
        }
    else:
        # 图片类型：统计检测框
        total_detections = len(detections)
        empty_count = sum(1 for box in detections if "empty" in box["class_name"].lower())
        product_count = total_detections - empty_count
        
        return {
            "success": True,
            "id": result.id,
            "image_path": result.image_path,
            "saved_image_path": result.saved_image_path,
            "file_type": file_type,
            "created_at": result.created_at.isoformat(),
            "detections": detections,
            "detection_count": total_detections,  # 前端使用的字段名
            "total_detections": total_detections,
            "product_count": product_count,
            "empty_count": empty_count,
            "empty_rate": empty_count / max(total_detections, 1) if total_detections > 0 else 0
        }


# 删除检测记录
@router.delete("/detections/{record_id}")
def delete_detection_record(
        record_id: int,
        db: Session = Depends(get_db),
        user_id: int = None,
        is_admin: bool = False
):
    """删除检测记录（包括数据库记录和本地文件）"""
    result = db.query(DetectionResult).filter(DetectionResult.id == record_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    deleted_files = []
    failed_files = []
    
    # 删除原始文件
    if result.image_path and os.path.exists(result.image_path):
        try:
            os.remove(result.image_path)
            deleted_files.append(os.path.basename(result.image_path))
            print(f"✓ 已删除原始文件: {result.image_path}")
        except Exception as e:
            failed_files.append(os.path.basename(result.image_path))
            print(f"✗ 删除原始文件失败: {result.image_path}, 错误: {e}")
    
    # 删除检测结果文件
    if result.saved_image_path and os.path.exists(result.saved_image_path):
        try:
            os.remove(result.saved_image_path)
            deleted_files.append(os.path.basename(result.saved_image_path))
            print(f"✓ 已删除结果文件: {result.saved_image_path}")
        except Exception as e:
            failed_files.append(os.path.basename(result.saved_image_path))
            print(f"✗ 删除结果文件失败: {result.saved_image_path}, 错误: {e}")
    
    # 删除数据库记录（级联删除检测框）
    db.delete(result)
    db.commit()
    print(f"✓ 已删除数据库记录: ID={record_id}")
    
    return {
        "success": True,
        "message": "删除成功",
        "deleted_files": deleted_files,
        "failed_files": failed_files
    }


# 获取检测记录的图片（原图或标注图）
@router.get("/detections/{record_id}/{image_type}")
def get_detection_image(
        record_id: int,
        image_type: str,  # "original", "annotated", 或 "result"
        db: Session = Depends(get_db),
        user_id: int = None,
        is_admin: bool = False
):
    """获取检测记录的图片"""
    from fastapi.responses import FileResponse
    
    result = db.query(DetectionResult).filter(DetectionResult.id == record_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 根据类型选择图片路径
    if image_type == "original":
        image_path = result.image_path
    elif image_type in ["annotated", "result"]:  # "result" 是 "annotated" 的别名
        image_path = result.saved_image_path
    else:
        raise HTTPException(status_code=400, detail=f"无效的图片类型: {image_type}，支持的类型: original, annotated, result")
    
    if not image_path:
        raise HTTPException(status_code=404, detail="图片路径为空")
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"图片文件不存在: {image_path}")
    
    return FileResponse(image_path)
