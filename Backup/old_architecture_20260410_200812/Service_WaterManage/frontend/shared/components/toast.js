/**
 * Toast消息组件 v2.0
 * 显示成功、错误、警告、信息提示
 * 特性：ARIA可访问性、键盘导航、移动端优化
 */

class ToastClass {
  constructor() {
    this.container = null;
    this.toasts = [];
    this.maxToasts = 5;
    this.defaultDuration = 3000;
    this.init();
  }

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      this.container.setAttribute('role', 'status');
      this.container.setAttribute('aria-live', 'polite');
      this.container.setAttribute('aria-label', '消息通知');
      document.body.appendChild(this.container);
    }
  }

  show(options) {
    const { type = 'info', title, message, duration = this.defaultDuration } = options;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');

    const icons = {
      success: 'fas fa-check-circle',
      error: 'fas fa-times-circle',
      warning: 'fas fa-exclamation-triangle',
      info: 'fas fa-info-circle'
    };

    const titles = {
      success: title || '成功',
      error: title || '错误',
      warning: title || '警告',
      info: title || '信息'
    };

    const ariaLabels = {
      success: '成功消息',
      error: '错误消息',
      warning: '警告消息',
      info: '信息消息'
    };

    const displayTitle = this.escapeHtml(titles[type]);
    const displayMessage = message ? this.escapeHtml(message) : '';

    toast.innerHTML = `
      <div class="toast-icon" aria-hidden="true">
        <i class="${icons[type]}"></i>
      </div>
      <div class="toast-content">
        <div class="toast-title">${displayTitle}</div>
        ${displayMessage ? `<div class="toast-message">${displayMessage}</div>` : ''}
      </div>
      <button class="toast-close" aria-label="关闭${ariaLabels[type]}" title="关闭">
        <i class="fas fa-times" aria-hidden="true"></i>
      </button>
    `;

    this.container.appendChild(toast);
    this.toasts.push(toast);

    if (this.toasts.length > this.maxToasts) {
      this.remove(this.toasts[0]);
    }

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => this.remove(toast));

    toast.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.remove(toast);
      }
    });

    toast.setAttribute('tabindex', '0');
    toast.focus();

    if (duration > 0) {
      setTimeout(() => this.remove(toast), duration);
    }

    return toast;
  }

  remove(toast) {
    if (!toast || !toast.parentNode) return;

    toast.style.animation = 'toast-slide-out 0.3s ease forwards';
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      this.toasts = this.toasts.filter(t => t !== toast);
    }, 300);
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  success(message, duration = this.defaultDuration) {
    return this.show({ type: 'success', message, duration });
  }

  error(message, duration = this.defaultDuration) {
    return this.show({ type: 'error', message, duration });
  }

  warning(message, duration = this.defaultDuration) {
    return this.show({ type: 'warning', message, duration });
  }

  info(message, duration = this.defaultDuration) {
    return this.show({ type: 'info', message, duration });
  }

  clear() {
    this.toasts.forEach(toast => this.remove(toast));
  }
}

const Toast = new ToastClass();

if (typeof window !== 'undefined') {
  window.Toast = Toast;
}