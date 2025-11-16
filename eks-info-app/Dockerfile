# EKS Info WebApp Dockerfile
# 
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-14
#
# 构建 ARM64 架构的 Docker 镜像，用于部署到 EKS Graviton 节点

FROM --platform=linux/arm64 python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
# gcc: 编译某些 Python 包需要
# 使用阿里云镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
# --no-cache-dir: 不缓存下载的包，减小镜像大小
# 使用阿里云 PyPI 镜像源加速
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录（用于 EBS 和 EFS 挂载）
RUN mkdir -p /data/ebs /data/efs

# 创建非 root 用户运行应用（安全最佳实践）
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /data

# 切换到非 root 用户
USER appuser

# 暴露应用端口
EXPOSE 5000

# 配置健康检查
# 每 30 秒检查一次，超时 3 秒，启动后 40 秒开始检查，失败 3 次认为不健康
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PORT=5000

# 使用 gunicorn 启动应用（生产环境推荐）
# --bind 0.0.0.0:5000: 监听所有网络接口
# --workers 4: 4 个工作进程
# --timeout 120: 请求超时时间 120 秒
# --access-logfile -: 访问日志输出到 stdout
# --error-logfile -: 错误日志输出到 stderr
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
