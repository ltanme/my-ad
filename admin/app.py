#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
媒体显示系统管理后台
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from werkzeug.utils import secure_filename
import os
import sqlite3
import logging
import yaml
from pathlib import Path
from functools import wraps
from config import *
from db_helper import DBHelper
from heic_converter import is_heic_file, process_heic_upload, HEIC_SUPPORT

# 配置日志
try:
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        app_config = yaml.safe_load(f)
    
    log_dir = app_config.get('logging', {}).get('admin_log_dir', '/tmp/admin')
    log_file = app_config.get('logging', {}).get('admin_log_file', 'admin.log')
    log_level = app_config.get('logging', {}).get('level', 'INFO')
    
    # 创建日志目录
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file_path = Path(log_dir) / log_file
    
    # 配置日志处理器
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"日志文件: {log_file_path}")
except Exception as e:
    # 如果配置加载失败，使用基本日志配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.warning(f"加载日志配置失败，使用默认配置: {e}")

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

db = DBHelper()


def trigger_reload():
    """触发 viewer 重载"""
    try:
        from datetime import datetime, timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reload_signal 
            SET need_reload = 1, updated_at = ? 
            WHERE id = 1
        """, (beijing_time,))
        conn.commit()
        conn.close()
        logger.info(f"已触发重载信号 (北京时间: {beijing_time})")
    except Exception as e:
        logger.error(f"触发重载信号失败: {e}", exc_info=True)


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ========== 登录相关 ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))


# ========== 主页 ==========
@app.route('/')
@login_required
def index():
    """管理主页"""
    zone_rows = db.get_all_zones()
    zone_map = {z['code']: z for z in zone_rows}

    zones = []
    for code, name in ZONES:
        z = zone_map.get(code, {'code': code, 'name': name, 'is_fullscreen': 0})
        z['name'] = z.get('name') or name
        z['is_fullscreen'] = bool(z.get('is_fullscreen'))
        zones.append(z)

    fullscreen_zone = next((z['code'] for z in zones if z.get('is_fullscreen')), None)

    return render_template(
        'index.html',
        zones=zones,
        zone_dict={z['code']: z for z in zones},
        fullscreen_zone=fullscreen_zone
    )


# ========== 区域管理 ==========
@app.route('/zone/<zone_code>')
@login_required
def zone_manage(zone_code):
    """区域管理页面"""
    if zone_code not in ZONE_DICT:
        flash('区域不存在', 'error')
        return redirect(url_for('index'))
    
    zone_name = ZONE_DICT[zone_code]
    playlists = db.get_playlists_by_zone(zone_code)
    
    return render_template('zone_manage.html', 
                         zone_code=zone_code, 
                         zone_name=zone_name,
                         playlists=playlists)


@app.route('/api/zone/<zone_code>/fullscreen', methods=['POST'])
@login_required
def api_set_zone_fullscreen(zone_code):
    """设置区域是否全屏显示"""
    data = request.json or {}
    enabled = bool(data.get('is_fullscreen'))

    try:
        db.set_zone_fullscreen(zone_code, enabled)
        trigger_reload()

        fullscreen_zone = db.get_fullscreen_zone()
        active_code = fullscreen_zone['code'] if fullscreen_zone else None

        logger.info(f"更新全屏区域: code={zone_code}, enabled={enabled}, active={active_code}")
        return jsonify({'success': True, 'fullscreen_zone': active_code})
    except ValueError as e:
        logger.warning(f"设置全屏失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"设置全屏失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': '内部错误'}), 500


# ========== 播放列表 API ==========
@app.route('/api/playlist/create', methods=['POST'])
@login_required
def api_create_playlist():
    """创建播放列表"""
    data = request.json
    zone_code = data.get('zone_code')
    name = data.get('name')
    loop_mode = data.get('loop_mode', 'loop')
    
    try:
        playlist_id = db.create_playlist(zone_code, name, loop_mode)
        logger.info(f"创建播放列表成功: {name} (zone={zone_code}, id={playlist_id})")
        return jsonify({'success': True, 'playlist_id': playlist_id})
    except Exception as e:
        logger.error(f"创建播放列表失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/playlist/<int:playlist_id>/update', methods=['POST'])
@login_required
def api_update_playlist(playlist_id):
    """更新播放列表"""
    data = request.json
    name = data.get('name')
    loop_mode = data.get('loop_mode')
    is_active = data.get('is_active', 0)
    
    try:
        db.update_playlist(playlist_id, name, loop_mode, is_active)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/playlist/<int:playlist_id>/delete', methods=['POST'])
@login_required
def api_delete_playlist(playlist_id):
    """删除播放列表"""
    try:
        db.delete_playlist(playlist_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/playlist/<int:playlist_id>/activate', methods=['POST'])
@login_required
def api_activate_playlist(playlist_id):
    """激活播放列表"""
    data = request.json
    zone_code = data.get('zone_code')
    
    try:
        db.set_active_playlist(zone_code, playlist_id)
        trigger_reload()
        logger.info(f"激活播放列表: id={playlist_id}, zone={zone_code}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"激活播放列表失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/playlist/<int:playlist_id>/items', methods=['GET'])
@login_required
def api_get_playlist_items(playlist_id):
    """获取播放列表项"""
    try:
        items = db.get_playlist_items(playlist_id)
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========== 播放项 API ==========
@app.route('/api/item/add', methods=['POST'])
@login_required
def api_add_item():
    """添加播放项"""
    data = request.json
    playlist_id = data.get('playlist_id')
    item_type = data.get('type')
    
    try:
        if item_type == 'text':
            text = data.get('text')
            display_ms = data.get('display_ms', 5000)
            item_id = db.add_playlist_item(playlist_id, text_inline=text, display_ms=display_ms)
        else:
            return jsonify({'success': False, 'error': '请先上传文件'})
        
        return jsonify({'success': True, 'item_id': item_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/item/<int:item_id>/delete', methods=['POST'])
@login_required
def api_delete_item(item_id):
    """删除播放项"""
    try:
        db.delete_playlist_item(item_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ========== 文件上传 ==========
@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """上传文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '文件名为空'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        ext = filename.rsplit('.', 1)[1].lower()
        
        # 处理 HEIC 格式：转换为 JPG
        if ext in {'heic', 'heif'}:
            if not HEIC_SUPPORT:
                return jsonify({'success': False, 'error': 'HEIC 格式不支持，请安装 pillow-heif'})
            
            try:
                # 转换 HEIC 为 JPG
                jpg_path = process_heic_upload(filepath, keep_original=False)
                filepath = jpg_path
                filename = os.path.basename(jpg_path)
                ext = 'jpg'
                logger.info(f"HEIC 已转换为 JPG: {filename}")
            except Exception as e:
                logger.error(f"HEIC 转换失败: {e}", exc_info=True)
                return jsonify({'success': False, 'error': f'HEIC 转换失败: {str(e)}'})
        
        # 判断文件类型
        if ext in {'png', 'jpg', 'jpeg', 'gif'}:
            kind = 'image'
        elif ext in {'mp4', 'avi', 'mov', 'mkv'}:
            kind = 'video'
        else:
            kind = 'unknown'
        
        uri = f"file://{filepath}"
        asset_id = db.create_media_asset(kind, uri)
        
        playlist_id = request.form.get('playlist_id')
        display_ms = request.form.get('display_ms', 5000)
        
        if playlist_id:
            db.add_playlist_item(int(playlist_id), asset_id=asset_id, display_ms=int(display_ms))
        
        return jsonify({'success': True, 'asset_id': asset_id, 'filename': filename})
    
    return jsonify({'success': False, 'error': '文件类型不允许'})


@app.route('/api/asset/add_by_path', methods=['POST'])
@login_required
def api_add_asset_by_path():
    """
    通过文件路径添加资源（用于 schedule 服务）
    不上传文件，直接使用已存在的文件路径
    """
    data = request.json
    file_path = data.get('file_path')
    playlist_id = data.get('playlist_id')
    display_ms = data.get('display_ms', 5000)
    
    if not file_path:
        return jsonify({'success': False, 'error': '缺少 file_path 参数'})
    
    if not os.path.exists(file_path):
        logger.warning(f"文件不存在: {file_path}")
        return jsonify({'success': False, 'error': f'文件不存在: {file_path}'})
    
    try:
        # 判断文件类型
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        if ext in {'png', 'jpg', 'jpeg', 'gif'}:
            kind = 'image'
        elif ext in {'mp4', 'avi', 'mov', 'mkv'}:
            kind = 'video'
        else:
            return jsonify({'success': False, 'error': f'不支持的文件类型: {ext}'})
        
        # 创建资源记录
        uri = f"file://{file_path}"
        asset_id = db.create_media_asset(kind, uri)
        
        # 如果指定了播放列表，添加到播放列表
        if playlist_id:
            db.add_playlist_item(int(playlist_id), asset_id=asset_id, display_ms=int(display_ms))
        
        logger.info(f"通过路径添加资源: {kind} - {file_path} (asset_id={asset_id})")
        
        return jsonify({
            'success': True, 
            'asset_id': asset_id,
            'kind': kind,
            'file_path': file_path
        })
        
    except Exception as e:
        logger.error(f"通过路径添加资源失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/database/download', methods=['GET'])
@login_required
def download_database():
    """下载数据库文件"""
    try:
        db_path = DATABASE_PATH
        
        if not os.path.exists(db_path):
            logger.error(f"数据库文件不存在: {db_path}")
            return jsonify({'success': False, 'error': '数据库文件不存在'}), 404
        
        # 生成带时间戳的文件名
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f'media_display_{timestamp}.db'
        
        logger.info(f"下载数据库: {db_path} -> {download_name}")
        
        return send_file(
            db_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/x-sqlite3'
        )
    except Exception as e:
        logger.error(f"下载数据库失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3400, debug=True)
