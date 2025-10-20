# 多区域媒体显示系统

一个功能强大的多区域媒体显示系统，支持图片、视频、文字的混合播放，适用于数字标牌、展示屏等场景。

## ✨ 特性

- 🎬 **多区域布局** - 支持 9 个独立显示区域，灵活配置
- 📺 **多媒体支持** - 图片、视频、文字混合播放
- 🔄 **自动播放列表** - 从 NAS 自动生成每日播放列表
- 🌐 **Web 管理界面** - 便捷的播放列表管理
- 📱 **实时重载** - 内容更新自动刷新显示
- 🎨 **跑马灯效果** - 顶部和底部文字滚动显示
- ⏱️ **倒计时功能** - 可配置的倒计时显示
- 📊 **日志系统** - 完整的日志记录和调试支持

## 🏗️ 系统架构

系统由三个独立服务组成：

### 1. Admin 服务 (端口 3400)
- Web 管理界面
- RESTful API
- 播放列表管理
- 媒体资源管理

### 2. Schedule 服务 (端口 3700)
- 自动挂载 NAS（支持 SMB/NFS）
- 自动生成播放列表
- 定时任务调度
- 媒体资源收集

### 3. Viewer 服务
- PyQt5 图形界面
- 多区域媒体播放
- 实时内容重载
- 硬件加速支持

## 📦 安装

### 系统要求

- Python 3.7+
- Debian 12 / Ubuntu / macOS
- SMB/CIFS 客户端（用于 NAS 挂载）

### 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/ltanme/my-ad.git
cd my-ad

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置系统
cp config/config.yaml.example config/config.yaml
# 编辑 config.yaml 填入你的配置

# 5. 初始化数据库
python init_db.py

# 6. 启动服务
python admin/app.py      # 终端 1
python schedule/app.py   # 终端 2
python viewer/main.py    # 终端 3
```

详细安装说明请参考 [INSTALL.md](INSTALL.md)

## 🚀 使用

### 访问 Web 管理界面

```
http://localhost:3400
默认账号: admin
默认密码: (在 config.yaml 中配置)
```

### 生成播放列表

```bash
curl -X POST http://localhost:3700/api/schedule/generate \
  -H "Content-Type: application/json"
```

### 查看日志

```bash
tail -f /tmp/admin/admin.log
tail -f /tmp/schedule/schedule.log
tail -f /tmp/viewer/viewer.log
```

## 📖 文档

- [安装指南](INSTALL.md)
- [Admin API 文档](admin/API文档.md)
- [Schedule API 文档](schedule/API文档.md)
- [自动启动配置](autostart/README.md)

## 🎯 区域布局

系统支持以下 9 个显示区域：

1. **top_marquee** - 顶部跑马灯
2. **left_16x9** - 中部左侧 16:9 容器
3. **right_9x16** - 中部右侧 9:16 容器
4. **extra_top** - 顶行最右侧竖条 上格
5. **extra_bottom** - 顶行最右侧竖条 下格
6. **bottom_cell_1** - 顶行下三格：左
7. **bottom_cell_2** - 顶行下三格：中
8. **bottom_cell_3** - 顶行下三格：右
9. **bottom_strip** - 底部状态条（仅文字）

## 🔧 配置

主要配置文件：`config/config.yaml`

```yaml
# 数据库配置
database:
  filename: config/media_display.db

# NAS 配置
schedule:
  nas_host: 192.168.100.xxx
  mount_type: smb
  smb_username: your_username
  smb_password: your_password

# 管理员配置
admin:
  username: admin
  password: your_password
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👤 作者

ltanme

## 🙏 致谢

感谢所有贡献者和使用者！

---

如有问题，请提交 [Issue](https://github.com/ltanme/my-ad/issues)
