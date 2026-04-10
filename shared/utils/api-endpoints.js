/**
 * AI产业集群空间服务系统统一API端点配置
 * 与后端v1 API规范完全对齐
 */

const API_ENDPOINTS = {
    // 水站服务
    WATER: {
        PRODUCTS: '/water/products',
        BALANCE: '/water/balance', 
        PICKUPS: '/water/pickups',
        PICKUP_CREATE: '/water/pickup',
        PICKUP_PAY: (pickupId) => `/water/pickup/${pickupId}/pay`,
        OFFICES: '/water/offices',
        SETTLEMENTS: '/water/settlements',
        SETTLEMENT_APPLY: '/water/settlement/apply',
        SETTLEMENT_CONFIRM: (pickupId) => `/water/settlement/${pickupId}/confirm`
    },
    
    // 会议室服务
    MEETING: {
        ROOMS: '/meeting/rooms',
        ROOM_DETAIL: (roomId) => `/meeting/rooms/${roomId}`,
        BOOKINGS: '/meeting/bookings',
        BOOKING_DETAIL: (bookingId) => `/meeting/bookings/${bookingId}`,
        BOOKING_APPROVE: (bookingId) => `/meeting/bookings/${bookingId}/approve`,
        BOOKING_CANCEL: (bookingId) => `/meeting/bookings/${bookingId}/cancel`,
        ROOM_AVAILABILITY: (roomId, date) => `/meeting/rooms/${roomId}/availability?date=${date}`
    },
    
    // 系统服务
    SYSTEM: {
        USERS: '/system/users',
        USER_DETAIL: (userId) => `/system/users/${userId}`,
        OFFICES: '/system/offices',
        OFFICE_DETAIL: (officeId) => `/system/offices/${officeId}`,
        AUTH_LOGIN: '/system/auth/login',
        AUTH_LOGOUT: '/system/auth/logout',
        AUTH_PROFILE: '/system/auth/profile'
    }
};

// 导出为全局变量
window.API_ENDPOINTS = API_ENDPOINTS;