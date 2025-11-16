"""
网络信息路由（简化版）

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-15
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
network_bp = Blueprint('network', __name__, url_prefix='/network')


@network_bp.route('/', methods=['GET'])
def network_info():
    """
    网络信息页面
    """
    # 检查是否请求 JSON 格式
    if request.accept_mimetypes.best_match(['text/html', 'application/json']) == 'application/json':
        return jsonify({
            'error': True,
            'error_type': 'temporarily_unavailable',
            'message': '网络信息功能暂时不可用，正在修复中',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503
    else:
        # 返回 HTML 页面
        return render_template('network.html')
