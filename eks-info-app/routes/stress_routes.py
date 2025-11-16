"""
压力测试路由

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from services.stress_test_service import StressTestService
from config import Config

# 创建蓝图
stress_bp = Blueprint('stress', __name__, url_prefix='/stress')

# 初始化压力测试服务
try:
    stress_service = StressTestService()
    stress_available = True
except Exception as e:
    stress_service = None
    stress_available = False
    print(f"压力测试服务初始化失败: {str(e)}")


@stress_bp.route('/', methods=['GET'])
def stress_overview():
    """
    压力测试界面
    
    显示压力测试的主界面，包括：
    - 当前 CPU 和内存使用率
    - 启动 CPU 压力测试的选项
    - 启动内存压力测试的选项
    - 测试配置选项（持续时间、强度）
    - 活动测试列表
    """
    # 检查是否请求 HTML 格式（浏览器访问）
    if request.accept_mimetypes.best_match(['text/html', 'application/json']) == 'text/html':
        # 返回 HTML 页面
        return render_template('stress.html')
    
    # 否则返回 JSON 数据（API 调用）
    if not stress_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '压力测试服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取当前资源使用情况
        current_cpu = stress_service.get_current_cpu_usage()
        current_memory = stress_service.get_current_memory_usage()
        
        # 获取所有活动测试
        active_tests = stress_service.get_all_active_tests()
        
        # 构建响应
        return jsonify({
            'current_resources': {
                'cpu': {
                    'usage_percent': current_cpu,
                    'description': 'CPU 使用率'
                },
                'memory': current_memory
            },
            'active_tests': active_tests,
            'active_tests_count': len(active_tests),
            'test_options': {
                'cpu': {
                    'duration_range': [1, 300],
                    'intensity_range': [1, 100],
                    'default_duration': 60,
                    'default_intensity': 100
                },
                'memory': {
                    'duration_range': [1, 300],
                    'target_mb_range': [10, 400],
                    'default_duration': 60,
                    'default_target_mb': 100
                }
            },
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
            'error_type': 'stress_overview_error',
            'message': '获取压力测试界面时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@stress_bp.route('/cpu/start', methods=['POST'])
def start_cpu_stress():
    """
    启动 CPU 压力测试
    
    请求体参数：
    - duration: 持续时间（秒），默认 60，范围 1-300
    - intensity: 强度级别（1-100），默认 100
    
    返回：
    - test_id: 测试 ID
    - status: 测试状态
    """
    if not stress_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '压力测试服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取请求参数
        data = request.get_json() or {}
        duration = data.get('duration', 60)
        intensity = data.get('intensity', 100)
        
        # 验证参数
        try:
            duration = int(duration)
            intensity = int(intensity)
        except (ValueError, TypeError):
            return jsonify({
                'error': True,
                'error_type': 'invalid_parameters',
                'message': '参数必须是整数',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        
        # 启动测试
        test_id = stress_service.start_cpu_stress(duration=duration, intensity=intensity)
        
        # 获取测试状态
        test_status = stress_service.get_stress_status(test_id)
        
        return jsonify({
            'success': True,
            'test_id': test_id,
            'test_status': test_status,
            'message': f'CPU 压力测试已启动，持续时间 {duration} 秒，强度 {intensity}%',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 201
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'start_cpu_stress_error',
            'message': '启动 CPU 压力测试时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@stress_bp.route('/memory/start', methods=['POST'])
def start_memory_stress():
    """
    启动内存压力测试
    
    请求体参数：
    - duration: 持续时间（秒），默认 60，范围 1-300
    - target_mb: 目标内存大小（MB），默认 100，范围 10-400
    
    返回：
    - test_id: 测试 ID
    - status: 测试状态
    """
    if not stress_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '压力测试服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取请求参数
        data = request.get_json() or {}
        duration = data.get('duration', 60)
        target_mb = data.get('target_mb', 100)
        
        # 验证参数
        try:
            duration = int(duration)
            target_mb = int(target_mb)
        except (ValueError, TypeError):
            return jsonify({
                'error': True,
                'error_type': 'invalid_parameters',
                'message': '参数必须是整数',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        
        # 启动测试
        test_id = stress_service.start_memory_stress(duration=duration, target_mb=target_mb)
        
        # 获取测试状态
        test_status = stress_service.get_stress_status(test_id)
        
        return jsonify({
            'success': True,
            'test_id': test_id,
            'test_status': test_status,
            'message': f'内存压力测试已启动，持续时间 {duration} 秒，目标 {target_mb} MB',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 201
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'start_memory_stress_error',
            'message': '启动内存压力测试时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@stress_bp.route('/status/<test_id>', methods=['GET'])
def get_test_status(test_id):
    """
    获取测试状态
    
    路径参数：
    - test_id: 测试 ID
    
    返回：
    - 测试的详细状态信息
    """
    if not stress_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '压力测试服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        test_status = stress_service.get_stress_status(test_id)
        
        if test_status is None:
            return jsonify({
                'error': True,
                'error_type': 'test_not_found',
                'message': f'测试不存在: {test_id}',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 404
        
        return jsonify({
            'success': True,
            'test_status': test_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'get_status_error',
            'message': '获取测试状态时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@stress_bp.route('/stop/<test_id>', methods=['POST'])
def stop_test(test_id):
    """
    停止测试
    
    路径参数：
    - test_id: 测试 ID
    
    返回：
    - 停止操作的结果
    """
    if not stress_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '压力测试服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        success = stress_service.stop_stress(test_id)
        
        if not success:
            return jsonify({
                'error': True,
                'error_type': 'stop_failed',
                'message': f'停止测试失败: {test_id}',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        
        # 获取更新后的测试状态
        test_status = stress_service.get_stress_status(test_id)
        
        return jsonify({
            'success': True,
            'message': f'测试已停止: {test_id}',
            'test_status': test_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'stop_test_error',
            'message': '停止测试时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@stress_bp.route('/resources', methods=['GET'])
def get_current_resources():
    """
    获取当前资源使用情况
    
    返回：
    - CPU 使用率
    - 内存使用情况
    """
    if not stress_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '压力测试服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        current_cpu = stress_service.get_current_cpu_usage()
        current_memory = stress_service.get_current_memory_usage()
        
        return jsonify({
            'success': True,
            'resources': {
                'cpu': {
                    'usage_percent': current_cpu,
                    'description': 'CPU 使用率'
                },
                'memory': current_memory
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'get_resources_error',
            'message': '获取资源使用情况时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@stress_bp.route('/tests', methods=['GET'])
def get_all_tests():
    """
    获取所有活动测试
    
    返回：
    - 所有活动测试的列表
    """
    if not stress_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '压力测试服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        active_tests = stress_service.get_all_active_tests()
        
        return jsonify({
            'success': True,
            'tests': active_tests,
            'count': len(active_tests),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'get_tests_error',
            'message': '获取测试列表时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500


@stress_bp.route('/cleanup', methods=['POST'])
def cleanup_tests():
    """
    清理已完成的测试记录
    
    请求体参数（可选）：
    - max_age_seconds: 最大保留时间（秒），默认 3600
    
    返回：
    - 清理操作的结果
    """
    if not stress_available:
        return jsonify({
            'error': True,
            'error_type': 'service_unavailable',
            'message': '压力测试服务不可用',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    
    try:
        # 获取请求参数
        data = request.get_json() or {}
        max_age_seconds = data.get('max_age_seconds', 3600)
        
        # 验证参数
        try:
            max_age_seconds = int(max_age_seconds)
        except (ValueError, TypeError):
            return jsonify({
                'error': True,
                'error_type': 'invalid_parameters',
                'message': '参数必须是整数',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        
        # 执行清理
        stress_service.cleanup_completed_tests(max_age_seconds=max_age_seconds)
        
        # 获取剩余的测试
        remaining_tests = stress_service.get_all_active_tests()
        
        return jsonify({
            'success': True,
            'message': '清理完成',
            'remaining_tests_count': len(remaining_tests),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'error_type': 'cleanup_error',
            'message': '清理测试记录时发生错误',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500
