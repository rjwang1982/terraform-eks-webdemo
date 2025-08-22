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
  description = "ALB 访问地址"
  value       = try(kubernetes_ingress_v1.app.status[0].load_balancer[0].ingress[0].hostname, "ALB 正在创建中...")
}

output "app_namespace" {
  description = "应用命名空间"
  value       = kubernetes_namespace.app.metadata[0].name
}
