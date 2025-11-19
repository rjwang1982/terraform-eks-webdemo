#!/usr/bin/env python3
"""
MetricsService 基本功能测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

from services.metrics_service import MetricsService

def test_basic_functionality():
    """测试基本功能"""
    print("开始测试 MetricsService...")
    
    # 测试初始化
    service = MetricsService()
    print("✓ MetricsService 初始化成功")
    
    # 测试记录访问
    service.record_access({
        'pod_name': 'test-pod',
        'client_ip': '192.168.1.1',
        'request_path': '/test',
        'response_status': 200,
        'response_time_ms': 50
    })
    print("✓ 记录访问信息成功")
    
    # 测试获取统计
    stats = service.get_access_stats(hours=1)
    assert stats['total_requests'] == 1
    print(f"✓ 获取访问统计成功: {stats['total_requests']} 个请求")
    
    # 测试记录扩展事件
    service.record_scaling_event({
        'event_type': 'pod_scale_up',
        'trigger': 'test',
        'status': 'completed',
        'details': {
            'replicas_before': 3,
            'replicas_after': 5
        }
    })
    print("✓ 记录扩展事件成功")
    
    # 测试获取扩展历史
    history = service.get_scaling_history(hours=24)
    assert len(history) == 1
    print(f"✓ 获取扩展历史成功: {len(history)} 个事件")
    
    # 测试记录资源指标
    service.record_resource_metric({
        'cpu_usage': 75.5,
        'memory_usage': 60.2,
        'pod_count': 5,
        'node_count': 3
    })
    print("✓ 记录资源指标成功")
    
    # 测试获取资源趋势
    trends = service.get_resource_trends(hours=24)
    assert trends['data_points'] == 1
    print(f"✓ 获取资源趋势成功: {trends['data_points']} 个数据点")
    
    # 测试获取扩展统计
    stats = service.get_scaling_statistics(hours=24)
    assert stats['total_events'] == 1
    print(f"✓ 获取扩展统计成功: {stats['total_events']} 个事件")
    
    # 测试清除功能
    service.clear_all_metrics()
    assert len(service._access_logs) == 0
    print("✓ 清除所有指标成功")
    
    print("\n所有测试通过！✓")

if __name__ == '__main__':
    test_basic_functionality()
