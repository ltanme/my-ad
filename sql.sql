-- 1) 区域表：固定枚举你当前布局中的区域
CREATE TABLE zone (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  code          TEXT UNIQUE NOT NULL,                      -- 机器可读：如 top_marquee, left_16x9 ...
  name          TEXT NOT NULL,                             -- 便于管理的显示名
  is_fullscreen INTEGER NOT NULL DEFAULT 0 CHECK (is_fullscreen IN (0,1)) -- 是否全屏
);

-- 只允许一个区域被标记为全屏
CREATE UNIQUE INDEX idx_zone_fullscreen ON zone(is_fullscreen) WHERE is_fullscreen = 1;

-- 建议的区域 code（供插入用）：
-- top_marquee        顶部跑马灯
-- left_16x9          中部左侧 16:9 容器
-- right_9x16         中部右侧 9:16 容器
-- extra_top          顶行最右侧竖条 上格
-- extra_bottom       顶行最右侧竖条 下格
-- bottom_cell_1      顶行下三格：左
-- bottom_cell_2      顶行下三格：中
-- bottom_cell_3      顶行下三格：右
-- bottom_strip       底部状态条（仅文字）

---------------------------------------------------------------------

-- 2) 媒体资源表：统一管理 文本/图片/视频 的来源（本地或 URL）
CREATE TABLE media_asset (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  kind          TEXT NOT NULL CHECK (kind IN ('text','image','video')),   -- 资源类型
  uri           TEXT NOT NULL,                                            -- 统一使用 URI：支持 http/https/file://
  -- 说明：本地路径如 /volume2/... 建议存成 file:///volume2/xxx.jpg；也可直接存绝对路径，但推荐 URI 统一化

  text_content  TEXT,                                                     -- 当 kind='text' 时的文本（跑马灯/底部文字）
  mime_hint     TEXT,                                                     -- 可选：image/jpeg, video/mp4 等
  format_hint   TEXT,                                                     -- 可选：jpg/png/mp4/avi 等（便于筛选）
  width         INTEGER,                                                  -- 可选：图片/视频宽（探测后可写回）
  height        INTEGER,                                                  -- 可选：图片/视频高
  duration_ms   INTEGER,                                                  -- 可选：视频时长（毫秒）；图片轮播时可作为默认驻留时间
  hash_sha1     TEXT,                                                     -- 可选：去重/校验
  meta_json     TEXT,                                                     -- 可选：额外元数据(JSON)

  created_at    DATETIME NOT NULL DEFAULT (datetime('now')),
  updated_at    DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_media_kind ON media_asset(kind);
CREATE INDEX idx_media_uri  ON media_asset(uri);

---------------------------------------------------------------------

-- 3) 播放列表：一个区域可有多个列表（方便 AB 切换/定时启用）
CREATE TABLE playlist (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  zone_id       INTEGER NOT NULL REFERENCES zone(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,                                  -- 播放列表名称
  is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  loop_mode     TEXT NOT NULL DEFAULT 'loop' CHECK (loop_mode IN ('loop','once')),
  notes         TEXT,
  created_at    DATETIME NOT NULL DEFAULT (datetime('now')),
  updated_at    DATETIME NOT NULL DEFAULT (datetime('now')),
  UNIQUE(zone_id, name)
);

CREATE INDEX idx_playlist_zone ON playlist(zone_id);

---------------------------------------------------------------------

-- 4) 播放项：把资源排到某个区域的某个播放列表里
CREATE TABLE playlist_item (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  playlist_id     INTEGER NOT NULL REFERENCES playlist(id) ON DELETE CASCADE,
  asset_id        INTEGER REFERENCES media_asset(id) ON DELETE CASCADE,

  -- 排序 & 时序
  play_order      INTEGER NOT NULL,                             -- 顺序（同一 playlist 内从小到大）
  display_ms      INTEGER,                                      -- 图片/文本驻留时间；为空则用资源/默认
  per_item_loops  INTEGER NOT NULL DEFAULT 1,                   -- 单项循环次数（如跑马灯每条文字=2）
                                                               -- 例：top_marquee 可设为 2，其它为 1

  -- 播放选项（按需）
  volume          REAL CHECK (volume BETWEEN 0.0 AND 1.0),      -- 视频音量（可空）
  scale_mode      TEXT NOT NULL DEFAULT 'cover'                 -- 尺寸策略：cover/fit（与你代码一致）
                   CHECK (scale_mode IN ('cover','fit')),
  active_from     DATETIME,                                     -- 可选：开始生效时间（排期）
  active_to       DATETIME,                                     -- 可选：结束生效时间
  enabled         INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),

  created_at      DATETIME NOT NULL DEFAULT (datetime('now')),
  updated_at      DATETIME NOT NULL DEFAULT (datetime('now')),

  -- 约束：当资源为文本时，asset_id 可空，只用 text_inline；反之必须有 asset_id
  text_inline     TEXT,                                         -- 直接内嵌的文本（便于跑马灯/底部快速配置）
  CHECK (
    (text_inline IS NOT NULL AND asset_id IS NULL)
    OR
    (text_inline IS NULL AND asset_id IS NOT NULL)
  )
);

CREATE INDEX idx_item_playlist_order ON playlist_item(playlist_id, play_order);
CREATE INDEX idx_item_active_window ON playlist_item(active_from, active_to);
CREATE INDEX idx_item_enabled ON playlist_item(enabled);
