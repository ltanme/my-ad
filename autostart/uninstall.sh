#!/bin/bash
# 自动启动脚本卸载工具

set -e

# 自动启动目录
AUTOSTART_DIR="$HOME/.config/autostart"

echo "=========================================="
echo "卸载自动启动脚本"
echo "=========================================="
echo "自动启动目录: $AUTOSTART_DIR"
echo ""

# 要卸载的服务列表
SERVICES=(
    "admin_service.desktop"
    "schedule_service.desktop"
    "viewer_service.desktop"
)

# 删除软链接或文件
echo "删除自动启动脚本..."
for service in "${SERVICES[@]}"; do
    TARGET="$AUTOSTART_DIR/$service"
    
    if [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
        rm -f "$TARGET"
        echo "  ✓ 已删除: $service"
    else
        echo "  - 不存在: $service"
    fi
done

echo ""
echo "=========================================="
echo "验证卸载结果"
echo "=========================================="

# 验证是否已删除
ALL_REMOVED=true
for service in "${SERVICES[@]}"; do
    TARGET="$AUTOSTART_DIR/$service"
    if [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
        echo "✗ $service 仍然存在"
        ALL_REMOVED=false
    else
        echo "✓ $service 已删除"
    fi
done

echo ""
if [ "$ALL_REMOVED" = true ]; then
    echo "=========================================="
    echo "卸载完成！"
    echo "=========================================="
    echo "所有自动启动脚本已删除"
    echo "重启系统后服务将不再自动启动"
else
    echo "=========================================="
    echo "卸载未完全成功"
    echo "=========================================="
    echo "请手动检查并删除残留文件"
fi
echo ""
