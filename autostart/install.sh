#!/bin/bash
# 自动启动脚本安装工具

set -e

# 获取脚本所在目录（项目的 autostart 目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 自动启动目录
AUTOSTART_DIR="$HOME/.config/autostart"

echo "=========================================="
echo "安装自动启动脚本"
echo "=========================================="
echo "项目目录: $PROJECT_DIR"
echo "自动启动目录: $AUTOSTART_DIR"
echo ""

# 确保自动启动目录存在
mkdir -p "$AUTOSTART_DIR"

# 要安装的服务列表
SERVICES=(
    "admin_service.desktop"
    "schedule_service.desktop"
    "viewer_service.desktop"
)

# 创建软链接
echo "创建软链接..."
for service in "${SERVICES[@]}"; do
    SOURCE="$SCRIPT_DIR/$service"
    TARGET="$AUTOSTART_DIR/$service"
    
    if [ -f "$SOURCE" ]; then
        # 如果目标已存在，先删除
        if [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
            echo "  删除旧的: $service"
            rm -f "$TARGET"
        fi
        
        # 创建软链接
        ln -sf "$SOURCE" "$TARGET"
        echo "  ✓ 已链接: $service"
    else
        echo "  ✗ 文件不存在: $service"
    fi
done

echo ""
echo "=========================================="
echo "验证安装结果"
echo "=========================================="

# 验证链接
for service in "${SERVICES[@]}"; do
    TARGET="$AUTOSTART_DIR/$service"
    if [ -L "$TARGET" ]; then
        LINK_TARGET=$(readlink "$TARGET")
        echo "✓ $service -> $LINK_TARGET"
    else
        echo "✗ $service 未安装"
    fi
done

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo "提示："
echo "1. 重启系统后服务将自动启动"
echo "2. 或手动测试: gtk-launch admin_service.desktop"
echo "3. 查看状态: ls -la ~/.config/autostart/"
echo "4. 卸载: 运行 ./uninstall.sh"
echo ""
