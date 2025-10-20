#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
媒体显示框架组件
支持文本、图片、GIF、视频的显示，带倒计时功能
"""

import platform
from PyQt5.QtWidgets import QFrame, QLabel, QSizePolicy, QStackedLayout
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget


class MediaFrame(QFrame):
    """
    媒体显示框架
    使用 QStackedLayout 切换显示层（文本/图片层 和 视频层）
    支持右下角倒计时显示
    """
    
    def __init__(self, name="", parent=None, border_color="yellow"):
        super().__init__(parent)
        self.name = name
        self._movie = None
        self.player = QMediaPlayer(self)
        self.playlist = QMediaPlaylist(self)
        self.player.setPlaylist(self.playlist)
        self._cover_images = True

        self.setStyleSheet(f"QFrame {{ background-color:black; border:5px solid {border_color}; }}")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 叠层布局
        self.stack = QStackedLayout(self)
        self.stack.setContentsMargins(5, 5, 5, 5)
        self.stack.setStackingMode(QStackedLayout.StackAll)

        # 文本/图片层
        self.content_label = QLabel(self.name, self)
        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("border:none; color:white; font-size:28px; font-weight:bold;")
        self.content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 倒计时定时器
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._update_countdown)
        self._countdown_remaining = 0
        
        # 资源ID标签（左上角）
        self.resource_id_label = QLabel("", self)
        self.resource_id_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 150);
                color: #00ff00;
                font-size: 18px;
                font-weight: bold;
                padding: 5px 10px;
                border: none;
                border-radius: 3px;
            }
        """)
        self.resource_id_label.setAlignment(Qt.AlignCenter)
        self.resource_id_label.setAttribute(Qt.WA_TranslucentBackground)
        self.resource_id_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.resource_id_label.setAutoFillBackground(False)
        self.resource_id_label.hide()
        self.resource_id_label.raise_()
        
        # 倒计时标签（右下角）
        self.countdown_label = QLabel("", self)
        self.countdown_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 120);
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 8px 12px;
                border: none;
            }
        """)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setAttribute(Qt.WA_TranslucentBackground)
        self.countdown_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.countdown_label.setAutoFillBackground(False)
        self.countdown_label.hide()
        self.countdown_label.raise_()

        # 视频层
        self.video_widget = QVideoWidget(self)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_widget.setAspectRatioMode(Qt.KeepAspectRatioByExpanding)
        if platform.system() == "Darwin":
            self.video_widget.setAttribute(Qt.WA_NativeWindow, True)

        self.player.setVideoOutput(self.video_widget)

        self.stack.addWidget(self.content_label)
        self.stack.addWidget(self.video_widget)
        self.stack.setCurrentWidget(self.content_label)

        # 连接信号
        self.player.error.connect(self._on_player_error)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.durationChanged.connect(self._on_video_duration_changed)
        self.player.positionChanged.connect(self._on_video_position_changed)
    
    def set_resource_id(self, resource_id):
        """设置并显示资源ID"""
        print(f"[MediaFrame] set_resource_id called: {resource_id}")
        if resource_id:
            text = f"#{resource_id}"
            self.resource_id_label.setText(text)
            self.resource_id_label.show()
            self._update_label_positions()
            print(f"[MediaFrame] 资源ID标签已显示: {text}, visible={self.resource_id_label.isVisible()}")
        else:
            self.resource_id_label.hide()
            print(f"[MediaFrame] 资源ID标签已隐藏")
    
    def clear_resource_id(self):
        """清除资源ID显示"""
        self.resource_id_label.hide()

    def set_text(self, text: str, display_ms=0):
        """显示文本"""
        if self._movie:
            self._movie.stop()
            self._movie = None
            self.content_label.setMovie(None)
        self.content_label.setPixmap(QPixmap())
        self.content_label.setText(text or "")
        self.stack.setCurrentWidget(self.content_label)
        
        if display_ms > 0:
            self._start_countdown(display_ms)
        else:
            self._stop_countdown()

    def set_image(self, path: str, cover=True, display_ms=5000):
        """显示图片"""
        self._cover_images = cover
        if self._movie:
            self._movie.stop()
            self._movie = None
            self.content_label.setMovie(None)
        pm = QPixmap(path)
        if pm.isNull():
            self.set_text("图片加载失败")
            return
        self._apply_pixmap(pm)
        self.stack.setCurrentWidget(self.content_label)
        self._start_countdown(display_ms)
        # 确保标签在最上层
        self.resource_id_label.raise_()
        self.countdown_label.raise_()

    def _apply_pixmap(self, pm: QPixmap):
        """应用图片（cover模式填满）"""
        target_w = max(1, self.width() - 10)
        target_h = max(1, self.height() - 10)
        
        if self._cover_images:
            scaled = pm.scaled(target_w, target_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x_off = max(0, (scaled.width() - target_w) // 2)
            y_off = max(0, (scaled.height() - target_h) // 2)
            cropped = scaled.copy(x_off, y_off, target_w, target_h)
            self.content_label.setPixmap(cropped)
        else:
            scaled = pm.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.content_label.setPixmap(scaled)

    def set_gif(self, gif_path: str):
        """显示GIF动画"""
        mv = QMovie(gif_path)
        if not mv.isValid():
            self.set_text("GIF 无效")
            return
        self._movie = mv
        mv.setCacheMode(QMovie.CacheAll)
        mv.setScaledSize(self.content_label.size())
        self.content_label.setMovie(mv)
        mv.start()
        self.stack.setCurrentWidget(self.content_label)

    def play_videos(self, items, loop=True, start_index=0):
        """播放视频列表"""
        self.playlist.clear()
        for p in items or []:
            url = QUrl.fromLocalFile(p) if self._looks_like_local(p) else QUrl(p)
            self.playlist.addMedia(QMediaContent(url))
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop if loop else QMediaPlaylist.Sequential)
        self.playlist.setCurrentIndex(max(0, start_index))
        self.stack.setCurrentWidget(self.video_widget)
        self.player.play()
        # 确保标签在最上层
        self.resource_id_label.raise_()
        self.countdown_label.raise_()

    def _looks_like_local(self, p: str) -> bool:
        return p.startswith(("/", "./", "../")) or p.lower().startswith("file://")

    def _on_player_error(self):
        print(f"[{self.name}] 播放器错误: {self.player.error()} - {self.player.errorString()}")

    def _on_media_status_changed(self, status):
        pass

    def _on_video_duration_changed(self, duration):
        """视频总时长变化"""
        self._video_duration = duration

    def _on_video_position_changed(self, position):
        """视频播放位置变化 - 更新倒计时"""
        if hasattr(self, '_video_duration') and self._video_duration > 0:
            remaining_ms = self._video_duration - position
            remaining_sec = max(0, remaining_ms // 1000)
            self.countdown_label.setText(f"{remaining_sec}s")
            self.countdown_label.show()
            self._position_countdown_label()
        else:
            self.countdown_label.hide()

    def _start_countdown(self, duration_ms):
        """启动倒计时（用于图片/文字）"""
        self._countdown_remaining = duration_ms // 1000
        self.countdown_label.setText(f"{self._countdown_remaining}s")
        self.countdown_label.show()
        self.countdown_label.raise_()
        self._position_countdown_label()
        self._countdown_timer.start(1000)

    def _update_countdown(self):
        """更新倒计时"""
        self._countdown_remaining -= 1
        if self._countdown_remaining >= 0:
            self.countdown_label.setText(f"{self._countdown_remaining}s")
            self.countdown_label.raise_()
            self._position_countdown_label()
        else:
            self._countdown_timer.stop()
            self.countdown_label.hide()

    def _stop_countdown(self):
        """停止倒计时"""
        self._countdown_timer.stop()
        self.countdown_label.hide()

    def _position_countdown_label(self):
        """定位倒计时标签到右下角"""
        if not self.countdown_label.text():
            return
        
        label_w = max(80, self.countdown_label.sizeHint().width())
        label_h = max(40, self.countdown_label.sizeHint().height())
        x = self.width() - label_w - 15
        y = self.height() - label_h - 15
        
        self.countdown_label.setGeometry(x, y, label_w, label_h)
        self.countdown_label.raise_()

    def _update_label_positions(self):
        """更新所有标签位置"""
        if self.resource_id_label.isVisible():
            self._position_resource_id_label()
        if self.countdown_label.isVisible():
            self._position_countdown_label()
    
    def _position_resource_id_label(self):
        """定位资源ID标签到左上角"""
        label_w = self.resource_id_label.sizeHint().width()
        label_h = self.resource_id_label.sizeHint().height()
        
        # 左上角，留10px边距
        x = 10
        y = 10
        
        self.resource_id_label.setGeometry(x, y, label_w, label_h)
        self.resource_id_label.raise_()
        print(f"[MediaFrame] 资源ID标签位置: ({x}, {y}, {label_w}, {label_h})")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.stack.currentWidget() is self.content_label:
            pm = self.content_label.pixmap()
            if pm and not pm.isNull():
                self._apply_pixmap(pm)
        
        self._update_label_positions()
