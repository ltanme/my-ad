#!/bin/bash
# 使用 git filter-repo 修改 Git 历史（更安全的方法）

echo "=========================================="
echo "修改 Git 历史提交记录（安全方法）"
echo "=========================================="
echo ""

# 检查是否安装了 git-filter-repo
if ! command -v git-filter-repo &> /dev/null; then
    echo "⚠️  git-filter-repo 未安装"
    echo ""
    echo "安装方法:"
    echo "  Debian/Ubuntu: sudo apt install git-filter-repo"
    echo "  macOS: brew install git-filter-repo"
    echo "  或: pip3 install git-filter-repo"
    echo ""
    echo "使用备用方法: ./fix_git_history.sh"
    exit 1
fi

# 新的用户名和邮箱
NEW_NAME="ltanme"
NEW_EMAIL="ltanme@users.noreply.github.com"

echo "将所有历史提交的作者修改为:"
echo "  用户名: $NEW_NAME"
echo "  邮箱: $NEW_EMAIL"
echo ""

read -p "是否继续? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "取消操作"
    exit 0
fi

echo ""
echo "备份当前仓库..."
cd ..
cp -r my-ad my-ad-backup
cd my-ad
echo "✓ 已备份到 ../my-ad-backup"
echo ""

echo "开始修改历史记录..."
echo ""

# 使用 git filter-repo 修改所有提交
git filter-repo --name-callback 'return b"ltanme"' \
                --email-callback 'return b"ltanme@users.noreply.github.com"' \
                --force

echo ""
echo "=========================================="
echo "✓ 历史记录修改完成"
echo "=========================================="
echo ""

# 显示最近的提交记录
echo "最近的提交记录:"
git log --oneline --graph --all -10 --pretty=format:"%h - %an <%ae> : %s"

echo ""
echo ""
echo "=========================================="
echo "下一步操作"
echo "=========================================="
echo ""
echo "1. 重新添加远程仓库:"
echo "   git remote add origin git@github.com:ltanme/my-ad.git"
echo ""
echo "2. 强制推送到远程仓库:"
echo "   git push --force origin main"
echo ""
echo "备份位置: ../my-ad-backup"
echo ""
