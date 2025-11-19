"""
S3 对象存储访问类

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import boto3
import json
from datetime import datetime
from typing import List, Dict, Optional
from botocore.exceptions import ClientError, NoCredentialsError


class S3Storage:
    """S3 对象存储访问类"""
    
    def __init__(self, bucket_name: str, region: str = 'ap-southeast-1'):
        """
        初始化 S3 存储
        
        Args:
            bucket_name: S3 存储桶名称
            region: AWS 区域
        """
        self.bucket_name = bucket_name
        self.region = region
        
        # 初始化 S3 客户端（使用 IRSA 自动获取凭证）
        try:
            self.s3_client = boto3.client('s3', region_name=region)
            
            # 验证存储桶是否存在和可访问
            self.s3_client.head_bucket(Bucket=bucket_name)
            self.available = True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                print(f"S3 存储桶不存在: {bucket_name}")
            elif error_code == '403':
                print(f"无权访问 S3 存储桶: {bucket_name}")
            else:
                print(f"S3 客户端初始化失败: {str(e)}")
            self.available = False
        except NoCredentialsError:
            print("无法获取 AWS 凭证，请检查 IRSA 配置")
            self.available = False
        except Exception as e:
            print(f"S3 存储初始化失败: {str(e)}")
            self.available = False

    def upload_object(self, key: str, data: bytes, metadata: Optional[Dict] = None) -> bool:
        """
        上传对象到 S3
        
        Args:
            key: 对象键名
            data: 对象数据（字节）
            metadata: 对象元数据（可选）
            
        Returns:
            bool: 上传是否成功
        """
        if not self.available:
            print("S3 存储不可用")
            return False
        
        try:
            # 准备上传参数
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': key,
                'Body': data
            }
            
            # 添加元数据
            if metadata:
                # S3 元数据键必须是字符串，值也必须是字符串
                upload_args['Metadata'] = {
                    k: str(v) for k, v in metadata.items()
                }
            
            # 上传对象
            self.s3_client.put_object(**upload_args)
            
            return True
        except ClientError as e:
            print(f"上传对象失败: {str(e)}")
            return False
        except Exception as e:
            print(f"上传对象时发生错误: {str(e)}")
            return False
    
    def download_object(self, key: str) -> Optional[bytes]:
        """
        从 S3 下载对象
        
        Args:
            key: 对象键名
            
        Returns:
            Optional[bytes]: 对象数据，失败时返回 None
        """
        if not self.available:
            print("S3 存储不可用")
            return None
        
        try:
            # 下载对象
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            # 读取对象内容
            data = response['Body'].read()
            
            return data
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                print(f"对象不存在: {key}")
            else:
                print(f"下载对象失败: {str(e)}")
            return None
        except Exception as e:
            print(f"下载对象时发生错误: {str(e)}")
            return None
    
    def list_objects(self, prefix: str = '', max_keys: int = 1000) -> List[Dict]:
        """
        列出 S3 存储桶中的对象
        
        Args:
            prefix: 对象键前缀（可选）
            max_keys: 返回的最大对象数
            
        Returns:
            List[Dict]: 对象信息列表
        """
        if not self.available:
            print("S3 存储不可用")
            return []
        
        try:
            # 列出对象
            list_args = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }
            
            if prefix:
                list_args['Prefix'] = prefix
            
            response = self.s3_client.list_objects_v2(**list_args)
            
            # 解析对象列表
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size_bytes': obj['Size'],
                    'size_kb': round(obj['Size'] / 1024, 2),
                    'size_mb': round(obj['Size'] / (1024**2), 2),
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"'),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
            
            # 按最后修改时间倒序排序
            objects.sort(key=lambda x: x['last_modified'], reverse=True)
            
            return objects
        except ClientError as e:
            print(f"列出对象失败: {str(e)}")
            return []
        except Exception as e:
            print(f"列出对象时发生错误: {str(e)}")
            return []
    
    def delete_object(self, key: str) -> bool:
        """
        删除 S3 对象
        
        Args:
            key: 对象键名
            
        Returns:
            bool: 删除是否成功
        """
        if not self.available:
            print("S3 存储不可用")
            return False
        
        try:
            # 删除对象
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return True
        except ClientError as e:
            print(f"删除对象失败: {str(e)}")
            return False
        except Exception as e:
            print(f"删除对象时发生错误: {str(e)}")
            return False
    
    def get_bucket_info(self) -> Dict:
        """
        获取存储桶信息
        
        Returns:
            Dict: 存储桶信息
        """
        if not self.available:
            return {
                'error': True,
                'message': 'S3 存储不可用',
                'bucket_name': self.bucket_name,
                'available': False,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        
        try:
            # 获取存储桶位置
            location_response = self.s3_client.get_bucket_location(
                Bucket=self.bucket_name
            )
            location = location_response.get('LocationConstraint', 'us-east-1')
            
            # 获取存储桶加密配置
            encryption_config = None
            try:
                encryption_response = self.s3_client.get_bucket_encryption(
                    Bucket=self.bucket_name
                )
                encryption_config = encryption_response.get('ServerSideEncryptionConfiguration', {})
            except ClientError as e:
                if e.response.get('Error', {}).get('Code') != 'ServerSideEncryptionConfigurationNotFoundError':
                    print(f"获取加密配置失败: {str(e)}")
            
            # 获取存储桶标签
            tags = {}
            try:
                tags_response = self.s3_client.get_bucket_tagging(
                    Bucket=self.bucket_name
                )
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
            except ClientError as e:
                if e.response.get('Error', {}).get('Code') != 'NoSuchTagSet':
                    print(f"获取标签失败: {str(e)}")
            
            # 统计对象数量和总大小
            objects = self.list_objects()
            total_size = sum(obj['size_bytes'] for obj in objects)
            
            return {
                'bucket_name': self.bucket_name,
                'region': location or self.region,
                'available': True,
                'object_count': len(objects),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024**2), 2),
                'total_size_gb': round(total_size / (1024**3), 2),
                'encryption': encryption_config is not None,
                'encryption_config': encryption_config,
                'tags': tags,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except ClientError as e:
            return {
                'error': True,
                'error_type': 'client_error',
                'message': f'获取存储桶信息失败: {str(e)}',
                'bucket_name': self.bucket_name,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except Exception as e:
            return {
                'error': True,
                'error_type': 'unexpected_error',
                'message': f'获取存储桶信息时发生错误: {str(e)}',
                'bucket_name': self.bucket_name,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    def get_object_metadata(self, key: str) -> Optional[Dict]:
        """
        获取对象元数据
        
        Args:
            key: 对象键名
            
        Returns:
            Optional[Dict]: 对象元数据，失败时返回 None
        """
        if not self.available:
            print("S3 存储不可用")
            return None
        
        try:
            # 获取对象元数据
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            return {
                'key': key,
                'size_bytes': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {}),
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'server_side_encryption': response.get('ServerSideEncryption'),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                print(f"对象不存在: {key}")
            else:
                print(f"获取对象元数据失败: {str(e)}")
            return None
        except Exception as e:
            print(f"获取对象元数据时发生错误: {str(e)}")
            return None
