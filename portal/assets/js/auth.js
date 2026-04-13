/**
 * 统一认证管理工具 - auth.js
 * 
 * 功能：
 * 1. 统一Token管理（存储key：'token'）
 * 2. 登录状态检查
 * 3. Token自动验证
 * 4. Token过期处理
 * 5. 自动跳转登录页
 * 
 * 使用方法：
 * - 在页面顶部引入：<script src="/portal/assets/js/auth.js"></script>
 * - 页面初始化时调用：checkAuth()
 * - API请求时调用：getAuthHeaders()
 * - 退出时调用：logout()
 */

const AuthManager = {
    // 统一Token存储key
    TOKEN_KEY: 'token',
    USER_INFO_KEY: 'userInfo',
    TOKEN_TIMESTAMP_KEY: 'token_timestamp',
    
    // API配置
    getApiBase() {
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port || '8008';
        return `${protocol}//${hostname}:${port}/api/v1/system`;
    },
    
    // Token过期时间（24小时，与后端一致）
    TOKEN_EXPIRE_HOURS: 24,
    
    /**
     * 获取Token
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },
    
    /**
     * 设置Token
     */
    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
        localStorage.setItem(this.TOKEN_TIMESTAMP_KEY, new Date().toISOString());
    },
    
    /**
     * 获取用户信息
     */
    getUserInfo() {
        const userInfoStr = localStorage.getItem(this.USER_INFO_KEY);
        if (!userInfoStr) return null;
        try {
            return JSON.parse(userInfoStr);
        } catch (e) {
            return null;
        }
    },
    
    /**
     * 设置用户信息
     */
    setUserInfo(userInfo) {
        localStorage.setItem(this.USER_INFO_KEY, JSON.stringify(userInfo));
    },
    
    /**
     * 检查Token是否过期（本地检查）
     */
    isTokenExpired() {
        const tokenTimestamp = localStorage.getItem(this.TOKEN_TIMESTAMP_KEY);
        if (!tokenTimestamp) return true;
        
        const loginTime = new Date(tokenTimestamp);
        const now = new Date();
        const hoursPassed = (now - loginTime) / (1000 * 60 * 60);
        
        return hoursPassed >= this.TOKEN_EXPIRE_HOURS;
    },
    
    /**
     * 获取认证请求头
     */
    getAuthHeaders() {
        const token = this.getToken();
        if (!token) return {};
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    },
    
    /**
     * 验证Token有效性（调用后端API）
     */
    async validateToken() {
        const token = this.getToken();
        if (!token) return false;
        
        try {
            const response = await fetch(`${this.getApiBase()}/auth/profile`, {
                method: 'GET',
                headers: this.getAuthHeaders()
            });
            
            if (response.status === 401) {
                // Token无效或过期
                this.clearAuth();
                return false;
            }
            
            if (response.ok) {
                const data = await response.json();
                // 更新用户信息
                this.setUserInfo({
                    id: data.user_id,
                    name: data.name || data.username,
                    username: data.username,
                    role: data.role,
                    roleName: data.role_name,
                    department: data.department,
                    avatar: '👤'
                });
                return true;
            }
            
            return false;
        } catch (e) {
            console.error('Token验证失败:', e);
            // 网络错误时，假设Token有效（避免频繁跳转）
            return !this.isTokenExpired();
        }
    },
    
    /**
     * 检查登录状态（完整流程）
     * 
     * @param {Object} options - 配置选项
     * @param {boolean} options.requireAuth - 是否必须登录（默认true）
     * @param {boolean} options.requireAdmin - 是否需要管理员权限（默认false）
     * @param {string} options.redirectUrl - 未登录跳转地址（默认自动判断）
     * @param {boolean} options.validateToken - 是否验证Token有效性（默认true）
     * 
     * @returns {Promise<Object|null>} - 返回用户信息或null
     */
    async checkAuth(options = {}) {
        const {
            requireAuth = true,
            requireAdmin = false,
            redirectUrl = null,
            validateToken = true
        } = options;
        
        // 1. 检查Token是否存在
        const token = this.getToken();
        if (!token) {
            if (requireAuth) {
                this.redirectToLogin(redirectUrl);
                return null;
            }
            return null;
        }
        
        // 2. 检查Token是否过期（本地快速检查）
        if (this.isTokenExpired()) {
            this.clearAuth();
            if (requireAuth) {
                this.redirectToLogin(redirectUrl);
                return null;
            }
            return null;
        }
        
        // 3. 验证Token有效性（后端验证）
        if (validateToken) {
            const isValid = await this.validateToken();
            if (!isValid) {
                if (requireAuth) {
                    this.redirectToLogin(redirectUrl);
                    return null;
                }
                return null;
            }
        }
        
        // 4. 获取用户信息
        const userInfo = this.getUserInfo();
        if (!userInfo) {
            if (requireAuth) {
                this.redirectToLogin(redirectUrl);
                return null;
            }
            return null;
        }
        
        // 5. 检查管理员权限
        if (requireAdmin) {
            const adminRoles = ['super_admin', 'admin', 'office_admin'];
            if (!adminRoles.includes(userInfo.role)) {
                alert('权限不足，需要管理员权限');
                window.location.href = '/portal/index.html';
                return null;
            }
        }
        
        return userInfo;
    },
    
    /**
     * 跳转到登录页（携带当前页面地址）
     */
    redirectToLogin(customUrl = null) {
        const loginUrl = customUrl || '/portal/admin/login.html';
        const currentUrl = window.location.pathname + window.location.search;
        const redirectParam = encodeURIComponent(currentUrl);
        
        // 携带redirect参数，登录后自动跳回
        window.location.href = `${loginUrl}?redirect=${redirectParam}`;
    },
    
    /**
     * 清除认证信息
     */
    clearAuth() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_INFO_KEY);
        localStorage.removeItem(this.TOKEN_TIMESTAMP_KEY);
        localStorage.removeItem('rememberedUsername');
    },
    
    /**
     * 退出登录
     */
    async logout() {
        const token = this.getToken();
        
        // 调用后端退出API（将Token加入黑名单）
        if (token) {
            try {
                await fetch(`${this.getApiBase()}/auth/logout`, {
                    method: 'POST',
                    headers: this.getAuthHeaders()
                });
            } catch (e) {
                console.error('退出API调用失败:', e);
            }
        }
        
        // 清除本地存储
        this.clearAuth();
        
        // 跳转登录页
        window.location.href = '/portal/admin/login.html';
    },
    
    /**
     * 检查并刷新Token（可选功能）
     * 在页面加载时调用，保持登录状态新鲜
     */
    async refreshAuth() {
        const token = this.getToken();
        if (!token) return false;
        
        // 检查是否需要刷新（接近过期时刷新）
        const tokenTimestamp = localStorage.getItem(this.TOKEN_TIMESTAMP_KEY);
        if (!tokenTimestamp) return false;
        
        const loginTime = new Date(tokenTimestamp);
        const now = new Date();
        const hoursPassed = (now - loginTime) / (1000 * 60 * 60);
        
        // 如果Token超过20小时，尝试刷新
        if (hoursPassed >= 20) {
            // 目前系统不支持Token刷新，所以重新验证
            return await this.validateToken();
        }
        
        return true;
    },
    
    /**
     * 获取用户显示名称
     */
    getUserDisplayName() {
        const userInfo = this.getUserInfo();
        if (!userInfo) return '未登录';
        return userInfo.name || userInfo.username || '用户';
    },
    
    /**
     * 获取用户角色显示名称
     */
    getUserRoleName() {
        const userInfo = this.getUserInfo();
        if (!userInfo) return '';
        return userInfo.roleName || userInfo.role || '';
    },
    
    /**
     * 检查是否为管理员
     */
    isAdmin() {
        const userInfo = this.getUserInfo();
        if (!userInfo) return false;
        return ['super_admin', 'admin', 'office_admin'].includes(userInfo.role);
    },
    
    /**
     * 检查是否为超级管理员
     */
    isSuperAdmin() {
        const userInfo = this.getUserInfo();
        if (!userInfo) return false;
        return userInfo.role === 'super_admin';
    }
};

// 导出到全局，方便使用
window.AuthManager = AuthManager;

// 快捷方法
window.checkAuth = (options = {}) => AuthManager.checkAuth(options);
window.getAuthHeaders = () => AuthManager.getAuthHeaders();
window.getToken = () => AuthManager.getToken();
window.logout = () => AuthManager.logout();
window.getUserInfo = () => AuthManager.getUserInfo();

console.log('✅ AuthManager已加载 - 统一认证管理工具');