# 🔐 GitHub SSH 密钥配置指南

## 🚨 问题描述
遇到 `Permission denied (publickey)` 错误，需要将 SSH 公钥添加到 GitHub 账户。

## 🔑 您的 SSH 公钥
请复制以下公钥内容：

```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDhZg3PCuCbe6FcaZjG8qjLfcDkdUfFbuVDrTCFgDWssQliViv19scn6WqMgDOqyhF+zlXsxRiqUhMKoehWZOZUBvtaCaSnNmP1RglkIjhLy2VVMfO9dFVyIUvaHFgE6TJcZFmz3hSFhqLcG2VEhTU7JAZIDuHaTbB+QTTtwlBGmbi0PvxCCdLDzxbR3zdofXEYPlznX2mBPFsDbqkEuTL25g7KO+f/iahG2DokG8ncJ9JJUMcE6KUqQhcsJxbpzM01viIylFZiTFiImamuD3agtivo+EgfPv0YIcmbNulL0ZMY0tBdyfQCR1BRJtlT822fnQ5xnqJK8M/L9WDehBa4vWlZRyxEtPlqpq7nmwWUxMJ+loHLNj1bf0P4KPKFSJtGQOh8ou0rjQQUZv5tA0ELjGnXzXe9GPiROnvV9dZ+qY1/ZFIgH9kvju8yMzvOBLniXTetgQ+znZD3+jSSmDLWALXNgjQekXB5LhB03nlmXKOccByu7UGC2nioxwOUEq8= 18616945668@139.com
```

## 📋 添加 SSH 密钥到 GitHub 的步骤

### 步骤 1: 访问 GitHub SSH 设置
1. 登录 GitHub: https://github.com
2. 点击右上角头像 → Settings
3. 左侧菜单点击 "SSH and GPG keys"
4. 点击 "New SSH key" 按钮

### 步骤 2: 添加 SSH 密钥
1. **Title**: 输入描述性名称，如 "MacBook Pro - RJ.Wang"
2. **Key type**: 选择 "Authentication Key"
3. **Key**: 粘贴上面的公钥内容（整行复制）
4. 点击 "Add SSH key"
5. 输入 GitHub 密码确认

### 步骤 3: 验证连接
添加密钥后，在终端运行：
```bash
ssh -T git@github.com
```

成功的话会看到：
```
Hi rjwang1982! You've successfully authenticated, but GitHub does not provide shell access.
```

## 🔄 方案 2: 使用 HTTPS 替代 SSH（临时方案）

如果 SSH 配置有问题，可以临时使用 HTTPS：

```bash
cd /Users/rj/SyncSpace/WorkSpace/GitHub/terraform-eks-webdemo

# 移除现有的 SSH remote
git remote remove origin

# 添加 HTTPS remote
git remote add origin https://github.com/rjwang1982/terraform-eks-webdemo.git

# 推送代码
git push -u origin main
```

使用 HTTPS 时，GitHub 会要求输入用户名和个人访问令牌（不是密码）。

## 🎫 创建 GitHub 个人访问令牌（如果使用 HTTPS）

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 点击 "Generate new token (classic)"
3. 设置过期时间和权限（至少需要 `repo` 权限）
4. 复制生成的令牌（只显示一次）
5. 推送时使用令牌作为密码

## 🔧 故障排除

### 检查 SSH 代理
```bash
# 检查 SSH 代理是否运行
ssh-add -l

# 如果没有密钥，添加密钥
ssh-add ~/.ssh/id_rsa_18616945668@139.com
```

### 检查 SSH 配置
确认 `~/.ssh/config` 中的 GitHub 配置正确：
```
Host github.com
HostName github.com
PreferredAuthentications publickey
IdentityFile ~/.ssh/id_rsa_18616945668@139.com
```

### 测试特定密钥
```bash
ssh -i ~/.ssh/id_rsa_18616945668@139.com -T git@github.com
```

## ✅ 推荐流程

1. **首选**: 添加 SSH 密钥到 GitHub（更安全，长期使用）
2. **备选**: 使用 HTTPS + 个人访问令牌（临时方案）

完成 SSH 配置后，就可以正常推送代码到 GitHub 了！

---

**创建时间**: 2025-08-22  
**作者**: RJ.Wang (wangrenjun@gmail.com)
