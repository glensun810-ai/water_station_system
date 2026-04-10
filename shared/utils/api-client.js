/**
 * AI产业集群空间服务系统统一API客户端
 * 提供标准化的API调用方法，处理认证、错误等通用逻辑
 */

class ApiService {
    constructor(baseURL = '/api/v1') {
        this.baseURL = baseURL;
        this.token = null;
    }

    // 设置认证令牌
    setToken(token) {
        this.token = token;
    }

    // 清除认证令牌
    clearToken() {
        this.token = null;
    }

    // 获取请求头
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    // 构建完整URL
    buildUrl(endpoint) {
        // 确保endpoint以/开头
        const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        return `${this.baseURL}${normalizedEndpoint}`;
    }

    // 通用请求方法
    async request(endpoint, options = {}) {
        const url = this.buildUrl(endpoint);
        const config = {
            headers: this.getHeaders(),
            ...options,
        };

        try {
            const response = await fetch(url, config);
            
            // 检查HTTP状态码
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // 检查API响应格式
            if (data.code >= 400) {
                throw new Error(data.message || 'API请求失败');
            }

            return data.data || data;
        } catch (error) {
            console.error('API请求失败:', { endpoint, error: error.message });
            throw error;
        }
    }

    // GET请求
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullEndpoint = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(fullEndpoint, { method: 'GET' });
    }

    // POST请求
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // PUT请求
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    // DELETE请求
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// 创建全局API实例
const apiClient = new ApiService();

// 从localStorage初始化token
const storedToken = localStorage.getItem('token');
if (storedToken) {
    apiClient.setToken(storedToken);
}

// 监听localStorage变化来同步token
window.addEventListener('storage', (event) => {
    if (event.key === 'token') {
        if (event.newValue) {
            apiClient.setToken(event.newValue);
        } else {
            apiClient.clearToken();
        }
    }
});

// 导出为全局变量
window.apiClient = apiClient;
window.ApiService = ApiService;