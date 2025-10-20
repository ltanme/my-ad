#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
负责加载和管理系统配置
"""

import os
import yaml
from pathlib import Path


class ConfigManager:
    """配置管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._config = {}
        self._project_root = None
        self._config_dir = None
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        # 获取项目根目录（main.py的父目录的父目录）
        current_file = Path(__file__).resolve()
        viewer_dir = current_file.parent
        self._project_root = viewer_dir.parent
        self._config_dir = self._project_root / "config"
        
        config_file = self._config_dir / "config.yaml"
        
        if not config_file.exists():
            # 配置文件不存在时，先不打印，等 logger 初始化后再说
            self._config = self._get_default_config()
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            # 配置加载成功，但此时 logger 可能还没初始化
        except Exception as e:
            # 配置加载失败，使用默认配置
            self._config = self._get_default_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            'database': {
                'filename': 'media_display.db',
                'auto_create': True
            },
            'display': {
                'window_title': '多区域媒体显示器',
                'start_maximized': True,
                'fullscreen': False
            },
            'zones': {
                'top_marquee': {
                    'enabled': True,
                    'font_size': 36,
                    'speed': 3,
                    'interval': 20,
                    'gap': 80,
                    'loops_per_text': 2
                }
            },
            'countdown': {
                'enabled': True,
                'font_size': 24,
                'background_opacity': 120
            },
            'logging': {
                'enabled': True,
                'level': 'INFO',
                'show_playback_info': True
            }
        }
    
    def get(self, key_path, default=None):
        """
        获取配置值
        key_path: 配置路径，如 'database.filename' 或 'zones.top_marquee.font_size'
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_database_path(self):
        """获取数据库文件的绝对路径"""
        db_filename = self.get('database.filename', 'media_display.db')
        
        # 如果是绝对路径，直接使用
        db_path = Path(db_filename)
        if db_path.is_absolute():
            return str(db_path.resolve())
        
        # 否则相对于 config 目录
        db_path = self._config_dir / db_filename
        return str(db_path.resolve())
    
    def get_project_root(self):
        """获取项目根目录"""
        return str(self._project_root)
    
    def get_config_dir(self):
        """获取配置目录"""
        return str(self._config_dir)
    
    def get_all(self):
        """获取所有配置"""
        return self._config.copy()
    
    def reload(self):
        """重新加载配置"""
        self.load_config()


# 全局配置实例
config = ConfigManager()
