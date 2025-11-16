#!/bin/bash

# 获取 ALB 主机名
ALB_HOSTNAME=$(kubectl get ingress rj-py-webdemo-ingress -n rj-webdemo -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)

if [ -n "$ALB_HOSTNAME" ] && [ "$ALB_HOSTNAME" != "null" ]; then
    echo "🌐 应用访问地址: http://$ALB_HOSTNAME"
    
    # 测试连接
    echo "正在测试连接..."
    if curl -s --connect-timeout 10 "http://$ALB_HOSTNAME" > /dev/null; then
        echo "✅ 应用已就绪，可以访问！"
    else
        echo "⏳ ALB 可能还在初始化中，请稍等几分钟后再试"
    fi
else
    echo "⏳ ALB 还在创建中，请稍后再试"
fi
