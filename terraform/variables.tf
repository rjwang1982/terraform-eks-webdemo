# --------------------------
# 变量定义
# 
# Author: RJ.Wang
# Email: wangrenjun@gmail.com
# --------------------------

variable "aws_profile" {
  description = "AWS Profile 名称，如果不指定则使用系统默认"
  type        = string
  default     = null
}

variable "aws_region" {
  description = "AWS 区域"
  type        = string
  default     = "ap-southeast-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR 块"
  type        = string
  default     = "10.101.0.0/16"
}

variable "cluster_name" {
  description = "EKS 集群名"
  type        = string
  default     = "RJtest-eks-cluster-202511171652"
}

variable "ssh_key_name" {
  description = "SSH 密钥对名称"
  type        = string
  default     = "RJ-test-Pem-269490040603"
}

variable "allowed_ssh_cidr" {
  description = "允许 SSH 的 CIDR"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "app_namespace" {
  description = "应用部署的 Kubernetes 命名空间"
  type        = string
  default     = "rj-webdemo"
}

variable "eks_info_app_image_tag" {
  description = "EKS Info App Docker 镜像标签"
  type        = string
  default     = "latest"
}
