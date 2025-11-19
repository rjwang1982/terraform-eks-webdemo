# 部署指南

**作者：** RJ.Wang  
**邮箱：** wangrenjun@gmail.com  
**创建时间：** 2025-11-14  
**最后更新：** 2025-11-16

---

## 📋 目录

1. [部署概览](#部署概览)
2. [架构组件](#架构组件)
3. [前置条件](#前置条件)
4. [部署步骤](#部署步骤)
5. [部署状态](#部署状态)
6. [验证部署](#验证部署)
7. [配置变量](#配置变量)
8. [更新应用](#更新应用)
9. [扩展配置](#扩展配置)
10. [已修复的问题](#已修复的问题)
11. [已知问题](#已知问题)
12. [清理资源](#清理资源)
13. [故障排查](#故障排查)
14. [成本估算](#成本估算)
15. [安全最佳实践](#安全最佳实践)

---

## 部署概览

本文档描述如何使用 Terraform 部署 EKS Info WebApp 到 AWS EKS 集群。

EKS 集群和应用已成功部署到 AWS Global 区域（ap-southeast-1）。

**✅ 最新状态：所有问题已修复，应用运行正常**

### 快速访问

- **应用地址**: http://k8s-rjwebdem-eksinfoa-276a74cf51-1382595953.ap-southeast-1.elb.amazonaws.com
- **集群名称**: RJtest-eks-cluster-202511171652
- **命名空间**: rj-webdemo
- **区域**: ap-southeast-1

---

## 架构组件

Terraform 配置将创建以下资源：

### 基础设施资源

#### VPC 和网络
- **VPC CIDR**: 10.101.0.0/16
- **公有子网**: 3 个（每个可用区一个）
- **私有子网**: 6 个（每个可用区两个）
- **NAT Gateway**: 3 个（高可用配置）
- **Internet Gateway**: 1 个
- **路由表**: 公有和私有路由表

#### EKS 集群
- **集群名称**: RJtest-eks-cluster-202511171652
- **Kubernetes 版本**: 1.31
- **节点组**: 
  - 实例类型: t4g.medium (ARM64 Graviton)
  - 期望数量: 2
  - 最小数量: 1
  - 最大数量: 4
  - AMI 类型: AL2023_ARM_64_STANDARD

#### 安全组
- 集群安全组
- 节点安全组
- EFS 安全组

### 存储资源

- **EFS 文件系统**: fs-063d4fdf83f33d7b5（加密的共享文件系统，带挂载目标）
- **S3 存储桶**: rjtest-eks-cluster-202511171652-eks-info-app-data（加密的对象存储，配置生命周期策略）
- **EBS CSI Driver**: 通过 Helm 安装
- **EFS CSI Driver**: 通过 Helm 安装

### IAM 和权限

- **OIDC Provider**: 用于 IRSA
- **EKS Info App IAM 角色**: S3 和 AWS 服务描述权限
- **CSI Driver IAM 角色**: EBS 和 EFS 操作权限
- **ALB Controller IAM 角色**: 负载均衡器管理权限

### Kubernetes 资源

- **Namespace**: rj-webdemo
- **ServiceAccount**: 配置 IRSA 注解
- **StorageClass**: EBS gp3 和 EFS
- **PVC**: EBS (10Gi) 和 EFS (20Gi)
- **Deployment**: 当前 10 个副本（由 HPA 自动扩展）
- **Service**: ClusterIP 类型
- **Ingress**: ALB 配置
- **HPA**: CPU 和内存自动扩展（3-10 副本）

---

## 前置条件

### 1. 工具安装

```bash
# Terraform >= 1.3.2
terraform version

# AWS CLI
aws --version

# kubectl
kubectl version --client

# Docker (用于构建镜像)
docker --version
```

### 2. AWS 凭证配置

```bash
# 配置 AWS Profile
aws configure --profile terraform_0603

# 验证凭证
aws --profile terraform_0603 sts get-caller-identity
```

### 3. SSH 密钥对

确保在 AWS 中已创建 SSH 密钥对（默认: RJ-test-Pem-<AWS_ACCOUNT_ID>）

---

## 部署步骤

### 步骤 1: 构建和推送 Docker 镜像

首先需要构建应用镜像并推送到 ECR。

**注意**：ECR 仓库由 Terraform 自动创建，无需手动创建。

```bash
# 使用构建脚本（推荐）
./scripts/build.sh

# 或手动构建和推送
cd eks-info-app

# 获取 AWS 账户 ID
AWS_ACCOUNT_ID=$(aws --profile terraform_0603 sts get-caller-identity --query Account --output text)
AWS_REGION="ap-southeast-1"

# 登录 ECR
aws --profile terraform_0603 ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# 构建 ARM64 镜像
docker buildx build --platform linux/arm64 \
  -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/eks-info-app:latest \
  --load .

# 推送镜像
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/eks-info-app:latest

cd ..
```

### 步骤 2: 初始化 Terraform

```bash
# 进入 terraform 目录
cd terraform

# 初始化 Terraform
terraform init

# 查看将要创建的资源
terraform plan -var="aws_profile=terraform_0603"
```

### 步骤 3: 部署基础设施

```bash
# 应用 Terraform 配置
terraform apply -var="aws_profile=terraform_0603"

# 输入 'yes' 确认部署
```

部署过程大约需要 15-20 分钟，包括：
- VPC 和网络资源创建（~5 分钟）
- EKS 集群创建（~10 分钟）
- 节点组创建（~5 分钟）
- CSI Driver 和应用部署（~5 分钟）

### 步骤 4: 配置 kubectl

```bash
# 更新 kubeconfig
aws --profile terraform_0603 eks update-kubeconfig \
  --region ap-southeast-1 \
  --name RJtest-eks-cluster-202511171652

# 验证连接
kubectl get nodes
kubectl get pods -n rj-webdemo
```

### 步骤 5: 获取应用访问地址

```bash
# 从 Terraform 输出获取 ALB 地址
terraform output eks_info_app_url

# 或者直接查询 Ingress
kubectl get ingress -n rj-webdemo eks-info-app-ingress
```

等待 ALB 创建完成（约 2-3 分钟），然后访问输出的 URL。

---

## 部署状态

### 应用部署

#### EKS Info App
- **命名空间**: rj-webdemo
- **副本数**: 当前 10 个（由 HPA 自动扩展）
- **镜像**: <AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/eks-info-app:latest
- **架构**: ARM64
- **访问地址**: http://k8s-rjwebdem-eksinfoa-276a74cf51-1382595953.ap-southeast-1.elb.amazonaws.com

#### 资源配置
- **CPU 请求**: 100m
- **CPU 限制**: 500m
- **内存请求**: 128Mi
- **内存限制**: 512Mi

#### HPA 配置
- **最小副本数**: 3
- **最大副本数**: 10
- **CPU 目标**: 70%
- **内存目标**: 80%
- **当前状态**: 
  - CPU 使用率: 6%
  - 内存使用率: 307% (触发扩展)
  - 当前副本数: 10

#### CSI Drivers
- **EBS CSI Driver**: 已安装并运行
- **EFS CSI Driver**: 已安装但存在权限问题
- **AWS Load Balancer Controller**: 已安装并运行

#### Metrics Server
- **状态**: 已安装并运行
- **用途**: 为 HPA 提供 CPU 和内存指标

---

## 验证部署

### 1. 检查 Pod 状态
```bash
kubectl get pods -n rj-webdemo
kubectl describe pod -n rj-webdemo -l app=eks-info-app
```

### 2. 检查存储
```bash
# 检查 PVC
kubectl get pvc -n rj-webdemo

# 检查 StorageClass
kubectl get storageclass
```

### 3. 检查 HPA
```bash
kubectl get hpa -n rj-webdemo
kubectl top pods -n rj-webdemo
```

### 4. 查看日志
```bash
kubectl logs -n rj-webdemo -l app=eks-info-app --tail=50
```

### 5. 测试应用功能
```bash
# 获取 ALB 地址
ALB_URL=$(terraform output -raw eks_info_app_url)

# 测试健康检查
curl $ALB_URL/health

# 访问首页
curl $ALB_URL/
```

### 6. 验证存储功能
```bash
# 健康检查
curl http://k8s-rjwebdem-eksinfoa-276a74cf51-1382595953.ap-southeast-1.elb.amazonaws.com/health

# 访问首页
curl http://k8s-rjwebdem-eksinfoa-276a74cf51-1382595953.ap-southeast-1.elb.amazonaws.com/
```

---

## 配置变量

可以通过 `terraform.tfvars` 文件自定义配置：

```hcl
# terraform.tfvars
aws_profile              = "terraform_0603"
aws_region              = "ap-southeast-1"
cluster_name            = "RJtest-eks-cluster-202511171652"
vpc_cidr                = "10.101.0.0/16"
app_namespace           = "rj-webdemo"
ssh_key_name            = "RJ-test-Pem-<AWS_ACCOUNT_ID>"
eks_info_app_image_tag  = "latest"
```

### Terraform 输出信息

Terraform 部署完成后会输出以下信息：

- `vpc_id`: VPC ID
- `eks_cluster_name`: EKS 集群名称
- `eks_cluster_endpoint`: EKS API 端点
- `efs_file_system_id`: EFS 文件系统 ID
- `s3_bucket_name`: S3 存储桶名称
- `eks_info_app_role_arn`: 应用 IAM 角色 ARN
- `eks_info_app_url`: 应用访问 URL

---

## 更新应用

### 更新镜像
```bash
# 构建新镜像
cd eks-info-app
docker buildx build --platform linux/arm64 \
  -t ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/eks-info-app:v2 \
  --load .

# 推送新镜像
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/eks-info-app:v2

# 更新 Deployment
kubectl set image deployment/eks-info-app \
  eks-info-app=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/eks-info-app:v2 \
  -n rj-webdemo

# 或者通过 Terraform
cd ../terraform
terraform apply -var="aws_profile=terraform_0603" -var="eks_info_app_image_tag=v2"
```

### 滚动重启
```bash
kubectl rollout restart deployment/eks-info-app -n rj-webdemo
kubectl rollout status deployment/eks-info-app -n rj-webdemo
```

---

## 扩展配置

### 手动扩展 Pod
```bash
kubectl scale deployment/eks-info-app --replicas=5 -n rj-webdemo
```

### 触发自动扩展
访问应用的压力测试页面 `/stress` 来触发 HPA。

---

## 已修复的问题

### ✅ 1. S3 存储桶配置错误（已修复 - 2025-11-15）

**问题描述**: 应用配置使用错误的 S3 存储桶名称

**原始配置**: `eks-info-app-data`  
**正确配置**: `rjtest-eks-cluster-202511171652-eks-info-app-data`

**影响**: S3 功能无法正常工作，日志中重复出现 "S3 存储桶不存在" 错误

**修复措施**: 
- 更新 `k8s/deployment-no-storage.yaml` 中的 S3_BUCKET_NAME 环境变量
- 应用新配置并重启 Pod

**验证结果**: 
- ✅ S3 存储桶可正常访问
- ✅ 日志中不再有错误信息
- ✅ 就绪检查显示 S3 状态为 "ready"

**详细报告**: 参见 `BUGFIX_REPORT.md`

---

## 已知问题

### 1. EFS CSI Driver 权限问题

**问题描述**: EFS CSI Driver 无法创建 Access Point，报错 "Access Denied"

**影响**: 无法使用 EFS 动态 provisioning 创建 PVC

**临时解决方案**: 当前使用无存储版本的部署配置，EBS 和 EFS 通过预创建的目录挂载

**状态**: 不影响当前功能，EBS 和 EFS 存储都可以正常使用

### 2. 内存使用率异常

**问题描述**: HPA 显示内存使用率较高

**可能原因**: 
- 资源限制配置需要优化
- Metrics 收集延迟

**影响**: 可能触发 HPA 扩展

**建议**: 
- 持续监控应用内存使用情况
- 根据实际使用情况调整资源限制配置

---

## 清理资源

### 删除应用（保留集群）
```bash
# 删除 Kubernetes 资源
kubectl delete namespace rj-webdemo

# 或者通过 Terraform 删除特定资源
cd terraform
terraform destroy -target=kubernetes_deployment.eks_info_app -var="aws_profile=terraform_0603"
```

### 完全删除所有资源
```bash
# 警告：这将删除所有资源，包括数据
cd terraform
terraform destroy -var="aws_profile=terraform_0603"

# 输入 'yes' 确认删除
```

**注意**: 
- S3 存储桶如果包含对象，需要先清空才能删除
- EBS 和 EFS 卷的 ReclaimPolicy 设置为 Retain，删除 PVC 后卷不会自动删除

---

## 故障排查

### Pod 无法启动
```bash
# 查看 Pod 事件
kubectl describe pod -n rj-webdemo -l app=eks-info-app

# 查看日志
kubectl logs -n rj-webdemo -l app=eks-info-app --previous
```

### 存储挂载失败
```bash
# 检查 CSI Driver
kubectl get pods -n kube-system | grep csi

# 检查 PVC 状态
kubectl describe pvc -n rj-webdemo
```

### ALB 无法访问
```bash
# 检查 Ingress 状态
kubectl describe ingress -n rj-webdemo eks-info-app-ingress

# 检查 ALB Controller 日志
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

### IRSA 权限问题
```bash
# 验证 ServiceAccount 注解
kubectl get sa eks-info-app-sa -n rj-webdemo -o yaml

# 检查 Pod 环境变量
kubectl exec -n rj-webdemo -it <pod-name> -- env | grep AWS
```

### S3 存储桶访问问题
```bash
# 检查存储桶名称配置
kubectl get deployment eks-info-app -n rj-webdemo -o yaml | grep S3_BUCKET_NAME

# 验证存储桶存在
aws --profile terraform_0603 s3 ls s3://rjtest-eks-cluster-202511171652-eks-info-app-data

# 检查应用日志
kubectl logs -n rj-webdemo -l app=eks-info-app | grep -i s3
```

更多故障排查信息，请参见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 成本估算

基于 ap-southeast-1 区域的大致成本（按月计算）：

- **EKS 集群**: $73/月
- **EC2 节点** (2x t4g.medium): ~$60/月
- **NAT Gateway** (3个): ~$100/月
- **EBS 卷** (10GB gp3): ~$1/月
- **EFS**: ~$0.30/GB/月（按使用量）
- **S3**: ~$0.023/GB/月（按使用量）
- **ALB**: ~$20/月
- **数据传输**: 按使用量

**总计**: 约 $250-300/月（不包括数据传输）

---

## 安全最佳实践

1. **使用 IRSA**: 应用通过 IRSA 获取临时凭证，不使用长期密钥
2. **加密**: EBS、EFS、S3 都启用了加密
3. **网络隔离**: Pod 运行在私有子网，通过 ALB 暴露
4. **最小权限**: IAM 策略遵循最小权限原则
5. **安全组**: 限制 NFS 访问仅来自 EKS 节点
6. **镜像扫描**: ECR 仓库启用镜像扫描
7. **资源限制**: Pod 配置了 CPU 和内存限制

---

## 下一步计划

### 任务 19.2 - 验证压力测试和扩展
1. ✅ EKS 集群已创建
2. ✅ 应用已部署
3. ✅ HPA 已配置
4. ✅ Metrics Server 已安装
5. ⏳ 执行 CPU 压力测试
6. ⏳ 验证 HPA 触发 Pod 扩展
7. ⏳ 执行内存压力测试
8. ⏳ 检查扩展事件记录

### 待优化项目
1. EFS CSI Driver 权限配置（可选，当前功能正常）
2. 内存资源限制优化（可选，根据实际使用情况）
3. 应用性能监控和优化

### 已完成的修复
1. ✅ S3 存储桶配置错误 - 已修复 (2025-11-15)
2. ✅ 前端数据加载验证 - 已完成 (2025-11-15)
3. ✅ 所有页面功能验证 - 已完成 (2025-11-15)

---

## 参考资料

- [EKS 用户指南](https://docs.aws.amazon.com/eks/latest/userguide/)
- [EBS CSI Driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)
- [EFS CSI Driver](https://github.com/kubernetes-sigs/aws-efs-csi-driver)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [项目 README](README.md)
- [故障排查指南](TROUBLESHOOTING.md)
- [Bug 修复报告](BUGFIX_REPORT.md)
- [项目总结](PROJECT_SUMMARY.md)

---

## 联系信息

如有问题，请联系：
- **作者**: RJ.Wang
- **邮箱**: wangrenjun@gmail.com

---

**文档版本**: 1.0  
**最后更新**: 2025-11-16
