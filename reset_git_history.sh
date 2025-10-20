#!/bin/bash
# 重置 Git 历史（最简单的方法）
# 删除所有历史记录，重新开始

echo "=========================================="
echo "重置 Git 历史记录"
echo "=========================================="
echo ""
echo "⚠️  警告: 这将删除所有 Git 历史记录"
echo "   所有提交历史将被清除，重新开始"
echo ""

read -p "是否继续? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "取消操作"
    exit 0
fi

echo ""
echo "开始重置..."
echo ""

# 1. 删除 .git 目录
echo "1. 删除旧的 Git 历史..."
rm -rf .git

# 2. 重新初始化
echo "2. 重新初始化 Git 仓库..."
git init

# 3. 配置用户信息
echo "3. 配置 Git 用户信息..."
git config user.name "ltanme"
git config user.email "ltanme@users.noreply.github.com"

# 4. 添加所有文件
echo "4. 添加所有文件..."
git add .

# 5. 创建初始提交
echo "5. 创建初始提交..."
git commit -m "Initial commit: Multi-zone media display system

- 多区域媒体显示系统
- 支持图片、视频、文字混合播放
- Web 管理界面
- 自动播放列表生成
- NAS 自动挂载（SMB/NFS）
- 完整的日志系统"

# 6. 设置主分支
echo "6. 设置主分支为 main..."
git branch -M main

# 7. 添加远程仓库
echo "7. 添加远程仓库..."
git remote add origin git@github.com:ltanme/my-ad.git

echo ""
echo "=========================================="
echo "✓ Git 历史已重置"
echo "=========================================="
echo ""

# 显示提交记录
echo "当前提交记录:"
git log --oneline --pretty=format:"%h - %an <%ae> : %s"

echo ""
echo ""
echo "=========================================="
echo "下一步操作"
echo "=========================================="
echo ""
echo "强制推送到 GitHub（会覆盖远程仓库）:"
echo "  git push --force origin main"
echo ""
echo "或者使用脚本:"
echo "  ./push_to_github.sh"
echo ""
