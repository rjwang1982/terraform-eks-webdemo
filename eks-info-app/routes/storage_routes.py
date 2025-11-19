"""
存储概览路由

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from services.storage_service import StorageService
from config import Config

# 创建蓝图
storage_bp = Blueprint('storage', __name__, url_prefix='/storage')

# 初始化存储服务
try:
    storage_service = StorageService(
        ebs_mount_path=Config.EBS_MOUNT_PATH,
        efs_mount_path=Config.EFS_MOUNT_PATH,
        s3_bucket_name=Config.S3_BUCKET_NAME,
        aws_region=Config.AWS_REGION
    )
    storage_available = True
except Exception as e:
    storage_service = None
    storage_available = False
    print(f"存储服务初始化失败: {str(e)}")


@storage_bp.route('/', methods=['GET'])
def storage_overview():
    """
    存储概览页面
    
    显示所有存储系统的概览信息，包括：
    - 所有挂载点信息
    - EBS 配置和状态
    - EFS 配置和状态
    - S3 配置和状态
    - 到各存储演示页面的导航链接
    """
    # 检查是否请求 JSON 格式
    if request.accept_mimetypes.best_match(['text/html', 'application/json']) == 'application/json':
        if not storage_available:
            return jsonify({
                'error': True,
                'error_type': 'service_unavailable',
                'message': '存储服务不可用',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503
        
        try:
            # 获取存储摘要
            summary = storage_service.get_storage_summary()
            
            # 获取挂载点信息
            mount_points = storage_service.get_mount_points()
            
            # 获取详细信息
            ebs_info = storage_service.get_ebs_info()
            efs_info = storage_service.get_efs_info()
            s3_info = storage_service.get_s3_info()
            
            # 构建导航链接
            navigation = {
                'ebs_demo': '/ebs',
                'efs_demo': '/efs',
                's3_demo': '/s3',
                'ebs_available': ebs_info['available'],
                'efs_available': efs_info['available'],
                's3_available': s3_info['available']
            }
            
            return jsonify({
                'summary': summary,
                'mount_points': mount_points,
                'storage_details': {
                    'ebs': ebs_info,
                    'efs': efs_info,
                    's3': s3_info
                },
                'navigation': navigation,
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
                'error_type': 'storage_overview_error',
                'message': '获取存储概览时发生错误',
                'details': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 500
    else:
        # 返回 HTML 页面
        return render_template('storage.html')


@storage_bp.route('/summary', methods=['GET'])
def storage_summary():
    """
    获取存储摘要信息
    
    返回所有存储系统的简要统计信息
    """
    if not storage_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '存储服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        summary = storage_service.get_storage_summary()
        
        return jsonify({
            'success': True,
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'summary_error',
            'message': '获取存储摘要时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@storage_bp.route('/mounts', methods=['GET'])
def storage_mounts():
    """
    获取所有挂载点信息
    
    返回系统中所有数据挂载点的详细信息
    """
    if not storage_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '存储服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        mount_points = storage_service.get_mount_points()
        
        return jsonify({
            'success': True,
            'mount_points': mount_points,
            'count': len(mount_points),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'mounts_error',
            'message': '获取挂载点信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@storage_bp.route('/ebs', methods=['GET'])
def storage_ebs_info():
    """
    获取 EBS 详细信息
    
    返回 EBS 存储的配置和状态信息
    """
    if not storage_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '存储服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        ebs_info = storage_service.get_ebs_info()
        
        return jsonify({
            'success': True,
            'ebs': ebs_info,
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


@storage_bp.route('/efs', methods=['GET'])
def storage_efs_info():
    """
    获取 EFS 详细信息
    
    返回 EFS 存储的配置和状态信息
    """
    if not storage_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '存储服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        efs_info = storage_service.get_efs_info()
        
        return jsonify({
            'success': True,
            'efs': efs_info,
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


@storage_bp.route('/s3', methods=['GET'])
def storage_s3_info():
    """
    获取 S3 详细信息
    
    返回 S3 存储的配置和状态信息
    """
    if not storage_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '存储服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        s3_info = storage_service.get_s3_info()
        
        return jsonify({
            'success': True,
            's3': s3_info,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 's3_info_error',
            'message': '获取 S3 信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@storage_bp.route('/health', methods=['GET'])
def storage_health():
    """
    存储健康检查
    
    检查所有存储系统的可用性
    """
    if not storage_available:
        return jsonify({
            'healthy': False,
            'error': '存储服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        ebs_info = storage_service.get_ebs_info()
        efs_info = storage_service.get_efs_info()
        s3_info = storage_service.get_s3_info()
        
        health_status = {
            'healthy': True,
            'storage_systems': {
                'ebs': {
                    'available': ebs_info['available'],
                    'mounted': ebs_info.get('mounted', False),
                    'error': ebs_info.get('error')
                },
                'efs': {
                    'available': efs_info['available'],
                    'mounted': efs_info.get('mounted', False),
                    'error': efs_info.get('error')
                },
                's3': {
                    'available': s3_info['available'],
                    'error': s3_info.get('error')
                }
            },
            'available_count': sum([
                ebs_info['available'],
                efs_info['available'],
                s3_info['available']
            ]),
            'total_count': 3,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # 如果所有存储系统都不可用，返回不健康状态
        if health_status['available_count'] == 0:
            health_status['healthy'] = False
            return jsonify(health_status), 503
        
        return jsonify(health_status)
    except Exception as e:
        return jsonify({
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500
