"""
EBS 存储功能测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from storage.ebs_storage import EBSStorage


def test_ebs_storage_init():
    """测试 EBS 存储初始化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = EBSStorage(tmpdir)
        assert storage.mount_path == Path(tmpdir)
        assert storage.log_file.exists()
        print("✓ EBS 存储初始化测试通过")


def test_write_and_read_logs():
    """测试写入和读取日志"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = EBSStorage(tmpdir)
        
        # 写入测试日志
        test_entry = {
            'pod_name': 'test-pod',
            'content': 'Test log entry',
            'type': 'test'
        }
        
        success = storage.write_log(test_entry)
        assert success, "日志写入失败"
        
        # 读取日志
        logs = storage.read_logs(limit=10)
        assert len(logs) > 0, "未读取到日志"
        assert logs[0]['content'] == 'Test log entry'
        assert 'timestamp' in logs[0]
        
        print("✓ 日志写入和读取测试通过")


def test_disk_usage():
    """测试磁盘使用情况获取"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = EBSStorage(tmpdir)
        
        usage = storage.get_disk_usage()
        assert 'total_bytes' in usage
        assert 'used_bytes' in usage
        assert 'free_bytes' in usage
        assert 'usage_percent' in usage
        assert usage['usage_percent'] >= 0
        assert usage['usage_percent'] <= 100
        
        print("✓ 磁盘使用情况测试通过")


def test_log_file_info():
    """测试日志文件信息获取"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = EBSStorage(tmpdir)
        
        # 写入一些日志
        for i in range(5):
            storage.write_log({'index': i, 'content': f'Log {i}'})
        
        info = storage.get_log_file_info()
        assert info['exists'] is True
        assert info['line_count'] == 5
        assert info['size_bytes'] > 0
        
        print("✓ 日志文件信息测试通过")


def test_cleanup_old_logs():
    """测试清理旧日志"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = EBSStorage(tmpdir)
        
        # 写入一些旧日志（模拟）
        old_time = (datetime.utcnow() - timedelta(days=10)).isoformat() + 'Z'
        recent_time = datetime.utcnow().isoformat() + 'Z'
        
        storage.write_log({'timestamp': old_time, 'content': 'Old log'})
        storage.write_log({'timestamp': recent_time, 'content': 'Recent log'})
        
        # 清理 7 天前的日志
        deleted = storage.cleanup_old_logs(days=7)
        
        # 验证旧日志被删除
        logs = storage.read_logs(limit=10)
        assert len(logs) == 1
        assert logs[0]['content'] == 'Recent log'
        
        print("✓ 清理旧日志测试通过")


def test_multiple_writes():
    """测试多次写入"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = EBSStorage(tmpdir)
        
        # 写入多条日志
        for i in range(20):
            storage.write_log({
                'index': i,
                'pod_name': f'pod-{i % 3}',
                'content': f'Log entry {i}'
            })
        
        # 读取所有日志
        logs = storage.read_logs(limit=100)
        assert len(logs) == 20
        
        # 验证顺序（最新的在前）
        assert logs[0]['index'] == 19
        assert logs[-1]['index'] == 0
        
        print("✓ 多次写入测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n开始 EBS 存储功能测试...\n")
    
    try:
        test_ebs_storage_init()
        test_write_and_read_logs()
        test_disk_usage()
        test_log_file_info()
        test_cleanup_old_logs()
        test_multiple_writes()
        
        print("\n✓ 所有测试通过！\n")
        return True
    except AssertionError as e:
        print(f"\n✗ 测试失败: {str(e)}\n")
        return False
    except Exception as e:
        print(f"\n✗ 测试错误: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
