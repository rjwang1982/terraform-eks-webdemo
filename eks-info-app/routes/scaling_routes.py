"""
扩展监控路由

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from services.kubernetes_service import KubernetesService
from services.metrics_service import MetricsService
from config import Config

# 创建蓝图
scaling_bp = Blueprint('scaling', __name__, url_prefix='/scaling')

# 初始化服务
try:
    k8s_service = KubernetesService()
    k8s_available = True
except Exception as e:
    k8s_service = None
    k8s_available = False
    print(f"Kubernetes 服务初始化失败: {str(e)}")

# 初始化指标服务（全局单例）
metrics_service = MetricsService()


@scaling_bp.route('/', methods=['GET'])
def scaling_overview():
    """
    扩展监控页面
    
    显示当前集群的扩展状态，包括：
    - 当前节点列表和资源使用
    - 每个节点上的 Pod 分布
    - Pending 状态的 Pod
    - HPA 当前状态和副本数
    """
    # 检查是否请求 HTML 格式（浏览器访问）
    if request.accept_mimetypes.best_match(['text/html', 'application/json']) == 'text/html':
        # 返回 HTML 页面
        return render_template('scaling.html')
    
    # 否则返回 JSON 数据（API 调用）
    if not k8s_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = Config.POD_NAMESPACE
        
        # 获取节点列表
        nodes = k8s_service.get_nodes()
        
        # 获取所有 Pod
        pods = k8s_service.get_pods(namespace=namespace)
        
        # 按节点分组 Pod
        pods_by_node = {}
        pending_pods = []
        
        for pod in pods:
            if pod['status'] == 'Pending':
                pending_pods.append(pod)
            else:
                node_name = pod.get('node_name', 'unknown')
                if node_name not in pods_by_node:
                    pods_by_node[node_name] = []
                pods_by_node[node_name].append(pod)
        
        # 为每个节点添加 Pod 信息
        nodes_with_pods = []
        for node in nodes:
            node_pods = pods_by_node.get(node['name'], [])
            node_info = {
                **node,
                'pod_count': len(node_pods),
                'pods': node_pods
            }
            nodes_with_pods.append(node_info)
        
        # 获取 HPA 信息
        hpa_info = k8s_service.get_hpa(namespace=namespace)
        
        # 获取 Deployment 信息
        deployments = k8s_service.get_deployments(namespace=namespace)
        
        return jsonify({
            'nodes': nodes_with_pods,
            'node_count': len(nodes),
            'total_pods': len(pods),
            'pending_pods': pending_pods,
            'pending_count': len(pending_pods),
            'hpa': hpa_info,
            'deployments': deployments,
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'scaling_overview_error',
            'message': '获取扩展监控信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/nodes', methods=['GET'])
def get_nodes():
    """
    获取节点列表和资源使用情况
    
    返回所有节点的详细信息和资源使用情况
    """
    if not k8s_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        nodes = k8s_service.get_nodes()
        
        return jsonify({
            'success': True,
            'nodes': nodes,
            'count': len(nodes),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'nodes_error',
            'message': '获取节点信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/pods', methods=['GET'])
def get_pods():
    """
    获取 Pod 列表和分布情况
    
    返回命名空间中所有 Pod 的信息，包括按节点分组
    """
    if not k8s_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        
        # 获取所有 Pod
        pods = k8s_service.get_pods(namespace=namespace)
        
        # 按节点分组
        pods_by_node = {}
        pending_pods = []
        
        for pod in pods:
            if pod['status'] == 'Pending':
                pending_pods.append(pod)
            else:
                node_name = pod.get('node_name', 'unknown')
                if node_name not in pods_by_node:
                    pods_by_node[node_name] = []
                pods_by_node[node_name].append(pod)
        
        # 按状态分组
        pods_by_status = {}
        for pod in pods:
            status = pod['status']
            if status not in pods_by_status:
                pods_by_status[status] = []
            pods_by_status[status].append(pod)
        
        return jsonify({
            'success': True,
            'pods': pods,
            'total_count': len(pods),
            'pods_by_node': pods_by_node,
            'pods_by_status': pods_by_status,
            'pending_pods': pending_pods,
            'pending_count': len(pending_pods),
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'pods_error',
            'message': '获取 Pod 信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/hpa', methods=['GET'])
def get_hpa():
    """
    获取 HPA 状态
    
    返回 HPA 的当前状态和副本数信息
    """
    if not k8s_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        name = request.args.get('name')
        
        hpa_info = k8s_service.get_hpa(namespace=namespace, name=name)
        
        return jsonify({
            'success': True,
            'hpa': hpa_info,
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'hpa_error',
            'message': '获取 HPA 信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/pending', methods=['GET'])
def get_pending_pods():
    """
    获取 Pending 状态的 Pod
    
    返回所有处于 Pending 状态的 Pod，这些 Pod 可能触发节点扩展
    """
    if not k8s_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        
        # 获取所有 Pod
        pods = k8s_service.get_pods(namespace=namespace)
        
        # 过滤 Pending 状态的 Pod
        pending_pods = [pod for pod in pods if pod['status'] == 'Pending']
        
        # 获取相关事件
        events = k8s_service.get_events(namespace=namespace, limit=20)
        
        # 过滤与 Pending Pod 相关的事件
        pending_events = []
        for event in events:
            if event['object']['kind'] == 'Pod':
                for pod in pending_pods:
                    if event['object']['name'] == pod['name']:
                        pending_events.append(event)
                        break
        
        return jsonify({
            'success': True,
            'pending_pods': pending_pods,
            'count': len(pending_pods),
            'related_events': pending_events,
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'pending_pods_error',
            'message': '获取 Pending Pod 信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/events', methods=['GET'])
def get_scaling_events():
    """
    获取扩展相关的事件
    
    返回与扩展相关的 Kubernetes 事件
    """
    if not k8s_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        limit = int(request.args.get('limit', 50))
        
        # 获取事件
        events = k8s_service.get_events(namespace=namespace, limit=limit)
        
        # 过滤扩展相关的事件
        scaling_keywords = ['scale', 'hpa', 'autoscaler', 'replica']
        scaling_events = []
        
        for event in events:
            message_lower = event['message'].lower()
            reason_lower = event['reason'].lower()
            
            if any(keyword in message_lower or keyword in reason_lower for keyword in scaling_keywords):
                scaling_events.append(event)
        
        return jsonify({
            'success': True,
            'events': scaling_events,
            'count': len(scaling_events),
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'events_error',
            'message': '获取扩展事件时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/refresh', methods=['POST'])
def refresh_status():
    """
    刷新扩展状态
    
    手动触发状态刷新，并记录当前的资源指标
    """
    if not k8s_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = Config.POD_NAMESPACE
        
        # 获取当前状态
        nodes = k8s_service.get_nodes()
        pods = k8s_service.get_pods(namespace=namespace)
        hpa_info = k8s_service.get_hpa(namespace=namespace)
        
        # 记录资源指标
        metric = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'node_count': len(nodes),
            'pod_count': len(pods)
        }
        
        # 如果有 HPA 信息，记录副本数
        if isinstance(hpa_info, dict) and 'items' in hpa_info:
            for hpa in hpa_info['items']:
                if 'current_replicas' in hpa:
                    metric['hpa_current_replicas'] = hpa['current_replicas']
                if 'desired_replicas' in hpa:
                    metric['hpa_desired_replicas'] = hpa['desired_replicas']
        
        metrics_service.record_resource_metric(metric)
        
        return jsonify({
            'success': True,
            'message': '状态已刷新',
            'current_state': {
                'node_count': len(nodes),
                'pod_count': len(pods),
                'hpa': hpa_info
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'refresh_error',
            'message': '刷新状态时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500



@scaling_bp.route('/history', methods=['GET'])
def scaling_history():
    """
    扩展历史页面
    
    显示过去一段时间的扩展历史，包括：
    - Pod 数量变化图表
    - 节点数量变化图表
    - 扩展事件列表
    - 扩展响应时间统计
    - 资源使用率趋势
    """
    try:
        # 获取时间范围参数（默认 24 小时）
        hours = int(request.args.get('hours', 24))
        
        # 获取资源趋势
        resource_trends = metrics_service.get_resource_trends(hours=hours)
        
        # 获取扩展历史
        scaling_events = metrics_service.get_scaling_history(hours=hours)
        
        # 获取扩展统计
        scaling_stats = metrics_service.get_scaling_statistics(hours=hours)
        
        # 获取访问统计（用于关联分析）
        access_stats = metrics_service.get_access_stats(hours=hours)
        
        return jsonify({
            'resource_trends': resource_trends,
            'scaling_events': scaling_events,
            'scaling_statistics': scaling_stats,
            'access_statistics': access_stats,
            'time_range': {
                'hours': hours,
                'start': resource_trends['time_range']['start'],
                'end': resource_trends['time_range']['end']
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'history_error',
            'message': '获取扩展历史时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/history/events', methods=['GET'])
def get_history_events():
    """
    获取扩展事件历史
    
    返回指定时间范围内的所有扩展事件
    """
    try:
        hours = int(request.args.get('hours', 24))
        
        # 获取扩展事件
        events = metrics_service.get_scaling_history(hours=hours)
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events),
            'time_range': {
                'hours': hours
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'history_events_error',
            'message': '获取扩展事件历史时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/history/trends', methods=['GET'])
def get_resource_trends():
    """
    获取资源使用趋势
    
    返回 CPU、内存、Pod 数量、节点数量的历史趋势数据
    """
    try:
        hours = int(request.args.get('hours', 24))
        
        # 获取资源趋势
        trends = metrics_service.get_resource_trends(hours=hours)
        
        return jsonify({
            'success': True,
            'trends': trends,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'trends_error',
            'message': '获取资源趋势时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/history/statistics', methods=['GET'])
def get_scaling_statistics():
    """
    获取扩展统计信息
    
    返回扩展事件的统计分析，包括：
    - 总事件数
    - 事件类型分布
    - 平均响应时间
    - 成功/失败率
    """
    try:
        hours = int(request.args.get('hours', 24))
        
        # 获取扩展统计
        stats = metrics_service.get_scaling_statistics(hours=hours)
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'statistics_error',
            'message': '获取扩展统计时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/history/chart-data', methods=['GET'])
def get_chart_data():
    """
    获取图表数据
    
    返回格式化的图表数据，用于前端可视化
    """
    try:
        hours = int(request.args.get('hours', 24))
        
        # 获取资源趋势
        trends = metrics_service.get_resource_trends(hours=hours)
        
        # 格式化为图表数据
        chart_data = {
            'pod_count_chart': {
                'labels': [point['timestamp'] for point in trends['pod_count_trend']],
                'data': [point['value'] for point in trends['pod_count_trend']],
                'label': 'Pod 数量'
            },
            'node_count_chart': {
                'labels': [point['timestamp'] for point in trends['node_count_trend']],
                'data': [point['value'] for point in trends['node_count_trend']],
                'label': '节点数量'
            },
            'cpu_usage_chart': {
                'labels': [point['timestamp'] for point in trends['cpu_trend']],
                'data': [point['value'] for point in trends['cpu_trend']],
                'label': 'CPU 使用率 (%)'
            },
            'memory_usage_chart': {
                'labels': [point['timestamp'] for point in trends['memory_trend']],
                'data': [point['value'] for point in trends['memory_trend']],
                'label': '内存使用率 (%)'
            }
        }
        
        return jsonify({
            'success': True,
            'chart_data': chart_data,
            'time_range': trends['time_range'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'chart_data_error',
            'message': '获取图表数据时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/record-event', methods=['POST'])
def record_scaling_event():
    """
    记录扩展事件
    
    允许手动记录扩展事件（用于测试或外部集成）
    """
    try:
        # 获取请求数据
        event_data = request.get_json()
        
        if not event_data:
            return jsonify({
                'error': True,
                'error_type': 'invalid_request',
                'message': '请求数据为空',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        
        # 验证必需字段
        required_fields = ['event_type', 'trigger']
        for field in required_fields:
            if field not in event_data:
                return jsonify({
                    'error': True,
                    'error_type': 'missing_field',
                    'message': f'缺少必需字段: {field}',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 400
        
        # 记录事件
        metrics_service.record_scaling_event(event_data)
        
        return jsonify({
            'success': True,
            'message': '扩展事件已记录',
            'event_id': event_data.get('event_id', 'auto-generated'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'record_event_error',
            'message': '记录扩展事件时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@scaling_bp.route('/metrics/record', methods=['POST'])
def record_resource_metric():
    """
    记录资源指标
    
    允许手动记录资源指标（用于测试或外部集成）
    """
    try:
        # 获取请求数据
        metric_data = request.get_json()
        
        if not metric_data:
            return jsonify({
                'error': True,
                'error_type': 'invalid_request',
                'message': '请求数据为空',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        
        # 记录指标
        metrics_service.record_resource_metric(metric_data)
        
        return jsonify({
            'success': True,
            'message': '资源指标已记录',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'record_metric_error',
            'message': '记录资源指标时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500
