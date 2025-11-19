# API 文档

**作者：** RJ.Wang  
**邮箱：** wangrenjun@gmail.com  
**创建时间：** 2025-11-16  
**最后更新：** 2025-11-16

---

## 📑 目录

- [概述](#概述)
- [存储 API](#存储-api)
  - [EBS 存储 API](#ebs-存储-api)
  - [EFS 存储 API](#efs-存储-api)
  - [S3 对象存储 API](#s3-对象存储-api)
  - [存储概览 API](#存储概览-api)
- [功能 API](#功能-api)
  - [网络信息 API](#网络信息-api)
  - [Kubernetes 资源信息 API](#kubernetes-资源信息-api)
  - [扩展监控 API](#扩展监控-api)
  - [压力测试 API](#压力测试-api)

---

## 概述

本文档整合了 EKS Info WebApp 的所有 API 接口说明，包括存储管理、网络信息、资源监控、扩展管理和压力测试等功能模块。

### 基础信息

- **基础 URL**: `http://<your-app-url>`
- **数据格式**: JSON
- **认证方式**: IRSA (IAM Roles for Service Accounts)
- **时区**: UTC (ISO 8601 格式)

### 通用错误响应

所有 API 在发生错误时都会返回统一的错误格式：

```json
{
  "error": true,
  "error_type": "error_type_code",
  "message": "错误描述",
  "details": "详细错误信息（可选）",
  "timestamp": "2025-11-14T10:30:45.123Z"
}
```

---

## 存储 API

### EBS 存储 API

EBS 存储模块提供了对 EBS 块存储的访问功能，支持日志记录、数据持久化和磁盘管理。

#### 1. 获取 EBS 信息和最近日志

**端点：** `GET /ebs/`

**描述：** 获取 EBS 存储信息、磁盘使用情况和最近的访问日志

**响应示例：**
```json
{
  "ebs_info": {
    "mount_path": "/data/ebs",
    "available": true,
    "disk_usage": {
      "total_gb": 10.0,
      "used_gb": 2.5,
      "free_gb": 7.5,
      "usage_percent": 25.0
    },
    "log_file": {
      "exists": true,
      "path": "/data/ebs/access_logs.jsonl",
      "size_mb": 1.2,
      "line_count": 150
    }
  },
  "recent_logs": [...],
  "current_pod": {
    "name": "eks-info-app-7d8f9c-abc12",
    "namespace": "rj-webdemo",
    "node": "ip-10-101-11-45"
  }
}
```

#### 2. 写入数据

**端点：** `POST /ebs/write`

**请求体：**
```json
{
  "content": "要写入的数据内容"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "数据写入成功",
  "entry": {
    "timestamp": "2025-11-14T10:30:45.123Z",
    "type": "user_data",
    "pod_name": "eks-info-app-7d8f9c-abc12",
    "content": "要写入的数据内容"
  }
}
```

#### 3. 读取数据

**端点：** `GET /ebs/read?limit=50`

**查询参数：**
- `limit` (可选): 返回的最大记录数，默认 50，最大 500

#### 4. 获取详细信息

**端点：** `GET /ebs/info`

#### 5. 清理旧日志

**端点：** `POST /ebs/cleanup`

**请求体：**
```json
{
  "days": 7
}
```

**使用示例：**

```bash
# 获取 EBS 信息
curl http://localhost:5000/ebs/

# 写入数据
curl -X POST http://localhost:5000/ebs/write \
  -H "Content-Type: application/json" \
  -d '{"content": "测试数据"}'

# 读取数据
curl http://localhost:5000/ebs/read?limit=10

# 清理旧日志
curl -X POST http://localhost:5000/ebs/cleanup \
  -H "Content-Type: application/json" \
  -d '{"days": 7}'
```

**特性：**
- 自动日志记录
- 数据持久化
- 磁盘管理
- ReadWriteOnce 访问模式

---

### EFS 存储 API

EFS（Elastic File System）API 提供了对共享文件系统的访问接口，支持多个 Pod 同时读写同一个文件系统。

#### 1. 获取 EFS 信息

**端点：** `GET /efs/`

**描述：** 获取 EFS 文件系统信息和所有文件列表

**响应示例：**
```json
{
  "efs_info": {
    "mount_path": "/data/efs",
    "available": true,
    "filesystem_usage": {
      "total_gb": 8192.0,
      "used_gb": 1.5,
      "free_gb": 8190.5,
      "usage_percent": 0.02,
      "file_count": 5
    }
  },
  "files": [...],
  "file_count": 5
}
```

#### 2. 写入数据到 EFS

**端点：** `POST /efs/write`

**请求体：**
```json
{
  "content": "这是从 Pod 写入的测试数据"
}
```

#### 3. 读取所有数据

**端点：** `GET /efs/read`

#### 4. 读取指定文件

**端点：** `GET /efs/read/<filename>`

#### 5. 列出所有文件

**端点：** `GET /efs/list`

#### 6. 删除文件

**端点：** `DELETE /efs/delete/<filename>`

#### 7. 获取详细信息

**端点：** `GET /efs/info`

**使用示例：**

```bash
# 获取 EFS 信息
curl http://localhost:5000/efs/

# 写入数据
curl -X POST http://localhost:5000/efs/write \
  -H "Content-Type: application/json" \
  -d '{"content": "测试数据"}'

# 读取所有数据
curl http://localhost:5000/efs/read

# 列出文件
curl http://localhost:5000/efs/list

# 删除文件
curl -X DELETE http://localhost:5000/efs/delete/filename.json
```

**EFS 特性：**
- 多 Pod 共享（ReadWriteMany）
- 自动扩展容量
- 文件元数据记录
- 支持并发访问

**文件命名规则：**
```
shared_data_{timestamp}_{pod_name}.json
```

---

### S3 对象存储 API

S3 对象存储 API 提供了完整的 S3 对象管理功能，包括上传、下载、列出、删除对象，以及查看存储桶信息和 IRSA 配置。

#### 1. 获取 S3 概览信息

**端点：** `GET /s3/`

**响应示例：**
```json
{
  "s3_info": {
    "bucket_name": "eks-info-app-data",
    "region": "ap-southeast-1",
    "available": true,
    "bucket_details": {
      "object_count": 15,
      "total_size_mb": 0.04,
      "encryption": true
    }
  },
  "irsa_info": {
    "service_account": "arn:aws:iam::123456789012:role/eks-info-app-role",
    "using_irsa": true
  },
  "recent_objects": [...]
}
```

#### 2. 上传对象到 S3

**端点：** `POST /s3/upload`

**请求体：**
```json
{
  "content": "这是要上传的数据内容",
  "key": "my_custom_key.json"
}
```

#### 3. 列出 S3 对象

**端点：** `GET /s3/list?prefix=data_&max_keys=50`

**查询参数：**
- `prefix` (可选): 对象键前缀
- `max_keys` (可选): 最大对象数，默认 100，最大 1000

#### 4. 下载 S3 对象

**端点：** `GET /s3/download/<key>`

#### 5. 删除 S3 对象

**端点：** `DELETE /s3/delete/<key>`

#### 6. 获取 S3 详细信息

**端点：** `GET /s3/info`

**使用示例：**

```bash
# 上传数据
curl -X POST http://localhost:5000/s3/upload \
  -H "Content-Type: application/json" \
  -d '{"content": "测试数据", "key": "test.json"}'

# 列出对象
curl http://localhost:5000/s3/list?max_keys=10

# 下载对象
curl http://localhost:5000/s3/download/test.json

# 删除对象
curl -X DELETE http://localhost:5000/s3/delete/test.json
```

**IRSA 权限要求：**

```json
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
    }
  ]
}
```

---

### 存储概览 API

存储概览 API 提供了统一的接口来查看和管理 EKS 应用中使用的所有存储系统（EBS、EFS、S3）。

#### 1. 获取存储概览

**端点：** `GET /storage/`

**响应示例：**
```json
{
  "summary": {
    "storage_types": [
      {
        "type": "EBS",
        "available": true,
        "usage_percent": 15.5,
        "total_gb": 10.0
      },
      {
        "type": "EFS",
        "available": true,
        "file_count": 25,
        "usage_percent": 8.2
      },
      {
        "type": "S3",
        "available": true,
        "object_count": 150,
        "total_size_gb": 5.2
      }
    ],
    "available_count": 3,
    "total_count": 3
  },
  "storage_details": {...}
}
```

#### 2. 获取存储摘要

**端点：** `GET /storage/summary`

#### 3. 获取挂载点信息

**端点：** `GET /storage/mounts`

#### 4. 获取 EBS 详细信息

**端点：** `GET /storage/ebs`

#### 5. 获取 EFS 详细信息

**端点：** `GET /storage/efs`

#### 6. 获取 S3 详细信息

**端点：** `GET /storage/s3`

#### 7. 存储健康检查

**端点：** `GET /storage/health`

**使用示例：**

```bash
# 获取存储概览
curl http://localhost:5000/storage/

# 获取存储摘要
curl http://localhost:5000/storage/summary

# 健康检查
curl http://localhost:5000/storage/health
```

---

## 功能 API

### 网络信息 API

网络信息 API 提供了完整的 AWS 网络架构信息，包括 VPC、子网、安全组、路由表和负载均衡器的详细配置。

#### 1. 获取完整网络信息

**端点：** `GET /network/`

**响应示例：**
```json
{
  "vpc": {
    "vpc_id": "vpc-0123456789abcdef0",
    "cidr_block": "10.0.0.0/16",
    "state": "available"
  },
  "current_subnet": {...},
  "all_subnets": [...],
  "security_groups": [...],
  "route_tables": [...],
  "load_balancers": [...],
  "summary": {
    "vpc_id": "vpc-0123456789abcdef0",
    "subnet_count": 6,
    "security_group_count": 3
  }
}
```

#### 2. 获取 VPC 详细信息

**端点：** `GET /network/vpc`

#### 3. 获取所有子网信息

**端点：** `GET /network/subnets`

#### 4. 获取安全组信息

**端点：** `GET /network/security-groups`

#### 5. 获取路由表信息

**端点：** `GET /network/route-tables`

#### 6. 获取负载均衡器信息

**端点：** `GET /network/load-balancers`

#### 7. 网络服务健康检查

**端点：** `GET /network/health`

**使用示例：**

```bash
# 获取完整网络信息
curl http://localhost:5000/network/

# 获取安全组信息
curl http://localhost:5000/network/security-groups

# 获取负载均衡器信息
curl http://localhost:5000/network/load-balancers
```

**权限要求：**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeRouteTables",
        "elasticloadbalancing:DescribeLoadBalancers"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Kubernetes 资源信息 API

Kubernetes 资源信息 API 提供了查看和监控 EKS 集群中各种 Kubernetes 资源的功能。

#### 1. 获取完整资源信息

**端点：** `GET /resources/`

**响应示例：**
```json
{
  "namespace": "rj-webdemo",
  "pods": [...],
  "services": [...],
  "deployments": [...],
  "nodes": [...],
  "pvcs": [...],
  "hpa": {...},
  "statistics": {
    "pods": {
      "total": 3,
      "running": 3
    },
    "nodes": {
      "total": 3,
      "ready": 3
    }
  }
}
```

#### 2. 获取 Pod 列表

**端点：** `GET /resources/pods?namespace=default&label_selector=app=myapp`

#### 3. 获取 Service 列表

**端点：** `GET /resources/services`

#### 4. 获取 Deployment 列表

**端点：** `GET /resources/deployments`

#### 5. 获取节点列表

**端点：** `GET /resources/nodes`

#### 6. 获取 PVC 列表

**端点：** `GET /resources/pvcs`

#### 7. 获取 HPA 信息

**端点：** `GET /resources/hpa?name=eks-info-app-hpa`

#### 8. 获取事件列表

**端点：** `GET /resources/events?limit=50`

#### 9. 获取当前 Pod 信息

**端点：** `GET /resources/current-pod`

#### 10. 健康检查

**端点：** `GET /resources/health`

**使用示例：**

```bash
# 获取所有资源信息
curl http://localhost:5000/resources/

# 获取特定应用的 Pod
curl "http://localhost:5000/resources/pods?label_selector=app=eks-info-app"

# 获取节点信息
curl http://localhost:5000/resources/nodes

# 获取 HPA 信息
curl http://localhost:5000/resources/hpa
```

---

### 扩展监控 API

扩展监控 API 提供了 Kubernetes 集群扩展状态的实时监控和历史分析功能。

#### 1. 扩展监控概览

**端点：** `GET /scaling/`

**响应示例：**
```json
{
  "nodes": [...],
  "node_count": 3,
  "total_pods": 15,
  "pending_pods": [],
  "hpa": {
    "items": [
      {
        "name": "eks-info-app-hpa",
        "current_replicas": 3,
        "desired_replicas": 3,
        "current_cpu_utilization": 45,
        "target_cpu_utilization": 70
      }
    ]
  }
}
```

#### 2. 获取节点列表

**端点：** `GET /scaling/nodes`

#### 3. 获取 Pod 列表

**端点：** `GET /scaling/pods?namespace=default`

#### 4. 获取 HPA 状态

**端点：** `GET /scaling/hpa?name=eks-info-app-hpa`

#### 5. 获取 Pending 状态的 Pod

**端点：** `GET /scaling/pending`

#### 6. 获取扩展相关事件

**端点：** `GET /scaling/events?limit=50`

#### 7. 刷新扩展状态

**端点：** `POST /scaling/refresh`

#### 8. 获取扩展历史

**端点：** `GET /scaling/history?hours=24`

**响应示例：**
```json
{
  "resource_trends": {
    "pod_count_trend": [...],
    "node_count_trend": [...],
    "cpu_trend": [...],
    "memory_trend": [...]
  },
  "scaling_events": [...],
  "scaling_statistics": {
    "total_events": 3,
    "success_rate": 100.0
  }
}
```

#### 9. 获取扩展事件历史

**端点：** `GET /scaling/history/events?hours=24`

#### 10. 获取资源使用趋势

**端点：** `GET /scaling/history/trends?hours=24`

#### 11. 获取扩展统计信息

**端点：** `GET /scaling/history/statistics?hours=24`

#### 12. 获取图表数据

**端点：** `GET /scaling/history/chart-data?hours=24`

#### 13. 记录扩展事件

**端点：** `POST /scaling/record-event`

**请求体：**
```json
{
  "event_type": "pod_scale_up",
  "trigger": "cpu_threshold_exceeded",
  "details": {
    "replicas_before": 3,
    "replicas_after": 5
  },
  "status": "completed"
}
```

#### 14. 记录资源指标

**端点：** `POST /scaling/metrics/record`

**请求体：**
```json
{
  "cpu_usage": 75.5,
  "memory_usage": 65.3,
  "pod_count": 5,
  "node_count": 3
}
```

**使用示例：**

```bash
# 获取扩展概览
curl http://localhost:5000/scaling/

# 获取扩展历史
curl "http://localhost:5000/scaling/history?hours=48"

# 监控 HPA 状态
watch -n 5 'curl -s http://localhost:5000/scaling/hpa | jq'

# 记录扩展事件
curl -X POST http://localhost:5000/scaling/record-event \
  -H "Content-Type: application/json" \
  -d '{"event_type": "pod_scale_up", "trigger": "manual_test"}'
```

---

### 压力测试 API

压力测试 API 提供了 CPU 和内存压力测试功能，用于演示 Kubernetes HPA 的自动扩展能力。

#### 1. 获取压力测试概览

**端点：** `GET /stress/`

**响应示例：**
```json
{
  "current_resources": {
    "cpu": {
      "usage_percent": 15.5
    },
    "memory": {
      "total_mb": 512.0,
      "used_mb": 256.3,
      "percent": 50.1
    }
  },
  "active_tests": [],
  "test_options": {
    "cpu": {
      "duration_range": [1, 300],
      "intensity_range": [1, 100]
    },
    "memory": {
      "duration_range": [1, 300],
      "target_mb_range": [10, 400]
    }
  }
}
```

#### 2. 启动 CPU 压力测试

**端点：** `POST /stress/cpu/start`

**请求体：**
```json
{
  "duration": 60,
  "intensity": 80
}
```

**参数说明：**
- `duration`（可选）：测试持续时间（秒），范围 1-300，默认 60
- `intensity`（可选）：压力强度（1-100），默认 100

#### 3. 启动内存压力测试

**端点：** `POST /stress/memory/start`

**请求体：**
```json
{
  "duration": 60,
  "target_mb": 100
}
```

**参数说明：**
- `duration`（可选）：测试持续时间（秒），范围 1-300，默认 60
- `target_mb`（可选）：目标内存分配大小（MB），范围 10-500，默认 100

#### 4. 获取测试状态

**端点：** `GET /stress/status/<test_id>`

#### 5. 停止测试

**端点：** `POST /stress/stop/<test_id>`

#### 6. 获取当前资源使用情况

**端点：** `GET /stress/resources`

#### 7. 获取所有测试

**端点：** `GET /stress/tests`

#### 8. 清理已完成的测试

**端点：** `POST /stress/cleanup`

**请求体（可选）：**
```json
{
  "max_age_seconds": 3600
}
```

**使用示例：**

```bash
# 启动 CPU 压力测试
curl -X POST http://localhost:5000/stress/cpu/start \
  -H "Content-Type: application/json" \
  -d '{"duration": 180, "intensity": 90}'

# 启动内存压力测试
curl -X POST http://localhost:5000/stress/memory/start \
  -H "Content-Type: application/json" \
  -d '{"duration": 180, "target_mb": 300}'

# 监控资源使用
watch -n 5 'curl -s http://localhost:5000/stress/resources | jq'

# 获取所有测试
curl http://localhost:5000/stress/tests

# 停止测试
curl -X POST http://localhost:5000/stress/stop/<test_id>
```

**测试状态说明：**

- `running`：测试正在运行
- `completed`：测试已正常完成
- `stopped`：测试被手动停止
- `failed`：测试执行失败

---

## 使用场景示例

### 场景 1：演示 HPA 自动扩展

```bash
# 1. 启动 CPU 压力测试
curl -X POST http://localhost:5000/stress/cpu/start \
  -H "Content-Type: application/json" \
  -d '{"duration": 180, "intensity": 90}'

# 2. 监控扩展状态
watch -n 5 'curl -s http://localhost:5000/scaling/ | jq'

# 3. 观察 Pod 扩展
kubectl get pods -n rj-webdemo -w

# 4. 查看扩展历史
curl http://localhost:5000/scaling/history
```

### 场景 2：存储功能演示

```bash
# 1. 写入 EBS 数据
curl -X POST http://localhost:5000/ebs/write \
  -H "Content-Type: application/json" \
  -d '{"content": "EBS 测试数据"}'

# 2. 写入 EFS 数据
curl -X POST http://localhost:5000/efs/write \
  -H "Content-Type: application/json" \
  -d '{"content": "EFS 测试数据"}'

# 3. 上传 S3 对象
curl -X POST http://localhost:5000/s3/upload \
  -H "Content-Type: application/json" \
  -d '{"content": "S3 测试数据", "key": "test.json"}'

# 4. 查看存储概览
curl http://localhost:5000/storage/
```

### 场景 3：网络和资源监控

```bash
# 1. 获取网络信息
curl http://localhost:5000/network/ | jq

# 2. 获取资源信息
curl http://localhost:5000/resources/ | jq

# 3. 查看节点状态
curl http://localhost:5000/resources/nodes | jq

# 4. 查看 HPA 状态
curl http://localhost:5000/resources/hpa | jq
```

---

## 注意事项

### 权限要求

1. **IRSA 配置**：确保 Kubernetes ServiceAccount 正确配置了 IAM 角色
2. **RBAC 权限**：应用需要有足够的 Kubernetes RBAC 权限
3. **AWS API 权限**：IAM 角色需要有访问 EC2、ELB、S3 等服务的权限

### 性能考虑

1. **API 限流**：AWS API 有速率限制，建议实现缓存机制
2. **并发访问**：某些存储操作可能受到并发限制
3. **数据保留**：定期清理历史数据以节省存储空间

### 安全考虑

1. **敏感信息**：不要在 API 响应中包含敏感信息
2. **输入验证**：所有用户输入都应进行验证
3. **错误处理**：避免在错误消息中泄露系统信息

---

## 相关文档

- [EKS Info WebApp README](README.md)
- [Docker 构建指南](DOCKER_BUILD_GUIDE.md)
- [AWS EKS 文档](https://docs.aws.amazon.com/eks/)
- [Kubernetes 文档](https://kubernetes.io/docs/)

---

**文档版本**: 1.0  
**最后更新**: 2025-11-16
