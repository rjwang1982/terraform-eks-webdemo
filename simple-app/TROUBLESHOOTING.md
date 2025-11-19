# 故障排查指南

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-18  
**用途**: 记录常见问题和解决方案

---

## 问题 1: exec format error - 镜像架构不匹配

### 症状
```bash
kubectl logs <pod-name>
# 输出: exec /usr/bin/python3: exec format error
```

Pod 状态显示 `CrashLoopBackOff`。

### 原因
Docker 镜像架构与 EKS 节点架构不匹配：
- EKS 使用 ARM64 架构（Graviton 节点）
- 推送的镜像是 AMD64 架构

### 解决方案

#### 1. 构建正确架构的镜像
```bash
# 使用 buildx 构建 ARM64 镜像
docker buildx build \
  --platform linux/arm64 \
  -t rjwang/rj-py-webdemo:1.0 \
  -t rjwang/rj-py-webdemo:latest \
  --push \
  simple-app/
```

#### 2. 验证镜像架构
```bash
# 检查本地镜像
docker inspect rjwang/rj-py-webdemo:1.0 | grep Architecture

# 检查 Docker Hub 上的镜像
docker buildx imagetools inspect rjwang/rj-py-webdemo:latest
```

#### 3. 更新 Kubernetes 部署
```bash
# 方法 1: 更新镜像标签
kubectl set image deployment/rj-py-webdemo \
  rj-py-webdemo=rjwang/rj-py-webdemo:latest \
  -n rj-webdemo

# 方法 2: 重启部署（如果使用相同标签）
kubectl rollout restart deployment/rj-py-webdemo -n rj-webdemo
```

#### 4. 验证部署
```bash
# 检查 Pod 状态
kubectl get pods -n rj-webdemo

# 查看 Pod 日志
kubectl logs -n rj-webdemo <pod-name>

# 检查部署详情
kubectl describe deployment rj-py-webdemo -n rj-webdemo
```

### 预防措施

1. **始终指定平台**：在 Dockerfile 中明确指定平台
   ```dockerfile
   FROM --platform=linux/arm64 python:3.11-slim
   ```

2. **使用 buildx 构建**：确保构建正确架构
   ```bash
   docker buildx build --platform linux/arm64 ...
   ```

3. **验证后再部署**：推送镜像后验证架构
   ```bash
   docker buildx imagetools inspect <image>
   ```

4. **使用 imagePullPolicy: Always**：确保拉取最新镜像
   ```yaml
   spec:
     containers:
     - name: app
       image: rjwang/rj-py-webdemo:latest
       imagePullPolicy: Always
   ```

---

## 问题 2: 镜像推送失败

### 症状
```bash
docker push rjwang/rj-py-webdemo:1.0
# 输出: write tcp: broken pipe 或 EOF
```

### 原因
- 网络连接不稳定
- Docker Hub 连接超时
- 代理配置问题

### 解决方案

#### 1. 重试推送
```bash
# 直接重试
docker push rjwang/rj-py-webdemo:1.0

# 或使用 buildx 直接构建并推送
docker buildx build --platform linux/arm64 --push -t rjwang/rj-py-webdemo:1.0 .
```

#### 2. 检查 Docker 登录状态
```bash
# 重新登录
docker login

# 验证登录
docker info | grep Username
```

#### 3. 检查网络连接
```bash
# 测试 Docker Hub 连接
curl -I https://hub.docker.com

# 检查代理设置
env | grep -i proxy
```

---

## 问题 3: Pod 无法拉取镜像

### 症状
```bash
kubectl describe pod <pod-name>
# Events 显示: Failed to pull image "rjwang/rj-py-webdemo:1.0"
```

### 原因
- 镜像不存在或标签错误
- Docker Hub 访问受限
- imagePullPolicy 设置不当

### 解决方案

#### 1. 验证镜像存在
```bash
# 在本地测试拉取
docker pull rjwang/rj-py-webdemo:1.0

# 检查 Docker Hub
# 访问: https://hub.docker.com/r/rjwang/rj-py-webdemo/tags
```

#### 2. 更新 imagePullPolicy
```bash
kubectl patch deployment rj-py-webdemo -n rj-webdemo \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"rj-py-webdemo","imagePullPolicy":"Always"}]}}}}'
```

#### 3. 强制重新拉取
```bash
# 删除旧 Pod
kubectl delete pods -n rj-webdemo -l app=rj-py-webdemo

# 或重启部署
kubectl rollout restart deployment/rj-py-webdemo -n rj-webdemo
```

---

## 快速诊断命令

### 检查 Pod 状态
```bash
# 查看所有 Pod
kubectl get pods -n rj-webdemo

# 查看 Pod 详情
kubectl describe pod <pod-name> -n rj-webdemo

# 查看 Pod 日志
kubectl logs <pod-name> -n rj-webdemo --tail=50

# 实时查看日志
kubectl logs -f <pod-name> -n rj-webdemo
```

### 检查部署状态
```bash
# 查看部署
kubectl get deployment -n rj-webdemo

# 查看部署详情
kubectl describe deployment rj-py-webdemo -n rj-webdemo

# 查看部署历史
kubectl rollout history deployment/rj-py-webdemo -n rj-webdemo

# 查看部署状态
kubectl rollout status deployment/rj-py-webdemo -n rj-webdemo
```

### 检查镜像信息
```bash
# 查看部署使用的镜像
kubectl get deployment rj-py-webdemo -n rj-webdemo -o jsonpath='{.spec.template.spec.containers[0].image}'

# 查看 Pod 使用的镜像
kubectl get pod <pod-name> -n rj-webdemo -o jsonpath='{.spec.containers[0].image}'
```

### 检查节点架构
```bash
# 查看节点信息
kubectl get nodes -o wide

# 查看节点架构
kubectl get nodes -o jsonpath='{.items[*].status.nodeInfo.architecture}'
```

---

## 完整部署流程

### 1. 构建并推送镜像
```bash
# 进入应用目录
cd simple-app

# 构建 ARM64 镜像并推送
docker buildx build \
  --platform linux/arm64 \
  -t rjwang/rj-py-webdemo:1.0 \
  -t rjwang/rj-py-webdemo:latest \
  --push \
  .

# 验证镜像
docker buildx imagetools inspect rjwang/rj-py-webdemo:latest
```

### 2. 部署到 EKS
```bash
# 更新部署镜像
kubectl set image deployment/rj-py-webdemo \
  rj-py-webdemo=rjwang/rj-py-webdemo:latest \
  -n rj-webdemo

# 或重启部署
kubectl rollout restart deployment/rj-py-webdemo -n rj-webdemo
```

### 3. 验证部署
```bash
# 等待部署完成
kubectl rollout status deployment/rj-py-webdemo -n rj-webdemo

# 检查 Pod 状态
kubectl get pods -n rj-webdemo

# 查看应用日志
kubectl logs -n rj-webdemo -l app=rj-py-webdemo --tail=20

# 测试应用
kubectl get ingress -n rj-webdemo
curl http://<alb-hostname>
```

---

## 常用命令速查

```bash
# 构建镜像
docker buildx build --platform linux/arm64 -t rjwang/rj-py-webdemo:latest --push .

# 更新部署
kubectl set image deployment/rj-py-webdemo rj-py-webdemo=rjwang/rj-py-webdemo:latest -n rj-webdemo

# 重启部署
kubectl rollout restart deployment/rj-py-webdemo -n rj-webdemo

# 查看状态
kubectl get pods -n rj-webdemo
kubectl logs -n rj-webdemo <pod-name>

# 删除失败的 Pod
kubectl delete pod <pod-name> -n rj-webdemo

# 强制重新创建所有 Pod
kubectl delete pods -n rj-webdemo -l app=rj-py-webdemo
```

---

## 联系信息

如有问题，请联系：
- **作者**: RJ.Wang
- **邮箱**: wangrenjun@gmail.com

---

**最后更新**: 2025-11-18
