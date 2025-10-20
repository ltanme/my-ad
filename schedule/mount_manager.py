"""
NAS 挂载管理模块
负责挂载和卸载 NFS 目录
"""
import os
import subprocess
import logging

logger = logging.getLogger(__name__)


class MountManager:
    """NAS 挂载管理器"""
    
    def __init__(self, config):
        schedule_config = config['schedule']
        self.nas_host = schedule_config['nas_host']
        self.mount_paths = schedule_config['mount_path']
        self.local_mount_base = schedule_config['local_mount_base']
        self.mount_type = schedule_config.get('mount_type', 'nfs')  # 默认 nfs
        self.smb_username = schedule_config.get('smb_username', '')
        self.smb_password = schedule_config.get('smb_password', '')
        
        # 确保本地挂载基础目录存在
        os.makedirs(self.local_mount_base, exist_ok=True)
    
    def mount_all(self):
        """挂载所有配置的 NAS 目录"""
        results = []
        
        for remote_path in self.mount_paths:
            try:
                result = self._mount_single(remote_path)
                results.append(result)
            except Exception as e:
                logger.error(f"挂载 {remote_path} 失败: {str(e)}")
                results.append({
                    'remote_path': remote_path,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def _mount_single(self, remote_path):
        """挂载单个目录（支持 NFS 和 SMB）"""
        # 生成本地挂载点路径
        local_mount_point = self._get_local_mount_point(remote_path)
        
        logger.info(f"准备挂载 ({self.mount_type.upper()}): {self.nas_host}:{remote_path} -> {local_mount_point}")
        
        # 创建本地挂载点目录
        os.makedirs(local_mount_point, exist_ok=True)
        logger.debug(f"本地挂载点目录已创建: {local_mount_point}")
        
        # 检查是否已经挂载
        if self._is_mounted(local_mount_point):
            logger.info(f"已挂载: {remote_path} -> {local_mount_point}")
            return {
                'remote_path': remote_path,
                'local_path': local_mount_point,
                'success': True,
                'already_mounted': True
            }
        
        # 根据挂载类型选择不同的挂载命令
        if self.mount_type == 'smb':
            return self._mount_smb(remote_path, local_mount_point)
        else:
            return self._mount_nfs(remote_path, local_mount_point)
    
    def _mount_nfs(self, remote_path, local_mount_point):
        """挂载 NFS"""
        nfs_path = f"{self.nas_host}:{remote_path}"
        mount_cmd = ['sudo', 'mount', '-t', 'nfs', '-o', 'resvport', nfs_path, local_mount_point]
        
        logger.info(f"执行 NFS 挂载命令: {' '.join(mount_cmd)}")
        
        try:
            result = subprocess.run(
                mount_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"✓ NFS 挂载成功: {remote_path} -> {local_mount_point}")
                return {
                    'remote_path': remote_path,
                    'local_path': local_mount_point,
                    'success': True,
                    'already_mounted': False
                }
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"✗ NFS 挂载失败: {error_msg}")
                logger.error(f"  远程路径: {nfs_path}")
                logger.error(f"  本地路径: {local_mount_point}")
                raise Exception(error_msg)
                
        except subprocess.TimeoutExpired:
            logger.error(f"✗ NFS 挂载超时 (30秒): {remote_path}")
            raise Exception("挂载超时")
        except Exception as e:
            logger.error(f"✗ NFS 挂载命令执行失败: {str(e)}")
            raise Exception(f"挂载命令执行失败: {str(e)}")
    
    def _mount_smb(self, remote_path, local_mount_point):
        """挂载 SMB/CIFS"""
        # SMB 路径格式: //host/share
        # 移除开头的斜杠，因为 SMB 共享名不需要路径分隔符
        share_name = remote_path.lstrip('/')
        smb_path = f"//{self.nas_host}/{share_name}"
        
        logger.debug(f"SMB 路径构建: remote_path={remote_path}, share_name={share_name}, smb_path={smb_path}")
        
        # 构建挂载选项
        mount_options = [
            f"username={self.smb_username}",
            f"password={self.smb_password}",
            "vers=3.0",  # SMB 版本
            "iocharset=utf8",  # 字符集
            "file_mode=0755",
            "dir_mode=0755"
        ]
        
        mount_cmd = [
            'sudo', 'mount', '-t', 'cifs',
            smb_path,
            local_mount_point,
            '-o', ','.join(mount_options)
        ]
        
        # 日志中隐藏密码
        safe_cmd = mount_cmd.copy()
        safe_cmd[-1] = safe_cmd[-1].replace(self.smb_password, '***')
        logger.info(f"执行 SMB 挂载命令: {' '.join(safe_cmd)}")
        
        try:
            result = subprocess.run(
                mount_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"✓ SMB 挂载成功: {remote_path} -> {local_mount_point}")
                return {
                    'remote_path': remote_path,
                    'local_path': local_mount_point,
                    'success': True,
                    'already_mounted': False
                }
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"✗ SMB 挂载失败: {error_msg}")
                logger.error(f"  远程路径: {smb_path}")
                logger.error(f"  本地路径: {local_mount_point}")
                raise Exception(error_msg)
                
        except subprocess.TimeoutExpired:
            logger.error(f"✗ SMB 挂载超时 (30秒): {remote_path}")
            raise Exception("挂载超时")
        except Exception as e:
            logger.error(f"✗ SMB 挂载命令执行失败: {str(e)}")
            raise Exception(f"挂载命令执行失败: {str(e)}")
    
    def unmount_all(self):
        """卸载所有挂载的目录"""
        results = []
        
        for remote_path in self.mount_paths:
            try:
                result = self._unmount_single(remote_path)
                results.append(result)
            except Exception as e:
                logger.error(f"卸载 {remote_path} 失败: {str(e)}")
                results.append({
                    'remote_path': remote_path,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def _unmount_single(self, remote_path):
        """卸载单个目录"""
        local_mount_point = self._get_local_mount_point(remote_path)
        
        if not self._is_mounted(local_mount_point):
            logger.info(f"{local_mount_point} 未挂载")
            return {
                'remote_path': remote_path,
                'local_path': local_mount_point,
                'success': True,
                'not_mounted': True
            }
        
        # 执行卸载命令（使用 sudo）
        unmount_cmd = ['sudo', 'umount', local_mount_point]
        
        logger.info(f"执行卸载命令: {' '.join(unmount_cmd)}")
        
        try:
            result = subprocess.run(
                unmount_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"卸载成功: {local_mount_point}")
                return {
                    'remote_path': remote_path,
                    'local_path': local_mount_point,
                    'success': True
                }
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"卸载失败: {error_msg}")
                raise Exception(error_msg)
                
        except subprocess.TimeoutExpired:
            raise Exception("卸载超时")
        except Exception as e:
            raise Exception(f"卸载命令执行失败: {str(e)}")
    
    def get_mount_status(self):
        """获取所有挂载点的状态"""
        status = []
        
        for remote_path in self.mount_paths:
            local_mount_point = self._get_local_mount_point(remote_path)
            is_mounted = self._is_mounted(local_mount_point)
            
            status.append({
                'remote_path': remote_path,
                'local_path': local_mount_point,
                'is_mounted': is_mounted
            })
        
        return status
    
    def _get_local_mount_point(self, remote_path):
        """根据远程路径生成本地挂载点路径"""
        # 将 /volume2/photo 转换为 volume2_photo
        safe_name = remote_path.strip('/').replace('/', '_')
        return os.path.join(self.local_mount_base, safe_name)
    
    def _is_mounted(self, local_path):
        """检查目录是否已挂载"""
        try:
            # 使用 mount 命令检查
            result = subprocess.run(
                ['mount'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return local_path in result.stdout
        except Exception as e:
            logger.error(f"检查挂载状态失败: {str(e)}")
            return False
    
    def get_all_local_paths(self):
        """获取所有本地挂载路径"""
        return [self._get_local_mount_point(path) for path in self.mount_paths]
