# 设计文档 - EKS Info WebApp 问题修复

**作者：** RJ.Wang  
**邮箱：** wangrenjun@gmail.com  
**创建时间：** 2025-11-15

## 概述

本文档描述如何修复已部署的 EKS Info WebApp 应用中发现的问题，包括 S3 配置错误、前端数据加载问题和其他潜在问题。

## 问题诊断

### 1. 已确认的问题

#### 1.1 S3 存储桶名称不匹配
- **现象**: 日志显示 "S3 存储桶不存在: eks-info-app-data"
- **原因**: Deployment 配置中使用 `eks-info-app-data`，但实际存储桶名称是 `rjtest-eks-cluster-202511171652-eks-info-app-data`
- **影响**: S3 相关功能无法正常工作
- **优先级**: 高

#### 1.2 前端数据可能未正确显示
- **现象**: 用户报告页面显示不符合预期
- **原因**: 需要验证前端 JavaScript 是否正确执行
- **影响**: 用户体验差
- **优先级**: 高

### 2. 后端 API 状态

✅ **正常工作的部分**:
- `/` 路由能正确返回 JSON 数据
- `/health` 健康检查正常
- `/ready` 就绪检查正常
- 环境信息收集功能正常
- EBS 和 EFS 存储检查正常

## 修复方案

### 方案 1：修复 S3 存储桶配置

#### 1.1 更新 Deployment 配置

修改 `k8s/deployment-no-storage.yaml` 中的环境变量：

```yaml
env:
- name: S3_BUCKET_NAME
  value: "rjtest-eks-cluster-202511171652-eks-info-app-data"  # 修改为正确的名称
```

#### 1.2 重新部署应用

```bash
kubectl apply -f k8s/deployment-no-storage.yaml
kubectl rollout restart deployment/eks-info-app -n rj-webdemo
```

### 方案 2：验证和修复前端问题

#### 2.1 检查项目

1. **验证 API 响应格式** - 确认 JSON 结构符合前端期望
2. **检查 JavaScript 错误** - 在浏览器控制台查看是否有错误
3. **验证 CORS 配置** - 确保跨域请求正常
4. **检查静态资源** - 确保所有 CSS/JS 文件正确加载

#### 2.2 可能的修复

如果发现问题，可能需要：
- 修复 JavaScript 代码中的错误
- 添加错误处理逻辑
- 优化数据加载流程

### 方案 3：添加静态资源路由

如果应用缺少 `/static/js/app.js`，需要：

#### 3.1 创建静态资源目录

```bash
mkdir -p eks-info-app/static/js
```

#### 3.2 创建 app.js 文件

创建一个空的或最小化的 `app.js` 文件，因为大部分 JavaScript 已经在模板中。

#### 3.3 配置 Flask 静态文件服务

确保 Flask 应用正确配置静态文件路径。

### 方案 4：优化错误处理

#### 4.1 减少重复日志

修改 S3Storage 类，只在初始化时检查一次存储桶：

```python
class S3Storage:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3')
        self._bucket_exists = None  # 缓存检查结果
        
    def _check_bucket_exists(self):
        if self._bucket_exists is None:
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                self._bucket_exists = True
            except Exception as e:
                logger.warning(f"S3 存储桶不存在: {self.bucket_name}")
                self._bucket_exists = False
        return self._bucket_exists
```

#### 4.2 改进前端错误显示

在前端添加更详细的错误信息：

```javascript
async function loadEnvironmentInfo() {
    try {
        const data = await apiRequest('/');
        if (data && data.environment) {
            displayEnvironmentInfo(data);
        } else {
            showError('数据格式不正确');
            console.error('API 返回的数据:', data);
        }
    } catch (error) {
        console.error('加载环境信息失败:', error);
        showError(`加载失败: ${error.message}`);
    }
}
```

## 实施步骤

### 步骤 1：修复 S3 配置（立即执行）

1. 更新 Deployment 配置文件
2. 应用新配置
3. 验证 Pod 重启后日志不再显示错误

### 步骤 2：验证前端功能（立即执行）

1. 在浏览器中打开应用
2. 打开开发者工具查看控制台
3. 检查是否有 JavaScript 错误
4. 验证网络请求是否成功
5. 确认数据是否正确显示

### 步骤 3：修复发现的问题（按需执行）

根据验证结果，修复发现的具体问题。

### 步骤 4：全面测试（最后执行）

1. 测试所有页面功能
2. 验证存储操作
3. 测试压力测试功能
4. 检查扩展监控功能

## 验证标准

### 1. S3 配置验证

```bash
# 检查 Pod 日志，不应再有 "S3 存储桶不存在" 错误
kubectl logs -n rj-webdemo -l app=eks-info-app --tail=50 | grep "S3 存储桶"

# 测试 S3 功能
curl -s "http://<ALB-URL>/s3" | grep -i error
```

### 2. 前端功能验证

在浏览器中：
1. 访问首页，确认所有信息卡片都显示
2. 检查浏览器控制台，确认没有 JavaScript 错误
3. 验证网络请求都返回 200 状态码
4. 确认数据正确渲染

### 3. 完整功能验证

测试所有页面：
- ✅ 首页 - 环境信息
- ✅ 存储概览
- ✅ EBS 演示
- ✅ EFS 演示
- ✅ S3 演示
- ✅ 网络信息
- ✅ 资源信息
- ✅ 压力测试
- ✅ 扩展监控

## 回滚计划

如果修复导致问题：

```bash
# 回滚到之前的配置
kubectl rollout undo deployment/eks-info-app -n rj-webdemo

# 或者重新应用原始配置
kubectl apply -f k8s/deployment-no-storage.yaml.backup
```

## 监控和日志

修复后持续监控：

```bash
# 监控 Pod 状态
kubectl get pods -n rj-webdemo -w

# 查看实时日志
kubectl logs -n rj-webdemo -l app=eks-info-app -f

# 检查 HPA 状态
kubectl get hpa -n rj-webdemo -w
```

## 预期结果

修复完成后：
1. ✅ S3 日志错误消失
2. ✅ 所有页面正确显示数据
3. ✅ 用户体验流畅
4. ✅ 所有功能正常工作
