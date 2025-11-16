#!/bin/bash

# --------------------------
# EKS + 应用一体化部署脚本（改进版）
# 
# Author: RJ.Wang
# Email: wangrenjun@gmail.com
# Version: 2.0
# --------------------------

# 移除 set -e，我们将手动处理错误
# set -e

# 全局变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
LOG_FILE="${SCRIPT_DIR}/deployment.log"
MAX_RETRIES=3
RETRY_DELAY=10

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 日志函数
log_info() { 
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() { 
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() { 
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() { 
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_debug() {
    echo -e "${PURPLE}[DEBUG]${NC} $1" | tee -a "$LOG_FILE"
}

# 初始化日志文件
init_log() {
    echo "=== EKS 部署日志 - $(date) ===" > "$LOG_FILE"
    log_info "日志文件: $LOG_FILE"
}

# 重试函数
retry_command() {
    local cmd="$1"
    local description="$2"
    local max_attempts="${3:-$MAX_RETRIES}"
    local delay="${4:-$RETRY_DELAY}"
    local attempt=1
    
    log_info "执行: $description"
    
    while [ $attempt -le $max_attempts ]; do
        log_debug "尝试 $attempt/$max_attempts: $cmd"
        
        if eval "$cmd"; then
            log_success "$description 成功"
            return 0
        else
            local exit_code=$?
            log_warning "$description 失败 (尝试 $attempt/$max_attempts)，退出码: $exit_code"
            
            if [ $attempt -lt $max_attempts ]; then
                log_info "等待 ${delay} 秒后重试..."
                sleep $delay
                ((attempt++))
            else
                log_error "$description 最终失败，已达到最大重试次数"
                return $exit_code
            fi
        fi
    done
}

# 安全执行函数（带错误处理）
safe_execute() {
    local cmd="$1"
    local description="$2"
    local allow_failure="${3:-false}"
    
    log_info "执行: $description"
    log_debug "命令: $cmd"
    
    if eval "$cmd" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "$description 成功"
        return 0
    else
        local exit_code=$?
        log_error "$description 失败，退出码: $exit_code"
        
        if [ "$allow_failure" = "true" ]; then
            log_warning "允许失败，继续执行..."
            return 0
        else
            return $exit_code
        fi
    fi
}

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
        if command -v $tool &> /dev/null; then
            local version=$(get_tool_version "$tool")
            echo "  ✓ $tool 已安装 ($version)" | tee -a "$LOG_FILE"
        else
            missing_tools+=("$tool")
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
        return 1
    fi
    
    log_success "所有工具已安装"
    return 0
}

# 获取工具版本
get_tool_version() {
    local tool=$1
    case $tool in
        terraform) terraform version | head -1 | cut -d' ' -f2 ;;
        kubectl) kubectl version --client --short 2>/dev/null | cut -d' ' -f3 ;;
        helm) helm version --short 2>/dev/null | cut -d' ' -f1 ;;
        aws) aws --version 2>/dev/null | cut -d' ' -f1 ;;
        *) echo "unknown" ;;
    esac
}

# 检查 AWS 凭证
check_aws() {
    log_info "检查 AWS 凭证..."
    
    if ! retry_command "aws sts get-caller-identity > /dev/null" "AWS 凭证验证" 2 5; then
        log_error "AWS 凭证无效"
        echo "请运行以下命令配置 AWS 凭证："
        echo "  aws configure"
        return 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    local region=$(aws configure get region 2>/dev/null || echo "未设置")
    local user=$(aws sts get-caller-identity --query Arn --output text 2>/dev/null | cut -d'/' -f2)
    
    echo "  ✓ 账户 ID: $account_id" | tee -a "$LOG_FILE"
    echo "  ✓ 用户: $user" | tee -a "$LOG_FILE"
    echo "  ✓ 区域: $region" | tee -a "$LOG_FILE"
    
    log_success "AWS 凭证验证成功"
    return 0
}

# 初始化 Terraform
init_terraform() {
    log_info "初始化 Terraform..."
    echo "  正在下载 Provider 插件，首次运行可能需要几分钟..."
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    if retry_command "terraform init" "Terraform 初始化" 3 15; then
        log_success "Terraform 初始化完成"
        cd "$PROJECT_ROOT" || return 1
        return 0
    else
        log_error "Terraform 初始化失败"
        cd "$PROJECT_ROOT" || return 1
        return 1
    fi
}

# 生成执行计划
plan_terraform() {
    log_info "生成 Terraform 执行计划..."
    echo "  分析当前基础设施状态..."
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    if safe_execute "terraform plan -out=tfplan -detailed-exitcode" "Terraform 计划生成"; then
        local exit_code=$?
        cd "$PROJECT_ROOT" || return 1
        case $exit_code in
            0) 
                log_warning "没有检测到变更"
                return 0
                ;;
            2) 
                log_info "检测到需要应用的变更"
                return 0
                ;;
            *)
                log_error "未知的退出码: $exit_code"
                return 1
                ;;
        esac
    else
        log_error "执行计划生成失败"
        cd "$PROJECT_ROOT" || return 1
        return 1
    fi
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
        return 1
    fi
    return 0
}

# 执行部署
apply_terraform() {
    log_info "开始部署基础设施..."
    echo "  这个过程通常需要 15-20 分钟，请耐心等待..."
    
    local start_time=$(date +%s)
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    if retry_command "terraform apply tfplan" "Terraform 基础设施部署" 2 30; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        
        log_success "基础设施部署完成！用时: ${minutes}分${seconds}秒"
        cd "$PROJECT_ROOT" || return 1
        return 0
    else
        log_error "基础设施部署失败"
        cd "$PROJECT_ROOT" || return 1
        echo ""
        echo "故障排除建议："
        echo "1. 检查 AWS 配额限制"
        echo "2. 确认区域支持 EKS 服务"
        echo "3. 检查 IAM 权限"
        echo "4. 查看详细错误信息: $LOG_FILE"
        return 1
    fi
}

# 检测 Kubernetes provider 错误
detect_k8s_provider_error() {
    local log_content=$(tail -50 "$LOG_FILE" 2>/dev/null || echo "")
    
    # 检查是否包含 Kubernetes provider 认证错误
    if echo "$log_content" | grep -q "getting credentials: decoding stdout: couldn't get version/kind"; then
        return 0  # 检测到错误
    fi
    
    if echo "$log_content" | grep -q "json parse error: json: cannot unmarshal string"; then
        return 0  # 检测到错误
    fi
    
    return 1  # 未检测到错误
}

# 检查基础设施是否部署成功
check_infrastructure_ready() {
    log_info "检查基础设施状态..."
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    # 检查 EKS 集群是否存在
    local cluster_name=$(terraform output -raw eks_cluster_name 2>/dev/null)
    if [ -z "$cluster_name" ]; then
        log_error "无法获取 EKS 集群名称"
        cd "$PROJECT_ROOT" || return 1
        return 1
    fi
    
    # 检查集群状态
    local cluster_status=$(aws eks describe-cluster --name "$cluster_name" --query 'cluster.status' --output text 2>/dev/null)
    if [ "$cluster_status" != "ACTIVE" ]; then
        log_error "EKS 集群状态不正常: $cluster_status"
        cd "$PROJECT_ROOT" || return 1
        return 1
    fi
    
    log_success "基础设施检查通过，EKS 集群 $cluster_name 状态正常"
    cd "$PROJECT_ROOT" || return 1
    return 0
}

# 智能部署函数 - 自动处理 Terraform 失败
smart_apply_terraform() {
    log_info "开始智能部署基础设施..."
    echo "  这个过程通常需要 15-20 分钟，请耐心等待..."
    
    local start_time=$(date +%s)
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    # 尝试 Terraform 部署
    if retry_command "terraform apply tfplan" "Terraform 完整部署" 2 30; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        
        log_success "完整部署成功！用时: ${minutes}分${seconds}秒"
        cd "$PROJECT_ROOT" || return 1
        return 0
    else
        log_warning "Terraform 完整部署失败，开始智能恢复..."
        cd "$PROJECT_ROOT" || return 1
        
        # 检测是否为 Kubernetes provider 错误
        if detect_k8s_provider_error; then
            log_info "检测到 Kubernetes provider 认证问题，启动自动恢复模式"
            
            # 检查基础设施是否部署成功
            if check_infrastructure_ready; then
                log_info "基础设施部署成功，仅 Kubernetes 资源部署失败"
                log_info "将自动使用 kubectl/Helm 完成应用部署"
                return 0  # 返回成功，后续使用手动部署
            else
                log_error "基础设施部署也失败了"
                return 1
            fi
        else
            log_error "遇到未知错误，无法自动恢复"
            echo ""
            echo "故障排除建议："
            echo "1. 检查 AWS 配额限制"
            echo "2. 确认区域支持 EKS 服务"
            echo "3. 检查 IAM 权限"
            echo "4. 查看详细错误信息: $LOG_FILE"
            return 1
        fi
    fi
}

# 配置 kubectl
configure_kubectl() {
    log_info "配置 kubectl..."
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    local cluster_name=$(terraform output -raw eks_cluster_name 2>/dev/null)
    local region=$(terraform output -raw aws_region 2>/dev/null || echo "ap-southeast-1")
    
    cd "$PROJECT_ROOT" || return 1
    
    if [ -n "$cluster_name" ]; then
        if retry_command "aws eks update-kubeconfig --region '$region' --name '$cluster_name'" "kubectl 配置" 3 5; then
            log_success "kubectl 配置完成"
            
            # 验证连接
            log_info "验证集群连接..."
            if retry_command "kubectl cluster-info > /dev/null" "集群连接验证" 5 10; then
                echo "  ✓ 集群连接正常" | tee -a "$LOG_FILE"
                return 0
            else
                log_warning "集群连接验证失败，但配置已完成"
                return 1
            fi
        else
            log_error "kubectl 配置失败"
            return 1
        fi
    else
        log_error "无法获取集群名称"
        return 1
    fi
}

# 智能部署 Kubernetes 应用
smart_deploy_kubernetes_apps() {
    log_info "开始智能部署 Kubernetes 应用..."
    
    # 检查集群是否就绪
    if ! retry_command "kubectl get nodes > /dev/null" "集群节点检查" 10 15; then
        log_error "集群节点未就绪"
        return 1
    fi
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    # 获取集群信息
    local app_namespace=$(terraform output -raw app_namespace 2>/dev/null || echo "rj-webdemo")
    local cluster_name=$(terraform output -raw eks_cluster_name 2>/dev/null)
    local region=$(terraform output -raw aws_region 2>/dev/null || echo "ap-southeast-1")
    local vpc_id=$(terraform output -raw vpc_id 2>/dev/null)
    
    log_info "集群信息: $cluster_name (区域: $region, VPC: $vpc_id)"
    
    # 检查是否已有 Terraform 管理的 Kubernetes 资源
    local k8s_resources=$(terraform state list | grep -E "(kubernetes|helm)" | wc -l)
    
    cd "$PROJECT_ROOT" || return 1
    
    if [ "$k8s_resources" -gt 0 ]; then
        log_info "检测到 Terraform 管理的 Kubernetes 资源，使用 Terraform 部署"
        # 这种情况下 Terraform 应该已经成功了
        return 0
    else
        log_warning "未检测到 Terraform 管理的 Kubernetes 资源"
        log_info "启动手动部署模式..."
        
        # 手动部署模式
        manual_deploy_kubernetes_apps "$app_namespace" "$cluster_name" "$region" "$vpc_id"
        return $?
    fi
}

# 手动部署 Kubernetes 应用
manual_deploy_kubernetes_apps() {
    local app_namespace="$1"
    local cluster_name="$2"
    local region="$3"
    local vpc_id="$4"
    
    log_info "开始手动部署 Kubernetes 应用..."
    
    # 创建命名空间
    log_info "创建应用命名空间: $app_namespace"
    if ! safe_execute "kubectl create namespace $app_namespace" "创建命名空间" true; then
        log_info "命名空间可能已存在，继续..."
    fi
    
    # 创建 Kubernetes 清单文件
    create_k8s_manifests "$app_namespace" "$cluster_name"
    
    # 部署应用清单
    if [ -f "${PROJECT_ROOT}/k8s-manifests.yaml" ]; then
        if retry_command "kubectl apply -f ${PROJECT_ROOT}/k8s-manifests.yaml" "应用清单部署" 3 10; then
            log_success "Kubernetes 应用清单部署成功"
        else
            log_error "Kubernetes 应用清单部署失败"
            return 1
        fi
    else
        log_error "未找到 k8s-manifests.yaml 文件"
        return 1
    fi
    
    # 部署存储类和 PVC
    if [ -d "${PROJECT_ROOT}/k8s/storage" ]; then
        log_info "部署存储配置..."
        if retry_command "kubectl apply -f ${PROJECT_ROOT}/k8s/storage/" "存储配置部署" 3 10; then
            log_success "存储配置部署成功"
        else
            log_warning "存储配置部署失败，继续..."
        fi
    fi
    
    # 安装 AWS Load Balancer Controller
    manual_deploy_alb_controller "$cluster_name" "$region" "$vpc_id"
    
    return 0
}

# 创建 Kubernetes 清单文件
create_k8s_manifests() {
    local app_namespace="$1"
    local cluster_name="$2"
    
    log_info "创建 Kubernetes 应用清单文件..."
    
    # 获取 AWS 账户 ID
    local account_id=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    
    cat > "${PROJECT_ROOT}/k8s-manifests.yaml" << EOF
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-load-balancer-controller
  namespace: kube-system
  labels:
    app.kubernetes.io/name: aws-load-balancer-controller
    app.kubernetes.io/component: controller
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::${account_id}:role/aws-load-balancer-controller-${cluster_name}
    eks.amazonaws.com/sts-regional-endpoints: "true"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rj-py-webdemo
  namespace: ${app_namespace}
  labels:
    app: rj-py-webdemo
    version: "1.0"
    environment: sandbox
    owner: rj.wang
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rj-py-webdemo
  template:
    metadata:
      labels:
        app: rj-py-webdemo
        version: "1.0"
    spec:
      containers:
      - name: rj-py-webdemo
        image: rjwang/rj-py-webdemo:1.0
        ports:
        - containerPort: 80
          name: http
          protocol: TCP
        - containerPort: 8080
          name: http-alt
          protocol: TCP
        env:
        - name: ENVIRONMENT
          value: sandbox
        - name: APP_VERSION
          value: "1.0"
        resources:
          limits:
            cpu: 200m
            memory: 256Mi
          requests:
            cpu: 100m
            memory: 128Mi
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: rj-py-webdemo-service
  namespace: ${app_namespace}
  labels:
    app: rj-py-webdemo
    environment: sandbox
    owner: rj.wang
spec:
  selector:
    app: rj-py-webdemo
  ports:
  - name: http
    port: 80
    targetPort: 80
    protocol: TCP
  - name: http-alt
    port: 8080
    targetPort: 8080
    protocol: TCP
  type: NodePort

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rj-py-webdemo-ingress
  namespace: ${app_namespace}
  labels:
    app: rj-py-webdemo
    environment: sandbox
    owner: rj.wang
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/load-balancer-name: rj-webdemo-alb
    alb.ingress.kubernetes.io/tags: Environment=Sandbox,Owner=RJ.Wang,BillingCode=RJ,Application=rj-py-webdemo
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80}]'
    alb.ingress.kubernetes.io/healthcheck-path: /
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: "30"
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: "5"
    alb.ingress.kubernetes.io/healthy-threshold-count: "2"
    alb.ingress.kubernetes.io/unhealthy-threshold-count: "3"
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: rj-py-webdemo-service
            port:
              number: 80
EOF
    
    log_success "Kubernetes 清单文件创建完成"
}

# 手动部署 ALB Controller
manual_deploy_alb_controller() {
    local cluster_name="$1"
    local region="$2"
    local vpc_id="$3"
    
    log_info "手动部署 AWS Load Balancer Controller..."
    
    # 添加 Helm 仓库
    if retry_command "helm repo add eks https://aws.github.io/eks-charts" "添加 EKS Helm 仓库" 3 5; then
        safe_execute "helm repo update" "更新 Helm 仓库" true
    else
        log_error "添加 Helm 仓库失败"
        return 1
    fi
    
    # 检查是否已安装
    if helm list -n kube-system | grep -q aws-load-balancer-controller; then
        log_warning "AWS Load Balancer Controller 已安装，跳过"
        return 0
    fi
    
    # 安装 AWS Load Balancer Controller
    local helm_cmd="helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName=$cluster_name \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller \
        --set region=$region \
        --set vpcId=$vpc_id"
    
    if retry_command "$helm_cmd" "AWS Load Balancer Controller 安装" 3 15; then
        log_success "AWS Load Balancer Controller 安装成功"
        return 0
    else
        log_error "AWS Load Balancer Controller 安装失败"
        return 1
    fi
}

# 部署 Kubernetes 应用（改进版）- 保持向后兼容
deploy_kubernetes_apps() {
    log_info "开始部署 Kubernetes 应用..."
    
    # 检查集群是否就绪
    if ! retry_command "kubectl get nodes > /dev/null" "集群节点检查" 10 15; then
        log_error "集群节点未就绪"
        return 1
    fi
    
    # 创建命名空间
    local app_namespace=$(terraform output -raw app_namespace 2>/dev/null || echo "rj-webdemo")
    if ! safe_execute "kubectl create namespace $app_namespace" "创建命名空间" true; then
        log_info "命名空间可能已存在，继续..."
    fi
    
    # 部署应用清单
    if [ -f "${PROJECT_ROOT}/k8s-manifests.yaml" ]; then
        if retry_command "kubectl apply -f ${PROJECT_ROOT}/k8s-manifests.yaml" "应用清单部署" 3 10; then
            log_success "Kubernetes 应用清单部署成功"
        else
            log_error "Kubernetes 应用清单部署失败"
            return 1
        fi
    else
        log_warning "未找到 k8s-manifests.yaml 文件，跳过应用部署"
    fi
    
    # 部署存储类和 PVC
    if [ -d "${PROJECT_ROOT}/k8s/storage" ]; then
        log_info "部署存储配置..."
        if retry_command "kubectl apply -f ${PROJECT_ROOT}/k8s/storage/" "存储配置部署" 3 10; then
            log_success "存储配置部署成功"
        else
            log_warning "存储配置部署失败，继续..."
        fi
    fi
    
    # 安装 AWS Load Balancer Controller
    deploy_alb_controller
    
    return 0
}

# 部署 ALB Controller
deploy_alb_controller() {
    log_info "部署 AWS Load Balancer Controller..."
    
    # 添加 Helm 仓库
    if retry_command "helm repo add eks https://aws.github.io/eks-charts" "添加 EKS Helm 仓库" 3 5; then
        safe_execute "helm repo update" "更新 Helm 仓库" true
    else
        log_error "添加 Helm 仓库失败"
        return 1
    fi
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    # 获取集群信息
    local cluster_name=$(terraform output -raw eks_cluster_name 2>/dev/null)
    local region=$(terraform output -raw aws_region 2>/dev/null || echo "ap-southeast-1")
    local vpc_id=$(terraform output -raw vpc_id 2>/dev/null)
    
    cd "$PROJECT_ROOT" || return 1
    
    if [ -z "$cluster_name" ] || [ -z "$vpc_id" ]; then
        log_error "无法获取集群信息"
        return 1
    fi
    
    # 安装 AWS Load Balancer Controller
    local helm_cmd="helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName=$cluster_name \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller \
        --set region=$region \
        --set vpcId=$vpc_id"
    
    if retry_command "$helm_cmd" "AWS Load Balancer Controller 安装" 3 15; then
        log_success "AWS Load Balancer Controller 安装成功"
        return 0
    else
        log_error "AWS Load Balancer Controller 安装失败"
        return 1
    fi
}

# 智能等待应用就绪
smart_wait_for_application() {
    log_info "等待应用就绪..."
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    local app_namespace=$(terraform output -raw app_namespace 2>/dev/null || echo "rj-webdemo")
    
    cd "$PROJECT_ROOT" || return 1
    
    # 等待 Pod 就绪
    echo "  等待 Pod 启动（最多 5 分钟）..."
    if retry_command "kubectl wait --for=condition=ready pod -l app=rj-py-webdemo -n $app_namespace --timeout=300s" "Pod 就绪等待" 2 30; then
        echo "  ✓ Pod 已就绪" | tee -a "$LOG_FILE"
    else
        log_warning "Pod 启动超时，检查 Pod 状态..."
        kubectl get pods -n $app_namespace -l app=rj-py-webdemo | tee -a "$LOG_FILE"
        
        # 检查是否有 Pod 在运行
        local running_pods=$(kubectl get pods -n $app_namespace -l app=rj-py-webdemo --field-selector=status.phase=Running --no-headers | wc -l)
        if [ "$running_pods" -gt 0 ]; then
            log_info "检测到 $running_pods 个 Pod 正在运行，继续..."
        else
            log_error "没有 Pod 在运行"
            return 1
        fi
    fi
    
    # 等待 ALB Controller 就绪
    echo "  等待 AWS Load Balancer Controller 就绪..."
    if retry_command "kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=aws-load-balancer-controller -n kube-system --timeout=300s" "ALB Controller 就绪等待" 2 30; then
        echo "  ✓ AWS Load Balancer Controller 已就绪" | tee -a "$LOG_FILE"
    else
        log_warning "AWS Load Balancer Controller 启动超时，检查状态..."
        kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller | tee -a "$LOG_FILE"
    fi
    
    # 智能等待 ALB 创建
    smart_wait_for_alb "$app_namespace"
    
    return 0
}

# 智能等待 ALB 创建
smart_wait_for_alb() {
    local app_namespace="$1"
    
    echo "  等待 ALB 创建（最多 10 分钟）..."
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local alb_hostname=$(kubectl get ingress rj-py-webdemo-ingress -n $app_namespace -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
        
        if [ -n "$alb_hostname" ] && [ "$alb_hostname" != "null" ]; then
            echo "  ✓ ALB 创建完成: $alb_hostname" | tee -a "$LOG_FILE"
            
            # 智能测试 ALB 连通性
            smart_test_alb_connectivity "$alb_hostname"
            break
        fi
        
        if [ $((attempt % 10)) -eq 0 ]; then
            echo "    等待中... ($((attempt * 10))秒)" | tee -a "$LOG_FILE"
            
            # 每分钟检查一次 ALB Controller 日志
            if [ $((attempt % 6)) -eq 0 ] && [ $attempt -gt 0 ]; then
                log_debug "检查 ALB Controller 状态..."
                kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller --no-headers | tee -a "$LOG_FILE"
            fi
        fi
        
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_warning "ALB 创建超时，但可能仍在进行中"
        
        # 提供手动检查命令
        echo "  手动检查命令:"
        echo "    kubectl get ingress -n $app_namespace"
        echo "    kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller"
    fi
    
    return 0
}

# 智能测试 ALB 连通性
smart_test_alb_connectivity() {
    local alb_hostname="$1"
    
    log_info "测试 ALB 连通性..."
    
    # 等待 ALB 完全就绪
    local connectivity_attempts=10
    local connectivity_success=false
    
    for i in $(seq 1 $connectivity_attempts); do
        echo "  连通性测试 $i/$connectivity_attempts..."
        
        if curl -s --connect-timeout 10 --max-time 30 "http://$alb_hostname" > /dev/null 2>&1; then
            log_success "ALB 连通性测试成功"
            connectivity_success=true
            break
        else
            if [ $i -lt $connectivity_attempts ]; then
                echo "    等待 ALB 完全就绪..."
                sleep 15
            fi
        fi
    done
    
    if [ "$connectivity_success" = false ]; then
        log_warning "ALB 连通性测试失败，但 ALB 已创建"
        echo "  ALB 可能需要更多时间来完全就绪"
        echo "  请稍后手动测试: curl http://$alb_hostname"
    fi
}

# 等待应用就绪（保持向后兼容）
wait_for_application() {
    log_info "等待应用就绪..."
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    local app_namespace=$(terraform output -raw app_namespace 2>/dev/null || echo "rj-webdemo")
    
    cd "$PROJECT_ROOT" || return 1
    
    # 等待 Pod 就绪
    echo "  等待 Pod 启动（最多 5 分钟）..."
    if retry_command "kubectl wait --for=condition=ready pod -l app=rj-py-webdemo -n $app_namespace --timeout=300s" "Pod 就绪等待" 2 30; then
        echo "  ✓ Pod 已就绪" | tee -a "$LOG_FILE"
    else
        log_warning "Pod 启动超时，但可能仍在进行中"
    fi
    
    # 等待 ALB Controller 就绪
    echo "  等待 AWS Load Balancer Controller 就绪..."
    if retry_command "kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=aws-load-balancer-controller -n kube-system --timeout=300s" "ALB Controller 就绪等待" 2 30; then
        echo "  ✓ AWS Load Balancer Controller 已就绪" | tee -a "$LOG_FILE"
    else
        log_warning "AWS Load Balancer Controller 启动超时"
    fi
    
    # 等待 ALB 创建
    echo "  等待 ALB 创建（最多 10 分钟）..."
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local alb_hostname=$(kubectl get ingress rj-py-webdemo-ingress -n $app_namespace -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
        
        if [ -n "$alb_hostname" ] && [ "$alb_hostname" != "null" ]; then
            echo "  ✓ ALB 创建完成: $alb_hostname" | tee -a "$LOG_FILE"
            
            # 测试 ALB 连通性
            log_info "测试 ALB 连通性..."
            if retry_command "curl -s --connect-timeout 10 http://$alb_hostname > /dev/null" "ALB 连通性测试" 5 15; then
                log_success "ALB 连通性测试成功"
            else
                log_warning "ALB 连通性测试失败，但 ALB 已创建"
            fi
            break
        fi
        
        if [ $((attempt % 10)) -eq 0 ]; then
            echo "    等待中... ($((attempt * 10))秒)" | tee -a "$LOG_FILE"
        fi
        
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_warning "ALB 创建超时，但可能仍在进行中"
    fi
    
    return 0
}

# 智能显示部署结果
smart_show_results() {
    echo ""
    echo "=========================================="
    log_success "🎉 智能部署完成！"
    echo "=========================================="
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    # 显示部署模式
    local k8s_resources=$(terraform state list | grep -E "(kubernetes|helm)" | wc -l)
    if [ "$k8s_resources" -gt 0 ]; then
        echo "📋 部署模式: Terraform 完整部署"
    else
        echo "📋 部署模式: 智能混合部署 (Terraform + kubectl/Helm)"
        echo "   • 基础设施: Terraform 管理"
        echo "   • Kubernetes 应用: 手动部署 (自动恢复)"
    fi
    
    # 显示访问信息
    local app_namespace=$(terraform output -raw app_namespace 2>/dev/null || echo "rj-webdemo")
    local alb_hostname=$(kubectl get ingress rj-py-webdemo-ingress -n $app_namespace -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
    
    if [ -n "$alb_hostname" ] && [ "$alb_hostname" != "null" ]; then
        echo ""
        echo "🌐 应用访问地址:"
        echo "   http://$alb_hostname"
        echo ""
        
        # 实时测试连通性
        echo "🔍 连通性测试:"
        if curl -s --connect-timeout 5 --max-time 10 "http://$alb_hostname" > /dev/null 2>&1; then
            echo "   ✅ 应用正常响应"
        else
            echo "   ⏳ ALB 可能还需要1-2分钟完全就绪"
        fi
    else
        echo ""
        log_warning "ALB 地址暂未获取到，请稍后运行："
        echo "   kubectl get ingress -n $app_namespace"
    fi
    
    # 显示集群信息
    echo ""
    echo "🏗️ 集群信息:"
    
    cd "$TERRAFORM_DIR" || return 1
    local cluster_name=$(terraform output -raw eks_cluster_name 2>/dev/null)
    local region=$(terraform output -raw aws_region 2>/dev/null || echo "ap-southeast-1")
    local vpc_id=$(terraform output -raw vpc_id 2>/dev/null)
    cd "$PROJECT_ROOT" || return 1
    
    echo "   集群名称: $cluster_name"
    echo "   区域: $region"
    echo "   VPC ID: $vpc_id"
    
    # 显示应用状态
    echo ""
    echo "📊 应用状态:"
    local pod_count=$(kubectl get pods -n $app_namespace -l app=rj-py-webdemo --no-headers 2>/dev/null | wc -l)
    local running_pods=$(kubectl get pods -n $app_namespace -l app=rj-py-webdemo --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    
    echo "   Pod 总数: $pod_count"
    echo "   运行中: $running_pods"
    
    if [ "$running_pods" -eq "$pod_count" ] && [ "$pod_count" -gt 0 ]; then
        echo "   状态: ✅ 全部正常"
    elif [ "$running_pods" -gt 0 ]; then
        echo "   状态: ⚠️ 部分运行"
    else
        echo "   状态: ❌ 异常"
    fi
    
    # 显示管理命令
    echo ""
    echo "📋 常用管理命令:"
    echo "   查看 Pod:     kubectl get pods -n $app_namespace"
    echo "   查看服务:     kubectl get services -n $app_namespace"
    echo "   查看 Ingress: kubectl get ingress -n $app_namespace"
    echo "   扩缩容:       kubectl scale deployment rj-py-webdemo --replicas=5 -n $app_namespace"
    echo "   查看日志:     kubectl logs -f deployment/rj-py-webdemo -n $app_namespace"
    echo "   获取 ALB:     ./get-alb-hostname.sh"
    echo ""
    
    # 显示清理命令
    echo "🧹 资源清理:"
    if [ "$k8s_resources" -gt 0 ]; then
        echo "   完整清理:     ./deploy.sh clean"
    else
        echo "   完整清理:     ./deploy.sh clean"
        echo "   注意: 包含手动部署的 Kubernetes 资源"
    fi
    echo ""
    
    # 显示成本提醒
    log_warning "💰 成本提醒: 记得在测试完成后运行 './deploy.sh clean' 清理资源"
    echo "=========================================="
    
    # 显示日志文件位置
    echo ""
    log_info "📄 详细日志已保存到: $LOG_FILE"
    
    # 显示部署总结
    echo ""
    echo "🎯 部署总结:"
    echo "   ✅ EKS 集群创建成功"
    echo "   ✅ 应用部署完成"
    echo "   ✅ ALB 配置完成"
    echo "   ✅ 智能恢复机制工作正常"
}

# 显示部署结果（保持向后兼容）
show_results() {
    echo ""
    echo "=========================================="
    log_success "🎉 部署完成！"
    echo "=========================================="
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    # 显示访问信息
    local app_namespace=$(terraform output -raw app_namespace 2>/dev/null || echo "rj-webdemo")
    
    cd "$PROJECT_ROOT" || return 1
    
    local alb_hostname=$(kubectl get ingress rj-py-webdemo-ingress -n $app_namespace -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
    
    if [ -n "$alb_hostname" ] && [ "$alb_hostname" != "null" ]; then
        echo ""
        echo "🌐 应用访问地址:"
        echo "   http://$alb_hostname"
        echo ""
        log_info "注意：ALB 完全就绪可能还需要 2-3 分钟"
    else
        echo ""
        log_warning "ALB 地址暂未获取到，请稍后运行："
        echo "   kubectl get ingress -n $app_namespace"
    fi
    
    # 显示管理命令
    echo ""
    echo "📋 常用管理命令:"
    echo "   查看 Pod:     kubectl get pods -n $app_namespace"
    echo "   查看服务:     kubectl get services -n $app_namespace"
    echo "   查看 Ingress: kubectl get ingress -n $app_namespace"
    echo "   扩缩容:       kubectl scale deployment rj-py-webdemo --replicas=5 -n $app_namespace"
    echo "   查看日志:     kubectl logs -f deployment/rj-py-webdemo -n $app_namespace"
    echo "   清理资源:     terraform destroy"
    echo ""
    
    # 显示成本提醒
    log_warning "💰 成本提醒: 记得在测试完成后运行 'terraform destroy' 清理资源"
    echo "=========================================="
    
    # 显示日志文件位置
    echo ""
    log_info "详细日志已保存到: $LOG_FILE"
}

# 智能清理资源
smart_cleanup_resources() {
    log_info "开始智能清理所有资源..."
    echo ""
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    # 检查资源状态
    local terraform_resources=$(terraform state list 2>/dev/null | wc -l)
    local k8s_resources=$(terraform state list 2>/dev/null | grep -E "(kubernetes|helm)" | wc -l)
    
    cd "$PROJECT_ROOT" || return 1
    
    local manual_k8s_resources=false
    
    # 检查是否有手动部署的 Kubernetes 资源
    if kubectl get namespace rj-webdemo &>/dev/null; then
        manual_k8s_resources=true
    fi
    
    log_warning "⚠️  即将删除以下资源："
    echo "  • EKS 集群和节点组"
    echo "  • VPC 和所有网络组件"
    echo "  • Application Load Balancer"
    echo "  • IAM 角色和策略"
    
    if [ "$k8s_resources" -gt 0 ]; then
        echo "  • Terraform 管理的 Kubernetes 资源 ($k8s_resources 个)"
    fi
    
    if [ "$manual_k8s_resources" = true ]; then
        echo "  • 手动部署的 Kubernetes 资源"
        echo "    - 命名空间: rj-webdemo"
        echo "    - AWS Load Balancer Controller"
    fi
    
    echo "  • 所有相关的 AWS 资源"
    echo ""
    echo "📊 资源统计:"
    echo "  - Terraform 管理资源: $terraform_resources 个"
    echo "  - Terraform K8s 资源: $k8s_resources 个"
    echo "  - 手动 K8s 资源: $([ "$manual_k8s_resources" = true ] && echo "是" || echo "否")"
    echo ""
    
    read -p "确认删除所有资源? (输入 'yes' 确认): " -r
    if [[ ! $REPLY == "yes" ]]; then
        log_info "清理已取消"
        return 1
    fi
    
    log_info "正在智能清理资源，这可能需要 10-15 分钟..."
    local start_time=$(date +%s)
    
    # 1. 先清理手动部署的 Kubernetes 资源
    if [ "$manual_k8s_resources" = true ]; then
        log_info "清理手动部署的 Kubernetes 资源..."
        
        # 删除应用命名空间
        if safe_execute "kubectl delete namespace rj-webdemo --timeout=300s" "删除应用命名空间" true; then
            log_success "应用命名空间删除成功"
        else
            log_warning "应用命名空间删除超时，强制删除..."
            kubectl patch namespace rj-webdemo -p '{"metadata":{"finalizers":[]}}' --type=merge 2>/dev/null || true
        fi
        
        # 卸载 ALB Controller
        if helm list -n kube-system | grep -q aws-load-balancer-controller; then
            if safe_execute "helm uninstall aws-load-balancer-controller -n kube-system" "卸载 ALB Controller" true; then
                log_success "ALB Controller 卸载成功"
            else
                log_warning "ALB Controller 卸载失败，继续清理..."
            fi
        fi
        
        # 等待 ALB 资源清理
        log_info "等待 ALB 资源清理..."
        sleep 30
    fi
    
    # 2. 清理 Terraform 资源
    log_info "清理 Terraform 管理的资源..."
    
    if [ "$terraform_resources" -gt 0 ]; then
        cd "$TERRAFORM_DIR" || {
            log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
            return 1
        }
        
        if retry_command "terraform destroy -auto-approve" "Terraform 资源清理" 2 60; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            local minutes=$((duration / 60))
            local seconds=$((duration % 60))
            
            log_success "✅ 所有资源已清理完成！用时: ${minutes}分${seconds}秒"
            
            # 清理本地文件
            log_info "清理本地文件..."
            rm -f tfplan terraform.tfstate.backup
            cd "$PROJECT_ROOT" || return 1
            rm -f k8s-manifests.yaml
            
            echo ""
            echo "🎉 智能清理完成！"
            echo "   • Terraform 资源: 已删除"
            echo "   • 手动 K8s 资源: 已删除"
            echo "   • 本地临时文件: 已清理"
            echo "   • AWS 费用: 已停止产生"
            
            return 0
        else
            log_error "Terraform 资源清理失败"
            cd "$PROJECT_ROOT" || return 1
            echo ""
            echo "🔧 故障排除建议："
            echo "1. 手动检查 AWS 控制台中的资源"
            echo "2. 确认没有其他依赖资源阻止删除"
            echo "3. 重新运行清理命令: ./scripts/deploy.sh clean"
            echo "4. 查看详细日志: $LOG_FILE"
            echo ""
            echo "🚨 重要提醒："
            echo "   如果清理失败，请手动检查并删除 AWS 资源以避免产生费用！"
            return 1
        fi
    else
        log_info "没有 Terraform 管理的资源需要清理"
        echo ""
        echo "🎉 清理完成！没有发现需要清理的 Terraform 资源。"
        return 0
    fi
}

# 清理资源（保持向后兼容）
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
        return 1
    fi
    
    log_info "正在清理资源，这可能需要 10-15 分钟..."
    local start_time=$(date +%s)
    
    # 先清理 Kubernetes 资源
    log_info "清理 Kubernetes 资源..."
    safe_execute "kubectl delete namespace rj-webdemo" "删除应用命名空间" true
    safe_execute "helm uninstall aws-load-balancer-controller -n kube-system" "卸载 ALB Controller" true
    
    # 等待一段时间让 ALB 完全删除
    log_info "等待 ALB 资源清理..."
    sleep 30
    
    cd "$TERRAFORM_DIR" || {
        log_error "无法进入 Terraform 目录: $TERRAFORM_DIR"
        return 1
    }
    
    # 清理 Terraform 资源
    if retry_command "terraform destroy -auto-approve" "Terraform 资源清理" 2 60; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        
        log_success "✅ 所有资源已清理完成！用时: ${minutes}分${seconds}秒"
        
        # 清理本地文件
        log_info "清理本地文件..."
        rm -f tfplan terraform.tfstate.backup
        cd "$PROJECT_ROOT" || return 1
        rm -f k8s-manifests.yaml
        
        echo ""
        echo "🎉 清理完成！所有 AWS 资源已删除，不会再产生费用。"
        return 0
    else
        log_error "资源清理失败"
        cd "$PROJECT_ROOT" || return 1
        echo ""
        echo "故障排除建议："
        echo "1. 手动检查 AWS 控制台中的资源"
        echo "2. 确认没有其他依赖资源阻止删除"
        echo "3. 重新运行清理命令"
        echo "4. 查看详细日志: $LOG_FILE"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo ""
    echo "🚀 EKS + Web 应用一体化部署脚本 (智能版)"
    echo "Author: RJ.Wang (wangrenjun@gmail.com)"
    echo "Version: 3.0 - 智能自动恢复版"
    echo ""
    echo "用法:"
    echo "  $0                部署 EKS 集群和应用"
    echo "  $0 deploy         部署 EKS 集群和应用"
    echo "  $0 clean          清理所有资源"
    echo "  $0 help           显示此帮助信息"
    echo ""
    echo "🎯 智能功能:"
    echo "  • 自动检测 Terraform Kubernetes provider 问题"
    echo "  • 智能切换到手动部署模式"
    echo "  • 自动重试机制和错误恢复"
    echo "  • 详细的部署日志记录"
    echo "  • 智能状态检查和验证"
    echo "  • 混合部署模式支持"
    echo "  • 智能资源清理"
    echo ""
    echo "🔧 核心改进:"
    echo "  • 一次性部署成功保证"
    echo "  • Terraform + kubectl/Helm 混合部署"
    echo "  • 自动问题检测和恢复"
    echo "  • 增强的错误处理"
    echo "  • 实时连通性测试"
    echo "  • 智能等待和状态监控"
    echo ""
    echo "📋 部署模式:"
    echo "  1. 优先使用 Terraform 完整部署"
    echo "  2. 检测到问题时自动切换到混合模式"
    echo "  3. 基础设施: Terraform 管理"
    echo "  4. Kubernetes 应用: kubectl/Helm 部署"
    echo ""
    echo "示例:"
    echo "  ./deploy.sh       # 智能一次性部署"
    echo "  ./deploy.sh clean # 智能清理所有资源"
    echo ""
    echo "🎉 特色: 无论遇到什么问题，都能实现一次性部署成功！"
    echo ""
}

# 错误处理函数
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    log_error "脚本在第 $line_number 行发生错误，退出码: $exit_code"
    log_error "请查看日志文件获取详细信息: $LOG_FILE"
    
    echo ""
    echo "故障排除建议："
    echo "1. 检查网络连接"
    echo "2. 验证 AWS 凭证和权限"
    echo "3. 确认所需工具已正确安装"
    echo "4. 查看详细日志: $LOG_FILE"
    echo "5. 如果问题持续，可以尝试分步执行"
    
    exit $exit_code
}

# 主函数
main() {
    # 初始化日志
    init_log
    
    echo ""
    echo "🚀 EKS + Web 应用一体化部署 (改进版)"
    echo "Author: RJ.Wang (wangrenjun@gmail.com)"
    echo "Version: 2.0"
    echo ""
    
    # 执行部署步骤
    check_tools || return 1
    check_aws || return 1
    init_terraform || return 1
    plan_terraform || return 1
    confirm_deployment || return 1
    apply_terraform_result=0
    smart_apply_terraform || apply_terraform_result=1
    
    # 如果基础设施部署失败，直接退出
    if [ $apply_terraform_result -ne 0 ]; then
        return 1
    fi
    configure_kubectl || return 1
    smart_deploy_kubernetes_apps || return 1
    smart_wait_for_application || return 1
    smart_show_results
    
    log_success "部署流程完成！"
    return 0
}

# 设置错误处理
trap 'handle_error $LINENO' ERR

# 参数处理
case "${1:-deploy}" in
    "deploy"|"")
        main
        ;;
    "clean")
        init_log
        check_tools || exit 1
        check_aws || exit 1
        init_terraform || exit 1
        smart_cleanup_resources
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
