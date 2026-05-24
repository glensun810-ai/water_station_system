/**
 * Toast 通知组件 - 纯 JS 实现，无框架依赖
 * 用法: showToast('操作成功', 'success', '提示');
 * 用法: showToast('操作失败: 网络错误', 'error');
 */

(function () {
    const style = document.createElement('style');
    style.textContent = `
        .s-toast {
            position: fixed;
            bottom: var(--spacing-xl, 24px);
            right: var(--spacing-xl, 24px);
            background: var(--bg-card, #fff);
            border-radius: var(--radius-lg, 12px);
            padding: var(--spacing-md, 16px) var(--spacing-lg, 24px);
            box-shadow: var(--shadow-lg, 0 8px 30px rgba(0,0,0,0.15));
            z-index: 10001;
            animation: s-slideIn 0.3s ease;
            max-width: 420px;
            font-size: 14px;
            line-height: 1.6;
            pointer-events: auto;
        }
        .s-toast.success { border-left: 4px solid var(--success, #10b981); }
        .s-toast.error   { border-left: 4px solid var(--danger, #ef4444); }
        .s-toast.warning { border-left: 4px solid var(--warning, #f59e0b); }
        .s-toast-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        @keyframes s-slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to   { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);

    let timer = null;
    let current = null;

    const typeLabels = {
        success: '操作成功',
        error: '操作失败',
        warning: '提示',
    };

    window.showToast = function (message, type, title) {
        if (current) current.remove();
        if (timer) clearTimeout(timer);

        type = type || 'success';
        title = title || typeLabels[type] || '提示';

        const el = document.createElement('div');
        el.className = 's-toast ' + type;
        el.innerHTML = '<div class="s-toast-title">' + title + '</div><div>' + message + '</div>';
        document.body.appendChild(el);
        current = el;

        timer = setTimeout(function () {
            el.remove();
            current = null;
        }, 5000);
    };
})();
