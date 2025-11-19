#!/bin/bash
#
# EKS Info WebApp - 推送镜像到 ECR 脚本
#
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-14
#
# 用途: 推送 Docker 镜像到 AWS ECR

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}EKS Info WebApp - 推送到 ECR${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查参数
if [ -z "$1" ]; then
    echo -e "${RED}错误: 缺少 ECR 仓库 URI${NC}"
    echo ""
    echo -e "${YELLOW}用法:${NC}"
    echo -e "  $0 <ecr-repo-uri> [image-tag]"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo -e "  $0 269490040603.dkr.ecr.ap-southeast-1.amazonaws.com/eks-info-app latest"
    echo ""
    exit 1
fi

# 设置变量
ECR_REPO_URI="$1"
IMAGE_TAG="${2:-latest}"
LOCAL_IMAGE="eks-info-app:${IMAGE_TAG}"
ECR_IMAGE="${ECR_REPO_URI}:${IMAGE_TAG}"
AWS_PROFILE="${AWS_PROFILE:-susermt}"

# 提取区域
REGION=$(echo "${ECR_REPO_URI}" | cut -d'.' -f4)
if [ -z "${REGION}" ]; then
    echo -e "${RED}错误: 无法从 ECR URI 提取区域${NC}"
    exit 1
fi

echo -e "${GREEN}本地镜像: ${LOCAL_IMAGE}${NC}"
echo -e "${GREEN}ECR 镜像: ${ECR_IMAGE}${NC}"
echo -e "${GREEN}AWS 区域: ${REGION}${NC}"
echo -e "${GREEN}AWS Profile: ${AWS_PROFILE}${NC}"
echo ""

# 检查本地镜像是否存在
if ! docker images | grep -q "eks-info-app.*${IMAGE_TAG}"; then
    echo -e "${RED}错误: 本地镜像 ${LOCAL_IMAGE} 不存在${NC}"
    echo -e "${YELLOW}请先运行 ./build.sh 构建镜像${NC}"
    exit 1
fi

# 登录到 ECR
echo -e "${YELLOW}登录到 ECR...${NC}"
aws --profile "${AWS_PROFILE}" ecr get-login-password --region "${REGION}" | \
    docker login --username AWS --password-stdin "${ECR_REPO_URI%/*}"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ ECR 登录失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ ECR 登录成功${NC}"
echo ""

# 标记镜像
echo -e "${YELLOW}标记镜像...${NC}"
docker tag "${LOCAL_IMAGE}" "${ECR_IMAGE}"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 镜像标记失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 镜像标记成功${NC}"
echo ""

# 推送镜像
echo -e "${YELLOW}推送镜像到 ECR...${NC}"
docker push "${ECR_IMAGE}"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 镜像推送失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 镜像推送成功${NC}"
echo ""

# 验证镜像架构
echo -e "${YELLOW}验证 ECR 镜像架构...${NC}"
aws --profile "${AWS_PROFILE}" ecr describe-images \
    --repository-name "$(basename ${ECR_REPO_URI})" \
    --image-ids imageTag="${IMAGE_TAG}" \
    --region "${REGION}" \
    --query 'imageDetails[0].imageManifestMediaType' \
    --output text

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}推送完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}ECR 镜像 URI:${NC}"
echo -e "  ${ECR_IMAGE}"
echo ""
echo -e "${YELLOW}在 Kubernetes 中使用:${NC}"
echo -e "  image: ${ECR_IMAGE}"
echo ""
