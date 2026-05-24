/**
 * 空间服务API工具类
 * 封装所有与后端API的交互
 */

const SPACE_API_BASE = '/api/v2/space';

class SpaceAPI {
    constructor() {
        this.baseURL = SPACE_API_BASE;
    }

    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('/api/')
            ? endpoint
            : `${SPACE_API_BASE}${endpoint}`;

        const defaultHeaders = {
            'Content-Type': 'application/json',
        };

        const skipAuth = options.skipAuth === true;
        if (!skipAuth) {
            const token = localStorage.getItem('token');
            if (token) {
                defaultHeaders['Authorization'] = `Bearer ${token}`;
            }
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

            const contentType = response.headers.get('content-type');

            if (!contentType || !contentType.includes('application/json')) {
                const textResponse = await response.text();
                console.error('非JSON响应:', textResponse.substring(0, 200));

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

            const data = await response.json();

            if (!response.ok) {
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

    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // ========== 空间类型 API ==========

    async getSpaceTypes() {
        return this.get('/types');
    }

    async getSpaceType(typeCode) {
        return this.get(`/types/${typeCode}`);
    }

    // ========== 空间资源 API ==========

    async getResources(params = {}) {
        return this.get('/resources', params);
    }

    async getResource(resourceId) {
        return this.get(`/resources/${resourceId}`);
    }

    async getResourceAvailability(resourceId, date) {
        return this.get(`/resources/${resourceId}/availability`, { date });
    }

    // ========== 预约管理 API ==========

    async getBookings(params = {}) {
        return this.get('/bookings', params);
    }

    async getMyBookings(params = {}) {
        return this.get('/bookings/my', params);
    }

    async getBooking(bookingId) {
        return this.get(`/bookings/${bookingId}`);
    }

    async createBooking(bookingData) {
        return this.post('/bookings', bookingData);
    }

    async updateBooking(bookingId, updateData) {
        return this.put(`/bookings/${bookingId}`, updateData);
    }

    async cancelBooking(bookingId, cancelReason, cancelType = 'user_cancel') {
        return this.put(`/bookings/${bookingId}/cancel`, {
            cancel_reason: cancelReason,
            cancel_type: cancelType,
        });
    }

    async deleteBooking(bookingId, deleteReason = '') {
        return this.delete(`/bookings/${bookingId}?delete_reason=${encodeURIComponent(deleteReason)}`);
    }

    async calculateFee(feeData) {
        return this.post('/bookings/calculate-fee', feeData);
    }

    async approveBookingDirect(bookingId, approveData = {}) {
        return this.put(`/bookings/${bookingId}/approve`, approveData);
    }

    async approveWithPayment(bookingId, paymentData = {}) {
        return this.post(`/bookings/${bookingId}/approve-with-payment`, paymentData);
    }

    async confirmBooking(bookingId) {
        return this.put(`/bookings/${bookingId}/confirm`);
    }

    async completeBooking(bookingId) {
        return this.put(`/bookings/${bookingId}/complete`);
    }

    async settleBooking(bookingId) {
        return this.put(`/bookings/${bookingId}/settle`);
    }

    async unsettleBooking(bookingId) {
        return this.put(`/bookings/${bookingId}/unsettle`);
    }

    async batchOperation(data) {
        return this.post('/bookings/batch-operation', data);
    }

    // ========== 审批管理 API ==========

    async getApprovals(params = {}) {
        return this.get('/approvals', params);
    }

    async getApproval(approvalId) {
        return this.get(`/approvals/${approvalId}`);
    }

    async getMyApprovals() {
        return this.get('/approvals/my');
    }

    async getPendingApprovals() {
        return this.get('/approvals/pending');
    }

    async approveBooking(approvalId, approveData = {}) {
        return this.put(`/approvals/${approvalId}/approve`, approveData);
    }

    async batchApprove(approvalData) {
        return this.post('/approvals/batch-approve', approvalData);
    }

    async rejectBooking(approvalId, rejectReason) {
        return this.put(`/approvals/${approvalId}/reject`, {
            rejected_reason: rejectReason,
        });
    }

    async requestModify(approvalId, modifyData) {
        return this.put(`/approvals/${approvalId}/request-modify`, modifyData);
    }

    // ========== 支付管理 API ==========

    async getPayments(params = {}) {
        return this.get('/payments', params);
    }

    async getPayment(paymentId) {
        return this.get(`/payments/${paymentId}`);
    }

    async getMyPayments() {
        return this.get('/payments/my');
    }

    async getPendingPayments() {
        return this.get('/payments/pending');
    }

    async confirmOfflinePayment(bookingId, paymentData) {
        return this.post('/payments/confirm-offline', {
            booking_id: bookingId,
            ...paymentData,
        });
    }

    async confirmPayment(paymentId) {
        return this.put(`/payments/${paymentId}/confirm`);
    }

    async verifyPayment(paymentId) {
        return this.put(`/payments/${paymentId}/verify`);
    }

    async refundPayment(paymentId, refundData = {}) {
        return this.put(`/payments/${paymentId}/refund`, refundData);
    }

    async getPaymentModes(bookingId) {
        return this.get(`/payment/modes/${bookingId}`);
    }

    async deductPayment(data) {
        return this.post('/payment/deduct', data);
    }

    async settleCredit(bookingId) {
        return this.post(`/payment/settle-credit/${bookingId}`);
    }

    async monthlySettlement(data) {
        return this.post('/payment/monthly-settlement', data);
    }

    async getCreditNotes(params = {}) {
        return this.get('/payment/credit-notes', params);
    }

    async getCreditNote(noteId) {
        return this.get(`/payment/credit-notes/${noteId}`);
    }

    // ========== 统计信息 API ==========

    async getStatistics(params = {}) {
        return this.get('/statistics/overview', params);
    }

    async getDashboard() {
        return this.get('/statistics/dashboard');
    }

    async getRevenueStats(params = {}) {
        return this.get('/statistics/revenue', params);
    }

    async getUsageStats(params = {}) {
        return this.get('/statistics/usage', params);
    }

    async getTrendsStats(params = {}) {
        return this.get('/statistics/trends', params);
    }

    async getMyStatistics() {
        return this.get('/statistics/my');
    }

    // ========== 通知 API ==========

    async getNotifications(params = {}) {
        return this.get('/notifications', params);
    }

    async getUnreadNotificationCount() {
        return this.get('/notifications/unread-count');
    }

    async markNotificationRead(notificationId) {
        return this.request(`/api/v2/space/notifications/${notificationId}/read`, {
            method: 'PATCH',
        });
    }

    async markAllNotificationsRead() {
        return this.request('/api/v2/space/notifications/read-all', {
            method: 'PATCH',
        });
    }

    // ========== 用户认证 API ==========

    async login(username, password) {
        return this.request('/api/v1/system/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
            skipAuth: true,
        });
    }

    async logout() {
        return this.request('/api/v1/system/auth/logout', {
            method: 'POST',
        });
    }

    async getCurrentUser() {
        return this.request('/api/v1/user/me');
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

if (typeof window !== 'undefined') {
    window.spaceAPI = spaceAPI;
}

export default spaceAPI;
export { SpaceAPI, SPACE_API_BASE };
