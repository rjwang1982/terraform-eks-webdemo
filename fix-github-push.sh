#!/bin/bash

# GitHub 推送问题解决脚本
# Author: RJ.Wang (wangrenjun@gmail.com)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

echo ""
echo "🔧 GitHub 推送问题解决脚本"
echo "Author: RJ.Wang (wangrenjun@gmail.com)"
echo ""

# 检查当前状态
log_info "检查当前 Git 状态..."
git status --porcelain

log_info "检查远程仓库配置..."
git remote -v

echo ""
log_warning "检测到 SSH 认证问题。提供以下解决方案："
echo ""

echo "🔑 方案 1: 配置 SSH 密钥（推荐）"
echo "   1. 复制您的公钥（已保存在 GITHUB_SSH_SETUP.md）"
echo "   2. 访问: https://github.com/settings/ssh/new"
echo "   3. 添加 SSH 密钥到 GitHub 账户"
echo "   4. 测试连接: ssh -T git@github.com"
echo ""

echo "🌐 方案 2: 使用 HTTPS（临时方案）"
echo "   执行以下命令切换到 HTTPS："
echo ""
echo "   git remote remove origin"
echo "   git remote add origin https://github.com/rjwang1982/terraform-eks-webdemo.git"
echo "   git push -u origin main"
echo ""

read -p "选择方案 (1=SSH配置, 2=切换HTTPS, q=退出): " choice

case $choice in
    1)
        log_info "显示您的 SSH 公钥："
        echo ""
        cat ~/.ssh/id_rsa_18616945668@139.com.pub
        echo ""
        log_warning "请复制上面的公钥内容，然后："
        echo "1. 访问: https://github.com/settings/ssh/new"
        echo "2. 粘贴公钥并保存"
        echo "3. 回来运行: ssh -T git@github.com 测试"
        ;;
    2)
        log_info "切换到 HTTPS 方式..."
        git remote remove origin 2>/dev/null || true
        git remote add origin https://github.com/rjwang1982/terraform-eks-webdemo.git
        log_success "已切换到 HTTPS 方式"
        echo ""
        log_info "现在尝试推送..."
        git push -u origin main
        ;;
    q)
        log_info "退出脚本"
        exit 0
        ;;
    *)
        log_error "无效选择"
        exit 1
        ;;
esac
