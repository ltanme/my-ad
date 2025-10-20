#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理后台配置
"""
import os
import yaml
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def load_config():
    """加载配置文件"""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_FILE}")
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def get_absolute_path(path_str):
    """将路径转换为绝对路径"""
    path = Path(path_str)
    if path.is_absolute():
        return path
    else:
        # 相对路径相对于 config 目录
        return (CONFIG_DIR / path).resolve()


# 加载配置
_config = load_config()

# 数据库配置
db_filename = _config.get('database', {}).get('filename', 'media_display.db')
DATABASE_PATH = str(get_absolute_path(db_filename))

# 管理员配置
admin_config = _config.get('admin', {})
ADMIN_USERNAME = admin_config.get('username', 'admin')
ADMIN_PASSWORD = admin_config.get('password', 'admin123')

# 上传目录配置
upload_folder = admin_config.get('upload_folder', 'uploads')
UPLOAD_FOLDER = get_absolute_path(upload_folder)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# 文件上传配置
ALLOWED_EXTENSIONS = set(admin_config.get('allowed_extensions', 
    ['png', 'jpg', 'jpeg', 'gif', 'heic', 'heif', 'mp4', 'avi', 'mov', 'mkv']))
max_size_mb = admin_config.get('max_file_size', 500)
MAX_CONTENT_LENGTH = max_size_mb * 1024 * 1024

# Flask 配置
# 从配置文件读取或使用默认值（生产环境应该修改）
SECRET_KEY = admin_config.get('secret_key', 'your-secret-key-change-in-production')

# 如果使用默认密钥，发出警告
if SECRET_KEY == 'your-secret-key-change-in-production':
    print("⚠️  警告: 使用默认 SECRET_KEY，生产环境请修改！")

# 区域定义
ZONES = [
    ('top_marquee', '顶部跑马灯'),
    ('left_16x9', '中部左侧 16:9 容器'),
    ('right_9x16', '中部右侧 9:16 容器'),
    ('extra_top', '顶行最右侧竖条 上格'),
    ('extra_bottom', '顶行最右侧竖条 下格'),
    ('bottom_cell_1', '顶行下三格：左'),
    ('bottom_cell_2', '顶行下三格：中'),
    ('bottom_cell_3', '顶行下三格：右'),
    ('bottom_strip', '底部状态条（仅文字）'),
]

ZONE_DICT = dict(ZONES)

# 打印配置信息（调试用）
if __name__ == '__main__':
    print("=" * 60)
    print("管理后台配置")
    print("=" * 60)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"配置目录: {CONFIG_DIR}")
    print(f"数据库路径: {DATABASE_PATH}")
    print(f"上传目录: {UPLOAD_FOLDER}")
    print(f"管理员: {ADMIN_USERNAME}")
    print(f"允许的文件类型: {ALLOWED_EXTENSIONS}")
    print(f"最大文件大小: {max_size_mb}MB")
    print("=" * 60)
