"""
S3Storage 类测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import json
from datetime import datetime
from storage.s3_storage import S3Storage


def test_s3_storage():
    """测试 S3Storage 类的基本功能"""
    
    print("=" * 60)
    print("S3Storage 类功能测试")
    print("=" * 60)
    
    # 初始化 S3 存储
    bucket_name = "eks-info-app-data"
    region = "ap-southeast-1"
    
    print(f"\n1. 初始化 S3 存储")
    print(f"   存储桶: {bucket_name}")
    print(f"   区域: {region}")
    
    try:
        s3_storage = S3Storage(bucket_name=bucket_name, region=region)
        print(f"   状态: {'可用' if s3_storage.available else '不可用'}")
        
        if not s3_storage.available:
            print("\n⚠️  S3 存储不可用，跳过后续测试")
            print("   可能的原因:")
            print("   - 存储桶不存在")
            print("   - 没有访问权限（检查 IRSA 配置）")
            print("   - AWS 凭证未配置")
            return
        
        # 测试获取存储桶信息
        print(f"\n2. 获取存储桶信息")
        bucket_info = s3_storage.get_bucket_info()
        if 'error' in bucket_info:
            print(f"   ❌ 错误: {bucket_info.get('message')}")
        else:
            print(f"   ✓ 存储桶名称: {bucket_info.get('bucket_name')}")
            print(f"   ✓ 区域: {bucket_info.get('region')}")
            print(f"   ✓ 对象数量: {bucket_info.get('object_count')}")
            print(f"   ✓ 总大小: {bucket_info.get('total_size_mb')} MB")
            print(f"   ✓ 加密: {'是' if bucket_info.get('encryption') else '否'}")
        
        # 测试上传对象
        print(f"\n3. 测试上传对象")
        test_key = f"test_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        test_data = {
            'message': 'S3Storage 测试数据',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'test_number': 12345
        }
        test_bytes = json.dumps(test_data, ensure_ascii=False, indent=2).encode('utf-8')
        test_metadata = {
            'test': 'true',
            'created_by': 'test_s3_storage.py'
        }
        
        success = s3_storage.upload_object(
            key=test_key,
            data=test_bytes,
            metadata=test_metadata
        )
        
        if success:
            print(f"   ✓ 上传成功: {test_key}")
            print(f"   ✓ 大小: {len(test_bytes)} 字节")
        else:
            print(f"   ❌ 上传失败")
            return
        
        # 测试列出对象
        print(f"\n4. 测试列出对象")
        objects = s3_storage.list_objects(max_keys=5)
        print(f"   ✓ 找到 {len(objects)} 个对象")
        for i, obj in enumerate(objects[:3], 1):
            print(f"   {i}. {obj['key']} ({obj['size_kb']} KB)")
        
        # 测试获取对象元数据
        print(f"\n5. 测试获取对象元数据")
        metadata = s3_storage.get_object_metadata(test_key)
        if metadata:
            print(f"   ✓ 键名: {metadata.get('key')}")
            print(f"   ✓ 大小: {metadata.get('size_bytes')} 字节")
            print(f"   ✓ 内容类型: {metadata.get('content_type')}")
            print(f"   ✓ 存储类: {metadata.get('storage_class')}")
            print(f"   ✓ 自定义元数据: {metadata.get('metadata')}")
        else:
            print(f"   ❌ 获取元数据失败")
        
        # 测试下载对象
        print(f"\n6. 测试下载对象")
        downloaded_data = s3_storage.download_object(test_key)
        if downloaded_data:
            downloaded_json = json.loads(downloaded_data.decode('utf-8'))
            print(f"   ✓ 下载成功")
            print(f"   ✓ 内容: {downloaded_json.get('message')}")
            print(f"   ✓ 数据完整性: {'通过' if downloaded_json == test_data else '失败'}")
        else:
            print(f"   ❌ 下载失败")
        
        # 测试删除对象
        print(f"\n7. 测试删除对象")
        delete_success = s3_storage.delete_object(test_key)
        if delete_success:
            print(f"   ✓ 删除成功: {test_key}")
            
            # 验证对象已删除
            verify_data = s3_storage.download_object(test_key)
            if verify_data is None:
                print(f"   ✓ 验证: 对象已不存在")
            else:
                print(f"   ⚠️  警告: 对象仍然存在")
        else:
            print(f"   ❌ 删除失败")
        
        print(f"\n{'=' * 60}")
        print("✓ 所有测试完成")
        print(f"{'=' * 60}\n")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_s3_storage()
