import requests
try:
    # 测试 IMDSv2
    token_response = requests.put(
        'http://169.254.169.254/latest/api/token',
        headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'},
        timeout=2
    )
    print(f'Token 请求状态码: {token_response.status_code}')
    if token_response.status_code == 200:
        token = token_response.text.strip()
        print(f'Token: {token[:20]}...')
        
        # 获取实例 ID
        metadata_response = requests.get(
            'http://169.254.169.254/latest/meta-data/instance-id',
            headers={'X-aws-ec2-metadata-token': token},
            timeout=2
        )
        print(f'元数据请求状态码: {metadata_response.status_code}')
        if metadata_response.status_code == 200:
            print(f'实例 ID: {metadata_response.text}')
except Exception as e:
    print(f'错误: {e}')
