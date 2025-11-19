"""
EBS 存储访问类

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional


class EBSStorage:
    """EBS 块存储访问类"""
    
    def __init__(self, mount_path: str):
        """
        初始化 EBS 存储
        
        Args:
            mount_path: EBS 卷挂载路径
        """
        self.mount_path = Path(mount_path)
        self.log_file = self.mount_path / 'access_logs.jsonl'
        
        # 确保挂载路径存在
        if not self.mount_path.exists():
            raise ValueError(f"EBS 挂载路径不存在: {mount_path}")
        
        # 确保日志文件存在
        if not self.log_file.exists():
            self.log_file.touch()
    
    def write_log(self, entry: Dict) -> bool:
        """
        写入访问日志
        
        Args:
            entry: 日志条目字典
            
        Returns:
            bool: 写入是否成功
        """
        try:
            # 添加时间戳
            if 'timestamp' not in entry:
                entry['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            
            # 追加到日志文件（JSONL 格式）
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            return True
        except Exception as e:
            print(f"写入日志失败: {str(e)}")
            return False
    
    def read_logs(self, limit: int = 100) -> List[Dict]:
        """
        读取日志记录
        
        Args:
            limit: 返回的最大记录数
            
        Returns:
            List[Dict]: 日志记录列表（最新的在前）
        """
        try:
            if not self.log_file.exists():
                return []
            
            logs = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            # 返回最新的 N 条记录
            return logs[-limit:][::-1]
        except Exception as e:
            print(f"读取日志失败: {str(e)}")
            return []
    
    def get_disk_usage(self) -> Dict:
        """
        获取磁盘使用情况
        
        Returns:
            Dict: 磁盘使用信息
        """
        try:
            stat = shutil.disk_usage(self.mount_path)
            
            return {
                'mount_path': str(self.mount_path),
                'total_bytes': stat.total,
                'used_bytes': stat.used,
                'free_bytes': stat.free,
                'total_gb': round(stat.total / (1024**3), 2),
                'used_gb': round(stat.used / (1024**3), 2),
                'free_gb': round(stat.free / (1024**3), 2),
                'usage_percent': round((stat.used / stat.total) * 100, 2),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except Exception as e:
            return {
                'error': True,
                'message': f"获取磁盘使用情况失败: {str(e)}",
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    def cleanup_old_logs(self, days: int = 7) -> int:
        """
        清理旧日志
        
        Args:
            days: 保留最近 N 天的日志
            
        Returns:
            int: 删除的日志条目数
        """
        try:
            if not self.log_file.exists():
                return 0
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            kept_logs = []
            deleted_count = 0
            
            # 读取所有日志
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        log_entry = json.loads(line)
                        timestamp_str = log_entry.get('timestamp', '')
                        
                        # 解析时间戳
                        if timestamp_str:
                            # 移除 'Z' 后缀
                            timestamp_str = timestamp_str.rstrip('Z')
                            log_time = datetime.fromisoformat(timestamp_str)
                            
                            # 保留最近的日志
                            if log_time >= cutoff_date:
                                kept_logs.append(line)
                            else:
                                deleted_count += 1
                        else:
                            # 没有时间戳的保留
                            kept_logs.append(line)
                    except (json.JSONDecodeError, ValueError):
                        # 无法解析的行保留
                        kept_logs.append(line)
            
            # 重写日志文件
            with open(self.log_file, 'w', encoding='utf-8') as f:
                for log_line in kept_logs:
                    f.write(log_line + '\n')
            
            return deleted_count
        except Exception as e:
            print(f"清理日志失败: {str(e)}")
            return 0
    
    def get_log_file_info(self) -> Dict:
        """
        获取日志文件信息
        
        Returns:
            Dict: 日志文件信息
        """
        try:
            if not self.log_file.exists():
                return {
                    'exists': False,
                    'path': str(self.log_file)
                }
            
            stat = self.log_file.stat()
            
            # 统计日志行数
            line_count = 0
            with open(self.log_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for line in f if line.strip())
            
            return {
                'exists': True,
                'path': str(self.log_file),
                'size_bytes': stat.st_size,
                'size_kb': round(stat.st_size / 1024, 2),
                'size_mb': round(stat.st_size / (1024**2), 2),
                'line_count': line_count,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat() + 'Z',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except Exception as e:
            return {
                'error': True,
                'message': f"获取日志文件信息失败: {str(e)}",
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
