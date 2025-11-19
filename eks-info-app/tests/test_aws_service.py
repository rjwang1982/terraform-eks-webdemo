"""
AWS 服务测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import logging
from services.aws_service import AWSService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_aws_service_initialization():
    """测试 AWSService 初始化"""
    try:
        # 测试默认区域初始化
        service = AWSService()
        assert service.region == 'ap-southeast-1'
        assert service.ec2_client is not None
        assert service.efs_client is not None
        assert service.elb_client is not None
        logger.info("✓ AWSService 初始化测试通过（默认区域）")
        
        # 测试指定区域初始化
        service_custom = AWSService(region='us-east-1')
        assert service_custom.region == 'us-east-1'
        logger.info("✓ AWSService 初始化测试通过（自定义区域）")
        
        return True
    except Exception as e:
        logger.error(f"✗ AWSService 初始化测试失败: {str(e)}")
        return False


def test_aws_service_methods():
    """测试 AWSService 方法签名"""
    try:
        service = AWSService()
        
        # 验证所有必需的方法存在
        required_methods = [
            'get_ec2_instance_info',
            'get_vpc_info',
            'get_subnet_info',
            'get_security_groups',
            'get_ebs_volume_info',
            'get_efs_filesystem_info',
            'get_load_balancers'
        ]
        
        for method_name in required_methods:
            assert hasattr(service, method_name), f"缺少方法: {method_name}"
            assert callable(getattr(service, method_name)), f"方法不可调用: {method_name}"
        
        logger.info(f"✓ AWSService 方法签名测试通过（{len(required_methods)} 个方法）")
        return True
    except Exception as e:
        logger.error(f"✗ AWSService 方法签名测试失败: {str(e)}")
        return False


def test_error_handling():
    """测试错误处理"""
    try:
        service = AWSService()
        
        # 测试不存在的实例 ID
        result = service.get_ec2_instance_info('i-nonexistent')
        assert 'error' in result or 'instance_id' in result
        logger.info("✓ EC2 实例错误处理测试通过")
        
        # 测试不存在的 VPC ID
        result = service.get_vpc_info('vpc-nonexistent')
        assert 'error' in result or 'vpc_id' in result
        logger.info("✓ VPC 错误处理测试通过")
        
        # 测试不存在的子网 ID
        result = service.get_subnet_info('subnet-nonexistent')
        assert 'error' in result or 'subnet_id' in result
        logger.info("✓ 子网错误处理测试通过")
        
        # 测试空安全组列表
        result = service.get_security_groups([])
        assert isinstance(result, list)
        assert len(result) == 0
        logger.info("✓ 安全组错误处理测试通过")
        
        # 测试不存在的 EBS 卷 ID
        result = service.get_ebs_volume_info('vol-nonexistent')
        assert 'error' in result or 'volume_id' in result
        logger.info("✓ EBS 卷错误处理测试通过")
        
        # 测试不存在的 EFS 文件系统 ID
        result = service.get_efs_filesystem_info('fs-nonexistent')
        assert 'error' in result or 'file_system_id' in result
        logger.info("✓ EFS 文件系统错误处理测试通过")
        
        # 测试负载均衡器列表（可能为空）
        result = service.get_load_balancers()
        assert isinstance(result, list)
        logger.info("✓ 负载均衡器错误处理测试通过")
        
        return True
    except Exception as e:
        logger.error(f"✗ 错误处理测试失败: {str(e)}")
        return False


def main():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("开始 AWSService 测试")
    logger.info("=" * 60)
    
    tests = [
        ("初始化测试", test_aws_service_initialization),
        ("方法签名测试", test_aws_service_methods),
        ("错误处理测试", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n运行测试: {test_name}")
        logger.info("-" * 60)
        result = test_func()
        results.append((test_name, result))
    
    # 输出测试总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{status}: {test_name}")
    
    logger.info("-" * 60)
    logger.info(f"总计: {passed}/{total} 测试通过")
    logger.info("=" * 60)
    
    return passed == total


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
