#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重载观察者
监听数据库 reload_signal 表，当有更新信号时触发回调
"""
import sqlite3
from PyQt5.QtCore import QTimer, QObject, pyqtSignal


class ReloadObserver(QObject):
    """重载观察者类"""
    
    # 信号：当需要重载时发出
    reload_requested = pyqtSignal()
    
    def __init__(self, db_path, interval_ms=5000):
        """
        初始化观察者
        
        Args:
            db_path: 数据库路径
            interval_ms: 检查间隔（毫秒），默认5000ms（5秒）
        """
        super().__init__()
        self.db_path = db_path
        self.interval_ms = interval_ms
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_reload_signal)
        self.last_check_time = None
        
    def start(self):
        """开始监听"""
        print(f"[ReloadObserver] 开始监听数据库变化，间隔: {self.interval_ms}ms")
        self.timer.start(self.interval_ms)
    
    def stop(self):
        """停止监听"""
        print(f"[ReloadObserver] 停止监听")
        self.timer.stop()
    
    def _check_reload_signal(self):
        """检查重载信号"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查询 reload_signal 表
            cursor.execute("SELECT need_reload, updated_at FROM reload_signal WHERE id = 1")
            row = cursor.fetchone()
            
            if row:
                need_reload, updated_at = row
                
                # 如果需要重载
                if need_reload == 1:
                    print(f"[ReloadObserver] 检测到重载信号，更新时间: {updated_at}")
                    
                    # 清除重载标志
                    cursor.execute("UPDATE reload_signal SET need_reload = 0 WHERE id = 1")
                    conn.commit()
                    
                    # 发出重载信号
                    self.reload_requested.emit()
                    print(f"[ReloadObserver] 已发出重载请求")
            
            conn.close()
            
        except Exception as e:
            print(f"[ReloadObserver] 检查重载信号失败: {e}")
    
    def trigger_reload(self):
        """手动触发重载（用于测试）"""
        try:
            from datetime import datetime, timezone, timedelta
            beijing_tz = timezone(timedelta(hours=8))
            beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reload_signal 
                SET need_reload = 1, updated_at = ? 
                WHERE id = 1
            """, (beijing_time,))
            conn.commit()
            conn.close()
            print(f"[ReloadObserver] 已设置重载信号 (北京时间: {beijing_time})")
        except Exception as e:
            print(f"[ReloadObserver] 设置重载信号失败: {e}")


def set_reload_signal(db_path):
    """
    设置重载信号（供外部调用，如管理后台）
    
    Args:
        db_path: 数据库路径
    """
    try:
        from datetime import datetime, timezone, timedelta
        beijing_tz = timezone(timedelta(hours=8))
        beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reload_signal 
            SET need_reload = 1, updated_at = ? 
            WHERE id = 1
        """, (beijing_time,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"设置重载信号失败: {e}")
        return False


if __name__ == '__main__':
    # 测试代码
    import sys
    from pathlib import Path
    
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DB_PATH = str(PROJECT_ROOT / "config" / "media_display.db")
    
    print("测试重载观察者")
    print(f"数据库路径: {DB_PATH}")
    
    # 设置重载信号
    if set_reload_signal(DB_PATH):
        print("✓ 重载信号已设置")
    else:
        print("✗ 设置重载信号失败")
