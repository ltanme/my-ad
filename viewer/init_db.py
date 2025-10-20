#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from pathlib import Path

# 获取config目录下的数据库路径（绝对路径）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_DIR.mkdir(exist_ok=True)  # 确保config目录存在
DB_PATH = str(CONFIG_DIR / "media_display.db")

print(f"项目根目录: {PROJECT_ROOT}")
print(f"配置目录: {CONFIG_DIR}")
print(f"数据库路径: {DB_PATH}")

# SQL 建表语句
SCHEMA_SQL = """
-- 1) 区域表：固定枚举你当前布局中的区域
CREATE TABLE IF NOT EXISTS zone (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  code          TEXT UNIQUE NOT NULL,
  name          TEXT NOT NULL
);

-- 2) 媒体资源表：统一管理 文本/图片/视频 的来源（本地或 URL）
CREATE TABLE IF NOT EXISTS media_asset (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  kind          TEXT NOT NULL CHECK (kind IN ('text','image','video')),
  uri           TEXT NOT NULL,
  text_content  TEXT,
  mime_hint     TEXT,
  format_hint   TEXT,
  width         INTEGER,
  height        INTEGER,
  duration_ms   INTEGER,
  hash_sha1     TEXT,
  meta_json     TEXT,
  created_at    DATETIME NOT NULL DEFAULT (datetime('now')),
  updated_at    DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_media_kind ON media_asset(kind);
CREATE INDEX IF NOT EXISTS idx_media_uri  ON media_asset(uri);

-- 3) 播放列表：一个区域可有多个列表（方便 AB 切换/定时启用）
CREATE TABLE IF NOT EXISTS playlist (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  zone_id       INTEGER NOT NULL REFERENCES zone(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  loop_mode     TEXT NOT NULL DEFAULT 'loop' CHECK (loop_mode IN ('loop','once')),
  notes         TEXT,
  created_at    DATETIME NOT NULL DEFAULT (datetime('now')),
  updated_at    DATETIME NOT NULL DEFAULT (datetime('now')),
  UNIQUE(zone_id, name)
);

CREATE INDEX IF NOT EXISTS idx_playlist_zone ON playlist(zone_id);

-- 4) 播放项：把资源排到某个区域的某个播放列表里
CREATE TABLE IF NOT EXISTS playlist_item (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  playlist_id     INTEGER NOT NULL REFERENCES playlist(id) ON DELETE CASCADE,
  asset_id        INTEGER REFERENCES media_asset(id) ON DELETE CASCADE,
  play_order      INTEGER NOT NULL,
  display_ms      INTEGER,
  per_item_loops  INTEGER NOT NULL DEFAULT 1,
  volume          REAL CHECK (volume BETWEEN 0.0 AND 1.0),
  scale_mode      TEXT NOT NULL DEFAULT 'cover' CHECK (scale_mode IN ('cover','fit')),
  active_from     DATETIME,
  active_to       DATETIME,
  enabled         INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),
  created_at      DATETIME NOT NULL DEFAULT (datetime('now')),
  updated_at      DATETIME NOT NULL DEFAULT (datetime('now')),
  text_inline     TEXT,
  CHECK (
    (text_inline IS NOT NULL AND asset_id IS NULL)
    OR
    (text_inline IS NULL AND asset_id IS NOT NULL)
  )
);

CREATE INDEX IF NOT EXISTS idx_item_playlist_order ON playlist_item(playlist_id, play_order);
CREATE INDEX IF NOT EXISTS idx_item_active_window ON playlist_item(active_from, active_to);
CREATE INDEX IF NOT EXISTS idx_item_enabled ON playlist_item(enabled);

-- 5) 重载信号表：用于通知 viewer 刷新内容
CREATE TABLE IF NOT EXISTS reload_signal (
  id              INTEGER PRIMARY KEY CHECK (id = 1),
  need_reload     INTEGER NOT NULL DEFAULT 0 CHECK (need_reload IN (0,1)),
  updated_at      DATETIME NOT NULL DEFAULT (datetime('now'))
);
"""

# 初始区域数据
INITIAL_ZONES = [
    ('top_marquee', '顶部跑马灯'),
    ('left_16x9', '中部左侧 16:9 容器'),
    ('right_9x16', '中部右侧 9:16 容器'),
    ('extra_top', '顶行最右侧竖条 上格'),
    ('extra_bottom', '顶行最右侧竖条 下格'),
    ('bottom_cell_1', '顶行下三格：左'),
    ('bottom_cell_2', '顶行下三格：中'),
    ('bottom_cell_3', '顶行下三格：右'),
    ('bottom_strip', '底部状态条（仅文字）'),
]


def init_database(db_path=DB_PATH):
    """初始化数据库：创建表结构并插入初始区域数据"""
    
    # 检查数据库是否已存在
    db_exists = os.path.exists(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 执行建表语句
        cursor.executescript(SCHEMA_SQL)
        
        # 插入初始区域数据（如果表为空）
        cursor.execute("SELECT COUNT(*) FROM zone")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO zone (code, name) VALUES (?, ?)",
                INITIAL_ZONES
            )
            print(f"✓ 已插入 {len(INITIAL_ZONES)} 个初始区域")
        
        # 初始化 reload_signal 表（如果为空）
        cursor.execute("SELECT COUNT(*) FROM reload_signal")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO reload_signal (id, need_reload) VALUES (1, 0)")
            print(f"✓ 已初始化 reload_signal 表")
        
        conn.commit()
        
        if db_exists:
            print(f"✓ 数据库已更新: {db_path}")
        else:
            print(f"✓ 数据库已创建: {db_path}")
        
        # 显示表信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"\n数据库表列表:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} 条记录")
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ 数据库错误: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("初始化媒体显示系统数据库")
    print("=" * 60)
    
    success = init_database()
    
    if success:
        print("\n✓ 数据库初始化完成！")
        print(f"\n数据库文件: {os.path.abspath(DB_PATH)}")
    else:
        print("\n✗ 数据库初始化失败")
        exit(1)
