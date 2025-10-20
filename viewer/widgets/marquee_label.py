#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跑马灯组件
用于顶部文字滚动显示
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QFontMetrics


class MarqueeLabel(QWidget):
    """跑马灯标签 - 支持文字列表循环滚动"""
    
    def __init__(self, text="", parent=None, speed_px_per_step=3, interval_ms=30, gap_px=60):
        super().__init__(parent)
        self._text = text
        self._offset = 0.0
        self._gap = gap_px
        self._speed = max(1, speed_px_per_step)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(max(16, interval_ms))
        self._text_color = QColor(255, 255, 255)
        self._font = self.font()
        self._text_list = []
        self._current_text_idx = 0
        self._loop_count = 0
        self._loops_per_text = 2

    def setFont(self, font):
        self._font = font
        super().setFont(font)
        self.updateGeometry()
        self.update()

    def set_text(self, text: str):
        self._text = text or ""
        self._offset = 0
        self.update()

    def set_text_list(self, text_list: list, loops_per_text: int = 2):
        """设置文字列表，每个文字滚动指定次数后切换"""
        self._text_list = text_list or []
        self._loops_per_text = max(1, loops_per_text)
        self._current_text_idx = 0
        self._loop_count = 0
        if self._text_list:
            self._text = self._text_list[0]
            self._offset = 0
            self.update()

    def _check_text_switch(self):
        if not self._text_list or len(self._text_list) <= 1:
            return
        self._loop_count += 1
        if self._loop_count >= self._loops_per_text:
            self._loop_count = 0
            self._current_text_idx = (self._current_text_idx + 1) % len(self._text_list)
            self._text = self._text_list[self._current_text_idx]
            self._offset = 0

    def _on_tick(self):
        if not self._text:
            return
        fm = QFontMetrics(self._font)
        w = fm.horizontalAdvance(self._text)
        total = w + self._gap
        if total > 0:
            old = self._offset
            self._offset = (self._offset + self._speed) % total
            if old > self._offset:
                self._check_text_switch()
            self.update()

    def sizeHint(self):
        h = QFontMetrics(self._font).height() + 20
        return QSize(100, h)

    def minimumSizeHint(self):
        h = QFontMetrics(self._font).height() + 20
        return QSize(100, h)

    def paintEvent(self, _):
        if not self._text:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing)
        rect = self.rect()
        content = rect.adjusted(0, 5, 0, -5)
        p.setPen(self._text_color)
        p.setFont(self._font)
        fm = QFontMetrics(self._font)
        text_w = fm.horizontalAdvance(self._text)
        text_h = fm.ascent()
        if text_w <= 0 or content.width() <= 0:
            p.end()
            return
        start_x = content.x() - int(self._offset)
        y = content.y() + (content.height() + text_h - fm.descent()) // 2
        loop_w = text_w + self._gap
        x = start_x
        while x < content.x() + content.width():
            p.drawText(QPoint(x, y), self._text)
            x += loop_w
        p.end()
