#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  该脚本是老的脚本，生成播放列表/home/show/photo_viewer_project/generate_playlist_fast.py --all

import os
import sys
import random
import time
from datetime import datetime, timedelta
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class FastPlaylistGenerator:
    def __init__(self):
        self.mount_path = "/volume2/photo"
        self.playlist_dir = os.path.expanduser("~")
        self.photo_extensions = ['.jpg', '.jpeg', '.png']
        self.lock = threading.Lock()

    def check_mount_status(self):
        """检查SMB共享是否已挂载"""
        if os.path.ismount(self.mount_path) and os.path.exists(self.mount_path):
            try:
                os.listdir(self.mount_path)
                print(f"✅ SMB挂载正常: {self.mount_path}")
                return True
            except Exception as e:
                print(f"❌ SMB挂载访问失败: {e}")
                return False
        else:
            print(f"❌ SMB未挂载: {self.mount_path}")
            return False

    def get_simple_date(self, image_path):
        """快速获取文件时间，不读取EXIF"""
        try:
            mtime = os.path.getmtime(image_path)
            return time.strftime("%Y:%m:%d %H:%M:%S", time.localtime(mtime))
        except:
            return ""

    def scan_directory_fast(self, directory, max_count=3):
        """快速扫描目录，只获取文件列表，不读取EXIF"""
        photos = []
        try:
            # 只扫描第一层，避免深度递归
            files = os.listdir(directory)
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.photo_extensions):
                    full_path = os.path.join(directory, file)
                    if os.path.isfile(full_path):  # 确保是文件
                        # 使用文件修改时间而不是EXIF
                        file_date = self.get_simple_date(full_path)
                        photos.append(f"{full_path}|{file_date}")

            if photos:
                random.shuffle(photos)
                return photos[:max_count]
        except Exception as e:
            pass  # 静默忽略错误，避免输出太多信息

        return []

    def process_subdirectory(self, subdir_info):
        """处理单个子目录"""
        subdir, index, total = subdir_info
        subdir_path = os.path.join(self.mount_path, subdir)

        # 显示进度（线程安全）
        with self.lock:
            print(f"  [{index:3d}/{total}] 扫描: {subdir[:50]}...")

        photos = self.scan_directory_fast(subdir_path, 3)
        return photos

    def generate_playlist(self, date_str, use_threads=True):
        """生成指定日期的播放列表"""
        playlist_file = os.path.join(self.playlist_dir, f"playlist_{date_str}.txt")

        if os.path.exists(playlist_file):
            print(f"播放列表已存在: {playlist_file}")
            with open(playlist_file, 'r', encoding='utf-8') as f:
                existing_count = len(f.readlines())
            print(f"   包含 {existing_count} 张图片")
            return playlist_file

        if not self.check_mount_status():
            print("SMB共享未挂载，无法生成播放列表")
            return None

        try:
            playlist = []
            start_time = time.time()
            print(f"开始生成播放列表: {date_str}")

            # 获取所有子目录
            subdirs = []
            for item in os.listdir(self.mount_path):
                subdir_path = os.path.join(self.mount_path, item)
                if os.path.isdir(subdir_path):
                    subdirs.append(item)

            print(f"发现 {len(subdirs)} 个子目录")
            print("开始扫描...")

            if use_threads and len(subdirs) > 10:
                # 使用多线程处理（适合网络存储）
                max_workers = min(8, len(subdirs))  # 最多8个线程
                print(f"使用 {max_workers} 个线程并行处理")

                # 准备任务列表
                tasks = [(subdir, i + 1, len(subdirs)) for i, subdir in enumerate(subdirs)]

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_subdir = {executor.submit(self.process_subdirectory, task): task[0]
                                        for task in tasks}

                    for future in as_completed(future_to_subdir):
                        try:
                            photos = future.result()
                            playlist.extend(photos)
                        except Exception as e:
                            pass  # 忽略单个目录的错误
            else:
                # 单线程处理
                for i, subdir in enumerate(subdirs):
                    print(f"  [{i + 1:3d}/{len(subdirs)}] 扫描: {subdir[:50]}...")
                    subdir_path = os.path.join(self.mount_path, subdir)
                    photos = self.scan_directory_fast(subdir_path, 3)
                    playlist.extend(photos)

            elapsed_time = time.time() - start_time

            if playlist:
                random.shuffle(playlist)
                with open(playlist_file, 'w', encoding='utf-8') as f:
                    for item in playlist:
                        f.write(item + '\n')
                print(f"✅ 生成播放列表完成: {playlist_file}")
                print(f"   共包含 {len(playlist)} 张图片")
                print(f"   耗时: {elapsed_time:.1f} 秒")
                return playlist_file
            else:
                print(f"❌ 未找到图片，无法生成播放列表")
                return None

        except Exception as e:
            print(f"❌ 生成播放列表失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_playlists(self, days=2):
        """生成多天的播放列表"""
        results = []
        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            date_str = date.strftime("%Y%m%d")
            result = self.generate_playlist(date_str)
            if result:
                results.append(result)
        return results


def main():
    print("=== 快速播放列表生成器 ===")
    print("优化版本：多线程 + 简化EXIF读取")
    print()

    generator = FastPlaylistGenerator()

    # 检查参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--today':
            today = datetime.now().strftime("%Y%m%d")
            generator.generate_playlist(today)
        elif sys.argv[1] == '--tomorrow':
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
            generator.generate_playlist(tomorrow)
        elif sys.argv[1] == '--all':
            generator.generate_playlists(2)
        elif sys.argv[1] == '--single':
            # 单线程模式
            today = datetime.now().strftime("%Y%m%d")
            generator.generate_playlist(today, use_threads=False)
        else:
            print("用法:")
            print("  python3 generate_playlist_fast.py --today     # 生成今天的播放列表")
            print("  python3 generate_playlist_fast.py --tomorrow  # 生成明天的播放列表")
            print("  python3 generate_playlist_fast.py --all       # 生成今天和明天的播放列表")
            print("  python3 generate_playlist_fast.py --single    # 单线程模式")
    else:
        generator.generate_playlists(2)

    print()
    print("=== 播放列表文件位置 ===")
    playlist_files = glob.glob(os.path.expanduser("~/playlist_*.txt"))
    if playlist_files:
        for pf in sorted(playlist_files):
            file_size = os.path.getsize(pf)
            with open(pf, 'r', encoding='utf-8') as f:
                line_count = len(f.readlines())
            print(f"  {pf} ({line_count} 张图片, {file_size} 字节)")
    else:
        print("  未找到播放列表文件")


if __name__ == "__main__":
    main()