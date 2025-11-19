"""
StorageService 测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.storage_service import StorageService


def test_storage_service_initialization():
    """测试 StorageService 初始化"""
    print("测试 StorageService 初始化...")
    
    # 创建临时目录模拟挂载点
    with tempfile.TemporaryDirectory() as temp_dir:
        ebs_path = os.path.join(temp_dir, 'ebs')
        efs_path = os.path.join(temp_dir, 'efs')
        
        os.makedirs(ebs_path)
        os.makedirs(efs_path)
        
        # 初始化存储服务
        storage_service = StorageService(
            ebs_mount_path=ebs_path,
            efs_mount_path=efs_path,
            s3_bucket_name='test-bucket',
            aws_region='ap-southeast-1'
        )
        
        assert storage_service is not None
        assert storage_service.ebs_storage is not None
        assert storage_service.efs_storage is not None
        # S3 可能不可用（没有 AWS 凭证）
        
        print("✓ StorageService 初始化成功")


def test_get_mount_points():
    """测试获取挂载点信息"""
    print("\n测试获取挂载点信息...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        ebs_path = os.path.join(temp_dir, 'ebs')
        efs_path = os.path.join(temp_dir, 'efs')
        
        os.makedirs(ebs_path)
        os.makedirs(efs_path)
        
        storage_service = StorageService(
            ebs_mount_path=ebs_path,
            efs_mount_path=efs_path,
            s3_bucket_name='test-bucket',
            aws_region='ap-southeast-1'
        )
        
        mount_points = storage_service.get_mount_points()
        
        assert isinstance(mount_points, list)
        print(f"✓ 找到 {len(mount_points)} 个挂载点")


def test_get_ebs_info():
    """测试获取 EBS 信息"""
    print("\n测试获取 EBS 信息...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        ebs_path = os.path.join(temp_dir, 'ebs')
        efs_path = os.path.join(temp_dir, 'efs')
        
        os.makedirs(ebs_path)
        os.makedirs(efs_path)
        
        storage_service = StorageService(
            ebs_mount_path=ebs_path,
            efs_mount_path=efs_path,
            s3_bucket_name='test-bucket',
            aws_region='ap-southeast-1'
        )
        
        ebs_info = storage_service.get_ebs_info()
        
        assert isinstance(ebs_info, dict)
        assert 'type' in ebs_info
        assert ebs_info['type'] == 'EBS'
        assert 'available' in ebs_info
        assert ebs_info['available'] == True
        assert 'mount_path' in ebs_info
        
        print(f"✓ EBS 信息获取成功")
        print(f"  - 类型: {ebs_info['type']}")
        print(f"  - 可用: {ebs_info['available']}")
        print(f"  - 挂载路径: {ebs_info['mount_path']}")


def test_get_efs_info():
    """测试获取 EFS 信息"""
    print("\n测试获取 EFS 信息...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        ebs_path = os.path.join(temp_dir, 'ebs')
        efs_path = os.path.join(temp_dir, 'efs')
        
        os.makedirs(ebs_path)
        os.makedirs(efs_path)
        
        storage_service = StorageService(
            ebs_mount_path=ebs_path,
            efs_mount_path=efs_path,
            s3_bucket_name='test-bucket',
            aws_region='ap-southeast-1'
        )
        
        efs_info = storage_service.get_efs_info()
        
        assert isinstance(efs_info, dict)
        assert 'type' in efs_info
        assert efs_info['type'] == 'EFS'
        assert 'available' in efs_info
        assert efs_info['available'] == True
        assert 'mount_path' in efs_info
        
        print(f"✓ EFS 信息获取成功")
        print(f"  - 类型: {efs_info['type']}")
        print(f"  - 可用: {efs_info['available']}")
        print(f"  - 挂载路径: {efs_info['mount_path']}")


def test_get_s3_info():
    """测试获取 S3 信息"""
    print("\n测试获取 S3 信息...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        ebs_path = os.path.join(temp_dir, 'ebs')
        efs_path = os.path.join(temp_dir, 'efs')
        
        os.makedirs(ebs_path)
        os.makedirs(efs_path)
        
        storage_service = StorageService(
            ebs_mount_path=ebs_path,
            efs_mount_path=efs_path,
            s3_bucket_name='test-bucket',
            aws_region='ap-southeast-1'
        )
        
        s3_info = storage_service.get_s3_info()
        
        assert isinstance(s3_info, dict)
        assert 'type' in s3_info
        assert s3_info['type'] == 'S3'
        assert 'bucket_name' in s3_info
        assert s3_info['bucket_name'] == 'test-bucket'
        
        print(f"✓ S3 信息获取成功")
        print(f"  - 类型: {s3_info['type']}")
        print(f"  - 存储桶: {s3_info['bucket_name']}")
        print(f"  - 可用: {s3_info['available']}")


def test_get_storage_summary():
    """测试获取存储摘要"""
    print("\n测试获取存储摘要...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        ebs_path = os.path.join(temp_dir, 'ebs')
        efs_path = os.path.join(temp_dir, 'efs')
        
        os.makedirs(ebs_path)
        os.makedirs(efs_path)
        
        storage_service = StorageService(
            ebs_mount_path=ebs_path,
            efs_mount_path=efs_path,
            s3_bucket_name='test-bucket',
            aws_region='ap-southeast-1'
        )
        
        summary = storage_service.get_storage_summary()
        
        assert isinstance(summary, dict)
        assert 'storage_types' in summary
        assert isinstance(summary['storage_types'], list)
        assert len(summary['storage_types']) == 3
        assert 'available_count' in summary
        assert 'total_count' in summary
        assert summary['total_count'] == 3
        
        print(f"✓ 存储摘要获取成功")
        print(f"  - 总存储系统数: {summary['total_count']}")
        print(f"  - 可用存储系统数: {summary['available_count']}")
        
        for storage_type in summary['storage_types']:
            print(f"  - {storage_type['type']}: {'可用' if storage_type['available'] else '不可用'}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试 StorageService")
    print("=" * 60)
    
    try:
        test_storage_service_initialization()
        test_get_mount_points()
        test_get_ebs_info()
        test_get_efs_info()
        test_get_s3_info()
        test_get_storage_summary()
        
        print("\n" + "=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n✗ 测试失败: {str(e)}")
        return False
    except Exception as e:
        print(f"\n✗ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
