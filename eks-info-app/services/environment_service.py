"""
环境信息收集服务

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-13
"""

import os
import platform
import socket
import logging
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class EnvironmentService:
    """环境信息收集服务类"""
    
    # EC2 元数据服务端点
    EC2_METADATA_BASE_URL = "http://169.254.169.254/latest/meta-data"
    EC2_METADATA_TOKEN_URL = "http://169.254.169.254/latest/api/token"
    EC2_METADATA_TIMEOUT = 2  # 超时时间（秒）
    
    def __init__(self):
        """初始化环境服务"""
        self._metadata_token = None
        logger.info("EnvironmentService 初始化完成")
    
    def _get_metadata_token(self) -> Optional[str]:
        """
        获取 EC2 元数据服务的 IMDSv2 令牌
        
        Returns:
            str: 元数据令牌，如果获取失败返回 None
        """
        if self._metadata_token:
            return self._metadata_token
        
        try:
            response = requests.put(
                self.EC2_METADATA_TOKEN_URL,
                headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
                timeout=self.EC2_METADATA_TIMEOUT
            )
            if response.status_code == 200:
                self._metadata_token = response.text
                return self._metadata_token
        except Exception as e:
            logger.warning(f"获取 EC2 元数据令牌失败: {str(e)}")
        
        return None
    
    def _get_ec2_metadata(self, path: str) -> Optional[str]:
        """
        从 EC2 元数据服务获取数据
        
        Args:
            path: 元数据路径（例如: "instance-id"）
        
        Returns:
            str: 元数据值，如果获取失败返回 None
        """
        try:
            url = f"{self.EC2_METADATA_BASE_URL}/{path}"
            headers = {}
            
            # 尝试使用 IMDSv2
            token = self._get_metadata_token()
            if token:
                headers["X-aws-ec2-metadata-token"] = token
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.EC2_METADATA_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.debug(f"获取 EC2 元数据 {path} 失败: {str(e)}")
        
        return None
    
    def get_pod_info(self) -> Dict[str, Any]:
        """
        获取当前 Pod 的基本信息
        
        Returns:
            dict: Pod 信息字典
                - name: Pod 名称
                - namespace: 命名空间
                - ip: Pod IP 地址
                - node_name: 运行的节点名称
                - hostname: 主机名
                - service_account: 服务账号
        """
        try:
            pod_info = {
                'name': os.environ.get('POD_NAME', 'unknown'),
                'namespace': os.environ.get('POD_NAMESPACE', 'default'),
                'ip': os.environ.get('POD_IP', self._get_local_ip()),
                'node_name': os.environ.get('NODE_NAME', 'unknown'),
                'hostname': socket.gethostname(),
                'service_account': os.environ.get('SERVICE_ACCOUNT', 'default')
            }
            
            logger.info(f"获取 Pod 信息成功: {pod_info['name']}")
            return pod_info
        
        except Exception as e:
            logger.error(f"获取 Pod 信息失败: {str(e)}")
            return {
                'name': 'unknown',
                'namespace': 'unknown',
                'ip': 'unknown',
                'node_name': 'unknown',
                'hostname': 'unknown',
                'service_account': 'unknown',
                'error': str(e)
            }
    
    def get_node_info(self) -> Dict[str, Any]:
        """
        获取节点信息
        
        Returns:
            dict: 节点信息字典
                - name: 节点名称
                - internal_ip: 内部 IP
                - external_ip: 外部 IP（如果有）
                - hostname: 主机名
        """
        try:
            node_info = {
                'name': os.environ.get('NODE_NAME', 'unknown'),
                'internal_ip': self._get_ec2_metadata('local-ipv4') or 'unknown',
                'external_ip': self._get_ec2_metadata('public-ipv4') or 'N/A',
                'hostname': self._get_ec2_metadata('hostname') or socket.gethostname()
            }
            
            logger.info(f"获取节点信息成功: {node_info['name']}")
            return node_info
        
        except Exception as e:
            logger.error(f"获取节点信息失败: {str(e)}")
            return {
                'name': 'unknown',
                'internal_ip': 'unknown',
                'external_ip': 'unknown',
                'hostname': 'unknown',
                'error': str(e)
            }
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """
        获取 Kubernetes 集群信息
        
        Returns:
            dict: 集群信息字典
                - api_server: API 服务器地址
                - service_account: 服务账号
                - namespace: 命名空间
                - ca_cert_path: CA 证书路径
                - token_path: Token 路径
        """
        try:
            cluster_info = {
                'api_server': os.environ.get('KUBERNETES_SERVICE_HOST', 'unknown'),
                'api_port': os.environ.get('KUBERNETES_SERVICE_PORT', 'unknown'),
                'service_account': os.environ.get('SERVICE_ACCOUNT', 'default'),
                'namespace': os.environ.get('POD_NAMESPACE', 'default'),
                'ca_cert_path': '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt',
                'token_path': '/var/run/secrets/kubernetes.io/serviceaccount/token'
            }
            
            # 检查服务账号文件是否存在
            cluster_info['ca_cert_exists'] = os.path.exists(cluster_info['ca_cert_path'])
            cluster_info['token_exists'] = os.path.exists(cluster_info['token_path'])
            
            logger.info("获取集群信息成功")
            return cluster_info
        
        except Exception as e:
            logger.error(f"获取集群信息失败: {str(e)}")
            return {
                'api_server': 'unknown',
                'api_port': 'unknown',
                'service_account': 'unknown',
                'namespace': 'unknown',
                'error': str(e)
            }
    
    def get_ec2_metadata(self) -> Dict[str, Any]:
        """
        从 EC2 元数据服务获取实例信息
        
        Returns:
            dict: EC2 实例信息字典
                - instance_id: 实例 ID
                - instance_type: 实例类型
                - availability_zone: 可用区
                - region: 区域
                - private_ip: 私有 IP
                - public_ip: 公有 IP
                - ami_id: AMI ID
                - security_groups: 安全组
        """
        try:
            ec2_info = {
                'instance_id': self._get_ec2_metadata('instance-id') or 'unknown',
                'instance_type': self._get_ec2_metadata('instance-type') or 'unknown',
                'availability_zone': self._get_ec2_metadata('placement/availability-zone') or 'unknown',
                'private_ip': self._get_ec2_metadata('local-ipv4') or 'unknown',
                'public_ip': self._get_ec2_metadata('public-ipv4') or 'N/A',
                'ami_id': self._get_ec2_metadata('ami-id') or 'unknown',
                'hostname': self._get_ec2_metadata('hostname') or 'unknown',
                'mac': self._get_ec2_metadata('mac') or 'unknown'
            }
            
            # 从可用区提取区域
            if ec2_info['availability_zone'] != 'unknown':
                ec2_info['region'] = ec2_info['availability_zone'][:-1]
            else:
                ec2_info['region'] = os.environ.get('AWS_REGION', 'unknown')
            
            # 获取安全组
            security_groups = self._get_ec2_metadata('security-groups')
            ec2_info['security_groups'] = security_groups.split('\n') if security_groups else []
            
            logger.info(f"获取 EC2 元数据成功: {ec2_info['instance_id']}")
            return ec2_info
        
        except Exception as e:
            logger.error(f"获取 EC2 元数据失败: {str(e)}")
            return {
                'instance_id': 'unknown',
                'instance_type': 'unknown',
                'availability_zone': 'unknown',
                'region': os.environ.get('AWS_REGION', 'unknown'),
                'private_ip': 'unknown',
                'public_ip': 'unknown',
                'ami_id': 'unknown',
                'hostname': 'unknown',
                'mac': 'unknown',
                'security_groups': [],
                'error': str(e)
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        Returns:
            dict: 系统信息字典
                - os: 操作系统
                - os_version: 操作系统版本
                - kernel: 内核版本
                - python_version: Python 版本
                - hostname: 主机名
        """
        try:
            system_info = {
                'os': platform.system(),
                'os_version': platform.version(),
                'kernel': platform.release(),
                'python_version': platform.python_version(),
                'hostname': socket.gethostname(),
                'platform': platform.platform()
            }
            
            logger.info("获取系统信息成功")
            return system_info
        
        except Exception as e:
            logger.error(f"获取系统信息失败: {str(e)}")
            return {
                'os': 'unknown',
                'os_version': 'unknown',
                'kernel': 'unknown',
                'python_version': 'unknown',
                'hostname': 'unknown',
                'platform': 'unknown',
                'error': str(e)
            }
    
    def get_architecture_info(self) -> Dict[str, Any]:
        """
        检测 CPU 架构信息，特别是 ARM64 架构
        
        Returns:
            dict: 架构信息字典
                - machine: 机器类型
                - processor: 处理器类型
                - architecture: 架构
                - is_arm64: 是否为 ARM64 架构
                - is_graviton: 是否为 AWS Graviton 处理器
        """
        try:
            machine = platform.machine().lower()
            processor = platform.processor().lower()
            
            # 检测是否为 ARM64
            is_arm64 = machine in ['aarch64', 'arm64']
            
            # 检测是否为 Graviton（通过 CPU 信息）
            is_graviton = False
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    is_graviton = 'graviton' in cpuinfo or ('arm' in cpuinfo and 'neoverse' in cpuinfo)
            except Exception:
                pass
            
            arch_info = {
                'machine': machine,
                'processor': processor or 'unknown',
                'architecture': platform.architecture()[0],
                'is_arm64': is_arm64,
                'is_graviton': is_graviton,
                'cpu_count': os.cpu_count() or 0
            }
            
            logger.info(f"获取架构信息成功: ARM64={is_arm64}, Graviton={is_graviton}")
            return arch_info
        
        except Exception as e:
            logger.error(f"获取架构信息失败: {str(e)}")
            return {
                'machine': 'unknown',
                'processor': 'unknown',
                'architecture': 'unknown',
                'is_arm64': False,
                'is_graviton': False,
                'cpu_count': 0,
                'error': str(e)
            }
    
    def _get_local_ip(self) -> str:
        """
        获取本地 IP 地址
        
        Returns:
            str: 本地 IP 地址
        """
        try:
            # 创建一个 UDP 套接字来获取本地 IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    def get_all_environment_info(self) -> Dict[str, Any]:
        """
        获取所有环境信息的汇总
        
        Returns:
            dict: 包含所有环境信息的字典
        """
        try:
            all_info = {
                'pod': self.get_pod_info(),
                'node': self.get_node_info(),
                'cluster': self.get_cluster_info(),
                'ec2': self.get_ec2_metadata(),
                'system': self.get_system_info(),
                'architecture': self.get_architecture_info(),
                'environment_variables': self._get_filtered_env_vars()
            }
            
            logger.info("获取所有环境信息成功")
            return all_info
        
        except Exception as e:
            logger.error(f"获取所有环境信息失败: {str(e)}")
            return {
                'error': str(e)
            }
    
    def _get_filtered_env_vars(self) -> Dict[str, str]:
        """
        获取过滤后的环境变量（排除敏感信息）
        
        Returns:
            dict: 环境变量字典
        """
        # 敏感关键字列表
        sensitive_keywords = [
            'password', 'secret', 'key', 'token', 'credential',
            'auth', 'api_key', 'access_key', 'private'
        ]
        
        filtered_vars = {}
        for key, value in os.environ.items():
            # 检查是否包含敏感关键字
            if any(keyword in key.lower() for keyword in sensitive_keywords):
                filtered_vars[key] = '***REDACTED***'
            else:
                filtered_vars[key] = value
        
        return filtered_vars

