"""
Kubernetes API 交互服务

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-13
"""

import logging
from typing import Dict, List, Optional, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class KubernetesService:
    """Kubernetes API 交互服务类"""
    
    def __init__(self):
        """
        初始化 Kubernetes 客户端
        使用 in-cluster 配置（从 Pod 内部访问）
        """
        try:
            # 尝试加载 in-cluster 配置
            config.load_incluster_config()
            logger.info("成功加载 Kubernetes in-cluster 配置")
        except config.ConfigException:
            try:
                # 如果不在集群内，尝试加载本地 kubeconfig（用于开发测试）
                config.load_kube_config()
                logger.info("成功加载 Kubernetes kubeconfig 配置")
            except Exception as e:
                logger.error(f"无法加载 Kubernetes 配置: {str(e)}")
                raise
        
        # 初始化 API 客户端
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.autoscaling_v2 = client.AutoscalingV2Api()
        
        logger.info("KubernetesService 初始化完成")
    
    def get_current_pod(self) -> Dict[str, Any]:
        """
        获取当前 Pod 的详细信息
        
        Returns:
            dict: 当前 Pod 的详细信息
                - name: Pod 名称
                - namespace: 命名空间
                - status: Pod 状态
                - ip: Pod IP
                - node_name: 运行的节点
                - labels: 标签
                - annotations: 注解
                - containers: 容器列表
                - created_at: 创建时间
        """
        try:
            import os
            pod_name = os.environ.get('POD_NAME', 'unknown')
            namespace = os.environ.get('POD_NAMESPACE', 'default')
            
            if pod_name == 'unknown':
                logger.warning("POD_NAME 环境变量未设置")
                return {
                    'name': 'unknown',
                    'namespace': namespace,
                    'error': 'POD_NAME 环境变量未设置'
                }
            
            # 获取 Pod 详细信息
            pod = self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            
            pod_info = {
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': pod.status.phase,
                'ip': pod.status.pod_ip,
                'node_name': pod.spec.node_name,
                'labels': pod.metadata.labels or {},
                'annotations': pod.metadata.annotations or {},
                'service_account': pod.spec.service_account_name,
                'created_at': pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                'restart_count': sum(
                    container_status.restart_count 
                    for container_status in (pod.status.container_statuses or [])
                ),
                'containers': [
                    {
                        'name': container.name,
                        'image': container.image,
                        'ready': container_status.ready if container_status else False,
                        'restart_count': container_status.restart_count if container_status else 0
                    }
                    for container, container_status in zip(
                        pod.spec.containers,
                        pod.status.container_statuses or []
                    )
                ]
            }
            
            logger.info(f"获取当前 Pod 信息成功: {pod_name}")
            return pod_info
        
        except ApiException as e:
            logger.error(f"获取当前 Pod 信息失败 (API 错误): {str(e)}")
            return {
                'name': 'unknown',
                'namespace': 'unknown',
                'error': f'API 错误: {e.status} - {e.reason}'
            }
        except Exception as e:
            logger.error(f"获取当前 Pod 信息失败: {str(e)}")
            return {
                'name': 'unknown',
                'namespace': 'unknown',
                'error': str(e)
            }
    
    def get_pods(self, namespace: str = 'default', label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出命名空间中的所有 Pod
        
        Args:
            namespace: 命名空间名称
            label_selector: 标签选择器（可选）
        
        Returns:
            list: Pod 信息列表
        """
        try:
            # 获取 Pod 列表
            if label_selector:
                pods = self.core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector
                )
            else:
                pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            
            pod_list = []
            for pod in pods.items:
                pod_info = {
                    'name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'status': pod.status.phase,
                    'ip': pod.status.pod_ip,
                    'node_name': pod.spec.node_name,
                    'labels': pod.metadata.labels or {},
                    'created_at': pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                    'restart_count': sum(
                        container_status.restart_count 
                        for container_status in (pod.status.container_statuses or [])
                    ),
                    'ready': all(
                        container_status.ready 
                        for container_status in (pod.status.container_statuses or [])
                    ) if pod.status.container_statuses else False
                }
                pod_list.append(pod_info)
            
            logger.info(f"获取 Pod 列表成功: {len(pod_list)} 个 Pod (namespace={namespace})")
            return pod_list
        
        except ApiException as e:
            logger.error(f"获取 Pod 列表失败 (API 错误): {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取 Pod 列表失败: {str(e)}")
            return []
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """
        列出集群中的所有节点
        
        Returns:
            list: 节点信息列表
                - name: 节点名称
                - status: 节点状态
                - roles: 节点角色
                - version: Kubelet 版本
                - internal_ip: 内部 IP
                - external_ip: 外部 IP
                - capacity: 资源容量
                - allocatable: 可分配资源
                - labels: 标签
                - created_at: 创建时间
        """
        try:
            nodes = self.core_v1.list_node()
            
            node_list = []
            for node in nodes.items:
                # 获取节点 IP 地址
                internal_ip = None
                external_ip = None
                for address in (node.status.addresses or []):
                    if address.type == 'InternalIP':
                        internal_ip = address.address
                    elif address.type == 'ExternalIP':
                        external_ip = address.address
                
                # 获取节点角色
                roles = []
                for label_key in (node.metadata.labels or {}).keys():
                    if label_key.startswith('node-role.kubernetes.io/'):
                        role = label_key.split('/')[-1]
                        roles.append(role)
                
                # 获取节点状态
                node_ready = False
                for condition in (node.status.conditions or []):
                    if condition.type == 'Ready':
                        node_ready = condition.status == 'True'
                        break
                
                node_info = {
                    'name': node.metadata.name,
                    'status': 'Ready' if node_ready else 'NotReady',
                    'roles': roles or ['<none>'],
                    'version': node.status.node_info.kubelet_version,
                    'internal_ip': internal_ip or 'unknown',
                    'external_ip': external_ip or 'N/A',
                    'os': node.status.node_info.operating_system,
                    'architecture': node.status.node_info.architecture,
                    'container_runtime': node.status.node_info.container_runtime_version,
                    'capacity': {
                        'cpu': node.status.capacity.get('cpu', 'unknown'),
                        'memory': node.status.capacity.get('memory', 'unknown'),
                        'pods': node.status.capacity.get('pods', 'unknown')
                    },
                    'allocatable': {
                        'cpu': node.status.allocatable.get('cpu', 'unknown'),
                        'memory': node.status.allocatable.get('memory', 'unknown'),
                        'pods': node.status.allocatable.get('pods', 'unknown')
                    },
                    'labels': node.metadata.labels or {},
                    'created_at': node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else None
                }
                node_list.append(node_info)
            
            logger.info(f"获取节点列表成功: {len(node_list)} 个节点")
            return node_list
        
        except ApiException as e:
            logger.error(f"获取节点列表失败 (API 错误): {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取节点列表失败: {str(e)}")
            return []
    
    def get_services(self, namespace: str = 'default') -> List[Dict[str, Any]]:
        """
        获取命名空间中的所有 Service
        
        Args:
            namespace: 命名空间名称
        
        Returns:
            list: Service 信息列表
                - name: Service 名称
                - namespace: 命名空间
                - type: Service 类型
                - cluster_ip: Cluster IP
                - external_ip: 外部 IP
                - ports: 端口列表
                - selector: 选择器
                - created_at: 创建时间
        """
        try:
            services = self.core_v1.list_namespaced_service(namespace=namespace)
            
            service_list = []
            for svc in services.items:
                # 获取外部 IP
                external_ips = []
                if svc.status.load_balancer and svc.status.load_balancer.ingress:
                    for ingress in svc.status.load_balancer.ingress:
                        if ingress.ip:
                            external_ips.append(ingress.ip)
                        elif ingress.hostname:
                            external_ips.append(ingress.hostname)
                
                # 获取端口信息
                ports = []
                for port in (svc.spec.ports or []):
                    port_info = {
                        'name': port.name or 'unnamed',
                        'port': port.port,
                        'target_port': str(port.target_port) if port.target_port else None,
                        'protocol': port.protocol,
                        'node_port': port.node_port if port.node_port else None
                    }
                    ports.append(port_info)
                
                service_info = {
                    'name': svc.metadata.name,
                    'namespace': svc.metadata.namespace,
                    'type': svc.spec.type,
                    'cluster_ip': svc.spec.cluster_ip,
                    'external_ips': external_ips or ['<none>'],
                    'ports': ports,
                    'selector': svc.spec.selector or {},
                    'created_at': svc.metadata.creation_timestamp.isoformat() if svc.metadata.creation_timestamp else None
                }
                service_list.append(service_info)
            
            logger.info(f"获取 Service 列表成功: {len(service_list)} 个 Service (namespace={namespace})")
            return service_list
        
        except ApiException as e:
            logger.error(f"获取 Service 列表失败 (API 错误): {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取 Service 列表失败: {str(e)}")
            return []
    
    def get_deployments(self, namespace: str = 'default') -> List[Dict[str, Any]]:
        """
        获取命名空间中的所有 Deployment
        
        Args:
            namespace: 命名空间名称
        
        Returns:
            list: Deployment 信息列表
                - name: Deployment 名称
                - namespace: 命名空间
                - replicas: 期望副本数
                - ready_replicas: 就绪副本数
                - available_replicas: 可用副本数
                - labels: 标签
                - selector: 选择器
                - images: 镜像列表
                - created_at: 创建时间
        """
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            
            deployment_list = []
            for deploy in deployments.items:
                # 获取镜像列表
                images = [container.image for container in deploy.spec.template.spec.containers]
                
                # 获取资源限制
                resources = []
                for container in deploy.spec.template.spec.containers:
                    if container.resources:
                        resource_info = {
                            'container': container.name,
                            'requests': {},
                            'limits': {}
                        }
                        if container.resources.requests:
                            resource_info['requests'] = dict(container.resources.requests)
                        if container.resources.limits:
                            resource_info['limits'] = dict(container.resources.limits)
                        resources.append(resource_info)
                
                deployment_info = {
                    'name': deploy.metadata.name,
                    'namespace': deploy.metadata.namespace,
                    'replicas': deploy.spec.replicas,
                    'ready_replicas': deploy.status.ready_replicas or 0,
                    'available_replicas': deploy.status.available_replicas or 0,
                    'updated_replicas': deploy.status.updated_replicas or 0,
                    'labels': deploy.metadata.labels or {},
                    'selector': deploy.spec.selector.match_labels or {},
                    'images': images,
                    'resources': resources,
                    'strategy': deploy.spec.strategy.type if deploy.spec.strategy else 'Unknown',
                    'created_at': deploy.metadata.creation_timestamp.isoformat() if deploy.metadata.creation_timestamp else None
                }
                deployment_list.append(deployment_info)
            
            logger.info(f"获取 Deployment 列表成功: {len(deployment_list)} 个 Deployment (namespace={namespace})")
            return deployment_list
        
        except ApiException as e:
            logger.error(f"获取 Deployment 列表失败 (API 错误): {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取 Deployment 列表失败: {str(e)}")
            return []
    
    def get_hpa(self, namespace: str = 'default', name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取 HPA (Horizontal Pod Autoscaler) 配置
        
        Args:
            namespace: 命名空间名称
            name: HPA 名称（可选，如果不指定则返回所有 HPA）
        
        Returns:
            dict: HPA 信息
                - name: HPA 名称
                - namespace: 命名空间
                - target: 目标资源
                - min_replicas: 最小副本数
                - max_replicas: 最大副本数
                - current_replicas: 当前副本数
                - desired_replicas: 期望副本数
                - metrics: 指标配置
                - current_metrics: 当前指标值
                - conditions: 状态条件
        """
        try:
            if name:
                # 获取指定的 HPA
                hpa = self.autoscaling_v2.read_namespaced_horizontal_pod_autoscaler(
                    name=name,
                    namespace=namespace
                )
                hpa_list = [hpa]
            else:
                # 获取所有 HPA
                hpa_response = self.autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(
                    namespace=namespace
                )
                hpa_list = hpa_response.items
            
            result = []
            for hpa in hpa_list:
                # 解析指标配置
                metrics = []
                for metric in (hpa.spec.metrics or []):
                    metric_info = {
                        'type': metric.type
                    }
                    if metric.type == 'Resource':
                        metric_info['resource'] = {
                            'name': metric.resource.name,
                            'target_type': metric.resource.target.type,
                            'target_value': None
                        }
                        if metric.resource.target.type == 'Utilization':
                            metric_info['resource']['target_value'] = metric.resource.target.average_utilization
                        elif metric.resource.target.type == 'AverageValue':
                            metric_info['resource']['target_value'] = metric.resource.target.average_value
                    metrics.append(metric_info)
                
                # 解析当前指标
                current_metrics = []
                for metric in (hpa.status.current_metrics or []):
                    current_metric_info = {
                        'type': metric.type
                    }
                    if metric.type == 'Resource':
                        current_metric_info['resource'] = {
                            'name': metric.resource.name,
                            'current_value': None
                        }
                        if metric.resource.current.average_utilization:
                            current_metric_info['resource']['current_value'] = metric.resource.current.average_utilization
                        elif metric.resource.current.average_value:
                            current_metric_info['resource']['current_value'] = metric.resource.current.average_value
                    current_metrics.append(current_metric_info)
                
                # 解析状态条件
                conditions = []
                for condition in (hpa.status.conditions or []):
                    conditions.append({
                        'type': condition.type,
                        'status': condition.status,
                        'reason': condition.reason,
                        'message': condition.message
                    })
                
                hpa_info = {
                    'name': hpa.metadata.name,
                    'namespace': hpa.metadata.namespace,
                    'target': {
                        'kind': hpa.spec.scale_target_ref.kind,
                        'name': hpa.spec.scale_target_ref.name
                    },
                    'min_replicas': hpa.spec.min_replicas,
                    'max_replicas': hpa.spec.max_replicas,
                    'current_replicas': hpa.status.current_replicas,
                    'desired_replicas': hpa.status.desired_replicas,
                    'metrics': metrics,
                    'current_metrics': current_metrics,
                    'conditions': conditions,
                    'created_at': hpa.metadata.creation_timestamp.isoformat() if hpa.metadata.creation_timestamp else None
                }
                result.append(hpa_info)
            
            logger.info(f"获取 HPA 信息成功: {len(result)} 个 HPA (namespace={namespace})")
            
            # 如果指定了名称，返回单个对象；否则返回列表
            if name:
                return result[0] if result else {}
            else:
                return {'items': result, 'count': len(result)}
        
        except ApiException as e:
            logger.error(f"获取 HPA 信息失败 (API 错误): {str(e)}")
            if name:
                return {'error': f'API 错误: {e.status} - {e.reason}'}
            else:
                return {'items': [], 'count': 0, 'error': f'API 错误: {e.status} - {e.reason}'}
        except Exception as e:
            logger.error(f"获取 HPA 信息失败: {str(e)}")
            if name:
                return {'error': str(e)}
            else:
                return {'items': [], 'count': 0, 'error': str(e)}
    
    def get_pvcs(self, namespace: str = 'default') -> List[Dict[str, Any]]:
        """
        获取 PersistentVolumeClaim 信息
        
        Args:
            namespace: 命名空间名称
        
        Returns:
            list: PVC 信息列表
                - name: PVC 名称
                - namespace: 命名空间
                - status: 状态
                - volume_name: 绑定的 PV 名称
                - storage_class: StorageClass 名称
                - access_modes: 访问模式
                - capacity: 容量
                - created_at: 创建时间
        """
        try:
            pvcs = self.core_v1.list_namespaced_persistent_volume_claim(namespace=namespace)
            
            pvc_list = []
            for pvc in pvcs.items:
                pvc_info = {
                    'name': pvc.metadata.name,
                    'namespace': pvc.metadata.namespace,
                    'status': pvc.status.phase,
                    'volume_name': pvc.spec.volume_name or 'N/A',
                    'storage_class': pvc.spec.storage_class_name or 'default',
                    'access_modes': pvc.spec.access_modes or [],
                    'requested_storage': pvc.spec.resources.requests.get('storage', 'unknown') if pvc.spec.resources.requests else 'unknown',
                    'capacity': pvc.status.capacity.get('storage', 'unknown') if pvc.status.capacity else 'unknown',
                    'labels': pvc.metadata.labels or {},
                    'created_at': pvc.metadata.creation_timestamp.isoformat() if pvc.metadata.creation_timestamp else None
                }
                pvc_list.append(pvc_info)
            
            logger.info(f"获取 PVC 列表成功: {len(pvc_list)} 个 PVC (namespace={namespace})")
            return pvc_list
        
        except ApiException as e:
            logger.error(f"获取 PVC 列表失败 (API 错误): {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取 PVC 列表失败: {str(e)}")
            return []
    
    def get_events(self, namespace: str = 'default', limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取事件列表
        
        Args:
            namespace: 命名空间名称
            limit: 返回的最大事件数
        
        Returns:
            list: 事件信息列表
                - type: 事件类型 (Normal/Warning)
                - reason: 原因
                - message: 消息
                - object: 相关对象
                - count: 发生次数
                - first_timestamp: 首次发生时间
                - last_timestamp: 最后发生时间
        """
        try:
            events = self.core_v1.list_namespaced_event(namespace=namespace)
            
            # 按最后发生时间排序
            sorted_events = sorted(
                events.items,
                key=lambda e: e.last_timestamp or e.event_time or e.metadata.creation_timestamp,
                reverse=True
            )
            
            event_list = []
            for event in sorted_events[:limit]:
                event_info = {
                    'type': event.type,
                    'reason': event.reason,
                    'message': event.message,
                    'object': {
                        'kind': event.involved_object.kind,
                        'name': event.involved_object.name,
                        'namespace': event.involved_object.namespace
                    },
                    'count': event.count or 1,
                    'first_timestamp': event.first_timestamp.isoformat() if event.first_timestamp else None,
                    'last_timestamp': event.last_timestamp.isoformat() if event.last_timestamp else (
                        event.event_time.isoformat() if event.event_time else None
                    ),
                    'source': event.source.component if event.source else 'unknown'
                }
                event_list.append(event_info)
            
            logger.info(f"获取事件列表成功: {len(event_list)} 个事件 (namespace={namespace})")
            return event_list
        
        except ApiException as e:
            logger.error(f"获取事件列表失败 (API 错误): {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取事件列表失败: {str(e)}")
            return []
