/**
 * EKS Info WebApp - 主应用 JavaScript
 * 
 * 作者: RJ.Wang
 * 邮箱: wangrenjun@gmail.com
 * 创建时间: 2025-11-14
 */

// 表单验证
document.addEventListener('DOMContentLoaded', function() {
    // 为所有表单添加验证
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(form)) {
                event.preventDefault();
                showError('请填写所有必填字段');
            }
        });
    });
    
    // 为所有输入框添加实时验证
    const inputs = document.querySelectorAll('input[required], textarea[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateInput(input);
        });
        
        input.addEventListener('input', function() {
            // 清除错误状态
            if (input.classList.contains('error')) {
                input.classList.remove('error');
            }
        });
    });
});

// 验证表单
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    inputs.forEach(input => {
        if (!validateInput(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// 验证单个输入
function validateInput(input) {
    const value = input.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // 检查必填字段
    if (input.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = '此字段为必填项';
    }
    
    // 检查数字类型
    if (input.type === 'number' && value) {
        const num = parseFloat(value);
        const min = input.hasAttribute('min') ? parseFloat(input.getAttribute('min')) : null;
        const max = input.hasAttribute('max') ? parseFloat(input.getAttribute('max')) : null;
        
        if (isNaN(num)) {
            isValid = false;
            errorMessage = '请输入有效的数字';
        } else if (min !== null && num < min) {
            isValid = false;
            errorMessage = `值不能小于 ${min}`;
        } else if (max !== null && num > max) {
            isValid = false;
            errorMessage = `值不能大于 ${max}`;
        }
    }
    
    // 检查邮箱格式
    if (input.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = '请输入有效的邮箱地址';
        }
    }
    
    // 检查 URL 格式
    if (input.type === 'url' && value) {
        try {
            new URL(value);
        } catch (e) {
            isValid = false;
            errorMessage = '请输入有效的 URL';
        }
    }
    
    // 显示验证结果
    if (!isValid) {
        input.classList.add('error');
        showInputError(input, errorMessage);
    } else {
        input.classList.remove('error');
        hideInputError(input);
    }
    
    return isValid;
}

// 显示输入错误
function showInputError(input, message) {
    // 移除已存在的错误消息
    hideInputError(input);
    
    // 创建错误消息元素
    const errorDiv = document.createElement('div');
    errorDiv.className = 'input-error-message';
    errorDiv.textContent = message;
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '0.875rem';
    errorDiv.style.marginTop = '5px';
    
    // 插入错误消息
    input.parentNode.appendChild(errorDiv);
}

// 隐藏输入错误
function hideInputError(input) {
    const errorDiv = input.parentNode.querySelector('.input-error-message');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// 添加 CSS 样式用于错误状态
const style = document.createElement('style');
style.textContent = `
    input.error,
    textarea.error,
    select.error {
        border-color: #dc3545 !important;
        box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1) !important;
    }
    
    .input-error-message {
        animation: fadeIn 0.3s;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-5px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 复制到剪贴板
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showSuccess('已复制到剪贴板');
        }).catch(err => {
            console.error('复制失败:', err);
            showError('复制失败');
        });
    } else {
        // 降级方案
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showSuccess('已复制到剪贴板');
        } catch (err) {
            console.error('复制失败:', err);
            showError('复制失败');
        }
        document.body.removeChild(textarea);
    }
}

// 下载文件
function downloadFile(content, filename, contentType = 'text/plain') {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// 确认对话框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 延迟执行
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 重试函数
async function retry(fn, maxAttempts = 3, delayMs = 1000) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await fn();
        } catch (error) {
            if (attempt === maxAttempts) {
                throw error;
            }
            console.warn(`尝试 ${attempt} 失败，${delayMs}ms 后重试...`);
            await delay(delayMs);
        }
    }
}

// 格式化 JSON
function formatJSON(obj) {
    return JSON.stringify(obj, null, 2);
}

// 安全的 JSON 解析
function safeJSONParse(str, defaultValue = null) {
    try {
        return JSON.parse(str);
    } catch (e) {
        console.error('JSON 解析失败:', e);
        return defaultValue;
    }
}

// 检查是否为移动设备
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// 获取查询参数
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 设置查询参数
function setQueryParam(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.pushState({}, '', url);
}

// 滚动到顶部
function scrollToTop(smooth = true) {
    window.scrollTo({
        top: 0,
        behavior: smooth ? 'smooth' : 'auto'
    });
}

// 滚动到元素
function scrollToElement(element, offset = 0) {
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;
    
    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

// 检查元素是否在视口中
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// 本地存储辅助函数
const storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('存储失败:', e);
            return false;
        }
    },
    
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('读取存储失败:', e);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('删除存储失败:', e);
            return false;
        }
    },
    
    clear: function() {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('清空存储失败:', e);
            return false;
        }
    }
};

// 导出函数供全局使用
window.eksApp = {
    validateForm,
    validateInput,
    debounce,
    throttle,
    copyToClipboard,
    downloadFile,
    confirmAction,
    delay,
    retry,
    formatJSON,
    safeJSONParse,
    isMobileDevice,
    getQueryParam,
    setQueryParam,
    scrollToTop,
    scrollToElement,
    isInViewport,
    storage
};
