#!/bin/bash

# --------------------------
# GitHub 同步脚本
# 
# Author: RJ.Wang
# Email: wangrenjun@gmail.com
# --------------------------

set -e

# 颜色定义
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
echo "🚀 Terraform EKS WebDemo - GitHub 同步脚本"
echo "Author: RJ.Wang (wangrenjun@gmail.com)"
echo ""

# 项目信息
REPO_NAME="terraform-eks-webdemo"
REPO_DESCRIPTION="Complete EKS cluster and web application deployment solution using Terraform"

log_info "项目信息:"
echo "  📦 仓库名称: $REPO_NAME"
echo "  📝 描述: $REPO_DESCRIPTION"
echo "  👤 作者: RJ.Wang"
echo "  📧 邮箱: wangrenjun@gmail.com"
echo ""

log_warning "请按照以下步骤在 GitHub 上创建仓库并同步代码："
echo ""

echo "🌐 步骤 1: 在 GitHub 上创建新仓库"
echo "   1. 访问: https://github.com/new"
echo "   2. 仓库名称: $REPO_NAME"
echo "   3. 描述: $REPO_DESCRIPTION"
echo "   4. 设置为 Public（推荐）或 Private"
echo "   5. ❌ 不要初始化 README、.gitignore 或 license（我们已经有了）"
echo "   6. 点击 'Create repository'"
echo ""

echo "📡 步骤 2: 获取仓库 URL"
echo "   创建后，GitHub 会显示仓库 URL，类似："
echo "   https://github.com/YOUR_USERNAME/$REPO_NAME.git"
echo ""

echo "🔗 步骤 3: 添加远程仓库并推送"
echo "   复制以下命令并替换 YOUR_USERNAME："
echo ""
echo "   cd $(pwd)"
echo "   git remote add origin https://github.com/YOUR_USERNAME/$REPO_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""

log_info "当前 Git 状态:"
git log --oneline -5 2>/dev/null || echo "  无提交历史"
echo ""

log_info "当前分支:"
git branch --show-current
echo ""

log_info "文件统计:"
echo "  📄 总文件数: $(find . -type f -not -path './.git/*' | wc -l | tr -d ' ')"
echo "  📝 代码行数: $(find . -name '*.tf' -o -name '*.sh' -o -name '*.md' | xargs wc -l | tail -1 | awk '{print $1}')"
echo ""

log_success "✅ 本地仓库已准备就绪！"
echo ""

log_warning "📋 推送完成后，您可以："
echo "  1. 🌐 访问仓库页面查看代码"
echo "  2. 📝 编辑仓库描述和标签"
echo "  3. 🏷️ 添加主题标签: terraform, aws, eks, kubernetes, devops"
echo "  4. 📖 确认 README.md 正确显示"
echo "  5. ⭐ 为仓库添加 star（如果您喜欢的话）"
echo ""

echo "🎯 推荐的仓库标签 (Topics):"
echo "   terraform aws eks kubernetes devops infrastructure-as-code"
echo "   automation deployment cloud-native container-orchestration"
echo ""

log_info "如果遇到问题，请检查："
echo "  1. GitHub 账户是否有创建仓库的权限"
echo "  2. Git 凭证是否正确配置"
echo "  3. 网络连接是否正常"
echo ""

echo "🎉 祝您使用愉快！"
