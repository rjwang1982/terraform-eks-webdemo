#!/bin/bash
#
# Docker 镜像架构检查脚本
#
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-17
#
# 用途: 在部署前检查 Docker 镜像是否为 ARM64 架构

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 默认镜像名称
IMAGE_NAME="${1:-rjwang/rj-py-webdemo:1.0}"

echo "=========================================="
echo "🔍 Docker 镜像架构检查"
echo "=========================================="
echo ""
echo "检查镜像: ${IMAGE_NAME}"
echo ""

# 检查镜像是否存在
if ! docker image inspect "${IMAGE_NAME}" &> /dev/null; then
    echo -e "${RED}❌ 错误: 镜像不存在${NC}"
    echo ""
    echo "请先构建镜像:"
    echo "  cd simple-app"
    echo "  ./build-and-push.sh"
    exit 1
fi

# 获取镜像架构
ARCH=$(docker inspect "${IMAGE_NAME}" | grep -i '"Architecture"' | head -1 | awk '{print $2}' | tr -d '",')

echo "检测到的架构: ${ARCH}"
echo ""

# 验证架构
if [ "$ARCH" = "arm64" ]; then
    echo -e "${GREEN}✅ 架构验证通过${NC}"
    echo ""
    echo "镜像信息:"
    echo "  名称: ${IMAGE_NAME}"
    echo "  架构: ARM64 (aarch64)"
    echo "  状态: ✅ 可以部署到 EKS Graviton 节点"
    echo ""
    
    # 显示镜像详细信息
    echo "详细信息:"
    docker inspect "${IMAGE_NAME}" | grep -E '"(Architecture|Os|Size)"' | head -3
    echo ""
    
    # 显示镜像大小
    SIZE=$(docker images "${IMAGE_NAME}" --format '{{.Size}}')
    echo "镜像大小: ${SIZE}"
    echo ""
    
    echo -e "${GREEN}🎉 镜像可以安全部署！${NC}"
    exit 0
else
    echo -e "${RED}❌ 架构验证失败${NC}"
    echo ""
    echo "当前架构: ${ARCH}"
    echo "期望架构: arm64"
    echo ""
    echo -e "${YELLOW}⚠️  警告: 此镜像无法在 EKS Graviton 节点上运行！${NC}"
    echo ""
    echo "错误原因:"
    echo "  • EKS 节点使用 AWS Graviton (ARM64) 处理器"
    echo "  • ${ARCH} 架构镜像会导致 'exec format error'"
    echo ""
    echo "解决方案:"
    echo "  1. 使用 Docker Buildx 重新构建:"
    echo "     cd simple-app"
    echo "     ./build-and-push.sh"
    echo ""
    echo "  2. 或手动构建 ARM64 镜像:"
    echo "     docker buildx build --platform linux/arm64 -t ${IMAGE_NAME} ."
    echo ""
    echo "  3. 验证架构:"
    echo "     docker inspect ${IMAGE_NAME} | grep Architecture"
    echo ""
    exit 1
fi
