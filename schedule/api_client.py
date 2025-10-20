"""
Admin API 客户端模块
负责与 admin 服务进行 API 交互
"""
import requests
import logging

logger = logging.getLogger(__name__)


class AdminAPIClient:
    """Admin 服务 API 客户端"""
    
    def __init__(self, config):
        schedule_config = config['schedule']
        self.api_host = schedule_config['api_host']
        self.username = schedule_config['username']
        self.password = schedule_config['password']
        self.session = requests.Session()
        self._logged_in = False
    
    def login(self):
        """登录到 admin 服务"""
        if self._logged_in:
            return True
        
        try:
            url = f"{self.api_host}/login"
            data = {
                'username': self.username,
                'password': self.password
            }
            
            logger.info(f"登录到 admin 服务: {url}")
            response = self.session.post(url, data=data, allow_redirects=True)
            
            if response.status_code == 200:
                self._logged_in = True
                logger.info("登录成功")
                return True
            else:
                logger.error(f"登录失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"登录异常: {str(e)}")
            return False
    
    def create_playlist(self, zone_code, name, loop_mode='loop'):
        """
        创建播放列表
        
        Returns:
            int: playlist_id 或 None
        """
        if not self._logged_in:
            if not self.login():
                raise Exception("未登录")
        
        try:
            url = f"{self.api_host}/api/playlist/create"
            data = {
                'zone_code': zone_code,
                'name': name,
                'loop_mode': loop_mode
            }
            
            logger.info(f"创建播放列表: {name} (zone: {zone_code})")
            response = self.session.post(url, json=data)
            result = response.json()
            
            if result.get('success'):
                playlist_id = result.get('playlist_id')
                logger.info(f"播放列表创建成功: ID={playlist_id}")
                return playlist_id
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"创建播放列表失败: {error}")
                return None
                
        except Exception as e:
            logger.error(f"创建播放列表异常: {str(e)}")
            return None
    
    def add_asset_to_playlist(self, playlist_id, asset_path, display_ms=5000):
        """
        添加资源到播放列表
        直接使用挂载后的文件路径，不上传文件
        
        Args:
            playlist_id: 播放列表 ID
            asset_path: 资源文件路径（挂载后的本地路径）
            display_ms: 显示时长（毫秒）
        
        Returns:
            bool: 是否成功
        """
        if not self._logged_in:
            if not self.login():
                raise Exception("未登录")
        
        try:
            url = f"{self.api_host}/api/asset/add_by_path"
            data = {
                'file_path': asset_path,
                'playlist_id': playlist_id,
                'display_ms': display_ms
            }
            
            logger.info(f"添加资源到播放列表 {playlist_id}: {asset_path}")
            response = self.session.post(url, json=data)
            result = response.json()
            
            if result.get('success'):
                asset_id = result.get('asset_id')
                logger.info(f"资源添加成功: asset_id={asset_id}, path={asset_path}")
                return True
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"添加资源失败: {error}")
                return False
                
        except Exception as e:
            logger.error(f"添加资源异常: {str(e)}")
            return False
    
    def activate_playlist(self, playlist_id, zone_code):
        """
        激活播放列表
        
        Returns:
            bool: 是否成功
        """
        if not self._logged_in:
            if not self.login():
                raise Exception("未登录")
        
        try:
            url = f"{self.api_host}/api/playlist/{playlist_id}/activate"
            data = {'zone_code': zone_code}
            
            logger.info(f"激活播放列表: ID={playlist_id}, zone={zone_code}")
            response = self.session.post(url, json=data)
            result = response.json()
            
            if result.get('success'):
                logger.info(f"播放列表激活成功")
                return True
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"激活播放列表失败: {error}")
                return False
                
        except Exception as e:
            logger.error(f"激活播放列表异常: {str(e)}")
            return False
