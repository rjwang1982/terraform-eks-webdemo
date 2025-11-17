# --------------------------
# 应用部署配置
# 
# Author: RJ.Wang
# Email: wangrenjun@gmail.com
# --------------------------

# 数据源 - 获取当前 AWS 账户信息
data "aws_caller_identity" "current" {}

# --------------------------
# ECR 仓库
# --------------------------

# ECR 仓库 - EKS Info App
resource "aws_ecr_repository" "eks_info_app" {
  name                 = "eks-info-app"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "eks-info-app"
    Project     = "eks-info-app"
    Application = "eks-info-app"
    Owner       = "RJ.Wang"
    BillingCode = "RJ"
    Environment = "Sandbox"
    ManagedBy   = "terraform"
  }
}

# ECR 生命周期策略 - 保留最近 10 个镜像
resource "aws_ecr_lifecycle_policy" "eks_info_app" {
  repository = aws_ecr_repository.eks_info_app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# --------------------------
# OIDC Provider for EKS
# --------------------------

# OIDC Provider for EKS
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer

  tags = {
    Name        = "${var.cluster_name}-eks-irsa"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# IAM 策略文档 - AWS Load Balancer Controller
data "aws_iam_policy_document" "aws_load_balancer_controller_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
      type        = "Federated"
    }
  }
}

# IAM 角色 - AWS Load Balancer Controller
resource "aws_iam_role" "aws_load_balancer_controller" {
  assume_role_policy = data.aws_iam_policy_document.aws_load_balancer_controller_assume_role_policy.json
  name               = "aws-load-balancer-controller-${var.cluster_name}"

  tags = {
    Name        = "aws-load-balancer-controller-${var.cluster_name}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# IAM 策略 - AWS Load Balancer Controller (内联)
resource "aws_iam_policy" "aws_load_balancer_controller" {
  name = "AWSLoadBalancerController-${var.cluster_name}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iam:CreateServiceLinkedRole"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "iam:AWSServiceName" = "elasticloadbalancing.amazonaws.com"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeAccountAttributes",
          "ec2:DescribeAddresses",
          "ec2:DescribeAvailabilityZones",
          "ec2:DescribeInternetGateways",
          "ec2:DescribeVpcs",
          "ec2:DescribeVpcPeeringConnections",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeInstances",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeTags",
          "ec2:GetCoipPoolUsage",
          "ec2:GetManagedPrefixListEntries",
          "ec2:DescribeCoipPools",
          "elasticloadbalancing:DescribeLoadBalancers",
          "elasticloadbalancing:DescribeLoadBalancerAttributes",
          "elasticloadbalancing:DescribeListeners",
          "elasticloadbalancing:DescribeListenerAttributes",
          "elasticloadbalancing:DescribeListenerCertificates",
          "elasticloadbalancing:DescribeSSLPolicies",
          "elasticloadbalancing:DescribeRules",
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeTargetGroupAttributes",
          "elasticloadbalancing:DescribeTargetHealth",
          "elasticloadbalancing:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:DescribeUserPoolClient",
          "acm:ListCertificates",
          "acm:DescribeCertificate",
          "iam:ListServerCertificates",
          "iam:GetServerCertificate",
          "waf-regional:GetWebACL",
          "waf-regional:GetWebACLForResource",
          "waf-regional:AssociateWebACL",
          "waf-regional:DisassociateWebACL",
          "wafv2:GetWebACL",
          "wafv2:GetWebACLForResource",
          "wafv2:AssociateWebACL",
          "wafv2:DisassociateWebACL",
          "shield:DescribeProtection",
          "shield:GetSubscriptionState",
          "shield:DescribeSubscription",
          "shield:CreateProtection",
          "shield:DeleteProtection"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateSecurityGroup"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateTags"
        ]
        Resource = "arn:aws:ec2:*:*:security-group/*"
        Condition = {
          StringEquals = {
            "ec2:CreateAction" = "CreateSecurityGroup"
          }
          Null = {
            "aws:RequestTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateTags",
          "ec2:DeleteTags"
        ]
        Resource = "arn:aws:ec2:*:*:security-group/*"
        Condition = {
          Null = {
            "aws:RequestTag/elbv2.k8s.aws/cluster"  = "true"
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:DeleteSecurityGroup"
        ]
        Resource = "*"
        Condition = {
          Null = {
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:CreateLoadBalancer",
          "elasticloadbalancing:CreateTargetGroup"
        ]
        Resource = "*"
        Condition = {
          Null = {
            "aws:RequestTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:CreateListener",
          "elasticloadbalancing:DeleteListener",
          "elasticloadbalancing:CreateRule",
          "elasticloadbalancing:DeleteRule"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:AddTags",
          "elasticloadbalancing:RemoveTags"
        ]
        Resource = [
          "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*"
        ]
        Condition = {
          Null = {
            "aws:RequestTag/elbv2.k8s.aws/cluster"  = "true"
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:AddTags",
          "elasticloadbalancing:RemoveTags"
        ]
        Resource = [
          "arn:aws:elasticloadbalancing:*:*:listener/net/*/*/*",
          "arn:aws:elasticloadbalancing:*:*:listener/app/*/*/*",
          "arn:aws:elasticloadbalancing:*:*:listener-rule/net/*/*/*",
          "arn:aws:elasticloadbalancing:*:*:listener-rule/app/*/*/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:ModifyLoadBalancerAttributes",
          "elasticloadbalancing:SetIpAddressType",
          "elasticloadbalancing:SetSecurityGroups",
          "elasticloadbalancing:SetSubnets",
          "elasticloadbalancing:DeleteLoadBalancer",
          "elasticloadbalancing:ModifyTargetGroup",
          "elasticloadbalancing:ModifyTargetGroupAttributes",
          "elasticloadbalancing:DeleteTargetGroup"
        ]
        Resource = "*"
        Condition = {
          Null = {
            "aws:ResourceTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:AddTags"
        ]
        Resource = [
          "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*"
        ]
        Condition = {
          StringEquals = {
            "elasticloadbalancing:CreateAction" = [
              "CreateTargetGroup",
              "CreateLoadBalancer"
            ]
          }
          Null = {
            "aws:RequestTag/elbv2.k8s.aws/cluster" = "false"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:RegisterTargets",
          "elasticloadbalancing:DeregisterTargets"
        ]
        Resource = "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:SetWebAcl",
          "elasticloadbalancing:ModifyListener",
          "elasticloadbalancing:AddListenerCertificates",
          "elasticloadbalancing:RemoveListenerCertificates",
          "elasticloadbalancing:ModifyRule"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "AWSLoadBalancerController-${var.cluster_name}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

resource "aws_iam_role_policy_attachment" "aws_load_balancer_controller_attach" {
  role       = aws_iam_role.aws_load_balancer_controller.name
  policy_arn = aws_iam_policy.aws_load_balancer_controller.arn
}

# Kubernetes Service Account - AWS Load Balancer Controller
resource "kubernetes_service_account" "aws_load_balancer_controller" {
  metadata {
    name      = "aws-load-balancer-controller"
    namespace = "kube-system"
    labels = {
      "app.kubernetes.io/name"      = "aws-load-balancer-controller"
      "app.kubernetes.io/component" = "controller"
    }
    annotations = {
      "eks.amazonaws.com/role-arn"               = aws_iam_role.aws_load_balancer_controller.arn
      "eks.amazonaws.com/sts-regional-endpoints" = "true"
    }
  }

  depends_on = [aws_eks_node_group.main]
}

# Helm Release - AWS Load Balancer Controller
resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.7.2"

  values = [
    yamlencode({
      clusterName = aws_eks_cluster.main.name
      serviceAccount = {
        create = false
        name   = "aws-load-balancer-controller"
      }
      region = var.aws_region
      vpcId  = aws_vpc.main.id
    })
  ]

  depends_on = [
    kubernetes_service_account.aws_load_balancer_controller,
    aws_iam_role_policy_attachment.aws_load_balancer_controller_attach
  ]
}

# --------------------------
# EKS Info App IRSA 配置
# --------------------------

# IAM 策略文档 - EKS Info App 信任策略
data "aws_iam_policy_document" "eks_info_app_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.app_namespace}:eks-info-app-sa"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
      type        = "Federated"
    }
  }
}

# IAM 角色 - EKS Info App
resource "aws_iam_role" "eks_info_app" {
  assume_role_policy = data.aws_iam_policy_document.eks_info_app_assume_role_policy.json
  name               = "eks-info-app-role-${var.cluster_name}"

  tags = {
    Name        = "eks-info-app-role-${var.cluster_name}"
    Application = "eks-info-app"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# IAM 策略 - S3 访问权限
resource "aws_iam_policy" "eks_info_app_s3" {
  name        = "EKSInfoAppS3Access-${var.cluster_name}"
  description = "S3 access policy for EKS Info App"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.app.arn,
          "${aws_s3_bucket.app.arn}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "EKSInfoAppS3Access-${var.cluster_name}"
    Application = "eks-info-app"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# IAM 策略 - EC2/EFS 描述权限
resource "aws_iam_policy" "eks_info_app_describe" {
  name        = "EKSInfoAppDescribe-${var.cluster_name}"
  description = "EC2 and EFS describe permissions for EKS Info App"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeRouteTables",
          "ec2:DescribeNetworkInterfaces"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticfilesystem:DescribeFileSystems",
          "elasticfilesystem:DescribeMountTargets",
          "elasticfilesystem:DescribeAccessPoints"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:DescribeLoadBalancers",
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeListeners"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "EKSInfoAppDescribe-${var.cluster_name}"
    Application = "eks-info-app"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# 附加 S3 策略到角色
resource "aws_iam_role_policy_attachment" "eks_info_app_s3_attach" {
  role       = aws_iam_role.eks_info_app.name
  policy_arn = aws_iam_policy.eks_info_app_s3.arn
}

# 附加描述权限策略到角色
resource "aws_iam_role_policy_attachment" "eks_info_app_describe_attach" {
  role       = aws_iam_role.eks_info_app.name
  policy_arn = aws_iam_policy.eks_info_app_describe.arn
}

# --------------------------
# EBS CSI Driver 配置
# --------------------------

# IAM 策略文档 - EBS CSI Driver 信任策略
data "aws_iam_policy_document" "ebs_csi_driver_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:ebs-csi-controller-sa"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
      type        = "Federated"
    }
  }
}

# IAM 角色 - EBS CSI Driver
resource "aws_iam_role" "ebs_csi_driver" {
  assume_role_policy = data.aws_iam_policy_document.ebs_csi_driver_assume_role_policy.json
  name               = "ebs-csi-driver-role-${var.cluster_name}"

  tags = {
    Name        = "ebs-csi-driver-role-${var.cluster_name}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# 附加 AWS 托管策略到 EBS CSI Driver 角色
resource "aws_iam_role_policy_attachment" "ebs_csi_driver_attach" {
  role       = aws_iam_role.ebs_csi_driver.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}

# Helm Release - EBS CSI Driver
resource "helm_release" "ebs_csi_driver" {
  name       = "aws-ebs-csi-driver"
  repository = "https://kubernetes-sigs.github.io/aws-ebs-csi-driver"
  chart      = "aws-ebs-csi-driver"
  namespace  = "kube-system"
  version    = "2.28.0"

  values = [
    yamlencode({
      controller = {
        serviceAccount = {
          create = true
          name   = "ebs-csi-controller-sa"
          annotations = {
            "eks.amazonaws.com/role-arn" = aws_iam_role.ebs_csi_driver.arn
          }
        }
      }
    })
  ]

  depends_on = [
    aws_eks_node_group.main,
    aws_iam_role_policy_attachment.ebs_csi_driver_attach
  ]
}

# --------------------------
# EFS CSI Driver 配置
# --------------------------

# IAM 策略文档 - EFS CSI Driver 信任策略
data "aws_iam_policy_document" "efs_csi_driver_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:efs-csi-controller-sa"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
      type        = "Federated"
    }
  }
}

# IAM 角色 - EFS CSI Driver
resource "aws_iam_role" "efs_csi_driver" {
  assume_role_policy = data.aws_iam_policy_document.efs_csi_driver_assume_role_policy.json
  name               = "efs-csi-driver-role-${var.cluster_name}"

  tags = {
    Name        = "efs-csi-driver-role-${var.cluster_name}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# IAM 策略 - EFS CSI Driver
resource "aws_iam_policy" "efs_csi_driver" {
  name        = "EFSCSIDriverPolicy-${var.cluster_name}"
  description = "EFS CSI Driver policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticfilesystem:DescribeAccessPoints",
          "elasticfilesystem:DescribeFileSystems",
          "elasticfilesystem:DescribeMountTargets",
          "ec2:DescribeAvailabilityZones"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticfilesystem:CreateAccessPoint"
        ]
        Resource = "*"
        Condition = {
          StringLike = {
            "aws:RequestTag/efs.csi.aws.com/cluster" = "true"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "elasticfilesystem:DeleteAccessPoint"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/efs.csi.aws.com/cluster" = "true"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "EFSCSIDriverPolicy-${var.cluster_name}"
    BillingCode = "RJ"
    Owner       = "RJ.Wang"
    Environment = "Sandbox"
  }
}

# 附加策略到 EFS CSI Driver 角色
resource "aws_iam_role_policy_attachment" "efs_csi_driver_attach" {
  role       = aws_iam_role.efs_csi_driver.name
  policy_arn = aws_iam_policy.efs_csi_driver.arn
}

# Helm Release - EFS CSI Driver
resource "helm_release" "efs_csi_driver" {
  name       = "aws-efs-csi-driver"
  repository = "https://kubernetes-sigs.github.io/aws-efs-csi-driver"
  chart      = "aws-efs-csi-driver"
  namespace  = "kube-system"
  version    = "2.5.7"

  values = [
    yamlencode({
      controller = {
        serviceAccount = {
          create = true
          name   = "efs-csi-controller-sa"
          annotations = {
            "eks.amazonaws.com/role-arn" = aws_iam_role.efs_csi_driver.arn
          }
        }
      }
    })
  ]

  depends_on = [
    aws_eks_node_group.main,
    aws_iam_role_policy_attachment.efs_csi_driver_attach,
    aws_efs_mount_target.app
  ]
}

# --------------------------
# 应用部署
# --------------------------

# Kubernetes Namespace
resource "kubernetes_namespace" "app" {
  metadata {
    name = var.app_namespace
    labels = {
      name        = var.app_namespace
      environment = "sandbox"
      owner       = "rj.wang"
    }
  }

  depends_on = [aws_eks_node_group.main]
}

# --------------------------
# EKS Info App 部署
# --------------------------

# Kubernetes ServiceAccount - EKS Info App
resource "kubernetes_service_account" "eks_info_app" {
  metadata {
    name      = "eks-info-app-sa"
    namespace = var.app_namespace
    labels = {
      app = "eks-info-app"
    }
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.eks_info_app.arn
    }
  }

  depends_on = [
    kubernetes_namespace.app,
    aws_iam_role.eks_info_app
  ]
}

# StorageClass - EBS gp3
resource "kubernetes_storage_class" "ebs_gp3" {
  metadata {
    name = "ebs-gp3"
    labels = {
      app = "eks-info-app"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Retain"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    type       = "gp3"
    encrypted  = "true"
    iops       = "3000"
    throughput = "125"
  }

  depends_on = [helm_release.ebs_csi_driver]
}

# StorageClass - EFS
resource "kubernetes_storage_class" "efs" {
  metadata {
    name = "efs-sc"
    labels = {
      app = "eks-info-app"
    }
  }

  storage_provisioner = "efs.csi.aws.com"
  reclaim_policy      = "Retain"
  volume_binding_mode = "Immediate"

  parameters = {
    fileSystemId     = aws_efs_file_system.app.id
    provisioningMode = "efs-ap"
    directoryPerms   = "700"
    gidRangeStart    = "1000"
    gidRangeEnd      = "2000"
    basePath         = "/eks-info-app"
  }

  mount_options = ["tls", "iam"]

  depends_on = [
    helm_release.efs_csi_driver,
    aws_efs_file_system.app
  ]
}

# PersistentVolumeClaim - EBS
resource "kubernetes_persistent_volume_claim" "ebs" {
  metadata {
    name      = "eks-info-app-ebs-pvc"
    namespace = var.app_namespace
    labels = {
      app          = "eks-info-app"
      storage-type = "ebs"
    }
  }

  spec {
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = kubernetes_storage_class.ebs_gp3.metadata[0].name

    resources {
      requests = {
        storage = "10Gi"
      }
    }
  }

  depends_on = [kubernetes_storage_class.ebs_gp3]
}

# PersistentVolumeClaim - EFS
resource "kubernetes_persistent_volume_claim" "efs" {
  metadata {
    name      = "eks-info-app-efs-pvc"
    namespace = var.app_namespace
    labels = {
      app          = "eks-info-app"
      storage-type = "efs"
    }
  }

  spec {
    access_modes       = ["ReadWriteMany"]
    storage_class_name = kubernetes_storage_class.efs.metadata[0].name

    resources {
      requests = {
        storage = "20Gi"
      }
    }
  }

  depends_on = [kubernetes_storage_class.efs]
}

# Kubernetes Deployment - EKS Info App
resource "kubernetes_deployment" "eks_info_app" {
  metadata {
    name      = "eks-info-app"
    namespace = var.app_namespace
    labels = {
      app = "eks-info-app"
    }
  }

  spec {
    replicas = 3

    selector {
      match_labels = {
        app = "eks-info-app"
      }
    }

    template {
      metadata {
        labels = {
          app = "eks-info-app"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.eks_info_app.metadata[0].name

        container {
          name              = "eks-info-app"
          image             = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/eks-info-app:latest"
          image_pull_policy = "Always"

          port {
            name           = "http"
            container_port = 5000
            protocol       = "TCP"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }

          volume_mount {
            name       = "ebs-storage"
            mount_path = "/data/ebs"
          }

          volume_mount {
            name       = "efs-storage"
            mount_path = "/data/efs"
          }

          env {
            name = "POD_NAME"
            value_from {
              field_ref {
                field_path = "metadata.name"
              }
            }
          }

          env {
            name = "POD_NAMESPACE"
            value_from {
              field_ref {
                field_path = "metadata.namespace"
              }
            }
          }

          env {
            name = "POD_IP"
            value_from {
              field_ref {
                field_path = "status.podIP"
              }
            }
          }

          env {
            name = "NODE_NAME"
            value_from {
              field_ref {
                field_path = "spec.nodeName"
              }
            }
          }

          env {
            name  = "S3_BUCKET_NAME"
            value = aws_s3_bucket.app.id
          }

          env {
            name  = "FLASK_ENV"
            value = "production"
          }

          env {
            name  = "LOG_LEVEL"
            value = "INFO"
          }

          liveness_probe {
            http_get {
              path   = "/health"
              port   = 5000
              scheme = "HTTP"
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 3
            success_threshold     = 1
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path   = "/ready"
              port   = 5000
              scheme = "HTTP"
            }
            initial_delay_seconds = 5
            period_seconds        = 5
            timeout_seconds       = 3
            success_threshold     = 1
            failure_threshold     = 3
          }

          startup_probe {
            http_get {
              path   = "/health"
              port   = 5000
              scheme = "HTTP"
            }
            initial_delay_seconds = 0
            period_seconds        = 5
            timeout_seconds       = 3
            success_threshold     = 1
            failure_threshold     = 12
          }
        }

        volume {
          name = "ebs-storage"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.ebs.metadata[0].name
          }
        }

        volume {
          name = "efs-storage"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.efs.metadata[0].name
          }
        }

        affinity {
          pod_anti_affinity {
            preferred_during_scheduling_ignored_during_execution {
              weight = 100
              pod_affinity_term {
                label_selector {
                  match_expressions {
                    key      = "app"
                    operator = "In"
                    values   = ["eks-info-app"]
                  }
                }
                topology_key = "kubernetes.io/hostname"
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    kubernetes_service_account.eks_info_app,
    kubernetes_persistent_volume_claim.ebs,
    kubernetes_persistent_volume_claim.efs
  ]
}

# Kubernetes Service - EKS Info App
resource "kubernetes_service" "eks_info_app" {
  metadata {
    name      = "eks-info-app-service"
    namespace = var.app_namespace
    labels = {
      app = "eks-info-app"
    }
  }

  spec {
    type = "ClusterIP"

    selector = {
      app = "eks-info-app"
    }

    port {
      name        = "http"
      protocol    = "TCP"
      port        = 80
      target_port = 5000
    }

    session_affinity = "None"
  }

  depends_on = [kubernetes_deployment.eks_info_app]
}

# Kubernetes Ingress - EKS Info App
resource "kubernetes_ingress_v1" "eks_info_app" {
  metadata {
    name      = "eks-info-app-ingress"
    namespace = var.app_namespace
    labels = {
      app = "eks-info-app"
    }
    annotations = {
      "kubernetes.io/ingress.class"                            = "alb"
      "alb.ingress.kubernetes.io/scheme"                       = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"                  = "ip"
      "alb.ingress.kubernetes.io/listen-ports"                 = jsonencode([{ HTTP = 80 }])
      "alb.ingress.kubernetes.io/healthcheck-path"             = "/health"
      "alb.ingress.kubernetes.io/healthcheck-interval-seconds" = "30"
      "alb.ingress.kubernetes.io/healthcheck-timeout-seconds"  = "5"
      "alb.ingress.kubernetes.io/healthy-threshold-count"      = "2"
      "alb.ingress.kubernetes.io/unhealthy-threshold-count"    = "2"
      "alb.ingress.kubernetes.io/success-codes"                = "200"
      "alb.ingress.kubernetes.io/tags"                         = "Environment=demo,Application=eks-info-app,ManagedBy=kubernetes"
    }
  }

  spec {
    rule {
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.eks_info_app.metadata[0].name
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    kubernetes_service.eks_info_app,
    helm_release.aws_load_balancer_controller
  ]
}

# HorizontalPodAutoscaler - EKS Info App
resource "kubernetes_horizontal_pod_autoscaler_v2" "eks_info_app" {
  metadata {
    name      = "eks-info-app-hpa"
    namespace = var.app_namespace
    labels = {
      app = "eks-info-app"
    }
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.eks_info_app.metadata[0].name
    }

    min_replicas = 3
    max_replicas = 10

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = 70
        }
      }
    }

    metric {
      type = "Resource"
      resource {
        name = "memory"
        target {
          type                = "Utilization"
          average_utilization = 80
        }
      }
    }

    behavior {
      scale_up {
        stabilization_window_seconds = 30
        select_policy                = "Max"

        policy {
          type           = "Percent"
          value          = 50
          period_seconds = 30
        }

        policy {
          type           = "Pods"
          value          = 2
          period_seconds = 30
        }
      }

      scale_down {
        stabilization_window_seconds = 300
        select_policy                = "Min"

        policy {
          type           = "Percent"
          value          = 10
          period_seconds = 60
        }

        policy {
          type           = "Pods"
          value          = 1
          period_seconds = 60
        }
      }
    }
  }

  depends_on = [kubernetes_deployment.eks_info_app]
}
