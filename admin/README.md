# 媒体显示系统管理后台

## 独立部署说明

管理后台是独立模块，只依赖 `config` 目录，不需要 `viewer` 模块。

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置系统
编辑 `../config/config.yaml`，配置以下内容：

```yaml
# 数据库配置
database:
  filename: /path/to/media_display.db

# 管理后台配置
admin:
  username: admin
  password: your_password
  upload_folder: /path/to/uploads
  allowed_extensions: ['png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'mkv']
  max_file_size: 500  # MB
```

### 3. 启动管理后台
```bash
python app.py
```

或使用启动脚本：
```bash
bash run.sh
```

### 4. 访问管理界面
打开浏览器访问: http://localhost:5000

登录信息在 `config/config.yaml` 中配置

## 功能说明

### 区域管理
系统支持以下9个显示区域的内容管理：
- 顶部跑马灯
- 中部左侧 16:9 容器
- 中部右侧 9:16 容器
- 顶行最右侧竖条 上格
- 顶行最右侧竖条 下格
- 顶行下三格：左/中/右
- 底部状态条

### 播放列表管理
- 每个区域可以创建多个播放列表
- 每个区域同时只能有一个活跃的播放列表
- 支持循环播放和单次播放模式

### 内容管理
- 添加文字内容
- 上传图片（png, jpg, jpeg, gif）
- 上传视频（mp4, avi, mov, mkv）
- 删除播放项
- 调整播放顺序

## 配置说明

### 修改配置
所有配置都在 `../config/config.yaml` 中：

- **管理员账号**: `admin.username` 和 `admin.password`
- **安全密钥**: `admin.secret_key`（生产环境必须修改）
- **上传目录**: `admin.upload_folder`（支持绝对路径和相对路径）
- **数据库路径**: `database.filename`（支持绝对路径和相对路径）
- **文件限制**: `admin.allowed_extensions` 和 `admin.max_file_size`

相对路径会相对于 `config` 目录解析。

### 生成安全密钥

**重要：生产环境必须修改 SECRET_KEY！**

生成新密钥：
```bash
python generate_secret_key.py
```

或使用命令：
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

将生成的密钥复制到 `config/config.yaml` 的 `admin.secret_key` 配置项。

## 目录结构
```
admin/
├── app.py              # Flask 应用主文件
├── config.py           # 配置加载模块
├── db_helper.py        # 数据库操作辅助类
├── requirements.txt    # Python 依赖
├── static/             # 静态文件
│   ├── bootstrap.min.css
│   ├── bootstrap.bundle.min.js
│   └── jquery-3.7.1.min.js
└── templates/          # HTML 模板
    ├── base.html
    ├── login.html
    ├── index.html
    └── zone_manage.html

config/                 # 配置目录（必需）
├── config.yaml         # 主配置文件
└── media_display.db    # 数据库文件
```

## 注意事项

1. 上传的文件保存位置在 `config.yaml` 中配置
2. 文件大小限制在 `config.yaml` 中配置
3. 修改内容后，viewer 程序需要按 R 键重新加载
4. 生产环境请修改 `config.yaml` 中的管理员密码
5. admin 模块可以独立部署，只需要 `admin/` 和 `config/` 两个目录
