#!/bin/bash
# 配置文件检查脚本

echo "=========================================="
echo "检查配置文件"
echo "=========================================="
echo ""

# 检查 config.yaml 是否存在
if [ -f "config/config.yaml" ]; then
    echo "✓ config/config.yaml 存在"
    
    # 检查是否包含敏感信息
    echo ""
    echo "检查敏感信息..."
    
    if grep -q "your_password_here" config/config.yaml; then
        echo "⚠️  警告: 配置文件包含默认密码，请修改"
    fi
    
    if grep -q "your_username" config/config.yaml; then
        echo "⚠️  警告: 配置文件包含默认用户名，请修改"
    fi
    
    if grep -q "change_this" config/config.yaml; then
        echo "⚠️  警告: 配置文件包含默认密钥，请修改"
    fi
    
else
    echo "✗ config/config.yaml 不存在"
    echo ""
    echo "请复制示例配置文件:"
    echo "  cp config/config.yaml.example config/config.yaml"
    echo ""
    exit 1
fi

echo ""
echo "=========================================="
echo "检查 Git 状态"
echo "=========================================="
echo ""

# 检查 config.yaml 是否被 Git 跟踪
if git ls-files --error-unmatch config/config.yaml 2>/dev/null; then
    echo "✗ 警告: config/config.yaml 被 Git 跟踪"
    echo "  请运行: git rm --cached config/config.yaml"
else
    echo "✓ config/config.yaml 未被 Git 跟踪"
fi

# 检查数据库文件是否被 Git 跟踪
if git ls-files --error-unmatch config/media_display.db 2>/dev/null; then
    echo "✗ 警告: media_display.db 被 Git 跟踪"
    echo "  请运行: git rm --cached config/media_display.db"
else
    echo "✓ media_display.db 未被 Git 跟踪"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
