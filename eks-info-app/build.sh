#!/bin/bash
#
# EKS Info WebApp - Docker 镜像构建脚本
#
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-14
#
# 用途: 构建 ARM64 架构的 Docker 镜像

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}EKS Info WebApp - Docker 镜像构建${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}错误: Docker daemon 未运行${NC}"
    echo -e "${YELLOW}请启动 Docker Desktop 后重试${NC}"
    exit 1
fi

# 检查 buildx 是否可用
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}错误: docker buildx 不可用${NC}"
    exit 1
fi

# 设置镜像名称和标签
IMAGE_NAME="eks-info-app"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${GREEN}镜像名称: ${FULL_IMAGE_NAME}${NC}"
echo -e "${GREEN}目标架构: linux/arm64${NC}"
echo ""

# 构建镜像
echo -e "${YELLOW}开始构建镜像...${NC}"
docker buildx build \
    --platform linux/arm64 \
    -t "${FULL_IMAGE_NAME}" \
    --load \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 镜像构建成功${NC}"
    echo ""
    
    # 显示镜像信息
    echo -e "${GREEN}镜像信息:${NC}"
    docker images "${IMAGE_NAME}" | grep "${IMAGE_TAG}"
    echo ""
    
    # 检查镜像架构
    echo -e "${GREEN}验证镜像架构:${NC}"
    docker inspect "${FULL_IMAGE_NAME}" | grep -A 5 "Architecture"
    echo ""
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}构建完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}下一步操作:${NC}"
    echo -e "1. 测试镜像: ./test.sh"
    echo -e "2. 推送到 ECR: ./push-to-ecr.sh <ecr-repo-uri>"
else
    echo -e "${RED}✗ 镜像构建失败${NC}"
    exit 1
fi
