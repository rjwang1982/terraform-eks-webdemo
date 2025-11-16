"""
S3 路由测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


def test_s3_routes():
    """测试 S3 路由是否正确注册"""
    
    print("=" * 60)
    print("S3 路由测试")
    print("=" * 60)
    
    # 创建测试客户端
    client = app.test_client()
    
    # 测试 S3 主页路由
    print("\n1. 测试 GET /s3/")
    response = client.get('/s3/')
    print(f"   状态码: {response.status_code}")
    print(f"   响应类型: {response.content_type}")
    
    if response.status_code == 503:
        print("   ✓ 路由正常（S3 存储不可用是预期的）")
        data = response.get_json()
        print(f"   消息: {data.get('message')}")
    elif response.status_code == 200:
        print("   ✓ 路由正常（S3 存储可用）")
        data = response.get_json()
        print(f"   存储桶: {data.get('s3_info', {}).get('bucket_name')}")
    else:
        print(f"   ⚠️  意外的状态码: {response.status_code}")
    
    # 测试 S3 信息路由
    print("\n2. 测试 GET /s3/info")
    response = client.get('/s3/info')
    print(f"   状态码: {response.status_code}")
    
    if response.status_code in [200, 503]:
        print("   ✓ 路由正常")
    else:
        print(f"   ⚠️  意外的状态码: {response.status_code}")
    
    # 测试 S3 列表路由
    print("\n3. 测试 GET /s3/list")
    response = client.get('/s3/list')
    print(f"   状态码: {response.status_code}")
    
    if response.status_code in [200, 503]:
        print("   ✓ 路由正常")
    else:
        print(f"   ⚠️  意外的状态码: {response.status_code}")
    
    # 测试 S3 上传路由（POST）
    print("\n4. 测试 POST /s3/upload")
    response = client.post('/s3/upload', json={'content': '测试数据'})
    print(f"   状态码: {response.status_code}")
    
    if response.status_code in [200, 503]:
        print("   ✓ 路由正常")
    else:
        print(f"   ⚠️  意外的状态码: {response.status_code}")
    
    # 测试 S3 下载路由
    print("\n5. 测试 GET /s3/download/test.json")
    response = client.get('/s3/download/test.json')
    print(f"   状态码: {response.status_code}")
    
    if response.status_code in [200, 404, 503]:
        print("   ✓ 路由正常")
    else:
        print(f"   ⚠️  意外的状态码: {response.status_code}")
    
    # 测试 S3 删除路由
    print("\n6. 测试 DELETE /s3/delete/test.json")
    response = client.delete('/s3/delete/test.json')
    print(f"   状态码: {response.status_code}")
    
    if response.status_code in [200, 503]:
        print("   ✓ 路由正常")
    else:
        print(f"   ⚠️  意外的状态码: {response.status_code}")
    
    # 列出所有注册的路由
    print("\n7. 已注册的 S3 相关路由:")
    s3_routes = [rule for rule in app.url_map.iter_rules() if '/s3' in rule.rule]
    for route in s3_routes:
        print(f"   - {route.rule} [{', '.join(route.methods - {'HEAD', 'OPTIONS'})}]")
    
    print(f"\n{'=' * 60}")
    print("✓ 所有路由测试完成")
    print(f"{'=' * 60}\n")


if __name__ == '__main__':
    test_s3_routes()
