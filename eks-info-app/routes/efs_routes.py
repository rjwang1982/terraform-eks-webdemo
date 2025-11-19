"""
EFS 共享文件系统演示路由

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from storage.efs_storage import EFSStorage
from config import Config

# 创建蓝图
efs_bp = Blueprint('efs', __name__, url_prefix='/efs')

# 初始化 EFS 存储
try:
    efs_storage = EFSStorage(Config.EFS_MOUNT_PATH)
    efs_available = True
except Exception as e:
    efs_storage = None
    efs_available = False
    print(f"EFS 存储初始化失败: {str(e)}")


@efs_bp.route('/', methods=['GET'])
def efs_index():
    """EFS 演示页面"""
    # 检查是否请求 HTML 格式（浏览器访问）
    if request.accept_mimetypes.best_match(['text/html', 'application/json']) == 'text/html':
        # 返回 HTML 页面
        return render_template('efs.html')
    
    # 否则返回 JSON 数据（API 调用）
    if not efs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EFS 存储不可用',
            'details': f'挂载路径 {Config.EFS_MOUNT_PATH} 不可访问',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取 EFS 信息
        filesystem_usage = efs_storage.get_filesystem_usage()
        
        # 获取所有文件列表
        files = efs_storage.list_files()
        
        return jsonify({
            'efs_info': {
                'mount_path': Config.EFS_MOUNT_PATH,
                'available': True,
                'filesystem_usage': filesystem_usage
            },
            'files': files,
            'file_count': len(files),
            'current_pod': {
                'name': Config.POD_NAME,
                'namespace': Config.POD_NAMESPACE,
                'node': Config.NODE_NAME
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'efs_access_error',
            'message': '访问 EFS 存储时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@efs_bp.route('/write', methods=['POST'])
def efs_write():
    """写入数据到 EFS（包含 Pod 名称）"""
    if not efs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EFS 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取请求数据
        data = request.get_json() or {}
        content = data.get('content', '')
        
        if not content:
            return jsonify({
                'error': True,
                'error_type': 'invalid_input',
                'message': '内容不能为空',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        
        # 生成文件名（包含时间戳和 Pod 名称）
        timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"shared_data_{timestamp_str}_{Config.POD_NAME}.json"
        
        # 准备元数据
        metadata = {
            'created_by_pod': Config.POD_NAME,
            'pod_namespace': Config.POD_NAMESPACE,
            'node_name': Config.NODE_NAME,
            'client_ip': request.remote_addr,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'content_type': 'text/plain'
        }
        
        # 写入文件
        success = efs_storage.write_file(filename, content, metadata)
        
        if success:
            return jsonify({
                'success': True,
                'message': '数据写入成功',
                'filename': filename,
                'metadata': metadata,
                'content': content,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        else:
            return jsonify({
                'error': True,
                'error_type': 'write_failed',
                'message': '数据写入失败',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 500
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'efs_write_error',
            'message': '写入数据时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@efs_bp.route('/read', methods=['GET'])
def efs_read():
    """读取所有 Pod 写入的数据"""
    if not efs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EFS 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取所有文件
        files = efs_storage.list_files()
        
        # 读取每个文件的内容
        file_contents = []
        for file_info in files:
            content, metadata = efs_storage.read_file(file_info['filename'])
            if content is not None:
                file_contents.append({
                    'filename': file_info['filename'],
                    'content': content,
                    'metadata': metadata,
                    'size_kb': file_info['size_kb'],
                    'modified_time': file_info['modified_time']
                })
        
        return jsonify({
            'success': True,
            'files': file_contents,
            'count': len(file_contents),
            'current_pod': {
                'name': Config.POD_NAME,
                'namespace': Config.POD_NAMESPACE,
                'node': Config.NODE_NAME
            },
            'message': f'当前请求由 Pod {Config.POD_NAME} 处理',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'efs_read_error',
            'message': '读取数据时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@efs_bp.route('/read/<filename>', methods=['GET'])
def efs_read_file(filename: str):
    """读取指定文件"""
    if not efs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EFS 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 读取文件
        content, metadata = efs_storage.read_file(filename)
        
        if content is None:
            return jsonify({
                'error': True,
                'error_type': 'file_not_found',
                'message': f'文件不存在: {filename}',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 404
        
        return jsonify({
            'success': True,
            'filename': filename,
            'content': content,
            'metadata': metadata,
            'current_pod': {
                'name': Config.POD_NAME,
                'namespace': Config.POD_NAMESPACE,
                'node': Config.NODE_NAME
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'efs_read_error',
            'message': '读取文件时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@efs_bp.route('/delete/<filename>', methods=['DELETE'])
def efs_delete(filename: str):
    """删除指定文件"""
    if not efs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EFS 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 删除文件
        success = efs_storage.delete_file(filename)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'文件删除成功: {filename}',
                'filename': filename,
                'deleted_by_pod': Config.POD_NAME,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        else:
            return jsonify({
                'error': True,
                'error_type': 'file_not_found',
                'message': f'文件不存在或删除失败: {filename}',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 404
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'efs_delete_error',
            'message': '删除文件时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@efs_bp.route('/info', methods=['GET'])
def efs_info():
    """获取 EFS 详细信息"""
    if not efs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EFS 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        filesystem_usage = efs_storage.get_filesystem_usage()
        files = efs_storage.list_files()
        
        return jsonify({
            'mount_path': Config.EFS_MOUNT_PATH,
            'filesystem_usage': filesystem_usage,
            'files': files,
            'file_count': len(files),
            'pod_info': {
                'name': Config.POD_NAME,
                'namespace': Config.POD_NAMESPACE,
                'node': Config.NODE_NAME
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'efs_info_error',
            'message': '获取 EFS 信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@efs_bp.route('/list', methods=['GET'])
def efs_list():
    """列出所有文件"""
    if not efs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EFS 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        files = efs_storage.list_files()
        
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files),
            'current_pod': Config.POD_NAME,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'efs_list_error',
            'message': '列出文件时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500
