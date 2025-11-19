# 部署检查清单

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-18

---

## 部署前检查

### 1. 镜像构建检查
- [ ] 确认目标架构（ARM64 for EKS Graviton）
- [ ] Dockerfile 中指定了正确的平台
- [ ] 使用 `docker buildx` 构建多架构镜像
- [ ] 镜像标签命名规范（版本号 + latest）

### 2. 镜像推送检查
- [ ] Docker Hub 登录状态正常
- [ ] 镜像推送成功（无网络错误）
- [ ] 验证镜像架构正确
- [ ] 镜像在 Docker Hub 上可访问

### 3. Kubernetes 配置检查
- [ ] kubectl 连接到正确的集群
- [ ] 命名空间存在
- [ ] 部署配置中的镜像名称正确
- [ ] imagePullPolicy 设置为 Always（推荐）

---

## 部署步骤

### Step 1: 构建镜像
```bash
cd simple-app

docker buildx build \
  --platform linux/arm64 \
  -t rjwang/rj-py-webdemo:$(date +%Y%m%d-%H%M%S) \
  -t rjwang/rj-py-webdemo:latest \
  --push \
  .
```

### Step 2: 验证镜像
```bash
# 检查本地镜像
docker images | grep rj-py-webdemo

# 检查远程镜像架构
docker buildx imagetools inspect rjwang/rj-py-webdemo:latest
```

### Step 3: 更新部署
```bash
# 方法 1: 更新镜像标签
kubectl set image deployment/rj-py-webdemo \
  rj-py-webdemo=rjwang/rj-py-webdemo:latest \
  -n rj-webdemo

# 方法 2: 重启部署
kubectl rollout restart deployment/rj-py-webdemo -n rj-webdemo
```

### Step 4: 监控部署
```bash
# 查看部署状态
kubectl rollout status deployment/rj-py-webdemo -n rj-webdemo

# 查看 Pod 状态
kubectl get pods -n rj-webdemo -w
```

### Step 5: 验证应用
```bash
# 检查 Pod 日志
kubectl logs -n rj-webdemo -l app=rj-py-webdemo --tail=20

# 获取访问地址
kubectl get ingress -n rj-webdemo

# 测试应用
curl http://<alb-hostname>
```

---

## 部署后验证

### 1. Pod 健康检查
- [ ] 所有 Pod 状态为 Running
- [ ] 没有 CrashLoopBackOff 错误
- [ ] 容器日志正常
- [ ] 健康检查探针通过

### 2. 服务可用性检查
- [ ] Service 正常工作
- [ ] Ingress 配置正确
- [ ] ALB 创建成功
- [ ] 应用可以通过 ALB 访问

### 3. 功能测试
- [ ] 首页可以访问
- [ ] API 端点响应正常
- [ ] 应用功能正常

---

## 回滚步骤

如果部署失败，按以下步骤回滚：

### 1. 查看部署历史
```bash
kubectl rollout history deployment/rj-py-webdemo -n rj-webdemo
```

### 2. 回滚到上一个版本
```bash
kubectl rollout undo deployment/rj-py-webdemo -n rj-webdemo
```

### 3. 回滚到指定版本
```bash
kubectl rollout undo deployment/rj-py-webdemo -n rj-webdemo --to-revision=<revision-number>
```

### 4. 验证回滚
```bash
kubectl rollout status deployment/rj-py-webdemo -n rj-webdemo
kubectl get pods -n rj-webdemo
```

---

## 常见错误及解决方案

### exec format error
**原因**: 镜像架构不匹配  
**解决**: 重新构建 ARM64 镜像并推送

### ImagePullBackOff
**原因**: 无法拉取镜像  
**解决**: 检查镜像名称、标签和网络连接

### CrashLoopBackOff
**原因**: 应用启动失败  
**解决**: 查看 Pod 日志，检查应用配置

---

## 紧急联系

- **作者**: RJ.Wang
- **邮箱**: wangrenjun@gmail.com

---

**最后更新**: 2025-11-18
