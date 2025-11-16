"""
测试 Kubernetes 资源信息路由

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from routes.resources_routes import resources_bp
from flask import Flask


@pytest.fixture
def app():
    """创建测试应用"""
    app = Flask(__name__)
    app.register_blueprint(resources_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def mock_k8s_service():
    """模拟 Kubernetes 服务"""
    with patch('routes.resources_routes.k8s_service') as mock:
        # 模拟 get_pods 方法
        mock.get_pods.return_value = [
            {
                'name': 'test-pod-1',
                'namespace': 'default',
                'status': 'Running',
                'ip': '10.0.0.1',
                'node_name': 'node-1',
                'labels': {'app': 'test'},
                'created_at': '2025-11-14T10:00:00.000Z',
                'restart_count': 0,
                'ready': True
            }
        ]
        
        # 模拟 get_services 方法
        mock.get_services.return_value = [
            {
                'name': 'test-service',
                'namespace': 'default',
                'type': 'ClusterIP',
                'cluster_ip': '10.100.0.1',
                'external_ips': ['<none>'],
                'ports': [{'name': 'http', 'port': 80, 'target_port': '8080', 'protocol': 'TCP', 'node_port': None}],
                'selector': {'app': 'test'},
                'created_at': '2025-11-14T10:00:00.000Z'
            }
        ]
        
        # 模拟 get_deployments 方法
        mock.get_deployments.return_value = [
            {
                'name': 'test-deployment',
                'namespace': 'default',
                'replicas': 3,
                'ready_replicas': 3,
                'available_replicas': 3,
                'updated_replicas': 3,
                'labels': {'app': 'test'},
                'selector': {'app': 'test'},
                'images': ['test-image:latest'],
                'resources': [],
                'strategy': 'RollingUpdate',
                'created_at': '2025-11-14T10:00:00.000Z'
            }
        ]
        
        # 模拟 get_nodes 方法
        mock.get_nodes.return_value = [
            {
                'name': 'node-1',
                'status': 'Ready',
                'roles': ['<none>'],
                'version': 'v1.28.0',
                'internal_ip': '10.0.0.1',
                'external_ip': 'N/A',
                'os': 'linux',
                'architecture': 'arm64',
                'container_runtime': 'containerd://1.7.0',
                'capacity': {'cpu': '2', 'memory': '4Gi', 'pods': '29'},
                'allocatable': {'cpu': '1930m', 'memory': '3Gi', 'pods': '29'},
                'labels': {},
                'created_at': '2025-11-14T09:00:00.000Z'
            }
        ]
        
        # 模拟 get_pvcs 方法
        mock.get_pvcs.return_value = [
            {
                'name': 'test-pvc',
                'namespace': 'default',
                'status': 'Bound',
                'volume_name': 'pv-123',
                'storage_class': 'gp3',
                'access_modes': ['ReadWriteOnce'],
                'requested_storage': '10Gi',
                'capacity': '10Gi',
                'labels': {},
                'created_at': '2025-11-14T10:00:00.000Z'
            }
        ]
        
        # 模拟 get_hpa 方法
        mock.get_hpa.return_value = {
            'items': [
                {
                    'name': 'test-hpa',
                    'namespace': 'default',
                    'target': {'kind': 'Deployment', 'name': 'test-deployment'},
                    'min_replicas': 3,
                    'max_replicas': 10,
                    'current_replicas': 3,
                    'desired_replicas': 3,
                    'metrics': [],
                    'current_metrics': [],
                    'conditions': [],
                    'created_at': '2025-11-14T10:00:00.000Z'
                }
            ],
            'count': 1
        }
        
        # 模拟 get_current_pod 方法
        mock.get_current_pod.return_value = {
            'name': 'current-pod',
            'namespace': 'default',
            'status': 'Running',
            'ip': '10.0.0.1',
            'node_name': 'node-1',
            'labels': {},
            'annotations': {},
            'service_account': 'default',
            'created_at': '2025-11-14T10:00:00.000Z',
            'restart_count': 0,
            'containers': []
        }
        
        # 模拟 get_events 方法
        mock.get_events.return_value = [
            {
                'type': 'Normal',
                'reason': 'Scheduled',
                'message': 'Successfully assigned pod',
                'object': {'kind': 'Pod', 'name': 'test-pod', 'namespace': 'default'},
                'count': 1,
                'first_timestamp': '2025-11-14T10:00:00.000Z',
                'last_timestamp': '2025-11-14T10:00:00.000Z',
                'source': 'scheduler'
            }
        ]
        
        yield mock


@pytest.fixture
def mock_service_available():
    """模拟服务可用"""
    with patch('routes.resources_routes.service_available', True):
        yield


def test_resources_info(client, mock_k8s_service, mock_service_available):
    """测试获取完整资源信息"""
    with patch('routes.resources_routes.Config') as mock_config:
        mock_config.POD_NAMESPACE = 'default'
        mock_config.POD_NAME = 'test-pod'
        mock_config.NODE_NAME = 'node-1'
        
        response = client.get('/resources/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'namespace' in data
        assert 'pods' in data
        assert 'services' in data
        assert 'deployments' in data
        assert 'nodes' in data
        assert 'pvcs' in data
        assert 'hpa' in data
        assert 'statistics' in data
        assert len(data['pods']) == 1
        assert data['pods'][0]['name'] == 'test-pod-1'


def test_pods_list(client, mock_k8s_service, mock_service_available):
    """测试获取 Pod 列表"""
    with patch('routes.resources_routes.Config') as mock_config:
        mock_config.POD_NAMESPACE = 'default'
        
        response = client.get('/resources/pods')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'pods' in data
        assert data['count'] == 1
        assert data['namespace'] == 'default'


def test_services_list(client, mock_k8s_service, mock_service_available):
    """测试获取 Service 列表"""
    with patch('routes.resources_routes.Config') as mock_config:
        mock_config.POD_NAMESPACE = 'default'
        
        response = client.get('/resources/services')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'services' in data
        assert data['count'] == 1


def test_deployments_list(client, mock_k8s_service, mock_service_available):
    """测试获取 Deployment 列表"""
    with patch('routes.resources_routes.Config') as mock_config:
        mock_config.POD_NAMESPACE = 'default'
        
        response = client.get('/resources/deployments')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'deployments' in data
        assert data['count'] == 1


def test_nodes_list(client, mock_k8s_service, mock_service_available):
    """测试获取节点列表"""
    response = client.get('/resources/nodes')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'nodes' in data
    assert data['count'] == 1


def test_pvcs_list(client, mock_k8s_service, mock_service_available):
    """测试获取 PVC 列表"""
    with patch('routes.resources_routes.Config') as mock_config:
        mock_config.POD_NAMESPACE = 'default'
        
        response = client.get('/resources/pvcs')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'pvcs' in data
        assert data['count'] == 1


def test_hpa_info(client, mock_k8s_service, mock_service_available):
    """测试获取 HPA 信息"""
    with patch('routes.resources_routes.Config') as mock_config:
        mock_config.POD_NAMESPACE = 'default'
        
        response = client.get('/resources/hpa')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'hpa' in data


def test_events_list(client, mock_k8s_service, mock_service_available):
    """测试获取事件列表"""
    with patch('routes.resources_routes.Config') as mock_config:
        mock_config.POD_NAMESPACE = 'default'
        
        response = client.get('/resources/events')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'events' in data
        assert data['count'] == 1


def test_current_pod_info(client, mock_k8s_service, mock_service_available):
    """测试获取当前 Pod 信息"""
    response = client.get('/resources/current-pod')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'pod' in data
    assert data['pod']['name'] == 'current-pod'


def test_resources_health(client, mock_k8s_service, mock_service_available):
    """测试健康检查"""
    response = client.get('/resources/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['healthy'] is True
    assert 'services' in data


def test_service_unavailable(client):
    """测试服务不可用的情况"""
    with patch('routes.resources_routes.service_available', False):
        response = client.get('/resources/')
        assert response.status_code == 503
        
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['error_type'] == 'service_unavailable'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
