#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多区域媒体显示系统 - 主入口
支持图片、视频、文字的混合播放，带倒计时功能
"""

import sys
import platform
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 导入配置管理器
from config_manager import config

# 导入日志配置
from logger_config import init_logger, get_logger

# 初始化日志
logger = init_logger(config)

# 导入自定义组件
from widgets.marquee_label import MarqueeLabel
from widgets.middle_stage import MiddleStage

# 导入数据库管理器
try:
    from db_manager import MediaDBManager
except Exception:
    MediaDBManager = None

# 导入重载观察者
try:
    from reload_observer import ReloadObserver
except Exception:
    ReloadObserver = None


class MultiZoneViewer(QMainWindow):
    """多区域媒体显示主窗口"""
    
    def __init__(self, db_manager=None, db_path=None):
        super().__init__()
        self.db_manager = db_manager
        self.db_path = db_path
        self.reload_observer = None
        self.init_ui()
        self.setup_reload_observer()

    def init_ui(self):
        """初始化界面"""
        # 从配置读取窗口标题
        window_title = config.get('display.window_title', '多区域媒体显示器')
        self.setWindowTitle(window_title)
        
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # 顶部跑马灯 - 从配置读取参数
        marquee_config = config.get('zones.top_marquee', {})
        self.marquee = MarqueeLabel(
            "欢迎使用多区域媒体显示系统 - 这是跑马灯文字显示区域",
            speed_px_per_step=marquee_config.get('speed', 3),
            interval_ms=marquee_config.get('interval', 20),
            gap_px=marquee_config.get('gap', 80)
        )
        self.marquee.setMinimumHeight(60)
        font = QFont()
        font.setPointSize(marquee_config.get('font_size', 36))
        self.marquee.setFont(font)
        
        top = QFrame()
        top.setStyleSheet("QFrame{background:black; border:5px solid yellow;}")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.addWidget(self.marquee)
        root.addWidget(top, stretch=5)

        # 中部舞台
        self.stage = MiddleStage()
        root.addWidget(self.stage, stretch=85)

        # 底部状态条 - 从配置读取字体大小
        bottom_font_size = config.get('zones.bottom_strip.font_size', 22)
        self.bottom = QLabel("底部常显文字区域 - 系统状态信息")
        self.bottom.setAlignment(Qt.AlignCenter)
        self.bottom.setStyleSheet(
            f"QLabel{{background:black;color:white;font-size:{bottom_font_size}px;"
            "font-weight:bold;padding:10px;border:5px solid yellow;}"
        )
        self.bottom.setMinimumHeight(60)
        root.addWidget(self.bottom, stretch=10)

        # 加载内容
        self.load_content()

    def load_content(self):
        """从数据库加载内容"""
        logger.debug(f"load_content: db_manager = {self.db_manager}")
        logger.debug(f"load_content: type = {type(self.db_manager)}")
        if self.db_manager:
            logger.debug(f"load_content: hasattr 'get_playlist_items' = {hasattr(self.db_manager, 'get_playlist_items')}")
            if hasattr(self.db_manager, 'get_playlist_items'):
                logger.debug(f"load_content: get_playlist_items = {self.db_manager.get_playlist_items}")
        
        if not (self.db_manager and hasattr(self.db_manager, "get_playlist_items")):
            logger.warning("未连接数据库，使用演示模式")
            self.stage.bind_demo()
            return
        
        try:
            # 加载顶部跑马灯
            items = self.db_manager.get_playlist_items("top_marquee", limit=50)
            if items:
                texts = [it.get("text", "") for it in items if it.get("text")]
                loops = config.get('zones.top_marquee.loops_per_text', 2)
                if texts:
                    self.marquee.set_text_list(texts, loops_per_text=loops)
            
            # 加载中部舞台
            self.stage.load_from_database(self.db_manager)
            
            # 加载底部状态条
            items = self.db_manager.get_playlist_items("bottom_strip", limit=20)
            if items:
                texts = [it.get("text", "") for it in items if it.get("text")]
                if texts:
                    self.bottom.setText(" | ".join(texts))
            
            logger.info("✓ 已从数据库加载内容")
        except Exception as e:
            logger.error(f"✗ 加载数据库内容失败: {e}", exc_info=True)
            self.stage.bind_demo()
    
    def setup_reload_observer(self):
        """设置重载观察者"""
        if not ReloadObserver or not self.db_path:
            return
        
        try:
            # 创建观察者，每5秒检查一次
            self.reload_observer = ReloadObserver(self.db_path, interval_ms=5000)
            
            # 连接重载信号到 load_content 方法
            self.reload_observer.reload_requested.connect(self.on_reload_requested)
            
            # 启动观察者
            self.reload_observer.start()
            logger.info("✓ 重载观察者已启动")
        except Exception as e:
            logger.error(f"✗ 启动重载观察者失败: {e}", exc_info=True)
    
    def on_reload_requested(self):
        """当收到重载请求时的处理"""
        logger.info("=" * 60)
        logger.info("收到重载请求，正在刷新内容...")
        logger.info("=" * 60)
        self.load_content()

    def keyPressEvent(self, e):
        """键盘事件处理"""
        if e.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.close()
        elif e.key() == Qt.Key_F11:
            self.showNormal() if self.isMaximized() else self.showMaximized()
        elif e.key() == Qt.Key_R:
            logger.info("重新加载数据库内容...")
            self.load_content()


def get_system_font():
    """获取系统字体"""
    sysname = platform.system()
    if sysname == "Darwin":
        return QFont("PingFang SC", 12)
    if sysname == "Linux":
        for nm in ["WenQuanYi Zen Hei", "WenQuanYi Micro Hei", "Noto Sans CJK SC", "DejaVu Sans"]:
            font = QFont(nm, 12)
            if font.family() == nm:
                return font
        return QFont("Sans", 12)
    return QFont("Microsoft YaHei", 12)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("多区域媒体显示系统")
    logger.info("=" * 60)
    
    # 显示配置信息
    print(f"项目根目录: {config.get_project_root()}")
    print(f"配置目录: {config.get_config_dir()}")
    
    # 高 DPI 处理
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    try:
        from PyQt5.QtCore import Qt as _Qt
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            _Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setFont(get_system_font())

    # 从配置获取数据库路径（绝对路径）
    db_path = config.get_database_path()
    print(f"数据库路径: {db_path}")
    
    db_manager = None
    if MediaDBManager:
        try:
            import os
            if os.path.exists(db_path):
                db_manager = MediaDBManager(db_path)
                print(f"✓ 已连接数据库")
            else:
                print(f"⚠️  数据库文件不存在: {db_path}")
                if config.get('database.auto_create', True):
                    print("   提示: 请运行 'python viewer/init_db.py' 创建数据库")
        except Exception as e:
            print(f"✗ 打开数据库失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️  数据库管理器模块导入失败")
    
    print("=" * 60)
    
    print(f"[main] 准备创建 MultiZoneViewer")
    print(f"[main] db_manager = {db_manager}")
    print(f"[main] type = {type(db_manager)}")
    if db_manager:
        print(f"[main] hasattr 'get_playlist_items' = {hasattr(db_manager, 'get_playlist_items')}")

    # 创建并显示主窗口
    viewer = MultiZoneViewer(db_manager, db_path)
    print(f"[main] viewer.db_manager = {viewer.db_manager}")
    
    # 根据配置决定启动模式
    if config.get('display.fullscreen', False):
        viewer.showFullScreen()
    elif config.get('display.start_maximized', True):
        viewer.showMaximized()
    else:
        viewer.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
