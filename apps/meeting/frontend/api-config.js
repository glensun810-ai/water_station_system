/**
 * 统一API配置 - 所有前端页面通用
 * 
 * 功能：
 * 1. 自动检测当前访问方式（IP/域名）
 * 2. 自动适配HTTP/HTTPS
 * 3. 支持localStorage覆盖（用于测试）
 * 
 * 使用方法：
 * 在HTML文件中引入：<script src="/api-config.js"></script>
 * 使用方式：const API_BASE = window.API_CONFIG.baseURL;
 */

(function() {
    'use strict';
    
    // 环境检测
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    const isLocalhost = 
        hostname === 'localhost' || 
        hostname === '127.0.0.1' ||
        hostname.startsWith('192.168.') ||
        hostname.startsWith('10.') ||
        hostname.startsWith('172.') ||
        protocol === 'file:';
    
    // 判断是否是IP地址访问
    const isIPAccess = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(hostname);
    
    // API基础地址配置
    let apiBaseURL;
    
    if (isLocalhost) {
        // 本地开发环境
        apiBaseURL = 'http://localhost:8000/api/v1';
    } else {
        // 生产环境：自动使用当前域名和协议
        apiBaseURL = `${protocol}//${hostname}/api/v1`;
    }
    
    // 允许通过localStorage临时覆盖（用于测试）
    const overrideURL = localStorage.getItem('API_BASE_OVERRIDE');
    if (overrideURL) {
        apiBaseURL = overrideURL;
        console.warn('⚠️ API地址已被覆盖:', overrideURL);
    }
    
    // 全局API配置对象
    window.API_CONFIG = {
        // 当前环境
        environment: isLocalhost ? 'development' : 'production',
        
        // API基础地址
        baseURL: apiBaseURL,
        
        // 水站管理API
        waterAPI: apiBaseURL,
        
        // 会议室管理API（注意：会议室API有/meeting前缀）
        meetingAPI: apiBaseURL + '/meeting',
        
        // 超时配置
        timeout: isLocalhost ? 30000 : 60000,
        
        // 辅助方法：获取完整API地址
        getFullURL(endpoint) {
            return this.baseURL + endpoint;
        },
        
        // 辅助方法：获取水站API地址
        getWaterAPI(endpoint) {
            return this.waterAPI + (endpoint.startsWith('/') ? endpoint : '/' + endpoint);
        },
        // 辅助方法：获取会议室API地址
        getMeetingAPI(endpoint) {
            return this.meetingAPI + (endpoint.startsWith('/') ? endpoint : '/' + endpoint);
        },
        
        // 临时覆盖API地址（用于测试）
        overrideBaseURL(url) {
            this.baseURL = url;
            this.waterAPI = url;
            this.meetingAPI = url + '/meeting';
            localStorage.setItem('API_BASE_OVERRIDE', url);
            console.warn('⚠️ API地址已临时覆盖:', url);
        },
        
        // 清除覆盖
        clearOverride() {
            localStorage.removeItem('API_BASE_OVERRIDE');
            console.log('✅ 已清除API地址覆盖，请刷新页面');
        }
    };
    
    // 输出配置信息
    console.log('✅ API配置已加载');
    console.log('   环境:', window.API_CONFIG.environment);
    console.log('   API地址:', window.API_CONFIG.baseURL);
    console.log('   水站API:', window.API_CONFIG.waterAPI);
    console.log('   会议室API:', window.API_CONFIG.meetingAPI);
    console.log('   访问方式:', isLocalhost ? '本地开发' : (isIPAccess ? 'IP地址' : '域名访问'));
    
    // 开发环境下提供调试信息
    if (isLocalhost) {
        console.log('💡 提示: 可以通过以下方式修改API地址:');
        console.log('   API_CONFIG.overrideBaseURL("http://新的地址/api")');
        console.log('   API_CONFIG.clearOverride()');
    }
    
})();

// 导出配置（兼容模块化）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.API_CONFIG;
}