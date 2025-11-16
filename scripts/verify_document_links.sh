#!/bin/bash

# 文档链接验证脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-16

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
TOTAL_LINKS=0
VALID_LINKS=0
INVALID_LINKS=0

echo "=========================================="
echo "文档链接验证工具"
echo "=========================================="
echo ""

# 验证文件是否存在
check_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
        return 0
    else
        echo -e "${RED}✗${NC} $file (文件不存在)"
        return 1
    fi
}

# 提取 Markdown 文件中的链接
extract_links() {
    local file=$1
    # 提取 [text](link) 格式的链接，排除 http/https 链接
    grep -oP '\[.*?\]\(\K[^)]+(?=\))' "$file" 2>/dev/null | grep -v '^http' || true
}

# 验证单个文档的所有链接
verify_document() {
    local doc=$1
    local doc_dir=$(dirname "$doc")
    
    echo ""
    echo "=========================================="
    echo "验证文档: $doc"
    echo "=========================================="
    
    if [ ! -f "$doc" ]; then
        echo -e "${RED}✗ 文档不存在: $doc${NC}"
        return 1
    fi
    
    local links=$(extract_links "$doc")
    
    if [ -z "$links" ]; then
        echo -e "${YELLOW}⚠ 未找到本地文件链接${NC}"
        return 0
    fi
    
    while IFS= read -r link; do
        # 跳过空行
        [ -z "$link" ] && continue
        
        # 跳过锚点链接
        [[ "$link" =~ ^# ]] && continue
        
        TOTAL_LINKS=$((TOTAL_LINKS + 1))
        
        # 处理相对路径
        if [[ "$link" =~ ^/ ]]; then
            # 绝对路径（从项目根目录）
            target_file="${link#/}"
        else
            # 相对路径
            target_file="$doc_dir/$link"
        fi
        
        # 规范化路径
        target_file=$(realpath -m "$target_file" 2>/dev/null || echo "$target_file")
        
        # 检查文件是否存在
        if [ -f "$target_file" ]; then
            echo -e "${GREEN}✓${NC} $link"
            VALID_LINKS=$((VALID_LINKS + 1))
        else
            echo -e "${RED}✗${NC} $link -> $target_file (文件不存在)"
            INVALID_LINKS=$((INVALID_LINKS + 1))
        fi
    done <<< "$links"
}

# 主验证流程
main() {
    echo "开始验证文档链接..."
    echo ""
    
    # 验证 README.md
    verify_document "README.md"
    
    # 验证 DEPLOYMENT.md
    verify_document "DEPLOYMENT.md"
    
    # 验证 API_DOCUMENTATION.md
    verify_document "eks-info-app/API_DOCUMENTATION.md"
    
    # 验证其他重要文档
    echo ""
    echo "=========================================="
    echo "验证其他引用的文档是否存在"
    echo "=========================================="
    
    # 从 README.md 中提取的文档列表
    local docs=(
        "DEPLOYMENT.md"
        "PROJECT_SUMMARY.md"
        "BUGFIX_REPORT.md"
        "TROUBLESHOOTING.md"
        "eks-info-app/API_DOCUMENTATION.md"
        "eks-info-app/DOCKER_BUILD_GUIDE.md"
        "k8s/README.md"
        ".kiro/specs/eks-info-webapp/requirements.md"
        ".kiro/specs/eks-info-webapp/design.md"
        ".kiro/specs/eks-info-webapp/tasks.md"
    )
    
    for doc in "${docs[@]}"; do
        TOTAL_LINKS=$((TOTAL_LINKS + 1))
        if check_file "$doc"; then
            VALID_LINKS=$((VALID_LINKS + 1))
        else
            INVALID_LINKS=$((INVALID_LINKS + 1))
        fi
    done
    
    # 验证脚本文件
    echo ""
    echo "=========================================="
    echo "验证脚本文件"
    echo "=========================================="
    
    local scripts=(
        "scripts/build.sh"
        "scripts/deploy.sh"
        "scripts/get-alb-hostname.sh"
        "scripts/test_all_pages.sh"
        "scripts/verify_environment_info.sh"
        "scripts/verify_frontend.sh"
    )
    
    for script in "${scripts[@]}"; do
        TOTAL_LINKS=$((TOTAL_LINKS + 1))
        if check_file "$script"; then
            VALID_LINKS=$((VALID_LINKS + 1))
        else
            INVALID_LINKS=$((INVALID_LINKS + 1))
        fi
    done
    
    # 验证 Terraform 文件
    echo ""
    echo "=========================================="
    echo "验证 Terraform 文件"
    echo "=========================================="
    
    local tf_files=(
        "terraform/main.tf"
        "terraform/app.tf"
        "terraform/variables.tf"
        "terraform/outputs.tf"
        "terraform/versions.tf"
        "terraform/terraform.tfvars"
    )
    
    for tf_file in "${tf_files[@]}"; do
        TOTAL_LINKS=$((TOTAL_LINKS + 1))
        if check_file "$tf_file"; then
            VALID_LINKS=$((VALID_LINKS + 1))
        else
            INVALID_LINKS=$((INVALID_LINKS + 1))
        fi
    done
    
    # 验证 Kubernetes 配置文件
    echo ""
    echo "=========================================="
    echo "验证 Kubernetes 配置文件"
    echo "=========================================="
    
    local k8s_files=(
        "k8s/namespace.yaml"
        "k8s/serviceaccount.yaml"
        "k8s/deployment.yaml"
        "k8s/service.yaml"
        "k8s/ingress.yaml"
        "k8s/hpa.yaml"
        "k8s/storage/storageclass-ebs.yaml"
        "k8s/storage/storageclass-efs.yaml"
        "k8s/storage/pvc-ebs.yaml"
        "k8s/storage/pvc-efs.yaml"
    )
    
    for k8s_file in "${k8s_files[@]}"; do
        TOTAL_LINKS=$((TOTAL_LINKS + 1))
        if check_file "$k8s_file"; then
            VALID_LINKS=$((VALID_LINKS + 1))
        else
            INVALID_LINKS=$((INVALID_LINKS + 1))
        fi
    done
    
    # 打印总结
    echo ""
    echo "=========================================="
    echo "验证总结"
    echo "=========================================="
    echo "总链接数: $TOTAL_LINKS"
    echo -e "${GREEN}有效链接: $VALID_LINKS${NC}"
    
    if [ $INVALID_LINKS -gt 0 ]; then
        echo -e "${RED}无效链接: $INVALID_LINKS${NC}"
        echo ""
        echo -e "${RED}验证失败！存在无效链接。${NC}"
        return 1
    else
        echo -e "${GREEN}无效链接: 0${NC}"
        echo ""
        echo -e "${GREEN}✓ 所有链接验证通过！${NC}"
        return 0
    fi
}

# 执行主函数
main
exit $?
