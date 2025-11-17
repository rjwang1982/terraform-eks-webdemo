# ARM64 架构部署指南

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-17  
**用途**: 确保所有 Docker 镜像使用正确的 ARM64 架构

---

## 🎯 为什么必须使用 ARM64？

### EKS 节点配置
本项目的 EKS 集群使用 **AWS Graviton 处理器**：
- 实例类型: `t4g.medium`
- 架构: ARM64 (aarch64)
- 优势: 性价比提升 20%，性能相当或更好

### 架构不匹配的后果
如果使用 x86_64 镜像，Pod 会立即失败：
```
standard_init_linux.go:228: exec user process caused: exec format error
```

---

## ✅ 正确的构建流程

### 步骤 1: 构建 ARM64 镜像

```bash
# 进入应用目录
cd simple-app

# 使用构建脚本（推荐）
./build-and-push.sh

# 脚本会自动：
# 1. 检查 Docker Buildx
# 2. 创建 ARM64 builder
# 3. 构建 ARM64 镜像
# 4. 验证镜像架构
# 5. 提示是否推送到 Docker Hub
```

### 步骤 2: 验证镜像架构

```bash
# 使用检查脚本
cd ..
./scripts/check-image-arch.sh rjwang/rj-py-webdemo:1.0

# 或手动检查
docker inspect rjwang/rj-py-webdemo:1.0 | grep -i architecture
# 期望输出: "Architecture": "arm64"
```

### 步骤 3: 部署到 EKS

```bash
# 部署脚本会自动使用正确的镜像
./scripts/deploy.sh
```

---

## 📋 相关文件说明

### 1. Dockerfile
**位置**: `simple-app/Dockerfile`

**关键配置**:
```dockerfile
# ⚠️ 必须指定 ARM64 平台
FROM --platform=linux/arm64 python:3.11-slim
```

### 2. 构建脚本
**位置**: `simple-app/build-and-push.sh`

**关键参数**:
```bash
PLATFORM="linux/arm64"  # 强制使用 ARM64

docker buildx build \
    --platform ${PLATFORM} \
    --tag ${IMAGE_NAME}:${VERSION} \
    --load \
    .
```

### 3. 架构检查脚本
**位置**: `scripts/check-image-arch.sh`

**用途**: 部署前验证镜像架构

**使用方法**:
```bash
./scripts/check-image-arch.sh [镜像名称]
```

### 4. Terraform 配置
**位置**: `terraform/main.tf`

**节点组配置**:
```hcl
resource "aws_eks_node_group" "main" {
  instance_types = ["t4g.medium"]  # Graviton ARM64
  ami_type       = "AL2_ARM_64"    # ARM64 AMI
}
```

---

## 🔍 验证清单

部署前请确认以下所有项：

### Docker 镜像
- [ ] 使用 Docker Buildx 构建
- [ ] 指定 `--platform linux/arm64` 参数
- [ ] Dockerfile 包含 `FROM --platform=linux/arm64`
- [ ] 运行 `docker inspect` 确认架构为 arm64
- [ ] 镜像大小合理（约 150-200MB）

### EKS 配置
- [ ] 节点组使用 t4g.* 实例类型
- [ ] AMI 类型为 AL2_ARM_64
- [ ] 安全组允许必要的流量
- [ ] IAM 角色配置正确

### 部署验证
- [ ] Pod 成功启动（无 exec format error）
- [ ] 容器内运行 `uname -m` 输出 aarch64
- [ ] 应用功能正常
- [ ] 性能符合预期

---

## 🛠️ 工具要求

### Docker Buildx
**检查**:
```bash
docker buildx version
```

**安装**（如果需要）:
```bash
# Docker Desktop 自动包含

# Linux 手动安装
mkdir -p ~/.docker/cli-plugins
curl -L https://github.com/docker/buildx/releases/latest/download/buildx-linux-amd64 \
  -o ~/.docker/cli-plugins/docker-buildx
chmod +x ~/.docker/cli-plugins/docker-buildx
```

### Docker 版本
- 最低: Docker 19.03+
- 推荐: Docker 20.10+

---

## 🚨 常见问题

### Q1: 为什么不能用 docker build？

**A**: 传统的 `docker build` 命令会构建当前主机架构的镜像。如果你在 x86_64 Mac/Linux 上构建，会得到 x86_64 镜像。必须使用 `docker buildx build --platform linux/arm64` 进行跨平台构建。

### Q2: 我在 ARM64 Mac 上，还需要指定 --platform 吗？

**A**: 是的！虽然你的 Mac 是 ARM64，但为了确保一致性和避免意外，仍然建议明确指定 `--platform linux/arm64`。

### Q3: 如何在 x86_64 机器上测试 ARM64 镜像？

**A**: 
```bash
# Docker Desktop 支持 QEMU 模拟
docker run --rm rjwang/rj-py-webdemo:1.0 uname -m
# 输出: aarch64

# 注意: 模拟运行会比较慢
```

### Q4: 构建时间为什么比较长？

**A**: 跨平台构建需要使用 QEMU 模拟，会比原生构建慢。这是正常现象。

### Q5: 能否同时支持 x86_64 和 ARM64？

**A**: 可以构建多架构镜像：
```bash
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag rjwang/rj-py-webdemo:1.0 \
    --push \
    .
```

但本项目只需要 ARM64，因为 EKS 节点是 Graviton。

---

## 📊 性能对比

| 指标 | x86_64 (t3.medium) | ARM64 (t4g.medium) |
|------|-------------------|-------------------|
| vCPU | 2 | 2 |
| 内存 | 4 GB | 4 GB |
| 价格 | $0.0416/小时 | $0.0336/小时 |
| 性价比 | 基准 | 提升 20% |
| 性能 | 基准 | 相当或更好 |
| 本项目支持 | ❌ | ✅ |

---

## 🎯 快速参考

### 构建命令
```bash
# 完整流程
cd simple-app && ./build-and-push.sh

# 手动构建
docker buildx build --platform linux/arm64 -t rjwang/rj-py-webdemo:1.0 --load .
```

### 验证命令
```bash
# 检查架构
docker inspect rjwang/rj-py-webdemo:1.0 | grep Architecture

# 使用脚本
./scripts/check-image-arch.sh rjwang/rj-py-webdemo:1.0

# 容器内检查
docker run --rm rjwang/rj-py-webdemo:1.0 uname -m
```

### 部署命令
```bash
# 一键部署
./scripts/deploy.sh

# 清理资源
./scripts/force-clean.sh
```

---

## 📚 相关文档

- [BUILD_REQUIREMENTS.md](simple-app/BUILD_REQUIREMENTS.md) - 详细的构建要求
- [Dockerfile](simple-app/Dockerfile) - 镜像定义
- [build-and-push.sh](simple-app/build-and-push.sh) - 构建脚本
- [check-image-arch.sh](scripts/check-image-arch.sh) - 架构检查脚本
- [README.md](README.md) - 项目总览

---

## 💡 最佳实践

### 1. 始终使用构建脚本
```bash
cd simple-app && ./build-and-push.sh
```
脚本包含所有必要的检查和验证。

### 2. 部署前验证
```bash
./scripts/check-image-arch.sh
```
确保镜像架构正确。

### 3. 记录镜像信息
```bash
docker images rjwang/rj-py-webdemo:1.0
docker inspect rjwang/rj-py-webdemo:1.0
```
保存镜像的详细信息以便追溯。

### 4. 测试镜像
```bash
# 本地测试
docker run --rm -p 80:80 rjwang/rj-py-webdemo:1.0

# 访问测试
curl http://localhost/
```

### 5. 版本管理
```bash
# 使用语义化版本
docker tag rjwang/rj-py-webdemo:1.0 rjwang/rj-py-webdemo:v1.0.0
docker tag rjwang/rj-py-webdemo:1.0 rjwang/rj-py-webdemo:latest
```

---

## 🎉 总结

**核心要点**：
1. ✅ EKS 使用 Graviton (ARM64) 节点
2. ✅ 必须构建 ARM64 架构镜像
3. ✅ 使用 Docker Buildx + --platform linux/arm64
4. ✅ 构建后验证架构
5. ✅ 使用项目提供的脚本和工具

**记住**：
```
正确的架构 = 成功的部署
错误的架构 = exec format error
```

---

**最后更新**: 2025-11-17  
**适用版本**: 所有版本  
**重要性**: ⭐⭐⭐⭐⭐ 必读
