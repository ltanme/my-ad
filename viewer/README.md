# 多区域媒体显示系统

## 快速开始

### 1. 安装依赖

```bash
pip install -r ../requirements.txt
```

### 2. 初始化数据库（首次运行）

```bash
python init_db.py
```

### 3. 运行程序

```bash
python main.py
```

## 配置文件

配置文件位于: `../config/config.yaml`

可配置项包括：
- 数据库路径
- 窗口标题和启动模式
- 各区域的显示参数
- 跑马灯速度和字体
- 倒计时样式
- 日志级别

## 数据库

数据库文件位于: `../config/media_display.db`

使用绝对路径连接，确保在任何目录下运行都能正确访问。

## 快捷键

- **Q / Esc** - 退出程序
- **F11** - 切换全屏/窗口模式
- **R** - 重新加载数据库内容

## 项目结构

```
viewer/
├── main.py                    # 主入口（使用配置文件）
├── qt_layout_viewer.py        # 原始单文件版本
├── config_manager.py          # 配置管理器
├── db_manager.py              # 数据库管理器
├── widgets/                   # 显示组件
│   ├── marquee_label.py       # 跑马灯
│   ├── media_frame.py         # 媒体框架
│   └── middle_stage.py        # 舞台布局
└── README.md

../config/
├── config.yaml                # 主配置文件
└── media_display.db           # 数据库文件
```
