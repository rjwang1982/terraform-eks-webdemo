"""
KubernetesService 测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-13
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 设置测试环境变量
os.environ['POD_NAME'] = os.environ.get('POD_NAME', 'test-pod')
os.environ['POD_NAMESPACE'] = os.environ.get('POD_NAMESPACE', 'default')
os.environ['NODE_NAME'] = os.environ.get('NODE_NAME', 'test-node')

from services.kubernetes_service import KubernetesService


def test_kubernetes_service():
    """测试 KubernetesService 的基本功能"""
    
    print("=" * 80)
    print("测试 KubernetesService")
    print("=" * 80)
    
    try:
        # 初始化服务
        print("\n1. 初始化 KubernetesService...")
        k8s_service = KubernetesService()
        print("✓ KubernetesService 初始化成功")
        
        # 测试获取当前 Pod
        print("\n2. 测试 get_current_pod()...")
        current_pod = k8s_service.get_current_pod()
        print(f"✓ 当前 Pod: {current_pod.get('name', 'unknown')}")
        print(f"  命名空间: {current_pod.get('namespace', 'unknown')}")
        print(f"  状态: {current_pod.get('status', 'unknown')}")
        if 'error' in current_pod:
            print(f"  注意: {current_pod['error']}")
        
        # 测试获取 Pod 列表
        print("\n3. 测试 get_pods()...")
        namespace = os.environ.get('POD_NAMESPACE', 'default')
        pods = k8s_service.get_pods(namespace=namespace)
        print(f"✓ 找到 {len(pods)} 个 Pod (namespace={namespace})")
        if pods:
            print(f"  示例 Pod: {pods[0]['name']} - 状态: {pods[0]['status']}")
        
        # 测试获取节点列表
        print("\n4. 测试 get_nodes()...")
        nodes = k8s_service.get_nodes()
        print(f"✓ 找到 {len(nodes)} 个节点")
        if nodes:
            print(f"  示例节点: {nodes[0]['name']}")
            print(f"    状态: {nodes[0]['status']}")
            print(f"    角色: {', '.join(nodes[0]['roles'])}")
            print(f"    架构: {nodes[0]['architecture']}")
        
        # 测试获取 Service 列表
        print("\n5. 测试 get_services()...")
        services = k8s_service.get_services(namespace=namespace)
        print(f"✓ 找到 {len(services)} 个 Service (namespace={namespace})")
        if services:
            print(f"  示例 Service: {services[0]['name']} - 类型: {services[0]['type']}")
        
        # 测试获取 Deployment 列表
        print("\n6. 测试 get_deployments()...")
        deployments = k8s_service.get_deployments(namespace=namespace)
        print(f"✓ 找到 {len(deployments)} 个 Deployment (namespace={namespace})")
        if deployments:
            deploy = deployments[0]
            print(f"  示例 Deployment: {deploy['name']}")
            print(f"    副本: {deploy['ready_replicas']}/{deploy['replicas']}")
        
        # 测试获取 HPA
        print("\n7. 测试 get_hpa()...")
        hpa_result = k8s_service.get_hpa(namespace=namespace)
        if 'error' not in hpa_result:
            print(f"✓ 找到 {hpa_result.get('count', 0)} 个 HPA (namespace={namespace})")
            if hpa_result.get('items'):
                hpa = hpa_result['items'][0]
                print(f"  示例 HPA: {hpa['name']}")
                print(f"    副本范围: {hpa['min_replicas']}-{hpa['max_replicas']}")
                print(f"    当前副本: {hpa['current_replicas']}")
        else:
            print(f"  注意: {hpa_result['error']}")
        
        # 测试获取 PVC 列表
        print("\n8. 测试 get_pvcs()...")
        pvcs = k8s_service.get_pvcs(namespace=namespace)
        print(f"✓ 找到 {len(pvcs)} 个 PVC (namespace={namespace})")
        if pvcs:
            pvc = pvcs[0]
            print(f"  示例 PVC: {pvc['name']}")
            print(f"    状态: {pvc['status']}")
            print(f"    容量: {pvc['capacity']}")
        
        # 测试获取事件列表
        print("\n9. 测试 get_events()...")
        events = k8s_service.get_events(namespace=namespace, limit=5)
        print(f"✓ 找到 {len(events)} 个最近事件 (namespace={namespace})")
        if events:
            event = events[0]
            print(f"  最近事件: {event['reason']}")
            print(f"    类型: {event['type']}")
            print(f"    对象: {event['object']['kind']}/{event['object']['name']}")
        
        print("\n" + "=" * 80)
        print("✓ 所有测试完成！")
        print("=" * 80)
        
        return True
    
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_kubernetes_service()
    sys.exit(0 if success else 1)
