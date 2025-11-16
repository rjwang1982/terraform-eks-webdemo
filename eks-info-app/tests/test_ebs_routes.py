"""
EBS 路由集成测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# 设置测试环境变量
os.environ['EBS_MOUNT_PATH'] = tempfile.mkdtemp()
os.environ['POD_NAME'] = 'test-pod'
os.environ['POD_NAMESPACE'] = 'test-namespace'
os.environ['NODE_NAME'] = 'test-node'

# 导入应用
from app import app


def test_ebs_index():
    """测试 EBS 首页"""
    with app.test_client() as client:
        response = client.get('/ebs/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'ebs_info' in data
        assert 'recent_logs' in data
        assert 'current_pod' in data
        assert data['ebs_info']['available'] is True
        
        print("✓ EBS 首页测试通过")


def test_ebs_write():
    """测试写入数据"""
    with app.test_client() as client:
        # 写入数据
        response = client.post('/ebs/write', 
                              json={'content': 'Test data from integration test'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'entry' in data
        assert data['entry']['content'] == 'Test data from integration test'
        
        print("✓ 写入数据测试通过")


def test_ebs_read():
    """测试读取数据"""
    with app.test_client() as client:
        # 先写入一些数据
        client.post('/ebs/write', 
                   json={'content': 'Test log 1'},
                   content_type='application/json')
        client.post('/ebs/write', 
                   json={'content': 'Test log 2'},
                   content_type='application/json')
        
        # 读取数据
        response = client.get('/ebs/read?limit=10')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'logs' in data
        assert len(data['logs']) >= 2
        
        print("✓ 读取数据测试通过")


def test_ebs_info():
    """测试获取 EBS 信息"""
    with app.test_client() as client:
        response = client.get('/ebs/info')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'mount_path' in data
        assert 'disk_usage' in data
        assert 'log_file' in data
        assert 'pod_info' in data
        
        print("✓ 获取 EBS 信息测试通过")


def test_ebs_cleanup():
    """测试清理日志"""
    with app.test_client() as client:
        response = client.post('/ebs/cleanup',
                              json={'days': 7},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'deleted_count' in data
        
        print("✓ 清理日志测试通过")


def test_invalid_write():
    """测试无效的写入请求"""
    with app.test_client() as client:
        # 空内容
        response = client.post('/ebs/write',
                              json={'content': ''},
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        
        print("✓ 无效写入测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n开始 EBS 路由集成测试...\n")
    
    try:
        test_ebs_index()
        test_ebs_write()
        test_ebs_read()
        test_ebs_info()
        test_ebs_cleanup()
        test_invalid_write()
        
        print("\n✓ 所有集成测试通过！\n")
        return True
    except AssertionError as e:
        print(f"\n✗ 测试失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ 测试错误: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试目录
        import shutil
        test_mount = os.environ.get('EBS_MOUNT_PATH')
        if test_mount and os.path.exists(test_mount):
            shutil.rmtree(test_mount)


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
