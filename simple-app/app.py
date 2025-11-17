"""
简单 Python Web 应用
作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-17
"""

from flask import Flask, jsonify
import socket
import platform
import os

app = Flask(__name__)

@app.route('/')
def home():
    """主页"""
    return f"""
    <html>
    <head>
        <title>RJ WebDemo - ARM64</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; }}
            .info {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .success {{ color: #27ae60; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 RJ WebDemo - ARM64 版本</h1>
            <div class="info">
                <p><strong>主机名:</strong> {socket.gethostname()}</p>
                <p><strong>架构:</strong> <span class="success">{platform.machine()}</span></p>
                <p><strong>系统:</strong> {platform.system()} {platform.release()}</p>
                <p><strong>Python:</strong> {platform.python_version()}</p>
                <p><strong>环境:</strong> {os.getenv('ENVIRONMENT', 'sandbox')}</p>
            </div>
            <p>✅ 应用运行正常 - ARM64 架构</p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'hostname': socket.gethostname(),
        'architecture': platform.machine()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
