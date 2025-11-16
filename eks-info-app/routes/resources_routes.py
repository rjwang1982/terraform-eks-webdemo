"""
Kubernetes 资源信息路由

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from services.kubernetes_service import KubernetesService
from config import Config
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
resources_bp = Blueprint('resources', __name__, url_prefix='/resources')

# 初始化服务
try:
    k8s_service = KubernetesService()
    service_available = True
except Exception as e:
    k8s_service = None
    service_available = False
    logger.error(f"Kubernetes 服务初始化失败: {str(e)}")


@resources_bp.route('/', methods=['GET'])
def resources_info():
    """
    Kubernetes 资源信息页面
    
    显示完整的 Kubernetes 资源信息，包括：
    - 命名空间中的 Pod 列表
    - Service 信息
    - Deployment 配置
    - 节点资源使用情况
    - PV 和 PVC 状态
    
    需求: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    # 检查是否请求 HTML 格式（浏览器访问）
    if request.accept_mimetypes.best_match(['text/html', 'application/json']) == 'text/html':
        # 返回 HTML 页面
        return render_template('resources.html')
    
    # 否则返回 JSON 数据（API 调用）
    if not service_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = Config.POD_NAMESPACE
        
        # 获取 Pod 列表
        pods = k8s_service.get_pods(namespace=namespace)
        
        # 获取 Service 列表
        services = k8s_service.get_services(namespace=namespace)
        
        # 获取 Deployment 列表
        deployments = k8s_service.get_deployments(namespace=namespace)
        
        # 获取节点列表
        nodes = k8s_service.get_nodes()
        
        # 获取 PVC 列表
        pvcs = k8s_service.get_pvcs(namespace=namespace)
        
        # 获取 HPA 信息
        hpa_info = k8s_service.get_hpa(namespace=namespace)
        
        # 计算资源统计
        pod_stats = {
            'total': len(pods),
            'running': sum(1 for p in pods if p.get('status') == 'Running'),
            'pending': sum(1 for p in pods if p.get('status') == 'Pending'),
            'failed': sum(1 for p in pods if p.get('status') == 'Failed'),
            'succeeded': sum(1 for p in pods if p.get('status') == 'Succeeded')
        }
        
        node_stats = {
            'total': len(nodes),
            'ready': sum(1 for n in nodes if n.get('status') == 'Ready'),
            'not_ready': sum(1 for n in nodes if n.get('status') != 'Ready')
        }
        
        # 构建响应
        response_data = {
            'namespace': namespace,
            'pods': pods,
            'services': services,
            'deployments': deployments,
            'nodes': nodes,
            'pvcs': pvcs,
            'hpa': hpa_info,
            'statistics': {
                'pods': pod_stats,
                'nodes': node_stats,
                'services': len(services),
                'deployments': len(deployments),
                'pvcs': len(pvcs)
            },
            'current_pod': {
                'name': Config.POD_NAME,
                'namespace': Config.POD_NAMESPACE,
                'node': Config.NODE_NAME
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"获取 Kubernetes 资源信息时发生错误: {str(e)}", exc_info=True)
        return jsonify({
            'error': True,
            'error_type': 'resources_info_error',
            'message': '获取 Kubernetes 资源信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@resources_bp.route('/pods', methods=['GET'])
def pods_list():
    """
    获取 Pod 列表
    
    查询参数:
    - namespace: 命名空间（默认使用当前命名空间）
    - label_selector: 标签选择器（可选）
    
    需求: 6.1
    """
    if not service_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        label_selector = request.args.get('label_selector')
        
        pods = k8s_service.get_pods(namespace=namespace, label_selector=label_selector)
        
        return jsonify({
            'success': True,
            'pods': pods,
            'count': len(pods),
            'namespace': namespace,
            'label_selector': label_selector,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        logger.error(f"获取 Pod 列表时发生错误: {str(e)}")
        return jsonify({
            'error': True,
            'error_type': 'pods_error',
            'message': '获取 Pod 列表时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@resources_bp.route('/services', methods=['GET'])
def services_list():
    """
    获取 Service 列表
    
    查询参数:
    - namespace: 命名空间（默认使用当前命名空间）
    
    需求: 6.2
    """
    if not service_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        
        services = k8s_service.get_services(namespace=namespace)
        
        return jsonify({
            'success': True,
            'services': services,
            'count': len(services),
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        logger.error(f"获取 Service 列表时发生错误: {str(e)}")
        return jsonify({
            'error': True,
            'error_type': 'services_error',
            'message': '获取 Service 列表时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@resources_bp.route('/deployments', methods=['GET'])
def deployments_list():
    """
    获取 Deployment 列表
    
    查询参数:
    - namespace: 命名空间（默认使用当前命名空间）
    
    需求: 6.3
    """
    if not service_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        
        deployments = k8s_service.get_deployments(namespace=namespace)
        
        return jsonify({
            'success': True,
            'deployments': deployments,
            'count': len(deployments),
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        logger.error(f"获取 Deployment 列表时发生错误: {str(e)}")
        return jsonify({
            'error': True,
            'error_type': 'deployments_error',
            'message': '获取 Deployment 列表时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@resources_bp.route('/nodes', methods=['GET'])
def nodes_list():
    """
    获取节点列表和资源使用情况
    
    需求: 6.4
    """
    if not service_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        nodes = k8s_service.get_nodes()
        
        # 为每个节点添加 Pod 分布信息
        for node in nodes:
            node_name = node['name']
            # 获取运行在该节点上的 Pod
            all_pods = k8s_service.get_pods(namespace='')  # 获取所有命名空间的 Pod
            node_pods = [p for p in all_pods if p.get('node_name') == node_name]
            
            node['pod_count'] = len(node_pods)
            node['running_pods'] = sum(1 for p in node_pods if p.get('status') == 'Running')
        
        return jsonify({
            'success': True,
            'nodes': nodes,
            'count': len(nodes),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        logger.error(f"获取节点列表时发生错误: {str(e)}")
        return jsonify({
            'error': True,
            'error_type': 'nodes_error',
            'message': '获取节点列表时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@resources_bp.route('/pvcs', methods=['GET'])
def pvcs_list():
    """
    获取 PersistentVolumeClaim 列表
    
    查询参数:
    - namespace: 命名空间（默认使用当前命名空间）
    
    需求: 6.5
    """
    if not service_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        
        pvcs = k8s_service.get_pvcs(namespace=namespace)
        
        return jsonify({
            'success': True,
            'pvcs': pvcs,
            'count': len(pvcs),
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        logger.error(f"获取 PVC 列表时发生错误: {str(e)}")
        return jsonify({
            'error': True,
            'error_type': 'pvcs_error',
            'message': '获取 PVC 列表时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@resources_bp.route('/hpa', methods=['GET'])
def hpa_info():
    """
    获取 HPA (Horizontal Pod Autoscaler) 信息
    
    查询参数:
    - namespace: 命名空间（默认使用当前命名空间）
    - name: HPA 名称（可选）
    """
    if not service_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        name = request.args.get('name')
        
        hpa_data = k8s_service.get_hpa(namespace=namespace, name=name)
        
        return jsonify({
            'success': True,
            'hpa': hpa_data,
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        logger.error(f"获取 HPA 信息时发生错误: {str(e)}")
        return jsonify({
            'error': True,
            'error_type': 'hpa_error',
            'message': '获取 HPA 信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@resources_bp.route('/events', methods=['GET'])
def events_list():
    """
    获取事件列表
    
    查询参数:
    - namespace: 命名空间（默认使用当前命名空间）
    - limit: 返回的最大事件数（默认 50）
    """
    if not service_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        namespace = request.args.get('namespace', Config.POD_NAMESPACE)
        limit = int(request.args.get('limit', 50))
        
        events = k8s_service.get_events(namespace=namespace, limit=limit)
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events),
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        logger.error(f"获取事件列表时发生错误: {str(e)}")
        return jsonify({
            'error': True,
            'error_type': 'events_error',
            'message': '获取事件列表时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@resources_bp.route('/current-pod', methods=['GET'])
def current_pod_info():
    """
    获取当前 Pod 的详细信息
    """
    if not service_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        pod_info = k8s_service.get_current_pod()
        
        return jsonify({
            'success': True,
            'pod': pod_info,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        logger.error(f"获取当前 Pod 信息时发生错误: {str(e)}")
        return jsonify({
            'error': True,
            'error_type': 'current_pod_error',
            'message': '获取当前 Pod 信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@resources_bp.route('/health', methods=['GET'])
def resources_health():
    """
    Kubernetes 资源服务健康检查
    """
    if not service_available:
        return jsonify({
            'healthy': False,
            'error': 'Kubernetes 服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 简单检查：尝试获取当前 Pod 信息
        pod_info = k8s_service.get_current_pod()
        
        if 'error' in pod_info:
            return jsonify({
                'healthy': False,
                'error': 'Kubernetes API 不可用',
                'details': pod_info.get('error'),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503
        
        return jsonify({
            'healthy': True,
            'services': {
                'kubernetes_service': True
            },
            'current_pod': pod_info.get('name', 'unknown'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        return jsonify({
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500
