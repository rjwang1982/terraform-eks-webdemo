"""
EBS 存储演示路由

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from storage.ebs_storage import EBSStorage
from config import Config

# 创建蓝图
ebs_bp = Blueprint('ebs', __name__, url_prefix='/ebs')

# 初始化 EBS 存储
try:
    ebs_storage = EBSStorage(Config.EBS_MOUNT_PATH)
    ebs_available = True
except Exception as e:
    ebs_storage = None
    ebs_available = False
    print(f"EBS 存储初始化失败: {str(e)}")


@ebs_bp.route('/', methods=['GET'])
def ebs_index():
    """EBS 演示页面"""
    # 检查是否请求 JSON 格式
    if request.accept_mimetypes.best_match(['text/html', 'application/json']) == 'application/json':
        # 返回 JSON 数据
        if not ebs_available:
            return jsonify({
                'error': True,
                'error_type': 'storage_unavailable',
                'message': 'EBS 存储不可用',
                'details': f'挂载路径 {Config.EBS_MOUNT_PATH} 不可访问',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503
        
        try:
            # 记录访问日志
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'pod_name': Config.POD_NAME,
                'node_name': Config.NODE_NAME,
                'client_ip': request.remote_addr,
                'request_path': request.path,
                'request_method': request.method,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }
            ebs_storage.write_log(log_entry)
            
            # 获取 EBS 信息
            disk_usage = ebs_storage.get_disk_usage()
            log_file_info = ebs_storage.get_log_file_info()
            
            # 获取最近的日志记录
            recent_logs = ebs_storage.read_logs(limit=10)
            
            return jsonify({
                'ebs_info': {
                    'mount_path': Config.EBS_MOUNT_PATH,
                    'available': True,
                    'disk_usage': disk_usage,
                    'log_file': log_file_info
                },
                'recent_logs': recent_logs,
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
                'error_type': 'ebs_access_error',
                'message': '访问 EBS 存储时发生错误',
                'details': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 500
    else:
        # 返回 HTML 页面
        return render_template('ebs.html')


@ebs_bp.route('/write', methods=['POST'])
def ebs_write():
    """写入数据到 EBS"""
    if not ebs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EBS 存储不可用',
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
        
        # 创建日志条目
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'type': 'user_data',
            'pod_name': Config.POD_NAME,
            'node_name': Config.NODE_NAME,
            'client_ip': request.remote_addr,
            'content': content
        }
        
        # 写入数据
        success = ebs_storage.write_log(log_entry)
        
        if success:
            return jsonify({
                'success': True,
                'message': '数据写入成功',
                'entry': log_entry,
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
            'error_type': 'ebs_write_error',
            'message': '写入数据时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@ebs_bp.route('/read', methods=['GET'])
def ebs_read():
    """读取 EBS 数据"""
    if not ebs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EBS 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 500)  # 最多返回 500 条
        
        # 读取日志
        logs = ebs_storage.read_logs(limit=limit)
        
        # 记录访问日志
        access_log = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'type': 'read_access',
            'pod_name': Config.POD_NAME,
            'node_name': Config.NODE_NAME,
            'client_ip': request.remote_addr,
            'request_path': request.path,
            'records_returned': len(logs)
        }
        ebs_storage.write_log(access_log)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs),
            'limit': limit,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'ebs_read_error',
            'message': '读取数据时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@ebs_bp.route('/info', methods=['GET'])
def ebs_info():
    """获取 EBS 详细信息"""
    if not ebs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EBS 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        disk_usage = ebs_storage.get_disk_usage()
        log_file_info = ebs_storage.get_log_file_info()
        
        return jsonify({
            'mount_path': Config.EBS_MOUNT_PATH,
            'disk_usage': disk_usage,
            'log_file': log_file_info,
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
            'error_type': 'ebs_info_error',
            'message': '获取 EBS 信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@ebs_bp.route('/cleanup', methods=['POST'])
def ebs_cleanup():
    """清理旧日志"""
    if not ebs_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'EBS 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取请求参数
        data = request.get_json() or {}
        days = data.get('days', 7)
        
        # 清理日志
        deleted_count = ebs_storage.cleanup_old_logs(days=days)
        
        return jsonify({
            'success': True,
            'message': f'清理完成，删除了 {deleted_count} 条旧日志',
            'deleted_count': deleted_count,
            'days': days,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'cleanup_error',
            'message': '清理日志时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500
