#!/bin/bash
# 前端功能验证脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-15

set -e

ALB_URL="http://k8s-rjwebdem-eksinfoa-276a74cf51-1382595953.ap-southeast-1.elb.amazonaws.com"

echo "========================================="
echo "前端功能验证"
echo "========================================="
echo ""

# 1. 测试首页 HTML
echo "1. 测试首页 HTML 加载..."
HTTP_CODE=$(curl -s -o /tmp/index.html -w "%{http_code}" "$ALB_URL/")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 首页 HTML 加载成功 (HTTP $HTTP_CODE)"
    LINE_COUNT=$(wc -l < /tmp/index.html)
    echo "   📄 页面行数: $LINE_COUNT"
else
    echo "   ❌ 首页 HTML 加载失败 (HTTP $HTTP_CODE)"
    exit 1
fi
echo ""

# 2. 测试 API 端点（JSON 格式）
echo "2. 测试首页 API 端点..."
HTTP_CODE=$(curl -s -H "Accept: application/json" -o /tmp/api_response.json -w "%{http_code}" "$ALB_URL/")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ API 端点响应成功 (HTTP $HTTP_CODE)"
    
    # 检查 JSON 结构
    if python3 -c "import json; data=json.load(open('/tmp/api_response.json')); assert 'environment' in data" 2>/dev/null; then
        echo "   ✅ JSON 数据结构正确"
        
        # 显示关键信息
        echo "   📊 数据摘要:"
        python3 << 'EOF'
import json
with open('/tmp/api_response.json') as f:
    data = json.load(f)
    env = data.get('environment', {})
    pod = env.get('pod', {})
    cluster = env.get('cluster', {})
    arch = env.get('architecture', {})
    
    print(f"      - Pod 名称: {pod.get('name', 'N/A')}")
    print(f"      - 命名空间: {pod.get('namespace', 'N/A')}")
    print(f"      - 节点: {pod.get('node_name', 'N/A')}")
    print(f"      - CPU 架构: {arch.get('machine', 'N/A')}")
    print(f"      - ARM64: {arch.get('is_arm64', False)}")
EOF
    else
        echo "   ❌ JSON 数据结构不正确"
        exit 1
    fi
else
    echo "   ❌ API 端点响应失败 (HTTP $HTTP_CODE)"
    exit 1
fi
echo ""

# 3. 检查页面中的关键元素
echo "3. 检查页面关键元素..."
if grep -q "EKS Info WebApp" /tmp/index.html; then
    echo "   ✅ 找到应用标题"
else
    echo "   ❌ 未找到应用标题"
fi

if grep -q "Pod 信息" /tmp/index.html; then
    echo "   ✅ 找到 Pod 信息卡片"
else
    echo "   ❌ 未找到 Pod 信息卡片"
fi

if grep -q "集群信息" /tmp/index.html; then
    echo "   ✅ 找到集群信息卡片"
else
    echo "   ❌ 未找到集群信息卡片"
fi

if grep -q "apiRequest" /tmp/index.html; then
    echo "   ✅ 找到 JavaScript API 调用函数"
else
    echo "   ❌ 未找到 JavaScript API 调用函数"
fi
echo ""

# 4. 测试其他页面
echo "4. 测试其他页面..."
PAGES=("storage" "ebs" "efs" "s3" "network" "resources" "stress" "scaling")
for page in "${PAGES[@]}"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$ALB_URL/$page")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ /$page 页面正常 (HTTP $HTTP_CODE)"
    else
        echo "   ❌ /$page 页面异常 (HTTP $HTTP_CODE)"
    fi
done
echo ""

# 5. 测试健康检查
echo "5. 测试健康检查端点..."
HTTP_CODE=$(curl -s -o /tmp/health.json -w "%{http_code}" "$ALB_URL/health")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 健康检查正常 (HTTP $HTTP_CODE)"
    python3 -c "import json; data=json.load(open('/tmp/health.json')); print(f\"   📊 状态: {data.get('status', 'unknown')}\")"
else
    echo "   ❌ 健康检查失败 (HTTP $HTTP_CODE)"
fi
echo ""

# 6. 测试就绪检查
echo "6. 测试就绪检查端点..."
HTTP_CODE=$(curl -s -o /tmp/ready.json -w "%{http_code}" "$ALB_URL/ready")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 就绪检查正常 (HTTP $HTTP_CODE)"
    python3 << 'EOF'
import json
with open('/tmp/ready.json') as f:
    data = json.load(f)
    storage = data.get('checks', {}).get('storage', {})
    print(f"   📊 存储状态:")
    for name, info in storage.items():
        status = info.get('status', 'unknown')
        emoji = '✅' if status == 'ready' else '❌'
        print(f"      {emoji} {name.upper()}: {status}")
EOF
else
    echo "   ❌ 就绪检查失败 (HTTP $HTTP_CODE)"
fi
echo ""

echo "========================================="
echo "验证完成！"
echo "========================================="
echo ""
echo "📝 建议："
echo "   1. 在浏览器中打开: $ALB_URL"
echo "   2. 打开浏览器开发者工具 (F12)"
echo "   3. 查看控制台是否有 JavaScript 错误"
echo "   4. 查看网络面板确认所有请求成功"
echo ""
