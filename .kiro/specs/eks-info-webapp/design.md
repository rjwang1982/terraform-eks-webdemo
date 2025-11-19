# 设计文档

**作者：** RJ.Wang  
**邮箱：** wangrenjun@gmail.com  
**创建时间：** 2025-11-13

## 概述

EKS Info WebApp 是一个基于 Python Flask 的 Web 应用，部署在 EKS 集群中，用于演示和展示：
1. EKS 环境的详细信息（Pod、Node、集群、网络、EC2）
2. 三种 AWS 存储服务的访问方式（EBS、EFS、S3）
3. Kubernetes 自动扩展能力（HPA 和 Cluster Autoscaler）

应用采用轻量级设计，使用 ARM64 架构，通过 IRSA 机制安全访问 AWS 服务。

## 架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Internet / User                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Load Balancer                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Ingress                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes Service (ClusterIP)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    ┌───────┐          ┌───────┐          ┌───────┐
    │ Pod 1 │          │ Pod 2 │          │ Pod 3 │
    │       │          │       │          │       │
    │ Flask │          │ Flask │          │ Flask │
    │  App  │          │  App  │          │  App  │
    └───┬───┘          └───┬───┘          └───┬───┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ┌───────┐          ┌───────┐          ┌───────┐
    │  EBS  │          │  EFS  │          │  S3   │
    │ (PVC) │          │(Shared)│         │(IRSA) │
    └───────┘          └───────┘          └───────┘
```

### 应用层架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Flask Application                    │
├─────────────────────────────────────────────────────────────┤
│  Web Layer (Routes & Templates)                            │
│  ├── / (首页 - 环境信息)                                    │
│  ├── /storage (存储概览)                                    │
│  ├── /ebs (EBS 演示)                                        │
│  ├── /efs (EFS 演示)                                        │
│  ├── /s3 (S3 演示)                                          │
│  ├── /network (网络信息)                                    │
│  ├── /resources (K8S 资源)                                  │
│  ├── /stress (压力测试)                                     │
│  ├── /scaling (扩展监控)                                    │
│  └── /health, /ready (健康检查)                             │
├─────────────────────────────────────────────────────────────┤
│  Service Layer (Business Logic)                            │
│  ├── EnvironmentService (环境信息收集)                      │
│  ├── StorageService (存储操作)                              │
│  ├── KubernetesService (K8S API 交互)                       │
│  ├── AWSService (AWS API 交互)                              │
│  ├── StressTestService (压力测试)                           │
│  └── MetricsService (指标收集)                              │
├─────────────────────────────────────────────────────────────┤
│  Data Access Layer                                         │
│  ├── EBSStorage (EBS 文件操作)                              │
│  ├── EFSStorage (EFS 文件操作)                              │
│  └── S3Storage (S3 对象操作)                                │
├─────────────────────────────────────────────────────────────┤
│  External Dependencies                                      │
│  ├── boto3 (AWS SDK)                                        │
│  ├── kubernetes (K8S Python Client)                         │
│  ├── psutil (系统信息)                                       │
│  └── requests (HTTP 请求)                                   │
└─────────────────────────────────────────────────────────────┘
```

## 组件和接口

### 1. Web 层组件

#### 1.1 Flask 应用主体
```python
# app.py
- 初始化 Flask 应用
- 配置路由
- 错误处理
- 日志配置
```

#### 1.2 路由处理器
```python
# routes/
- home.py: 首页和环境信息
- storage.py: 存储相关路由
- network.py: 网络信息路由
- resources.py: K8S 资源路由
- stress.py: 压力测试路由
- health.py: 健康检查路由
```

### 2. 服务层组件

#### 2.1 EnvironmentService
**职责**: 收集环境信息
```python
class EnvironmentService:
    def get_pod_info() -> dict
    def get_node_info() -> dict
    def get_cluster_info() -> dict
    def get_ec2_metadata() -> dict
    def get_system_info() -> dict
    def get_architecture_info() -> dict
```

#### 2.2 StorageService
**职责**: 管理存储操作
```python
class StorageService:
    def get_mount_points() -> list
    def get_ebs_info() -> dict
    def get_efs_info() -> dict
    def get_s3_info() -> dict
    def write_to_ebs(data: str) -> bool
    def read_from_ebs() -> list
    def write_to_efs(data: str, pod_name: str) -> bool
    def read_from_efs() -> list
    def upload_to_s3(key: str, data: bytes) -> bool
    def list_s3_objects() -> list
    def download_from_s3(key: str) -> bytes
    def delete_from_s3(key: str) -> bool
```

#### 2.3 KubernetesService
**职责**: 与 Kubernetes API 交互
```python
class KubernetesService:
    def __init__(self)
    def get_current_pod() -> dict
    def get_pods(namespace: str) -> list
    def get_nodes() -> list
    def get_services(namespace: str) -> list
    def get_deployments(namespace: str) -> list
    def get_hpa(namespace: str) -> dict
    def get_pvcs(namespace: str) -> list
    def get_events(namespace: str) -> list
```

#### 2.4 AWSService
**职责**: 与 AWS API 交互
```python
class AWSService:
    def __init__(self)
    def get_ec2_instance_info(instance_id: str) -> dict
    def get_vpc_info(vpc_id: str) -> dict
    def get_subnet_info(subnet_id: str) -> dict
    def get_security_groups(group_ids: list) -> list
    def get_ebs_volume_info(volume_id: str) -> dict
    def get_efs_filesystem_info(fs_id: str) -> dict
    def get_load_balancers() -> list
```

#### 2.5 StressTestService
**职责**: 执行压力测试
```python
class StressTestService:
    def start_cpu_stress(duration: int, intensity: int) -> str
    def start_memory_stress(duration: int, target_mb: int) -> str
    def get_stress_status(test_id: str) -> dict
    def stop_stress(test_id: str) -> bool
    def get_current_cpu_usage() -> float
    def get_current_memory_usage() -> dict
```

#### 2.6 MetricsService
**职责**: 收集和存储指标
```python
class MetricsService:
    def record_access(request_info: dict) -> None
    def get_access_stats() -> dict
    def record_scaling_event(event: dict) -> None
    def get_scaling_history(hours: int) -> list
    def get_resource_trends() -> dict
```

### 3. 数据访问层组件

#### 3.1 EBSStorage
```python
class EBSStorage:
    def __init__(self, mount_path: str)
    def write_log(entry: dict) -> bool
    def read_logs(limit: int) -> list
    def get_disk_usage() -> dict
    def cleanup_old_logs(days: int) -> int
```

#### 3.2 EFSStorage
```python
class EFSStorage:
    def __init__(self, mount_path: str)
    def write_file(filename: str, content: str, metadata: dict) -> bool
    def read_file(filename: str) -> tuple
    def list_files() -> list
    def delete_file(filename: str) -> bool
    def get_filesystem_usage() -> dict
```

#### 3.3 S3Storage
```python
class S3Storage:
    def __init__(self, bucket_name: str)
    def upload_object(key: str, data: bytes, metadata: dict) -> bool
    def download_object(key: str) -> bytes
    def list_objects(prefix: str) -> list
    def delete_object(key: str) -> bool
    def get_bucket_info() -> dict
```

## 数据模型

### 1. 访问日志记录 (EBS)
```json
{
  "timestamp": "2025-11-13T10:30:45.123Z",
  "pod_name": "eks-info-app-7d8f9c-abc12",
  "node_name": "ip-10-101-11-45.ap-southeast-1.compute.internal",
  "client_ip": "203.0.113.42",
  "request_path": "/ebs",
  "request_method": "GET",
  "user_agent": "Mozilla/5.0...",
  "response_status": 200,
  "response_time_ms": 45
}
```

### 2. EFS 共享文件记录
```json
{
  "filename": "shared_data_20251113_103045.txt",
  "content": "Test data from pod",
  "metadata": {
    "created_by_pod": "eks-info-app-7d8f9c-abc12",
    "created_at": "2025-11-13T10:30:45.123Z",
    "size_bytes": 1024,
    "content_type": "text/plain"
  }
}
```

### 3. S3 统计数据对象
```json
{
  "report_id": "stats_20251113_103000",
  "time_range": {
    "start": "2025-11-13T10:00:00Z",
    "end": "2025-11-13T10:30:00Z"
  },
  "statistics": {
    "total_requests": 150,
    "unique_ips": 25,
    "path_distribution": {
      "/": 50,
      "/ebs": 30,
      "/efs": 25,
      "/s3": 20,
      "/stress": 15,
      "/other": 10
    },
    "avg_response_time_ms": 52.3,
    "error_count": 2
  },
  "generated_by": "eks-info-app-7d8f9c-abc12",
  "generated_at": "2025-11-13T10:30:00Z"
}
```

### 4. 扩展事件记录
```json
{
  "event_id": "scale_20251113_103045",
  "event_type": "pod_scale_up",
  "timestamp": "2025-11-13T10:30:45.123Z",
  "trigger": "cpu_threshold_exceeded",
  "details": {
    "metric_name": "cpu_utilization",
    "metric_value": 85.5,
    "threshold": 70.0,
    "replicas_before": 3,
    "replicas_after": 5,
    "duration_seconds": 45
  },
  "status": "completed"
}
```

## 错误处理

### 1. 错误分类

#### 1.1 存储错误
- EBS 挂载失败或不可访问
- EFS 文件系统不可用
- S3 权限不足或网络错误

**处理策略**: 
- 记录详细错误日志
- 返回友好的错误消息给用户
- 继续运行其他功能
- 在健康检查中报告状态

#### 1.2 Kubernetes API 错误
- 权限不足
- API 服务器不可达
- 资源不存在

**处理策略**:
- 使用重试机制（最多 3 次）
- 降级显示部分信息
- 记录错误但不中断服务

#### 1.3 AWS API 错误
- IRSA 凭证过期
- API 限流
- 资源不存在

**处理策略**:
- 自动刷新凭证
- 实现指数退避重试
- 缓存成功的响应

#### 1.4 压力测试错误
- 资源限制导致 OOM
- 测试超时

**处理策略**:
- 设置资源上限
- 实现优雅的超时处理
- 自动清理资源

### 2. 错误响应格式
```json
{
  "error": true,
  "error_type": "storage_error",
  "message": "无法访问 EBS 卷",
  "details": "Mount point /data/ebs is not accessible",
  "timestamp": "2025-11-13T10:30:45.123Z",
  "request_id": "req_abc123"
}
```

## 测试策略

### 1. 单元测试
- 测试每个服务类的方法
- Mock 外部依赖（AWS SDK、K8S Client）
- 覆盖率目标：70%

### 2. 集成测试
- 测试存储操作的完整流程
- 测试 Kubernetes API 交互
- 测试 AWS API 交互

### 3. 压力测试验证
- 验证 CPU 压力测试能触发 HPA
- 验证内存压力测试的资源清理
- 验证扩展事件的正确记录

### 4. 端到端测试
- 部署到实际 EKS 集群
- 验证所有存储挂载正常
- 验证 IRSA 权限配置正确
- 验证自动扩展功能

## Kubernetes 资源配置

### 1. Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eks-info-app
  namespace: rj-webdemo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: eks-info-app
  template:
    metadata:
      labels:
        app: eks-info-app
    spec:
      serviceAccountName: eks-info-app-sa
      containers:
      - name: eks-info-app
        image: <ECR_REPO>/eks-info-app:latest
        ports:
        - containerPort: 5000
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        volumeMounts:
        - name: ebs-storage
          mountPath: /data/ebs
        - name: efs-storage
          mountPath: /data/efs
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: S3_BUCKET_NAME
          value: "eks-info-app-data"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: ebs-storage
        persistentVolumeClaim:
          claimName: eks-info-app-ebs-pvc
      - name: efs-storage
        persistentVolumeClaim:
          claimName: eks-info-app-efs-pvc
```

### 2. HorizontalPodAutoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: eks-info-app-hpa
  namespace: rj-webdemo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: eks-info-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 50
        periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### 3. EBS PersistentVolumeClaim
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: eks-info-app-ebs-pvc
  namespace: rj-webdemo
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 10Gi
```

### 4. EFS PersistentVolumeClaim
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: eks-info-app-efs-pvc
  namespace: rj-webdemo
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: efs-sc
  resources:
    requests:
      storage: 20Gi
```

### 5. ServiceAccount with IRSA
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: eks-info-app-sa
  namespace: rj-webdemo
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<ACCOUNT_ID>:role/eks-info-app-role
```

### 6. IAM Role Policy (Terraform)
```hcl
# S3 访问权限
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::eks-info-app-data",
        "arn:aws:s3:::eks-info-app-data/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeRouteTables"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticfilesystem:DescribeFileSystems",
        "elasticfilesystem:DescribeMountTargets"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups"
      ],
      "Resource": "*"
    }
  ]
}
```

## 存储配置

### 1. EBS CSI Driver
- 使用 AWS EBS CSI Driver
- StorageClass: gp3（通用 SSD）
- 访问模式: ReadWriteOnce
- 用途: 单 Pod 持久化日志

### 2. EFS CSI Driver
- 使用 AWS EFS CSI Driver
- StorageClass: efs-sc
- 访问模式: ReadWriteMany
- 用途: 多 Pod 共享文件

### 3. S3 访问
- 使用 boto3 SDK
- 通过 IRSA 获取临时凭证
- 不需要挂载卷
- 用途: 对象存储和归档

## Docker 镜像构建

### Dockerfile (ARM64)
```dockerfile
FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /data/ebs /data/efs

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# 启动应用
CMD ["python", "app.py"]
```

### requirements.txt
```
Flask==3.0.0
boto3==1.34.0
kubernetes==28.1.0
psutil==5.9.6
requests==2.31.0
gunicorn==21.2.0
```

## 部署流程

### 1. 构建和推送镜像
```bash
# 构建 ARM64 镜像
docker buildx build --platform linux/arm64 -t <ECR_REPO>/eks-info-app:latest .

# 推送到 ECR
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <ECR_REPO>
docker push <ECR_REPO>/eks-info-app:latest
```

### 2. 部署存储资源
```bash
# 安装 EBS CSI Driver
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.25"

# 安装 EFS CSI Driver
kubectl apply -k "github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.7"

# 创建 EFS 文件系统（Terraform）
# 创建 S3 存储桶（Terraform）
```

### 3. 部署应用
```bash
# 应用 Kubernetes 资源
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/storageclass.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

### 4. 配置 Cluster Autoscaler
```bash
# 部署 Cluster Autoscaler
kubectl apply -f k8s/cluster-autoscaler.yaml
```

## 监控和日志

### 1. 应用日志
- 使用 Python logging 模块
- 日志级别: INFO
- 输出到 stdout（由 Kubernetes 收集）
- 格式: JSON 结构化日志

### 2. 指标收集
- 使用 Prometheus 格式暴露指标
- 端点: /metrics
- 指标包括:
  - HTTP 请求计数和延迟
  - 存储操作计数和延迟
  - 压力测试状态
  - 扩展事件计数

### 3. 健康检查
- /health: 基本健康检查
- /ready: 就绪检查（包含存储可用性）

## 安全考虑

### 1. IRSA 配置
- 使用 IAM Roles for Service Accounts
- 最小权限原则
- 不在代码中硬编码凭证

### 2. 网络安全
- Pod 运行在私有子网
- 通过 ALB 暴露服务
- 配置安全组限制访问

### 3. 数据安全
- EBS 卷加密
- EFS 文件系统加密
- S3 存储桶加密

### 4. 容器安全
- 使用非 root 用户运行
- 只读根文件系统
- 限制容器权限

## 性能优化

### 1. 缓存策略
- 缓存 AWS API 响应（5 分钟）
- 缓存 Kubernetes API 响应（1 分钟）
- 使用内存缓存（不引入 Redis）

### 2. 异步处理
- 压力测试在后台线程执行
- S3 上传使用异步操作
- 指标收集不阻塞请求

### 3. 资源限制
- 设置合理的 CPU 和内存限制
- 配置 HPA 避免过度扩展
- 限制压力测试的强度

## 故障恢复

### 1. Pod 重启
- EBS 数据持久化，重启后可恢复
- EFS 数据在所有 Pod 间共享
- S3 数据永久存储

### 2. 节点故障
- Pod 自动调度到健康节点
- EBS 卷自动重新挂载
- EFS 继续可用

### 3. 存储故障
- 应用继续运行其他功能
- 在 UI 中显示存储状态
- 记录错误日志

## 扩展性设计

### 1. 水平扩展
- 支持多 Pod 副本
- 无状态设计（状态存储在外部）
- 通过 HPA 自动扩展

### 2. 垂直扩展
- 可调整资源限制
- 支持更大的压力测试负载

### 3. 功能扩展
- 模块化设计便于添加新功能
- 插件式存储后端
- 可配置的指标收集
