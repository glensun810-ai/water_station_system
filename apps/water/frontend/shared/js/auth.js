/**
 * 认证工具
 * 处理用户认证、权限检查、登录状态管理
 */

const Auth = {
  getToken() {
    return localStorage.getItem('token') || localStorage.getItem('access_token');
  },

  setToken(token) {
    localStorage.setItem('token', token);
    localStorage.setItem('access_token', token);
  },

  getUser() {
    try {
      const userStr = localStorage.getItem('user') || localStorage.getItem('current_user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('current_user', JSON.stringify(user));
  },

  isLoggedIn() {
    return !!this.getToken() && !!this.getUser();
  },

  isAdmin() {
    const user = this.getUser();
    if (!user) return false;
    return user.role === 'admin' || user.role === 'super_admin';
  },

  isSuperAdmin() {
    const user = this.getUser();
    if (!user) return false;
    return user.role === 'super_admin';
  },

  hasPermission(requiredRole) {
    const user = this.getUser();
    if (!user) return false;

    const roleHierarchy = {
      staff: 1,
      admin: 2,
      super_admin: 3
    };

    const userLevel = roleHierarchy[user.role] || 0;
    const requiredLevel = roleHierarchy[requiredRole] || 0;

    return userLevel >= requiredLevel;
  },

  async checkAuth() {
    if (!this.isLoggedIn()) {
      return false;
    }

    try {
      const user = await api.get('/auth/me');
      this.setUser(user);
      return true;
    } catch (error) {
      this.clearAuth();
      return false;
    }
  },

  async login(username, password) {
    try {
      const response = await api.post('/auth/login', {
        name: username,
        password: password
      });

      this.setToken(response.access_token);
      this.setUser(response.user);

      return {
        success: true,
        user: response.user
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  },

  getLoginUrl() {
    const currentPath = window.location.pathname;

    // Portal管理后台登录页
    if (currentPath.startsWith('/portal/')) {
      return '/portal/admin/login.html';
    }

    // 水站管理后台登录页
    if (currentPath.startsWith('/frontend/') || currentPath.includes('/admin-')) {
      return '/frontend/login.html';
    }

    // 会议室管理后台登录页
    if (currentPath.startsWith('/meeting-frontend/')) {
      return '/meeting-frontend/login.html';
    }

    // 默认：水站登录页
    return '/frontend/login.html';
  },

  logout() {
    this.clearAuth();
    if (typeof Toast !== 'undefined') {
      Toast.success('已退出登录');
    }
    setTimeout(() => {
      window.location.href = this.getLoginUrl();
    }, 500);
  },

  clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('current_user');
  },

  requireAuth(redirectUrl = null) {
    if (!this.isLoggedIn()) {
      if (typeof Toast !== 'undefined') {
        Toast.warning('请先登录');
      }
      setTimeout(() => {
        window.location.href = redirectUrl || this.getLoginUrl();
      }, 500);
      return false;
    }
    return true;
  },

  requireAdmin(redirectUrl = null) {
    // 先检查是否登录
    if (!this.isLoggedIn()) {
      if (typeof Toast !== 'undefined') {
        Toast.warning('请先登录');
      }
      setTimeout(() => {
        window.location.href = redirectUrl || this.getLoginUrl();
      }, 500);
      return false;
    }

    // 再检查是否是管理员
    if (!this.isAdmin()) {
      if (typeof Toast !== 'undefined') {
        Toast.error('权限不足，需要管理员权限');
      }
      setTimeout(() => {
        window.location.href = redirectUrl || this.getLoginUrl();
      }, 1000);
      return false;
    }

    return true;
  },

  async changePassword(oldPassword, newPassword) {
    try {
      const user = this.getUser();
      await api.post(`/users/${user.id}/change-password`, {
        old_password: oldPassword,
        new_password: newPassword
      });

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
};

if (typeof window !== 'undefined') {
  window.Auth = Auth;
}