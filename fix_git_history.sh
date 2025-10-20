#!/bin/bash
# 修改 Git 历史提交记录中的用户名和邮箱

echo "=========================================="
echo "修改 Git 历史提交记录"
echo "=========================================="
echo ""

# 新的用户名和邮箱
NEW_NAME="ltanme"
NEW_EMAIL="ltanme@users.noreply.github.com"  # GitHub 提供的匿名邮箱

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
echo "开始修改历史记录..."
echo ""

# 使用 git filter-branch 修改所有提交的作者信息
git filter-branch --env-filter '
NEW_NAME="ltanme"
NEW_EMAIL="ltanme@users.noreply.github.com"

export GIT_AUTHOR_NAME="$NEW_NAME"
export GIT_AUTHOR_EMAIL="$NEW_EMAIL"
export GIT_COMMITTER_NAME="$NEW_NAME"
export GIT_COMMITTER_EMAIL="$NEW_EMAIL"
' --tag-name-filter cat -- --branches --tags

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
echo "1. 检查提交历史是否正确:"
echo "   git log --pretty=format:\"%h - %an <%ae> : %s\""
echo ""
echo "2. 强制推送到远程仓库（会覆盖远程历史）:"
echo "   git push --force origin main"
echo ""
echo "⚠️  警告: 强制推送会覆盖远程仓库的历史记录"
echo "   如果其他人已经克隆了仓库，他们需要重新克隆"
echo ""
