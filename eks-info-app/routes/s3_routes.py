"""
S3 对象存储演示路由

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from storage.s3_storage import S3Storage
from config import Config

# 创建蓝图
s3_bp = Blueprint('s3', __name__, url_prefix='/s3')

# 初始化 S3 存储
try:
    s3_storage = S3Storage(
        bucket_name=Config.S3_BUCKET_NAME,
        region=Config.AWS_REGION
    )
    s3_available = s3_storage.available
except Exception as e:
    s3_storage = None
    s3_available = False
    print(f"S3 存储初始化失败: {str(e)}")


@s3_bp.route('/', methods=['GET'])
def s3_index():
    """S3 演示页面"""
    # 检查是否请求 HTML 格式（浏览器访问）
    if request.accept_mimetypes.best_match(['text/html', 'application/json']) == 'text/html':
        # 返回 HTML 页面
        return render_template('s3.html')
    
    # 否则返回 JSON 数据（API 调用）
    if not s3_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'S3 存储不可用',
            'details': f'存储桶 {Config.S3_BUCKET_NAME} 不可访问或不存在',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取 S3 存储桶信息
        bucket_info = s3_storage.get_bucket_info()
        
        # 获取 IRSA 角色信息
        irsa_info = {
            'service_account': os.environ.get('AWS_ROLE_ARN', 'Not configured'),
            'web_identity_token_file': os.environ.get('AWS_WEB_IDENTITY_TOKEN_FILE', 'Not configured'),
            'using_irsa': bool(os.environ.get('AWS_ROLE_ARN'))
        }
        
        # 列出最近的对象
        recent_objects = s3_storage.list_objects(max_keys=10)
        
        return jsonify({
            's3_info': {
                'bucket_name': Config.S3_BUCKET_NAME,
                'region': Config.AWS_REGION,
                'available': True,
                'bucket_details': bucket_info
            },
            'irsa_info': irsa_info,
            'recent_objects': recent_objects,
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
            'error_type': 's3_access_error',
            'message': '访问 S3 存储时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@s3_bp.route('/upload', methods=['POST'])
def s3_upload():
    """上传数据到 S3"""
    if not s3_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'S3 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取请求数据
        data = request.get_json() or {}
        content = data.get('content', '')
        key_name = data.get('key', '')
        
        if not content:
            return jsonify({
                'error': True,
                'error_type': 'invalid_input',
                'message': '内容不能为空',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        
        # 如果没有提供键名，自动生成
        if not key_name:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            key_name = f"data_{Config.POD_NAME}_{timestamp}.json"
        
        # 准备对象数据
        object_data = {
            'content': content,
            'pod_name': Config.POD_NAME,
            'node_name': Config.NODE_NAME,
            'namespace': Config.POD_NAMESPACE,
            'client_ip': request.remote_addr,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # 准备元数据
        metadata = {
            'pod_name': Config.POD_NAME,
            'node_name': Config.NODE_NAME,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # 转换为字节
        data_bytes = json.dumps(object_data, ensure_ascii=False, indent=2).encode('utf-8')
        
        # 上传到 S3
        success = s3_storage.upload_object(
            key=key_name,
            data=data_bytes,
            metadata=metadata
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '数据上传成功',
                'object': {
                    'key': key_name,
                    'size_bytes': len(data_bytes),
                    'bucket': Config.S3_BUCKET_NAME,
                    'metadata': metadata
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        else:
            return jsonify({
                'error': True,
                'error_type': 'upload_failed',
                'message': '数据上传失败',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 500
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 's3_upload_error',
            'message': '上传数据时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@s3_bp.route('/list', methods=['GET'])
def s3_list():
    """列出 S3 对象"""
    if not s3_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'S3 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取查询参数
        prefix = request.args.get('prefix', '')
        max_keys = request.args.get('max_keys', 100, type=int)
        max_keys = min(max_keys, 1000)  # 最多返回 1000 个
        
        # 列出对象
        objects = s3_storage.list_objects(prefix=prefix, max_keys=max_keys)
        
        return jsonify({
            'success': True,
            'objects': objects,
            'count': len(objects),
            'bucket': Config.S3_BUCKET_NAME,
            'prefix': prefix,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 's3_list_error',
            'message': '列出对象时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@s3_bp.route('/download/<path:key>', methods=['GET'])
def s3_download(key: str):
    """下载 S3 对象"""
    if not s3_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'S3 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 下载对象
        data = s3_storage.download_object(key)
        
        if data is None:
            return jsonify({
                'error': True,
                'error_type': 'object_not_found',
                'message': f'对象不存在: {key}',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 404
        
        # 尝试解析为 JSON
        try:
            content = json.loads(data.decode('utf-8'))
            is_json = True
        except:
            content = data.decode('utf-8', errors='replace')
            is_json = False
        
        # 获取对象元数据
        metadata = s3_storage.get_object_metadata(key)
        
        return jsonify({
            'success': True,
            'object': {
                'key': key,
                'content': content,
                'is_json': is_json,
                'size_bytes': len(data),
                'metadata': metadata
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 's3_download_error',
            'message': '下载对象时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@s3_bp.route('/delete/<path:key>', methods=['DELETE'])
def s3_delete(key: str):
    """删除 S3 对象"""
    if not s3_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'S3 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 删除对象
        success = s3_storage.delete_object(key)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'对象删除成功: {key}',
                'key': key,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        else:
            return jsonify({
                'error': True,
                'error_type': 'delete_failed',
                'message': '对象删除失败',
                'key': key,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 500
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 's3_delete_error',
            'message': '删除对象时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@s3_bp.route('/info', methods=['GET'])
def s3_info():
    """获取 S3 详细信息"""
    if not s3_available:
        return jsonify({
            'error': True,
            'error_type': 'storage_unavailable',
            'message': 'S3 存储不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取存储桶信息
        bucket_info = s3_storage.get_bucket_info()
        
        # 获取 IRSA 信息
        irsa_info = {
            'role_arn': os.environ.get('AWS_ROLE_ARN', 'Not configured'),
            'web_identity_token_file': os.environ.get('AWS_WEB_IDENTITY_TOKEN_FILE', 'Not configured'),
            'region': os.environ.get('AWS_REGION', Config.AWS_REGION),
            'using_irsa': bool(os.environ.get('AWS_ROLE_ARN'))
        }
        
        return jsonify({
            'bucket_info': bucket_info,
            'irsa_info': irsa_info,
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
            'error_type': 's3_info_error',
            'message': '获取 S3 信息时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500
