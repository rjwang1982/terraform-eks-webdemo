"""
EnvironmentService 测试脚本

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-13
"""

import sys
import os
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.environment_service import EnvironmentService


def test_environment_service():
    """测试 EnvironmentService 的所有方法"""
    
    print("=" * 80)
    print("测试 EnvironmentService")
    print("=" * 80)
    
    # 创建服务实例
    env_service = EnvironmentService()
    
    # 测试 get_pod_info
    print("\n1. 测试 get_pod_info():")
    print("-" * 80)
    pod_info = env_service.get_pod_info()
    print(json.dumps(pod_info, indent=2, ensure_ascii=False))
    
    # 测试 get_node_info
    print("\n2. 测试 get_node_info():")
    print("-" * 80)
    node_info = env_service.get_node_info()
    print(json.dumps(node_info, indent=2, ensure_ascii=False))
    
    # 测试 get_cluster_info
    print("\n3. 测试 get_cluster_info():")
    print("-" * 80)
    cluster_info = env_service.get_cluster_info()
    print(json.dumps(cluster_info, indent=2, ensure_ascii=False))
    
    # 测试 get_ec2_metadata
    print("\n4. 测试 get_ec2_metadata():")
    print("-" * 80)
    ec2_info = env_service.get_ec2_metadata()
    print(json.dumps(ec2_info, indent=2, ensure_ascii=False))
    
    # 测试 get_system_info
    print("\n5. 测试 get_system_info():")
    print("-" * 80)
    system_info = env_service.get_system_info()
    print(json.dumps(system_info, indent=2, ensure_ascii=False))
    
    # 测试 get_architecture_info
    print("\n6. 测试 get_architecture_info():")
    print("-" * 80)
    arch_info = env_service.get_architecture_info()
    print(json.dumps(arch_info, indent=2, ensure_ascii=False))
    
    # 测试 get_all_environment_info
    print("\n7. 测试 get_all_environment_info():")
    print("-" * 80)
    all_info = env_service.get_all_environment_info()
    print(json.dumps(all_info, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == '__main__':
    test_environment_service()

