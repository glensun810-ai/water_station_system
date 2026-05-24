/**
 * 统一认证 fetch 封装
 * 自动注入 JWT token，401 时自动跳转登录页
 *
 * 使用方式：直接替换 fetch() 调用
 *   const res = await authFetch('/api/v1/offices');
 *   const data = await res.json();
 */

(function () {
  const TOKEN_KEY = 'token';
  const ALT_TOKEN_KEYS = ['admin_token'];
  const LOGIN_URL = '/portal/admin/login.html';

  function getToken() {
    let token = localStorage.getItem(TOKEN_KEY);
    if (token) return token;
    for (const key of ALT_TOKEN_KEYS) {
      token = localStorage.getItem(key);
      if (token) return token;
    }
    return null;
  }

  function authFetch(url, options = {}) {
    const token = getToken();
    const headers = { ...(options.headers || {}) };

    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }

    return fetch(url, { ...options, headers }).then(function (response) {
      if (response.status === 401 && token) {
        // Token 过期或不合法 → 清除并跳转登录
        localStorage.removeItem(TOKEN_KEY);
        ALT_TOKEN_KEYS.forEach(function (k) { localStorage.removeItem(k); });
        localStorage.removeItem('userInfo');
        if (window.location.pathname !== LOGIN_URL) {
          window.location.href = LOGIN_URL;
        }
      }
      return response;
    });
  }

  window.authFetch = authFetch;
})();
