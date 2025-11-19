# 项目清理需求文档

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-16  
**项目**: EKS Info WebApp - 项目清理与优化

---

## 简介

本项目已完成所有功能开发和测试，现需要进行全面的清理和优化，使项目结构更加专业、简洁、易于维护和部署。

## 术语表

- **System**: 项目清理系统
- **Temporary File**: 临时文件，包括日志、缓存、备份等开发过程中产生的文件
- **Redundant Document**: 冗余文档，指内容重复或过时的文档文件
- **Core File**: 核心文件，指项目运行和部署必需的文件
- **Project Structure**: 项目结构，指文件和目录的组织方式
- **Git Repository**: Git 仓库，指版本控制系统管理的项目

---

## 需求

### 需求 1: 临时文件清理

**用户故事**: 作为项目维护者，我希望删除所有开发过程中产生的临时文件，以保持项目目录整洁。

#### 验收标准

1. WHEN 执行清理操作时，THE System SHALL 删除所有日志文件（*.log, deployment.log, terraform-apply*.log）
2. WHEN 执行清理操作时，THE System SHALL 删除所有 Terraform 临时文件（tfplan, tfplan.*）
3. WHEN 执行清理操作时，THE System SHALL 删除所有系统生成文件（.DS_Store, Thumbs.db）
4. WHEN 执行清理操作时，THE System SHALL 删除所有 Python 缓存目录（__pycache__, .pytest_cache）
5. WHEN 执行清理操作时，THE System SHALL 保留核心配置文件（terraform.tfstate, .terraform.lock.hcl）

### 需求 2: 过时脚本清理

**用户故事**: 作为项目维护者，我希望删除已完成任务的临时脚本，只保留必要的工具脚本。

#### 验收标准

1. WHEN 执行清理操作时，THE System SHALL 删除所有修复脚本（fix_*.sh, fix_*.py, redeploy_*.sh）
2. WHEN 执行清理操作时，THE System SHALL 删除重复的部署脚本（final_deploy.sh）
3. WHEN 执行清理操作时，THE System SHALL 保留核心脚本（build.sh, deploy.sh）
4. WHEN 执行清理操作时，THE System SHALL 将验证脚本移动到 scripts 目录
5. WHEN 执行清理操作时，THE System SHALL 删除临时测试部署文件（test-deployment.yaml）

### 需求 3: 文档整合

**用户故事**: 作为项目维护者，我希望合并重复的文档，创建统一的文档结构。

#### 验收标准

1. WHEN 整合文档时，THE System SHALL 合并所有 Bug 修复文档为单一文件 BUGFIX_REPORT.md
2. WHEN 整合文档时，THE System SHALL 合并所有任务总结文档为单一文件 PROJECT_SUMMARY.md
3. WHEN 整合文档时，THE System SHALL 合并所有部署文档为单一文件 DEPLOYMENT.md
4. WHEN 整合文档时，THE System SHALL 删除原始的分散文档文件
5. WHEN 整合文档时，THE System SHALL 保留主 README.md 和 TROUBLESHOOTING.md

### 需求 4: API 文档合并

**用户故事**: 作为开发者，我希望所有 API 文档集中在一个文件中，方便查阅和维护。

#### 验收标准

1. WHEN 合并 API 文档时，THE System SHALL 创建 eks-info-app/API_DOCUMENTATION.md 文件
2. WHEN 合并 API 文档时，THE System SHALL 包含所有存储 API 文档内容（EBS, EFS, S3）
3. WHEN 合并 API 文档时，THE System SHALL 包含所有功能 API 文档内容（Network, Resources, Scaling, Stress）
4. WHEN 合并 API 文档时，THE System SHALL 删除原始的 8 个独立 API 文档文件
5. WHEN 合并 API 文档时，THE System SHALL 保持代码示例和格式完整性

### 需求 5: 目录结构优化

**用户故事**: 作为项目维护者，我希望优化项目目录结构，使其更加清晰和专业。

#### 验收标准

1. WHEN 优化结构时，THE System SHALL 创建 terraform 目录并移动所有 .tf 文件
2. WHEN 优化结构时，THE System SHALL 创建 scripts 目录并移动所有脚本文件
3. WHEN 优化结构时，THE System SHALL 创建 eks-info-app/tests 目录并移动所有测试文件
4. WHEN 优化结构时，THE System SHALL 创建 k8s/storage 目录并移动存储相关 YAML 文件
5. WHEN 优化结构时，THE System SHALL 保持所有文件的相对引用关系正确

### 需求 6: 测试文件整理

**用户故事**: 作为开发者，我希望所有测试文件集中管理，便于执行和维护。

#### 验收标准

1. WHEN 整理测试文件时，THE System SHALL 将所有 test_*.py 文件移动到 eks-info-app/tests 目录
2. WHEN 整理测试文件时，THE System SHALL 删除重复的测试脚本（test.sh, test-docker.sh）
3. WHEN 整理测试文件时，THE System SHALL 保留 test_all_pages.sh 并移动到 scripts 目录
4. WHEN 整理测试文件时，THE System SHALL 在 tests 目录创建 __init__.py 文件
5. WHEN 整理测试文件时，THE System SHALL 确保所有测试导入路径正确

### 需求 7: 构建脚本优化

**用户故事**: 作为开发者，我希望删除重复的构建脚本，只保留必要的构建工具。

#### 验收标准

1. WHEN 优化构建脚本时，THE System SHALL 删除 eks-info-app/build-docker.sh
2. WHEN 优化构建脚本时，THE System SHALL 保留 eks-info-app/build.sh
3. WHEN 优化构建脚本时，THE System SHALL 保留 eks-info-app/push-to-ecr.sh
4. WHEN 优化构建脚本时，THE System SHALL 删除 eks-info-app 中的任务总结文档
5. WHEN 优化构建脚本时，THE System SHALL 保留 DOCKER_BUILD_GUIDE.md

### 需求 8: .gitignore 更新

**用户故事**: 作为项目维护者，我希望更新 .gitignore 文件，确保临时文件不会被提交到版本控制。

#### 验收标准

1. WHEN 更新 .gitignore 时，THE System SHALL 添加所有日志文件模式
2. WHEN 更新 .gitignore 时，THE System SHALL 添加所有 Python 缓存模式
3. WHEN 更新 .gitignore 时，THE System SHALL 添加所有临时文件模式
4. WHEN 更新 .gitignore 时，THE System SHALL 添加所有系统文件模式
5. WHEN 更新 .gitignore 时，THE System SHALL 保留必要的 Terraform 文件（terraform.tfvars）

### 需求 9: 文档引用更新

**用户故事**: 作为项目维护者，我希望更新所有文档中的文件引用，确保链接正确。

#### 验收标准

1. WHEN 更新文档引用时，THE System SHALL 更新 README.md 中的项目结构说明
2. WHEN 更新文档引用时，THE System SHALL 更新所有脚本中的路径引用
3. WHEN 更新文档引用时，THE System SHALL 更新 Kubernetes YAML 文件中的路径引用
4. WHEN 更新文档引用时，THE System SHALL 验证所有文档链接有效性
5. WHEN 更新文档引用时，THE System SHALL 更新 .kiro/specs 中的文档引用

### 需求 10: 清理验证

**用户故事**: 作为项目维护者，我希望验证清理操作的正确性，确保项目仍然可以正常构建和部署。

#### 验收标准

1. WHEN 验证清理结果时，THE System SHALL 执行 Terraform 初始化和验证
2. WHEN 验证清理结果时，THE System SHALL 执行 Docker 镜像构建测试
3. WHEN 验证清理结果时，THE System SHALL 验证所有脚本可执行性
4. WHEN 验证清理结果时，THE System SHALL 检查所有文档链接有效性
5. WHEN 验证清理结果时，THE System SHALL 生成清理报告文档

---

## 约束条件

### 安全约束
1. 清理操作前必须创建项目备份
2. 不得删除 Terraform 状态文件（terraform.tfstate）
3. 不得删除核心配置文件（terraform.tfvars, .terraform.lock.hcl）
4. 不得删除 Kubernetes 部署配置文件
5. 不得删除应用核心代码文件

### 性能约束
1. 清理操作应在 5 分钟内完成
2. 文档合并应保持原有格式和代码示例
3. 目录结构调整不应影响构建速度

### 兼容性约束
1. 清理后的项目必须与现有部署脚本兼容
2. 清理后的项目必须与 Terraform 版本兼容
3. 清理后的项目必须与 Kubernetes 配置兼容

---

## 非功能需求

### 可维护性
- 清理后的项目结构应符合行业最佳实践
- 文档应清晰、准确、易于理解
- 代码组织应逻辑清晰、层次分明

### 可扩展性
- 目录结构应便于添加新功能
- 文档结构应便于添加新章节
- 脚本应便于添加新命令

### 可读性
- 所有文档应使用中文编写
- 代码注释应清晰明了
- 文件命名应具有描述性

---

## 验收标准总结

项目清理完成后，应满足以下条件：

1. ✅ 所有临时文件已删除
2. ✅ 所有过时脚本已删除
3. ✅ 文档已合并为 4 个主要文件
4. ✅ 目录结构已优化为 4 层结构
5. ✅ 测试文件已集中管理
6. ✅ .gitignore 已更新
7. ✅ 所有文档引用已更新
8. ✅ 项目可以正常构建和部署
9. ✅ 所有文档链接有效
10. ✅ 生成清理报告

---

## 参考文档

- [项目清理分析报告](../../../PROJECT_CLEANUP_ANALYSIS.md)
- [清理执行计划](../../../CLEANUP_EXECUTION_PLAN.md)
- [AWS 清理报告](../../../AWS_CLEANUP_REPORT.md)
- [主 README](../../../README.md)

---

**文档版本**: 1.0  
**最后更新**: 2025-11-16
