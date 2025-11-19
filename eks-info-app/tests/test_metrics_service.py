"""
MetricsService 测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import pytest
from datetime import datetime, timedelta
from services.metrics_service import MetricsService


def test_metrics_service_initialization():
    """测试 MetricsService 初始化"""
    service = MetricsService()
    assert service is not None
    assert service._access_logs == []
    assert service._scaling_events == []
    assert service._resource_metrics == []


def test_record_access():
    """测试记录访问信息"""
    service = MetricsService()
    
    # 记录访问
    request_info = {
        'pod_name': 'test-pod',
        'node_name': 'test-node',
        'client_ip': '192.168.1.1',
        'request_path': '/test',
        'request_method': 'GET',
        'response_status': 200,
        'response_time_ms': 50
    }
    
    service.record_access(request_info)
    
    # 验证记录
    assert len(service._access_logs) == 1
    assert service._access_logs[0]['pod_name'] == 'test-pod'
    assert 'timestamp' in service._access_logs[0]


def test_get_access_stats():
    """测试获取访问统计"""
    service = MetricsService()
    
    # 记录多个访问
    for i in range(5):
        service.record_access({
            'pod_name': f'pod-{i}',
            'client_ip': f'192.168.1.{i}',
            'request_path': '/test',
            'request_method': 'GET',
            'response_status': 200,
            'response_time_ms': 50 + i
        })
    
    # 获取统计
    stats = service.get_access_stats(hours=1)
    
    assert stats['total_requests'] == 5
    assert stats['unique_ips'] == 5
    assert stats['path_distribution']['/test'] == 5
    assert stats['avg_response_time_ms'] > 0


def test_record_scaling_event():
    """测试记录扩展事件"""
    service = MetricsService()
    
    # 记录扩展事件
    event = {
        'event_type': 'pod_scale_up',
        'trigger': 'cpu_threshold_exceeded',
        'details': {
            'replicas_before': 3,
            'replicas_after': 5,
            'duration_seconds': 45
        },
        'status': 'completed'
    }
    
    service.record_scaling_event(event)
    
    # 验证记录
    assert len(service._scaling_events) == 1
    assert service._scaling_events[0]['event_type'] == 'pod_scale_up'
    assert 'timestamp' in service._scaling_events[0]
    assert 'event_id' in service._scaling_events[0]


def test_get_scaling_history():
    """测试获取扩展历史"""
    service = MetricsService()
    
    # 记录多个扩展事件
    for i in range(3):
        service.record_scaling_event({
            'event_type': 'pod_scale_up' if i % 2 == 0 else 'pod_scale_down',
            'trigger': 'test',
            'status': 'completed'
        })
    
    # 获取历史
    history = service.get_scaling_history(hours=24)
    
    assert len(history) == 3
    # 验证按时间倒序排序
    for i in range(len(history) - 1):
        assert history[i]['timestamp'] >= history[i + 1]['timestamp']


def test_record_resource_metric():
    """测试记录资源指标"""
    service = MetricsService()
    
    # 记录资源指标
    metric = {
        'cpu_usage': 75.5,
        'memory_usage': 60.2,
        'pod_count': 5,
        'node_count': 3
    }
    
    service.record_resource_metric(metric)
    
    # 验证记录
    assert len(service._resource_metrics) == 1
    assert service._resource_metrics[0]['cpu_usage'] == 75.5
    assert 'timestamp' in service._resource_metrics[0]


def test_get_resource_trends():
    """测试获取资源趋势"""
    service = MetricsService()
    
    # 记录多个资源指标
    for i in range(5):
        service.record_resource_metric({
            'cpu_usage': 50 + i * 5,
            'memory_usage': 40 + i * 3,
            'pod_count': 3 + i,
            'node_count': 2
        })
    
    # 获取趋势
    trends = service.get_resource_trends(hours=24)
    
    assert len(trends['cpu_trend']) == 5
    assert len(trends['memory_trend']) == 5
    assert len(trends['pod_count_trend']) == 5
    assert len(trends['node_count_trend']) == 5
    assert trends['data_points'] == 5


def test_get_scaling_statistics():
    """测试获取扩展统计"""
    service = MetricsService()
    
    # 记录多个扩展事件
    for i in range(5):
        service.record_scaling_event({
            'event_type': 'pod_scale_up' if i < 3 else 'pod_scale_down',
            'trigger': 'test',
            'details': {
                'duration_seconds': 40 + i * 5
            },
            'status': 'completed' if i < 4 else 'failed'
        })
    
    # 获取统计
    stats = service.get_scaling_statistics(hours=24)
    
    assert stats['total_events'] == 5
    assert stats['event_type_distribution']['pod_scale_up'] == 3
    assert stats['event_type_distribution']['pod_scale_down'] == 2
    assert stats['successful_events'] == 4
    assert stats['failed_events'] == 1
    assert stats['avg_response_time_seconds'] > 0


def test_clear_all_metrics():
    """测试清除所有指标"""
    service = MetricsService()
    
    # 添加一些数据
    service.record_access({'test': 'data'})
    service.record_scaling_event({'test': 'data'})
    service.record_resource_metric({'test': 'data'})
    
    # 清除
    service.clear_all_metrics()
    
    # 验证清除
    assert len(service._access_logs) == 0
    assert len(service._scaling_events) == 0
    assert len(service._resource_metrics) == 0


def test_thread_safety():
    """测试线程安全性"""
    import threading
    
    service = MetricsService()
    
    def record_data():
        for i in range(10):
            service.record_access({'test': i})
            service.record_scaling_event({'test': i})
            service.record_resource_metric({'test': i})
    
    # 创建多个线程
    threads = [threading.Thread(target=record_data) for _ in range(5)]
    
    # 启动线程
    for thread in threads:
        thread.start()
    
    # 等待完成
    for thread in threads:
        thread.join()
    
    # 验证数据完整性
    assert len(service._access_logs) == 50
    assert len(service._scaling_events) == 50
    assert len(service._resource_metrics) == 50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
