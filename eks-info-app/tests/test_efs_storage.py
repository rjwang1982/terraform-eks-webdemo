"""
EFS 存储类测试

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import sys
import os
from pathlib import Path
from storage.efs_storage import EFSStorage


def test_efs_storage():
    """测试 EFS 存储类的所有功能"""
    
    # 创建临时测试目录
    test_dir = Path('/tmp/test_efs')
    test_dir.mkdir(exist_ok=True)
    print(f'✓ 创建测试目录: {test_dir}')
    
    # 测试初始化
    try:
        efs = EFSStorage(str(test_dir))
        print('✓ EFSStorage 初始化成功')
    except Exception as e:
        print(f'✗ 初始化失败: {e}')
        return False
    
    # 测试写入文件
    try:
        metadata = {'test': 'data', 'pod': 'test-pod'}
        success = efs.write_file('test_file.json', 'Hello from EFS!', metadata)
        if success:
            print('✓ 写入文件成功')
        else:
            print('✗ 写入文件失败')
            return False
    except Exception as e:
        print(f'✗ 写入文件异常: {e}')
        return False
    
    # 测试读取文件
    try:
        content, meta = efs.read_file('test_file.json')
        if content == 'Hello from EFS!' and meta.get('test') == 'data':
            print('✓ 读取文件成功')
        else:
            print(f'✗ 读取文件内容不匹配: content={content}, meta={meta}')
            return False
    except Exception as e:
        print(f'✗ 读取文件异常: {e}')
        return False
    
    # 测试列出文件
    try:
        files = efs.list_files()
        if len(files) == 1 and files[0]['filename'] == 'test_file.json':
            print('✓ 列出文件成功')
        else:
            print(f'✗ 列出文件结果不正确: {files}')
            return False
    except Exception as e:
        print(f'✗ 列出文件异常: {e}')
        return False
    
    # 测试获取文件系统使用情况
    try:
        usage = efs.get_filesystem_usage()
        if 'total_bytes' in usage and 'file_count' in usage:
            print(f'✓ 获取文件系统使用情况成功 (文件数: {usage["file_count"]})')
        else:
            print(f'✗ 文件系统使用情况数据不完整: {usage}')
            return False
    except Exception as e:
        print(f'✗ 获取文件系统使用情况异常: {e}')
        return False
    
    # 测试删除文件
    try:
        success = efs.delete_file('test_file.json')
        if success:
            print('✓ 删除文件成功')
        else:
            print('✗ 删除文件失败')
            return False
    except Exception as e:
        print(f'✗ 删除文件异常: {e}')
        return False
    
    # 验证文件已删除
    try:
        files = efs.list_files()
        if len(files) == 0:
            print('✓ 验证文件已删除')
        else:
            print(f'✗ 文件未被删除: {files}')
            return False
    except Exception as e:
        print(f'✗ 验证删除异常: {e}')
        return False
    
    print('\n所有测试通过！')
    return True


if __name__ == '__main__':
    success = test_efs_storage()
    sys.exit(0 if success else 1)
