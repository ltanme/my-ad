#!/bin/bash
# 快速推送到 GitHub

echo "=========================================="
echo "推送代码到 GitHub"
echo "=========================================="
echo ""

# 检查是否有未提交的更改
if [[ -n $(git status -s) ]]; then
    echo "发现未提交的更改，添加到 Git..."
    git add .
    
    # 提交
    read -p "请输入提交信息: " commit_msg
    if [ -z "$commit_msg" ]; then
        commit_msg="Update files"
    fi
    
    git commit -m "$commit_msg"
    echo "✓ 已提交"
else
    echo "没有需要提交的更改"
fi

echo ""
echo "推送到 GitHub..."
git push origin main

echo ""
echo "=========================================="
echo "✓ 完成！"
echo "=========================================="
echo ""
echo "查看项目: https://github.com/ltanme/my-ad"
echo ""
