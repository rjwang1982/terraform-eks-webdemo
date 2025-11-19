"""
首页和健康检查路由

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from services.environment_service import EnvironmentService
from services.kubernetes_service import KubernetesService
from services.aws_service import AWSService
from storage.ebs_storage import EBSStorage
from storage.efs_storage import EFSStorage
from storage.s3_storage import S3Storage
import os

logger = logging.getLogger(__name__)

# 创建蓝图
home_bp = Blueprint('home', __name__)

# 初始化服务
env_service = EnvironmentService()


@home_bp.route('/')
def index():
    """
    首页 - 显示完整的环境信息
    
    需求: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
    """
    # 检查是否请求 JSON 格式
    if request.accept_mimetypes.best_match(['text/html', 'application/json']) == 'application/json':
        try:
            logger.info("处理首页 API 请求")
            
            # 获取所有环境信息
            environment_info = env_service.get_all_environment_info()
            
            # 添加应用信息
            app_info = {
                'name': 'EKS Info WebApp',
                'version': '1.0.0',
                'description': 'EKS 环境信息展示和存储演示应用',
                'author': 'RJ.Wang',
                'email': 'wangrenjun@gmail.com'
            }
            
            response_data = {
                'success': True,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'app': app_info,
                'environment': environment_info
            }
            
            logger.info("首页 API 请求处理成功")
            return jsonify(response_data), 200
        
        except Exception as e:
            logger.error(f"处理首页 API 请求失败: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': '获取环境信息失败',
                'details': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 500
    else:
        # 返回 HTML 页面
        logger.info("处理首页 HTML 请求")
        return render_template('index.html')


@home_bp.route('/health')
def health():
    """
    健康检查端点 - 返回基本健康状态
    
    需求: 8.1
    """
    try:
        # 基本健康检查
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': {
                'application': 'ok',
                'python_version': os.sys.version.split()[0]
            }
        }
        
        logger.debug("健康检查: 正常")
        return jsonify(health_status), 200
    
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@home_bp.route('/ready')
def ready():
    """
    就绪检查端点 - 检查存储系统可用性
    
    需求: 8.2, 8.3, 8.4
    """
    try:
        logger.info("执行就绪检查")
        
        readiness_checks = {
            'application': 'ok',
            'storage': {}
        }
        
        all_ready = True
        
        # 检查 EBS 存储
        try:
            ebs_mount_path = os.environ.get('EBS_MOUNT_PATH', '/data/ebs')
            if os.path.exists(ebs_mount_path) and os.access(ebs_mount_path, os.W_OK):
                readiness_checks['storage']['ebs'] = {
                    'status': 'ready',
                    'mount_path': ebs_mount_path,
                    'writable': True
                }
                logger.debug(f"EBS 存储检查: 正常 ({ebs_mount_path})")
            else:
                readiness_checks['storage']['ebs'] = {
                    'status': 'not_ready',
                    'mount_path': ebs_mount_path,
                    'writable': False,
                    'error': '挂载点不存在或不可写'
                }
                all_ready = False
                logger.warning(f"EBS 存储检查: 失败 ({ebs_mount_path})")
        except Exception as e:
            readiness_checks['storage']['ebs'] = {
                'status': 'error',
                'error': str(e)
            }
            all_ready = False
            logger.error(f"EBS 存储检查异常: {str(e)}")
        
        # 检查 EFS 存储
        try:
            efs_mount_path = os.environ.get('EFS_MOUNT_PATH', '/data/efs')
            if os.path.exists(efs_mount_path) and os.access(efs_mount_path, os.W_OK):
                readiness_checks['storage']['efs'] = {
                    'status': 'ready',
                    'mount_path': efs_mount_path,
                    'writable': True
                }
                logger.debug(f"EFS 存储检查: 正常 ({efs_mount_path})")
            else:
                readiness_checks['storage']['efs'] = {
                    'status': 'not_ready',
                    'mount_path': efs_mount_path,
                    'writable': False,
                    'error': '挂载点不存在或不可写'
                }
                all_ready = False
                logger.warning(f"EFS 存储检查: 失败 ({efs_mount_path})")
        except Exception as e:
            readiness_checks['storage']['efs'] = {
                'status': 'error',
                'error': str(e)
            }
            all_ready = False
            logger.error(f"EFS 存储检查异常: {str(e)}")
        
        # 检查 S3 访问
        try:
            s3_bucket = os.environ.get('S3_BUCKET_NAME')
            if s3_bucket:
                # 尝试初始化 S3 存储（这会验证凭证）
                s3_storage = S3Storage(s3_bucket)
                readiness_checks['storage']['s3'] = {
                    'status': 'ready',
                    'bucket_name': s3_bucket,
                    'accessible': True
                }
                logger.debug(f"S3 存储检查: 正常 ({s3_bucket})")
            else:
                readiness_checks['storage']['s3'] = {
                    'status': 'not_configured',
                    'error': 'S3_BUCKET_NAME 环境变量未设置'
                }
                # S3 不是必需的，不影响就绪状态
                logger.warning("S3 存储检查: 未配置")
        except Exception as e:
            readiness_checks['storage']['s3'] = {
                'status': 'error',
                'error': str(e)
            }
            # S3 不是必需的，不影响就绪状态
            logger.error(f"S3 存储检查异常: {str(e)}")
        
        # 构建响应
        response_data = {
            'status': 'ready' if all_ready else 'not_ready',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': readiness_checks
        }
        
        status_code = 200 if all_ready else 503
        
        if all_ready:
            logger.info("就绪检查: 所有系统正常")
        else:
            logger.warning("就绪检查: 部分系统未就绪")
        
        return jsonify(response_data), status_code
    
    except Exception as e:
        logger.error(f"就绪检查失败: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500
