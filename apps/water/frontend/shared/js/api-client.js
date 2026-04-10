/**
 * 统一API客户端 v2.0
 * 处理所有HTTP请求，统一认证、错误处理
 * 特性：边界处理、错误重试、请求取消
 */

class APIClient {
  constructor(baseURL = null) {
    this.baseURL = baseURL || this.getBaseURL();
    this.token = this.getToken();
    this.controllers = new Map();
    this.retryAttempts = 3;
    this.retryDelay = 1000;
  }

  getBaseURL() {
    try {
      const isLocalhost =
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1' ||
        window.location.hostname.startsWith('192.168');

      return isLocalhost ? 'http://localhost:8000/api' : window.location.origin + '/api';
    } catch (error) {
      console.error('Error getting base URL:', error);
      return '/api';
    }
  }

  getToken() {
    try {
      return localStorage.getItem('token') || localStorage.getItem('access_token') || null;
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  }

  setToken(token) {
    if (!token) {
      console.warn('Attempted to set null/undefined token');
      return;
    }
    this.token = token;
    try {
      localStorage.setItem('token', token);
      localStorage.setItem('access_token', token);
    } catch (error) {
      console.error('Error setting token:', error);
    }
  }

  clearToken() {
    this.token = null;
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      localStorage.removeItem('current_user');
    } catch (error) {
      console.error('Error clearing token:', error);
    }
  }

  async request(method, endpoint, options = {}) {
    if (!endpoint) {
      throw new Error('Endpoint is required');
    }

    const requestId = `${method}-${endpoint}-${Date.now()}`;

    const controller = new AbortController();
    this.controllers.set(requestId, controller);

    const url = `${this.baseURL}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config = {
      method,
      headers,
      signal: controller.signal,
      ...options
    };

    let lastError;

    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const response = await fetch(url, config);

        this.controllers.delete(requestId);

        if (response.status === 401) {
          this.clearToken();
          this.handleUnauthorized();
          throw new Error('未登录或登录已过期');
        }

        if (response.status === 403) {
          throw new Error('权限不足，需要管理员权限');
        }

        if (response.status === 404) {
          throw new Error('请求的资源不存在');
        }

        if (response.status === 422) {
          const errorData = await response.json().catch(() => ({}));
          const message = errorData.detail || '请求参数错误';
          throw new Error(message);
        }

        if (response.status >= 500) {
          throw new Error(`服务器错误 (${response.status})，请稍后重试`);
        }

        if (response.status >= 400) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || errorData.message || `请求失败 (${response.status})`);
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json();
          return data;
        }

        return response;
      } catch (error) {
        lastError = error;

        if (error.name === 'AbortError') {
          console.log('Request aborted:', endpoint);
          throw new Error('请求已取消');
        }

        if (error.message.includes('未登录') || error.message.includes('权限')) {
          throw error;
        }

        if (attempt < this.retryAttempts) {
          console.warn(`Request failed (attempt ${attempt}/${this.retryAttempts}):`, error.message);
          await this.sleep(this.retryDelay * attempt);
        }
      }
    }

    console.error(`API Error [${method} ${endpoint}]:`, lastError);

    if (typeof Toast !== 'undefined' && lastError) {
      Toast.error(lastError.message || '请求失败');
    }

    throw lastError;
  }

  handleUnauthorized() {
    if (typeof Toast !== 'undefined') {
      Toast.error('未登录或登录已过期');
    }
    setTimeout(() => {
      window.location.href = '/login.html';
    }, 1000);
  }

  cancel(requestId) {
    const controller = this.controllers.get(requestId);
    if (controller) {
      controller.abort();
      this.controllers.delete(requestId);
    }
  }

  cancelAll() {
    this.controllers.forEach(controller => controller.abort());
    this.controllers.clear();
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  get(endpoint, params = {}) {
    const filteredParams = {};
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        filteredParams[key] = params[key];
      }
    });

    const query = new URLSearchParams(filteredParams).toString();
    const url = query ? `${endpoint}?${query}` : endpoint;
    return this.request('GET', url);
  }

  post(endpoint, data = {}) {
    if (data === null || data === undefined) {
      data = {};
    }
    return this.request('POST', endpoint, { body: JSON.stringify(data) });
  }

  put(endpoint, data = {}) {
    if (data === null || data === undefined) {
      data = {};
    }
    return this.request('PUT', endpoint, { body: JSON.stringify(data) });
  }

  patch(endpoint, data = {}) {
    if (data === null || data === undefined) {
      data = {};
    }
    return this.request('PATCH', endpoint, { body: JSON.stringify(data) });
  }

  delete(endpoint) {
    return this.request('DELETE', endpoint);
  }

  upload(endpoint, formData) {
    if (!formData || !(formData instanceof FormData)) {
      throw new Error('FormData is required for upload');
    }

    const headers = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return this.request('POST', endpoint, {
      headers,
      body: formData
    });
  }
}

const api = new APIClient();

if (typeof window !== 'undefined') {
  window.api = api;
  window.APIClient = APIClient;
}