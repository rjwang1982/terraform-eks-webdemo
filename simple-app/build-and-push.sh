#!/bin/bash
#
# Docker 镜像构建和推送脚本 - ARM64 架构
#
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-17
# 更新时间: 2025-11-17
#
# ⚠️ 重要提示:
# 1. 必须构建 ARM64 架构镜像
# 2. EKS 节点使用 t4g.medium (Graviton ARM64)
# 3. x86_64 镜像会导致 "exec format error"
# 4. 使用 Docker Buildx 进行跨平台构建
#
# 架构要求说明:
# - 目标平台: linux/arm64 (aarch64)
# - 基础镜像: python:3.11-slim (ARM64 版本)
# - 构建工具: Docker Buildx
# - 验证方法: docker inspect 检查 Architecture 字段

set -e

# 配置
IMAGE_NAME="rjwang/rj-py-webdemo"
VERSION="1.0"
PLATFORM="linux/arm64"  # ⚠️ 强制使用 ARM64 架构

echo "=========================================="
echo "🐳 Docker 镜像构建 - ARM64 架构"
echo "=========================================="
echo ""
echo "镜像名称: ${IMAGE_NAME}:${VERSION}"
echo "目标平台: ${PLATFORM}"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    exit 1
fi

# 检查 Docker Buildx
if ! docker buildx version &> /dev/null; then
    echo "❌ 错误: Docker Buildx 未安装"
    echo "请运行: docker buildx install"
    exit 1
fi

# 创建 builder（如果不存在）
if ! docker buildx ls | grep -q "arm64-builder"; then
    echo "📦 创建 ARM64 builder..."
    docker buildx create --name arm64-builder --platform linux/arm64 --use
else
    echo "✓ 使用现有 ARM64 builder"
    docker buildx use arm64-builder
fi

# 构建镜像
echo ""
echo "🔨 开始构建 ARM64 镜像..."
docker buildx build \
    --platform ${PLATFORM} \
    --tag ${IMAGE_NAME}:${VERSION} \
    --tag ${IMAGE_NAME}:latest \
    --load \
    .

echo ""
echo "✅ 镜像构建成功！"
echo ""

# 验证镜像架构
echo "🔍 验证镜像架构..."
ARCH=$(docker inspect ${IMAGE_NAME}:${VERSION} | grep -i architecture | head -1 | awk '{print $2}' | tr -d '",')
echo "镜像架构: ${ARCH}"

if [ "$ARCH" != "arm64" ]; then
    echo "❌ 错误: 镜像架构不是 ARM64！"
    echo ""
    echo "当前架构: ${ARCH}"
    echo "期望架构: arm64"
    echo ""
    echo "可能的原因:"
    echo "1. Docker Buildx 未正确配置"
    echo "2. --platform 参数未生效"
    echo "3. 基础镜像不支持 ARM64"
    echo ""
    echo "解决方案:"
    echo "1. 确保使用 Docker Buildx: docker buildx version"
    echo "2. 创建 ARM64 builder: docker buildx create --name arm64-builder --platform linux/arm64"
    echo "3. 使用正确的构建命令: docker buildx build --platform linux/arm64 ..."
    exit 1
fi

echo "✅ 架构验证通过 - ARM64 (aarch64)"
echo ""

# 推送到 Docker Hub
read -p "是否推送到 Docker Hub? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 推送镜像到 Docker Hub..."
    docker push ${IMAGE_NAME}:${VERSION}
    docker push ${IMAGE_NAME}:latest
    echo "✅ 推送完成！"
fi

echo ""
echo "=========================================="
echo "🎉 完成！"
echo "=========================================="
echo ""
echo "镜像信息:"
echo "  名称: ${IMAGE_NAME}:${VERSION}"
echo "  架构: ARM64 (aarch64)"
echo "  大小: $(docker images ${IMAGE_NAME}:${VERSION} --format '{{.Size}}')"
echo ""
echo "使用方法:"
echo "  docker run -p 80:80 ${IMAGE_NAME}:${VERSION}"
echo ""
