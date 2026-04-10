/**
 * 全局配置文件
 * 所有前端页面共享使用
 */

const CONFIG = {
    // API基础URL
    API_BASE_URL: window.location.origin,
    
    // 默认设置
    DEFAULTS: {
        // 分页大小
        PAGE_SIZE: 20,
        // 日期格式
        DATE_FORMAT: 'YYYY-MM-DD',
        // 时间格式
        TIME_FORMAT: 'HH:mm',
        // 日期时间格式
        DATETIME_FORMAT: 'YYYY-MM-DD HH:mm:ss'
    },
    
    // 本地存储键名
    STORAGE_KEYS: {
        TOKEN: 'access_token',
        USER: 'current_user',
        THEME: 'theme',
        LANGUAGE: 'language'
    },
    
    // 业务配置
    BUSINESS: {
        // 促销买N赠M
        PROMOTION_TRIGGER_QTY: 10,
        PROMOTION_GIFT_QTY: 1,
        // 默认积分余额
        DEFAULT_CREDIT_BALANCE: 0,
        // 用户角色
        ROLES: {
            STAFF: 'staff',
            ADMIN: 'admin',
            SUPER_ADMIN: 'super_admin'
        }
    },
    
    // 服务类型
    SERVICE_TYPES: {
        WATER: 'water',
        MEETING: 'meeting_room',
        DINING: 'dining'
    },
    
    // 订单状态
    ORDER_STATUS: {
        UNPAID: 'unpaid',
        PAID: 'paid',
        REFUNDED: 'refunded'
    },
    
    // 会议室预约状态
    BOOKING_STATUS: {
        PENDING: 'pending',
        CONFIRMED: 'confirmed',
        CANCELLED: 'cancelled',
        COMPLETED: 'completed'
    }
};

// 工具函数
const Utils = {
    /**
     * 格式化日期
     */
    formatDate(date, format = CONFIG.DEFAULTS.DATE_FORMAT) {
        if (!date) return '';
        const d = new Date(date);
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
    
    /**
     * 格式化金额
     */
    formatMoney(amount) {
        return '¥' + (amount || 0).toFixed(2);
    },
    
    /**
     * 显示提示消息
     */
    showMessage(message, type = 'info') {
        alert(message);
        // 可以扩展为更美观的提示组件
    },
    
    /**
     * 获取本地存储
     */
    getStorage(key) {
        try {
            return JSON.parse(localStorage.getItem(key));
        } catch {
            return localStorage.getItem(key);
        }
    },
    
    /**
     * 设置本地存储
     */
    setStorage(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    },
    
    /**
     * 删除本地存储
     */
    removeStorage(key) {
        localStorage.removeItem(key);
    },
    
    /**
     * 检查是否登录
     */
    isLoggedIn() {
        return !!this.getStorage(CONFIG.STORAGE_KEYS.TOKEN);
    },
    
    /**
     * 获取当前用户
     */
    getCurrentUser() {
        return this.getStorage(CONFIG.STORAGE_KEYS.USER);
    },
    
    /**
     * 登出
     */
    logout() {
        this.removeStorage(CONFIG.STORAGE_KEYS.TOKEN);
        this.removeStorage(CONFIG.STORAGE_KEYS.USER);
        window.location.href = '/login.html';
    }
};

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CONFIG, Utils };
}