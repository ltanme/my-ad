# 修改 Git 历史提交作者

如果你的 Git 历史记录中的用户名不正确，可以使用以下方法修改。

## 方法一：重置历史（推荐，最简单）

**适用场景**：新项目，不在意历史记录

```bash
chmod +x reset_git_history.sh
./reset_git_history.sh
```

这会：
- ✅ 删除所有 Git 历史
- ✅ 重新初始化仓库
- ✅ 使用正确的用户名（ltanme）创建新的初始提交
- ✅ 配置远程仓库

然后强制推送：
```bash
git push --force origin main
```

## 方法二：使用 git filter-branch

**适用场景**：需要保留提交历史

```bash
chmod +x fix_git_history.sh
./fix_git_history.sh
```

这会修改所有历史提交的作者信息，然后：

```bash
git push --force origin main
```

## 方法三：使用 git filter-repo（最安全）

**适用场景**：大型项目，需要保留完整历史

首先安装 git-filter-repo：
```bash
# Debian/Ubuntu
sudo apt install git-filter-repo

# macOS
brew install git-filter-repo

# 或使用 pip
pip3 install git-filter-repo
```

然后运行：
```bash
chmod +x fix_git_history_safe.sh
./fix_git_history_safe.sh
```

## 验证修改

查看提交历史：
```bash
git log --pretty=format:"%h - %an <%ae> : %s"
```

应该显示所有提交的作者都是 `ltanme`。

## 推送到 GitHub

修改完成后，强制推送到远程仓库：

```bash
git push --force origin main
```

⚠️ **警告**：强制推送会覆盖远程仓库的历史记录。如果其他人已经克隆了仓库，他们需要重新克隆。

## 如果远程仓库是空的

如果你的 GitHub 仓库是新创建的空仓库，直接推送即可：

```bash
git push -u origin main
```

不需要使用 `--force`。

## 推荐流程

对于新项目，推荐使用**方法一**（重置历史）：

```bash
# 1. 重置历史
./reset_git_history.sh

# 2. 推送到 GitHub
git push --force origin main
```

简单快速，一步到位！
