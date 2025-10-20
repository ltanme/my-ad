#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from logger_config import get_logger

logger = get_logger()


class MediaDBManager:
    """媒体数据库管理器"""
    
    def __init__(self, db_path="media_display.db"):
        self.db_path = db_path
        self._ensure_connection()
    
    def _ensure_connection(self):
        """确保数据库连接可用"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"数据库连接错误: {e}", exc_info=True)
    
    def get_zone_id(self, zone_code: str) -> Optional[int]:
        """根据区域代码获取区域ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM zone WHERE code = ?", (zone_code,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def get_active_playlist(self, zone_code: str) -> Optional[Dict]:
        """获取指定区域的活跃播放列表"""
        zone_id = self.get_zone_id(zone_code)
        if not zone_id:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, loop_mode 
            FROM playlist 
            WHERE zone_id = ? AND is_active = 1 
            ORDER BY id DESC 
            LIMIT 1
        """, (zone_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"id": row[0], "name": row[1], "loop_mode": row[2]}
        return None
    
    def get_playlist_items(self, zone_code: str, limit: int = 10) -> List[Dict]:
        """
        获取指定区域的播放项列表（最新10条）
        返回格式: [{"kind": "text/image/video", "uri": "...", "text": "...", 
                    "display_ms": 5000, "loops": 2, "scale_mode": "cover"}, ...]
        """
        logger.info(f"查询区域播放项: {zone_code}")
        
        playlist = self.get_active_playlist(zone_code)
        if not playlist:
            logger.warning(f"区域 {zone_code} 没有活跃的播放列表")
            return []
        
        logger.info(f"找到播放列表: {playlist['name']} (ID={playlist['id']})")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            SELECT 
                pi.id as item_id,
                pi.text_inline,
                pi.display_ms,
                pi.per_item_loops,
                pi.scale_mode,
                pi.volume,
                pi.asset_id,
                ma.kind,
                ma.uri,
                ma.text_content,
                ma.duration_ms
            FROM playlist_item pi
            LEFT JOIN media_asset ma ON pi.asset_id = ma.id
            WHERE pi.playlist_id = ? 
              AND pi.enabled = 1
              AND (pi.active_from IS NULL OR pi.active_from <= ?)
              AND (pi.active_to IS NULL OR pi.active_to >= ?)
            ORDER BY pi.play_order ASC
            LIMIT ?
        """, (playlist["id"], now, now, limit))
        
        items = []
        rows = cursor.fetchall()
        logger.info(f"查询到 {len(rows)} 条播放项")
        
        for idx, row in enumerate(rows, 1):
            logger.debug(f"  [{idx}] item_id={row['item_id']}, asset_id={row['asset_id']}")
            logger.debug(f"      text_inline={row['text_inline']}")
            logger.debug(f"      ma.kind={row['kind']}, ma.uri={row['uri']}")
            
            item = {
                "id": row["item_id"],  # 添加播放项ID
                "kind": None,
                "uri": None,
                "text": row["text_inline"] or row["text_content"],
                "display_ms": row["display_ms"] or 5000,
                "loops": row["per_item_loops"] or 1,
                "scale_mode": row["scale_mode"] or "cover",
                "volume": row["volume"] if row["volume"] is not None else 1.0,
            }
            
            if row["text_inline"]:
                item["kind"] = "text"
                logger.debug(f"      → 类型: 内联文本")
            else:
                item["kind"] = row["kind"]
                # 规范化URI：去掉 file:// 前缀
                raw_uri = row["uri"]
                item["uri"] = self.normalize_uri(raw_uri) if raw_uri else None
                logger.debug(f"      → 类型: {item['kind']}")
                logger.debug(f"         原始URI: {raw_uri}")
                logger.debug(f"         规范化URI: {item['uri']}")
                if item["kind"] == "video" and row["duration_ms"]:
                    item["display_ms"] = row["duration_ms"]
            
            items.append(item)
        
        conn.close()
        logger.info(f"返回 {len(items)} 条有效项目")
        return items
    
    def normalize_uri(self, uri: str) -> str:
        """
        规范化 URI：
        - file:///path -> /path
        - http/https -> 保持不变
        - 相对路径 -> 保持不变
        """
        if uri.startswith("file://"):
            return uri[7:]  # 去掉 file://
        return uri
