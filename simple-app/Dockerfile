# 简单 Python Web 应用 - ARM64 架构
# 
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-17
#
# ⚠️ 重要: 必须构建 ARM64 架构镜像用于 EKS Graviton 节点

FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /app

# 安装系统依赖和 Python 包
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir flask gunicorn requests

# 复制应用代码
COPY app.py .

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:80/')" || exit 1

# 启动应用
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "2", "--timeout", "60", "app:app"]
