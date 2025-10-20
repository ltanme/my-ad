#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库操作辅助类
"""
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from config import DATABASE_PATH

# 北京时区 UTC+8
BEIJING_TZ = timezone(timedelta(hours=8))


def get_beijing_time():
    """获取北京时间字符串"""
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')


class DBHelper:
    """数据库操作辅助类"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========== 区域相关 ==========
    def get_zone_by_code(self, zone_code: str) -> Optional[Dict]:
        """根据区域代码获取区域信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM zone WHERE code = ?", (zone_code,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    # ========== 播放列表相关 ==========
    def get_playlists_by_zone(self, zone_code: str) -> List[Dict]:
        """获取指定区域的所有播放列表"""
        zone = self.get_zone_by_code(zone_code)
        if not zone:
            return []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM playlist 
            WHERE zone_id = ? 
            ORDER BY is_active DESC, id DESC
        """, (zone['id'],))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_playlist(self, playlist_id: int) -> Optional[Dict]:
        """获取播放列表详情"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM playlist WHERE id = ?", (playlist_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def create_playlist(self, zone_code: str, name: str, loop_mode: str = 'loop') -> int:
        """创建播放列表"""
        zone = self.get_zone_by_code(zone_code)
        if not zone:
            raise ValueError(f"区域不存在: {zone_code}")
        
        beijing_time = get_beijing_time()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO playlist (zone_id, name, loop_mode, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (zone['id'], name, loop_mode, beijing_time, beijing_time))
        playlist_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return playlist_id
    
    def update_playlist(self, playlist_id: int, name: str, loop_mode: str, is_active: int):
        """更新播放列表"""
        beijing_time = get_beijing_time()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE playlist 
            SET name = ?, loop_mode = ?, is_active = ?, updated_at = ?
            WHERE id = ?
        """, (name, loop_mode, is_active, beijing_time, playlist_id))
        conn.commit()
        conn.close()
    
    def delete_playlist(self, playlist_id: int):
        """删除播放列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM playlist WHERE id = ?", (playlist_id,))
        conn.commit()
        conn.close()
    
    def set_active_playlist(self, zone_code: str, playlist_id: int):
        """设置活跃播放列表"""
        zone = self.get_zone_by_code(zone_code)
        if not zone:
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        # 先将该区域所有列表设为非活跃
        cursor.execute("UPDATE playlist SET is_active = 0 WHERE zone_id = ?", (zone['id'],))
        # 设置指定列表为活跃
        cursor.execute("UPDATE playlist SET is_active = 1 WHERE id = ?", (playlist_id,))
        conn.commit()
        conn.close()
    
    # ========== 播放项相关 ==========
    def get_playlist_items(self, playlist_id: int) -> List[Dict]:
        """获取播放列表的所有项"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pi.*, ma.kind, ma.uri, ma.text_content
            FROM playlist_item pi
            LEFT JOIN media_asset ma ON pi.asset_id = ma.id
            WHERE pi.playlist_id = ?
            ORDER BY pi.created_at DESC
        """, (playlist_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def add_playlist_item(self, playlist_id: int, asset_id: Optional[int] = None, 
                         text_inline: Optional[str] = None, display_ms: int = 5000,
                         play_order: Optional[int] = None):
        """添加播放项"""
        if play_order is None:
            # 获取当前最大序号
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(play_order) FROM playlist_item WHERE playlist_id = ?", (playlist_id,))
            max_order = cursor.fetchone()[0]
            play_order = (max_order or 0) + 1
            conn.close()
        
        beijing_time = get_beijing_time()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO playlist_item 
            (playlist_id, asset_id, text_inline, display_ms, play_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (playlist_id, asset_id, text_inline, display_ms, play_order, beijing_time, beijing_time))
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return item_id
    
    def delete_playlist_item(self, item_id: int):
        """删除播放项"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM playlist_item WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
    
    def update_item_order(self, item_id: int, new_order: int):
        """更新播放项顺序"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE playlist_item SET play_order = ? WHERE id = ?", (new_order, item_id))
        conn.commit()
        conn.close()
    
    # ========== 媒体资源相关 ==========
    def create_media_asset(self, kind: str, uri: str, text_content: Optional[str] = None,
                          duration_ms: Optional[int] = None) -> int:
        """创建媒体资源"""
        beijing_time = get_beijing_time()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO media_asset (kind, uri, text_content, duration_ms, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (kind, uri, text_content, duration_ms, beijing_time, beijing_time))
        asset_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return asset_id
    
    def get_media_asset(self, asset_id: int) -> Optional[Dict]:
        """获取媒体资源"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media_asset WHERE id = ?", (asset_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
