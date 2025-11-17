---
inclusion: always
---

# Shell 脚本最佳实践

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-17  
**更新时间**: 2025-11-17  
**用途**: 规范项目中所有 Shell 脚本的编写和执行方式

---

## 核心原则

### 1. 使用绝对路径

**要求**: 所有 Shell 脚本中的文件和目录引用必须使用绝对路径。

**原因**:
- 防止因当前工作目录不同导致命令执行失败
- 提高脚本的可移植性和可靠性
- 避免相对路径引起的混淆和错误

---

## 路径处理规范

### 获取脚本所在目录

**标准模式**:
```bash
#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 获取项目根目录
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 定义其他常用目录
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
K8S_DIR="${PROJECT_ROOT}/k8s"
APP_DIR="${PROJECT_ROOT}/simple-app"
```

**说明**:
- `SCRIPT_DIR`: 脚本文件所在的目录
- `PROJECT_ROOT`: 项目根目录
- 使用 `$(cd ... && pwd)` 确保获取绝对路径

---

## 文件操作规范

### 读取文件

❌ **错误示例**:
```bash
# 相对路径 - 依赖当前工作目录
cat config.yaml
source ./env.sh
```

✅ **正确示例**:
```bash
# 绝对路径 - 不依赖当前工作目录
cat "${PROJECT_ROOT}/config.yaml"
source "${SCRIPT_DIR}/env.sh"
```

### 写入文件

❌ **错误示例**:
```bash
echo "data" > output.txt
cat > file.txt << EOF
content
EOF
```

✅ **正确示例**:
```bash
echo "data" > "${PROJECT_ROOT}/output.txt"
cat > "${PROJECT_ROOT}/file.txt" << EOF
content
EOF
```

### 检查文件存在

❌ **错误示例**:
```bash
if [ -f "config.yaml" ]; then
    echo "File exists"
fi
```

✅ **正确示例**:
```bash
if [ -f "${PROJECT_ROOT}/config.yaml" ]; then
    echo "File exists"
fi
```

---

## 目录切换规范

### 临时切换目录

❌ **错误示例**:
```bash
cd terraform
terraform apply
cd ..
```

✅ **正确示例 1** - 使用绝对路径:
```bash
cd "${TERRAFORM_DIR}" || {
    echo "错误: 无法进入 Terraform 目录"
    exit 1
}
terraform apply
cd "${PROJECT_ROOT}" || exit 1
```

✅ **正确示例 2** - 使用子 shell:
```bash
(
    cd "${TERRAFORM_DIR}" || exit 1
    terraform apply
)
# 自动返回原目录
```

✅ **正确示例 3** - 使用 pushd/popd:
```bash
pushd "${TERRAFORM_DIR}" > /dev/null || exit 1
terraform apply
popd > /dev/null || exit 1
```

### 目录切换错误处理

**必须包含错误处理**:
```bash
cd "${TERRAFORM_DIR}" || {
    echo "错误: 无法进入目录 ${TERRAFORM_DIR}"
    echo "请检查目录是否存在"
    exit 1
}
```

---

## 命令执行规范

### 执行其他脚本

❌ **错误示例**:
```bash
./build.sh
source env.sh
```

✅ **正确示例**:
```bash
"${APP_DIR}/build.sh"
source "${SCRIPT_DIR}/env.sh"
```

### 执行系统命令

❌ **错误示例**:
```bash
# 假设文件在当前目录
kubectl apply -f deployment.yaml
terraform -chdir=terraform apply
```

✅ **正确示例**:
```bash
# 使用绝对路径
kubectl apply -f "${K8S_DIR}/deployment.yaml"

# 或切换到目标目录
cd "${TERRAFORM_DIR}" || exit 1
terraform apply
cd "${PROJECT_ROOT}" || exit 1
```

---

## 变量定义规范

### 路径变量

**在脚本开头定义所有路径变量**:
```bash
#!/bin/bash

# 脚本元信息
# 作者: RJ.Wang
# 创建时间: 2025-11-17

set -e

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
K8S_DIR="${PROJECT_ROOT}/k8s"
APP_DIR="${PROJECT_ROOT}/simple-app"
SCRIPTS_DIR="${PROJECT_ROOT}/scripts"
LOG_FILE="${SCRIPTS_DIR}/deployment.log"

# 配置变量
IMAGE_NAME="rjwang/rj-py-webdemo"
VERSION="1.0"

# 脚本主逻辑
main() {
    # 使用定义的路径变量
    cd "${TERRAFORM_DIR}" || exit 1
    terraform apply
    cd "${PROJECT_ROOT}" || exit 1
}

main "$@"
```

---

## 日志文件规范

### 日志文件路径

❌ **错误示例**:
```bash
echo "log" >> deployment.log
```

✅ **正确示例**:
```bash
LOG_FILE="${SCRIPTS_DIR}/deployment.log"
echo "log" >> "${LOG_FILE}"
```

### 日志函数

```bash
# 日志文件路径
LOG_FILE="${SCRIPTS_DIR}/deployment.log"

# 日志函数
log_info() {
    echo "[INFO] $1" | tee -a "${LOG_FILE}"
}

log_error() {
    echo "[ERROR] $1" | tee -a "${LOG_FILE}"
}

# 使用
log_info "开始部署..."
log_error "部署失败"
```

---

## 配置文件规范

### 读取配置文件

❌ **错误示例**:
```bash
source config.sh
. ./env.sh
```

✅ **正确示例**:
```bash
# 检查文件存在后再加载
CONFIG_FILE="${PROJECT_ROOT}/config.sh"
if [ -f "${CONFIG_FILE}" ]; then
    source "${CONFIG_FILE}"
else
    echo "错误: 配置文件不存在: ${CONFIG_FILE}"
    exit 1
fi
```

---

## 临时文件规范

### 创建临时文件

❌ **错误示例**:
```bash
echo "data" > temp.txt
rm temp.txt
```

✅ **正确示例**:
```bash
# 使用项目临时目录
TEMP_DIR="${PROJECT_ROOT}/.tmp"
mkdir -p "${TEMP_DIR}"

TEMP_FILE="${TEMP_DIR}/temp_$(date +%s).txt"
echo "data" > "${TEMP_FILE}"

# 清理
rm -f "${TEMP_FILE}"
```

---

## 实际案例

### 案例 1: 部署脚本

```bash
#!/bin/bash
#
# EKS 部署脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com

set -e

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
LOG_FILE="${SCRIPT_DIR}/deployment.log"

# 日志函数
log_info() {
    echo "[INFO] $1" | tee -a "${LOG_FILE}"
}

# 初始化 Terraform
init_terraform() {
    log_info "初始化 Terraform..."
    
    cd "${TERRAFORM_DIR}" || {
        log_error "无法进入 Terraform 目录: ${TERRAFORM_DIR}"
        return 1
    }
    
    terraform init
    
    cd "${PROJECT_ROOT}" || return 1
    log_info "Terraform 初始化完成"
}

# 主函数
main() {
    log_info "开始部署..."
    init_terraform || exit 1
    log_info "部署完成"
}

main "$@"
```

### 案例 2: 构建脚本

```bash
#!/bin/bash
#
# Docker 镜像构建脚本
# 作者: RJ.Wang

set -e

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOCKERFILE="${SCRIPT_DIR}/Dockerfile"
BUILD_CONTEXT="${SCRIPT_DIR}"

# 配置
IMAGE_NAME="rjwang/rj-py-webdemo"
VERSION="1.0"

# 构建镜像
build_image() {
    echo "构建镜像..."
    
    # 检查 Dockerfile 存在
    if [ ! -f "${DOCKERFILE}" ]; then
        echo "错误: Dockerfile 不存在: ${DOCKERFILE}"
        exit 1
    fi
    
    # 构建
    docker buildx build \
        --platform linux/arm64 \
        --tag "${IMAGE_NAME}:${VERSION}" \
        --file "${DOCKERFILE}" \
        "${BUILD_CONTEXT}"
    
    echo "构建完成"
}

build_image
```

### 案例 3: 清理脚本

```bash
#!/bin/bash
#
# 资源清理脚本
# 作者: RJ.Wang

set -e

# 路径定义
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
K8S_MANIFESTS="${PROJECT_ROOT}/k8s-manifests.yaml"

# 清理 Kubernetes 资源
cleanup_k8s() {
    echo "清理 Kubernetes 资源..."
    
    if [ -f "${K8S_MANIFESTS}" ]; then
        kubectl delete -f "${K8S_MANIFESTS}" || true
        rm -f "${K8S_MANIFESTS}"
    fi
}

# 清理 Terraform 资源
cleanup_terraform() {
    echo "清理 Terraform 资源..."
    
    cd "${TERRAFORM_DIR}" || {
        echo "错误: 无法进入 Terraform 目录"
        exit 1
    }
    
    terraform destroy -auto-approve
    
    cd "${PROJECT_ROOT}" || exit 1
}

# 主函数
main() {
    cleanup_k8s
    cleanup_terraform
    echo "清理完成"
}

main
```

---

## 检查清单

编写 Shell 脚本时，请确认：

### 路径处理
- [ ] 定义了 `SCRIPT_DIR` 变量
- [ ] 定义了 `PROJECT_ROOT` 变量
- [ ] 所有文件操作使用绝对路径
- [ ] 所有目录切换使用绝对路径
- [ ] 目录切换包含错误处理

### 变量定义
- [ ] 路径变量在脚本开头定义
- [ ] 使用有意义的变量名
- [ ] 变量使用双引号包裹

### 错误处理
- [ ] 使用 `set -e` 或手动错误处理
- [ ] 目录切换包含 `|| exit 1`
- [ ] 关键操作包含错误提示

### 代码风格
- [ ] 包含脚本元信息（作者、时间）
- [ ] 使用函数组织代码
- [ ] 添加必要的注释

---

## 常见错误

### 错误 1: 相对路径依赖

❌ **问题**:
```bash
cd scripts
./deploy.sh  # 脚本内使用相对路径
```

如果在不同目录执行，会失败。

✅ **解决**:
```bash
"${PROJECT_ROOT}/scripts/deploy.sh"
```

### 错误 2: 未检查目录切换

❌ **问题**:
```bash
cd terraform
terraform apply
```

如果目录不存在，会在错误的位置执行命令。

✅ **解决**:
```bash
cd "${TERRAFORM_DIR}" || {
    echo "错误: 目录不存在"
    exit 1
}
terraform apply
```

### 错误 3: 硬编码路径

❌ **问题**:
```bash
cd /Users/rj/project/terraform
```

在其他机器上无法运行。

✅ **解决**:
```bash
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
cd "${TERRAFORM_DIR}" || exit 1
```

---

## 工具推荐

### ShellCheck

使用 ShellCheck 检查脚本质量：

```bash
# 安装
brew install shellcheck  # macOS
apt-get install shellcheck  # Ubuntu

# 检查脚本
shellcheck script.sh
```

### 常见 ShellCheck 警告

```bash
# SC2164: 使用 cd || exit 防止目录切换失败
cd "${DIR}" || exit 1

# SC2086: 变量使用双引号
echo "${VAR}"

# SC2155: 分离声明和赋值
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
```

---

## 总结

**核心要点**:
1. ✅ 始终使用绝对路径
2. ✅ 在脚本开头定义路径变量
3. ✅ 目录切换包含错误处理
4. ✅ 使用 ShellCheck 检查脚本
5. ✅ 遵循项目编码规范

**记住这个公式**:
```
可靠的脚本 = 绝对路径 + 错误处理 + 清晰的变量定义
```

---

**最后更新**: 2025-11-17  
**适用范围**: 项目中所有 Shell 脚本
