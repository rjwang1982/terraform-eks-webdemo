#!/bin/bash
#
# EKS Info WebApp - 构建和推送脚本
#
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-14
#
# 用途: 构建 Docker 镜像并推送到 ECR

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# 显示帮助信息
show_help() {
    echo ""
    echo "EKS Info WebApp - 构建和推送脚本"
    echo ""
    echo "用法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示帮助信息"
    echo "  -t, --tag TAG       指定镜像标签 (默认: latest)"
    echo "  -p, --profile NAME  指定 AWS Profile (默认: susermt)"
    echo "  -r, --region REGION 指定 AWS 区域 (默认: ap-southeast-1)"
    echo "  --no-push           只构建不推送"
    echo "  --no-build          只推送不构建"
    echo ""
    echo "示例:"
    echo "  $0                                    # 构建并推送 latest 标签"
    echo "  $0 -t v1.0                            # 构建并推送 v1.0 标签"
    echo "  $0 --no-push                          # 只构建不推送"
    echo "  $0 -p myprofile -r us-west-2          # 使用自定义 profile 和区域"
    echo ""
}

# 默认参数
IMAGE_TAG="latest"
AWS_PROFILE="${AWS_PROFILE:-susermt}"
AWS_REGION="ap-southeast-1"
DO_BUILD=true
DO_PUSH=true

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -p|--profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        --no-push)
            DO_PUSH=false
            shift
            ;;
        --no-build)
            DO_BUILD=false
            shift
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

echo ""
echo "=========================================="
echo "EKS Info WebApp - 构建和推送"
echo "=========================================="
echo ""

# 检查工具
log_info "检查必要工具..."
for tool in docker aws; do
    if ! command -v $tool &> /dev/null; then
        log_error "$tool 未安装"
        exit 1
    fi
done
log_success "工具检查通过"

# 获取 AWS 账户信息
log_info "获取 AWS 账户信息..."
AWS_ACCOUNT_ID=$(aws --profile "$AWS_PROFILE" sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    log_error "无法获取 AWS 账户 ID，请检查 AWS 凭证"
    exit 1
fi

ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/eks-info-app"
FULL_IMAGE_NAME="${ECR_REPO_URI}:${IMAGE_TAG}"

echo "  AWS 账户 ID: $AWS_ACCOUNT_ID"
echo "  AWS Profile: $AWS_PROFILE"
echo "  AWS 区域: $AWS_REGION"
echo "  ECR 仓库: $ECR_REPO_URI"
echo "  镜像标签: $IMAGE_TAG"
echo ""

# 确保 ECR 仓库存在
log_info "检查 ECR 仓库..."
if ! aws --profile "$AWS_PROFILE" ecr describe-repositories \
    --repository-names eks-info-app \
    --region "$AWS_REGION" &>/dev/null; then
    
    log_error "ECR 仓库不存在"
    echo ""
    echo "ECR 仓库由 Terraform 管理，请先运行 Terraform 创建基础设施："
    echo "  cd terraform"
    echo "  terraform init"
    echo "  terraform apply"
    echo ""
    echo "或者运行完整部署脚本："
    echo "  ./scripts/deploy.sh"
    echo ""
    exit 1
else
    log_success "ECR 仓库已存在"
fi

# 构建镜像
if [ "$DO_BUILD" = true ]; then
    log_info "开始构建 Docker 镜像..."
    echo "  平台: linux/arm64"
    echo "  镜像: $FULL_IMAGE_NAME"
    echo ""
    
    # 获取脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    APP_DIR="$PROJECT_ROOT/eks-info-app"
    
    # 检查应用目录是否存在
    if [ ! -d "$APP_DIR" ]; then
        log_error "应用目录不存在: $APP_DIR"
        exit 1
    fi
    
    # 检查 Docker Buildx
    if ! docker buildx version &> /dev/null; then
        log_error "Docker Buildx 未安装"
        exit 1
    fi
    
    # 构建镜像（使用绝对路径作为构建上下文）
    docker buildx build \
        --platform linux/arm64 \
        --tag "$FULL_IMAGE_NAME" \
        --load \
        --progress=plain \
        "$APP_DIR"
    
    if [ $? -eq 0 ]; then
        log_success "镜像构建成功"
    else
        log_error "镜像构建失败"
        exit 1
    fi
    
    # 验证镜像
    log_info "验证镜像架构..."
    ARCH=$(docker inspect "$FULL_IMAGE_NAME" --format='{{.Architecture}}')
    if [ "$ARCH" = "arm64" ]; then
        log_success "镜像架构验证通过: $ARCH"
    else
        log_error "镜像架构不正确: $ARCH (期望: arm64)"
        exit 1
    fi
else
    log_info "跳过构建步骤"
fi

# 推送镜像
if [ "$DO_PUSH" = true ]; then
    log_info "登录到 ECR..."
    aws --profile "$AWS_PROFILE" ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$ECR_REPO_URI"
    
    if [ $? -ne 0 ]; then
        log_error "ECR 登录失败"
        exit 1
    fi
    log_success "ECR 登录成功"
    
    log_info "推送镜像到 ECR..."
    docker push "$FULL_IMAGE_NAME"
    
    if [ $? -eq 0 ]; then
        log_success "镜像推送成功"
    else
        log_error "镜像推送失败"
        exit 1
    fi
    
    # 验证推送
    log_info "验证 ECR 镜像..."
    aws --profile "$AWS_PROFILE" ecr describe-images \
        --repository-name eks-info-app \
        --image-ids imageTag="$IMAGE_TAG" \
        --region "$AWS_REGION" \
        --query 'imageDetails[0].[imageTags[0],imageSizeInBytes,imagePushedAt]' \
        --output table
    
    log_success "镜像验证成功"
else
    log_info "跳过推送步骤"
fi

echo ""
echo "=========================================="
log_success "完成！"
echo "=========================================="
echo ""
echo "镜像信息:"
echo "  URI: $FULL_IMAGE_NAME"
echo "  标签: $IMAGE_TAG"
echo "  架构: arm64"
echo ""
echo "下一步:"
echo "  1. 更新 Kubernetes Deployment 使用新镜像"
echo "  2. 运行 ./deploy.sh 部署到 EKS"
echo ""
