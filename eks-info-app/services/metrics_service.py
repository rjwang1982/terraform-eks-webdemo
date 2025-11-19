"""
指标收集服务

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class MetricsService:
    """
    指标收集服务
    
    负责记录和管理应用的访问统计、扩展事件和资源趋势数据
    """
    
    def __init__(self):
        """初始化指标服务"""
        # 使用内存存储（简单实现）
        self._access_logs: List[Dict] = []
        self._scaling_events: List[Dict] = []
        self._resource_metrics: List[Dict] = []
        
        # 线程锁，确保线程安全
        self._access_lock = threading.Lock()
        self._scaling_lock = threading.Lock()
        self._resource_lock = threading.Lock()
        
        # 数据保留时间（小时）
        self._retention_hours = 24
        
        # 最大记录数
        self._max_access_logs = 10000
        self._max_scaling_events = 1000
        self._max_resource_metrics = 1000
    
    def record_access(self, request_info: Dict) -> None:
        """
        记录访问信息
        
        Args:
            request_info: 请求信息字典，包含：
                - timestamp: 时间戳
                - pod_name: Pod 名称
                - node_name: 节点名称
                - client_ip: 客户端 IP
                - request_path: 请求路径
                - request_method: 请求方法
                - user_agent: 用户代理
                - response_status: 响应状态码
                - response_time_ms: 响应时间（毫秒）
        """
        with self._access_lock:
            # 添加记录时间戳（如果没有提供）
            if 'timestamp' not in request_info:
                request_info['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            
            self._access_logs.append(request_info)
            
            # 限制记录数量
            if len(self._access_logs) > self._max_access_logs:
                self._access_logs = self._access_logs[-self._max_access_logs:]
            
            # 清理过期数据
            self._cleanup_old_access_logs()
    
    def get_access_stats(self, hours: int = 1) -> Dict:
        """
        获取访问统计
        
        Args:
            hours: 统计时间范围（小时）
        
        Returns:
            访问统计信息字典
        """
        with self._access_lock:
            # 计算时间范围
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 过滤时间范围内的日志
            recent_logs = [
                log for log in self._access_logs
                if self._parse_timestamp(log.get('timestamp', '')) >= cutoff_time
            ]
            
            if not recent_logs:
                return {
                    'time_range': {
                        'start': cutoff_time.isoformat() + 'Z',
                        'end': datetime.utcnow().isoformat() + 'Z',
                        'hours': hours
                    },
                    'total_requests': 0,
                    'unique_ips': 0,
                    'path_distribution': {},
                    'method_distribution': {},
                    'status_distribution': {},
                    'avg_response_time_ms': 0,
                    'error_count': 0,
                    'pod_distribution': {}
                }
            
            # 统计数据
            unique_ips = set()
            path_counts = defaultdict(int)
            method_counts = defaultdict(int)
            status_counts = defaultdict(int)
            pod_counts = defaultdict(int)
            response_times = []
            error_count = 0
            
            for log in recent_logs:
                # 客户端 IP
                if 'client_ip' in log:
                    unique_ips.add(log['client_ip'])
                
                # 请求路径
                if 'request_path' in log:
                    path_counts[log['request_path']] += 1
                
                # 请求方法
                if 'request_method' in log:
                    method_counts[log['request_method']] += 1
                
                # 响应状态
                if 'response_status' in log:
                    status = log['response_status']
                    status_counts[str(status)] += 1
                    if status >= 400:
                        error_count += 1
                
                # Pod 分布
                if 'pod_name' in log:
                    pod_counts[log['pod_name']] += 1
                
                # 响应时间
                if 'response_time_ms' in log:
                    response_times.append(log['response_time_ms'])
            
            # 计算平均响应时间
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                'time_range': {
                    'start': cutoff_time.isoformat() + 'Z',
                    'end': datetime.utcnow().isoformat() + 'Z',
                    'hours': hours
                },
                'total_requests': len(recent_logs),
                'unique_ips': len(unique_ips),
                'path_distribution': dict(path_counts),
                'method_distribution': dict(method_counts),
                'status_distribution': dict(status_counts),
                'avg_response_time_ms': round(avg_response_time, 2),
                'error_count': error_count,
                'error_rate': round(error_count / len(recent_logs) * 100, 2) if recent_logs else 0,
                'pod_distribution': dict(pod_counts)
            }
    
    def record_scaling_event(self, event: Dict) -> None:
        """
        记录扩展事件
        
        Args:
            event: 扩展事件字典，包含：
                - event_id: 事件 ID
                - event_type: 事件类型（pod_scale_up, pod_scale_down, node_scale_up, node_scale_down）
                - timestamp: 时间戳
                - trigger: 触发原因
                - details: 详细信息
                - status: 状态（pending, in_progress, completed, failed）
        """
        with self._scaling_lock:
            # 添加记录时间戳（如果没有提供）
            if 'timestamp' not in event:
                event['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            
            # 添加事件 ID（如果没有提供）
            if 'event_id' not in event:
                event['event_id'] = f"scale_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            
            self._scaling_events.append(event)
            
            # 限制记录数量
            if len(self._scaling_events) > self._max_scaling_events:
                self._scaling_events = self._scaling_events[-self._max_scaling_events:]
            
            # 清理过期数据
            self._cleanup_old_scaling_events()
    
    def get_scaling_history(self, hours: int = 24) -> List[Dict]:
        """
        获取扩展历史
        
        Args:
            hours: 历史时间范围（小时）
        
        Returns:
            扩展事件列表
        """
        with self._scaling_lock:
            # 计算时间范围
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 过滤时间范围内的事件
            recent_events = [
                event for event in self._scaling_events
                if self._parse_timestamp(event.get('timestamp', '')) >= cutoff_time
            ]
            
            # 按时间倒序排序
            recent_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return recent_events
    
    def get_resource_trends(self, hours: int = 24) -> Dict:
        """
        获取资源趋势
        
        Args:
            hours: 趋势时间范围（小时）
        
        Returns:
            资源趋势数据字典
        """
        with self._resource_lock:
            # 计算时间范围
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 过滤时间范围内的指标
            recent_metrics = [
                metric for metric in self._resource_metrics
                if self._parse_timestamp(metric.get('timestamp', '')) >= cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    'time_range': {
                        'start': cutoff_time.isoformat() + 'Z',
                        'end': datetime.utcnow().isoformat() + 'Z',
                        'hours': hours
                    },
                    'cpu_trend': [],
                    'memory_trend': [],
                    'pod_count_trend': [],
                    'node_count_trend': []
                }
            
            # 按时间排序
            recent_metrics.sort(key=lambda x: x.get('timestamp', ''))
            
            # 提取趋势数据
            cpu_trend = []
            memory_trend = []
            pod_count_trend = []
            node_count_trend = []
            
            for metric in recent_metrics:
                timestamp = metric.get('timestamp', '')
                
                if 'cpu_usage' in metric:
                    cpu_trend.append({
                        'timestamp': timestamp,
                        'value': metric['cpu_usage']
                    })
                
                if 'memory_usage' in metric:
                    memory_trend.append({
                        'timestamp': timestamp,
                        'value': metric['memory_usage']
                    })
                
                if 'pod_count' in metric:
                    pod_count_trend.append({
                        'timestamp': timestamp,
                        'value': metric['pod_count']
                    })
                
                if 'node_count' in metric:
                    node_count_trend.append({
                        'timestamp': timestamp,
                        'value': metric['node_count']
                    })
            
            return {
                'time_range': {
                    'start': cutoff_time.isoformat() + 'Z',
                    'end': datetime.utcnow().isoformat() + 'Z',
                    'hours': hours
                },
                'cpu_trend': cpu_trend,
                'memory_trend': memory_trend,
                'pod_count_trend': pod_count_trend,
                'node_count_trend': node_count_trend,
                'data_points': len(recent_metrics)
            }
    
    def record_resource_metric(self, metric: Dict) -> None:
        """
        记录资源指标
        
        Args:
            metric: 资源指标字典，包含：
                - timestamp: 时间戳
                - cpu_usage: CPU 使用率
                - memory_usage: 内存使用率
                - pod_count: Pod 数量
                - node_count: 节点数量
        """
        with self._resource_lock:
            # 添加记录时间戳（如果没有提供）
            if 'timestamp' not in metric:
                metric['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            
            self._resource_metrics.append(metric)
            
            # 限制记录数量
            if len(self._resource_metrics) > self._max_resource_metrics:
                self._resource_metrics = self._resource_metrics[-self._max_resource_metrics:]
            
            # 清理过期数据
            self._cleanup_old_resource_metrics()
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        解析时间戳字符串
        
        Args:
            timestamp_str: ISO 格式的时间戳字符串
        
        Returns:
            datetime 对象
        """
        try:
            # 移除 'Z' 后缀
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError):
            # 如果解析失败，返回很久以前的时间
            return datetime.min
    
    def _cleanup_old_access_logs(self) -> None:
        """清理过期的访问日志"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self._retention_hours)
        self._access_logs = [
            log for log in self._access_logs
            if self._parse_timestamp(log.get('timestamp', '')) >= cutoff_time
        ]
    
    def _cleanup_old_scaling_events(self) -> None:
        """清理过期的扩展事件"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self._retention_hours)
        self._scaling_events = [
            event for event in self._scaling_events
            if self._parse_timestamp(event.get('timestamp', '')) >= cutoff_time
        ]
    
    def _cleanup_old_resource_metrics(self) -> None:
        """清理过期的资源指标"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self._retention_hours)
        self._resource_metrics = [
            metric for metric in self._resource_metrics
            if self._parse_timestamp(metric.get('timestamp', '')) >= cutoff_time
        ]
    
    def get_scaling_statistics(self, hours: int = 24) -> Dict:
        """
        获取扩展统计信息
        
        Args:
            hours: 统计时间范围（小时）
        
        Returns:
            扩展统计信息字典
        """
        with self._scaling_lock:
            # 获取历史事件
            events = self.get_scaling_history(hours)
            
            if not events:
                return {
                    'time_range': {
                        'start': (datetime.utcnow() - timedelta(hours=hours)).isoformat() + 'Z',
                        'end': datetime.utcnow().isoformat() + 'Z',
                        'hours': hours
                    },
                    'total_events': 0,
                    'event_type_distribution': {},
                    'avg_response_time_seconds': 0,
                    'successful_events': 0,
                    'failed_events': 0
                }
            
            # 统计数据
            event_type_counts = defaultdict(int)
            response_times = []
            successful_count = 0
            failed_count = 0
            
            for event in events:
                # 事件类型
                if 'event_type' in event:
                    event_type_counts[event['event_type']] += 1
                
                # 响应时间
                if 'details' in event and 'duration_seconds' in event['details']:
                    response_times.append(event['details']['duration_seconds'])
                
                # 状态
                if 'status' in event:
                    if event['status'] == 'completed':
                        successful_count += 1
                    elif event['status'] == 'failed':
                        failed_count += 1
            
            # 计算平均响应时间
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                'time_range': {
                    'start': (datetime.utcnow() - timedelta(hours=hours)).isoformat() + 'Z',
                    'end': datetime.utcnow().isoformat() + 'Z',
                    'hours': hours
                },
                'total_events': len(events),
                'event_type_distribution': dict(event_type_counts),
                'avg_response_time_seconds': round(avg_response_time, 2),
                'successful_events': successful_count,
                'failed_events': failed_count,
                'success_rate': round(successful_count / len(events) * 100, 2) if events else 0
            }
    
    def clear_all_metrics(self) -> None:
        """清除所有指标数据（用于测试）"""
        with self._access_lock:
            self._access_logs.clear()
        with self._scaling_lock:
            self._scaling_events.clear()
        with self._resource_lock:
            self._resource_metrics.clear()
