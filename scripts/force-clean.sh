#!/bin/bash
#
# 强制清理所有 AWS 资源
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-17

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"

echo "=========================================="
echo "🧹 强制清理所有 AWS 资源"
echo "=========================================="
echo ""

# 1. 清理手动部署的 Kubernetes 资源
echo "📋 步骤 1/4: 清理 Kubernetes 应用资源..."
if kubectl get namespace rj-webdemo &>/dev/null; then
    echo "  删除命名空间 rj-webdemo..."
    kubectl delete namespace rj-webdemo --timeout=300s || true
    echo "  ✓ 命名空间已删除"
else
    echo "  ✓ 命名空间不存在，跳过"
fi

# 2. 卸载 ALB Controller
echo ""
echo "📋 步骤 2/4: 卸载 AWS Load Balancer Controller..."
if helm list -n kube-system | grep -q aws-load-balancer-controller; then
    echo "  卸载 ALB Controller..."
    helm uninstall aws-load-balancer-controller -n kube-system || true
    echo "  ✓ ALB Controller 已卸载"
else
    echo "  ✓ ALB Controller 不存在，跳过"
fi

# 3. 等待 ALB 资源清理
echo ""
echo "📋 步骤 3/4: 等待 ALB 资源清理..."
echo "  等待 30 秒..."
sleep 30
echo "  ✓ 等待完成"

# 4. 清理 Terraform 资源
echo ""
echo "📋 步骤 4/4: 清理 Terraform 基础设施..."
cd "$TERRAFORM_DIR"

echo "  开始 Terraform destroy（这可能需要 10-15 分钟）..."
terraform destroy -auto-approve

echo ""
echo "=========================================="
echo "✅ 所有资源清理完成！"
echo "=========================================="
echo ""
echo "已清理的资源："
echo "  ✓ Kubernetes 命名空间"
echo "  ✓ AWS Load Balancer Controller"
echo "  ✓ Application Load Balancer"
echo "  ✓ EKS 集群和节点组"
echo "  ✓ VPC 和网络组件"
echo "  ✓ IAM 角色和策略"
echo "  ✓ 所有 Terraform 管理的资源"
echo ""
echo "💰 AWS 费用已停止产生"
echo ""
