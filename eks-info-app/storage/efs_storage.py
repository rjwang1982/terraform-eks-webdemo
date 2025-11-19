"""
EFS 共享文件系统访问类

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class EFSStorage:
    """EFS 共享文件系统访问类"""
    
    def __init__(self, mount_path: str):
        """
        初始化 EFS 存储
        
        Args:
            mount_path: EFS 文件系统挂载路径
        """
        self.mount_path = Path(mount_path)
        
        # 确保挂载路径存在
        if not self.mount_path.exists():
            raise ValueError(f"EFS 挂载路径不存在: {mount_path}")
        
        # 确保挂载路径可写
        if not os.access(self.mount_path, os.W_OK):
            raise ValueError(f"EFS 挂载路径不可写: {mount_path}")
    
    def write_file(self, filename: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        写入文件到 EFS
        
        Args:
            filename: 文件名
            content: 文件内容
            metadata: 元数据字典（可选）
            
        Returns:
            bool: 写入是否成功
        """
        try:
            file_path = self.mount_path / filename
            
            # 准备文件数据
            file_data = {
                'content': content,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            # 如果元数据中没有创建时间，添加它
            if 'created_at' not in file_data['metadata']:
                file_data['metadata']['created_at'] = file_data['created_at']
            
            # 写入文件（JSON 格式）
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"写入文件失败: {str(e)}")
            return False
    
    def read_file(self, filename: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        读取文件内容和元数据
        
        Args:
            filename: 文件名
            
        Returns:
            Tuple[Optional[str], Optional[Dict]]: (内容, 元数据) 元组，失败时返回 (None, None)
        """
        try:
            file_path = self.mount_path / filename
            
            if not file_path.exists():
                return None, None
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            content = file_data.get('content', '')
            metadata = file_data.get('metadata', {})
            
            return content, metadata
        except Exception as e:
            print(f"读取文件失败: {str(e)}")
            return None, None
    
    def list_files(self) -> List[Dict]:
        """
        列出所有文件
        
        Returns:
            List[Dict]: 文件信息列表
        """
        try:
            files = []
            
            # 遍历挂载路径下的所有文件
            for item in self.mount_path.iterdir():
                if item.is_file():
                    try:
                        stat = item.stat()
                        
                        # 尝试读取文件元数据
                        metadata = {}
                        try:
                            with open(item, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                                metadata = file_data.get('metadata', {})
                        except:
                            pass
                        
                        files.append({
                            'filename': item.name,
                            'path': str(item),
                            'size_bytes': stat.st_size,
                            'size_kb': round(stat.st_size / 1024, 2),
                            'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat() + 'Z',
                            'metadata': metadata
                        })
                    except Exception as e:
                        print(f"获取文件信息失败 {item.name}: {str(e)}")
                        continue
            
            # 按修改时间倒序排序
            files.sort(key=lambda x: x['modified_time'], reverse=True)
            
            return files
        except Exception as e:
            print(f"列出文件失败: {str(e)}")
            return []
    
    def delete_file(self, filename: str) -> bool:
        """
        删除文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 删除是否成功
        """
        try:
            file_path = self.mount_path / filename
            
            if not file_path.exists():
                return False
            
            # 删除文件
            file_path.unlink()
            
            return True
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return False
    
    def get_filesystem_usage(self) -> Dict:
        """
        获取文件系统使用情况
        
        Returns:
            Dict: 文件系统使用信息
        """
        try:
            stat = shutil.disk_usage(self.mount_path)
            
            # 统计文件数量和总大小
            file_count = 0
            total_file_size = 0
            
            for item in self.mount_path.iterdir():
                if item.is_file():
                    file_count += 1
                    try:
                        total_file_size += item.stat().st_size
                    except:
                        pass
            
            return {
                'mount_path': str(self.mount_path),
                'total_bytes': stat.total,
                'used_bytes': stat.used,
                'free_bytes': stat.free,
                'total_gb': round(stat.total / (1024**3), 2),
                'used_gb': round(stat.used / (1024**3), 2),
                'free_gb': round(stat.free / (1024**3), 2),
                'usage_percent': round((stat.used / stat.total) * 100, 2),
                'file_count': file_count,
                'total_file_size_bytes': total_file_size,
                'total_file_size_mb': round(total_file_size / (1024**2), 2),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except Exception as e:
            return {
                'error': True,
                'message': f"获取文件系统使用情况失败: {str(e)}",
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
