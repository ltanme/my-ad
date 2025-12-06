#!/bin/bash
# 启动管理后台

echo "======================================"
echo "媒体显示系统管理后台"
echo "======================================"

# 检查依赖
python3 -c "import flask" 2>/dev/null || {
    echo "✗ Flask 未安装"
    echo "请运行: pip install -r ../requirements.txt"
    exit 1
}

echo "✓ 依赖检查通过"
echo ""
echo "启动管理后台..."
echo "访问地址: http://[::1]:3400 或 http://127.0.0.1:3400"
echo "默认账号: admin / admin123"
echo "======================================"
echo ""

python3 app.py
