"""
Schedule Service - 播放列表计划任务生成服务
独立的 Flask 服务，通过 API 与 admin 服务交互
"""
from flask import Flask, jsonify, request
import logging
import os
from pathlib import Path
from config_loader import load_config
from scheduler import PlaylistScheduler

# 加载配置
config = load_config()

# 配置日志
log_dir = config.get('logging', {}).get('schedule_log_dir', '/tmp/schedule')
log_file = config.get('logging', {}).get('schedule_log_file', 'schedule.log')
log_level = config.get('logging', {}).get('level', 'INFO')

# 创建日志目录
log_dir_path = Path(log_dir)
log_dir_path.mkdir(parents=True, exist_ok=True)
log_file_path = log_dir_path / log_file

# 清除已有的 handlers
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 创建文件 handler
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 创建控制台 handler
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 配置 root logger
root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)
logger.info(f"日志文件: {log_file_path}")
logger.info(f"日志目录: {log_dir_path}")

app = Flask(__name__)

# 初始化调度器
scheduler = PlaylistScheduler(config)


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'schedule',
        'version': '1.0.0'
    })


@app.route('/api/schedule/generate', methods=['POST'])
def generate_schedule():
    """
    生成播放列表计划
    可选参数:
    - date: 指定日期 (YYYY-MM-DD)，默认为今天
    - force: 是否强制重新生成，默认 false
    """
    try:
        # 允许空请求体
        data = request.get_json(silent=True) or {}
        target_date = data.get('date')
        force = data.get('force', False)
        
        result = scheduler.generate_daily_schedule(target_date, force)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"生成计划失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/schedule/mount', methods=['POST'])
def mount_nas():
    """手动挂载 NAS 目录"""
    try:
        result = scheduler.mount_manager.mount_all()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"挂载失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/schedule/unmount', methods=['POST'])
def unmount_nas():
    """手动卸载 NAS 目录"""
    try:
        result = scheduler.mount_manager.unmount_all()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"卸载失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/schedule/status', methods=['GET'])
def get_status():
    """获取服务状态"""
    try:
        mount_status = scheduler.mount_manager.get_mount_status()
        return jsonify({
            'success': True,
            'mounts': mount_status
        })
    except Exception as e:
        logger.error(f"获取状态失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("启动 Schedule 服务...")
    logger.info("=" * 60)
    
    # 启动时检查并挂载 NAS 目录
    logger.info("检查 NAS 挂载状态...")
    try:
        mount_status = scheduler.mount_manager.get_mount_status()
        
        logger.info(f"配置的挂载目录数量: {len(mount_status)}")
        for status in mount_status:
            remote = status['remote_path']
            local = status['local_path']
            is_mounted = status['is_mounted']
            
            if is_mounted:
                logger.info(f"✓ 已挂载: {remote} -> {local}")
            else:
                logger.warning(f"✗ 未挂载: {remote} -> {local}")
        
        # 尝试挂载未挂载的目录
        unmounted = [s for s in mount_status if not s['is_mounted']]
        if unmounted:
            logger.info(f"尝试挂载 {len(unmounted)} 个未挂载的目录...")
            mount_results = scheduler.mount_manager.mount_all()
            
            for result in mount_results:
                remote = result['remote_path']
                local = result.get('local_path', 'N/A')
                success = result.get('success', False)
                
                if success:
                    if result.get('already_mounted'):
                        logger.info(f"✓ {remote} 已经挂载")
                    else:
                        logger.info(f"✓ {remote} 挂载成功 -> {local}")
                else:
                    error = result.get('error', 'Unknown error')
                    logger.error(f"✗ {remote} 挂载失败: {error}")
        else:
            logger.info("所有目录已挂载")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"挂载检查失败: {str(e)}", exc_info=True)
        logger.warning("服务将继续启动，但挂载可能不可用")
        logger.info("=" * 60)
    
    logger.info("Schedule 服务启动完成")
    logger.info("服务地址: http://0.0.0.0:3700")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=3700, debug=False)
