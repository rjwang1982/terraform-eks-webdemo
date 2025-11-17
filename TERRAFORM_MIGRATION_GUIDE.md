# Terraform 资源迁移指南

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-16  
**用途**: 将手动创建的 Kubernetes 资源迁移到 Terraform 管理

---

## 📋 概述

如果你使用了备用部署模式，部分 Kubernetes 资源可能不在 Terraform 状态管理中。本指南说明如何将这些资源迁移到 Terraform 管理。

## 🔍 检查当前状态

### 步骤 1: 检查 Terraform 状态

```bash
cd terraform

# 查看所有 Terraform 管理的资源
terraform state list

# 检查 Kubernetes 资源
terraform state list | grep -E "(kubernetes|helm)"
```

**预期结果**：

如果使用标准 Terraform 部署，应该看到：
```
kubernetes_namespace.app
kubernetes_service_account.eks_info_app
kubernetes_storage_class.ebs_gp3
kubernetes_storage_class.efs
kubernetes_persistent_volume_claim.ebs
kubernetes_persistent_volume_claim.efs
kubernetes_deployment.eks_info_app
kubernetes_service.eks_info_app
kubernetes_ingress_v1.eks_info_app
kubernetes_horizontal_pod_autoscaler_v2.eks_info_app
helm_release.aws_load_balancer_controller
helm_release.ebs_csi_driver
helm_release.efs_csi_driver
```

如果使用备用部署模式，可能只看到 Helm releases 或完全没有 Kubernetes 资源。

### 步骤 2: 检查实际 Kubernetes 资源

```bash
# 检查命名空间
kubectl get namespace rj-webdemo

# 检查应用资源
kubectl get all -n rj-webdemo

# 检查存储资源
kubectl get pvc,storageclass -n rj-webdemo

# 检查 Helm releases
helm list -A
```

---

## 🔄 迁移方案

### 方案 A: 清理并重新部署（推荐）

这是最简单和最安全的方法。

#### 步骤 1: 备份重要数据

```bash
# 备份 EBS 数据（如果有重要数据）
kubectl exec -n rj-webdemo deployment/eks-info-app -- tar czf /tmp/ebs-backup.tar.gz /data/ebs
kubectl cp rj-webdemo/<pod-name>:/tmp/ebs-backup.tar.gz ./ebs-backup.tar.gz

# 备份 EFS 数据（如果有重要数据）
kubectl exec -n rj-webdemo deployment/eks-info-app -- tar czf /tmp/efs-backup.tar.gz /data/efs
kubectl cp rj-webdemo/<pod-name>:/tmp/efs-backup.tar.gz ./efs-backup.tar.gz

# 备份 S3 数据（如果有重要数据）
aws s3 sync s3://your-bucket-name ./s3-backup/
```

#### 步骤 2: 清理手动创建的资源

```bash
# 删除应用命名空间（会删除所有相关资源）
kubectl delete namespace rj-webdemo

# 卸载手动安装的 Helm releases
helm uninstall aws-load-balancer-controller -n kube-system
helm uninstall aws-ebs-csi-driver -n kube-system
helm uninstall aws-efs-csi-driver -n kube-system

# 等待资源完全删除
kubectl get all -n rj-webdemo
# 应该显示 "No resources found"
```

#### 步骤 3: 清理 Terraform 状态（如果需要）

```bash
cd terraform

# 如果 Terraform 状态中有孤立的资源，移除它们
terraform state list | grep kubernetes | while read resource; do
  terraform state rm "$resource"
done

terraform state list | grep helm | while read resource; do
  terraform state rm "$resource"
done
```

#### 步骤 4: 重新部署

```bash
cd ..

# 使用部署脚本重新部署
./scripts/deploy.sh

# 或使用 Terraform 直接部署
cd terraform
terraform apply
```

#### 步骤 5: 恢复数据（如果需要）

```bash
# 等待 Pod 就绪
kubectl wait --for=condition=ready pod -l app=eks-info-app -n rj-webdemo --timeout=300s

# 恢复 EBS 数据
kubectl cp ./ebs-backup.tar.gz rj-webdemo/<pod-name>:/tmp/
kubectl exec -n rj-webdemo deployment/eks-info-app -- tar xzf /tmp/ebs-backup.tar.gz -C /

# 恢复 EFS 数据
kubectl cp ./efs-backup.tar.gz rj-webdemo/<pod-name>:/tmp/
kubectl exec -n rj-webdemo deployment/eks-info-app -- tar xzf /tmp/efs-backup.tar.gz -C /

# 恢复 S3 数据
aws s3 sync ./s3-backup/ s3://your-bucket-name/
```

#### 步骤 6: 验证

```bash
# 验证 Terraform 状态
cd terraform
terraform state list | grep -E "(kubernetes|helm)"

# 验证应用运行
kubectl get pods -n rj-webdemo
kubectl get ingress -n rj-webdemo

# 测试应用访问
ALB_URL=$(kubectl get ingress eks-info-app-ingress -n rj-webdemo -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$ALB_URL/health
```

---

### 方案 B: 导入现有资源到 Terraform（高级）

这个方法更复杂，但可以保留现有资源而不中断服务。

**注意**：这需要对 Terraform 和 Kubernetes 有深入了解。

#### 步骤 1: 准备导入

```bash
cd terraform

# 确保 Terraform 配置是最新的
terraform init
terraform validate
```

#### 步骤 2: 导入 Namespace

```bash
terraform import kubernetes_namespace.app rj-webdemo
```

#### 步骤 3: 导入其他 Kubernetes 资源

```bash
# ServiceAccount
terraform import kubernetes_service_account.eks_info_app rj-webdemo/eks-info-app-sa

# StorageClass（全局资源，不需要命名空间）
terraform import kubernetes_storage_class.ebs_gp3 ebs-gp3
terraform import kubernetes_storage_class.efs efs-sc

# PVC
terraform import kubernetes_persistent_volume_claim.ebs rj-webdemo/eks-info-app-ebs-pvc
terraform import kubernetes_persistent_volume_claim.efs rj-webdemo/eks-info-app-efs-pvc

# Deployment
terraform import kubernetes_deployment.eks_info_app rj-webdemo/eks-info-app

# Service
terraform import kubernetes_service.eks_info_app rj-webdemo/eks-info-app-service

# Ingress
terraform import kubernetes_ingress_v1.eks_info_app rj-webdemo/eks-info-app-ingress

# HPA
terraform import kubernetes_horizontal_pod_autoscaler_v2.eks_info_app rj-webdemo/eks-info-app-hpa
```

#### 步骤 4: 导入 Helm Releases

```bash
# AWS Load Balancer Controller
terraform import helm_release.aws_load_balancer_controller kube-system/aws-load-balancer-controller

# EBS CSI Driver
terraform import helm_release.ebs_csi_driver kube-system/aws-ebs-csi-driver

# EFS CSI Driver
terraform import helm_release.efs_csi_driver kube-system/aws-efs-csi-driver
```

#### 步骤 5: 验证导入

```bash
# 运行 plan 检查差异
terraform plan

# 如果有差异，可能需要调整 Terraform 配置以匹配实际资源
# 或者使用 terraform apply 更新资源以匹配配置
```

#### 步骤 6: 应用配置（如果需要）

```bash
# 如果 plan 显示需要更新，应用变更
terraform apply
```

---

## 🔍 故障排查

### 问题 1: 导入失败

**错误信息**：
```
Error: resource already managed by Terraform
```

**解决方案**：
资源已经在 Terraform 状态中，无需导入。

### 问题 2: 资源 ID 不正确

**错误信息**：
```
Error: Cannot import non-existent remote object
```

**解决方案**：
检查资源 ID 格式是否正确。Kubernetes 资源通常使用 `namespace/name` 格式。

```bash
# 检查实际资源名称
kubectl get <resource-type> -n <namespace>
```

### 问题 3: 配置不匹配

**错误信息**：
```
Plan: 0 to add, 5 to change, 0 to destroy
```

**解决方案**：
导入后，Terraform 配置可能与实际资源有差异。你需要：

1. 更新 Terraform 配置以匹配实际资源
2. 或者应用 Terraform 配置更新实际资源

### 问题 4: Helm Release 导入失败

**错误信息**：
```
Error: release not found
```

**解决方案**：
检查 Helm release 名称和命名空间：

```bash
helm list -A
```

---

## 📝 最佳实践

### 1. 始终使用 Terraform

从一开始就使用 Terraform 管理所有资源，避免手动创建。

### 2. 定期检查状态

定期运行 `terraform plan` 检查配置漂移。

### 3. 使用版本控制

将 Terraform 配置提交到 Git，追踪所有变更。

### 4. 文档化变更

记录所有手动操作和导入过程。

### 5. 测试迁移过程

在开发环境中先测试迁移过程，再应用到生产环境。

---

## 🎯 预防措施

### 避免使用备用部署模式

1. **修复 Terraform 配置**
   - 确保 Kubernetes Provider 配置正确
   - 检查 kubeconfig 文件
   - 验证 AWS 凭证

2. **使用正确的部署方式**
   ```bash
   # 始终使用部署脚本或 Terraform
   ./scripts/deploy.sh
   
   # 或
   cd terraform
   terraform apply
   ```

3. **不要直接使用 kubectl apply**
   - 避免使用 `kubectl apply -f k8s/`
   - 让 Terraform 管理所有资源

---

## 📞 获取帮助

如果遇到问题：

1. 查看 [故障排查指南](TROUBLESHOOTING.md)
2. 查看 [Terraform 合规性报告](TERRAFORM_COMPLIANCE_REPORT_V2.md)
3. 联系项目维护者：
   - **作者**: RJ.Wang
   - **邮箱**: wangrenjun@gmail.com

---

## 📚 参考资料

- [Terraform Import 文档](https://www.terraform.io/docs/cli/import/index.html)
- [Terraform Kubernetes Provider](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs)
- [Terraform Helm Provider](https://registry.terraform.io/providers/hashicorp/helm/latest/docs)
- [项目 Terraform 规范](.kiro/steering/terraform-infrastructure.md)

---

**文档版本**: 1.0  
**最后更新**: 2025-11-16
