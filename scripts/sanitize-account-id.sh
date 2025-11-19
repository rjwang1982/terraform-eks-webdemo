#!/bin/bash
#
# 替换 AWS 账号 ID 为占位符
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-19

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ACCOUNT_ID="<AWS_ACCOUNT_ID>"
PLACEHOLDER="<AWS_ACCOUNT_ID>"

echo "=== 开始替换 AWS 账号 ID ==="
echo "账号 ID: ${ACCOUNT_ID}"
echo "占位符: ${PLACEHOLDER}"
echo ""

# 备份提示
echo "⚠️  建议先提交当前更改到 Git"
read -p "是否继续? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

cd "${PROJECT_ROOT}"

# 统计需要替换的文件
echo ""
echo "📊 扫描需要替换的文件..."
FILES_TO_UPDATE=$(grep -rl "${ACCOUNT_ID}" . \
    --include="*.md" \
    --include="*.yaml" \
    --include="*.yml" \
    --include="*.sh" \
    --include="*.tf" \
    --include="*.tfvars" \
    --exclude-dir=.git \
    --exclude-dir=.terraform \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    2>/dev/null || true)

if [ -z "${FILES_TO_UPDATE}" ]; then
    echo "✅ 没有找到需要替换的文件"
    exit 0
fi

FILE_COUNT=$(echo "${FILES_TO_UPDATE}" | wc -l | tr -d ' ')
echo "找到 ${FILE_COUNT} 个文件需要更新"
echo ""

# 显示将要更新的文件
echo "📝 将要更新的文件:"
echo "${FILES_TO_UPDATE}" | sed 's/^/  - /'
echo ""

# 执行替换
echo "🔄 开始替换..."
UPDATED_COUNT=0

while IFS= read -r file; do
    if [ -f "${file}" ]; then
        # macOS 使用 sed -i ''，Linux 使用 sed -i
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/${ACCOUNT_ID}/${PLACEHOLDER}/g" "${file}"
        else
            sed -i "s/${ACCOUNT_ID}/${PLACEHOLDER}/g" "${file}"
        fi
        echo "  ✓ ${file}"
        ((UPDATED_COUNT++))
    fi
done <<< "${FILES_TO_UPDATE}"

echo ""
echo "✅ 完成！已更新 ${UPDATED_COUNT} 个文件"
echo ""
echo "📋 后续步骤:"
echo "  1. 检查更改: git diff"
echo "  2. 验证文件: grep -r '${PLACEHOLDER}' ."
echo "  3. 提交更改: git add -A && git commit -m 'chore: 替换 AWS 账号 ID 为占位符'"
echo ""
