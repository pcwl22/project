"""
配置管理路由
支持实时修改检测参数并持久化保存
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..config import settings
from ..config_manager import ConfigManager

router = APIRouter(prefix="/api/config", tags=["config"])


class EmptyDetectionConfig(BaseModel):
    """空货架检测配置"""
    enable_empty_detection: Optional[bool] = None
    gap_threshold: Optional[float] = None
    row_threshold: Optional[float] = None
    min_gap_pixels: Optional[int] = None
    edge_detection: Optional[bool] = None
    min_products_per_row: Optional[int] = None


class DetectionConfig(BaseModel):
    """检测配置（包含所有参数）"""
    # 空货架检测参数
    enable_empty_detection: bool
    gap_threshold: float
    row_threshold: float
    min_gap_pixels: int
    edge_detection: bool
    min_products_per_row: int
    black_edge_threshold: int
    # 检测参数
    default_conf_threshold: float
    default_iou_threshold: float
    # 视频检测参数
    video_skip_frames: int
    video_process_width: int
    video_direct_draw: bool
    video_use_gpu: bool
    video_enable_ffmpeg: bool


class ThresholdConfig(BaseModel):
    """置信度和IOU阈值配置"""
    conf_threshold: Optional[float] = None
    iou_threshold: Optional[float] = None


@router.get("/detection", response_model=DetectionConfig)
def get_detection_config():
    """获取当前检测配置"""
    return DetectionConfig(
        enable_empty_detection=settings.enable_empty_detection,
        gap_threshold=settings.gap_threshold,
        row_threshold=settings.row_threshold,
        min_gap_pixels=settings.min_gap_pixels,
        edge_detection=settings.edge_detection,
        min_products_per_row=settings.min_products_per_row,
        black_edge_threshold=settings.black_edge_threshold,
        default_conf_threshold=settings.default_conf_threshold,
        default_iou_threshold=settings.default_iou_threshold,
        video_skip_frames=settings.video_skip_frames,
        video_process_width=settings.video_process_width,
        video_direct_draw=settings.video_direct_draw,
        video_use_gpu=settings.video_use_gpu,
        video_enable_ffmpeg=settings.video_enable_ffmpeg
    )


@router.put("/detection")
def update_detection_config(config: EmptyDetectionConfig):
    """
    更新检测配置（实时生效并持久化保存）
    
    只更新提供的参数，未提供的参数保持不变
    """
    updated_fields = []
    updates = {}
    
    if config.enable_empty_detection is not None:
        settings.enable_empty_detection = config.enable_empty_detection
        updates["enable_empty_detection"] = config.enable_empty_detection
        updated_fields.append("enable_empty_detection")
    
    if config.gap_threshold is not None:
        if not 0.1 <= config.gap_threshold <= 2.0:
            return {"success": False, "message": "gap_threshold 必须在 0.1 到 2.0 之间"}
        settings.gap_threshold = config.gap_threshold
        updates["gap_threshold"] = config.gap_threshold
        updated_fields.append("gap_threshold")
    
    if config.row_threshold is not None:
        if not 0.1 <= config.row_threshold <= 2.0:
            return {"success": False, "message": "row_threshold 必须在 0.1 到 2.0 之间"}
        settings.row_threshold = config.row_threshold
        updates["row_threshold"] = config.row_threshold
        updated_fields.append("row_threshold")
    
    if config.min_gap_pixels is not None:
        if not 5 <= config.min_gap_pixels <= 100:
            return {"success": False, "message": "min_gap_pixels 必须在 5 到 100 之间"}
        settings.min_gap_pixels = config.min_gap_pixels
        updates["min_gap_pixels"] = config.min_gap_pixels
        updated_fields.append("min_gap_pixels")
    
    if config.edge_detection is not None:
        settings.edge_detection = config.edge_detection
        updates["edge_detection"] = config.edge_detection
        updated_fields.append("edge_detection")
    
    if config.min_products_per_row is not None:
        if not 1 <= config.min_products_per_row <= 10:
            return {"success": False, "message": "min_products_per_row 必须在 1 到 10 之间"}
        settings.min_products_per_row = config.min_products_per_row
        updates["min_products_per_row"] = config.min_products_per_row
        updated_fields.append("min_products_per_row")
    
    # 持久化保存配置
    if updates:
        ConfigManager.update_config(updates)
    
    return {
        "success": True,
        "message": f"配置已更新并保存: {', '.join(updated_fields)}",
        "updated_fields": updated_fields,
        "current_config": ConfigManager.get_current_config()
    }


@router.post("/detection/reset")
def reset_detection_config():
    """重置检测配置为默认值并保存"""
    # 重置为默认值
    config = ConfigManager.reset_to_default()
    
    return {
        "success": True,
        "message": "配置已重置为默认值并保存",
        "current_config": config
    }


@router.put("/thresholds")
def update_thresholds(config: ThresholdConfig):
    """
    更新置信度和IOU阈值（实时生效并持久化保存）
    
    只更新提供的参数，未提供的参数保持不变
    """
    updated_fields = []
    updates = {}
    
    if config.conf_threshold is not None:
        if not 0.01 <= config.conf_threshold <= 1.0:
            return {"success": False, "message": "conf_threshold 必须在 0.01 到 1.0 之间"}
        settings.default_conf_threshold = config.conf_threshold
        updates["default_conf_threshold"] = config.conf_threshold
        updated_fields.append("conf_threshold")
    
    if config.iou_threshold is not None:
        if not 0.01 <= config.iou_threshold <= 1.0:
            return {"success": False, "message": "iou_threshold 必须在 0.01 到 1.0 之间"}
        settings.default_iou_threshold = config.iou_threshold
        updates["default_iou_threshold"] = config.iou_threshold
        updated_fields.append("iou_threshold")
    
    # 持久化保存配置
    if updates:
        ConfigManager.update_config(updates)
    
    return {
        "success": True,
        "message": f"阈值已更新并保存: {', '.join(updated_fields)}",
        "updated_fields": updated_fields,
        "conf_threshold": settings.default_conf_threshold,
        "iou_threshold": settings.default_iou_threshold
    }


@router.get("/thresholds")
def get_thresholds():
    """获取当前的置信度和IOU阈值"""
    return {
        "conf_threshold": settings.default_conf_threshold,
        "iou_threshold": settings.default_iou_threshold
    }
