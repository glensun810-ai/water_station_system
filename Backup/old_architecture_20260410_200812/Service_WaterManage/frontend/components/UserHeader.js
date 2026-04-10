/**
 * UserHeader - 全局用户信息展示组件
 * 功能：
 * 1. 在所有页面右上角显示用户信息
 * 2. 提供用户菜单（个人中心、退出等）
 * 3. 跨页面自动同步用户状态
 * 4. 响应式设计
 */

const UserHeader = {
    template: `
        <header class="user-header" v-cloak>
            <div class="header-left">
                <a href="/portal/index.html" class="logo-link">
                    <span class="logo-icon">🏢</span>
                    <span class="logo-text">AI产业集群空间服务</span>
                </a>
            </div>

            <div class="header-right" v-if="userInfo">
                <div class="user-info" @click="toggleUserMenu">
                    <div class="user-avatar">{{ userInfo.avatar }}</div>
                    <div class="user-details">
                        <div class="user-name">{{ userInfo.name }}</div>
                        <div class="user-meta">{{ userInfo.department }}</div>
                    </div>
                    <div class="user-badge" v-if="userInfo.is_admin">
                        {{ userInfo.role === 'super_admin' ? '超管' : '管理员' }}
                    </div>
                    <span class="dropdown-icon">▼</span>
                </div>

                <!-- 用户菜单 -->
                <div class="user-menu" v-if="showUserMenu" @click.stop>
                    <a href="/portal/index.html" class="menu-item">
                        <span class="menu-icon">🏠</span>
                        <span class="menu-text">返回首页</span>
                    </a>
                    <a href="/water/admin.html" class="menu-item" v-if="userInfo.is_admin">
                        <span class="menu-icon">⚙️</span>
                        <span class="menu-text">管理后台</span>
                    </a>
                    <a href="/portal/settlement.html" class="menu-item">
                        <span class="menu-icon">💰</span>
                        <span class="menu-text">我的余额</span>
                    </a>
                    <a href="/water/change-password.html" class="menu-item">
                        <span class="menu-icon">🔐</span>
                        <span class="menu-text">修改密码</span>
                    </a>
                    <div class="menu-divider"></div>
                    <button class="menu-item menu-logout" @click="handleLogout">
                        <span class="menu-icon">🚪</span>
                        <span class="menu-text">退出登录</span>
                    </button>
                </div>
            </div>

            <div class="header-right" v-else>
                <a href="/water/login.html" class="login-btn">
                    登录
                </a>
            </div>
        </header>
    `,
    data() {
        return {
            userInfo: null,
            showUserMenu: false
        };
    },
    mounted() {
        this.loadUserInfo();
        // 监听localStorage变化
        window.addEventListener('storage', this.handleStorageChange);
        document.addEventListener('click', this.handleClickOutside);
    },
    beforeUnmount() {
        window.removeEventListener('storage', this.handleStorageChange);
        document.removeEventListener('click', this.handleClickOutside);
    },
    methods: {
        loadUserInfo() {
            try {
                const userInfo = localStorage.getItem('userInfo');
                if (userInfo) {
                    const parsed = JSON.parse(userInfo);
                    this.userInfo = {
                        ...parsed,
                        avatar: parsed.avatar || '👤',
                        is_admin: parsed.role === 'admin' || parsed.role === 'super_admin'
                    };
                    console.log('用户信息已加载:', this.userInfo);
                } else {
                    console.log('未找到用户信息');
                    this.userInfo = null;
                }
            } catch (e) {
                console.error('加载用户信息失败:', e);
                this.userInfo = null;
            }
        },
        handleStorageChange(event) {
            if (event.key === 'userInfo') {
                this.loadUserInfo();
            }
        },
        toggleUserMenu() {
            this.showUserMenu = !this.showUserMenu;
        },
        handleClickOutside(event) {
            if (!event.target.closest('.user-header')) {
                this.showUserMenu = false;
            }
        },
        handleLogout() {
            if (confirm('确定要退出登录吗？')) {
                localStorage.removeItem('token');
                localStorage.removeItem('userInfo');
                localStorage.removeItem('user_offices');
                window.location.href = '/portal/index.html';
            }
        }
    }
};

// 如果使用Vue 3，导出为组件
if (typeof Vue !== 'undefined' && Vue.createApp) {
    // Vue 3
    window.UserHeader = UserHeader;
} else {
    // Vue 2
    if (typeof Vue !== 'undefined') {
        Vue.component('user-header', UserHeader);
    }
}