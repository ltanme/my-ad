"""
媒体资源收集模块
负责从挂载的目录中收集图片和视频文件
"""
import os
import random
import logging

logger = logging.getLogger(__name__)


class MediaCollector:
    """媒体资源收集器"""
    
    def __init__(self, config):
        self.image_extensions = config['schedule']['image_extensions']
        self.video_extensions = config['schedule']['video_extensions']
    
    def collect_media(self, directories, image_count, video_count):
        """
        从指定目录收集媒体文件
        
        Args:
            directories: 要扫描的目录列表
            image_count: 需要收集的图片数量
            video_count: 需要收集的视频数量
        
        Returns:
            dict: {'images': [...], 'videos': [...]}
        """
        all_images = []
        all_videos = []
        
        # 遍历所有目录收集文件
        for directory in directories:
            if not os.path.exists(directory):
                logger.warning(f"目录不存在: {directory}")
                continue
            
            if not os.path.ismount(directory):
                logger.warning(f"目录未挂载: {directory}")
            
            logger.info(f"扫描目录: {directory}")
            images, videos = self._scan_directory(directory)
            all_images.extend(images)
            all_videos.extend(videos)
        
        logger.info(f"共找到 {len(all_images)} 个图片, {len(all_videos)} 个视频")
        
        # 随机选择指定数量的文件
        selected_images = self._random_select(all_images, image_count)
        selected_videos = self._random_select(all_videos, video_count)
        
        return {
            'images': selected_images,
            'videos': selected_videos
        }
    
    def _scan_directory(self, directory):
        """
        递归扫描目录，收集所有图片和视频文件
        
        Returns:
            tuple: (images, videos)
        """
        images = []
        videos = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    ext = os.path.splitext(filename)[1].lower().lstrip('.')
                    
                    if ext in self.image_extensions:
                        images.append(file_path)
                    elif ext in self.video_extensions:
                        videos.append(file_path)
            
        except Exception as e:
            logger.error(f"扫描目录 {directory} 失败: {str(e)}")
        
        return images, videos
    
    def _random_select(self, items, count):
        """随机选择指定数量的项目"""
        if len(items) <= count:
            return items
        
        return random.sample(items, count)
