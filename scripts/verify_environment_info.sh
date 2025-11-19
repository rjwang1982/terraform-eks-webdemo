#!/bin/bash

# 验证环境信息展示脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-15

set -e

ALB_URL="http://k8s-rjwebdem-eksinfoa-276a74cf51-1382595953.ap-southeast-1.elb.amazonaws.com"

echo "=========================================="
echo "验证任务 19.3: 环境信息展示"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 验证函数
verify_endpoint() {
    local endpoint=$1
    local description=$2
    local check_pattern=$3
    
    echo -e "${YELLOW}正在验证: ${description}${NC}"
    echo "端点: ${endpoint}"
    
    response=$(curl -s "${ALB_URL}${endpoint}" || echo "ERROR")
    
    if [ "$response" = "ERROR" ]; then
        echo -e "${RED}✗ 失败: 无法访问端点${NC}"
        return 1
    fi
    
    if echo "$response" | grep -q "$check_pattern"; then
        echo -e "${GREEN}✓ 成功: 找到预期内容${NC}"
        return 0
    else
        echo -e "${RED}✗ 失败: 未找到预期内容 '${check_pattern}'${NC}"
        return 1
    fi
}

# 计数器
total_tests=0
passed_tests=0

echo "=========================================="
echo "1. 验证所有环境信息正确显示 (需求 1.1-1.6)"
echo "=========================================="
echo ""

# 1.1 验证 Pod 信息
total_tests=$((total_tests + 1))
if verify_endpoint "/" "Pod 基本信息" "Pod Name"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 1.2 验证集群信息
total_tests=$((total_tests + 1))
if verify_endpoint "/" "Kubernetes 集群信息" "Cluster Info"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 1.3 验证 EC2 实例信息
total_tests=$((total_tests + 1))
if verify_endpoint "/" "EC2 实例信息" "Instance ID"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 1.4 验证系统架构信息
total_tests=$((total_tests + 1))
if verify_endpoint "/" "系统架构信息" "Architecture"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 1.5 验证网络架构信息
total_tests=$((total_tests + 1))
if verify_endpoint "/" "网络架构信息" "VPC"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 1.6 验证环境变量
total_tests=$((total_tests + 1))
if verify_endpoint "/" "环境变量" "Environment Variables"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

echo "=========================================="
echo "2. 验证 ARM64 架构检测 (需求 11.1-11.5)"
echo "=========================================="
echo ""

# 验证 ARM64 架构
total_tests=$((total_tests + 1))
if verify_endpoint "/" "ARM64 架构检测" "aarch64\|arm64"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

echo "=========================================="
echo "3. 验证网络信息准确 (需求 7.1-7.5)"
echo "=========================================="
echo ""

# 3.1 验证 VPC 信息
total_tests=$((total_tests + 1))
if verify_endpoint "/network" "VPC 详细信息" "VPC Information"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 3.2 验证子网信息
total_tests=$((total_tests + 1))
if verify_endpoint "/network" "子网信息" "Subnet"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 3.3 验证安全组信息
total_tests=$((total_tests + 1))
if verify_endpoint "/network" "安全组规则" "Security Group"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 3.4 验证路由表信息
total_tests=$((total_tests + 1))
if verify_endpoint "/network" "路由表配置" "Route"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 3.5 验证 Load Balancer 信息
total_tests=$((total_tests + 1))
if verify_endpoint "/network" "Load Balancer 信息" "Load Balancer"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

echo "=========================================="
echo "4. 验证 K8S 资源信息完整 (需求 6.1-6.5)"
echo "=========================================="
echo ""

# 4.1 验证 Pod 列表
total_tests=$((total_tests + 1))
if verify_endpoint "/resources" "Pod 列表" "Pods"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 4.2 验证 Service 信息
total_tests=$((total_tests + 1))
if verify_endpoint "/resources" "Service 信息" "Services"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 4.3 验证 Deployment 配置
total_tests=$((total_tests + 1))
if verify_endpoint "/resources" "Deployment 配置" "Deployment"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 4.4 验证节点资源使用情况
total_tests=$((total_tests + 1))
if verify_endpoint "/resources" "节点资源使用情况" "Node"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

# 4.5 验证 PV 和 PVC 状态
total_tests=$((total_tests + 1))
if verify_endpoint "/resources" "PV 和 PVC 状态" "PersistentVolume\|Storage"; then
    passed_tests=$((passed_tests + 1))
fi
echo ""

echo "=========================================="
echo "验证结果汇总"
echo "=========================================="
echo ""
echo "总测试数: ${total_tests}"
echo -e "通过测试: ${GREEN}${passed_tests}${NC}"
echo -e "失败测试: ${RED}$((total_tests - passed_tests))${NC}"
echo ""

if [ $passed_tests -eq $total_tests ]; then
    echo -e "${GREEN}✓ 所有验证通过！${NC}"
    exit 0
else
    echo -e "${RED}✗ 部分验证失败${NC}"
    exit 1
fi
