# Docker 镜像构建指南

**作者：** RJ.Wang  
**邮箱：** wangrenjun@gmail.com  
**创建时间：** 2025-11-14

## 概述

本文档说明如何构建和测试 EKS Info App 的 ARM64 Docker 镜像。

## 前置要求

- Docker Desktop 或 Docker Engine
- Docker Buildx（用于多架构构建）
- 至少 2GB 可用磁盘空间

## 快速开始

### 1. 构建镜像

```bash
cd eks-info-app
./build-docker.sh
```

### 2. 测试镜像

```bash
./test-docker.sh
```

### 3. 推送到 ECR

```bash
./push-to-ecr.sh
```

## 常见问题

### 问题 1: Docker 镜像源访问失败

**错误信息:**
```
ERROR: failed to resolve reference "docker.io/library/python:3.11-slim": 
unexpected status from HEAD request to https://l10nt4hq.mirror.aliyuncs.com/...: 403 Forbidden
```

**原因:** 
Docker 配置了阿里云镜像加速器，但该镜像源可能不稳定或访问受限。

**解决方案 1: 临时禁用镜像加速器**

编辑 `~/.docker/daemon.json`，注释掉或删除 `registry-mirrors` 配置：

```json
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "insecure-registries": [
    "http://harbor.rjwang.site"
  ]
  // 临时注释掉镜像加速器
  // "registry-mirrors": [
  //   "https://l10nt4hq.mirror.aliyuncs.com"
  // ]
}
```

然后重启 Docker Desktop 或 Docker 服务：

```bash
# macOS
# 通过 Docker Desktop 菜单重启

# Linux
sudo systemctl restart docker
```

**解决方案 2: 使用其他镜像源**

替换为其他可用的镜像源：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

**解决方案 3: 直接使用 Docker Hub**

如果网络允许，直接使用 Docker Hub 官方源（移除所有镜像配置）。

### 问题 2: ARM64 架构不支持

**错误信息:**
```
WARNING: The requested image's platform (linux/arm64) does not match the detected host platform
```

**解决方案:**

这是正常的警告信息。如果你在 x86_64 机器上构建 ARM64 镜像，Docker 会使用 QEMU 模拟。

验证镜像架构：

```bash
docker inspect eks-info-app:arm64-latest | grep Architecture
```

应该显示：
```json
"Architecture": "arm64"
```

### 问题 3: 依赖包安装失败

**错误信息:**
```
ERROR: Could not find a version that satisfies the requirement <package>
```

**解决方案:**

检查 `requirements.txt` 中的包是否支持 ARM64 架构。所有当前使用的包都已验证支持 ARM64：

- Flask 3.0.0 ✓
- boto3 1.34.0 ✓
- kubernetes 28.1.0 ✓
- psutil 5.9.6 ✓
- requests 2.31.0 ✓
- gunicorn 21.2.0 ✓

## 手动构建步骤

如果自动脚本失败，可以手动执行以下步骤：

### 步骤 1: 检查 Docker Buildx

```bash
docker buildx version
```

如果未安装，参考 [Docker Buildx 文档](https://docs.docker.com/buildx/working-with-buildx/)。

### 步骤 2: 创建 Builder 实例（可选）

```bash
docker buildx create --name arm64-builder --use
docker buildx inspect --bootstrap
```

### 步骤 3: 构建镜像

```bash
cd eks-info-app

# 构建并加载到本地
docker buildx build \
  --platform linux/arm64 \
  --tag eks-info-app:arm64-latest \
  --load \
  .
```

### 步骤 4: 验证镜像

```bash
# 查看镜像
docker images | grep eks-info-app

# 检查架构
docker inspect eks-info-app:arm64-latest | grep -A 5 "Architecture"

# 检查镜像大小
docker images eks-info-app:arm64-latest --format "{{.Size}}"
```

### 步骤 5: 测试运行

```bash
# 创建测试目录
mkdir -p /tmp/eks-test/{ebs,efs}

# 运行容器
docker run -d \
  --name eks-info-app-test \
  --platform linux/arm64 \
  -p 5000:5000 \
  -v /tmp/eks-test/ebs:/data/ebs \
  -v /tmp/eks-test/efs:/data/efs \
  -e POD_NAME="test-pod" \
  -e POD_NAMESPACE="default" \
  -e NODE_NAME="test-node" \
  -e S3_BUCKET_NAME="test-bucket" \
  eks-info-app:arm64-latest

# 等待启动
sleep 10

# 检查日志
docker logs eks-info-app-test

# 测试健康检查
curl http://localhost:5000/health

# 测试首页
curl http://localhost:5000/

# 清理
docker stop eks-info-app-test
docker rm eks-info-app-test
```

## 镜像优化

当前镜像大小约为 200-300MB。如果需要进一步优化：

### 1. 使用 Alpine 基础镜像

```dockerfile
FROM --platform=linux/arm64 python:3.11-alpine
```

注意：Alpine 可能需要额外的编译工具。

### 2. 多阶段构建

```dockerfile
# 构建阶段
FROM --platform=linux/arm64 python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 运行阶段
FROM --platform=linux/arm64 python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["gunicorn", ...]
```

### 3. 清理不必要的文件

在 `.dockerignore` 中添加：

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
.pytest_cache
.venv
*.log
```

## 推送到 ECR

### 前置步骤

**注意**：ECR 仓库由 Terraform 自动创建，无需手动创建。

如果 ECR 仓库不存在，请先运行 Terraform：

```bash
cd terraform
terraform init
terraform apply
```

### 推送步骤

1. 获取 ECR 登录凭证：

```bash
aws --profile susermt ecr get-login-password \
  --region ap-southeast-1 | \
  docker login \
  --username AWS \
  --password-stdin <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com
```

### 推送镜像

```bash
# 标记镜像
docker tag eks-info-app:arm64-latest \
  <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/eks-info-app:latest

# 推送
docker push <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/eks-info-app:latest
```

或使用提供的脚本：

```bash
./push-to-ecr.sh
```

## 验证清单

构建完成后，验证以下项目：

- [ ] 镜像成功构建
- [ ] 镜像架构为 ARM64
- [ ] 容器可以成功启动
- [ ] 健康检查端点返回 200
- [ ] 所有 Python 依赖已安装
- [ ] 应用日志正常输出
- [ ] 数据目录可以挂载
- [ ] 环境变量正确传递

## 性能基准

在 ARM64 架构上的预期性能：

- 镜像大小: ~250MB
- 启动时间: ~5-10 秒
- 内存使用: ~100-150MB（空闲）
- CPU 使用: <5%（空闲）

## 下一步

镜像构建和测试完成后：

1. 推送镜像到 ECR
2. 更新 Kubernetes Deployment 配置
3. 部署到 EKS 集群
4. 验证应用功能

## 参考资料

- [Docker Buildx 文档](https://docs.docker.com/buildx/)
- [Docker 多架构构建](https://docs.docker.com/build/building/multi-platform/)
- [AWS ECR 用户指南](https://docs.aws.amazon.com/ecr/)
- [Python Docker 最佳实践](https://docs.docker.com/language/python/)
