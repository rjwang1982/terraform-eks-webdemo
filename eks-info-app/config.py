"""
应用配置文件

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-13
"""

import os

class Config:
    """应用配置类"""
    
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'eks-info-app-secret-key-change-in-production')
    JSON_AS_ASCII = False
    
    # 存储配置
    EBS_MOUNT_PATH = os.environ.get('EBS_MOUNT_PATH', '/data/ebs')
    EFS_MOUNT_PATH = os.environ.get('EFS_MOUNT_PATH', '/data/efs')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'eks-info-app-data')
    
    # Kubernetes 配置
    POD_NAME = os.environ.get('POD_NAME', 'unknown-pod')
    POD_NAMESPACE = os.environ.get('POD_NAMESPACE', 'default')
    NODE_NAME = os.environ.get('NODE_NAME', 'unknown-node')
    
    # AWS 配置
    AWS_REGION = os.environ.get('AWS_REGION', 'ap-southeast-1')
    AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-1')
    
    # 应用配置
    APP_VERSION = '1.0.0'
    APP_NAME = 'EKS Info WebApp'
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # 缓存配置（秒）
    CACHE_AWS_API_TTL = 300  # 5 分钟
    CACHE_K8S_API_TTL = 60   # 1 分钟
    
    # 压力测试配置
    STRESS_TEST_MAX_DURATION = 300  # 最大 5 分钟
    STRESS_TEST_DEFAULT_DURATION = 60  # 默认 60 秒
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        pass

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
