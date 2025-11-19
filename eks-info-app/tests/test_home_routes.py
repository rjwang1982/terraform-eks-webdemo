"""
首页和健康检查路由测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """测试首页路由"""
    response = client.get('/')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'environment' in data
    assert 'app' in data
    assert data['app']['name'] == 'EKS Info WebApp'
    assert 'timestamp' in data


def test_index_environment_info(client):
    """测试首页返回的环境信息"""
    response = client.get('/')
    data = json.loads(response.data)
    
    # 验证环境信息结构
    env = data['environment']
    assert 'pod' in env
    assert 'node' in env
    assert 'cluster' in env
    assert 'ec2' in env
    assert 'system' in env
    assert 'architecture' in env
    assert 'environment_variables' in env


def test_health_endpoint(client):
    """测试健康检查端点"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'checks' in data
    assert data['checks']['application'] == 'ok'


def test_ready_endpoint_with_storage(client):
    """测试就绪检查端点（存储可用）"""
    # 模拟存储挂载点存在
    with patch('os.path.exists', return_value=True), \
         patch('os.access', return_value=True), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs',
             'S3_BUCKET_NAME': 'test-bucket'
         }):
        
        response = client.get('/ready')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ready'
        assert 'checks' in data
        assert 'storage' in data['checks']
        
        # 验证 EBS 检查
        assert data['checks']['storage']['ebs']['status'] == 'ready'
        assert data['checks']['storage']['ebs']['writable'] is True
        
        # 验证 EFS 检查
        assert data['checks']['storage']['efs']['status'] == 'ready'
        assert data['checks']['storage']['efs']['writable'] is True


def test_ready_endpoint_storage_not_available(client):
    """测试就绪检查端点（存储不可用）"""
    # 模拟存储挂载点不存在
    with patch('os.path.exists', return_value=False), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs'
         }):
        
        response = client.get('/ready')
        assert response.status_code == 503
        
        data = json.loads(response.data)
        assert data['status'] == 'not_ready'
        assert 'checks' in data
        
        # 验证 EBS 检查失败
        assert data['checks']['storage']['ebs']['status'] == 'not_ready'
        assert data['checks']['storage']['ebs']['writable'] is False


def test_ready_endpoint_without_s3_config(client):
    """测试就绪检查端点（未配置 S3）"""
    # 模拟 EBS 和 EFS 可用，但未配置 S3
    with patch('os.path.exists', return_value=True), \
         patch('os.access', return_value=True), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs'
         }, clear=True):
        
        response = client.get('/ready')
        # S3 不是必需的，应该仍然返回 ready
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ready'
        assert data['checks']['storage']['s3']['status'] == 'not_configured'


def test_index_pod_info(client):
    """测试首页返回的 Pod 信息"""
    response = client.get('/')
    data = json.loads(response.data)
    
    pod_info = data['environment']['pod']
    assert 'name' in pod_info
    assert 'namespace' in pod_info
    assert 'ip' in pod_info
    assert 'node_name' in pod_info
    assert 'hostname' in pod_info


def test_index_architecture_info(client):
    """测试首页返回的架构信息"""
    response = client.get('/')
    data = json.loads(response.data)
    
    arch_info = data['environment']['architecture']
    assert 'machine' in arch_info
    assert 'is_arm64' in arch_info
    assert 'is_graviton' in arch_info
    assert 'cpu_count' in arch_info


def test_health_response_format(client):
    """测试健康检查响应格式"""
    response = client.get('/health')
    data = json.loads(response.data)
    
    # 验证必需字段
    required_fields = ['status', 'timestamp', 'checks']
    for field in required_fields:
        assert field in data, f"缺少必需字段: {field}"


def test_ready_response_format(client):
    """测试就绪检查响应格式"""
    with patch('os.path.exists', return_value=True), \
         patch('os.access', return_value=True):
        
        response = client.get('/ready')
        data = json.loads(response.data)
        
        # 验证必需字段
        required_fields = ['status', 'timestamp', 'checks']
        for field in required_fields:
            assert field in data, f"缺少必需字段: {field}"
        
        # 验证 checks 结构
        assert 'application' in data['checks']
        assert 'storage' in data['checks']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
