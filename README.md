# EKS + Web 应用一体化部署

这是一个完整的 Amazon EKS 集群和 Web 应用的自动化部署解决方案，使用 Terraform 进行基础设施即代码管理。

## 作者信息

- **作者**: RJ.Wang
- **邮箱**: wangrenjun@gmail.com
- **项目**: EKS 集群 + Python Web 应用自动化部署

## 功能特性

- 🚀 **一键部署**: 自动创建 EKS 集群、VPC、应用等所有资源
- 🧹 **一键清理**: 自动删除所有创建的 AWS 资源，避免产生不必要费用
- 📊 **进度监控**: 实时显示部署进度和状态
- 💰 **成本透明**: 清晰显示预估成本和资源使用情况
- 🔧 **工具检查**: 自动检查所需工具和 AWS 凭证
- 📋 **详细输出**: 提供详细的部署信息和管理命令

## 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS VPC                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Public AZ-A   │  │   Public AZ-B   │  │ Public AZ-C  │ │
│  │                 │  │                 │  │              │ │
│  │   NAT Gateway   │  │   NAT Gateway   │  │ NAT Gateway  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Private AZ-A   │  │  Private AZ-B   │  │ Private AZ-C │ │
│  │                 │  │                 │  │              │ │
│  │  EKS Nodes      │  │  EKS Nodes      │  │  EKS Nodes   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────────────┐
                    │ Application     │
                    │ Load Balancer   │
                    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   Internet      │
                    │   Gateway       │
                    └─────────────────┘
```

## 部署的资源

### 网络基础设施
- **VPC**: 10.101.0.0/16 CIDR
- **公有子网**: 3个可用区，每个 /24
- **私有子网**: 6个子网（每个可用区2个），每个 /24
- **NAT Gateway**: 3个（每个可用区1个）
- **Internet Gateway**: 1个
- **路由表**: 公有和私有路由表

### EKS 集群
- **EKS 集群**: Kubernetes 1.31
- **节点组**: t3.medium 实例，2-4个节点
- **IAM 角色**: 集群和节点组所需的角色和策略
- **安全组**: 集群和节点的安全组配置

### 应用组件
- **Namespace**: rj-webdemo
- **Deployment**: Python Web 应用，3个副本
- **Service**: NodePort 服务
- **Ingress**: ALB Ingress Controller
- **Load Balancer**: Application Load Balancer

### 支持组件
- **AWS Load Balancer Controller**: Helm 部署
- **Service Account**: IRSA 配置
- **IAM 策略**: Load Balancer Controller 权限

## 前置要求

### 必需工具
- [Terraform](https://www.terraform.io/downloads.html) >= 1.3.2
- [kubectl](https://kubernetes.io/docs/tasks/tools/) >= 1.28
- [Helm](https://helm.sh/docs/intro/install/) >= 3.0
- [AWS CLI](https://aws.amazon.com/cli/) >= 2.0

### AWS 配置
```bash
# 配置 AWS 凭证
aws configure

# 或设置环境变量
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="ap-southeast-1"
```

### IAM 权限
确保 AWS 用户具有以下权限：
- EC2 完全访问权限
- EKS 完全访问权限
- IAM 角色和策略管理权限
- VPC 和网络资源管理权限
- Application Load Balancer 管理权限

## 使用方法

### 1. 部署集群和应用

```bash
# 方法1：直接运行
./deploy.sh

# 方法2：明确指定部署
./deploy.sh deploy
```

部署过程包括：
1. ✅ 工具和凭证检查
2. 🔧 Terraform 初始化
3. 📋 生成执行计划
4. ⚠️ 确认部署（需要输入 'yes'）
5. 🚀 创建基础设施（15-20分钟）
6. 🔧 配置 kubectl
7. ⏳ 等待应用就绪
8. 📊 显示访问信息

### 2. 清理所有资源

```bash
./deploy.sh clean
```

清理过程包括：
1. ⚠️ 确认删除（需要输入 'yes'）
2. 🗑️ 删除所有 AWS 资源（10-15分钟）
3. 🧹 清理本地文件

### 3. 查看帮助

```bash
./deploy.sh help
```

## 成本估算

### 主要费用组件
- **EKS 集群**: ~$0.10/小时
- **EC2 实例**: t3.medium × 2-4个 ≈ $0.08-0.16/小时
- **NAT Gateway**: 3个 × $0.045/小时 ≈ $0.135/小时
- **Application Load Balancer**: ~$0.025/小时
- **数据传输**: 根据使用量

**总计**: 约 $2-4/小时（根据区域和使用情况）

⚠️ **重要**: 测试完成后请及时运行 `./deploy.sh clean` 清理资源！

## 部署后管理

### 访问应用
部署完成后，脚本会显示应用的访问地址：
```
🌐 应用访问地址:
   http://your-alb-hostname.region.elb.amazonaws.com
```

### 常用 kubectl 命令
```bash
# 查看 Pod 状态
kubectl get pods -n rj-webdemo

# 查看服务
kubectl get services -n rj-webdemo

# 查看 Ingress
kubectl get ingress -n rj-webdemo

# 扩缩容应用
kubectl scale deployment rj-py-webdemo --replicas=5 -n rj-webdemo

# 查看 Pod 日志
kubectl logs -f deployment/rj-py-webdemo -n rj-webdemo
```

### Terraform 命令
```bash
# 查看输出信息
terraform output

# 查看状态
terraform state list

# 查看特定资源
terraform show
```

## 故障排除

### 常见问题

1. **部署失败**
   - 检查 AWS 配额限制
   - 确认区域支持 EKS 服务
   - 检查 IAM 权限
   - 查看详细错误信息

2. **应用无法访问**
   - 等待 ALB 完全就绪（2-3分钟）
   - 检查安全组配置
   - 验证 DNS 解析

3. **kubectl 连接失败**
   - 重新配置 kubeconfig：
     ```bash
     aws eks update-kubeconfig --region ap-southeast-1 --name RJtest-eks-cluster-20250822
     ```

4. **清理失败**
   - 手动检查 AWS 控制台
   - 确认没有其他依赖资源
   - 重新运行清理命令

### 日志查看
```bash
# Terraform 详细日志
export TF_LOG=DEBUG
terraform apply

# kubectl 详细输出
kubectl get events -n rj-webdemo
```

## 文件结构

```
.
├── deploy.sh              # 主部署脚本
├── versions.tf            # Terraform 版本约束和 Provider 配置
├── main.tf                # 基础设施定义
├── app.tf                 # 应用资源定义
├── variables.tf           # 变量定义
├── outputs.tf             # 输出定义
├── terraform.tfvars       # 变量值（如果存在）
├── README.md              # 本文档
├── .gitignore             # Git 忽略文件
└── .terraform/            # Terraform 工作目录
```

## 安全注意事项

1. **凭证管理**: 不要在代码中硬编码 AWS 凭证
2. **网络安全**: 私有子网中的节点通过 NAT Gateway 访问互联网
3. **IAM 权限**: 使用最小权限原则
4. **资源标签**: 所有资源都有适当的标签用于管理和计费

## 许可证

本项目仅供学习和测试使用。请遵守 AWS 服务条款和相关法律法规。

---

**⚠️ 重要提醒**: 这是一个演示项目，生产环境使用前请进行充分的安全评估和配置调整。
