#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HEIC/HEIF 图片格式转换工具
"""
import os
from pathlib import Path

try:
    from PIL import Image
    from pillow_heif import register_heif_opener
    # 注册 HEIF 格式支持
    register_heif_opener()
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False
    print("⚠️  pillow-heif 未安装，HEIC 格式不支持")


def is_heic_file(filename):
    """检查是否是 HEIC/HEIF 文件"""
    ext = filename.lower().split('.')[-1]
    return ext in ['heic', 'heif']


def convert_heic_to_jpg(heic_path, output_path=None, quality=95):
    """
    将 HEIC 文件转换为 JPG
    
    Args:
        heic_path: HEIC 文件路径
        output_path: 输出 JPG 文件路径，如果为 None 则自动生成
        quality: JPG 质量 (1-100)
    
    Returns:
        转换后的 JPG 文件路径
    """
    if not HEIC_SUPPORT:
        raise RuntimeError("pillow-heif 未安装，无法转换 HEIC 格式")
    
    heic_path = Path(heic_path)
    
    if output_path is None:
        # 自动生成输出路径：同目录，文件名相同，扩展名改为 .jpg
        output_path = heic_path.with_suffix('.jpg')
    else:
        output_path = Path(output_path)
    
    try:
        # 打开 HEIC 文件
        img = Image.open(heic_path)
        
        # 转换为 RGB 模式（HEIC 可能是 RGBA）
        if img.mode in ('RGBA', 'LA', 'P'):
            # 创建白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 保存为 JPG
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        print(f"✓ HEIC 转换成功: {heic_path.name} -> {output_path.name}")
        return str(output_path)
        
    except Exception as e:
        print(f"✗ HEIC 转换失败: {e}")
        raise


def process_heic_upload(heic_path, keep_original=False):
    """
    处理上传的 HEIC 文件
    
    Args:
        heic_path: HEIC 文件路径
        keep_original: 是否保留原始 HEIC 文件
    
    Returns:
        JPG 文件路径
    """
    jpg_path = convert_heic_to_jpg(heic_path)
    
    # 删除原始 HEIC 文件（如果不保留）
    if not keep_original:
        try:
            os.remove(heic_path)
            print(f"✓ 已删除原始 HEIC 文件: {heic_path}")
        except Exception as e:
            print(f"⚠️  删除原始文件失败: {e}")
    
    return jpg_path


if __name__ == '__main__':
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python heic_converter.py <heic_file>")
        sys.exit(1)
    
    heic_file = sys.argv[1]
    
    if not os.path.exists(heic_file):
        print(f"文件不存在: {heic_file}")
        sys.exit(1)
    
    try:
        jpg_file = convert_heic_to_jpg(heic_file)
        print(f"转换成功: {jpg_file}")
    except Exception as e:
        print(f"转换失败: {e}")
        sys.exit(1)
