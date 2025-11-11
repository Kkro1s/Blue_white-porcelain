#!/bin/bash

# 青花瓷数字博物馆 - 快速部署脚本
# 用于部署到 GitHub Pages

echo "🚀 青花瓷数字博物馆部署脚本"
echo "================================"

# 检查是否已初始化 git
if [ ! -d ".git" ]; then
    echo "📦 初始化 Git 仓库..."
    git init
    echo "✅ Git 仓库初始化完成"
else
    echo "✅ Git 仓库已存在"
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo "📝 发现未提交的更改，正在添加..."
    git add .
    
    echo ""
    read -p "请输入提交信息（直接回车使用默认信息）: " commit_msg
    if [ -z "$commit_msg" ]; then
        commit_msg="Update: 更新青花瓷数字博物馆"
    fi
    
    git commit -m "$commit_msg"
    echo "✅ 更改已提交"
fi

# 检查远程仓库
if [ -z "$(git remote -v)" ]; then
    echo ""
    echo "⚠️  未检测到远程仓库"
    echo ""
    read -p "请输入您的 GitHub 仓库 URL (例如: https://github.com/username/repo.git): " repo_url
    
    if [ -n "$repo_url" ]; then
        git remote add origin "$repo_url"
        echo "✅ 远程仓库已添加"
    else
        echo "❌ 未提供仓库 URL，跳过远程仓库设置"
        echo "💡 您可以稍后手动添加: git remote add origin <your-repo-url>"
        exit 0
    fi
fi

# 推送到 GitHub
echo ""
echo "📤 正在推送到 GitHub..."
current_branch=$(git branch --show-current)

if [ -z "$current_branch" ]; then
    git checkout -b main
    current_branch="main"
fi

git push -u origin "$current_branch"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 部署成功！"
    echo ""
    echo "📋 下一步："
    echo "1. 访问您的 GitHub 仓库"
    echo "2. 进入 Settings > Pages"
    echo "3. Source 选择 'Deploy from a branch'"
    echo "4. Branch 选择 '$current_branch'，文件夹选择 '/'"
    echo "5. 点击 Save"
    echo ""
    echo "🌐 几分钟后，您的网站将在以下地址可用："
    echo "   https://您的用户名.github.io/仓库名/"
else
    echo ""
    echo "❌ 推送失败，请检查："
    echo "1. GitHub 仓库是否存在"
    echo "2. 您是否有推送权限"
    echo "3. 网络连接是否正常"
fi

