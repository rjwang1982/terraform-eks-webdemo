#!/bin/bash
#
# Simple App 构建和推送脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-18

set -e

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 配置
IMAGE_NAME="rjwang/rj-py-webdemo"
VERSION="2.0"
PLATFORM="linux/arm64"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker
check_docker() {
    log_info "检查 Docker..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    log_success "Docker 检查通过"
}

# 构建镜像
build_image() {
    log_info "开始构建 ARM64 镜像..."
    log_info "镜像: ${IMAGE_NAME}:${VERSION}"
    log_info "构建目录: ${SCRIPT_DIR}"
    
    docker buildx build \
        --platform "${PLATFORM}" \
        --tag "${IMAGE_NAME}:${VERSION}" \
        --tag "${IMAGE_NAME}:latest" \
        --load \
        --file "${SCRIPT_DIR}/Dockerfile" \
        "${SCRIPT_DIR}"
    
    log_success "镜像构建完成"
}

# 推送镜像
push_image() {
    log_info "推送镜像到 DockerHub..."
    
    docker push "${IMAGE_NAME}:${VERSION}"
    docker push "${IMAGE_NAME}:latest"
    
    log_success "镜像推送完成"
}

# 主函数
main() {
    echo "========================================"
    echo "  Simple App 构建和推送"
    echo "========================================"
    
    check_docker
    build_image
    push_image
    
    echo ""
    log_success "全部完成！"
    echo "镜像: ${IMAGE_NAME}:${VERSION}"
}

main "$@"
