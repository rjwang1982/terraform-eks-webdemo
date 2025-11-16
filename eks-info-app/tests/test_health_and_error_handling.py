"""
健康检查和错误处理综合测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-15

测试范围:
- 健康检查端点 (/health)
- 就绪检查端点 (/ready)
- 存储不可用时的错误处理
- API 调用失败的重试机制
- 日志记录验证

需求: 8.1-8.5, 9.4, 9.5
"""

import pytest
import json
import os
import logging
from unittest.mock import patch, MagicMock, call
from app import app
from storage.ebs_storage import EBSStorage
from storage.efs_storage import EFSStorage
from storage.s3_storage import S3Storage
from services.aws_service import AWSService
from services.kubernetes_service import KubernetesService


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_logger():
    """创建模拟日志记录器"""
    logger = MagicMock(spec=logging.Logger)
    return logger


# ============================================================================
# 测试 1: 健康检查端点
# 需求: 8.1
# ============================================================================

def test_health_endpoint_returns_200(client):
    """测试健康检查端点返回 200 状态码"""
    response = client.get('/health')
    assert response.status_code == 200


def test_health_endpoint_returns_healthy_status(client):
    """测试健康检查端点返回健康状态"""
    response = client.get('/health')
    data = json.loads(response.data)
    
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'checks' in data
    assert data['checks']['application'] == 'ok'


def test_health_endpoint_includes_python_version(client):
    """测试健康检查端点包含 Python 版本信息"""
    response = client.get('/health')
    data = json.loads(response.data)
    
    assert 'python_version' in data['checks']
    assert data['checks']['python_version'] != ''


def test_health_endpoint_response_format(client):
    """测试健康检查端点响应格式正确"""
    response = client.get('/health')
    data = json.loads(response.data)
    
    # 验证必需字段
    required_fields = ['status', 'timestamp', 'checks']
    for field in required_fields:
        assert field in data, f"缺少必需字段: {field}"
    
    # 验证时间戳格式（ISO 8601）
    assert data['timestamp'].endswith('Z')


# ============================================================================
# 测试 2: 就绪检查端点 - 存储可用
# 需求: 8.2, 8.3
# ============================================================================

def test_ready_endpoint_all_storage_available(client):
    """测试就绪检查端点 - 所有存储可用"""
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
        assert data['checks']['storage']['ebs']['status'] == 'ready'
        assert data['checks']['storage']['efs']['status'] == 'ready'


def test_ready_endpoint_checks_ebs_writable(client):
    """测试就绪检查验证 EBS 可写"""
    with patch('os.path.exists', return_value=True), \
         patch('os.access', return_value=True) as mock_access, \
         patch.dict(os.environ, {'EBS_MOUNT_PATH': '/data/ebs'}):
        
        response = client.get('/ready')
        data = json.loads(response.data)
        
        # 验证调用了 os.access 检查写权限
        assert data['checks']['storage']['ebs']['writable'] is True


def test_ready_endpoint_checks_efs_writable(client):
    """测试就绪检查验证 EFS 可写"""
    with patch('os.path.exists', return_value=True), \
         patch('os.access', return_value=True) as mock_access, \
         patch.dict(os.environ, {'EFS_MOUNT_PATH': '/data/efs'}):
        
        response = client.get('/ready')
        data = json.loads(response.data)
        
        # 验证调用了 os.access 检查写权限
        assert data['checks']['storage']['efs']['writable'] is True


# ============================================================================
# 测试 3: 就绪检查端点 - 存储不可用
# 需求: 8.4
# ============================================================================

def test_ready_endpoint_ebs_not_available(client):
    """测试就绪检查端点 - EBS 不可用"""
    with patch('os.path.exists', return_value=False), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs'
         }):
        
        response = client.get('/ready')
        assert response.status_code == 503
        
        data = json.loads(response.data)
        assert data['status'] == 'not_ready'
        assert data['checks']['storage']['ebs']['status'] == 'not_ready'
        assert 'error' in data['checks']['storage']['ebs']


def test_ready_endpoint_efs_not_available(client):
    """测试就绪检查端点 - EFS 不可用"""
    with patch('os.path.exists', side_effect=lambda path: path != '/data/efs'), \
         patch('os.access', return_value=True), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs'
         }):
        
        response = client.get('/ready')
        assert response.status_code == 503
        
        data = json.loads(response.data)
        assert data['status'] == 'not_ready'
        assert data['checks']['storage']['efs']['status'] == 'not_ready'


def test_ready_endpoint_storage_not_writable(client):
    """测试就绪检查端点 - 存储不可写"""
    with patch('os.path.exists', return_value=True), \
         patch('os.access', return_value=False), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs'
         }):
        
        response = client.get('/ready')
        assert response.status_code == 503
        
        data = json.loads(response.data)
        assert data['status'] == 'not_ready'
        assert data['checks']['storage']['ebs']['writable'] is False
        assert data['checks']['storage']['efs']['writable'] is False


def test_ready_endpoint_reports_specific_errors(client):
    """测试就绪检查端点报告具体错误信息"""
    with patch('os.path.exists', return_value=False), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs'
         }):
        
        response = client.get('/ready')
        data = json.loads(response.data)
        
        # 验证包含具体错误信息
        assert 'error' in data['checks']['storage']['ebs']
        assert '挂载点不存在或不可写' in data['checks']['storage']['ebs']['error']


# ============================================================================
# 测试 4: S3 存储检查
# 需求: 8.2, 8.4
# ============================================================================

def test_ready_endpoint_s3_not_configured(client):
    """测试就绪检查端点 - S3 未配置（不影响就绪状态）"""
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


def test_ready_endpoint_s3_error_does_not_fail_readiness(client):
    """测试就绪检查端点 - S3 错误不影响就绪状态"""
    with patch('os.path.exists', return_value=True), \
         patch('os.access', return_value=True), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs',
             'S3_BUCKET_NAME': 'test-bucket'
         }), \
         patch('storage.s3_storage.S3Storage.__init__', side_effect=Exception('S3 连接失败')):
        
        response = client.get('/ready')
        # S3 错误不应该导致整体不就绪
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ready'
        assert data['checks']['storage']['s3']['status'] == 'error'


# ============================================================================
# 测试 5: 存储错误处理
# 需求: 8.4, 9.4
# ============================================================================

def test_ebs_storage_handles_write_error():
    """测试 EBS 存储处理写入错误"""
    # EBS 存储在初始化时会检查路径，如果不存在会抛出 ValueError
    with pytest.raises(ValueError, match="EBS 挂载路径不存在"):
        ebs = EBSStorage('/nonexistent/path')


def test_efs_storage_handles_write_error():
    """测试 EFS 存储处理写入错误"""
    # EFS 存储在初始化时会检查路径，如果不存在会抛出 ValueError
    with pytest.raises(ValueError, match="EFS 挂载路径不存在"):
        efs = EFSStorage('/nonexistent/path')


def test_s3_storage_handles_connection_error():
    """测试 S3 存储处理连接错误"""
    with patch('boto3.client') as mock_boto:
        mock_boto.side_effect = Exception('无法连接到 S3')
        
        # 初始化应该失败但不抛出异常
        try:
            s3 = S3Storage('test-bucket')
            # 如果没有抛出异常，测试通过
            assert True
        except Exception:
            # 如果抛出异常，测试失败
            pytest.fail("S3Storage 应该优雅地处理连接错误")


# ============================================================================
# 测试 6: API 调用失败和重试机制
# 需求: 9.4, 9.5
# ============================================================================

def test_aws_service_handles_api_error():
    """测试 AWS 服务处理 API 错误"""
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_client.describe_instances.side_effect = Exception('API 调用失败')
        mock_boto.return_value = mock_client
        
        aws_service = AWSService()
        result = aws_service.get_ec2_instance_info('i-12345')
        
        # 应该返回错误信息而不是抛出异常
        assert 'error' in result


def test_kubernetes_service_handles_api_error():
    """测试 Kubernetes 服务处理 API 错误"""
    with patch('kubernetes.config.load_incluster_config'), \
         patch('kubernetes.client.CoreV1Api') as mock_api:
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_pod_for_all_namespaces.side_effect = Exception('API 调用失败')
        mock_api.return_value = mock_api_instance
        
        k8s_service = KubernetesService()
        result = k8s_service.get_pods('default')
        
        # 应该返回空列表或错误信息而不是抛出异常
        assert isinstance(result, (list, dict))


# ============================================================================
# 测试 7: 日志记录验证
# 需求: 8.5, 9.5
# ============================================================================

def test_health_check_logs_debug_message(client, caplog):
    """测试健康检查记录调试日志"""
    with caplog.at_level(logging.DEBUG):
        response = client.get('/health')
        
        # 验证记录了日志
        assert any('健康检查' in record.message for record in caplog.records)


def test_ready_check_logs_info_message(client, caplog):
    """测试就绪检查记录信息日志"""
    with caplog.at_level(logging.INFO), \
         patch('os.path.exists', return_value=True), \
         patch('os.access', return_value=True):
        
        response = client.get('/ready')
        
        # 验证记录了日志
        assert any('就绪检查' in record.message for record in caplog.records)


def test_storage_error_logs_warning(client, caplog):
    """测试存储错误记录警告日志"""
    with caplog.at_level(logging.WARNING), \
         patch('os.path.exists', return_value=False), \
         patch.dict(os.environ, {'EBS_MOUNT_PATH': '/data/ebs'}):
        
        response = client.get('/ready')
        
        # 验证记录了警告日志
        assert any('EBS 存储检查' in record.message and 'WARNING' in record.levelname 
                   for record in caplog.records)


def test_api_error_logs_error_message(caplog):
    """测试 API 错误记录错误日志"""
    with caplog.at_level(logging.ERROR), \
         patch('boto3.client') as mock_boto:
        
        mock_client = MagicMock()
        mock_client.describe_instances.side_effect = Exception('API 调用失败')
        mock_boto.return_value = mock_client
        
        aws_service = AWSService()
        result = aws_service.get_ec2_instance_info('i-12345')
        
        # 验证记录了错误日志
        assert any('ERROR' in record.levelname for record in caplog.records)


def test_logs_do_not_contain_sensitive_info(client, caplog):
    """测试日志不包含敏感信息"""
    with caplog.at_level(logging.DEBUG), \
         patch.dict(os.environ, {
             'AWS_SECRET_ACCESS_KEY': 'secret123',
             'PASSWORD': 'password123',
             'API_KEY': 'key123'
         }):
        
        response = client.get('/')
        
        # 验证日志中没有敏感信息
        log_text = ' '.join([record.message for record in caplog.records])
        assert 'secret123' not in log_text
        assert 'password123' not in log_text
        assert 'key123' not in log_text


# ============================================================================
# 测试 8: 错误响应格式
# 需求: 8.4, 9.4
# ============================================================================

def test_error_response_includes_timestamp(client):
    """测试错误响应包含时间戳"""
    with patch('os.path.exists', return_value=False), \
         patch.dict(os.environ, {'EBS_MOUNT_PATH': '/data/ebs'}):
        
        response = client.get('/ready')
        data = json.loads(response.data)
        
        assert 'timestamp' in data
        assert data['timestamp'].endswith('Z')


def test_error_response_includes_error_details(client):
    """测试错误响应包含错误详情"""
    with patch('os.path.exists', return_value=False), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs'
         }):
        
        response = client.get('/ready')
        data = json.loads(response.data)
        
        # 验证包含详细的错误信息
        assert 'checks' in data
        assert 'storage' in data['checks']
        assert 'error' in data['checks']['storage']['ebs']


def test_404_error_handler(client):
    """测试 404 错误处理器"""
    response = client.get('/nonexistent-path')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data['error'] is True
    assert data['error_type'] == 'not_found'
    assert 'timestamp' in data


def test_500_error_handler(client):
    """测试 500 错误处理器"""
    # 测试首页在发生异常时的错误处理
    # 需要模拟一个会导致500错误的场景
    with patch('services.environment_service.EnvironmentService.get_all_environment_info', 
               side_effect=Exception('测试异常')):
        
        response = client.get('/', headers={'Accept': 'application/json'})
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        assert 'timestamp' in data


# ============================================================================
# 测试 9: 启动时初始化检查
# 需求: 8.3
# ============================================================================

def test_application_starts_within_30_seconds():
    """测试应用在 30 秒内完成初始化"""
    import time
    
    # 记录启动时间
    start_time = time.time()
    
    # 创建测试客户端（模拟应用启动）
    app.config['TESTING'] = True
    with app.test_client() as client:
        # 发送健康检查请求
        response = client.get('/health')
        
        # 计算启动时间
        startup_time = time.time() - start_time
        
        # 验证启动时间小于 30 秒
        assert startup_time < 30
        assert response.status_code == 200


# ============================================================================
# 测试 10: 综合场景测试
# 需求: 8.1-8.5, 9.4, 9.5
# ============================================================================

def test_health_check_always_succeeds_even_with_storage_errors(client):
    """测试健康检查即使存储错误也能成功"""
    with patch('os.path.exists', return_value=False):
        # 健康检查不应该受存储状态影响
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


def test_ready_check_fails_gracefully_with_multiple_errors(client):
    """测试就绪检查优雅地处理多个错误"""
    with patch('os.path.exists', return_value=False), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs',
             'S3_BUCKET_NAME': 'test-bucket'
         }), \
         patch('storage.s3_storage.S3Storage.__init__', side_effect=Exception('S3 错误')):
        
        response = client.get('/ready')
        assert response.status_code == 503
        
        data = json.loads(response.data)
        assert data['status'] == 'not_ready'
        
        # 验证所有存储都报告了错误
        assert data['checks']['storage']['ebs']['status'] == 'not_ready'
        assert data['checks']['storage']['efs']['status'] == 'not_ready'
        assert data['checks']['storage']['s3']['status'] == 'error'


def test_application_continues_running_with_partial_storage_failure(client):
    """测试应用在部分存储失败时继续运行"""
    with patch('os.path.exists', side_effect=lambda path: path == '/data/ebs'), \
         patch('os.access', return_value=True), \
         patch.dict(os.environ, {
             'EBS_MOUNT_PATH': '/data/ebs',
             'EFS_MOUNT_PATH': '/data/efs'
         }):
        
        # 就绪检查应该失败
        ready_response = client.get('/ready')
        assert ready_response.status_code == 503
        
        # 但健康检查应该成功
        health_response = client.get('/health')
        assert health_response.status_code == 200
        
        # 首页应该仍然可访问
        index_response = client.get('/')
        assert index_response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
