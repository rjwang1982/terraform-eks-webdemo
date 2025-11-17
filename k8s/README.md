# Kubernetes 资源配置文件

**作者：** RJ.Wang  
**邮箱：** wangrenjun@gmail.com  
**创建时间：** 2025-11-14  
**最后更新：** 2025-11-16

---

## ⚠️ 重要说明

**这些 YAML 文件仅用于以下场景**：

1. **备用部署方案** 🔄
   - 当 Terraform Kubernetes Provider 失败时
   - 由 `scripts/deploy.sh` 自动使用
   - 不需要手动干预

2. **开发和测试** 🧪
   - 快速测试单个资源配置
   - 调试 Kubernetes 资源问题
   - 验证配置正确性

3. **故障排查** 🔍
   - 分析资源配置
   - 对比 Terraform 生成的资源
   - 手动修复问题

### 标准部署方式

**推荐使用 Terraform 管理所有资源**：

```bash
cd terraform
terraform apply
```

或使用部署脚本（会自动选择最佳方式）：

```bash
./scripts/deploy.sh
```

### ❌ 不要直接使用

**不要直接使用** `kubectl apply -f k8s/` 进行生产部署，原因：

- ⚠️ 会绕过 Terraform 状态管理
- ⚠️ 导致资源管理不一致
- ⚠️ 无法通过 Terraform 追踪变更
- ⚠️ 可能与 Terraform 资源冲突

### 如果需要手动部署

如果确实需要手动部署（例如 Terraform 完全失败），请：

1. 先尝试修复 Terraform 配置
2. 如果无法修复，使用部署脚本的备用模式
3. 部署后参考 [资源迁移指南](../TERRAFORM_MIGRATION_GUIDE.md)

---

## 概述

本目录包含 EKS Info WebApp 的所有 Kubernetes 资源配置文件。

## 文件列表

### 基础资源
- `namespace.yaml` - 命名空间配置
- `serviceaccount.yaml` - ServiceAccount 配置（包含 IRSA 注解）
- `service.yaml` - ClusterIP Service 配置
- `ingress.yaml` - ALB Ingress 配置

### 存储资源（storage/ 子目录）
- `storage/storageclass-ebs.yaml` - EBS StorageClass（gp3）
- `storage/storageclass-efs.yaml` - EFS StorageClass
- `storage/pvc-ebs.yaml` - EBS PersistentVolumeClaim（ReadWriteOnce）
- `storage/pvc-efs.yaml` - EFS PersistentVolumeClaim（ReadWriteMany）

### 应用资源
- `deployment.yaml` - Deployment 配置
- `hpa.yaml` - HorizontalPodAutoscaler 配置

## 部署前准备

### 1. 替换占位符

在部署前，需要替换以下配置文件中的占位符：

#### serviceaccount.yaml
```yaml
eks.amazonaws.com/role-arn: arn:aws:iam::<ACCOUNT_ID>:role/eks-info-app-role
```
替换 `<ACCOUNT_ID>` 为实际的 AWS 账号 ID。

#### storage/storageclass-efs.yaml
```yaml
fileSystemId: fs-xxxxxxxxx
```
替换 `fs-xxxxxxxxx` 为实际的 EFS 文件系统 ID。

#### deployment.yaml
```yaml
image: <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/eks-info-app:latest
```
替换 `<ACCOUNT_ID>` 为实际的 AWS 账号 ID。

### 2. 确保前置条件

- EKS 集群已创建并配置
- AWS Load Balancer Controller 已安装
- EBS CSI Driver 已安装
- EFS CSI Driver 已安装
- Metrics Server 已安装（用于 HPA）
- EFS 文件系统已创建
- S3 存储桶已创建
- IAM Role 已创建并配置 IRSA 信任关系

## 部署顺序

按以下顺序部署资源：

### 1. 创建命名空间
```bash
kubectl apply -f namespace.yaml
```

### 2. 创建 ServiceAccount
```bash
kubectl apply -f serviceaccount.yaml
```

### 3. 创建存储资源
```bash
# 创建 StorageClass
kubectl apply -f storage/storageclass-ebs.yaml
kubectl apply -f storage/storageclass-efs.yaml

# 创建 PVC
kubectl apply -f storage/pvc-ebs.yaml
kubectl apply -f storage/pvc-efs.yaml

# 验证 PVC 状态
kubectl get pvc -n rj-webdemo
```

### 4. 创建 Service
```bash
kubectl apply -f service.yaml
```

### 5. 创建 Deployment
```bash
kubectl apply -f deployment.yaml

# 验证 Deployment 状态
kubectl get deployment -n rj-webdemo
kubectl get pods -n rj-webdemo
```

### 6. 创建 Ingress
```bash
kubectl apply -f ingress.yaml

# 获取 ALB 地址
kubectl get ingress -n rj-webdemo
```

### 7. 创建 HPA
```bash
kubectl apply -f hpa.yaml

# 验证 HPA 状态
kubectl get hpa -n rj-webdemo
```

## 一键部署

如果所有占位符已替换，可以使用以下命令一次性部署所有资源：

```bash
kubectl apply -f namespace.yaml
kubectl apply -f serviceaccount.yaml
kubectl apply -f storage/storageclass-ebs.yaml
kubectl apply -f storage/storageclass-efs.yaml
kubectl apply -f storage/pvc-ebs.yaml
kubectl apply -f storage/pvc-efs.yaml
kubectl apply -f service.yaml
kubectl apply -f deployment.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml
```

或者使用目录方式（递归应用所有 YAML 文件）：
```bash
kubectl apply -f k8s/ -R
```

## 验证部署

### 检查所有资源
```bash
kubectl get all -n rj-webdemo
```

### 检查 Pod 日志
```bash
kubectl logs -n rj-webdemo -l app=eks-info-app --tail=100
```

### 检查 PVC 绑定状态
```bash
kubectl get pvc -n rj-webdemo
```

### 检查 Ingress 状态
```bash
kubectl describe ingress eks-info-app-ingress -n rj-webdemo
```

### 检查 HPA 状态
```bash
kubectl get hpa -n rj-webdemo
kubectl describe hpa eks-info-app-hpa -n rj-webdemo
```

### 测试应用访问
```bash
# 获取 ALB 地址
ALB_URL=$(kubectl get ingress eks-info-app-ingress -n rj-webdemo -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Application URL: http://$ALB_URL"

# 测试健康检查
curl http://$ALB_URL/health

# 测试就绪检查
curl http://$ALB_URL/ready
```

## 更新部署

### 更新镜像
```bash
kubectl set image deployment/eks-info-app eks-info-app=<NEW_IMAGE> -n rj-webdemo
```

### 重启 Deployment
```bash
kubectl rollout restart deployment/eks-info-app -n rj-webdemo
```

### 查看滚动更新状态
```bash
kubectl rollout status deployment/eks-info-app -n rj-webdemo
```

### 回滚部署
```bash
kubectl rollout undo deployment/eks-info-app -n rj-webdemo
```

## 扩展配置

### 手动扩展 Pod
```bash
kubectl scale deployment eks-info-app --replicas=5 -n rj-webdemo
```

### 查看 HPA 自动扩展
```bash
# 实时监控 HPA
kubectl get hpa -n rj-webdemo --watch

# 查看 HPA 事件
kubectl describe hpa eks-info-app-hpa -n rj-webdemo
```

## 清理资源

### 删除所有资源
```bash
kubectl delete -f hpa.yaml
kubectl delete -f ingress.yaml
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml
kubectl delete -f storage/pvc-ebs.yaml
kubectl delete -f storage/pvc-efs.yaml
kubectl delete -f storage/storageclass-ebs.yaml
kubectl delete -f storage/storageclass-efs.yaml
kubectl delete -f serviceaccount.yaml
kubectl delete -f namespace.yaml
```

或者使用目录方式（递归删除所有 YAML 文件）：
```bash
kubectl delete -f k8s/ -R
```

## 故障排查

### Pod 无法启动
```bash
# 查看 Pod 详情
kubectl describe pod -n rj-webdemo -l app=eks-info-app

# 查看 Pod 日志
kubectl logs -n rj-webdemo -l app=eks-info-app --tail=100

# 查看 Pod 事件
kubectl get events -n rj-webdemo --sort-by='.lastTimestamp'
```

### PVC 无法绑定
```bash
# 查看 PVC 状态
kubectl describe pvc -n rj-webdemo

# 查看 StorageClass
kubectl get storageclass

# 查看 PV
kubectl get pv
```

### Ingress 无法创建 ALB
```bash
# 查看 Ingress 详情
kubectl describe ingress eks-info-app-ingress -n rj-webdemo

# 查看 ALB Controller 日志
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

### HPA 无法获取指标
```bash
# 检查 Metrics Server
kubectl get deployment metrics-server -n kube-system

# 查看 HPA 详情
kubectl describe hpa eks-info-app-hpa -n rj-webdemo

# 测试指标 API
kubectl top pods -n rj-webdemo
```

## 配置说明

### 资源限制
- CPU Request: 100m
- CPU Limit: 500m
- Memory Request: 128Mi
- Memory Limit: 512Mi

### HPA 配置
- 最小副本数: 3
- 最大副本数: 10
- CPU 阈值: 70%
- 内存阈值: 80%
- 扩容稳定窗口: 30 秒
- 缩容稳定窗口: 300 秒

### 存储配置
- EBS: 10Gi, gp3, ReadWriteOnce
- EFS: 20Gi, ReadWriteMany

### 健康检查
- Liveness Probe: /health, 30s 初始延迟
- Readiness Probe: /ready, 5s 初始延迟
- Startup Probe: /health, 60s 超时

## 注意事项

1. 确保 EKS 集群有足够的资源来运行应用
2. 确保 IAM Role 有正确的权限访问 S3、EC2、EFS 等服务
3. 确保 EFS 文件系统和 EKS 集群在同一个 VPC
4. 确保安全组允许 EFS 的 NFS 流量（端口 2049）
5. 确保 ALB Controller 有权限创建和管理 ALB
6. 建议在生产环境中使用 Helm Chart 管理这些资源
7. 定期备份 PVC 数据
8. 监控 HPA 的扩展行为，根据实际情况调整阈值
