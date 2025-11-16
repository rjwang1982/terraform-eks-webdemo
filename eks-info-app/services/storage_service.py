"""
存储服务类 - 管理所有存储操作

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from storage.ebs_storage import EBSStorage
from storage.efs_storage import EFSStorage
from storage.s3_storage import S3Storage


class StorageService:
    """存储服务类 - 统一管理 EBS、EFS 和 S3 存储"""
    
    def __init__(self, ebs_mount_path: str, efs_mount_path: str, s3_bucket_name: str, aws_region: str = 'ap-southeast-1'):
        """
        初始化存储服务
        
        Args:
            ebs_mount_path: EBS 卷挂载路径
            efs_mount_path: EFS 文件系统挂载路径
            s3_bucket_name: S3 存储桶名称
            aws_region: AWS 区域
        """
        self.ebs_mount_path = ebs_mount_path
        self.efs_mount_path = efs_mount_path
        self.s3_bucket_name = s3_bucket_name
        self.aws_region = aws_region
        
        # 初始化存储客户端
        self.ebs_storage = None
        self.efs_storage = None
        self.s3_storage = None
        
        # 尝试初始化 EBS 存储
        try:
            self.ebs_storage = EBSStorage(ebs_mount_path)
        except Exception as e:
            print(f"EBS 存储初始化失败: {str(e)}")
        
        # 尝试初始化 EFS 存储
        try:
            self.efs_storage = EFSStorage(efs_mount_path)
        except Exception as e:
            print(f"EFS 存储初始化失败: {str(e)}")
        
        # 尝试初始化 S3 存储
        try:
            self.s3_storage = S3Storage(s3_bucket_name, aws_region)
        except Exception as e:
            print(f"S3 存储初始化失败: {str(e)}")
    
    def get_mount_points(self) -> List[Dict]:
        """
        获取所有挂载点信息
        
        Returns:
            List[Dict]: 挂载点信息列表
        """
        mount_points = []
        
        try:
            # 读取 /proc/mounts 获取挂载信息
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        device = parts[0]
                        mount_point = parts[1]
                        fs_type = parts[2]
                        options = parts[3]
                        
                        # 过滤掉系统挂载点，只保留数据挂载点
                        if mount_point.startswith('/data') or mount_point.startswith('/mnt'):
                            try:
                                # 获取磁盘使用情况
                                stat = shutil.disk_usage(mount_point)
                                
                                mount_points.append({
                                    'device': device,
                                    'mount_point': mount_point,
                                    'filesystem_type': fs_type,
                                    'options': options,
                                    'total_bytes': stat.total,
                                    'used_bytes': stat.used,
                                    'free_bytes': stat.free,
                                    'total_gb': round(stat.total / (1024**3), 2),
                                    'used_gb': round(stat.used / (1024**3), 2),
                                    'free_gb': round(stat.free / (1024**3), 2),
                                    'usage_percent': round((stat.used / stat.total) * 100, 2) if stat.total > 0 else 0
                                })
                            except Exception as e:
                                print(f"获取挂载点 {mount_point} 使用情况失败: {str(e)}")
                                mount_points.append({
                                    'device': device,
                                    'mount_point': mount_point,
                                    'filesystem_type': fs_type,
                                    'options': options,
                                    'error': str(e)
                                })
        except Exception as e:
            print(f"读取挂载点信息失败: {str(e)}")
        
        return mount_points
    
    def get_ebs_info(self) -> Dict:
        """
        获取 EBS 配置和状态信息
        
        Returns:
            Dict: EBS 信息
        """
        info = {
            'type': 'EBS',
            'name': 'Elastic Block Store',
            'mount_path': self.ebs_mount_path,
            'available': self.ebs_storage is not None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        if self.ebs_storage:
            try:
                # 获取磁盘使用情况
                disk_usage = self.ebs_storage.get_disk_usage()
                info.update({
                    'disk_usage': disk_usage,
                    'access_mode': 'ReadWriteOnce',
                    'description': 'EBS 块存储卷，用于单 Pod 持久化数据存储'
                })
                
                # 获取日志文件信息
                log_info = self.ebs_storage.get_log_file_info()
                info['log_file'] = log_info
                
                # 检查挂载点是否存在
                mount_path = Path(self.ebs_mount_path)
                info['mounted'] = mount_path.exists() and mount_path.is_dir()
                
            except Exception as e:
                info['error'] = str(e)
        else:
            info['error'] = 'EBS 存储未初始化'
        
        return info
    
    def get_efs_info(self) -> Dict:
        """
        获取 EFS 配置和状态信息
        
        Returns:
            Dict: EFS 信息
        """
        info = {
            'type': 'EFS',
            'name': 'Elastic File System',
            'mount_path': self.efs_mount_path,
            'available': self.efs_storage is not None,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        if self.efs_storage:
            try:
                # 获取文件系统使用情况
                fs_usage = self.efs_storage.get_filesystem_usage()
                info.update({
                    'filesystem_usage': fs_usage,
                    'access_mode': 'ReadWriteMany',
                    'description': 'EFS 共享文件系统，支持多 Pod 同时读写'
                })
                
                # 列出文件
                files = self.efs_storage.list_files()
                info['file_count'] = len(files)
                info['recent_files'] = files[:5]  # 最近的 5 个文件
                
                # 检查挂载点是否存在
                mount_path = Path(self.efs_mount_path)
                info['mounted'] = mount_path.exists() and mount_path.is_dir()
                
            except Exception as e:
                info['error'] = str(e)
        else:
            info['error'] = 'EFS 存储未初始化'
        
        return info
    
    def get_s3_info(self) -> Dict:
        """
        获取 S3 配置和状态信息
        
        Returns:
            Dict: S3 信息
        """
        info = {
            'type': 'S3',
            'name': 'Simple Storage Service',
            'bucket_name': self.s3_bucket_name,
            'region': self.aws_region,
            'available': self.s3_storage is not None and self.s3_storage.available,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        if self.s3_storage and self.s3_storage.available:
            try:
                # 获取存储桶信息
                bucket_info = self.s3_storage.get_bucket_info()
                info.update({
                    'bucket_info': bucket_info,
                    'access_mode': 'API',
                    'description': 'S3 对象存储，通过 IRSA 访问，支持大规模数据存储'
                })
                
                # 获取 IRSA 角色信息（从环境变量）
                service_account = os.environ.get('AWS_ROLE_ARN', 'Not configured')
                info['irsa_role'] = service_account
                
                # 列出最近的对象
                objects = self.s3_storage.list_objects(max_keys=5)
                info['object_count'] = bucket_info.get('object_count', 0)
                info['recent_objects'] = objects
                
            except Exception as e:
                info['error'] = str(e)
        else:
            info['error'] = 'S3 存储未初始化或不可用'
        
        return info
    
    def get_storage_summary(self) -> Dict:
        """
        获取所有存储系统的摘要信息
        
        Returns:
            Dict: 存储摘要信息
        """
        summary = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'storage_types': []
        }
        
        # EBS 摘要
        ebs_info = self.get_ebs_info()
        summary['storage_types'].append({
            'type': 'EBS',
            'name': 'Elastic Block Store',
            'available': ebs_info['available'],
            'mount_path': ebs_info['mount_path'],
            'usage_percent': ebs_info.get('disk_usage', {}).get('usage_percent', 0) if ebs_info['available'] else 0,
            'total_gb': ebs_info.get('disk_usage', {}).get('total_gb', 0) if ebs_info['available'] else 0,
            'used_gb': ebs_info.get('disk_usage', {}).get('used_gb', 0) if ebs_info['available'] else 0
        })
        
        # EFS 摘要
        efs_info = self.get_efs_info()
        summary['storage_types'].append({
            'type': 'EFS',
            'name': 'Elastic File System',
            'available': efs_info['available'],
            'mount_path': efs_info['mount_path'],
            'file_count': efs_info.get('file_count', 0) if efs_info['available'] else 0,
            'usage_percent': efs_info.get('filesystem_usage', {}).get('usage_percent', 0) if efs_info['available'] else 0,
            'total_gb': efs_info.get('filesystem_usage', {}).get('total_gb', 0) if efs_info['available'] else 0,
            'used_gb': efs_info.get('filesystem_usage', {}).get('used_gb', 0) if efs_info['available'] else 0
        })
        
        # S3 摘要
        s3_info = self.get_s3_info()
        summary['storage_types'].append({
            'type': 'S3',
            'name': 'Simple Storage Service',
            'available': s3_info['available'],
            'bucket_name': s3_info['bucket_name'],
            'object_count': s3_info.get('object_count', 0) if s3_info['available'] else 0,
            'total_size_gb': s3_info.get('bucket_info', {}).get('total_size_gb', 0) if s3_info['available'] else 0
        })
        
        # 统计可用的存储系统数量
        summary['available_count'] = sum(1 for st in summary['storage_types'] if st['available'])
        summary['total_count'] = len(summary['storage_types'])
        
        return summary
