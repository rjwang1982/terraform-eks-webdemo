#!/bin/bash
# 测试所有页面
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com

BASE_URL="http://k8s-rjwebdem-eksinfoa-276a74cf51-1382595953.ap-southeast-1.elb.amazonaws.com"

echo "========================================="
echo "测试所有页面功能"
echo "========================================="

# 测试页面列表
pages=(
    "/"
    "/storage/"
    "/ebs/"
    "/efs/"
    "/s3/"
    "/network/"
    "/resources/"
    "/stress/"
    "/scaling/"
)

page_names=(
    "首页"
    "存储概览"
    "EBS 演示"
    "EFS 演示"
    "S3 演示"
    "网络信息"
    "资源信息"
    "压力测试"
    "扩展监控"
)

# 测试每个页面
for i in "${!pages[@]}"; do
    page="${pages[$i]}"
    name="${page_names[$i]}"
    
    echo ""
    echo "测试: $name ($page)"
    
    # 测试 HTML 响应
    response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${page}")
    http_code=$(echo "$response" | tail -n 1)
    content=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        if echo "$content" | grep -q "<title>"; then
            echo "   ✅ 返回 HTML (HTTP $http_code)"
        else
            echo "   ⚠️  返回 200 但不是 HTML"
        fi
    else
        echo "   ❌ HTTP $http_code"
    fi
done

echo ""
echo "========================================="
echo "测试完成"
echo "========================================="
