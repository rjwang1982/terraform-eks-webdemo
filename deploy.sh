#!/bin/bash

# --------------------------
# EKS + 应用一体化部署脚本（增强版）
# 
# Author: RJ.Wang
# Email: wangrenjun@gmail.com
# --------------------------

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# 显示进度条
show_progress() {
    local duration=$1
    local message=$2
    
    echo -n "$message"
    for ((i=0; i<duration; i++)); do
        echo -n "."
        sleep 1
    done
    echo " 完成"
}

# 检查工具
check_tools() {
    log_info "检查必要工具..."
    local missing_tools=()
    
    for tool in terraform kubectl helm aws; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=("$tool")
        else
            echo "  ✓ $tool 已安装"
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "缺少工具: ${missing_tools[*]}"
        echo "请安装缺失的工具："
        for tool in "${missing_tools[@]}"; do
            case $tool in
                terraform) echo "  - Terraform: https://www.terraform.io/downloads.html" ;;
                kubectl) echo "  - kubectl: https://kubernetes.io/docs/tasks/tools/" ;;
                helm) echo "  - Helm: https://helm.sh/docs/intro/install/" ;;
                aws) echo "  - AWS CLI: https://aws.amazon.com/cli/" ;;
            esac
        done
        exit 1
    fi
    
    log_success "所有工具已安装"
}

# 检查 AWS 凭证
check_aws() {
    log_info "检查 AWS 凭证..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS 凭证无效"
        echo "请运行以下命令配置 AWS 凭证："
        echo "  aws configure"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local region=$(aws configure get region 2>/dev/null || echo "未设置")
    local user=$(aws sts get-caller-identity --query Arn --output text | cut -d'/' -f2)
    
    echo "  ✓ 账户 ID: $account_id"
    echo "  ✓ 用户: $user"
    echo "  ✓ 区域: $region"
    
    log_success "AWS 凭证验证成功"
}

# 初始化 Terraform
init_terraform() {
    log_info "初始化 Terraform..."
    echo "  正在下载 Provider 插件，首次运行可能需要几分钟..."
    
    # 显示详细输出
    if terraform init; then
        log_success "Terraform 初始化完成"
    else
        log_error "Terraform 初始化失败"
        exit 1
    fi
}

# 生成执行计划
plan_terraform() {
    log_info "生成 Terraform 执行计划..."
    echo "  分析当前基础设施状态..."
    
    # 执行 terraform plan 并获取退出码
    terraform plan -out=tfplan -detailed-exitcode
    local exit_code=$?
    
    case $exit_code in
        0) 
            log_warning "没有检测到变更"
            ;;
        1) 
            log_error "执行计划生成失败"
            exit 1
            ;;
        2) 
            log_info "检测到需要应用的变更"
            ;;
        *)
            log_error "未知的退出码: $exit_code"
            exit 1
            ;;
    esac
}

# 确认部署
confirm_deployment() {
    echo ""
    log_warning "即将开始部署，这将创建以下资源："
    echo "  • VPC 和网络组件（NAT Gateway 等，会产生费用）"
    echo "  • EKS 集群（按小时计费）"
    echo "  • EC2 实例（t3.medium 节点组）"
    echo "  • Application Load Balancer"
    echo "  • Web 应用（3个副本）"
    echo ""
    echo "预估成本：约 $2-4/小时（根据区域和使用情况）"
    echo ""
    
    read -p "确认继续部署? (输入 'yes' 确认): " -r
    if [[ ! $REPLY == "yes" ]]; then
        log_info "部署已取消"
        exit 0
    fi
}

# 执行部署
apply_terraform() {
    log_info "开始部署基础设施和应用..."
    echo "  这个过程通常需要 15-20 分钟，请耐心等待..."
    
    # 记录开始时间
    local start_time=$(date +%s)
    
    if terraform apply tfplan; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        
        log_success "部署完成！用时: ${minutes}分${seconds}秒"
    else
        log_error "部署失败"
        echo ""
        echo "故障排除建议："
        echo "1. 检查 AWS 配额限制"
        echo "2. 确认区域支持 EKS 服务"
        echo "3. 检查 IAM 权限"
        echo "4. 查看详细错误信息"
        exit 1
    fi
}

# 配置 kubectl
configure_kubectl() {
    log_info "配置 kubectl..."
    
    local cluster_name=$(terraform output -raw eks_cluster_name 2>/dev/null)
    local region=$(terraform output -raw aws_region 2>/dev/null || echo "ap-southeast-1")
    
    if [ -n "$cluster_name" ]; then
        if aws eks update-kubeconfig --region "$region" --name "$cluster_name"; then
            log_success "kubectl 配置完成"
            
            # 验证连接
            log_info "验证集群连接..."
            if kubectl cluster-info &>/dev/null; then
                echo "  ✓ 集群连接正常"
            else
                log_warning "集群连接验证失败，但配置已完成"
            fi
        else
            log_error "kubectl 配置失败"
        fi
    else
        log_error "无法获取集群名称"
    fi
}

# 等待应用就绪
wait_for_application() {
    log_info "等待应用就绪..."
    
    # 等待 Pod 就绪
    echo "  等待 Pod 启动（最多 5 分钟）..."
    if kubectl wait --for=condition=ready pod -l app=rj-py-webdemo -n rj-webdemo --timeout=300s 2>/dev/null; then
        echo "  ✓ Pod 已就绪"
    else
        log_warning "Pod 启动超时，但可能仍在进行中"
    fi
    
    # 等待 ALB 创建
    echo "  等待 ALB 创建（最多 10 分钟）..."
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local alb_hostname=$(kubectl get ingress rj-py-webdemo-ingress -n rj-webdemo -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
        
        if [ -n "$alb_hostname" ] && [ "$alb_hostname" != "null" ]; then
            echo "  ✓ ALB 创建完成"
            break
        fi
        
        if [ $((attempt % 10)) -eq 0 ]; then
            echo "    等待中... ($((attempt * 10))秒)"
        fi
        
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_warning "ALB 创建超时，但可能仍在进行中"
    fi
}

# 显示部署结果
show_results() {
    echo ""
    echo "=========================================="
    log_success "🎉 部署完成！"
    echo "=========================================="
    
    # 显示访问信息
    local alb_hostname=$(terraform output -raw app_load_balancer_hostname 2>/dev/null)
    if [ -n "$alb_hostname" ] && [ "$alb_hostname" != "ALB 正在创建中..." ]; then
        echo ""
        echo "🌐 应用访问地址:"
        echo "   http://$alb_hostname"
        echo ""
        log_info "注意：ALB 完全就绪可能还需要 2-3 分钟"
    else
        echo ""
        log_warning "ALB 地址暂未获取到，请稍后运行："
        echo "   terraform output app_load_balancer_hostname"
    fi
    
    # 显示管理命令
    echo ""
    echo "📋 常用管理命令:"
    echo "   查看 Pod:     kubectl get pods -n rj-webdemo"
    echo "   查看服务:     kubectl get services -n rj-webdemo"
    echo "   查看 Ingress: kubectl get ingress -n rj-webdemo"
    echo "   扩缩容:       kubectl scale deployment rj-py-webdemo --replicas=5 -n rj-webdemo"
    echo "   清理资源:     terraform destroy"
    echo ""
    
    # 显示成本提醒
    log_warning "💰 成本提醒: 记得在测试完成后运行 'terraform destroy' 清理资源"
    echo "=========================================="
}

# 清理资源
cleanup_resources() {
    log_info "开始清理所有资源..."
    echo ""
    log_warning "⚠️  即将删除以下资源："
    echo "  • EKS 集群和节点组"
    echo "  • VPC 和所有网络组件"
    echo "  • Application Load Balancer"
    echo "  • IAM 角色和策略"
    echo "  • 所有相关的 AWS 资源"
    echo ""
    
    read -p "确认删除所有资源? (输入 'yes' 确认): " -r
    if [[ ! $REPLY == "yes" ]]; then
        log_info "清理已取消"
        exit 0
    fi
    
    log_info "正在清理资源，这可能需要 10-15 分钟..."
    local start_time=$(date +%s)
    
    if terraform destroy -auto-approve; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        
        log_success "✅ 所有资源已清理完成！用时: ${minutes}分${seconds}秒"
        
        # 清理本地文件
        log_info "清理本地文件..."
        rm -f tfplan terraform.tfstate.backup
        
        echo ""
        echo "🎉 清理完成！所有 AWS 资源已删除，不会再产生费用。"
    else
        log_error "资源清理失败"
        echo ""
        echo "故障排除建议："
        echo "1. 手动检查 AWS 控制台中的资源"
        echo "2. 确认没有其他依赖资源阻止删除"
        echo "3. 重新运行清理命令"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo ""
    echo "🚀 EKS + Web 应用一体化部署脚本"
    echo "Author: RJ.Wang (wangrenjun@gmail.com)"
    echo ""
    echo "用法:"
    echo "  $0                部署 EKS 集群和应用"
    echo "  $0 deploy         部署 EKS 集群和应用"
    echo "  $0 clean          清理所有资源"
    echo "  $0 help           显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./deploy.sh       # 开始部署"
    echo "  ./deploy.sh clean # 清理所有资源"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "🚀 EKS + Web 应用一体化部署"
    echo "Author: RJ.Wang (wangrenjun@gmail.com)"
    echo ""
    
    check_tools
    check_aws
    init_terraform
    plan_terraform
    confirm_deployment
    apply_terraform
    configure_kubectl
    wait_for_application
    show_results
}

# 错误处理
trap 'log_error "操作过程中发生错误，请检查上述输出信息"' ERR

# 参数处理
case "${1:-deploy}" in
    "deploy"|"")
        main
        ;;
    "clean")
        check_tools
        check_aws
        init_terraform
        cleanup_resources
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        log_error "未知参数: $1"
        show_help
        exit 1
        ;;
esac
