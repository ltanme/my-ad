# 媒体显示系统安装指南

## 系统要求

- Python 3.7+
- Debian 12 / Ubuntu / macOS
- SMB/CIFS 客户端（用于 NAS 挂载）

## 快速开始

### 1. 初始化数据库

```bash
# 在项目根目录执行
python init_db.py
```

这会在 `config/media_display.db` 创建数据库并初始化表结构。

### 2. 安装系统依赖（Debian/Ubuntu）

```bash
# 安装 SMB/CIFS 客户端
sudo apt update
sudo apt install -y cifs-utils

# 配置 sudo 权限（用于挂载 NAS）
cd schedule
chmod +x setup_sudo.sh
./setup_sudo.sh
```

### 3. 安装 Python 依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r admin/requirements.txt
pip install -r schedule/requirements.txt
pip install -r viewer/requirements.txt
```

### 4. 配置系统

编辑 `config/config.yaml`，配置：
- 数据库路径
- NAS 连接信息
- 日志目录
- 其他参数

### 5. 启动服务

#### 方式一：手动启动（开发环境）

```bash
# 终端 1: 启动 Admin 服务
python admin/app.py

# 终端 2: 启动 Schedule 服务
python schedule/app.py

# 终端 3: 启动 Viewer 服务
python viewer/main.py
```

#### 方式二：自动启动（生产环境）

```bash
# 安装自动启动脚本
cd autostart
chmod +x install.sh
./install.sh

# 重启系统验证
sudo reboot
```

## 服务说明

### Admin 服务 (端口 3400)

管理后台，提供 Web 界面和 API 接口。

- Web 界面: http://localhost:3400
- 默认账号: admin / adm
- 日志文件: /tmp/admin/admin.log

### Schedule 服务 (端口 3700)

播放列表计划生成服务，自动挂载 NAS 并生成播放列表。

- API 地址: http://localhost:3700
- 日志文件: /tmp/schedule/schedule.log

### Viewer 服务

媒体显示界面，从数据库读取播放列表并显示。

- 日志文件: /tmp/viewer/viewer.log

## 验证安装

### 1. 检查数据库

```bash
sqlite3 config/media_display.db "SELECT * FROM zone;"
```

应该显示 9 个区域。

### 2. 检查 Admin 服务

```bash
curl http://localhost:3400/login
```

应该返回登录页面。

### 3. 检查 Schedule 服务

```bash
curl http://localhost:3700/health
```

应该返回：
```json
{
  "status": "ok",
  "service": "schedule",
  "version": "1.0.0"
}
```

### 4. 生成测试播放列表

```bash
curl -X POST http://localhost:3700/api/schedule/generate \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 故障排查

### 数据库初始化失败

```bash
# 删除旧数据库重新初始化
rm config/media_display.db
python init_db.py
```

### NAS 挂载失败

```bash
# 检查依赖
cd schedule
chmod +x check_dependencies.sh
./check_dependencies.sh

# 手动测试挂载
sudo mount -t cifs //192.168.100.193/photo /tmp/test -o username=ad,password=8uyJf73
```

### 查看日志

```bash
# 实时查看所有日志
tail -f /tmp/admin/admin.log /tmp/schedule/schedule.log /tmp/viewer/viewer.log
```

## 目录结构

```
my-ad/
├── init_db.py              # 数据库初始化脚本
├── config/
│   ├── config.yaml         # 主配置文件
│   └── media_display.db    # SQLite 数据库
├── admin/                  # 管理后台服务
│   ├── app.py
│   └── templates/
├── schedule/               # 播放列表计划服务
│   ├── app.py
│   ├── scheduler.py
│   └── mount_manager.py
├── viewer/                 # 媒体显示服务
│   ├── main.py
│   ├── db_manager.py
│   └── widgets/
└── autostart/              # 自动启动脚本
    ├── install.sh
    └── *.desktop
```

## 下一步

1. 访问 Admin 界面创建播放列表
2. 使用 Schedule 服务生成每日播放列表
3. 启动 Viewer 查看播放效果

详细文档请参考各模块的 README.md 文件。
