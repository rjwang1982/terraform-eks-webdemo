# AWS 资源清理报告

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**日期**: 2025-11-16  
**AWS 账号**: 269490040603  
**区域**: ap-southeast-1

---

## 问题诊断

### 症状
执行 `terraform destroy -auto-approve` 时，VPC 删除一直卡住无法完成。

### 根本原因
VPC 中存在 **Kubernetes 自动创建的安全组**，这些资源不在 Terraform 管理范围内，导致 VPC 无法删除。

### 发现的遗留资源

#### 1. Kubernetes 创建的安全组
- `sg-0d5773f7c3e9c5d74` - k8s-traffic-RJtestekscluster20250822-c8f4903cf0
  - 用途: LoadBalancer 后端共享安全组
  - 创建者: Kubernetes AWS Load Balancer Controller
  
- `sg-08ff19da000e09f21` - k8s-rjwebdem-eksinfoa-b40cf13bf1
  - 用途: LoadBalancer 管理安全组
  - 创建者: Kubernetes Service (type: LoadBalancer)

#### 2. VPC 资源
- `vpc-0b88311ee8b8cdd32` - RJtest-eks-cluster-20250822-vpc
  - CIDR: 10.101.0.0/16
  - 状态: 被安全组依赖，无法删除

---

## 解决方案

### 步骤 1: 识别依赖资源
```bash
# 查找 VPC 中的所有安全组
aws --profile terraform_0603 ec2 describe-security-groups \
  --region ap-southeast-1 \
  --filters "Name=vpc-id,Values=vpc-0b88311ee8b8cdd32" \
  --query 'SecurityGroups[*].[GroupId,GroupName,Description]' \
  --output table
```

### 步骤 2: 手动删除 Kubernetes 安全组
```bash
# 删除第一个安全组
aws --profile terraform_0603 ec2 delete-security-group \
  --region ap-southeast-1 \
  --group-id sg-0d5773f7c3e9c5d74

# 删除第二个安全组
aws --profile terraform_0603 ec2 delete-security-group \
  --region ap-southeast-1 \
  --group-id sg-08ff19da000e09f21
```

### 步骤 3: 重新执行 Terraform Destroy
```bash
terraform destroy -auto-approve
```

**结果**: ✅ 成功删除 VPC 和所有相关资源

---

## 已清理的资源清单

### ✅ 网络资源
- [x] VPC: vpc-0b88311ee8b8cdd32
- [x] 安全组: sg-0d5773f7c3e9c5d74 (k8s-traffic)
- [x] 安全组: sg-08ff19da000e09f21 (k8s-rjwebdem)
- [x] 默认安全组: sg-0a259b9c31c947a5e

### ✅ Terraform 管理的资源
- [x] VPC (10.101.0.0/16)
- [x] 所有子网 (公有/私有)
- [x] Internet Gateway
- [x] NAT Gateway (3个)
- [x] Elastic IP (3个)
- [x] 路由表和关联

### ⚠️ 未清理的资源
以下资源不属于本项目，保留：
- VPC: vpc-03cb93548deb5007d (RJtest20240919-vpc)

---

## 经验教训

### 1. Kubernetes 资源管理
**问题**: Kubernetes 在创建 LoadBalancer 服务时会自动创建 AWS 资源（安全组、ELB 等），这些资源不在 Terraform 管理范围内。

**最佳实践**:
- 在删除 Terraform 资源前，先删除所有 Kubernetes 资源
- 使用 `kubectl delete svc --all -n <namespace>` 删除所有 LoadBalancer 服务
- 等待 AWS 资源自动清理完成后再执行 `terraform destroy`

### 2. 正确的清理顺序
```
1. 删除 Kubernetes 应用和服务
   └─> kubectl delete -f k8s/

2. 等待 LoadBalancer 和安全组自动清理
   └─> aws elbv2 describe-load-balancers (验证)

3. 手动清理遗留的 Kubernetes 安全组
   └─> aws ec2 delete-security-group

4. 执行 Terraform destroy
   └─> terraform destroy -auto-approve
```

### 3. 诊断工具命令

#### 检查 VPC 依赖
```bash
# 安全组
aws --profile terraform_0603 ec2 describe-security-groups \
  --region ap-southeast-1 \
  --filters "Name=vpc-id,Values=<vpc-id>"

# 网络接口
aws --profile terraform_0603 ec2 describe-network-interfaces \
  --region ap-southeast-1 \
  --filters "Name=vpc-id,Values=<vpc-id>"

# Internet Gateway
aws --profile terraform_0603 ec2 describe-internet-gateways \
  --region ap-southeast-1 \
  --filters "Name=attachment.vpc-id,Values=<vpc-id>"

# LoadBalancer (ALB/NLB)
aws --profile terraform_0603 elbv2 describe-load-balancers \
  --region ap-southeast-1 \
  --query 'LoadBalancers[?VpcId==`<vpc-id>`]'

# Classic LoadBalancer
aws --profile terraform_0603 elb describe-load-balancers \
  --region ap-southeast-1 \
  --query 'LoadBalancerDescriptions[?VPCId==`<vpc-id>`]'
```

---

## 清理验证

### 验证命令
```bash
# 验证 VPC 已删除
aws --profile terraform_0603 ec2 describe-vpcs \
  --region ap-southeast-1 \
  --filters "Name=tag:Name,Values=RJtest-eks-cluster-20250822-vpc"

# 验证 EKS 集群已删除
aws --profile terraform_0603 eks list-clusters \
  --region ap-southeast-1

# 验证 Terraform 状态
terraform state list
```

### 验证结果
```
✅ VPC vpc-0b88311ee8b8cdd32 已删除
✅ 所有安全组已删除
✅ EKS 集群已删除
✅ Terraform 状态为空
```

---

## 成本影响

### 已停止计费的资源
- NAT Gateway: ~$0.045/小时 × 3 = $0.135/小时
- EKS 集群: $0.10/小时
- EC2 实例 (t4g.medium): ~$0.0336/小时 × 2 = $0.0672/小时
- EBS 卷: 按 GB 计费
- 数据传输: 按流量计费

**预计节省**: ~$0.30/小时 = ~$216/月

---

## 总结

✅ **问题已解决**: 成功删除所有项目相关的 AWS 资源  
✅ **根本原因**: Kubernetes 创建的安全组阻止 VPC 删除  
✅ **解决方法**: 手动删除 Kubernetes 安全组后重新执行 terraform destroy  
✅ **清理完成**: 所有资源已删除，不再产生费用

---

## 附录: 完整清理脚本

创建一个自动化清理脚本以供将来使用：

```bash
#!/bin/bash
# cleanup-eks-resources.sh
# 作者: RJ.Wang
# 用途: 清理 EKS 项目的所有 AWS 资源

set -e

PROFILE="terraform_0603"
REGION="ap-southeast-1"
VPC_ID="vpc-0b88311ee8b8cdd32"

echo "=== EKS 资源清理脚本 ==="
echo "AWS Profile: $PROFILE"
echo "Region: $REGION"
echo "VPC ID: $VPC_ID"
echo ""

# 1. 删除 Kubernetes 资源
echo "步骤 1: 删除 Kubernetes 资源..."
kubectl delete -f k8s/ --ignore-not-found=true || true
echo "等待 LoadBalancer 清理..."
sleep 30

# 2. 查找并删除 Kubernetes 创建的安全组
echo "步骤 2: 查找 Kubernetes 安全组..."
K8S_SGS=$(aws --profile $PROFILE ec2 describe-security-groups \
  --region $REGION \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=k8s-*" \
  --query 'SecurityGroups[*].GroupId' \
  --output text)

if [ -n "$K8S_SGS" ]; then
  echo "发现 Kubernetes 安全组: $K8S_SGS"
  for sg in $K8S_SGS; do
    echo "删除安全组: $sg"
    aws --profile $PROFILE ec2 delete-security-group \
      --region $REGION \
      --group-id $sg || echo "无法删除 $sg，可能有依赖"
  done
else
  echo "未发现 Kubernetes 安全组"
fi

# 3. 执行 Terraform destroy
echo "步骤 3: 执行 Terraform destroy..."
terraform destroy -auto-approve

echo ""
echo "=== 清理完成 ==="
echo "请验证所有资源已删除:"
echo "  terraform state list"
echo "  aws --profile $PROFILE ec2 describe-vpcs --region $REGION"
```

---

**最后更新**: 2025-11-16  
**状态**: ✅ 清理完成
