"""
路由模块

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-13
"""

from .ebs_routes import ebs_bp
from .resources_routes import resources_bp

__all__ = ['ebs_bp', 'resources_bp']
