"""
播放列表调度器模块
负责协调各个模块，生成每日播放列表计划
"""
import logging
from datetime import datetime
from mount_manager import MountManager
from media_collector import MediaCollector
from api_client import AdminAPIClient

logger = logging.getLogger(__name__)


class PlaylistScheduler:
    """播放列表调度器"""
    
    def __init__(self, config):
        self.config = config
        self.schedule_config = config['schedule']
        
        # 初始化各个模块
        self.mount_manager = MountManager(config)
        self.media_collector = MediaCollector(config)
        self.api_client = AdminAPIClient(config)
        
        # 配置参数
        self.target_zones = self.schedule_config['target_zones']
        self.image_count = self.schedule_config['image_count']
        self.video_count = self.schedule_config['video_count']
        self.image_playlists_per_zone = self.schedule_config['image_playlists_per_zone']
        self.video_playlists_per_zone = self.schedule_config['video_playlists_per_zone']
    
    def generate_daily_schedule(self, target_date=None, force=False):
        """
        生成每日播放列表计划
        
        Args:
            target_date: 目标日期 (YYYY-MM-DD)，默认为今天
            force: 是否强制重新生成
        
        Returns:
            dict: 生成结果
        """
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"开始生成 {target_date} 的播放列表计划")
        
        result = {
            'date': target_date,
            'mount_results': [],
            'playlists': [],
            'errors': []
        }
        
        try:
            # 步骤 1: 挂载 NAS 目录
            logger.info("步骤 1: 挂载 NAS 目录")
            mount_results = self.mount_manager.mount_all()
            result['mount_results'] = mount_results
            
            # 检查是否有挂载成功的目录
            mounted_paths = [
                r['local_path'] for r in mount_results 
                if r.get('success')
            ]
            
            if not mounted_paths:
                raise Exception("没有成功挂载的目录")
            
            logger.info(f"成功挂载 {len(mounted_paths)} 个目录")
            
            # 步骤 2: 收集媒体资源
            logger.info("步骤 2: 收集媒体资源")
            
            # 步骤 3: 为每个区域生成播放列表
            logger.info("步骤 3: 为每个区域生成播放列表")
            
            for zone_code in self.target_zones:
                logger.info(f"处理区域: {zone_code}")
                
                # 生成图片播放列表
                for i in range(self.image_playlists_per_zone):
                    try:
                        playlist_result = self._create_image_playlist(
                            zone_code, 
                            target_date, 
                            i + 1,
                            mounted_paths
                        )
                        result['playlists'].append(playlist_result)
                    except Exception as e:
                        error_msg = f"创建图片播放列表失败 ({zone_code}, #{i+1}): {str(e)}"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
                
                # 生成视频播放列表
                for i in range(self.video_playlists_per_zone):
                    try:
                        playlist_result = self._create_video_playlist(
                            zone_code, 
                            target_date, 
                            i + 1,
                            mounted_paths
                        )
                        result['playlists'].append(playlist_result)
                    except Exception as e:
                        error_msg = f"创建视频播放列表失败 ({zone_code}, #{i+1}): {str(e)}"
                        logger.error(error_msg)
                        result['errors'].append(error_msg)
            
            logger.info(f"播放列表计划生成完成，共创建 {len(result['playlists'])} 个播放列表")
            
        except Exception as e:
            error_msg = f"生成计划失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result['errors'].append(error_msg)
        
        return result
    
    def _create_image_playlist(self, zone_code, date, index, mounted_paths):
        """创建图片播放列表"""
        playlist_name = f"{date}_图片_{zone_code}_{index}"
        
        logger.info(f"创建图片播放列表: {playlist_name}")
        
        # 收集图片
        media = self.media_collector.collect_media(
            mounted_paths,
            self.image_count,
            0  # 不收集视频
        )
        
        images = media['images']
        
        if not images:
            raise Exception("没有找到图片文件")
        
        logger.info(f"收集到 {len(images)} 个图片")
        
        # 创建播放列表
        playlist_id = self.api_client.create_playlist(
            zone_code=zone_code,
            name=playlist_name,
            loop_mode='loop'
        )
        
        if not playlist_id:
            raise Exception("创建播放列表失败")
        
        # 添加图片到播放列表
        success_count = 0
        for image_path in images:
            if self.api_client.add_asset_to_playlist(playlist_id, image_path, display_ms=5000):
                success_count += 1
        
        logger.info(f"成功添加 {success_count}/{len(images)} 个图片")
        
        # 激活播放列表
        activated = self.api_client.activate_playlist(playlist_id, zone_code)
        
        return {
            'type': 'image',
            'zone_code': zone_code,
            'playlist_id': playlist_id,
            'name': playlist_name,
            'item_count': success_count,
            'activated': activated
        }
    
    def _create_video_playlist(self, zone_code, date, index, mounted_paths):
        """创建视频播放列表"""
        playlist_name = f"{date}_视频_{zone_code}_{index}"
        
        logger.info(f"创建视频播放列表: {playlist_name}")
        
        # 收集视频
        media = self.media_collector.collect_media(
            mounted_paths,
            0,  # 不收集图片
            self.video_count
        )
        
        videos = media['videos']
        
        if not videos:
            raise Exception("没有找到视频文件")
        
        logger.info(f"收集到 {len(videos)} 个视频")
        
        # 创建播放列表
        playlist_id = self.api_client.create_playlist(
            zone_code=zone_code,
            name=playlist_name,
            loop_mode='loop'
        )
        
        if not playlist_id:
            raise Exception("创建播放列表失败")
        
        # 添加视频到播放列表
        success_count = 0
        for video_path in videos:
            # 视频不需要 display_ms，由视频长度决定
            if self.api_client.add_asset_to_playlist(playlist_id, video_path):
                success_count += 1
        
        logger.info(f"成功添加 {success_count}/{len(videos)} 个视频")
        
        # 激活播放列表
        activated = self.api_client.activate_playlist(playlist_id, zone_code)
        
        return {
            'type': 'video',
            'zone_code': zone_code,
            'playlist_id': playlist_id,
            'name': playlist_name,
            'item_count': success_count,
            'activated': activated
        }
