# 需求文档

**作者：** RJ.Wang  
**邮箱：** wangrenjun@gmail.com  
**创建时间：** 2025-11-13

## 简介

开发一个基于 Python 的 Web 应用，部署到现有 EKS 集群中，核心目标是演示部署在 EKS 中的应用如何访问和使用 AWS 的三种存储服务（EBS、EFS、S3）。应用将展示环境信息，并通过实际的读写操作演示每种存储服务的特性和使用方式。

## 术语表

- **EKS_Info_App**: 本项目开发的 EKS 环境信息展示应用
- **Pod**: Kubernetes 中运行容器的最小单元
- **Node**: Kubernetes 集群中的工作节点（EC2 实例）
- **EBS**: Elastic Block Store，块存储服务
- **EFS**: Elastic File System，共享文件系统
- **S3**: Simple Storage Service，对象存储服务
- **IRSA**: IAM Roles for Service Accounts，Kubernetes 服务账号的 IAM 角色绑定
- **CSI Driver**: Container Storage Interface 驱动程序
- **ARM64**: 基于 ARM 架构的 64 位处理器架构
- **Graviton**: AWS 自研的基于 ARM 架构的处理器
- **HPA**: Horizontal Pod Autoscaler，Kubernetes 水平 Pod 自动扩缩容
- **Cluster Autoscaler**: EKS 集群节点自动扩缩容器
- **Stress Test**: 压力测试，通过增加负载来测试系统的扩展能力

## 需求

### 需求 1：环境信息展示

**用户故事：** 作为运维人员，我想查看 EKS 环境的完整信息，以便了解当前部署的详细状态

#### 验收标准

1. WHEN 用户访问应用首页，THE EKS_Info_App SHALL 显示当前 Pod 的基本信息（名称、命名空间、IP 地址、节点名称）
2. WHEN 用户访问应用首页，THE EKS_Info_App SHALL 显示 Kubernetes 集群信息（版本、API 服务器地址、服务账号信息）
3. WHEN 用户访问应用首页，THE EKS_Info_App SHALL 显示底层 EC2 实例信息（实例 ID、类型、可用区、私有 IP、公有 IP）
4. WHEN 用户访问应用首页，THE EKS_Info_App SHALL 显示系统架构信息（CPU 架构、处理器型号、是否为 ARM64 架构）
5. WHEN 用户访问应用首页，THE EKS_Info_App SHALL 显示网络架构信息（VPC ID、子网 ID、安全组、路由信息）
6. WHEN 用户访问应用首页，THE EKS_Info_App SHALL 显示所有环境变量和系统信息

### 需求 2：存储系统概览

**用户故事：** 作为运维人员，我想查看应用使用的所有存储系统，以便了解存储配置和访问方式

#### 验收标准

1. WHEN 用户访问存储概览页面，THE EKS_Info_App SHALL 显示所有挂载的存储卷信息（挂载路径、文件系统类型、容量、使用率）
2. WHEN 用户访问存储概览页面，THE EKS_Info_App SHALL 显示 EBS 卷的配置（PersistentVolume 名称、StorageClass、访问模式）
3. WHEN 用户访问存储概览页面，THE EKS_Info_App SHALL 显示 EFS 文件系统的配置（文件系统 ID、CSI Driver 信息）
4. WHEN 用户访问存储概览页面，THE EKS_Info_App SHALL 显示 S3 访问配置（存储桶名称、IAM 角色 ARN、权限策略）
5. WHEN 用户访问存储概览页面，THE EKS_Info_App SHALL 提供到各存储演示页面的导航链接

### 需求 3：EBS 块存储访问演示

**用户故事：** 作为开发人员，我想演示应用如何访问 EBS 卷，以便展示块存储的持久化特性

#### 验收标准

1. WHEN 用户访问 EBS 演示页面，THE EKS_Info_App SHALL 显示挂载的 EBS 卷信息（卷 ID、挂载路径、容量、使用率）
2. WHEN 用户在 EBS 演示页面写入数据，THE EKS_Info_App SHALL 将数据（时间戳、内容）保存到 EBS 卷的文件中
3. WHEN 用户在 EBS 演示页面读取数据，THE EKS_Info_App SHALL 从 EBS 卷读取并显示所有历史记录
4. WHEN 用户访问应用任意页面，THE EKS_Info_App SHALL 自动将访问日志追加到 EBS 卷的日志文件
5. WHEN Pod 重启后，THE EKS_Info_App SHALL 验证 EBS 卷中的数据仍然存在并可读取

### 需求 4：EFS 共享文件系统访问演示

**用户故事：** 作为开发人员，我想演示应用如何访问 EFS，以便展示多 Pod 共享文件系统的特性

#### 验收标准

1. WHEN 用户访问 EFS 演示页面，THE EKS_Info_App SHALL 显示挂载的 EFS 文件系统信息（文件系统 ID、挂载路径、访问点）
2. WHEN 用户在 EFS 演示页面写入数据，THE EKS_Info_App SHALL 将数据（时间戳、Pod 名称、内容）保存到 EFS 的文件中
3. WHEN 用户在 EFS 演示页面读取数据，THE EKS_Info_App SHALL 从 EFS 读取并显示所有 Pod 写入的记录
4. WHEN 多个 Pod 副本同时运行时，THE EKS_Info_App SHALL 展示所有 Pod 都能读写同一个 EFS 文件
5. WHEN 用户刷新页面时，THE EKS_Info_App SHALL 显示当前处理请求的 Pod 名称，证明不同 Pod 访问相同的 EFS 数据

### 需求 5：S3 对象存储访问演示

**用户故事：** 作为开发人员，我想演示应用如何访问 S3，以便展示对象存储的使用方式和 IRSA 权限机制

#### 验收标准

1. WHEN 用户访问 S3 演示页面，THE EKS_Info_App SHALL 显示配置的 S3 存储桶信息（桶名称、区域、访问方式）
2. WHEN 用户在 S3 演示页面上传数据，THE EKS_Info_App SHALL 将数据（时间戳、Pod 名称、内容）作为对象上传到 S3 存储桶
3. WHEN 用户在 S3 演示页面列出对象，THE EKS_Info_App SHALL 从 S3 读取并显示所有对象的列表（键名、大小、最后修改时间）
4. WHEN 用户在 S3 演示页面下载对象，THE EKS_Info_App SHALL 从 S3 读取对象内容并显示
5. WHEN 用户在 S3 演示页面删除对象，THE EKS_Info_App SHALL 从 S3 删除指定的对象
6. WHEN 应用访问 S3 时，THE EKS_Info_App SHALL 使用 IRSA 机制自动获取临时凭证，不使用硬编码密钥

### 需求 6：Kubernetes 资源信息

**用户故事：** 作为 Kubernetes 管理员，我想查看集群资源使用情况，以便监控和优化资源分配

#### 验收标准

1. WHEN 用户访问资源信息页面，THE EKS_Info_App SHALL 显示当前命名空间中所有 Pod 的列表（名称、状态、节点、重启次数）
2. WHEN 用户访问资源信息页面，THE EKS_Info_App SHALL 显示所有 Service 的信息（名称、类型、ClusterIP、端口）
3. WHEN 用户访问资源信息页面，THE EKS_Info_App SHALL 显示 Deployment 的配置信息（副本数、镜像版本、资源限制）
4. WHEN 用户访问资源信息页面，THE EKS_Info_App SHALL 显示节点资源使用情况（CPU 使用率、内存使用率、磁盘使用率）
5. WHEN 用户访问资源信息页面，THE EKS_Info_App SHALL 显示 PersistentVolume 和 PersistentVolumeClaim 的状态

### 需求 7：网络架构可视化

**用户故事：** 作为网络工程师，我想查看详细的网络配置，以便理解流量路径和安全策略

#### 验收标准

1. WHEN 用户访问网络信息页面，THE EKS_Info_App SHALL 显示 VPC 的详细信息（CIDR 块、DNS 设置、标签）
2. WHEN 用户访问网络信息页面，THE EKS_Info_App SHALL 显示所有子网的信息（子网 ID、CIDR、可用区、类型）
3. WHEN 用户访问网络信息页面，THE EKS_Info_App SHALL 显示安全组规则（入站规则、出站规则、端口范围）
4. WHEN 用户访问网络信息页面，THE EKS_Info_App SHALL 显示路由表配置（目标 CIDR、网关、NAT Gateway）
5. WHEN 用户访问网络信息页面，THE EKS_Info_App SHALL 显示 Load Balancer 的配置（DNS 名称、监听器、目标组）

### 需求 8：实时监控和健康检查

**用户故事：** 作为 SRE 工程师，我想监控应用的健康状态，以便及时发现和处理问题

#### 验收标准

1. THE EKS_Info_App SHALL 提供 /health 端点，返回 HTTP 200 状态码和健康状态信息
2. THE EKS_Info_App SHALL 提供 /ready 端点，检查所有存储系统的可用性
3. WHEN 应用启动时，THE EKS_Info_App SHALL 在 30 秒内完成初始化并响应健康检查
4. WHEN 存储系统不可用时，THE EKS_Info_App SHALL 在健康检查中报告具体的错误信息
5. THE EKS_Info_App SHALL 每分钟记录一次系统指标（CPU、内存、磁盘 IO、网络流量）到日志

### 需求 9：安全和权限管理

**用户故事：** 作为安全工程师，我想确保应用使用最小权限原则，以便降低安全风险

#### 验收标准

1. THE EKS_Info_App SHALL 使用 IRSA 机制获取 AWS 服务访问权限，不使用硬编码的访问密钥
2. THE EKS_Info_App SHALL 仅请求访问指定 S3 存储桶的权限
3. THE EKS_Info_App SHALL 使用 Kubernetes ServiceAccount 访问集群 API
4. WHEN 访问 AWS 服务失败时，THE EKS_Info_App SHALL 记录详细的权限错误信息
5. THE EKS_Info_App SHALL 不在日志中输出敏感信息（密钥、令牌、密码）

### 需求 10：用户界面和交互

**用户故事：** 作为最终用户，我想通过友好的界面查看信息，以便快速理解系统状态

#### 验收标准

1. THE EKS_Info_App SHALL 提供响应式 Web 界面，支持桌面和移动设备访问
2. THE EKS_Info_App SHALL 使用导航菜单组织不同功能模块（环境信息、存储、网络、监控）
3. WHEN 数据加载时，THE EKS_Info_App SHALL 显示加载指示器
4. WHEN 操作失败时，THE EKS_Info_App SHALL 显示清晰的错误消息
5. THE EKS_Info_App SHALL 使用颜色编码显示状态（绿色表示正常，黄色表示警告，红色表示错误）

### 需求 11：ARM 架构支持

**用户故事：** 作为架构师，我想应用运行在 ARM 架构上，以便利用 AWS Graviton 处理器的性能和成本优势

#### 验收标准

1. THE EKS_Info_App SHALL 构建为 ARM64 架构的 Docker 镜像
2. THE EKS_Info_App SHALL 在 ARM64 架构的 EKS 节点上正常运行
3. WHEN 应用启动时，THE EKS_Info_App SHALL 检测并显示当前运行的 CPU 架构
4. THE EKS_Info_App SHALL 使用支持 ARM64 架构的 Python 基础镜像
5. THE EKS_Info_App SHALL 确保所有依赖库都兼容 ARM64 架构

### 需求 12：CPU 压力测试和 Pod 自动扩展

**用户故事：** 作为性能工程师，我想执行 CPU 压力测试，以便演示 HPA 如何自动扩展 Pod 数量

#### 验收标准

1. WHEN 用户访问压力测试页面，THE EKS_Info_App SHALL 提供启动 CPU 压力测试的按钮
2. WHEN 用户启动 CPU 压力测试，THE EKS_Info_App SHALL 在后台线程中执行高 CPU 负载计算（持续 60 秒）
3. WHEN CPU 压力测试运行时，THE EKS_Info_App SHALL 实时显示当前 CPU 使用率百分比
4. WHEN CPU 使用率超过 HPA 阈值时，THE EKS_Info_App SHALL 显示 Pod 副本数的变化
5. WHEN 压力测试结束后，THE EKS_Info_App SHALL 显示扩展事件的时间线（触发时间、扩展前后的 Pod 数量）
6. THE EKS_Info_App SHALL 允许用户配置压力测试的持续时间和强度级别

### 需求 13：内存压力测试和 Pod 自动扩展

**用户故事：** 作为性能工程师，我想执行内存压力测试，以便演示基于内存使用率的 Pod 自动扩展

#### 验收标准

1. WHEN 用户访问压力测试页面，THE EKS_Info_App SHALL 提供启动内存压力测试的按钮
2. WHEN 用户启动内存压力测试，THE EKS_Info_App SHALL 分配大量内存对象（持续 60 秒）
3. WHEN 内存压力测试运行时，THE EKS_Info_App SHALL 实时显示当前内存使用量和使用率
4. WHEN 内存使用率超过 HPA 阈值时，THE EKS_Info_App SHALL 显示 Pod 副本数的变化
5. WHEN 压力测试结束后，THE EKS_Info_App SHALL 释放分配的内存并显示内存回收情况
6. THE EKS_Info_App SHALL 允许用户配置内存压力测试的目标内存大小

### 需求 14：集群节点自动扩展监控

**用户故事：** 作为集群管理员，我想监控节点自动扩展，以便了解 Cluster Autoscaler 如何添加新的 EC2 节点

#### 验收标准

1. WHEN 用户访问扩展监控页面，THE EKS_Info_App SHALL 显示当前集群的节点列表（节点名称、状态、CPU 和内存容量）
2. WHEN 用户访问扩展监控页面，THE EKS_Info_App SHALL 显示每个节点上运行的 Pod 数量和资源使用情况
3. WHEN Pod 数量增加导致资源不足时，THE EKS_Info_App SHALL 检测并显示 Pending 状态的 Pod
4. WHEN Cluster Autoscaler 添加新节点时，THE EKS_Info_App SHALL 显示节点扩展事件（时间、原因、新节点信息）
5. WHEN 负载降低后，THE EKS_Info_App SHALL 显示节点缩减事件（如果配置了缩减策略）
6. THE EKS_Info_App SHALL 提供刷新按钮以实时更新节点和 Pod 状态

### 需求 15：扩展历史和指标可视化

**用户故事：** 作为运维人员，我想查看扩展历史，以便分析自动扩展的效果和趋势

#### 验收标准

1. WHEN 用户访问扩展历史页面，THE EKS_Info_App SHALL 显示过去 24 小时的 Pod 数量变化图表
2. WHEN 用户访问扩展历史页面，THE EKS_Info_App SHALL 显示过去 24 小时的节点数量变化图表
3. WHEN 用户访问扩展历史页面，THE EKS_Info_App SHALL 显示所有扩展事件的列表（时间、类型、触发原因、结果）
4. WHEN 用户访问扩展历史页面，THE EKS_Info_App SHALL 显示平均扩展响应时间（从触发到完成）
5. WHEN 用户访问扩展历史页面，THE EKS_Info_App SHALL 显示资源使用率趋势（CPU 和内存）
