# EKS 部署状态报告

**生成时间**: 2025-11-19 10:10  
**作者**: RJ.Wang  
**集群名称**: RJtest-eks-cluster-202511171652

---

## 📊 总体状态

**部署状态**: ⚠️ **部分成功 - 节点组创建失败**

---

## ✅ 已成功创建的资源

### 1. 网络基础设施
- ✅ **VPC**: vpc-0012649bf803235df (10.101.0.0/16)
- ✅ **Internet Gateway**: 已创建
- ✅ **NAT Gateway**: 3个 (每个可用区1个)
- ✅ **公有子网**: 3个
  - subnet-04b68ee63c860f2e6 (ap-southeast-1a)
  - subnet-01a6e5c5452b9d82a (ap-southeast-1b)
  - subnet-0faad244d974ec47c (ap-southeast-1c)
- ✅ **私有子网**: 6个
  - subnet-0474702195829bd7d (ap-southeast-1a)
  - subnet-03b2510e1cabbf855 (ap-southeast-1b)
  - subnet-05cb92427990c4a4a (ap-southeast-1c)
  - subnet-0aab52e71466485f7 (ap-southeast-1a)
  - subnet-0041d6f643ce6090d (ap-southeast-1b)
  - subnet-0e30272e065f9d49f (ap-southeast-1c)
- ✅ **路由表**: 公有和私有路由表已配置

### 2. EKS 集群
- ✅ **集群名称**: RJtest-eks-cluster-202511171652
- ✅ **集群状态**: ACTIVE
- ✅ **Kubernetes 版本**: 1.34
- ✅ **集群端点**: https://95F6F0F4C5C08417FA5F948EF6D9BDCE.gr7.ap-southeast-1.eks.amazonaws.com
- ✅ **安全组**: sg-0a226dcac121992b3

### 3. IAM 角色和策略
- ✅ **EKS 集群角色**: eks-cluster-role-RJtest-eks-cluster-202511171652
- ✅ **EKS 节点角色**: eks-node-role-RJtest-eks-cluster-202511171652
- ✅ **应用角色**: RJtest-eks-cluster-202511171652-app-role
- ✅ **ALB Controller 角色**: aws-load-balancer-controller-RJtest-eks-cluster-202511171652
- ✅ **OIDC Provider**: 已创建并配置

### 4. 存储资源
- ✅ **EFS 文件系统**: fs-0c28ffe9dd1b80e92
  - 状态: available
  - DNS: fs-0c28ffe9dd1b80e92.efs.ap-southeast-1.amazonaws.com
  - 挂载目标: 3个 (每个可用区1个)
- ✅ **S3 存储桶**: rjtest-eks-cluster-202511171652-eks-info-app-data
  - 加密: 已启用 (AES256)
  - 版本控制: 已启用
  - 生命周期策略: 已配置

### 5. ECR 仓库
- ✅ **仓库名称**: eks-info-app
- ✅ **镜像扫描**: 已启用
- ✅ **生命周期策略**: 保留最近10个镜像

### 6. 安全组
- ✅ **EKS 集群安全组**: 已创建
- ✅ **EKS 节点安全组**: 已创建
- ✅ **EFS 安全组**: 已创建

---

## ❌ 失败的资源

### 1. EKS 节点组
- ❌ **节点组名称**: RJtest-eks-cluster-202511171652-nodes
- ❌ **状态**: CREATE_FAILED
- ❌ **错误代码**: NodeCreationFailure
- ❌ **错误信息**: "Instances failed to join the kubernetes cluster"
- ❌ **失败的实例**:
  - i-00733b19a90cef00d
  - i-0292ff9b3b7ac172a

**失败原因分析**:
EC2 实例创建成功，但无法加入 Kubernetes 集群。可能的原因：
1. Launch Template 配置问题
2. 用户数据 (user data) 脚本问题
3. 网络连接问题
4. IAM 角色权限问题

---

## 🔍 Kubernetes 集群状态

### CoreDNS Pods
```
NAMESPACE     NAME                      READY   STATUS    RESTARTS   AGE
kube-system   coredns-f65d9fb89-l424s   0/1     Pending   0          46m
kube-system   coredns-f65d9fb89-vbd7p   0/1     Pending   0          46m
```

**状态**: Pending (等待节点加入)

### 命名空间
- default
- kube-node-lease
- kube-public
- kube-system

**应用命名空间**: ❌ rj-webdemo 未创建 (因为节点组失败)

---

## 📋 Terraform State

**Terraform 管理的资源总数**: 62个

**未在 State 中的资源**:
- aws_eks_node_group.main (创建失败，未加入 state)
- kubernetes_service_account.aws_load_balancer_controller (未部署)
- 所有应用相关的 Kubernetes 资源 (未部署)

---

## 💰 当前费用估算

### 正在产生费用的资源
1. **EKS 集群**: ~$0.10/小时
2. **NAT Gateway**: 3个 × $0.045/小时 = $0.135/小时
3. **EFS 文件系统**: 按使用量计费 (当前无数据，费用极低)
4. **S3 存储桶**: 按使用量计费 (当前无数据，费用极低)
5. **EIP**: 3个 × $0.005/小时 = $0.015/小时

**总计**: 约 $0.25/小时 (因为没有 EC2 节点运行)

⚠️ **注意**: 虽然节点组创建失败，但基础设施仍在产生费用！

---

## 🔧 下一步建议

### 选项 1: 修复节点组问题 (推荐)
1. 检查 Launch Template 配置
2. 删除失败的节点组
3. 重新创建节点组
4. 继续部署应用

### 选项 2: 完全清理并重新部署
```bash
./scripts/deploy.sh clean
./scripts/deploy.sh deploy
```

### 选项 3: 手动修复
1. 在 AWS 控制台检查节点组失败详情
2. 查看 EC2 实例系统日志
3. 修复配置问题
4. 手动创建节点组

---

## 📝 部署日志位置

- **主日志**: `/Users/rj/SyncSpace/WorkSpace/GitHub/terraform-eks-webdemo/scripts/deployment.log`
- **Terraform State**: `/Users/rj/SyncSpace/WorkSpace/GitHub/terraform-eks-webdemo/terraform/terraform.tfstate`

---

## 🎯 快速命令参考

### 检查集群状态
```bash
aws eks describe-cluster --name RJtest-eks-cluster-202511171652 --region ap-southeast-1 --profile terraform_0603
```

### 检查节点组状态
```bash
aws eks describe-nodegroup --cluster-name RJtest-eks-cluster-202511171652 --nodegroup-name RJtest-eks-cluster-202511171652-nodes --region ap-southeast-1 --profile terraform_0603
```

### 查看 Kubernetes 资源
```bash
kubectl get nodes
kubectl get pods -A
kubectl cluster-info
```

### 清理所有资源
```bash
cd /Users/rj/SyncSpace/WorkSpace/GitHub/terraform-eks-webdemo
./scripts/deploy.sh clean
```

---

**报告结束**
