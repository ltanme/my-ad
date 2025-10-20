#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viewer 日志配置模块
"""
import logging
import os
from pathlib import Path
from datetime import datetime


def setup_logger(config):
    """
    配置 viewer 日志
    
    Args:
        config: 配置管理器对象
    
    Returns:
        logger: 配置好的 logger 对象
    """
    # 获取日志配置
    log_enabled = config.get('logging.enabled', True)
    log_level = config.get('logging.level', 'INFO')
    log_dir = config.get('logging.viewer_log_dir', '/tmp/viewer')
    log_file = config.get('logging.viewer_log_file', 'viewer.log')
    
    # 创建 logger
    logger = logging.getLogger('viewer')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 清除已有的 handlers
    logger.handlers.clear()
    
    if not log_enabled:
        # 如果禁用日志，添加一个 NullHandler
        logger.addHandler(logging.NullHandler())
        return logger
    
    # 创建日志目录
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    
    # 日志文件路径
    log_file_path = log_dir_path / log_file
    
    # 创建文件 handler
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 创建控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加 handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("=" * 60)
    logger.info("Viewer 日志系统已初始化")
    logger.info(f"日志级别: {log_level}")
    logger.info(f"日志文件: {log_file_path}")
    logger.info("=" * 60)
    
    return logger


# 全局 logger 实例（延迟初始化）
_logger = None


def get_logger():
    """获取全局 logger 实例"""
    global _logger
    if _logger is None:
        # 如果还没初始化，创建一个基本的 logger
        _logger = logging.getLogger('viewer')
        _logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        _logger.addHandler(handler)
    return _logger


def init_logger(config):
    """初始化全局 logger"""
    global _logger
    _logger = setup_logger(config)
    return _logger
