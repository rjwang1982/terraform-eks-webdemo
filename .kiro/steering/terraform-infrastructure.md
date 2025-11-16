# Terraform 基础设施管理规范

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-16  
**用途**: 规范项目中所有 AWS 资源的创建和管理方式

---

## 核心原则

### Infrastructure as Code (IaC)
本项目的所有 AWS 资源**必须**通过 Terraform 进行管理，禁止手动在 AWS 控制台创建资源。

---

## 强制要求

### 1. 所有 AWS 资源必须使用 Terraform

**适用范围**：
- ✅ EKS 集群及节点组
- ✅ VPC、子网、路由表、安全组
- ✅ IAM 角色、策略、服务账号
- ✅ ECR 仓库
- ✅ Load Balancer (ALB/NLB)
- ✅ RDS 数据库实例
- ✅ S3 存储桶
- ✅ CloudWatch 日志组
- ✅ 任何其他 AWS 服务资源

**禁止操作**：
- ❌ 在 AWS 控制台手动创建资源
- ❌ 使用 AWS CLI 直接创建资源（除非用于临时测试）
- ❌ 使用 CloudFormation 或其他 IaC 工具
- ❌ 绕过 Terraform 修改资源配置

---

## Terraform 工作流程

### 标准操作流程

```bash
# 1. 初始化 Terraform
cd terraform
terraform init

# 2. 验证配置
terraform validate

# 3. 预览变更
terraform plan

# 4. 应用变更（需要确认）
terraform apply

# 5. 查看当前状态
terraform show

# 6. 销毁资源（谨慎使用）
terraform destroy
```

### 配置文件组织

```
terraform/
├── main.tf              # 主配置文件
├── variables.tf         # 变量定义
├── outputs.tf          # 输出定义
├── providers.tf        # Provider 配置
├── versions.tf         # 版本约束
├── terraform.tfvars    # 变量值（不提交到 Git）
└── modules/            # 自定义模块
    ├── eks/
    ├── vpc/
    └── iam/
```

---

## 资源命名规范

### 命名格式
```
<project>-<environment>-<resource-type>-<description>
```

### 示例
```hcl
# EKS 集群
resource "aws_eks_cluster" "main" {
  name = "eks-webdemo-prod-cluster"
}

# ECR 仓库
resource "aws_ecr_repository" "app" {
  name = "eks-webdemo-prod-app"
}

# IAM 角色
resource "aws_iam_role" "eks_node" {
  name = "eks-webdemo-prod-node-role"
}
```

---

## 状态管理

### 远程状态存储（推荐）

```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-bucket"
    key            = "eks-webdemo/terraform.tfstate"
    region         = "cn-northwest-1"
    profile        = "susermt"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

### 本地状态（开发环境）
- 状态文件：`terraform.tfstate`
- 备份文件：`terraform.tfstate.backup`
- **注意**：不要提交状态文件到 Git

---

## 变更管理流程

### 添加新资源

1. **编写 Terraform 配置**
   ```hcl
   resource "aws_s3_bucket" "data" {
     bucket = "eks-webdemo-prod-data"
     
     tags = {
       Project     = "eks-webdemo"
       Environment = "prod"
       ManagedBy   = "terraform"
     }
   }
   ```

2. **验证配置**
   ```bash
   terraform validate
   terraform fmt
   ```

3. **预览变更**
   ```bash
   terraform plan -out=tfplan
   ```

4. **应用变更**
   ```bash
   terraform apply tfplan
   ```

5. **提交代码**
   ```bash
   git add terraform/
   git commit -m "feat: 添加 S3 数据存储桶"
   ```

### 修改现有资源

1. **修改 Terraform 配置**
2. **运行 `terraform plan` 查看影响**
3. **确认变更不会导致资源重建（除非必要）**
4. **应用变更**
5. **提交代码**

### 删除资源

```bash
# 方法1：从配置中移除后应用
terraform apply

# 方法2：使用 destroy 命令删除特定资源
terraform destroy -target=aws_s3_bucket.data
```

---

## 最佳实践

### 1. 使用变量
```hcl
variable "environment" {
  description = "部署环境"
  type        = string
  default     = "prod"
}

variable "cluster_name" {
  description = "EKS 集群名称"
  type        = string
}
```

### 2. 使用模块
```hcl
module "vpc" {
  source = "./modules/vpc"
  
  vpc_cidr = "10.0.0.0/16"
  environment = var.environment
}
```

### 3. 添加标签
```hcl
tags = {
  Project     = "eks-webdemo"
  Environment = var.environment
  ManagedBy   = "terraform"
  Owner       = "rj.wang"
}
```

### 4. 使用数据源
```hcl
data "aws_caller_identity" "current" {}

data "aws_eks_cluster" "cluster" {
  name = aws_eks_cluster.main.name
}
```

### 5. 输出重要信息
```hcl
output "cluster_endpoint" {
  description = "EKS 集群端点"
  value       = aws_eks_cluster.main.endpoint
}

output "ecr_repository_url" {
  description = "ECR 仓库 URL"
  value       = aws_ecr_repository.app.repository_url
}
```

---

## 安全要求

### 1. 敏感信息管理
- ❌ 不要在代码中硬编码密钥、密码
- ✅ 使用 AWS Secrets Manager 或 Parameter Store
- ✅ 使用 Terraform 变量和环境变量

### 2. 状态文件安全
- ✅ 启用状态文件加密
- ✅ 使用 S3 版本控制
- ✅ 配置 DynamoDB 状态锁
- ❌ 不要提交状态文件到 Git

### 3. 访问控制
```hcl
resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

---

## 多环境管理

### 使用 Workspace
```bash
# 创建环境
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# 切换环境
terraform workspace select prod

# 查看当前环境
terraform workspace show
```

### 使用不同的变量文件
```bash
# 开发环境
terraform apply -var-file="dev.tfvars"

# 生产环境
terraform apply -var-file="prod.tfvars"
```

---

## 故障排查

### 常见问题

#### 1. 状态锁定
```bash
# 强制解锁（谨慎使用）
terraform force-unlock <lock-id>
```

#### 2. 状态不一致
```bash
# 刷新状态
terraform refresh

# 导入现有资源
terraform import aws_s3_bucket.data bucket-name
```

#### 3. 资源依赖问题
```hcl
# 显式声明依赖
resource "aws_instance" "app" {
  # ...
  depends_on = [aws_security_group.app]
}
```

---

## 文档要求

### 每个 Terraform 配置必须包含

1. **README.md**
   - 资源说明
   - 使用方法
   - 变量说明
   - 输出说明

2. **注释**
   ```hcl
   # 创建 EKS 集群
   # 用途：运行容器化应用
   # 依赖：VPC、IAM 角色
   resource "aws_eks_cluster" "main" {
     # ...
   }
   ```

3. **变更日志**
   - 记录重要变更
   - 说明变更原因
   - 记录影响范围

---

## 检查清单

### 提交前检查
- [ ] 运行 `terraform fmt` 格式化代码
- [ ] 运行 `terraform validate` 验证配置
- [ ] 运行 `terraform plan` 确认变更
- [ ] 检查是否有敏感信息泄露
- [ ] 更新相关文档
- [ ] 添加适当的标签
- [ ] 测试变更不会破坏现有资源

### 部署前检查
- [ ] 确认使用正确的 AWS Profile
- [ ] 确认目标环境正确
- [ ] 备份当前状态文件
- [ ] 通知相关人员
- [ ] 准备回滚方案

---

## 紧急情况处理

### 回滚变更
```bash
# 1. 恢复之前的配置文件
git checkout HEAD~1 terraform/

# 2. 应用旧配置
terraform apply

# 或者使用状态文件备份
cp terraform.tfstate.backup terraform.tfstate
```

### 手动修复
如果必须手动修复资源：
1. 记录所有手动操作
2. 尽快更新 Terraform 配置
3. 运行 `terraform plan` 确认状态一致
4. 必要时使用 `terraform import` 导入资源

---

## 总结

**核心要点**：
1. ✅ 所有 AWS 资源必须通过 Terraform 管理
2. ✅ 遵循标准的 Terraform 工作流程
3. ✅ 使用版本控制管理配置文件
4. ✅ 保护状态文件安全
5. ✅ 添加完整的文档和注释
6. ✅ 定期备份和审查

**记住**：Infrastructure as Code 不仅是技术要求，更是团队协作和系统可维护性的保障。

---

**最后更新**: 2025-11-16  
**适用项目**: terraform-eks-webdemo
