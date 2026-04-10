// 更新后的登录API调用示例
const { createApp, ref, onMounted } = Vue;

createApp({
    setup() {
        // ... 其他代码保持不变 ...
        
        const handleLogin = async () => {
            loading.value = true;
            errorMessage.value = '';
            
            try {
                // 使用新的API服务
                const response = await ApiService.auth.login(username.value, password.value);
                
                if (response.data) {
                    localStorage.setItem('token', response.data.access_token);
                    
                    const userInfo = {
                        id: response.data.user_info.user_id,
                        name: response.data.user_info.username,
                        role: response.data.user_info.role,
                        roleName: response.data.user_info.role_name,
                        department: response.data.user_info.department || '',
                        avatar: getAvatarEmoji(response.data.user_info.role),
                        is_admin: ['super_admin', 'admin', 'office_admin'].includes(response.data.user_info.role)
                    };
                    localStorage.setItem('userInfo', JSON.stringify(userInfo));
                    
                    // 保存账户信息...
                    
                    // 跳转到首页
                    window.location.href = '/portal/index.html';
                }
            } catch (error) {
                console.error('登录失败:', error);
                errorMessage.value = error.message || '登录失败，请检查用户名和密码';
            } finally {
                loading.value = false;
            }
        };
        
        // 设置API基础URL（根据当前环境）
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port || (protocol === 'https:' ? '443' : '80');
        ApiService.setBaseURL(`${protocol}//${hostname}:${port}/api/v1`);
        
        // 从localStorage恢复token
        const token = localStorage.getItem('token');
        if (token) {
            ApiService.setAuthToken(token);
        }
        
        return {
            // ... 返回的响应式数据 ...
            handleLogin,
            // ... 其他方法 ...
        };
    }
}).mount('#app');