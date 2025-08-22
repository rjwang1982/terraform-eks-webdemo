# --------------------------
# EKS 集群基础设施配置
# 
# Author: RJ.Wang
# Email: wangrenjun@gmail.com
# --------------------------

# --------------------------
# 数据源
# --------------------------
data "aws_availability_zones" "available" {
  state = "available"
}

# --------------------------
# VPC 和网络资源
# --------------------------
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name                                        = "${var.cluster_name}-vpc"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    BillingCode                                 = "RJ"
    Owner                                       = "RJ.Wang"
    Environment                                 = "Sandbox"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.cluster_name}-igw"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# 公有子网
resource "aws_subnet" "public" {
  count = 3

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.101.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                                        = "${var.cluster_name}-public-${count.index + 1}"
    Type                                        = "Public"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = "1"
    BillingCode                                 = "RJ"
    Owner                                       = "RJ.Wang"
    Environment                                 = "Sandbox"
  }
}

# 私有子网
resource "aws_subnet" "private" {
  count = 6

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.101.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index % 3]

  tags = {
    Name                                        = "${var.cluster_name}-private-${count.index + 1}"
    Type                                        = "Private"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = "1"
    BillingCode                                 = "RJ"
    Owner                                       = "RJ.Wang"
    Environment                                 = "Sandbox"
  }
}

# NAT Gateway 资源
resource "aws_eip" "nat" {
  count = 3

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = {
    Name        = "${var.cluster_name}-nat-eip-${count.index + 1}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

resource "aws_nat_gateway" "main" {
  count = 3

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  depends_on    = [aws_internet_gateway.main]

  tags = {
    Name        = "${var.cluster_name}-nat-${count.index + 1}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# 路由表配置
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.cluster_name}-public-rt"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

resource "aws_route_table_association" "public" {
  count = 3

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  count = 3

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name        = "${var.cluster_name}-private-rt-${count.index + 1}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

resource "aws_route_table_association" "private" {
  count = 6

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index % 3].id
}

# --------------------------
# EKS 集群 IAM 角色
# --------------------------
resource "aws_iam_role" "eks_cluster_role" {
  name = "eks-cluster-role-${var.cluster_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name        = "eks-cluster-role-${var.cluster_name}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  role       = aws_iam_role.eks_cluster_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

# EKS 节点组 IAM 角色
resource "aws_iam_role" "eks_node_role" {
  name = "eks-node-role-${var.cluster_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name        = "eks-node-role-${var.cluster_name}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  role       = aws_iam_role.eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  role       = aws_iam_role.eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "ec2_registry_readonly" {
  role       = aws_iam_role.eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# --------------------------
# 安全组
# --------------------------
resource "aws_security_group" "eks_cluster" {
  name        = "${var.cluster_name}-cluster-sg"
  description = "Security group for EKS cluster"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.cluster_name}-cluster-sg"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

resource "aws_security_group" "eks_nodes" {
  name        = "${var.cluster_name}-nodes-sg"
  description = "Security group for EKS nodes"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
  }

  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.cluster_name}-nodes-sg"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# --------------------------
# EKS 集群和节点组
# --------------------------
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.31"

  vpc_config {
    subnet_ids              = aws_subnet.private[*].id
    endpoint_private_access = true
    endpoint_public_access  = true
    security_group_ids      = [aws_security_group.eks_cluster.id]
  }

  access_config {
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = true
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
  ]

  tags = {
    Name        = var.cluster_name
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = aws_subnet.private[*].id

  instance_types = ["t3.medium"]
  capacity_type  = "ON_DEMAND"

  scaling_config {
    desired_size = 2
    max_size     = 4
    min_size     = 1
  }

  update_config {
    max_unavailable = 1
  }

  remote_access {
    ec2_ssh_key               = var.ssh_key_name
    source_security_group_ids = [aws_security_group.eks_nodes.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.ec2_registry_readonly,
  ]

  tags = {
    Name        = "${var.cluster_name}-nodes"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}
