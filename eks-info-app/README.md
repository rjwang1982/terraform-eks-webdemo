# EKS Info WebApp

**作者：** RJ.Wang  
**邮箱：** wangrenjun@gmail.com  
**创建时间：** 2025-11-13

## 项目简介

EKS Info WebApp 是一个基于 Python Flask 的 Web 应用，部署在 Amazon EKS 集群中，用于演示和展示：

1. **EKS 环境信息** - Pod、Node、集群、网络、EC2 实例详细信息
2. **存储服务访问** - 演示 EBS、EFS、S3 三种存储服务的使用方式
3. **自动扩展能力** - 演示 HPA 和 Cluster Autoscaler 的工作原理

## 功能特性

### 环境信息展示
- Pod 基本信息（名称、命名空间、IP、节点）
- Kubernetes 集群信息（版本、API 服务器）
- EC2 实例信息（实例 ID、类型、可用区）
- 系统架构信息（ARM64 检测）
- 网络架构信息（VPC、子网、安全组）

### 存储服务演示
- **EBS 块存储** - 持久化访问日志，演示单 Pod 存储
- **EFS 共享文件系统** - 多 Pod 共享文件，演示分布式存储
- **S3 对象存储** - 使用 IRSA 访问，演示对象存储操作

### 压力测试和自动扩展
- CPU 压力测试触发 HPA Pod 扩展
- 内存压力测试触发 HPA Pod 扩展
- 监控节点自动扩展（Cluster Autoscaler）
- 扩展历史和指标可视化

## 项目结构

```
eks-info-app/
├── app.py                 # Flask 应用主文件
├── config.py              # 应用配置
├── requirements.txt       # Python 依赖
├── API_DOCUMENTATION.md   # API 文档（详细的 API 使用说明）
├── services/              # 服务层
│   ├── __init__.py
│   ├── environment_service.py
│   ├── kubernetes_service.py
│   ├── aws_service.py
│   ├── stress_test_service.py
│   └── metrics_service.py
├── storage/               # 存储访问层
│   ├── __init__.py
│   ├── ebs_storage.py
│   ├── efs_storage.py
│   └── s3_storage.py
├── routes/                # 路由处理器
│   ├── __init__.py
│   ├── home.py
│   ├── storage.py
│   ├── network.py
│   ├── resources.py
│   ├── stress.py
│   └── health.py
├── templates/             # HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── storage.html
│   ├── ebs.html
│   ├── efs.html
│   ├── s3.html
│   ├── network.html
│   ├── resources.html
│   ├── stress.html
│   └── scaling.html
├── static/                # 静态资源
│   ├── css/
│   └── js/
└── tests/                 # 测试文件
    ├── __init__.py
    ├── conftest.py
    └── test_*.py
```

## 技术栈

- **Web 框架**: Flask 3.0.0
- **AWS SDK**: boto3 1.34.0
- **Kubernetes 客户端**: kubernetes 28.1.0
- **系统信息**: psutil 5.9.6
- **HTTP 客户端**: requests 2.31.0
- **WSGI 服务器**: gunicorn 21.2.0

## 本地开发

### 前置要求
- Python 3.11+
- UV 包管理器（推荐）

### 安装依赖

```bash
# 使用 UV 创建虚拟环境
uv venv
source .venv/bin/activate  # macOS/Linux

# 安装依赖
uv pip install -r requirements.txt
```

### 运行应用

```bash
# 设置环境变量
export FLASK_APP=app.py
export FLASK_ENV=development

# 运行应用
python app.py
```

应用将在 http://localhost:5000 启动。

## 部署到 EKS

详细的部署步骤请参考项目根目录的 README.md 文件。

### 快速部署

```bash
# 1. 构建 Docker 镜像
docker buildx build --platform linux/arm64 -t <ECR_REPO>/eks-info-app:latest .

# 2. 推送到 ECR
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <ECR_REPO>
docker push <ECR_REPO>/eks-info-app:latest

# 3. 部署到 EKS
kubectl apply -f k8s/
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `POD_NAME` | Pod 名称 | unknown-pod |
| `POD_NAMESPACE` | Pod 命名空间 | default |
| `NODE_NAME` | 节点名称 | unknown-node |
| `S3_BUCKET_NAME` | S3 存储桶名称 | eks-info-app-data |
| `EBS_MOUNT_PATH` | EBS 挂载路径 | /data/ebs |
| `EFS_MOUNT_PATH` | EFS 挂载路径 | /data/efs |
| `AWS_REGION` | AWS 区域 | ap-southeast-1 |
| `LOG_LEVEL` | 日志级别 | INFO |

## API 端点

### 健康检查
- `GET /health` - 基本健康检查
- `GET /ready` - 就绪检查（包含存储可用性）

### 页面路由
- `GET /` - 首页（环境信息）
- `GET /storage` - 存储概览
- `GET /ebs` - EBS 演示
- `GET /efs` - EFS 演示
- `GET /s3` - S3 演示
- `GET /network` - 网络信息
- `GET /resources` - Kubernetes 资源
- `GET /stress` - 压力测试
- `GET /scaling` - 扩展监控

详细的 API 使用说明和示例请参考 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)。

## 测试

### 运行测试

项目的所有测试文件位于 `tests/` 目录中。

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_aws_service.py -v

# 运行测试并显示覆盖率
pytest tests/ --cov=. --cov-report=html
```

### 测试结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest 配置和共享 fixtures
├── test_aws_service.py      # AWS 服务测试
├── test_ebs_storage.py      # EBS 存储测试
├── test_efs_storage.py      # EFS 存储测试
├── test_s3_storage.py       # S3 存储测试
├── test_kubernetes_service.py  # Kubernetes 服务测试
├── test_environment_service.py # 环境服务测试
├── test_metrics_service.py  # 指标服务测试
└── test_*_routes.py         # 路由处理器测试
```

## 许可证

本项目仅供学习和演示使用。

## 作者

RJ.Wang - wangrenjun@gmail.com
