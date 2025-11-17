# Docker 镜像构建要求

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-17  
**用途**: 明确 Docker 镜像构建的架构要求

---

## 🎯 核心要求

### 必须使用 ARM64 架构

本项目的 Docker 镜像**必须**构建为 ARM64 (aarch64) 架构，原因如下：

1. **EKS 节点架构**: 使用 AWS Graviton 处理器（t4g.medium）
2. **性能优化**: ARM64 架构提供更好的性价比
3. **兼容性**: x86_64 镜像会导致 `exec format error` 错误

---

## ⚠️ 架构不匹配的后果

### 错误现象
如果使用 x86_64 架构镜像，Pod 会出现以下错误：

```
standard_init_linux.go:228: exec user process caused: exec format error
```

### 错误原因
- Docker 镜像架构与 EKS 节点架构不匹配
- x86_64 二进制文件无法在 ARM64 处理器上运行

---

## ✅ 正确的构建方法

### 方法 1: 使用项目提供的构建脚本（推荐）

```bash
cd simple-app
./build-and-push.sh
```

**脚本功能**：
- ✅ 自动检查 Docker 和 Docker Buildx
- ✅ 创建 ARM64 builder（如果不存在）
- ✅ 强制使用 `--platform linux/arm64` 参数
- ✅ 自动验证构建的镜像架构
- ✅ 提供推送到 Docker Hub 的选项

### 方法 2: 手动构建

```bash
# 1. 确保 Docker Buildx 可用
docker buildx version

# 2. 创建 ARM64 builder（首次需要）
docker buildx create --name arm64-builder --platform linux/arm64 --use

# 3. 构建 ARM64 镜像
docker buildx build \
    --platform linux/arm64 \
    --tag rjwang/rj-py-webdemo:1.0 \
    --tag rjwang/rj-py-webdemo:latest \
    --load \
    .

# 4. 验证镜像架构
docker inspect rjwang/rj-py-webdemo:1.0 | grep -i architecture
# 输出应该是: "Architecture": "arm64"
```

---

## 🔍 验证镜像架构

### 方法 1: 使用 docker inspect

```bash
docker inspect rjwang/rj-py-webdemo:1.0 | grep -i architecture
```

**期望输出**:
```json
"Architecture": "arm64"
```

### 方法 2: 使用 docker manifest

```bash
docker manifest inspect rjwang/rj-py-webdemo:1.0
```

**期望输出**:
```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
  "config": {
    "architecture": "arm64",
    "os": "linux"
  }
}
```

### 方法 3: 在容器内检查

```bash
docker run --rm rjwang/rj-py-webdemo:1.0 uname -m
```

**期望输出**:
```
aarch64
```

---

## 📋 Dockerfile 要求

### 必须包含的配置

```dockerfile
# ⚠️ 重要: 必须指定 ARM64 平台
FROM --platform=linux/arm64 python:3.11-slim

# 其他配置...
```

### 关键点说明

1. **FROM 指令**: 必须使用 `--platform=linux/arm64` 参数
2. **基础镜像**: 确保基础镜像支持 ARM64 架构
3. **依赖包**: 所有 Python 包必须有 ARM64 版本

---

## 🛠️ 工具要求

### Docker Buildx

**检查是否安装**:
```bash
docker buildx version
```

**安装方法**:
- Docker Desktop: 自动包含
- Linux: 
  ```bash
  # Ubuntu/Debian
  sudo apt-get install docker-buildx-plugin
  
  # 或手动安装
  mkdir -p ~/.docker/cli-plugins
  curl -L https://github.com/docker/buildx/releases/latest/download/buildx-linux-amd64 \
    -o ~/.docker/cli-plugins/docker-buildx
  chmod +x ~/.docker/cli-plugins/docker-buildx
  ```

### Docker 版本要求

- **最低版本**: Docker 19.03+
- **推荐版本**: Docker 20.10+

---

## 🚨 常见错误和解决方案

### 错误 1: 构建的镜像是 x86_64

**原因**: 未使用 `--platform` 参数或 Buildx

**解决方案**:
```bash
# 使用 Buildx 和 --platform 参数
docker buildx build --platform linux/arm64 ...
```

### 错误 2: Buildx 不可用

**错误信息**:
```
docker: 'buildx' is not a docker command.
```

**解决方案**:
```bash
# 安装 Docker Buildx
# 参考上面的安装方法
```

### 错误 3: 基础镜像不支持 ARM64

**错误信息**:
```
no match for platform in manifest
```

**解决方案**:
- 确认基础镜像支持 ARM64
- Python 官方镜像支持多架构
- 使用 `docker manifest inspect python:3.11-slim` 检查

### 错误 4: 依赖包没有 ARM64 版本

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement
```

**解决方案**:
- 大多数 Python 包支持 ARM64
- 检查 PyPI 包的平台支持
- 考虑使用替代包

---

## 📊 架构对比

| 特性 | x86_64 | ARM64 (Graviton) |
|------|--------|------------------|
| 指令集 | x86-64 | aarch64 |
| AWS 实例类型 | t3.medium | t4g.medium |
| 性价比 | 标准 | 提升 20% |
| 性能 | 标准 | 相当或更好 |
| 兼容性 | 广泛 | 主流软件支持 |
| 本项目要求 | ❌ 不支持 | ✅ 必须使用 |

---

## 🎯 部署流程中的架构检查

### 构建阶段

```bash
# 1. 构建镜像
./simple-app/build-and-push.sh

# 2. 自动验证架构
# 脚本会自动检查并确认是 ARM64
```

### 部署阶段

```bash
# 1. 推送到 ECR
aws ecr get-login-password | docker login ...
docker tag rjwang/rj-py-webdemo:1.0 <ecr-url>
docker push <ecr-url>

# 2. 部署到 EKS
kubectl apply -f k8s/

# 3. 验证 Pod 运行
kubectl get pods -n rj-webdemo
# Pod 应该正常运行，无 exec format error
```

---

## 📝 检查清单

部署前请确认：

- [ ] 使用 Docker Buildx 构建
- [ ] 指定 `--platform linux/arm64` 参数
- [ ] Dockerfile 包含 `--platform=linux/arm64`
- [ ] 验证镜像架构为 arm64
- [ ] 基础镜像支持 ARM64
- [ ] 所有依赖包有 ARM64 版本
- [ ] 在 ARM64 环境测试过镜像

---

## 🔗 相关文档

- [Dockerfile](Dockerfile) - 镜像定义文件
- [build-and-push.sh](build-and-push.sh) - 构建脚本
- [Docker Buildx 文档](https://docs.docker.com/buildx/working-with-buildx/)
- [AWS Graviton 文档](https://aws.amazon.com/ec2/graviton/)

---

## 💡 最佳实践

### 1. 始终验证架构

每次构建后都要验证：
```bash
docker inspect <image> | grep Architecture
```

### 2. 使用自动化脚本

使用项目提供的 `build-and-push.sh` 脚本，避免手动错误。

### 3. 多阶段构建

如果需要编译，使用多阶段构建：
```dockerfile
FROM --platform=linux/arm64 python:3.11 as builder
# 编译阶段

FROM --platform=linux/arm64 python:3.11-slim
# 运行阶段
```

### 4. 本地测试

如果在 ARM64 Mac 上开发，可以直接测试：
```bash
docker run --rm -p 80:80 rjwang/rj-py-webdemo:1.0
```

### 5. CI/CD 集成

在 CI/CD 流程中添加架构验证：
```bash
# 构建后验证
ARCH=$(docker inspect $IMAGE | grep -i architecture | awk '{print $2}' | tr -d '",')
if [ "$ARCH" != "arm64" ]; then
  echo "错误: 镜像架构不是 ARM64"
  exit 1
fi
```

---

## 🎉 总结

**核心要点**：
1. ✅ 必须使用 ARM64 架构
2. ✅ 使用 Docker Buildx 构建
3. ✅ 指定 `--platform linux/arm64`
4. ✅ 构建后验证架构
5. ✅ 使用项目提供的脚本

**记住这个公式**：
```
ARM64 镜像 = Docker Buildx + --platform linux/arm64 + 架构验证
```

---

**最后更新**: 2025-11-17  
**适用版本**: 所有版本
