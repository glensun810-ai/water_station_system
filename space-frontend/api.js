/**
 * 空间服务API工具类
 * 封装所有与后端API的交互
 */

const API_BASE_URL = '/api/v2/space/types';
const API_RESOURCES_URL = '/api/v2/space/resources';
const API_BOOKINGS_URL = '/api/v2/space/bookings';

class SpaceAPI {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.resourcesURL = API_RESOURCES_URL;
        this.bookingsURL = API_BOOKINGS_URL;
    }

    async request(endpoint, options = {}, baseURL = this.baseURL) {
        const url = `${baseURL}${endpoint}`;
        
        const defaultHeaders = {
            'Content-Type': 'application/json',
        };

        const token = localStorage.getItem('token');
        if (token) {
            defaultHeaders['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);
            
            // 检查响应的Content-Type
            const contentType = response.headers.get('content-type');
            
            // 如果响应不是JSON格式，尝试读取文本并抛出友好错误
            if (!contentType || !contentType.includes('application/json')) {
                const textResponse = await response.text();
                console.error('非JSON响应:', textResponse.substring(0, 200));
                
                // 射取有用的错误信息
                let errorMsg = '服务器返回非预期格式';
                if (textResponse.includes('Internal Server Error')) {
                    errorMsg = '服务器内部错误，请联系管理员';
                } else if (textResponse.includes('Not Found')) {
                    errorMsg = '请求的资源不存在';
                } else if (response.status === 401) {
                    errorMsg = '登录已过期，请重新登录';
                } else if (response.status === 403) {
                    errorMsg = '无权限执行此操作';
                }
                
                throw new Error(errorMsg);
            }
            
            // 解析JSON响应
            const data = await response.json();

            // 处理错误状态
            if (!response.ok) {
                // 优先使用detail字段（FastAPI标准），其次使用message
                const errorMsg = data.detail || data.message || data.error?.message || '请求失败';
                throw new Error(errorMsg);
            }

            return data;
        } catch (error) {
            console.error('API请求错误:', {
                url: url,
                error: error.message,
                type: error.constructor.name
            });
            throw error;
        }
    }

    async get(endpoint, params = {}, baseURL = this.baseURL) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' }, baseURL);
    }

    async post(endpoint, data = {}, baseURL = this.baseURL) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        }, baseURL);
    }

    async put(endpoint, data = {}, baseURL = this.baseURL) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        }, baseURL);
    }

    async delete(endpoint, baseURL = this.baseURL) {
        return this.request(endpoint, { method: 'DELETE' }, baseURL);
    }

    // ========== 空间类型 API ==========
    
    async getSpaceTypes() {
        return this.get('/space/types');
    }

    async getSpaceType(typeCode) {
        return this.get(`/space/types/${typeCode}`);
    }

    async getResources(params = {}) {
        return this.get('/space/resources', params, this.resourcesURL);
    }

    async getResource(resourceId) {
        return this.get(`/space/resources/${resourceId}`, {}, this.resourcesURL);
    }

    async getResourceAvailability(resourceId, date) {
        return this.get(`/space/resources/${resourceId}/availability`, { date }, this.resourcesURL);
    }

    async getBookings(params = {}) {
        return this.get('/space/bookings', params, this.bookingsURL);
    }

    async getMyBookings(params = {}) {
        return this.get('/space/bookings/my', params, this.bookingsURL);
    }

    async getBooking(bookingId) {
        return this.get(`/space/bookings/${bookingId}`, {}, this.bookingsURL);
    }

    async createBooking(bookingData) {
        return this.post('/space/bookings', bookingData, this.bookingsURL);
    }

    async updateBooking(bookingId, updateData) {
        return this.put(`/space/bookings/${bookingId}`, updateData, this.bookingsURL);
    }

    async cancelBooking(bookingId, cancelReason, cancelType = 'user_cancel') {
        return this.put(`/space/bookings/${bookingId}/cancel`, {
            cancel_reason: cancelReason,
            cancel_type: cancelType,
        }, this.bookingsURL);
    }

    async deleteBooking(bookingId, deleteReason = '') {
        return this.delete(`/space/bookings/${bookingId}?delete_reason=${encodeURIComponent(deleteReason)}`, this.bookingsURL);
    }

    async calculateFee(feeData) {
        return this.post('/space/bookings/calculate-fee', feeData, this.bookingsURL);
    }

    async getApprovals(params = {}) {
        return this.get('/space/approvals', params, this.bookingsURL);
    }

    async getApproval(approvalId) {
        return this.get(`/space/approvals/${approvalId}`, {}, this.bookingsURL);
    }

    async approveBooking(approvalId, approveData = {}) {
        return this.put(`/space/approvals/${approvalId}/approve`, approveData, this.bookingsURL);
    }

    async rejectBooking(approvalId, rejectReason) {
        return this.put(`/space/approvals/${approvalId}/reject`, {
            rejected_reason: rejectReason,
        }, this.bookingsURL);
    }

    async getPayments(params = {}) {
        return this.get('/space/payments', params, this.bookingsURL);
    }

    async getPayment(paymentId) {
        return this.get(`/space/payments/${paymentId}`, {}, this.bookingsURL);
    }

    async confirmOfflinePayment(bookingId, paymentData) {
        return this.post(`/space/payments/confirm-offline`, {
            booking_id: bookingId,
            ...paymentData,
        });
    }

    // ========== 统计信息 API ==========
    
    async getStatistics(params = {}) {
        return this.get('/space/statistics', params);
    }

    async getMyStatistics() {
        return this.get('/space/statistics/my');
    }

    // ========== 用户认证 API ==========
    
    async login(username, password) {
        return this.post('/auth/login', { username, password });
    }

    async logout() {
        return this.post('/auth/logout');
    }

    async getCurrentUser() {
        return this.get('/auth/me');
    }

    async updateProfile(profileData) {
        return this.put('/auth/profile', profileData);
    }

    async changePassword(oldPassword, newPassword) {
        return this.put('/auth/password', {
            old_password: oldPassword,
            new_password: newPassword,
        });
    }

    // ========== 通知管理 API ==========
    
    async getNotifications(params = {}) {
        return this.get('/notifications', params);
    }

    async markNotificationRead(notificationId) {
        return this.put(`/notifications/${notificationId}/read`);
    }

    async markAllNotificationsRead() {
        return this.put('/notifications/read-all');
    }
}

const spaceAPI = new SpaceAPI();

export default spaceAPI;
export { SpaceAPI, API_BASE_URL };