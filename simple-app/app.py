"""
简单 Python Web 应用
作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-17
更新时间: 2025-11-18
"""

from flask import Flask, jsonify
import socket
import platform
import os
import requests

app = Flask(__name__)

def get_aws_metadata(path):
    """获取 AWS 元数据（支持 IMDSv2）"""
    try:
        # 首先获取 IMDSv2 token
        token_url = 'http://169.254.169.254/latest/api/token'
        token_headers = {'X-aws-ec2-metadata-token-ttl-seconds': '21600'}
        
        token_response = requests.put(
            token_url,
            headers=token_headers,
            timeout=2
        )
        
        if token_response.status_code == 200:
            token = token_response.text.strip()
            
            # 使用 token 获取元数据
            metadata_url = f'http://169.254.169.254/latest/meta-data/{path}'
            metadata_headers = {'X-aws-ec2-metadata-token': token}
            
            metadata_response = requests.get(
                metadata_url,
                headers=metadata_headers,
                timeout=2
            )
            
            if metadata_response.status_code == 200:
                return metadata_response.text.strip()
    except Exception as e:
        print(f"获取 AWS 元数据失败 ({path}): {e}")
    
    return None

def get_eks_info():
    """获取 EKS 相关信息"""
    info = {
        'pod_name': os.getenv('POD_NAME', 'N/A'),
        'pod_namespace': os.getenv('POD_NAMESPACE', 'N/A'),
        'pod_ip': os.getenv('POD_IP', 'N/A'),
        'node_name': os.getenv('NODE_NAME', 'N/A'),
        'service_account': os.getenv('SERVICE_ACCOUNT', 'N/A'),
    }
    
    # 获取 AWS 元数据
    instance_id = get_aws_metadata('instance-id')
    info['instance_id'] = instance_id if instance_id else 'N/A'
    
    availability_zone = get_aws_metadata('placement/availability-zone')
    info['availability_zone'] = availability_zone if availability_zone else 'N/A'
    
    instance_type = get_aws_metadata('instance-type')
    info['instance_type'] = instance_type if instance_type else 'N/A'
    
    return info

@app.route('/')
def home():
    """主页"""
    eks_info = get_eks_info()
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RJ WebDemo - EKS on ARM64</title>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ 
                max-width: 1200px;
                margin: 0 auto;
                background: white; 
                padding: 40px; 
                border-radius: 15px; 
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }}
            h1 {{ 
                color: #2c3e50; 
                margin-bottom: 10px;
                font-size: 2.5em;
            }}
            .subtitle {{
                color: #7f8c8d;
                margin-bottom: 30px;
                font-size: 1.1em;
            }}
            .section {{
                margin: 25px 0;
            }}
            .section-title {{
                color: #34495e;
                font-size: 1.5em;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 3px solid #667eea;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }}
            .info-card {{ 
                background: #f8f9fa; 
                padding: 20px; 
                border-radius: 10px;
                border-left: 4px solid #667eea;
                transition: transform 0.2s;
            }}
            .info-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .info-label {{
                color: #7f8c8d;
                font-size: 0.9em;
                margin-bottom: 5px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .info-value {{
                color: #2c3e50;
                font-size: 1.2em;
                font-weight: 600;
                word-break: break-all;
            }}
            .success {{ 
                color: #27ae60; 
                font-weight: bold; 
            }}
            .badge {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: 600;
                margin: 5px 5px 5px 0;
            }}
            .badge-success {{
                background: #d4edda;
                color: #155724;
            }}
            .badge-info {{
                background: #d1ecf1;
                color: #0c5460;
            }}
            .status-banner {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                font-size: 1.3em;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
                text-align: center;
                color: #7f8c8d;
            }}
            .icon {{
                font-size: 1.5em;
                margin-right: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1><span class="icon">🚀</span>RJ WebDemo - EKS on ARM64</h1>
            <p class="subtitle">Amazon EKS 集群运行状态监控</p>
            
            <div class="status-banner">
                ✅ 应用运行正常 - ARM64 Graviton 架构
            </div>

            <div class="section">
                <h2 class="section-title">💻 系统信息</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <div class="info-label">主机名</div>
                        <div class="info-value">{hostname}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">架构</div>
                        <div class="info-value success">{architecture}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">操作系统</div>
                        <div class="info-value">{system} {release}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Python 版本</div>
                        <div class="info-value">{python_version}</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">☸️ Kubernetes 信息</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <div class="info-label">Pod 名称</div>
                        <div class="info-value">{pod_name}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">命名空间</div>
                        <div class="info-value">{pod_namespace}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Pod IP</div>
                        <div class="info-value">{pod_ip}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">节点名称</div>
                        <div class="info-value">{node_name}</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">☁️ AWS/EKS 信息</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <div class="info-label">实例 ID</div>
                        <div class="info-value">{instance_id}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">实例类型</div>
                        <div class="info-value">{instance_type}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">可用区</div>
                        <div class="info-value">{availability_zone}</div>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Service Account</div>
                        <div class="info-value">{service_account}</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">🏷️ 环境标签</h2>
                <div>
                    <span class="badge badge-success">环境: {environment}</span>
                    <span class="badge badge-info">版本: {app_version}</span>
                    <span class="badge badge-info">架构: ARM64</span>
                    <span class="badge badge-success">状态: 运行中</span>
                </div>
            </div>

            <div class="footer">
                <p>作者: RJ.Wang | 邮箱: wangrenjun@gmail.com</p>
                <p>最后更新: 2025-11-18</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_template.format(
        hostname=socket.gethostname(),
        architecture=platform.machine(),
        system=platform.system(),
        release=platform.release(),
        python_version=platform.python_version(),
        pod_name=eks_info['pod_name'],
        pod_namespace=eks_info['pod_namespace'],
        pod_ip=eks_info['pod_ip'],
        node_name=eks_info['node_name'],
        instance_id=eks_info['instance_id'],
        instance_type=eks_info['instance_type'],
        availability_zone=eks_info['availability_zone'],
        service_account=eks_info['service_account'],
        environment=os.getenv('ENVIRONMENT', 'sandbox'),
        app_version=os.getenv('APP_VERSION', '1.0')
    )

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'hostname': socket.gethostname(),
        'architecture': platform.machine()
    })

@app.route('/api/info')
def api_info():
    """API 端点 - 返回所有信息"""
    eks_info = get_eks_info()
    
    return jsonify({
        'status': 'ok',
        'system': {
            'hostname': socket.gethostname(),
            'architecture': platform.machine(),
            'system': platform.system(),
            'release': platform.release(),
            'python_version': platform.python_version()
        },
        'kubernetes': {
            'pod_name': eks_info['pod_name'],
            'pod_namespace': eks_info['pod_namespace'],
            'pod_ip': eks_info['pod_ip'],
            'node_name': eks_info['node_name'],
            'service_account': eks_info['service_account']
        },
        'aws': {
            'instance_id': eks_info['instance_id'],
            'instance_type': eks_info['instance_type'],
            'availability_zone': eks_info['availability_zone']
        },
        'environment': {
            'name': os.getenv('ENVIRONMENT', 'sandbox'),
            'version': os.getenv('APP_VERSION', '1.0')
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
