# --------------------------
# 输出定义
# 
# Author: RJ.Wang
# Email: wangrenjun@gmail.com
# --------------------------

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "eks_cluster_name" {
  description = "EKS 集群名称"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "EKS 集群端点"
  value       = aws_eks_cluster.main.endpoint
}

output "configure_kubectl" {
  description = "配置 kubectl 命令"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}

output "app_load_balancer_hostname" {
  description = "EKS Info App ALB 访问地址"
  value       = try(kubernetes_ingress_v1.eks_info_app.status[0].load_balancer[0].ingress[0].hostname, "ALB 正在创建中...")
}

output "app_namespace" {
  description = "应用命名空间"
  value       = kubernetes_namespace.app.metadata[0].name
}

output "eks_info_app_url" {
  description = "EKS Info App 访问 URL"
  value       = try("http://${kubernetes_ingress_v1.eks_info_app.status[0].load_balancer[0].ingress[0].hostname}", "等待 ALB 创建...")
}

output "efs_file_system_id" {
  description = "EFS 文件系统 ID"
  value       = aws_efs_file_system.app.id
}

output "efs_file_system_dns_name" {
  description = "EFS 文件系统 DNS 名称"
  value       = aws_efs_file_system.app.dns_name
}

output "s3_bucket_name" {
  description = "S3 存储桶名称"
  value       = aws_s3_bucket.app.id
}

output "s3_bucket_arn" {
  description = "S3 存储桶 ARN"
  value       = aws_s3_bucket.app.arn
}

output "eks_info_app_role_arn" {
  description = "EKS Info App IAM 角色 ARN"
  value       = aws_iam_role.eks_info_app.arn
}

output "ecr_repository_url" {
  description = "ECR 仓库 URL"
  value       = aws_ecr_repository.eks_info_app.repository_url
}

output "ecr_repository_arn" {
  description = "ECR 仓库 ARN"
  value       = aws_ecr_repository.eks_info_app.arn
}
