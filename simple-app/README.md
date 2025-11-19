# 简单 Python Web 应用

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-17  
**更新时间**: 2025-11-18

---

## 项目说明

这是一个简单的 Python Flask Web 应用，用于部署到 EKS 集群进行测试。

## 重要文档

- [故障排查指南](./TROUBLESHOOTING.md) - 常见问题和解决方案
- [部署检查清单](./DEPLOYMENT_CHECKLIST.md) - 部署前后的检查步骤

---

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install flask gunicorn

# 运行应用
python app.py
```

### Docker 构建

```bash
# 构建 ARM64 镜像（用于 EKS Graviton 节点）
docker buildx build \
  --platform linux/arm64 \
  -t rjwang/rj-py-webdemo:latest \
  --push \
  .
```

### 部署到 EKS

```bash
# 更新部署
kubectl set image deployment/rj-py-webdemo \
  rj-py-webdemo=rjwang/rj-py-webdemo:latest \
  -n rj-webdemo

# 验证部署
kubectl get pods -n rj-webdemo
```

---

## 架构要求

⚠️ **重要**: 此应用必须构建为 **ARM64** 架构镜像，以匹配 EKS Graviton 节点。

如果遇到 `exec format error` 错误，请参考 [故障排查指南](./TROUBLESHOOTING.md)。

---

## 文件结构

```
simple-app/
├── app.py                      # Flask 应用主文件
├── Dockerfile                  # Docker 构建文件（ARM64）
├── README.md                   # 项目说明
├── TROUBLESHOOTING.md          # 故障排查指南
└── DEPLOYMENT_CHECKLIST.md     # 部署检查清单
```

---

## 联系方式

- **作者**: RJ.Wang
- **邮箱**: wangrenjun@gmail.com

---

**最后更新**: 2025-11-18
