/**
 * AI产业集群空间服务系统统一API配置
 */
const API_CONFIG = {
    // 主API网关基础URL
    BASE_URL: window.location.origin + '/api/v1',
    
    // 水站服务
    WATER: {
        PRODUCTS: '/water/products',
        BALANCE: '/water/balance',
        PICKUPS: '/water/pickups', 
        SETTLEMENTS: '/water/settlements',
        TRANSACTIONS: '/water/transactions'
    },
    
    // 会议室服务  
    MEETING: {
        ROOMS: '/meeting/rooms',
        BOOKINGS: '/meeting/bookings',
        APPROVALS: '/meeting/approvals'
    },
    
    // 系统服务
    SYSTEM: {
        USERS: '/system/users',
        OFFICES: '/system/offices',
        AUTH: '/system/auth'
    }
};

// 工具函数：构建完整API URL
function buildApiUrl(endpoint) {
    return API_CONFIG.BASE_URL + endpoint;
}

// 导出配置
window.API_CONFIG = API_CONFIG;
window.buildApiUrl = buildApiUrl;