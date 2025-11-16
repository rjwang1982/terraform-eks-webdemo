"""
EKS Info WebApp - 主应用文件

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-13
"""

import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from logging.handlers import RotatingFileHandler

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'eks-info-app-secret-key')
app.config['JSON_AS_ASCII'] = False

# 注册蓝图
from routes.home_routes import home_bp
from routes.ebs_routes import ebs_bp
from routes.efs_routes import efs_bp
from routes.s3_routes import s3_bp
from routes.storage_routes import storage_bp
from routes.stress_routes import stress_bp
from routes.scaling_routes import scaling_bp
from routes.network_routes import network_bp
from routes.resources_routes import resources_bp
app.register_blueprint(home_bp)
app.register_blueprint(ebs_bp)
app.register_blueprint(efs_bp)
app.register_blueprint(s3_bp)
app.register_blueprint(storage_bp)
app.register_blueprint(stress_bp)
app.register_blueprint(scaling_bp)
app.register_blueprint(network_bp)
app.register_blueprint(resources_bp)

# 配置日志
def setup_logging():
    """配置应用日志"""
    # 创建日志格式器
    formatter = logging.Formatter(
        json.dumps({
            'timestamp': '%(asctime)s',
            'level': '%(levelname)s',
            'module': '%(module)s',
            'function': '%(funcName)s',
            'message': '%(message)s'
        })
    )
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 配置应用日志
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    
    # 移除默认处理器
    app.logger.handlers = [console_handler]
    
    app.logger.info("日志系统初始化完成")

# 初始化日志
setup_logging()

# 错误处理器
@app.errorhandler(404)
def not_found_error(error):
    """处理 404 错误"""
    app.logger.warning(f"404 错误: {request.url}")
    return jsonify({
        'error': True,
        'error_type': 'not_found',
        'message': '请求的资源不存在',
        'path': request.path,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    app.logger.error(f"500 错误: {str(error)}")
    return jsonify({
        'error': True,
        'error_type': 'internal_server_error',
        'message': '服务器内部错误',
        'details': str(error),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """处理未捕获的异常"""
    app.logger.error(f"未捕获的异常: {str(error)}", exc_info=True)
    return jsonify({
        'error': True,
        'error_type': 'unexpected_error',
        'message': '发生意外错误',
        'details': str(error),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 500

# 请求前后钩子
@app.before_request
def before_request():
    """请求前记录日志"""
    request.start_time = datetime.utcnow()
    app.logger.info(f"收到请求: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def after_request(response):
    """请求后记录日志"""
    if hasattr(request, 'start_time'):
        duration = (datetime.utcnow() - request.start_time).total_seconds() * 1000
        app.logger.info(f"请求完成: {request.method} {request.path} - {response.status_code} ({duration:.2f}ms)")
    return response

# 首页和健康检查路由已在 home_routes.py 中实现

if __name__ == '__main__':
    app.logger.info("启动 EKS Info WebApp")
    app.logger.info(f"Python 版本: {os.sys.version}")
    app.logger.info(f"工作目录: {os.getcwd()}")
    
    # 启动应用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
