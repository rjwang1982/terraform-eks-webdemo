"""
AWS API 交互服务

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import logging
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class AWSService:
    """AWS API 交互服务类"""
    
    def __init__(self, region: Optional[str] = None):
        """
        初始化 AWS 客户端
        使用 IRSA (IAM Roles for Service Accounts) 自动获取凭证
        
        Args:
            region: AWS 区域，如果不指定则使用默认区域
        """
        self.region = region or 'ap-southeast-1'
        
        try:
            # 初始化 boto3 客户端（自动使用 IRSA 凭证）
            self.ec2_client = boto3.client('ec2', region_name=self.region)
            self.efs_client = boto3.client('efs', region_name=self.region)
            self.elb_client = boto3.client('elbv2', region_name=self.region)
            
            logger.info(f"AWSService 初始化完成 (region={self.region})")
        except Exception as e:
            logger.error(f"初始化 AWS 客户端失败: {str(e)}")
            raise
    
    def get_ec2_instance_info(self, instance_id: str) -> Dict[str, Any]:
        """
        获取 EC2 实例详细信息
        
        Args:
            instance_id: EC2 实例 ID
        
        Returns:
            dict: EC2 实例信息
                - instance_id: 实例 ID
                - instance_type: 实例类型
                - state: 实例状态
                - availability_zone: 可用区
                - private_ip: 私有 IP
                - public_ip: 公有 IP
                - vpc_id: VPC ID
                - subnet_id: 子网 ID
                - security_groups: 安全组列表
                - tags: 标签
                - launch_time: 启动时间
                - architecture: 架构
                - platform: 平台
        """
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            
            if not response['Reservations']:
                logger.warning(f"未找到实例: {instance_id}")
                return {
                    'instance_id': instance_id,
                    'error': '实例不存在'
                }
            
            instance = response['Reservations'][0]['Instances'][0]
            
            # 解析安全组
            security_groups = [
                {
                    'id': sg['GroupId'],
                    'name': sg['GroupName']
                }
                for sg in instance.get('SecurityGroups', [])
            ]
            
            # 解析标签
            tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
            
            instance_info = {
                'instance_id': instance['InstanceId'],
                'instance_type': instance['InstanceType'],
                'state': instance['State']['Name'],
                'availability_zone': instance['Placement']['AvailabilityZone'],
                'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                'public_ip': instance.get('PublicIpAddress', 'N/A'),
                'vpc_id': instance.get('VpcId', 'N/A'),
                'subnet_id': instance.get('SubnetId', 'N/A'),
                'security_groups': security_groups,
                'tags': tags,
                'launch_time': instance['LaunchTime'].isoformat() if instance.get('LaunchTime') else None,
                'architecture': instance.get('Architecture', 'unknown'),
                'platform': instance.get('Platform', 'linux'),
                'ami_id': instance.get('ImageId', 'unknown'),
                'key_name': instance.get('KeyName', 'N/A'),
                'iam_instance_profile': instance.get('IamInstanceProfile', {}).get('Arn', 'N/A')
            }
            
            logger.info(f"获取 EC2 实例信息成功: {instance_id}")
            return instance_info
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"获取 EC2 实例信息失败 (ClientError): {error_code} - {error_message}")
            return {
                'instance_id': instance_id,
                'error': f'{error_code}: {error_message}'
            }
        except Exception as e:
            logger.error(f"获取 EC2 实例信息失败: {str(e)}")
            return {
                'instance_id': instance_id,
                'error': str(e)
            }
    
    def get_vpc_info(self, vpc_id: str) -> Dict[str, Any]:
        """
        获取 VPC 详细信息
        
        Args:
            vpc_id: VPC ID
        
        Returns:
            dict: VPC 信息
                - vpc_id: VPC ID
                - cidr_block: CIDR 块
                - state: 状态
                - is_default: 是否为默认 VPC
                - dhcp_options_id: DHCP 选项集 ID
                - tags: 标签
                - enable_dns_support: 是否启用 DNS 支持
                - enable_dns_hostnames: 是否启用 DNS 主机名
        """
        try:
            response = self.ec2_client.describe_vpcs(VpcIds=[vpc_id])
            
            if not response['Vpcs']:
                logger.warning(f"未找到 VPC: {vpc_id}")
                return {
                    'vpc_id': vpc_id,
                    'error': 'VPC 不存在'
                }
            
            vpc = response['Vpcs'][0]
            
            # 解析标签
            tags = {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
            
            # 获取 VPC 属性
            dns_support = self.ec2_client.describe_vpc_attribute(
                VpcId=vpc_id,
                Attribute='enableDnsSupport'
            )
            dns_hostnames = self.ec2_client.describe_vpc_attribute(
                VpcId=vpc_id,
                Attribute='enableDnsHostnames'
            )
            
            vpc_info = {
                'vpc_id': vpc['VpcId'],
                'cidr_block': vpc['CidrBlock'],
                'cidr_block_associations': [
                    {
                        'cidr_block': assoc['CidrBlock'],
                        'state': assoc['CidrBlockState']['State']
                    }
                    for assoc in vpc.get('CidrBlockAssociationSet', [])
                ],
                'state': vpc['State'],
                'is_default': vpc.get('IsDefault', False),
                'dhcp_options_id': vpc.get('DhcpOptionsId', 'N/A'),
                'tags': tags,
                'enable_dns_support': dns_support['EnableDnsSupport']['Value'],
                'enable_dns_hostnames': dns_hostnames['EnableDnsHostnames']['Value'],
                'owner_id': vpc.get('OwnerId', 'unknown')
            }
            
            logger.info(f"获取 VPC 信息成功: {vpc_id}")
            return vpc_info
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"获取 VPC 信息失败 (ClientError): {error_code} - {error_message}")
            return {
                'vpc_id': vpc_id,
                'error': f'{error_code}: {error_message}'
            }
        except Exception as e:
            logger.error(f"获取 VPC 信息失败: {str(e)}")
            return {
                'vpc_id': vpc_id,
                'error': str(e)
            }
    
    def get_subnet_info(self, subnet_id: str) -> Dict[str, Any]:
        """
        获取子网详细信息
        
        Args:
            subnet_id: 子网 ID
        
        Returns:
            dict: 子网信息
                - subnet_id: 子网 ID
                - vpc_id: VPC ID
                - cidr_block: CIDR 块
                - availability_zone: 可用区
                - available_ip_count: 可用 IP 数量
                - state: 状态
                - map_public_ip: 是否自动分配公有 IP
                - tags: 标签
        """
        try:
            response = self.ec2_client.describe_subnets(SubnetIds=[subnet_id])
            
            if not response['Subnets']:
                logger.warning(f"未找到子网: {subnet_id}")
                return {
                    'subnet_id': subnet_id,
                    'error': '子网不存在'
                }
            
            subnet = response['Subnets'][0]
            
            # 解析标签
            tags = {tag['Key']: tag['Value'] for tag in subnet.get('Tags', [])}
            
            # 判断子网类型（公有/私有）
            subnet_type = 'private'
            if tags.get('Name', '').lower().find('public') != -1:
                subnet_type = 'public'
            elif subnet.get('MapPublicIpOnLaunch', False):
                subnet_type = 'public'
            
            subnet_info = {
                'subnet_id': subnet['SubnetId'],
                'vpc_id': subnet['VpcId'],
                'cidr_block': subnet['CidrBlock'],
                'availability_zone': subnet['AvailabilityZone'],
                'availability_zone_id': subnet.get('AvailabilityZoneId', 'N/A'),
                'available_ip_count': subnet['AvailableIpAddressCount'],
                'state': subnet['State'],
                'map_public_ip': subnet.get('MapPublicIpOnLaunch', False),
                'default_for_az': subnet.get('DefaultForAz', False),
                'subnet_type': subnet_type,
                'tags': tags,
                'owner_id': subnet.get('OwnerId', 'unknown')
            }
            
            logger.info(f"获取子网信息成功: {subnet_id}")
            return subnet_info
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"获取子网信息失败 (ClientError): {error_code} - {error_message}")
            return {
                'subnet_id': subnet_id,
                'error': f'{error_code}: {error_message}'
            }
        except Exception as e:
            logger.error(f"获取子网信息失败: {str(e)}")
            return {
                'subnet_id': subnet_id,
                'error': str(e)
            }
    
    def get_security_groups(self, group_ids: List[str]) -> List[Dict[str, Any]]:
        """
        获取安全组详细信息
        
        Args:
            group_ids: 安全组 ID 列表
        
        Returns:
            list: 安全组信息列表
                - group_id: 安全组 ID
                - group_name: 安全组名称
                - description: 描述
                - vpc_id: VPC ID
                - ingress_rules: 入站规则
                - egress_rules: 出站规则
                - tags: 标签
        """
        try:
            if not group_ids:
                logger.warning("安全组 ID 列表为空")
                return []
            
            response = self.ec2_client.describe_security_groups(GroupIds=group_ids)
            
            security_groups = []
            for sg in response['SecurityGroups']:
                # 解析入站规则
                ingress_rules = []
                for rule in sg.get('IpPermissions', []):
                    rule_info = {
                        'protocol': rule.get('IpProtocol', 'all'),
                        'from_port': rule.get('FromPort', 'all'),
                        'to_port': rule.get('ToPort', 'all'),
                        'sources': []
                    }
                    
                    # IP 范围
                    for ip_range in rule.get('IpRanges', []):
                        rule_info['sources'].append({
                            'type': 'cidr',
                            'value': ip_range.get('CidrIp', ''),
                            'description': ip_range.get('Description', '')
                        })
                    
                    # IPv6 范围
                    for ipv6_range in rule.get('Ipv6Ranges', []):
                        rule_info['sources'].append({
                            'type': 'cidr_ipv6',
                            'value': ipv6_range.get('CidrIpv6', ''),
                            'description': ipv6_range.get('Description', '')
                        })
                    
                    # 安全组
                    for sg_pair in rule.get('UserIdGroupPairs', []):
                        rule_info['sources'].append({
                            'type': 'security_group',
                            'value': sg_pair.get('GroupId', ''),
                            'description': sg_pair.get('Description', '')
                        })
                    
                    ingress_rules.append(rule_info)
                
                # 解析出站规则
                egress_rules = []
                for rule in sg.get('IpPermissionsEgress', []):
                    rule_info = {
                        'protocol': rule.get('IpProtocol', 'all'),
                        'from_port': rule.get('FromPort', 'all'),
                        'to_port': rule.get('ToPort', 'all'),
                        'destinations': []
                    }
                    
                    # IP 范围
                    for ip_range in rule.get('IpRanges', []):
                        rule_info['destinations'].append({
                            'type': 'cidr',
                            'value': ip_range.get('CidrIp', ''),
                            'description': ip_range.get('Description', '')
                        })
                    
                    # IPv6 范围
                    for ipv6_range in rule.get('Ipv6Ranges', []):
                        rule_info['destinations'].append({
                            'type': 'cidr_ipv6',
                            'value': ipv6_range.get('CidrIpv6', ''),
                            'description': ipv6_range.get('Description', '')
                        })
                    
                    # 安全组
                    for sg_pair in rule.get('UserIdGroupPairs', []):
                        rule_info['destinations'].append({
                            'type': 'security_group',
                            'value': sg_pair.get('GroupId', ''),
                            'description': sg_pair.get('Description', '')
                        })
                    
                    egress_rules.append(rule_info)
                
                # 解析标签
                tags = {tag['Key']: tag['Value'] for tag in sg.get('Tags', [])}
                
                sg_info = {
                    'group_id': sg['GroupId'],
                    'group_name': sg['GroupName'],
                    'description': sg.get('Description', ''),
                    'vpc_id': sg.get('VpcId', 'N/A'),
                    'ingress_rules': ingress_rules,
                    'egress_rules': egress_rules,
                    'tags': tags,
                    'owner_id': sg.get('OwnerId', 'unknown')
                }
                security_groups.append(sg_info)
            
            logger.info(f"获取安全组信息成功: {len(security_groups)} 个安全组")
            return security_groups
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"获取安全组信息失败 (ClientError): {error_code} - {error_message}")
            return []
        except Exception as e:
            logger.error(f"获取安全组信息失败: {str(e)}")
            return []
    
    def get_ebs_volume_info(self, volume_id: str) -> Dict[str, Any]:
        """
        获取 EBS 卷详细信息
        
        Args:
            volume_id: EBS 卷 ID
        
        Returns:
            dict: EBS 卷信息
                - volume_id: 卷 ID
                - size: 大小 (GB)
                - volume_type: 卷类型
                - state: 状态
                - availability_zone: 可用区
                - encrypted: 是否加密
                - iops: IOPS
                - throughput: 吞吐量
                - attachments: 挂载信息
                - tags: 标签
                - created_at: 创建时间
        """
        try:
            response = self.ec2_client.describe_volumes(VolumeIds=[volume_id])
            
            if not response['Volumes']:
                logger.warning(f"未找到 EBS 卷: {volume_id}")
                return {
                    'volume_id': volume_id,
                    'error': 'EBS 卷不存在'
                }
            
            volume = response['Volumes'][0]
            
            # 解析挂载信息
            attachments = [
                {
                    'instance_id': att.get('InstanceId', 'N/A'),
                    'device': att.get('Device', 'N/A'),
                    'state': att.get('State', 'unknown'),
                    'attach_time': att['AttachTime'].isoformat() if att.get('AttachTime') else None,
                    'delete_on_termination': att.get('DeleteOnTermination', False)
                }
                for att in volume.get('Attachments', [])
            ]
            
            # 解析标签
            tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
            
            volume_info = {
                'volume_id': volume['VolumeId'],
                'size': volume['Size'],
                'volume_type': volume['VolumeType'],
                'state': volume['State'],
                'availability_zone': volume['AvailabilityZone'],
                'encrypted': volume.get('Encrypted', False),
                'iops': volume.get('Iops', 'N/A'),
                'throughput': volume.get('Throughput', 'N/A'),
                'multi_attach_enabled': volume.get('MultiAttachEnabled', False),
                'attachments': attachments,
                'tags': tags,
                'created_at': volume['CreateTime'].isoformat() if volume.get('CreateTime') else None,
                'snapshot_id': volume.get('SnapshotId', 'N/A')
            }
            
            logger.info(f"获取 EBS 卷信息成功: {volume_id}")
            return volume_info
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"获取 EBS 卷信息失败 (ClientError): {error_code} - {error_message}")
            return {
                'volume_id': volume_id,
                'error': f'{error_code}: {error_message}'
            }
        except Exception as e:
            logger.error(f"获取 EBS 卷信息失败: {str(e)}")
            return {
                'volume_id': volume_id,
                'error': str(e)
            }
    
    def get_efs_filesystem_info(self, fs_id: str) -> Dict[str, Any]:
        """
        获取 EFS 文件系统详细信息
        
        Args:
            fs_id: EFS 文件系统 ID
        
        Returns:
            dict: EFS 文件系统信息
                - file_system_id: 文件系统 ID
                - name: 名称
                - size: 大小 (字节)
                - lifecycle_state: 生命周期状态
                - performance_mode: 性能模式
                - throughput_mode: 吞吐量模式
                - encrypted: 是否加密
                - mount_targets: 挂载目标
                - tags: 标签
                - created_at: 创建时间
        """
        try:
            response = self.efs_client.describe_file_systems(FileSystemId=fs_id)
            
            if not response['FileSystems']:
                logger.warning(f"未找到 EFS 文件系统: {fs_id}")
                return {
                    'file_system_id': fs_id,
                    'error': 'EFS 文件系统不存在'
                }
            
            fs = response['FileSystems'][0]
            
            # 获取挂载目标
            mount_targets = []
            try:
                mt_response = self.efs_client.describe_mount_targets(FileSystemId=fs_id)
                for mt in mt_response['MountTargets']:
                    mount_targets.append({
                        'mount_target_id': mt['MountTargetId'],
                        'subnet_id': mt['SubnetId'],
                        'ip_address': mt.get('IpAddress', 'N/A'),
                        'availability_zone': mt.get('AvailabilityZoneName', 'N/A'),
                        'lifecycle_state': mt['LifeCycleState'],
                        'network_interface_id': mt.get('NetworkInterfaceId', 'N/A')
                    })
            except Exception as e:
                logger.warning(f"获取 EFS 挂载目标失败: {str(e)}")
            
            # 解析标签
            tags = {tag['Key']: tag['Value'] for tag in fs.get('Tags', [])}
            
            fs_info = {
                'file_system_id': fs['FileSystemId'],
                'name': fs.get('Name', tags.get('Name', 'N/A')),
                'size_in_bytes': fs['SizeInBytes']['Value'],
                'size_in_gb': round(fs['SizeInBytes']['Value'] / (1024**3), 2),
                'lifecycle_state': fs['LifeCycleState'],
                'performance_mode': fs['PerformanceMode'],
                'throughput_mode': fs.get('ThroughputMode', 'bursting'),
                'encrypted': fs.get('Encrypted', False),
                'number_of_mount_targets': fs['NumberOfMountTargets'],
                'mount_targets': mount_targets,
                'tags': tags,
                'created_at': fs['CreationTime'].isoformat() if fs.get('CreationTime') else None,
                'owner_id': fs.get('OwnerId', 'unknown')
            }
            
            logger.info(f"获取 EFS 文件系统信息成功: {fs_id}")
            return fs_info
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"获取 EFS 文件系统信息失败 (ClientError): {error_code} - {error_message}")
            return {
                'file_system_id': fs_id,
                'error': f'{error_code}: {error_message}'
            }
        except Exception as e:
            logger.error(f"获取 EFS 文件系统信息失败: {str(e)}")
            return {
                'file_system_id': fs_id,
                'error': str(e)
            }
    
    def get_load_balancers(self, names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        获取负载均衡器信息
        
        Args:
            names: 负载均衡器名称列表（可选）
        
        Returns:
            list: 负载均衡器信息列表
                - name: 负载均衡器名称
                - arn: ARN
                - dns_name: DNS 名称
                - type: 类型 (application/network/gateway)
                - scheme: 方案 (internet-facing/internal)
                - state: 状态
                - vpc_id: VPC ID
                - availability_zones: 可用区
                - security_groups: 安全组
                - created_at: 创建时间
        """
        try:
            if names:
                response = self.elb_client.describe_load_balancers(Names=names)
            else:
                response = self.elb_client.describe_load_balancers()
            
            load_balancers = []
            for lb in response['LoadBalancers']:
                # 解析可用区
                availability_zones = [
                    {
                        'zone_name': az['ZoneName'],
                        'subnet_id': az.get('SubnetId', 'N/A'),
                        'load_balancer_addresses': [
                            addr.get('IpAddress', 'N/A') 
                            for addr in az.get('LoadBalancerAddresses', [])
                        ]
                    }
                    for az in lb.get('AvailabilityZones', [])
                ]
                
                lb_info = {
                    'name': lb['LoadBalancerName'],
                    'arn': lb['LoadBalancerArn'],
                    'dns_name': lb['DNSName'],
                    'type': lb['Type'],
                    'scheme': lb['Scheme'],
                    'state': lb['State']['Code'],
                    'vpc_id': lb.get('VpcId', 'N/A'),
                    'availability_zones': availability_zones,
                    'security_groups': lb.get('SecurityGroups', []),
                    'ip_address_type': lb.get('IpAddressType', 'ipv4'),
                    'created_at': lb['CreatedTime'].isoformat() if lb.get('CreatedTime') else None
                }
                
                # 获取标签
                try:
                    tags_response = self.elb_client.describe_tags(
                        ResourceArns=[lb['LoadBalancerArn']]
                    )
                    if tags_response['TagDescriptions']:
                        lb_info['tags'] = {
                            tag['Key']: tag['Value'] 
                            for tag in tags_response['TagDescriptions'][0].get('Tags', [])
                        }
                    else:
                        lb_info['tags'] = {}
                except Exception as e:
                    logger.warning(f"获取负载均衡器标签失败: {str(e)}")
                    lb_info['tags'] = {}
                
                load_balancers.append(lb_info)
            
            logger.info(f"获取负载均衡器信息成功: {len(load_balancers)} 个负载均衡器")
            return load_balancers
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"获取负载均衡器信息失败 (ClientError): {error_code} - {error_message}")
            return []
        except Exception as e:
            logger.error(f"获取负载均衡器信息失败: {str(e)}")
            return []
