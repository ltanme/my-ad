# 自动启动脚本说明

本目录包含用于 Debian 12 系统的自动启动脚本（.desktop 文件）。

## 脚本列表

### 1. admin_service.desktop
- **服务**: Admin 管理后台服务
- **端口**: 3400
- **启动延迟**: 5秒
- **说明**: 提供 Web 管理界面和 API 接口

### 2. schedule_service.desktop
- **服务**: Schedule 播放列表计划服务
- **端口**: 3700
- **启动延迟**: 10秒（在 admin 之后）
- **说明**: 自动挂载 NAS 并生成播放列表计划

### 3. viewer_service.desktop
- **服务**: Viewer 媒体显示器
- **端口**: 无（GUI 应用）
- **启动延迟**: 20秒（在其他服务之后）
- **说明**: 多区域媒体显示界面

## 启动顺序

```
5秒  -> Admin Service (管理后台)
10秒 -> Schedule Service (计划服务，依赖 Admin)
20秒 -> Viewer Service (显示器，依赖 Admin)
```

## 安装方法

### 方法一：软链接到用户自动启动目录（推荐）

使用软链接的好处是修改项目中的 .desktop 文件后，自动启动配置会自动同步更新。

```bash
# 进入项目目录
cd /home/show/my-ad

 chown -R show:show /home/show/my-ad

# 确保自动启动目录存在
mkdir -p ~/.config/autostart

# 创建软链接
ln -sf $(pwd)/autostart/admin_service.desktop ~/.config/autostart/admin_service.desktop
ln -sf $(pwd)/autostart/schedule_service.desktop ~/.config/autostart/schedule_service.desktop
ln -sf $(pwd)/autostart/viewer_service.desktop ~/.config/autostart/viewer_service.desktop

# 验证链接
ls -la ~/.config/autostart/ | grep "my-ad"
```

**一键安装脚本：**

```bash
# 在项目根目录执行
cd /home/show/my-ad
for file in autostart/*.desktop; do
    ln -sf "$(pwd)/$file" ~/.config/autostart/$(basename "$file")
done
echo "自动启动脚本已链接完成"
```

### 方法二：复制到用户自动启动目录

如果不想使用软链接，可以直接复制文件：

```bash
# 复制所有 .desktop 文件到用户自动启动目录
cp autostart/*.desktop ~/.config/autostart/

# 设置可执行权限
chmod +x ~/.config/autostart/*.desktop
```

### 方法三：复制到系统自动启动目录（需要 root 权限）

```bash
# 复制到系统目录
sudo cp autostart/*.desktop /etc/xdg/autostart/

# 设置权限
sudo chmod 644 /etc/xdg/autostart/*.desktop
```

## 配置说明

### 修改项目路径

如果项目不在 `/home/show/my-ad` 目录，需要修改 .desktop 文件中的路径：

```ini
# 修改 Exec 行中的路径
Exec=/your/project/path/venv/bin/python /your/project/path/admin/app.py
```

### 修改虚拟环境路径

如果使用不同的虚拟环境名称，修改 `venv` 为实际名称：

```ini
# 例如使用 photoenv
Exec=/home/show/my-ad/photoenv/bin/python /home/show/my-ad/admin/app.py
```

### 修改启动延迟

调整 `X-GNOME-Autostart-Delay` 值（单位：秒）：

```ini
# 延迟 30 秒启动
X-GNOME-Autostart-Delay=30
```

### 禁用某个服务

设置 `X-GNOME-Autostart-enabled=false`：

```ini
X-GNOME-Autostart-enabled=false
```

## 验证安装

### 检查自动启动项

```bash
# 查看用户自动启动目录
ls -la ~/.config/autostart/

# 查看系统自动启动目录
ls -la /etc/xdg/autostart/
```

### 测试启动脚本

```bash
# 手动执行 .desktop 文件测试
gtk-launch admin_service.desktop
gtk-launch schedule_service.desktop
gtk-launch viewer_service.desktop
```

### 查看服务状态

```bash
# 检查服务是否运行
ps aux | grep "admin/app.py"
ps aux | grep "schedule/app.py"
ps aux | grep "viewer/main.py"

# 检查端口占用
netstat -tlnp | grep 3400  # Admin
netstat -tlnp | grep 3700  # Schedule
```

## 日志查看

服务启动后的日志输出位置：

```bash
# 查看系统日志
journalctl -xe | grep -i "admin\|schedule\|viewer"

# 如果使用 systemd 用户服务
journalctl --user -xe
```

## 卸载方法

### 删除软链接或复制的文件

```bash
# 删除用户自动启动文件（软链接或复制的文件）
rm ~/.config/autostart/admin_service.desktop
rm ~/.config/autostart/schedule_service.desktop
rm ~/.config/autostart/viewer_service.desktop

# 一键删除
rm ~/.config/autostart/{admin,schedule,viewer}_service.desktop
```

### 删除系统自动启动文件

```bash
# 删除系统自动启动文件（需要 root）
sudo rm /etc/xdg/autostart/admin_service.desktop
sudo rm /etc/xdg/autostart/schedule_service.desktop
sudo rm /etc/xdg/autostart/viewer_service.desktop
```

## 故障排查

### 服务未启动

1. 检查 Python 路径是否正确
2. 检查虚拟环境是否存在
3. 检查项目路径是否正确
4. 查看系统日志

### 权限问题

```bash
# 确保脚本有执行权限
chmod +x ~/.config/autostart/*.desktop

# 确保 Python 脚本有执行权限
chmod +x /home/show/my-ad/admin/app.py
chmod +x /home/show/my-ad/schedule/app.py
chmod +x /home/show/my-ad/viewer/main.py
```

### NAS 挂载失败

Schedule 服务需要 sudo 权限挂载 NFS，配置 sudoers：

```bash
# 编辑 sudoers
sudo visudo

# 添加以下行（替换 show 为实际用户名）
show ALL=(ALL) NOPASSWD: /bin/mount, /bin/umount
```

## 注意事项

1. **启动顺序很重要**: Viewer 和 Schedule 依赖 Admin 服务，确保 Admin 先启动
2. **延迟时间**: 根据系统性能调整启动延迟时间
3. **虚拟环境**: 确保使用正确的 Python 虚拟环境
4. **NAS 挂载**: Schedule 服务需要网络和 NFS 客户端支持
5. **显示器**: Viewer 需要图形界面环境（X11 或 Wayland）

## 生产环境部署清单

### 0. 安装系统依赖（必需）

```bash
# 安装 SMB/CIFS 客户端（Debian/Ubuntu）
su -
apt update
apt install -y cifs-utils
exit

# 验证安装
mount.cifs --version
```

### 1. 安装自动启动脚本

```bash
cd /home/show/my-ad/autostart
chmod +x install.sh
./install.sh
```

### 2. 配置 Schedule 服务 sudo 权限（重要）

```bash
cd /home/show/my-ad/schedule
chmod +x setup_sudo.sh
./setup_sudo.sh
```

### 3. 验证配置

```bash
# 验证 sudo 权限
sudo -n mount --version

# 验证自动启动脚本
ls -la ~/.config/autostart/ | grep service
```

### 4. 测试手动启动

```bash
# 测试 Admin 服务
cd /home/show/my-ad
./venv/bin/python admin/app.py

# 测试 Schedule 服务
./venv/bin/python schedule/app.py

# 测试 Viewer 服务
./venv/bin/python viewer/main.py
```

### 5. 重启系统验证

```bash
sudo reboot
```

### 6. 检查服务状态

```bash
# 检查进程
ps aux | grep "admin/app.py"
ps aux | grep "schedule/app.py"
ps aux | grep "viewer/main.py"

# 检查端口
netstat -tlnp | grep 3400  # Admin
netstat -tlnp | grep 3700  # Schedule
```

### 部署检查清单

- [ ] 安装自动启动脚本（install.sh）
- [ ] 配置 sudo 权限（setup_sudo.sh）
- [ ] 修改项目路径为实际路径（如果不是 /home/show/my-ad）
- [ ] 修改虚拟环境路径（如果不是 venv）
- [ ] 测试手动启动每个服务
- [ ] 验证 sudo 权限（sudo -n mount --version）
- [ ] 重启系统验证自动启动
- [ ] 检查服务运行状态
- [ ] 检查日志输出
- [ ] 测试 NAS 挂载
- [ ] 测试生成播放列表
