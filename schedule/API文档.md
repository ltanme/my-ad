# Schedule 服务 API 文档

## 基础信息

- **Base URL**: `http://localhost:3700`
- **认证方式**: 无需认证
- **Content-Type**: `application/json`

---

## API 接口列表

### 1. 健康检查

**接口**: `GET /health`

**描述**: 检查服务是否正常运行

**请求示例**
```bash
curl http://localhost:3700/health
```

**响应示例**
```json
{
  "status": "ok",
  "service": "schedule",
  "version": "1.0.0"
}
```

---

### 2. 生成播放列表计划

**接口**: `POST /api/schedule/generate`

**描述**: 生成每日播放列表计划（核心功能）

**请求示例**
```bash
# 生成今天的播放列表
curl -X POST http://localhost:3700/api/schedule/generate \
  -H "Content-Type: application/json"

# 生成指定日期的播放列表
curl -X POST http://localhost:3700/api/schedule/generate \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-10-20",
    "force": true
  }'
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | 否 | 目标日期 (YYYY-MM-DD)，默认为今天 |
| force | boolean | 否 | 是否强制重新生成，默认 false |

**响应示例**
```json
{
  "success": true,
  "result": {
    "date": "2025-10-19",
    "mount_results": [
      {
        "remote_path": "/volume2/photo",
        "local_path": "/tmp/nas_mounts/volume2_photo",
        "success": true,
        "already_mounted": true
      }
    ],
    "playlists": [
      {
        "type": "image",
        "zone_code": "left_16x9",
        "playlist_id": 10,
        "name": "2025-10-19_图片_left_16x9_1",
        "item_count": 10,
        "activated": true
      },
      {
        "type": "video",
        "zone_code": "left_16x9",
        "playlist_id": 11,
        "name": "2025-10-19_视频_left_16x9_1",
        "item_count": 10,
        "activated": true
      }
    ],
    "errors": []
  }
}
```

---

### 3. 查看挂载状态

**接口**: `GET /api/schedule/status`

**描述**: 查看所有 NAS 目录的挂载状态

**请求示例**
```bash
curl http://localhost:3700/api/schedule/status
```

**响应示例**
```json
{
  "success": true,
  "mounts": [
    {
      "remote_path": "/volume2/photo",
      "local_path": "/tmp/nas_mounts/volume2_photo",
      "is_mounted": true
    },
    {
      "remote_path": "/volume2/newPhoto",
      "local_path": "/tmp/nas_mounts/volume2_newPhoto",
      "is_mounted": false
    }
  ]
}
```

---

### 4. 手动挂载 NAS

**接口**: `POST /api/schedule/mount`

**描述**: 手动挂载所有配置的 NAS 目录

**请求示例**
```bash
curl -X POST http://localhost:3700/api/schedule/mount
```

**响应示例**
```json
{
  "success": true,
  "result": [
    {
      "remote_path": "/volume2/photo",
      "local_path": "/tmp/nas_mounts/volume2_photo",
      "success": true,
      "already_mounted": false
    }
  ]
}
```

---

### 5. 手动卸载 NAS

**接口**: `POST /api/schedule/unmount`

**描述**: 手动卸载所有已挂载的 NAS 目录

**请求示例**
```bash
curl -X POST http://localhost:3700/api/schedule/unmount
```

**响应示例**
```json
{
  "success": true,
  "result": [
    {
      "remote_path": "/volume2/photo",
      "local_path": "/tmp/nas_mounts/volume2_photo",
      "success": true
    }
  ]
}
```

---

## 使用流程

### 典型使用场景

1. **启动服务后首次使用**
```bash
# 1. 检查服务状态
curl http://localhost:3700/health

# 2. 查看挂载状态
curl http://localhost:3700/api/schedule/status

# 3. 如果未挂载，手动挂载
curl -X POST http://localhost:3700/api/schedule/mount

# 4. 生成今日播放列表
curl -X POST http://localhost:3700/api/schedule/generate \
  -H "Content-Type: application/json"
```

2. **每日定时任务**
```bash
# 使用 cron 每天早上 8 点生成播放列表
0 8 * * * curl -X POST http://localhost:3700/api/schedule/generate -H "Content-Type: application/json"
```

---

## 错误处理

### 错误响应格式
```json
{
  "success": false,
  "error": "错误信息描述"
}
```

### 常见错误

**挂载失败**
```json
{
  "success": true,
  "result": {
    "mount_results": [
      {
        "remote_path": "/volume2/photo",
        "success": false,
        "error": "mount: Operation not permitted"
      }
    ]
  }
}
```

**没有找到媒体文件**
```json
{
  "success": true,
  "result": {
    "errors": [
      "创建图片播放列表失败 (left_16x9, #1): 没有找到图片文件"
    ]
  }
}
```

---

## 配置说明

在 `config/config.yaml` 中配置 schedule 服务：

```yaml
schedule:
    api_host: http://127.0.0.1:3400      # admin 服务地址
    username: admin                       # admin 用户名
    password: adm                         # admin 密码
    nas_host: 192.168.100.193            # NAS IP 地址
    mount_path:                           # NAS 远程路径
       - /volume2/photo
       - /volume2/newPhoto
    local_mount_base: /tmp/nas_mounts    # 本地挂载目录
    image_count: 10                       # 每个播放列表的图片数
    video_count: 10                       # 每个播放列表的视频数
    image_playlists_per_zone: 2          # 每区域图片列表数
    video_playlists_per_zone: 1          # 每区域视频列表数
    target_zones:                         # 目标区域
       - left_16x9
       - right_9x16
```

---

# Admin 服务 API 文档（供 Schedule 调用）

## 基础信息

- **Base URL**: `http://localhost:3400`
- **认证方式**: Session Cookie（需要先登录）
- **Content-Type**: `application/json` (除文件上传外)

## 认证流程

### 1. 登录获取 Session

所有 API 调用前必须先登录获取 session cookie。

**请求**
```bash
curl -X POST http://localhost:3400/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  -c cookies.txt \
  -L
```

**参数说明**
- `-c cookies.txt`: 保存 cookie 到文件
- `-L`: 跟随重定向
- `username`: 管理员用户名（在 config.yaml 中配置）
- `password`: 管理员密码（在 config.yaml 中配置）

**成功响应**
- 返回 302 重定向到主页
- Cookie 保存在 cookies.txt 文件中

**后续请求**
所有后续 API 请求都需要带上 `-b cookies.txt` 参数来使用保存的 cookie。

---

## API 接口列表

### 播放列表管理

#### 1. 创建播放列表

**接口**: `POST /api/playlist/create`

**描述**: 为指定区域创建新的播放列表

**请求示例**
```bash
curl -X POST http://localhost:3400/api/playlist/create \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "zone_code": "left_16x9",
    "name": "我的播放列表",
    "loop_mode": "loop"
  }'
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| zone_code | string | 是 | 区域代码，见下方区域列表 |
| name | string | 是 | 播放列表名称 |
| loop_mode | string | 否 | 循环模式：`loop`(循环) 或 `once`(单次)，默认 `loop` |

**响应示例**
```json
{
  "success": true,
  "playlist_id": 10
}
```

---

#### 2. 更新播放列表

**接口**: `POST /api/playlist/<playlist_id>/update`

**描述**: 更新播放列表信息

**请求示例**
```bash
curl -X POST http://localhost:3400/api/playlist/10/update \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "更新后的名称",
    "loop_mode": "loop",
    "is_active": 0
  }'
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 播放列表名称 |
| loop_mode | string | 是 | 循环模式：`loop` 或 `once` |
| is_active | integer | 否 | 是否激活：1=激活，0=未激活，默认 0 |

**响应示例**
```json
{
  "success": true
}
```

---

#### 3. 删除播放列表

**接口**: `POST /api/playlist/<playlist_id>/delete`

**描述**: 删除指定的播放列表及其所有播放项

**请求示例**
```bash
curl -X POST http://localhost:3400/api/playlist/10/delete \
  -b cookies.txt
```

**响应示例**
```json
{
  "success": true
}
```

---

#### 4. 激活播放列表

**接口**: `POST /api/playlist/<playlist_id>/activate`

**描述**: 激活指定的播放列表（会自动触发 viewer 重载）

**请求示例**
```bash
curl -X POST http://localhost:3400/api/playlist/10/activate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "zone_code": "left_16x9"
  }'
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| zone_code | string | 是 | 区域代码 |

**响应示例**
```json
{
  "success": true
}
```

**注意**: 激活播放列表会触发 viewer 自动重载（5秒内生效）

---

#### 5. 获取播放列表项

**接口**: `GET /api/playlist/<playlist_id>/items`

**描述**: 获取指定播放列表的所有播放项

**请求示例**
```bash
curl -X GET http://localhost:3400/api/playlist/10/items \
  -b cookies.txt
```

**响应示例**
```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "playlist_id": 10,
      "asset_id": 5,
      "text_inline": null,
      "display_ms": 5000,
      "play_order": 1,
      "kind": "image",
      "uri": "/path/to/image.jpg",
      "created_at": "2025-10-19 10:00:00"
    },
    {
      "id": 2,
      "playlist_id": 10,
      "asset_id": null,
      "text_inline": "这是文字内容",
      "display_ms": 5000,
      "play_order": 2,
      "kind": null,
      "uri": null,
      "created_at": "2025-10-19 10:01:00"
    }
  ]
}
```

---

### 播放项管理

#### 6. 添加文字播放项

**接口**: `POST /api/item/add`

**描述**: 向播放列表添加文字内容

**请求示例**
```bash
curl -X POST http://localhost:3400/api/item/add \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "playlist_id": 10,
    "type": "text",
    "text": "这是要显示的文字内容",
    "display_ms": 5000
  }'
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| playlist_id | integer | 是 | 播放列表ID |
| type | string | 是 | 类型，固定为 `text` |
| text | string | 是 | 文字内容 |
| display_ms | integer | 否 | 显示时长（毫秒），默认 5000 |

**响应示例**
```json
{
  "success": true,
  "item_id": 15
}
```

---

#### 7. 删除播放项

**接口**: `POST /api/item/<item_id>/delete`

**描述**: 删除指定的播放项

**请求示例**
```bash
curl -X POST http://localhost:3400/api/item/15/delete \
  -b cookies.txt
```

**响应示例**
```json
{
  "success": true
}
```

---

### 文件上传

#### 8. 上传图片/视频

**接口**: `POST /api/upload`

**描述**: 上传图片或视频文件并添加到播放列表

**请求示例**
```bash
curl -X POST http://localhost:3400/api/upload \
  -b cookies.txt \
  -F "file=@/path/to/your/image.jpg" \
  -F "playlist_id=10" \
  -F "display_ms=5000"
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 文件对象 |
| playlist_id | integer | 否 | 播放列表ID，如果提供则自动添加到列表 |
| display_ms | integer | 否 | 显示时长（毫秒），仅对图片有效，默认 5000 |

**支持的文件格式**
- 图片: png, jpg, jpeg, gif, heic, heif
- 视频: mp4, avi, mov, mkv

**HEIC 格式说明**
- HEIC/HEIF 文件上传后会自动转换为 JPG 格式
- 转换后原始 HEIC 文件会被删除
- 需要安装 `pillow-heif` 库支持

**文件大小限制**: 500MB（在 config.yaml 中配置）

**响应示例**
```json
{
  "success": true,
  "asset_id": 20,
  "filename": "image.jpg"
}
```

---

#### 9. 通过路径添加资源（Schedule 服务专用）

**接口**: `POST /api/asset/add_by_path`

**描述**: 直接使用文件路径添加资源到数据库，不上传文件。用于 schedule 服务添加挂载目录中的文件。

**请求示例**
```bash
curl -X POST http://localhost:3400/api/asset/add_by_path \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "file_path": "/tmp/nas_mounts/volume2_photo/image.jpg",
    "playlist_id": 10,
    "display_ms": 5000
  }'
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_path | string | 是 | 文件的完整路径（必须存在） |
| playlist_id | integer | 否 | 播放列表ID，如果提供则自动添加到列表 |
| display_ms | integer | 否 | 显示时长（毫秒），仅对图片有效，默认 5000 |

**响应示例**
```json
{
  "success": true,
  "asset_id": 20,
  "kind": "image",
  "file_path": "/tmp/nas_mounts/volume2_photo/image.jpg"
}
```

**错误响应**
```json
{
  "success": false,
  "error": "文件不存在: /path/to/file.jpg"
}
```

---

## 区域代码列表

| 区域代码 | 区域名称 |
|----------|----------|
| top_marquee | 顶部跑马灯 |
| left_16x9 | 中部左侧 16:9 容器 |
| right_9x16 | 中部右侧 9:16 容器 |
| extra_top | 顶行最右侧竖条 上格 |
| extra_bottom | 顶行最右侧竖条 下格 |
| bottom_cell_1 | 顶行下三格：左 |
| bottom_cell_2 | 顶行下三格：中 |
| bottom_cell_3 | 顶行下三格：右 |
| bottom_strip | 底部状态条（仅文字） |

---

## 完整使用示例

### 场景：创建并激活一个新的播放列表

```bash
# 1. 登录
curl -X POST http://localhost:3400/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  -c cookies.txt \
  -L

# 2. 创建播放列表
curl -X POST http://localhost:3400/api/playlist/create \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "zone_code": "left_16x9",
    "name": "新播放列表",
    "loop_mode": "loop"
  }'
# 假设返回 playlist_id: 10

# 3. 添加文字内容
curl -X POST http://localhost:3400/api/item/add \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "playlist_id": 10,
    "type": "text",
    "text": "欢迎使用",
    "display_ms": 5000
  }'

# 4. 上传图片
curl -X POST http://localhost:3400/api/upload \
  -b cookies.txt \
  -F "file=@/path/to/image.jpg" \
  -F "playlist_id=10" \
  -F "display_ms=5000"

# 5. 上传视频
curl -X POST http://localhost:3400/api/upload \
  -b cookies.txt \
  -F "file=@/path/to/video.mp4" \
  -F "playlist_id=10"

# 6. 激活播放列表（触发 viewer 自动刷新）
curl -X POST http://localhost:3400/api/playlist/10/activate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "zone_code": "left_16x9"
  }'
```

---

## 错误处理

### 错误响应格式
```json
{
  "success": false,
  "error": "错误信息描述"
}
```

### 常见错误

**未登录 (401)**
```bash
# 响应: 302 重定向到登录页
# 解决: 先调用登录接口获取 cookie
```

**参数错误 (400)**
```json
{
  "success": false,
  "error": "缺少必填参数"
}
```

**资源不存在 (404)**
```json
{
  "success": false,
  "error": "播放列表不存在"
}
```

**文件类型不允许**
```json
{
  "success": false,
  "error": "文件类型不允许"
}
```

---

## 注意事项

1. **Session 有效期**: Session 在浏览器关闭或服务器重启后失效，需要重新登录
2. **并发限制**: 建议不要并发调用修改类接口，可能导致数据不一致
3. **文件路径**: 上传的文件保存在 `config.yaml` 中配置的 `upload_folder` 目录
4. **自动重载**: 只有激活播放列表时才会触发 viewer 自动重载（5秒内生效）
5. **数据库**: 所有数据存储在 `config/media_display.db` SQLite 数据库中

---

## Python 示例代码

```python
import requests

# 基础配置
BASE_URL = "http://localhost:3400"
session = requests.Session()

# 1. 登录
login_data = {
    "username": "admin",
    "password": "admin123"
}
response = session.post(f"{BASE_URL}/login", data=login_data)
print("登录成功" if response.ok else "登录失败")

# 2. 创建播放列表
playlist_data = {
    "zone_code": "left_16x9",
    "name": "Python创建的列表",
    "loop_mode": "loop"
}
response = session.post(f"{BASE_URL}/api/playlist/create", json=playlist_data)
result = response.json()
playlist_id = result.get('playlist_id')
print(f"创建播放列表: {playlist_id}")

# 3. 添加文字
text_data = {
    "playlist_id": playlist_id,
    "type": "text",
    "text": "Python添加的文字",
    "display_ms": 5000
}
response = session.post(f"{BASE_URL}/api/item/add", json=text_data)
print(f"添加文字: {response.json()}")

# 4. 上传文件
files = {'file': open('/path/to/image.jpg', 'rb')}
data = {'playlist_id': playlist_id, 'display_ms': 5000}
response = session.post(f"{BASE_URL}/api/upload", files=files, data=data)
print(f"上传文件: {response.json()}")

# 5. 激活播放列表
activate_data = {"zone_code": "left_16x9"}
response = session.post(f"{BASE_URL}/api/playlist/{playlist_id}/activate", json=activate_data)
print(f"激活播放列表: {response.json()}")
```

---

## 技术支持

如有问题，请查看：
- 服务器日志：查看控制台输出
- 数据库：使用 SQLite 工具查看 `config/media_display.db`
- 配置文件：`config/config.yaml`
