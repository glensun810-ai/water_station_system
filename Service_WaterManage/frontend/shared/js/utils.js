/**
 * 通用工具函数
 * 日期格式化、金额格式化、字符串处理等
 */

const Utils = {
  formatDate(date, format = 'YYYY-MM-DD') {
    if (!date) return '';

    const d = new Date(date);

    if (isNaN(d.getTime())) return '';

    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');

    return format
      .replace('YYYY', year)
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds);
  },

  formatDateTime(date) {
    return this.formatDate(date, 'YYYY-MM-DD HH:mm:ss');
  },

  formatTime(date) {
    return this.formatDate(date, 'HH:mm:ss');
  },

  formatMoney(amount, currency = '¥') {
    if (amount === null || amount === undefined) return currency + '0.00';
    return currency + Number(amount).toFixed(2);
  },

  formatNumber(num, decimals = 0) {
    if (num === null || num === undefined) return '0';
    return Number(num).toFixed(decimals);
  },

  formatPercent(value, decimals = 1) {
    if (value === null || value === undefined) return '0%';
    return Number(value).toFixed(decimals) + '%';
  },

  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  truncate(str, length = 50, suffix = '...') {
    if (!str) return '';
    if (str.length <= length) return str;
    return str.substring(0, length) + suffix;
  },

  capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  },

  slugify(str) {
    if (!str) return '';
    return str
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  },

  debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  throttle(func, limit = 300) {
    let inThrottle;
    return function (...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;

    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => this.deepClone(item));
    if (obj instanceof Object) {
      const copy = {};
      Object.keys(obj).forEach(key => {
        copy[key] = this.deepClone(obj[key]);
      });
      return copy;
    }

    return obj;
  },

  isEmpty(obj) {
    if (obj === null || obj === undefined) return true;
    if (typeof obj === 'string') return obj.trim().length === 0;
    if (Array.isArray(obj)) return obj.length === 0;
    if (typeof obj === 'object') return Object.keys(obj).length === 0;
    return false;
  },

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  randomId() {
    return Math.random().toString(36).substring(2, 9);
  },

  uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  },

  getStatusText(status) {
    const statusMap = {
      pending: '待确认',
      applied: '待确认',
      confirmed: '已确认',
      settled: '已结算',
      rejected: '已拒绝',
      active: '活跃',
      inactive: '已停用',
      unpaid: '未付款',
      paid: '已付款'
    };
    return statusMap[status] || status;
  },

  getRoleText(role) {
    const roleMap = {
      staff: '普通员工',
      admin: '管理员',
      super_admin: '超级管理员'
    };
    return roleMap[role] || role;
  },

  copyToClipboard(text) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text);
      if (typeof Toast !== 'undefined') {
        Toast.success('已复制到剪贴板');
      }
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      if (typeof Toast !== 'undefined') {
        Toast.success('已复制到剪贴板');
      }
    }
  },

  downloadFile(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  },

  parseQuery(queryString) {
    const params = {};
    const searchParams = new URLSearchParams(queryString);
    for (const [key, value] of searchParams) {
      params[key] = value;
    }
    return params;
  },

  buildQuery(params) {
    return new URLSearchParams(params).toString();
  }
};

if (typeof window !== 'undefined') {
  window.Utils = Utils;
}