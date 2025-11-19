# --------------------------
# Terraform 输出配置
# 
# Author: RJ.Wang
# Email: wangrenjun@gmail.com
# --------------------------

# EKS 集群信息
output "cluster_name" {
  description = "EKS 集群名称"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "EKS 集群端点"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_version" {
  description = "EKS 集群版本"
  value       = aws_eks_cluster.main.version
}

output "cluster_security_group_id" {
  description = "EKS 集群安全组 ID"
  value       = aws_security_group.eks_cluster.id
}

# VPC 信息
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "公有子网 ID 列表"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "私有子网 ID 列表"
  value       = aws_subnet.private[*].id
}

# EFS 信息
output "efs_id" {
  description = "EFS 文件系统 ID"
  value       = aws_efs_file_system.app.id
}

output "efs_dns_name" {
  description = "EFS DNS 名称"
  value       = aws_efs_file_system.app.dns_name
}

# S3 信息
output "s3_bucket_name" {
  description = "S3 存储桶名称"
  value       = aws_s3_bucket.app.id
}

output "s3_bucket_arn" {
  description = "S3 存储桶 ARN"
  value       = aws_s3_bucket.app.arn
}

# IRSA 信息
output "app_role_arn" {
  description = "应用 IAM Role ARN（用于 IRSA）"
  value       = aws_iam_role.app_role.arn
}

output "alb_controller_role_arn" {
  description = "ALB Controller IAM Role ARN"
  value       = aws_iam_role.aws_load_balancer_controller.arn
}

output "oidc_provider_arn" {
  description = "EKS OIDC Provider ARN"
  value       = aws_iam_openid_connect_provider.eks.arn
}

# 配置命令
output "configure_kubectl" {
  description = "配置 kubectl 的命令"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name} --profile ${var.aws_profile}"
}
