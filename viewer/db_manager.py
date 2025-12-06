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
        self._ensure_schema()
    
    def _ensure_connection(self):
        """确保数据库连接可用"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"数据库连接错误: {e}", exc_info=True)

    def _ensure_schema(self):
        """补充新增字段/索引，兼容旧库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='zone'")
        has_zone_table = cursor.fetchone()
        if not has_zone_table:
            conn.close()
            return

        cursor.execute("PRAGMA table_info(zone)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'is_fullscreen' not in columns:
            try:
                cursor.execute(
                    "ALTER TABLE zone ADD COLUMN is_fullscreen INTEGER NOT NULL DEFAULT 0 CHECK (is_fullscreen IN (0,1))"
                )
            except sqlite3.Error as e:
                logger.error(f"补充 is_fullscreen 字段失败: {e}")

        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_zone_fullscreen ON zone(is_fullscreen) WHERE is_fullscreen = 1"
        )

        # playlist_item 增加倒计时字段
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='playlist_item'")
        has_item_table = cursor.fetchone()
        if has_item_table:
            cursor.execute("PRAGMA table_info(playlist_item)")
            item_columns = [row[1] for row in cursor.fetchall()]
            if 'countdown_target' not in item_columns:
                try:
                    cursor.execute("ALTER TABLE playlist_item ADD COLUMN countdown_target TEXT")
                except sqlite3.Error as e:
                    logger.error(f"补充 countdown_target 字段失败: {e}")

        conn.commit()
        conn.close()
    
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

    def get_fullscreen_zone_code(self) -> Optional[str]:
        """获取当前标记为全屏的区域代码（如有多条取第一条）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT code FROM zone WHERE is_fullscreen = 1 ORDER BY id LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
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
                pi.countdown_target,
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
                "display_ms": self._safe_int(row["display_ms"], 5000),
                "loops": row["per_item_loops"] or 1,
                "scale_mode": row["scale_mode"] or "cover",
                "volume": row["volume"] if row["volume"] is not None else 1.0,
            }

            # 倒计时类型优先
            if row["countdown_target"]:
                item["kind"] = "countdown"
                item["countdown_target"] = row["countdown_target"]
                logger.debug(f"      → 类型: 倒计时，到期: {row['countdown_target']}")
            elif row["text_inline"]:
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
                    item["display_ms"] = self._safe_int(row["duration_ms"], item["display_ms"])
            
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

    def _safe_int(self, val, default: int) -> int:
        """将数据库读出的值转为正整数，异常时使用默认值"""
        try:
            v = int(val)
            return v if v > 0 else default
        except Exception:
            return default
