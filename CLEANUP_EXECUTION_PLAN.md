# 项目清理执行计划

**作者：** RJ.Wang  
**邮箱：** wangrenjun@gmail.com  
**日期：** 2025-11-15

## 🎯 清理目标

1. 删除临时和调试文件
2. 合并重复的文档
3. 优化项目结构
4. 保持代码简洁专业

## 📝 执行步骤

### 阶段 1：安全删除临时文件

#### 1.1 删除日志文件
```bash
# 根目录
rm deployment.log
rm terraform-apply.log
rm terraform-apply-final.log
rm tfplan
```

#### 1.2 删除系统文件
```bash
# macOS 系统文件
find . -name ".DS_Store" -delete
```

#### 1.3 删除已完成的修复脚本
```bash
rm fix_all_routes.sh
rm fix_routes_accept_header.py
rm fix_routes_indentation.py
rm fix_routes_logic.py
rm fix_routes_properly.py
rm redeploy_fixed_app.sh
```

### 阶段 2：文档整合

#### 2.1 合并 Bug 修复文档
**目标文件：** `BUGFIX_REPORT.md`

**合并来源：**
- `BUGFIX_SUMMARY.md`
- `BUGFIX_VERIFICATION_REPORT.md`
- `BUGFIX_FINAL_REPORT.md`

**删除原文件：**
```bash
rm BUGFIX_SUMMARY.md
rm BUGFIX_VERIFICATION_REPORT.md
rm BUGFIX_FINAL_REPORT.md
```

#### 2.2 合并项目总结文档
**目标文件：** `PROJECT_SUMMARY.md`

**合并来源：**
- `TASK_5_SUMMARY.md`
- `TASK_7_SUMMARY.md`
- `TASK_8_SUMMARY.md`
- `TASK_19_3_VERIFICATION.md`
- `TASK_19_4_VERIFICATION.md`
- `PROJECT_COMPLETION_SUMMARY.md`

**删除原文件：**
```bash
rm TASK_5_SUMMARY.md
rm TASK_7_SUMMARY.md
rm TASK_8_SUMMARY.md
rm TASK_19_3_VERIFICATION.md
rm TASK_19_4_VERIFICATION.md
rm PROJECT_COMPLETION_SUMMARY.md
```

#### 2.3 合并部署文档
**目标文件：** `DEPLOYMENT.md`

**合并来源：**
- `DEPLOYMENT_STATUS.md`
- `TERRAFORM_DEPLOYMENT.md`

**删除原文件：**
```bash
rm DEPLOYMENT_STATUS.md
rm TERRAFORM_DEPLOYMENT.md
```

#### 2.4 合并 API 文档（eks-info-app 目录）
**目标文件：** `eks-info-app/API_DOCUMENTATION.md`

**合并来源：**
- `eks-info-app/EBS_API_USAGE.md`
- `eks-info-app/EFS_API_USAGE.md`
- `eks-info-app/S3_API_USAGE.md`
- `eks-info-app/NETWORK_API_USAGE.md`
- `eks-info-app/RESOURCES_API_USAGE.md`
- `eks-info-app/SCALING_API_USAGE.md`
- `eks-info-app/STORAGE_API_USAGE.md`
- `eks-info-app/STRESS_API_USAGE.md`

**删除原文件：**
```bash
cd eks-info-app
rm EBS_API_USAGE.md EFS_API_USAGE.md S3_API_USAGE.md
rm NETWORK_API_USAGE.md RESOURCES_API_USAGE.md
rm SCALING_API_USAGE.md STORAGE_API_USAGE.md STRESS_API_USAGE.md
cd ..
```

#### 2.5 删除 eks-info-app 中的任务文档
```bash
cd eks-info-app
rm TASK_9_10_SUMMARY.md
rm TASK_12_SUMMARY.md
cd ..
```

### 阶段 3：结构优化

#### 3.1 创建新目录结构
```bash
# 创建 terraform 目录
mkdir -p terraform

# 创建 scripts 目录
mkdir -p scripts

# 创建测试目录
mkdir -p eks-info-app/tests
```

#### 3.2 移动 Terraform 文件
```bash
mv main.tf terraform/
mv variables.tf terraform/
mv outputs.tf terraform/
mv versions.tf terraform/
mv app.tf terraform/
mv terraform.tfvars terraform/
mv .terraform.lock.hcl terraform/
```

#### 3.3 移动脚本文件
```bash
mv build.sh scripts/
mv deploy.sh scripts/
mv test_all_pages.sh scripts/
mv verify_environment_info.sh scripts/
mv verify_frontend.sh scripts/
mv get-alb-hostname.sh scripts/
```

#### 3.4 移动测试文件
```bash
cd eks-info-app
mv test_*.py tests/
cd ..
```

#### 3.5 整理 k8s 目录
```bash
cd k8s
mkdir -p storage
mv storageclass-*.yaml storage/
mv pvc-*.yaml storage/
cd ..
```

### 阶段 4：清理 eks-info-app

#### 4.1 删除重复的构建脚本
```bash
cd eks-info-app
# 保留 build.sh，删除 build-docker.sh
rm build-docker.sh
cd ..
```

#### 4.2 删除测试脚本（如果已移动测试文件）
```bash
cd eks-info-app
rm test.sh
rm test-docker.sh
cd ..
```

### 阶段 5：更新配置文件

#### 5.1 更新 .gitignore
添加以下内容：
```
# Logs
*.log
deployment.log
terraform-apply*.log

# Terraform
*.tfstate
*.tfstate.*
.terraform/
tfplan
.terraform.lock.hcl

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.venv/
venv/
*.egg-info/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.bak
*.swp
*~
```

#### 5.2 更新主 README.md
更新项目结构说明，反映新的目录结构。

### 阶段 6：验证和测试

#### 6.1 验证文件引用
```bash
# 检查脚本中的路径引用
grep -r "main.tf" scripts/
grep -r "test_" scripts/
```

#### 6.2 测试构建和部署
```bash
# 测试 Terraform
cd terraform
terraform init
terraform validate
cd ..

# 测试应用构建
cd eks-info-app
docker build -t test .
cd ..
```

## 📊 清理统计

### 预计删除的文件数量

| 类别 | 数量 |
|------|------|
| 临时日志文件 | 4 |
| 系统文件 | 3+ |
| 修复脚本 | 6 |
| Bug 修复文档 | 3 |
| 任务总结文档 | 6 |
| 部署文档 | 2 |
| API 文档 | 8 |
| 其他临时文件 | 5 |
| **总计** | **37+** |

### 预计创建的文件

| 文件 | 说明 |
|------|------|
| `BUGFIX_REPORT.md` | 合并的 Bug 修复报告 |
| `PROJECT_SUMMARY.md` | 合并的项目总结 |
| `DEPLOYMENT.md` | 合并的部署文档 |
| `eks-info-app/API_DOCUMENTATION.md` | 合并的 API 文档 |

### 目录结构变化

| 操作 | 目录 |
|------|------|
| 新建 | `terraform/` |
| 新建 | `scripts/` |
| 新建 | `eks-info-app/tests/` |
| 新建 | `k8s/storage/` |

## ⚠️ 重要提醒

1. **执行前备份**
   ```bash
   # 创建备份
   tar -czf project-backup-$(date +%Y%m%d).tar.gz .
   ```

2. **分步执行**
   - 不要一次性执行所有命令
   - 每个阶段完成后验证
   - 确保没有破坏依赖关系

3. **Git 提交**
   ```bash
   # 每个阶段完成后提交
   git add .
   git commit -m "清理阶段 X: [描述]"
   ```

4. **测试验证**
   - 每个阶段后测试应用
   - 确保部署脚本仍然工作
   - 验证文档链接

## ✅ 完成检查清单

- [ ] 阶段 1：删除临时文件
- [ ] 阶段 2：合并文档
- [ ] 阶段 3：优化结构
- [ ] 阶段 4：清理 eks-info-app
- [ ] 阶段 5：更新配置
- [ ] 阶段 6：验证测试
- [ ] 更新 README.md
- [ ] Git 提交
- [ ] 最终验证

## 🎉 预期结果

清理后的项目将：
- ✅ 结构清晰，易于维护
- ✅ 文档精简，内容准确
- ✅ 无冗余文件
- ✅ 符合最佳实践
- ✅ 便于部署和扩展
