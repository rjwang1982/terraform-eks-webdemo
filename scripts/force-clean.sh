#!/bin/bash
#
# 强制清理 AWS 资源脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-19

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${SCRIPT_DIR}/force-clean.log"

CLUSTER_NAME="RJtest-eks-cluster-202511171652"
REGION="ap-southeast-1"
PROFILE="terraform_0603"
VPC_ID="vpc-0012649bf803235df"

echo "=== 强制清理开始 - $(date) ===" | tee "${LOG_FILE}"

# 1. 等待并删除节点组
echo "[1/8] 等待节点组删除..." | tee -a "${LOG_FILE}"
while true; do
    STATUS=$(aws eks describe-nodegroup \
        --cluster-name "${CLUSTER_NAME}" \
        --nodegroup-name "${CLUSTER_NAME}-nodes" \
        --region "${REGION}" \
        --profile "${PROFILE}" \
        --query 'nodegroup.status' \
        --output text 2>/dev/null || echo "DELETED")
    
    if [ "${STATUS}" = "DELETED" ]; then
        echo "  ✓ 节点组已删除" | tee -a "${LOG_FILE}"
        break
    fi
    echo "  节点组状态: ${STATUS}，等待中..." | tee -a "${LOG_FILE}"
    sleep 10
done

# 2. 删除 EKS 集群
echo "[2/8] 删除 EKS 集群..." | tee -a "${LOG_FILE}"
aws eks delete-cluster \
    --name "${CLUSTER_NAME}" \
    --region "${REGION}" \
    --profile "${PROFILE}" 2>&1 | tee -a "${LOG_FILE}" || echo "  集群已删除或不存在"

# 等待集群删除
while true; do
    STATUS=$(aws eks describe-cluster \
        --name "${CLUSTER_NAME}" \
        --region "${REGION}" \
        --profile "${PROFILE}" \
        --query 'cluster.status' \
        --output text 2>/dev/null || echo "DELETED")
    
    if [ "${STATUS}" = "DELETED" ]; then
        echo "  ✓ EKS 集群已删除" | tee -a "${LOG_FILE}"
        break
    fi
    echo "  集群状态: ${STATUS}，等待中..." | tee -a "${LOG_FILE}"
    sleep 15
done

# 3. 删除网络接口
echo "[3/8] 删除网络接口..." | tee -a "${LOG_FILE}"
ENIS=$(aws ec2 describe-network-interfaces \
    --filters "Name=vpc-id,Values=${VPC_ID}" \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --query 'NetworkInterfaces[].NetworkInterfaceId' \
    --output text)

for ENI in ${ENIS}; do
    echo "  删除 ENI: ${ENI}" | tee -a "${LOG_FILE}"
    aws ec2 delete-network-interface \
        --network-interface-id "${ENI}" \
        --region "${REGION}" \
        --profile "${PROFILE}" 2>&1 | tee -a "${LOG_FILE}" || echo "  ENI 删除失败或已删除"
done

# 4. 删除安全组
echo "[4/8] 删除安全组..." | tee -a "${LOG_FILE}"
sleep 5
SGS=$(aws ec2 describe-security-groups \
    --filters "Name=vpc-id,Values=${VPC_ID}" \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --query 'SecurityGroups[?GroupName!=`default`].GroupId' \
    --output text)

for SG in ${SGS}; do
    echo "  删除安全组: ${SG}" | tee -a "${LOG_FILE}"
    aws ec2 delete-security-group \
        --group-id "${SG}" \
        --region "${REGION}" \
        --profile "${PROFILE}" 2>&1 | tee -a "${LOG_FILE}" || echo "  安全组删除失败或已删除"
done

# 5. 删除子网
echo "[5/8] 删除子网..." | tee -a "${LOG_FILE}"
SUBNETS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=${VPC_ID}" \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --query 'Subnets[].SubnetId' \
    --output text)

for SUBNET in ${SUBNETS}; do
    echo "  删除子网: ${SUBNET}" | tee -a "${LOG_FILE}"
    aws ec2 delete-subnet \
        --subnet-id "${SUBNET}" \
        --region "${REGION}" \
        --profile "${PROFILE}" 2>&1 | tee -a "${LOG_FILE}" || echo "  子网删除失败或已删除"
done

# 6. 删除路由表
echo "[6/8] 删除路由表..." | tee -a "${LOG_FILE}"
ROUTE_TABLES=$(aws ec2 describe-route-tables \
    --filters "Name=vpc-id,Values=${VPC_ID}" \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --query 'RouteTables[?Associations[0].Main!=`true`].RouteTableId' \
    --output text)

for RT in ${ROUTE_TABLES}; do
    echo "  删除路由表: ${RT}" | tee -a "${LOG_FILE}"
    aws ec2 delete-route-table \
        --route-table-id "${RT}" \
        --region "${REGION}" \
        --profile "${PROFILE}" 2>&1 | tee -a "${LOG_FILE}" || echo "  路由表删除失败或已删除"
done

# 7. 删除 Internet Gateway
echo "[7/8] 删除 Internet Gateway..." | tee -a "${LOG_FILE}"
IGWS=$(aws ec2 describe-internet-gateways \
    --filters "Name=attachment.vpc-id,Values=${VPC_ID}" \
    --region "${REGION}" \
    --profile "${PROFILE}" \
    --query 'InternetGateways[].InternetGatewayId' \
    --output text)

for IGW in ${IGWS}; do
    echo "  分离并删除 IGW: ${IGW}" | tee -a "${LOG_FILE}"
    aws ec2 detach-internet-gateway \
        --internet-gateway-id "${IGW}" \
        --vpc-id "${VPC_ID}" \
        --region "${REGION}" \
        --profile "${PROFILE}" 2>&1 | tee -a "${LOG_FILE}" || true
    
    aws ec2 delete-internet-gateway \
        --internet-gateway-id "${IGW}" \
        --region "${REGION}" \
        --profile "${PROFILE}" 2>&1 | tee -a "${LOG_FILE}" || echo "  IGW 删除失败或已删除"
done

# 8. 删除 VPC
echo "[8/8] 删除 VPC..." | tee -a "${LOG_FILE}"
aws ec2 delete-vpc \
    --vpc-id "${VPC_ID}" \
    --region "${REGION}" \
    --profile "${PROFILE}" 2>&1 | tee -a "${LOG_FILE}" || echo "  VPC 删除失败或已删除"

echo "" | tee -a "${LOG_FILE}"
echo "✅ 强制清理完成！" | tee -a "${LOG_FILE}"
echo "=== 清理结束 - $(date) ===" | tee -a "${LOG_FILE}"
