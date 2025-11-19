#!/bin/bash
#
# 修复 AWS 元数据显示 N/A 问题
# 
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-18

set -e

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
K8S_DIR="${PROJECT_ROOT}/k8s"
APP_DIR="${PROJECT_ROOT}/simple-app"

# 配置
AWS_PROFILE="terraform_0603"
AWS_REGION="ap-southeast-1"
CLUSTER_NAME="rj-webdemo"
NAMESPACE="rj-webdemo"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查工具
check_tools() {
    log_info "检查必需工具..."
    
    local tools=("terraform" "kubectl" "aws" "docker")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool 未安装"
            exit 1
        fi
    done
    
    log_info "所有工具已安装"
}

# 步骤 1: 应用 Terraform 配置
apply_terraform() {
    log_info "步骤 1: 应用 Terraform 配置..."
    
    cd "${TERRAFORM_DIR}" || exit 1
    
    # 初始化
    log_info "初始化 Terraform..."
    terraform init
    
    # 应用变更
    log_info "应用 Terraform 变更..."
    terraform apply -auto-approve
    
    # 获取 IAM Role ARN
    ROLE_ARN=$(terraform output -raw app_role_arn)
    log_info "IAM Role ARN: ${ROLE_ARN}"
    
    cd "${PROJECT_ROOT}" || exit 1
}

# 步骤 2: 配置 kubectl
configure_kubectl() {
    log_info "步骤 2: 配置 kubectl..."
    
    aws eks update-kubeconfig \
        --region "${AWS_REGION}" \
        --name "${CLUSTER_NAME}" \
        --profile "${AWS_PROFILE}"
    
    log_info "kubectl 配置完成"
}

# 步骤 3: 重新构建镜像
rebuild_image() {
    log_info "步骤 3: 重新构建和推送镜像..."
    
    cd "${APP_DIR}" || exit 1
    
    if [ -f "build-and-push.sh" ]; then
        chmod +x build-and-push.sh
        ./build-and-push.sh
    else
        log_error "构建脚本不存在: ${APP_DIR}/build-and-push.sh"
        exit 1
    fi
    
    cd "${PROJECT_ROOT}" || exit 1
    log_info "镜像构建完成"
}

# 步骤 4: 更新 Kubernetes 资源
update_k8s_resources() {
    log_info "步骤 4: 更新 Kubernetes 资源..."
    
    # 应用 ServiceAccount
    log_info "应用 ServiceAccount..."
    kubectl apply -f "${K8S_DIR}/serviceaccount.yaml"
    
    # 应用 Deployment
    log_info "应用 Deployment..."
    kubectl apply -f "${K8S_DIR}/deployment.yaml"
    
    # 重启 Deployment
    log_info "重启 Deployment..."
    kubectl rollout restart deployment/eks-info-app -n "${NAMESPACE}"
    
    # 等待部署完成
    log_info "等待部署完成..."
    kubectl rollout status deployment/eks-info-app -n "${NAMESPACE}" --timeout=5m
    
    log_info "Kubernetes 资源更新完成"
}

# 步骤 5: 验证配置
verify_configuration() {
    log_info "步骤 5: 验证配置..."
    
    # 检查 ServiceAccount
    log_info "检查 ServiceAccount..."
    kubectl describe sa rj-webdemo-sa -n "${NAMESPACE}" | grep "role-arn"
    
    # 获取 Pod 名称
    POD_NAME=$(kubectl get pods -n "${NAMESPACE}" -l app=eks-info-app -o jsonpath='{.items[0].metadata.name}')
    log_info "Pod 名称: ${POD_NAME}"
    
    # 检查 Pod 环境变量
    log_info "检查 Pod AWS 环境变量..."
    kubectl exec -n "${NAMESPACE}" "${POD_NAME}" -- env | grep AWS || true
    
    # 检查 Pod 日志
    log_info "检查 Pod 日志（最后 20 行）..."
    kubectl logs -n "${NAMESPACE}" "${POD_NAME}" --tail=20
    
    log_info "配置验证完成"
}

# 步骤 6: 测试应用
test_application() {
    log_info "步骤 6: 测试应用..."
    
    # 获取 Ingress 地址
    INGRESS_HOST=$(kubectl get ingress -n "${NAMESPACE}" -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')
    
    if [ -z "${INGRESS_HOST}" ]; then
        log_warn "Ingress 地址未就绪，请稍后手动测试"
        return
    fi
    
    log_info "应用地址: http://${INGRESS_HOST}"
    
    # 等待 ALB 就绪
    log_info "等待 ALB 就绪（最多 2 分钟）..."
    for i in {1..24}; do
        if curl -s -o /dev/null -w "%{http_code}" "http://${INGRESS_HOST}/health" | grep -q "200"; then
            log_info "ALB 已就绪"
            break
        fi
        echo -n "."
        sleep 5
    done
    echo ""
    
    # 测试健康检查
    log_info "测试健康检查端点..."
    curl -s "http://${INGRESS_HOST}/health" | jq . || true
    
    log_info "请访问以下地址验证 AWS 信息："
    log_info "  http://${INGRESS_HOST}/"
}

# 主函数
main() {
    log_info "开始修复 AWS 元数据显示问题..."
    echo ""
    
    check_tools
    echo ""
    
    # 询问用户是否继续
    read -p "是否继续执行修复流程？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "用户取消操作"
        exit 0
    fi
    
    apply_terraform
    echo ""
    
    configure_kubectl
    echo ""
    
    rebuild_image
    echo ""
    
    update_k8s_resources
    echo ""
    
    verify_configuration
    echo ""
    
    test_application
    echo ""
    
    log_info "修复完成！"
    log_info "如果仍然显示 N/A，请查看故障排查文档："
    log_info "  ${APP_DIR}/FIX_AWS_METADATA.md"
}

# 执行主函数
main "$@"
