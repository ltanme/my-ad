#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
媒体显示系统数据库初始化脚本
独立运行，初始化项目所需的数据库
"""

import sqlite3
import os
import sys
from pathlib import Path

# 获取项目根目录和配置目录
PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_DIR.mkdir(exist_ok=True)  # 确保config目录存在
DB_PATH = str(CONFIG_DIR / "media_display.db")

print("=" * 60)
print("媒体显示系统数据库初始化")
print("=" * 60)
print(f"项目根目录: {PROJECT_ROOT}")
print(f"配置目录: {CONFIG_DIR}")
print(f"数据库路径: {DB_PATH}")
print("=" * 60)
print()

# SQL 建表语句
SCHEMA_SQL = """
-- 1) 区域表：固定枚举你当前布局中的区域
CREATE TABLE IF NOT EXISTS zone (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  code          TEXT UNIQUE NOT NULL,
  name          TEXT NOT NULL,
  is_fullscreen INTEGER NOT NULL DEFAULT 0 CHECK (is_fullscreen IN (0,1))
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

-- 只允许一个区域被标记为全屏
CREATE UNIQUE INDEX IF NOT EXISTS idx_zone_fullscreen ON zone(is_fullscreen) WHERE is_fullscreen = 1;

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
    
    if db_exists:
        print(f"⚠️  数据库文件已存在: {db_path}")
        print("   将更新表结构（不会删除现有数据）")
        print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 执行建表语句
        print("创建数据库表结构...")
        cursor.executescript(SCHEMA_SQL)
        print("✓ 表结构创建完成")
        print()

        # 确保 is_fullscreen 字段存在（旧库兼容）
        cursor.execute("PRAGMA table_info(zone)")
        zone_columns = [row[1] for row in cursor.fetchall()]
        if 'is_fullscreen' not in zone_columns:
            print("为 zone 表增加 is_fullscreen 字段...")
            cursor.execute(
                "ALTER TABLE zone ADD COLUMN is_fullscreen INTEGER NOT NULL DEFAULT 0 CHECK (is_fullscreen IN (0,1))"
            )
            print("✓ 已补充 is_fullscreen 字段")

        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_zone_fullscreen ON zone(is_fullscreen) WHERE is_fullscreen = 1"
        )
        
        # 插入初始区域数据（如果表为空）
        cursor.execute("SELECT COUNT(*) FROM zone")
        zone_count = cursor.fetchone()[0]
        
        if zone_count == 0:
            print("插入初始区域数据...")
            cursor.executemany(
                "INSERT INTO zone (code, name) VALUES (?, ?)",
                INITIAL_ZONES
            )
            print(f"✓ 已插入 {len(INITIAL_ZONES)} 个初始区域")
        else:
            print(f"✓ 区域表已有 {zone_count} 条记录，跳过初始化")
        print()
        
        # 初始化 reload_signal 表（如果为空）
        cursor.execute("SELECT COUNT(*) FROM reload_signal")
        signal_count = cursor.fetchone()[0]
        
        if signal_count == 0:
            print("初始化重载信号表...")
            cursor.execute("INSERT INTO reload_signal (id, need_reload) VALUES (1, 0)")
            print("✓ 重载信号表初始化完成")
        else:
            print("✓ 重载信号表已初始化")
        print()
        
        conn.commit()
        
        # 显示表信息
        print("=" * 60)
        print("数据库表统计:")
        print("=" * 60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  {table[0]:<20} {count:>6} 条记录")
        
        conn.close()
        
        print("=" * 60)
        print()
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ 数据库错误: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        if 'conn' in locals():
            conn.close()
        return False


def verify_database():
    """验证数据库是否正确初始化"""
    print("验证数据库...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查必需的表
        required_tables = ['zone', 'media_asset', 'playlist', 'playlist_item', 'reload_signal']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"✗ 缺少表: {', '.join(missing_tables)}")
            conn.close()
            return False
        
        # 检查区域数据
        cursor.execute("SELECT COUNT(*) FROM zone")
        zone_count = cursor.fetchone()[0]
        
        if zone_count == 0:
            print("✗ 区域表为空")
            conn.close()
            return False
        
        conn.close()
        print("✓ 数据库验证通过")
        print()
        return True
        
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return False


def main():
    """主函数"""
    
    # 初始化数据库
    success = init_database()
    
    if not success:
        print()
        print("=" * 60)
        print("✗ 数据库初始化失败")
        print("=" * 60)
        sys.exit(1)
    
    # 验证数据库
    if not verify_database():
        print()
        print("=" * 60)
        print("✗ 数据库验证失败")
        print("=" * 60)
        sys.exit(1)
    
    # 成功
    print("=" * 60)
    print("✓ 数据库初始化完成！")
    print("=" * 60)
    print()
    print("数据库文件:")
    print(f"  {os.path.abspath(DB_PATH)}")
    print()
    print("现在可以启动以下服务:")
    print("  1. Admin 服务:    python admin/app.py")
    print("  2. Schedule 服务: python schedule/app.py")
    print("  3. Viewer 服务:   python viewer/main.py")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
