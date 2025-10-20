#!/bin/bash
# Git 配置和提交脚本

echo "=========================================="
echo "配置 Git 仓库"
echo "=========================================="
echo ""

# 设置用户名（使用 ltanme）
echo "设置 Git 用户名为: ltanme"
git config user.name "ltanme"

# 设置邮箱（如果需要）
read -p "请输入 Git 邮箱（回车跳过）: " email
if [ ! -z "$email" ]; then
    git config user.email "$email"
    echo "✓ 已设置邮箱: $email"
fi

echo ""
echo "当前 Git 配置:"
echo "  用户名: $(git config user.name)"
echo "  邮箱: $(git config user.email)"
echo ""

# 初始化 Git 仓库（如果还没有）
if [ ! -d ".git" ]; then
    echo "初始化 Git 仓库..."
    git init
    echo "✓ Git 仓库已初始化"
else
    echo "✓ Git 仓库已存在"
fi

echo ""
echo "=========================================="
echo "检查敏感文件"
echo "=========================================="
echo ""

# 检查并移除已跟踪的敏感文件
if git ls-files --error-unmatch config/config.yaml 2>/dev/null; then
    echo "移除 config/config.yaml..."
    git rm --cached config/config.yaml
fi

if git ls-files --error-unmatch config/media_display.db 2>/dev/null; then
    echo "移除 config/media_display.db..."
    git rm --cached config/media_display.db
fi

echo "✓ 敏感文件检查完成"
echo ""

echo "=========================================="
echo "准备提交文件"
echo "=========================================="
echo ""

# 添加所有文件
echo "添加文件到 Git..."
git add .

# 显示状态
echo ""
echo "Git 状态:"
git status --short

echo ""
echo "=========================================="
echo "提交到 GitHub"
echo "=========================================="
echo ""

# 提交
echo "提交代码..."
git commit -m "Initial commit: Multi-zone media display system

- 多区域媒体显示系统
- 支持图片、视频、文字混合播放
- Web 管理界面
- 自动播放列表生成
- NAS 自动挂载（SMB/NFS）
- 完整的日志系统"

# 设置分支名为 main
echo ""
echo "设置主分支为 main..."
git branch -M main

# 添加远程仓库
echo ""
echo "添加远程仓库..."
if git remote | grep -q "^origin$"; then
    echo "远程仓库已存在，移除旧的..."
    git remote remove origin
fi
git remote add origin git@github.com:ltanme/my-ad.git

echo "✓ 远程仓库已添加: git@github.com:ltanme/my-ad.git"

# 推送到 GitHub
echo ""
echo "推送到 GitHub..."
git push -u origin main

echo ""
echo "=========================================="
echo "✓ 完成！"
echo "=========================================="
echo ""
echo "项目已推送到: https://github.com/ltanme/my-ad"
echo ""
