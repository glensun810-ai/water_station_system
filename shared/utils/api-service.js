/**
 * AI产业集群空间服务系统API服务模块
 * 
 * 版本: 1.0
 * 作者: 系统架构团队  
 * 日期: 2026-04-09
 */

import { apiClient } from './api-client.js';

// ==================== 用户认证服务 ====================
const AuthService = {
  /**
   * 用户登录
   * @param {string} username - 用户名
   * @param {string} password - 密码
   * @returns {Promise} 登录结果
   */
  async login(username, password) {
    const response = await apiClient.post('/auth/login', {
      username,
      password
    });
    
    // 设置认证token
    if (response.data?.access_token) {
      apiClient.setAuthToken(response.data.access_token);
    }
    
    return response;
  },

  /**
   * 用户登出
   * @returns {Promise}
   */
  async logout() {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // 登出失败不影响本地状态清理
      console.warn('Logout API failed:', error);
    } finally {
      apiClient.clearAuthToken();
    }
  },

  /**
   * 刷新token
   * @returns {Promise}
   */
  async refreshToken() {
    try {
      const response = await apiClient.post('/auth/refresh');
      if (response.data?.access_token) {
        apiClient.setAuthToken(response.data.access_token);
        return response.data;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  },

  /**
   * 获取当前用户信息
   * @returns {Promise}
   */
  async getCurrentUser() {
    return await apiClient.get('/system/users/me');
  }
};

// ==================== 水站服务 ====================
const WaterService = {
  /**
   * 获取产品列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getProducts(params = {}) {
    return await apiClient.get('/water/products', params);
  },

  /**
   * 获取用户余额
   * @param {number} userId - 用户ID
   * @returns {Promise}
   */
  async getUserBalance(userId) {
    return await apiClient.get(`/water/balance/${userId}`);
  },

  /**
   * 创建领水记录
   * @param {Object} pickupData - 领水数据
   * @returns {Promise}
   */
  async createPickup(pickupData) {
    return await apiClient.post('/water/pickup', pickupData);
  },

  /**
   * 获取领水记录
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getPickups(params = {}) {
    return await apiClient.get('/water/pickups', params);
  },

  /**
   * 申请结算
   * @param {Object} settlementData - 结算数据
   * @returns {Promise}
   */
  async applySettlement(settlementData) {
    return await apiClient.post('/water/settlement/apply', settlementData);
  },

  /**
   * 获取结算列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getSettlements(params = {}) {
    return await apiClient.get('/water/settlement', params);
  },

  /**
   * 确认结算
   * @param {number} settlementId - 结算ID
   * @returns {Promise}
   */
  async confirmSettlement(settlementId) {
    return await apiClient.post(`/water/settlement/${settlementId}/confirm`);
  }
};

// ==================== 会议室服务 ====================
const MeetingService = {
  /**
   * 获取会议室列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getRooms(params = {}) {
    return await apiClient.get('/meeting/rooms', params);
  },

  /**
   * 创建预约
   * @param {Object} bookingData - 预约数据
   * @returns {Promise}
   */
  async createBooking(bookingData) {
    return await apiClient.post('/meeting/bookings', bookingData);
  },

  /**
   * 获取预约列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getBookings(params = {}) {
    return await apiClient.get('/meeting/bookings', params);
  },

  /**
   * 审批预约
   * @param {number} bookingId - 预约ID
   * @param {boolean} approved - 是否批准
   * @returns {Promise}
   */
  async approveBooking(bookingId, approved = true) {
    const endpoint = approved ? '/approve' : '/reject';
    return await apiClient.post(`/meeting/bookings/${bookingId}${endpoint}`);
  },

  /**
   * 取消预约
   * @param {number} bookingId - 预约ID
   * @returns {Promise}
   */
  async cancelBooking(bookingId) {
    return await apiClient.delete(`/meeting/bookings/${bookingId}`);
  }
};

// ==================== 统一账户服务 ====================
const UnifiedService = {
  /**
   * 获取统一账户信息
   * @param {number} userId - 用户ID
   * @returns {Promise}
   */
  async getUnifiedAccount(userId) {
    return await apiClient.get(`/unified/account/${userId}`);
  },

  /**
   * 初始化账户
   * @param {number} userId - 用户ID
   * @returns {Promise}
   */
  async initializeAccount(userId) {
    return await apiClient.post(`/unified/account/${userId}/initialize`);
  },

  /**
   * 调整钱包余额
   * @param {Object} balanceData - 余额调整数据
   * @returns {Promise}
   */
  async adjustWalletBalance(balanceData) {
    return await apiClient.post('/unified/wallet/balance', balanceData);
  },

  /**
   * 记录领取
   * @param {Object} pickupData - 领取数据
   * @returns {Promise}
   */
  async recordPickup(pickupData) {
    return await apiClient.post('/unified/pickup/record', pickupData);
  }
};

// ==================== 系统管理服务 ====================
const SystemService = {
  /**
   * 获取用户列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getUsers(params = {}) {
    return await apiClient.get('/system/users', params);
  },

  /**
   * 创建用户
   * @param {Object} userData - 用户数据
   * @returns {Promise}
   */
  async createUser(userData) {
    return await apiClient.post('/system/users', userData);
  },

  /**
   * 更新用户
   * @param {number} userId - 用户ID
   * @param {Object} userData - 更新数据
   * @returns {Promise}
   */
  async updateUser(userId, userData) {
    return await apiClient.put(`/system/users/${userId}`, userData);
  },

  /**
   * 删除用户
   * @param {number} userId - 用户ID
   * @returns {Promise}
   */
  async deleteUser(userId) {
    return await apiClient.delete(`/system/users/${userId}`);
  },

  /**
   * 获取办公室列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getOffices(params = {}) {
    return await apiClient.get('/system/offices', params);
  },

  /**
   * 创建办公室
   * @param {Object} officeData - 办公室数据
   * @returns {Promise}
   */
  async createOffice(officeData) {
    return await apiClient.post('/system/offices', officeData);
  },

  /**
   * 获取系统统计信息
   * @returns {Promise}
   */
  async getSystemStats() {
    return await apiClient.get('/system/stats');
  },

  /**
   * 获取操作日志
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  async getAuditLogs(params = {}) {
    return await apiClient.get('/system/audit-logs', params);
  }
};

// ==================== 工具函数 ====================
const ApiService = {
  // 服务实例
  auth: AuthService,
  water: WaterService,
  meeting: MeetingService,
  unified: UnifiedService,
  system: SystemService,
  
  /**
   * 设置API基础URL
   * @param {string} baseURL - 基础URL
   */
  setBaseURL(baseURL) {
    apiClient.baseURL = baseURL;
  },
  
  /**
   * 设置认证token
   * @param {string} token - JWT token
   */
  setAuthToken(token) {
    apiClient.setAuthToken(token);
  },
  
  /**
   * 清除认证token
   */
  clearAuthToken() {
    apiClient.clearAuthToken();
  },
  
  /**
   * 批量请求
   * @param {Array} requests - 请求配置数组
   * @returns {Promise}
   */
  batch(requests) {
    return apiClient.batch(requests);
  }
};

// 全局错误处理
apiClient.config.errorHandler = (error) => {
  if (error instanceof APIError) {
    switch (error.statusCode) {
      case 401:
        // 未认证，重定向到登录页
        window.location.href = '/portal/admin/login.html';
        break;
      case 403:
        // 权限不足，显示错误提示
        console.error('Permission denied:', error.message);
        break;
      case 404:
        // 资源不存在
        console.error('Resource not found:', error.message);
        break;
      case 500:
        // 服务器错误
        console.error('Server error:', error.message);
        break;
      default:
        console.error('API error:', error.message);
    }
  }
};

export default ApiService;