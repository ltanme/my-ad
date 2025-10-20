# Schedule Service - 播放列表计划任务生成服务

独立的 Flask 服务，负责自动生成每日播放列表计划。

## 功能特性

- 自动挂载 NAS NFS 目录
- 从挂载目录递归收集图片和视频资源
- 随机选择媒体文件生成播放列表
- 通过 API 与 admin 服务交互
- 支持多区域播放列表生成
- 模块化设计，每个模块职责单一

## 模块说明

### 1. app.py
主应用入口，提供 Flask API 接口：
- `/health` - 健康检查
- `/api/schedule/generate` - 生成播放列表计划
- `/api/schedule/mount` - 手动挂载 NAS
- `/api/schedule/unmount` - 手动卸载 NAS
- `/api/schedule/status` - 获取挂载状态

### 2. config_loader.py
配置加载模块，负责读取 `config/config.yaml` 文件。

### 3. mount_manager.py
NAS 挂载管理模块，负责：
- 挂载 NFS 目录到本地
- 卸载已挂载的目录
- 检查挂载状态

### 4. media_collector.py
媒体资源收集模块，负责：
- 递归扫描目录收集图片和视频
- 随机选择指定数量的媒体文件

### 5. api_client.py
Admin API 客户端模块，负责：
- 登录 admin 服务
- 创建播放列表
- 添加资源到播放列表
- 激活播放列表

### 6. scheduler.py
播放列表调度器，协调各模块完成：
- 挂载 NAS 目录
- 收集媒体资源
- 为每个区域生成图片和视频播放列表
- 激活播放列表

## 安装依赖

```bash
cd schedule
pip install -r requirements.txt
```

## 配置 sudo 权限（必需）

Schedule 服务需要挂载 NFS 目录，需要 sudo 权限。

### 自动配置（推荐）

```bash
cd schedule
chmod +x setup_sudo.sh
./setup_sudo.sh
```

### 手动配置

```bash
# 编辑 sudoers
sudo visudo -f /etc/sudoers.d/schedule-mount

# 添加以下内容（替换 show 为实际用户名）
show ALL=(ALL) NOPASSWD: /bin/mount, /usr/bin/mount, /bin/umount, /usr/bin/umount

# 保存并退出，然后设置权限
sudo chmod 0440 /etc/sudoers.d/schedule-mount
```

### 验证配置

```bash
# 测试 sudo 权限（不需要输入密码）
sudo -n mount --version

# 如果成功，说明配置正确
```

## 配置说明

在 `config/config.yaml` 中配置：

```yaml
schedule:
    api_host: http://127.0.0.1:3400  # admin 服务地址
    username: admin                   # admin 用户名
    password: adm                     # admin 密码
    nas_host: 192.168.100.193        # NAS IP 地址
    mount_path:                       # NAS 远程路径列表
       - /volume2/photo
       - /volume2/newPhoto
    local_mount_base: /tmp/nas_mounts  # 本地挂载基础目录
    image_count: 10                    # 每个播放列表的图片数量
    video_count: 10                    # 每个播放列表的视频数量
    image_playlists_per_zone: 2        # 每个区域生成的图片播放列表数量
    video_playlists_per_zone: 1        # 每个区域生成的视频播放列表数量
    target_zones:                      # 目标区域列表
       - left_16x9
       - right_9x16
    image_extensions: ['jpg', 'jpeg', 'png', 'gif']
    video_extensions: ['mp4', 'avi', 'mov', 'mkv']
```

## 运行服务

```bash
cd schedule
python app.py
```

服务将在 `http://0.0.0.0:3700` 启动。

### 启动时自动挂载

服务启动时会自动执行以下操作：

1. 检查所有配置的 NAS 目录挂载状态
2. 打印每个目录的挂载状态（已挂载/未挂载）
3. 自动尝试挂载未挂载的目录
4. 打印挂载结果日志

**启动日志示例：**

```
============================================================
启动 Schedule 服务...
============================================================
检查 NAS 挂载状态...
配置的挂载目录数量: 2
✗ 未挂载: /volume2/photo -> /tmp/nas_mounts/volume2_photo
✗ 未挂载: /volume2/newPhoto -> /tmp/nas_mounts/volume2_newPhoto
尝试挂载 2 个未挂载的目录...
准备挂载: 192.168.100.193:/volume2/photo -> /tmp/nas_mounts/volume2_photo
执行挂载命令: mount -t nfs -o resvport 192.168.100.193:/volume2/photo /tmp/nas_mounts/volume2_photo
✓ 挂载成功: /volume2/photo -> /tmp/nas_mounts/volume2_photo
准备挂载: 192.168.100.193:/volume2/newPhoto -> /tmp/nas_mounts/volume2_newPhoto
执行挂载命令: mount -t nfs -o resvport 192.168.100.193:/volume2/newPhoto /tmp/nas_mounts/volume2_newPhoto
✓ 挂载成功: /volume2/newPhoto -> /tmp/nas_mounts/volume2_newPhoto
============================================================
Schedule 服务启动完成
服务地址: http://0.0.0.0:3700
============================================================
```

## API 使用示例

### 快速测试（推荐）

使用提供的测试脚本：

```bash
cd schedule
chmod +x test_generate.sh
./test_generate.sh
```

### 手动调用 API

#### 1. 健康检查

```bash
curl http://localhost:3700/health
```

#### 2. 生成今天的播放列表计划（常用）

```bash
curl -X POST http://localhost:3700/api/schedule/generate \
  -H "Content-Type: application/json"
```

**响应示例：**
```json
{
  "success": true,
  "result": {
    "date": "2025-10-19",
    "mount_results": [...],
    "playlists": [
      {
        "type": "image",
        "zone_code": "left_16x9",
        "playlist_id": 10,
        "name": "2025-10-19_图片_left_16x9_1",
        "item_count": 10,
        "activated": true
      }
    ],
    "errors": []
  }
}
```

#### 3. 生成指定日期的播放列表计划

```bash
curl -X POST http://localhost:3700/api/schedule/generate \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-10-20",
    "force": true
  }'
```

#### 4. 查看挂载状态

```bash
curl http://localhost:3700/api/schedule/status
```

**响应示例：**
```json
{
  "success": true,
  "mounts": [
    {
      "remote_path": "/volume2/photo",
      "local_path": "/tmp/nas_mounts/volume2_photo",
      "is_mounted": true
    }
  ]
}
```

#### 5. 手动挂载 NAS

```bash
curl -X POST http://localhost:3700/api/schedule/mount
```

#### 6. 手动卸载 NAS

```bash
curl -X POST http://localhost:3700/api/schedule/unmount
```

## 工作流程

1. **挂载 NAS 目录**
   - 根据配置挂载所有 NFS 目录到本地
   - 如果挂载失败，记录错误并跳过

2. **收集媒体资源**
   - 递归扫描所有挂载目录
   - 收集所有图片和视频文件路径

3. **生成播放列表**
   - 为每个目标区域（left_16x9, right_9x16）生成播放列表
   - 每个区域生成指定数量的图片和视频播放列表
   - 随机选择媒体文件添加到播放列表

4. **激活播放列表**
   - 自动激活新创建的播放列表
   - 触发 viewer 自动重载（5秒内生效）

## 注意事项

1. **NFS 挂载权限**
   - macOS 需要 sudo 权限执行 mount 命令
   - 建议配置 sudoers 允许无密码挂载

2. **挂载目录**
   - 默认挂载到 `/tmp/nas_mounts` 目录
   - 可在配置文件中修改

3. **文件路径**
   - 使用挂载后的本地路径上传文件到 admin 服务
   - 不直接操作 NAS 路径

4. **错误处理**
   - 挂载失败不会中断整个流程
   - 会记录错误并继续处理其他目录

5. **随机选择**
   - 每次生成都会随机选择不同的媒体文件
   - 确保播放内容的多样性

## 系统要求

- Python 3.7+
- macOS 或 Linux 系统
- NFS 客户端支持
- 网络访问 NAS 服务器

### 安装挂载工具

#### SMB/CIFS 挂载（推荐）

```bash
# Debian/Ubuntu
su -
apt update
apt install -y cifs-utils
exit

# 验证安装
mount.cifs --version
```

#### NFS 挂载（可选）

```bash
# Debian/Ubuntu
su -
apt update
apt install -y nfs-common
exit

# 验证安装
showmount --version
```

#### CentOS/RHEL

```bash
# SMB
sudo yum install -y cifs-utils

# NFS
sudo yum install -y nfs-utils
```

#### macOS

macOS 默认已安装 NFS 和 SMB 客户端，无需额外安装。

## 故障排查

### 挂载失败

#### 错误 1: `must be superuser to use mount`

**原因**: 没有配置 sudo 权限

**解决方法**: 运行 sudo 配置脚本

```bash
cd schedule
chmod +x setup_sudo.sh
./setup_sudo.sh
```

**验证配置**:
```bash
# 测试 sudo 权限（不需要输入密码）
sudo -n mount --version
```

#### 错误 2: `bad option; you might need a /sbin/mount.<type> helper program`

**原因**: 系统缺少 NFS 客户端工具

**解决方法**: 安装 nfs-common

```bash
# Debian/Ubuntu
su -
apt update
apt install -y nfs-common
exit

# CentOS/RHEL
sudo yum install -y nfs-utils
```

**验证安装**:
```bash
showmount --version
```

#### 错误 3: NFS 服务器不可访问

**检查方法**:

```bash
# 检查网络连接
ping 192.168.100.193

# 检查 NFS 服务是否可访问
showmount -e 192.168.100.193

# 检查 NFS 端口
telnet 192.168.100.193 2049

# 手动测试挂载
sudo mount -t nfs -o resvport 192.168.100.193:/volume2/photo /tmp/test_mount
```

### API 调用失败

- 检查 admin 服务是否运行在 3400 端口
- 检查用户名和密码是否正确
- 查看日志输出

### 找不到媒体文件

- 检查挂载目录是否成功
- 检查文件扩展名配置是否正确
- 检查目录权限
