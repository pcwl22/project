"""
配置管理器
支持算法参数的持久化保存和加载
"""
import os
import json
from typing import Dict, Any
from .config import settings


class ConfigManager:
    """配置管理器，负责保存和加载用户自定义的算法参数"""
    
    # 配置文件路径
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "algorithm_config.json")
    
    # 默认配置
    DEFAULT_CONFIG = {
        "enable_empty_detection": True,
        "gap_threshold": 0.5,
        "row_threshold": 0.6,
        "min_gap_pixels": 20,
        "edge_detection": True,
        "min_products_per_row": 2,
        "black_edge_threshold": 30,
        "default_conf_threshold": 0.25,
        "default_iou_threshold": 0.45,
        "video_skip_frames": 4,
        "video_process_width": 640,
        "video_direct_draw": True,
        "video_use_gpu": True,
        "video_enable_ffmpeg": False
    }
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """
        加载配置文件
        如果文件不存在，返回默认配置
        """
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"✓ 加载配置文件: {cls.CONFIG_FILE}")
                    return config
            except Exception as e:
                print(f"⚠ 加载配置文件失败: {e}")
                return cls.DEFAULT_CONFIG.copy()
        else:
            print(f"⚠ 配置文件不存在，使用默认配置")
            return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def save_config(cls, config: Dict[str, Any]) -> bool:
        """
        保存配置到文件
        
        Args:
            config: 配置字典
            
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(cls.CONFIG_FILE), exist_ok=True)
            
            # 保存配置
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✓ 配置已保存: {cls.CONFIG_FILE}")
            return True
        except Exception as e:
            print(f"✗ 保存配置失败: {e}")
            return False
    
    @classmethod
    def update_config(cls, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新配置（部分更新）
        
        Args:
            updates: 要更新的配置项
            
        Returns:
            更新后的完整配置
        """
        # 加载当前配置
        config = cls.load_config()
        
        # 更新配置
        config.update(updates)
        
        # 保存配置
        cls.save_config(config)
        
        return config
    
    @classmethod
    def apply_to_settings(cls):
        """
        将配置文件中的参数应用到 settings 对象
        在应用启动时调用
        """
        config = cls.load_config()
        
        # 更新 settings 对象
        for key, value in config.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
                print(f"  - {key}: {value}")
        
        print(f"✓ 配置已应用到 settings")
    
    @classmethod
    def get_current_config(cls) -> Dict[str, Any]:
        """
        获取当前的配置（从 settings 对象）
        
        Returns:
            当前配置字典
        """
        return {
            "enable_empty_detection": settings.enable_empty_detection,
            "gap_threshold": settings.gap_threshold,
            "row_threshold": settings.row_threshold,
            "min_gap_pixels": settings.min_gap_pixels,
            "edge_detection": settings.edge_detection,
            "min_products_per_row": settings.min_products_per_row,
            "black_edge_threshold": settings.black_edge_threshold,
            "default_conf_threshold": settings.default_conf_threshold,
            "default_iou_threshold": settings.default_iou_threshold,
            "video_skip_frames": settings.video_skip_frames,
            "video_process_width": settings.video_process_width,
            "video_direct_draw": settings.video_direct_draw,
            "video_use_gpu": settings.video_use_gpu,
            "video_enable_ffmpeg": settings.video_enable_ffmpeg
        }
    
    @classmethod
    def reset_to_default(cls) -> Dict[str, Any]:
        """
        重置为默认配置
        
        Returns:
            默认配置
        """
        config = cls.DEFAULT_CONFIG.copy()
        cls.save_config(config)
        cls.apply_to_settings()
        return config


# 在模块加载时自动应用配置
ConfigManager.apply_to_settings()
