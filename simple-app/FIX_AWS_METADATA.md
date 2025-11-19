# 修复 AWS 元数据显示 "N/A" 问题

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-18

---

## 问题描述

部署到 EKS 后，访问应用页面显示的 AWS/EKS 信息全部为 "N/A"：
- 实例 ID: N/A
- 实例类型: N/A
- 可用区: N/A

## 根本原因

1. **应用端口配置错误**：代码监听 80 端口，但 Deployment 配置的是 5000 端口
2. **缺少 IRSA 配置**：Pod 没有正确的 IAM 权限访问 AWS 服务
3. **ServiceAccount 未正确配置**：IAM Role ARN 是占位符
4. **缺少 EC2 元数据访问权限**：Pod 无法通过 IMDSv2 访问节点元数据

---

## 解决方案

### 步骤 1: 更新 Terraform 配置

已创建 `terraform/irsa.tf` 文件，包含：
- OIDC Provider 配置
- 应用 IAM Role（用于 IRSA）
- S3 访问策略
- CloudWatch Logs 策略
- EC2 元数据访问策略

**应用 Terraform 变更**：

```bash
cd terraform

# 初始化（如果是新文件）
terraform init

# 查看变更
terraform plan

# 应用变更
terraform apply

# 获取 IAM Role ARN
terraform output app_role_arn
```

输出示例：
```
app_role_arn = "arn:aws:iam::<AWS_ACCOUNT_ID>:role/rj-webdemo-app-role"
```

### 步骤 2: 更新 ServiceAccount

已更新 `k8s/serviceaccount.yaml`，将 IAM Role ARN 设置为：
```yaml
eks.amazonaws.com/role-arn: arn:aws:iam::<AWS_ACCOUNT_ID>:role/rj-webdemo-app-role
```

**应用 ServiceAccount**：

```bash
kubectl apply -f k8s/serviceaccount.yaml
```

### 步骤 3: 重新构建和推送镜像

已修复 `app.py` 端口配置（从 80 改为 5000）。

**重新构建镜像**：

```bash
cd simple-app

# 构建 ARM64 镜像
./build-and-push.sh
```

### 步骤 4: 更新 Deployment

已更新 `k8s/deployment.yaml`：
- ServiceAccount: `rj-webdemo-sa`
- 容器端口: 5000
- 镜像: `rjwang/rj-py-webdemo:1.0`

**应用 Deployment**：

```bash
kubectl apply -f k8s/deployment.yaml

# 等待 Pod 重启
kubectl rollout status deployment/eks-info-app -n rj-webdemo

# 强制重启（如果需要）
kubectl rollout restart deployment/eks-info-app -n rj-webdemo
```

### 步骤 5: 验证配置

**检查 ServiceAccount**：

```bash
kubectl describe sa rj-webdemo-sa -n rj-webdemo
```

应该看到：
```
Annotations:  eks.amazonaws.com/role-arn: arn:aws:iam::<AWS_ACCOUNT_ID>:role/rj-webdemo-app-role
```

**检查 Pod 环境变量**：

```bash
POD_NAME=$(kubectl get pods -n rj-webdemo -l app=eks-info-app -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n rj-webdemo $POD_NAME -- env | grep AWS
```

应该看到：
```
AWS_ROLE_ARN=arn:aws:iam::<AWS_ACCOUNT_ID>:role/rj-webdemo-app-role
AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token
```

**检查 Pod 日志**：

```bash
kubectl logs -n rj-webdemo $POD_NAME
```

查看是否有元数据访问错误。

**测试元数据访问**：

```bash
# 进入 Pod
kubectl exec -it -n rj-webdemo $POD_NAME -- /bin/sh

# 测试 IMDSv2
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null)

curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id

# 应该返回实例 ID，例如: i-0123456789abcdef0
```

### 步骤 6: 访问应用验证

```bash
# 获取 ALB 地址
kubectl get ingress -n rj-webdemo

# 访问应用
curl http://rj-webdemo-alb-947298878.ap-southeast-1.elb.amazonaws.com/
```

现在应该看到正确的 AWS 信息：
- ✅ 实例 ID: i-0xxxxx
- ✅ 实例类型: t4g.medium
- ✅ 可用区: ap-southeast-1a

---

## 完整部署流程

如果要从头开始部署：

```bash
# 1. 应用 Terraform（创建基础设施和 IRSA）
cd terraform
terraform init
terraform apply
ROLE_ARN=$(terraform output -raw app_role_arn)
echo "IAM Role ARN: $ROLE_ARN"

# 2. 配置 kubectl
aws eks update-kubeconfig \
  --region ap-southeast-1 \
  --name rj-webdemo \
  --profile terraform_0603

# 3. 构建和推送镜像
cd ../simple-app
./build-and-push.sh

# 4. 部署 Kubernetes 资源
kubectl apply -f ../k8s/namespace.yaml
kubectl apply -f ../k8s/serviceaccount.yaml
kubectl apply -f ../k8s/deployment.yaml
kubectl apply -f ../k8s/service.yaml
kubectl apply -f ../k8s/ingress.yaml

# 5. 等待部署完成
kubectl rollout status deployment/eks-info-app -n rj-webdemo

# 6. 获取访问地址
kubectl get ingress -n rj-webdemo
```

---

## 故障排查

### 问题 1: Pod 仍然显示 N/A

**检查 ServiceAccount 绑定**：

```bash
kubectl get pod -n rj-webdemo -o yaml | grep serviceAccountName
```

应该显示 `rj-webdemo-sa`。

**检查 IAM Role 信任关系**：

```bash
aws iam get-role --role-name rj-webdemo-app-role --profile terraform_0603
```

确认信任策略包含正确的 OIDC Provider 和 ServiceAccount。

### 问题 2: 元数据访问超时

**检查节点安全组**：

确保节点可以访问 169.254.169.254（AWS 元数据服务）。

**检查 Pod 网络**：

```bash
kubectl exec -n rj-webdemo $POD_NAME -- curl -v http://169.254.169.254/latest/meta-data/
```

### 问题 3: 权限被拒绝

**检查 IAM 策略**：

```bash
aws iam list-role-policies --role-name rj-webdemo-app-role --profile terraform_0603
aws iam get-role-policy --role-name rj-webdemo-app-role \
  --policy-name rj-webdemo-app-ec2-metadata-policy \
  --profile terraform_0603
```

---

## 技术说明

### IRSA 工作原理

1. **ServiceAccount 注解**：指定 IAM Role ARN
2. **Webhook 注入**：EKS 自动注入 AWS 凭证到 Pod
3. **Web Identity Token**：Pod 使用 OIDC token 获取临时凭证
4. **AWS SDK**：自动使用注入的凭证访问 AWS 服务

### IMDSv2 访问流程

1. **获取 Token**：PUT 请求到 token 端点
2. **使用 Token**：在后续请求中携带 token
3. **获取元数据**：访问元数据端点获取信息

### 为什么需要 EC2 元数据策略

虽然 Pod 可以直接访问节点的元数据服务（169.254.169.254），但某些信息（如实例标签）需要 IAM 权限才能通过 API 获取。

---

## 验证清单

部署后检查：

- [ ] Terraform 成功创建 IRSA 配置
- [ ] ServiceAccount 包含正确的 IAM Role ARN
- [ ] Pod 环境变量包含 AWS_ROLE_ARN
- [ ] Pod 可以访问元数据服务
- [ ] 应用页面显示正确的 AWS 信息
- [ ] 日志中没有权限错误

---

## 参考资料

- [EKS IRSA 文档](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [IMDSv2 文档](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)

---

**最后更新**: 2025-11-18
