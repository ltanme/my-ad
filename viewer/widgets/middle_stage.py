#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中部舞台布局组件
管理16:9、9:16主显示区域，以及右侧竖条和底部三格
"""

import os
import sys
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer, QRect
from PyQt5.QtMultimedia import QMediaPlayer
from .media_frame import MediaFrame

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import get_logger

logger = get_logger()


class MiddleStage(QWidget):
    """中部舞台 - 管理所有显示区域的布局和内容"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 主显示区域
        self.left_16x9  = MediaFrame("", border_color="yellow")
        self.right_9x16 = MediaFrame("", border_color="yellow")
        # 顶行右侧竖条
        self.extra_top  = MediaFrame("上格", border_color="red")
        self.extra_bot  = MediaFrame("下格", border_color="red")
        # 底部三格
        self.bottom_cells = [MediaFrame(f"格{i+1}", border_color="cyan") for i in range(3)]

        # 全屏占位框（仅在全屏模式下展示）
        self.fullscreen_zone = None
        self.fullscreen_frame = MediaFrame("全屏区域", border_color="orange")

        for w in [self.left_16x9, self.right_9x16, self.extra_top, self.extra_bot, *self.bottom_cells, self.fullscreen_frame]:
            w.setParent(self)
            w.show()

        self.fullscreen_frame.hide()

        self.bind_demo()

    def bind_demo(self):
        """演示模式 - 显示默认文字"""
        self.left_16x9.set_text("左侧 16:9（黄色框）")
        self.right_9x16.set_text("右侧 9:16（黄色框）")
        self.extra_top.set_text("资讯 A（红框）")
        self.extra_bot.set_text("资讯 B（红框）")
        for i, cell in enumerate(self.bottom_cells, 1):
            cell.set_text(f"格子 {i}（青框）")

    def _stop_all_frames(self):
        """停止所有播放器，避免隐藏时仍占用资源"""
        for frame in [self.left_16x9, self.right_9x16, self.extra_top, self.extra_bot, *self.bottom_cells, self.fullscreen_frame]:
            frame.stop()

    def load_from_database(self, db_manager, fullscreen_zone=None):
        """从数据库加载内容"""
        if not db_manager:
            return

        self._stop_all_frames()
        self.fullscreen_zone = fullscreen_zone

        normal_frames = [
            self.left_16x9,
            self.right_9x16,
            self.extra_top,
            self.extra_bot,
            *self.bottom_cells,
        ]

        if fullscreen_zone:
            self.fullscreen_frame.set_fullscreen_mode(True)
            for f in normal_frames:
                f.hide()
            self._load_fullscreen_zone(db_manager, fullscreen_zone)
            return
        else:
            self.fullscreen_frame.set_fullscreen_mode(False)
            for f in normal_frames:
                f.show()
            self.fullscreen_frame.hide()
            self.fullscreen_zone = None

        # 左侧 16:9 - 支持图片+视频混合播放
        self.left_16x9.name = "左侧16:9"
        items = db_manager.get_playlist_items("left_16x9", limit=20)
        logger.info(f"[左侧16:9] 从数据库获取到 {len(items)} 个播放项")
        if items:
            self._start_mixed_playlist(self.left_16x9, items)
        else:
            logger.warning(f"[左侧16:9] 没有播放项，显示默认文字")
        
        # 右侧 9:16 - 支持图片+视频混合播放
        self.right_9x16.name = "右侧9:16"
        items = db_manager.get_playlist_items("right_9x16", limit=20)
        logger.info(f"[右侧9:16] 从数据库获取到 {len(items)} 个播放项")
        if items:
            self._start_mixed_playlist(self.right_9x16, items)
        else:
            logger.warning(f"[右侧9:16] 没有播放项，显示默认文字")
        
        # 顶行右侧两格
        self.extra_top.name = "右上格"
        items = db_manager.get_playlist_items("extra_top", limit=20)
        if items:
            txts = [it.get("text") for it in items if it.get("text")]
            if txts:
                self.extra_top.set_text("\n".join(txts))
        
        self.extra_bot.name = "右下格"
        items = db_manager.get_playlist_items("extra_bottom", limit=20)
        if items:
            txts = [it.get("text") for it in items if it.get("text")]
            if txts:
                self.extra_bot.set_text("\n".join(txts))
        
        # 底部三格
        for i, cell in enumerate(self.bottom_cells, 1):
            cell.name = f"底部格{i}"
            items = db_manager.get_playlist_items(f"bottom_cell_{i}", limit=20)
            if items:
                txts = [it.get("text") for it in items if it.get("text")]
                if txts:
                    cell.set_text("\n".join(txts))

    def _load_fullscreen_zone(self, db_manager, zone_code: str):
        """加载并播放指定区域的全屏内容"""
        self.fullscreen_zone = zone_code
        self.fullscreen_frame.name = f"全屏:{zone_code}"
        items = db_manager.get_playlist_items(zone_code, limit=50)

        logger.info(f"[全屏模式] 区域 {zone_code} 播放项: {len(items)}")
        if items:
            self._start_mixed_playlist(self.fullscreen_frame, items)
        else:
            self.fullscreen_frame.set_text(f"{zone_code}\n暂无播放内容")

        self.fullscreen_frame.show()
        area = self.rect().adjusted(6, 6, -6, -6)
        self.fullscreen_frame.setGeometry(area)
        self.fullscreen_frame.raise_()

    def _start_mixed_playlist(self, frame: MediaFrame, items: list):
        """启动混合播放列表：图片+视频+文字按顺序循环"""
        if not items:
            logger.warning(f"[{frame.name}] 播放列表为空")
            return
        
        logger.info(f"[{frame.name}] 开始构建混合播放列表，共 {len(items)} 个项目")
        
        playlist = []
        for idx, item in enumerate(items, 1):
            kind = item.get("kind")
            item_id = item.get("id")
            
            if kind == "image":
                uri = item.get("uri")
                if uri:
                    logger.debug(f"[{frame.name}] 项目 {idx}: 图片 - {uri}")
                    playlist.append({
                        "type": "image",
                        "uri": uri,
                        "display_ms": item.get("display_ms", 5000),
                        "item_id": item_id
                    })
                else:
                    logger.warning(f"[{frame.name}] 项目 {idx}: 图片 URI 为空")
                    
            elif kind == "video":
                uri = item.get("uri")
                if uri:
                    logger.debug(f"[{frame.name}] 项目 {idx}: 视频 - {uri}")
                    playlist.append({
                        "type": "video",
                        "uri": uri,
                        "item_id": item_id
                    })
                else:
                    logger.warning(f"[{frame.name}] 项目 {idx}: 视频 URI 为空")
                    
            elif kind == "text":
                text = item.get("text")
                if text:
                    logger.debug(f"[{frame.name}] 项目 {idx}: 文字 - {text[:30]}...")
                    playlist.append({
                        "type": "text",
                        "text": text,
                        "display_ms": item.get("display_ms", 5000),
                        "item_id": item_id
                    })
                else:
                    logger.warning(f"[{frame.name}] 项目 {idx}: 文字内容为空")
        
        if not playlist:
            logger.error(f"[{frame.name}] 没有有效的播放项")
            return
        
        logger.info(f"[{frame.name}] ✓ 构建完成，有效播放项: {len(playlist)}/{len(items)}")
        
        frame._mixed_playlist = playlist
        frame._mixed_index = 0
        self._play_mixed_item(frame, 0)

    def _play_mixed_item(self, frame: MediaFrame, index: int):
        """播放混合列表中的指定项"""
        if not hasattr(frame, '_mixed_playlist') or not frame._mixed_playlist:
            return
        
        if index >= len(frame._mixed_playlist):
            index = 0
        
        frame._mixed_index = index
        item = frame._mixed_playlist[index]
        item_type = item.get("type")
        item_id = item.get("item_id")
        
        print(f"[{frame.name}] 播放第 {index+1}/{len(frame._mixed_playlist)} 项: {item_type} (ID: {item_id})")
        
        # 显示资源ID
        if item_id:
            frame.set_resource_id(item_id)
        else:
            frame.clear_resource_id()
        
        if item_type == "text":
            display_ms = item.get("display_ms", 5000)
            frame.set_text(item.get("text", ""), display_ms=display_ms)
            QTimer.singleShot(display_ms, lambda: self._play_next_mixed_item(frame))
        
        elif item_type == "image":
            uri = item.get("uri")
            display_ms = item.get("display_ms", 5000)
            frame.set_image(uri, cover=True, display_ms=display_ms)
            QTimer.singleShot(display_ms, lambda: self._play_next_mixed_item(frame))
        
        elif item_type == "video":
            uri = item.get("uri")
            try:
                frame.player.mediaStatusChanged.disconnect()
            except:
                pass
            frame.player.mediaStatusChanged.connect(
                lambda status: self._on_video_status(frame, status)
            )
            frame.play_videos([uri], loop=False)

    def _play_next_mixed_item(self, frame: MediaFrame):
        """播放下一项"""
        if not hasattr(frame, '_mixed_playlist'):
            return
        next_index = (frame._mixed_index + 1) % len(frame._mixed_playlist)
        self._play_mixed_item(frame, next_index)

    def _on_video_status(self, frame: MediaFrame, status):
        """视频状态变化回调"""
        if status == QMediaPlayer.EndOfMedia:
            print(f"[{frame.name}] 视频播放完成")
            QTimer.singleShot(500, lambda: self._play_next_mixed_item(frame))

    def resizeEvent(self, e):
        """窗口大小变化时重新布局"""
        super().resizeEvent(e)
        GUT = 6
        area: QRect = self.rect().adjusted(GUT, GUT, -GUT, -GUT)
        if area.width() <= 0 or area.height() <= 0:
            return

        if self.fullscreen_zone:
            self.fullscreen_frame.setGeometry(area.x(), area.y(), area.width(), area.height())
            return

        ax, ay = area.x(), area.y()
        aw, ah = area.width(), area.height()

        # 顶行：并排 16:9 与 9:16
        sum_ratio = (16 / 9) + (9 / 16)
        h_top_max = int(min(ah, (aw - GUT) / sum_ratio))
        w16 = int((16 / 9) * h_top_max)
        w9  = int((9 / 16) * h_top_max)

        scale = 0.8
        h_top = max(0, int(h_top_max * scale))
        w16s  = max(0, int(w16 * scale))
        w9s   = max(0, int(w9  * scale))

        # 顶行放置
        x, y = ax, ay
        self.left_16x9.setGeometry(x, y, w16s, h_top)
        self.right_9x16.setGeometry(x + w16s + GUT, y, w9s, h_top)

        # 右侧竖条
        used_w = w16s + GUT + w9s
        strip_w = aw - used_w - GUT
        if strip_w > 0:
            half_h = (h_top - GUT) // 2
            top_x, top_y = x + used_w + GUT, y
            bot_x, bot_y = top_x, y + half_h + GUT
            top_w, top_h = strip_w, max(0, half_h)
            bot_w, bot_h = strip_w, max(0, h_top - half_h - GUT)
            self.extra_top.setGeometry(top_x, top_y, max(0, top_w), max(0, top_h))
            self.extra_bot.setGeometry(bot_x, bot_y, max(0, bot_w), max(0, bot_h))
        else:
            self.extra_top.setGeometry(0, 0, 0, 0)
            self.extra_bot.setGeometry(0, 0, 0, 0)

        # 底部三格
        y_rest = y + h_top + GUT
        h_rest = ah - (h_top + GUT)
        if h_rest > 0:
            cell_w = max(0, (aw - 2 * GUT) // 3)
            for i in range(3):
                cx = ax + i * (cell_w + GUT)
                self.bottom_cells[i].setGeometry(cx, y_rest, cell_w, h_rest)
        else:
            for b in self.bottom_cells:
                b.setGeometry(0, 0, 0, 0)
