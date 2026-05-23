/**
 * GlobalHeader - 全局导航栏组件 v2.0
 *
 * 设计理念：极简主义 + 角色驱动 + 渐进式信息披露 + 玻璃质感
 *
 * Props:
 *   breadcrumbs - 面包屑数组 [{text, url, icon}]
 *   backUrl      - 返回按钮链接
 *   backText     - 返回按钮文本，默认"返回"
 *   transparent  - 透明背景模式，滚动后渐变显现
 *
 * Slots:
 *   nav-actions  - 页面操作区（标签页、按钮等）
 */

const GlobalHeader = {
    template: `
        <header class="global-header" :class="{ 'header-transparent': transparent && !isScrolled, 'header-scrolled': isScrolled }" v-cloak>
            <div class="header-left">
                <!-- 返回按钮 -->
                <a v-if="backUrl" :href="backUrl" class="header-back-btn" :title="backText || '返回'">
                    <svg class="back-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="15 18 9 12 15 6"></polyline>
                    </svg>
                    <span class="back-text" v-if="!isMobile">{{ backText || '返回' }}</span>
                </a>

                <!-- Logo和面包屑 -->
                <div class="breadcrumb-nav">
                    <a href="/portal/index.html" class="breadcrumb-item breadcrumb-home">
                        <img src="/portal/assets/images/logo.png" class="breadcrumb-logo" alt="进化湾" onerror="this.style.display='none';this.nextElementSibling.style.display='inline-block';">
                        <span class="breadcrumb-icon" style="display:none">🏢</span>
                        <span class="breadcrumb-text">进化湾</span>
                    </a>
                    <template v-for="(item, index) in breadcrumbs">
                        <span class="breadcrumb-separator">/</span>
                        <a :href="item.url" class="breadcrumb-item" :class="{ 'breadcrumb-active': index === breadcrumbs.length - 1 }">
                            <span class="breadcrumb-icon" v-if="item.icon">{{ item.icon }}</span>
                            <span class="breadcrumb-text">{{ item.text }}</span>
                        </a>
                    </template>
                </div>
            </div>

            <!-- 页面操作区（slot） -->
            <div class="header-center" v-if="$slots['nav-actions']">
                <slot name="nav-actions"></slot>
            </div>

            <div class="header-right" v-if="userInfo">
                <!-- 办公室切换（仅办公室管理员） -->
                <div v-if="isOfficeAdmin && managedOffices.length > 0" class="office-switcher" @click="toggleOfficeMenu">
                    <span class="office-name">{{ currentOfficeName }}</span>
                    <span class="dropdown-icon" :class="{ 'dropdown-open': showOfficeMenu }">▼</span>
                </div>

                <!-- 用户信息 -->
                <div class="user-info-container" @click="toggleUserMenu">
                    <div class="user-avatar">{{ userInfo.avatar || '👤' }}</div>
                    <div class="user-details">
                        <div class="user-name">{{ userInfo.name }}</div>
                        <div class="user-office" v-if="userOfficeLabel">{{ userOfficeLabel }}</div>
                    </div>
                    <div class="user-badge external" v-if="isExternalUser">外部用户</div>
                    <div class="user-badge admin" v-else-if="userInfo.is_admin">{{ adminBadgeText }}</div>
                    <span class="dropdown-icon" :class="{ 'dropdown-open': showUserMenu }">▼</span>
                </div>

                <!-- 办公室切换下拉菜单 -->
                <transition name="menu-fade">
                    <div class="office-menu" v-if="showOfficeMenu" @click.stop>
                        <div class="menu-section">
                            <div
                                v-for="office in managedOffices"
                                :key="office.office_id"
                                class="office-menu-item"
                                :class="{ 'office-active': currentOfficeId === office.office_id }"
                                @click="switchOffice(office)">
                                <div class="office-radio">
                                    <span v-if="currentOfficeId === office.office_id" class="radio-checked">✓</span>
                                </div>
                                <div class="office-details">
                                    <div class="office-name">{{ office.office_name }}</div>
                                    <div class="office-location">3层305室</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </transition>

                <!-- 用户下拉菜单 -->
                <transition name="header-menu-trans">
                    <div class="user-menu" :class="{ 'mobile-sheet': isMobile }" v-if="showUserMenu" @click.stop>
                        <!-- 移动端拖拽手柄 -->
                        <div class="sheet-handle" v-if="isMobile"></div>

                        <!-- 用户身份信息 -->
                        <div class="menu-user-info">
                            <div class="user-name">{{ userInfo.name }}</div>
                            <div class="user-role-label">{{ userRoleLabel }}</div>
                        </div>

                        <div class="menu-divider"></div>

                        <!-- 超级管理员/系统管理员菜单 -->
                        <template v-if="isSuperOrAdmin">
                            <a href="/portal/index.html#system-management-section" class="menu-item">
                                <span class="menu-icon">📊</span>
                                <span class="menu-text">管理中心</span>
                            </a>
                            <a href="/portal/admin/login-logs.html" class="menu-item">
                                <span class="menu-icon">📝</span>
                                <span class="menu-text">登录日志</span>
                            </a>
                            <div class="menu-divider"></div>
                        </template>

                        <!-- 办公室管理员菜单 -->
                        <template v-else-if="isOfficeAdmin">
                            <a href="/portal/admin/water/dashboard.html" class="menu-item">
                                <span class="menu-icon">💧</span>
                                <span class="menu-text">水站管理</span>
                            </a>
                            <a href="/portal/admin/meeting/bookings.html" class="menu-item">
                                <span class="menu-icon">📅</span>
                                <span class="menu-text">会议室管理</span>
                            </a>
                            <div class="menu-divider"></div>
                        </template>

                        <!-- 内部用户菜单 -->
                        <template v-else-if="isInternalUser">
                            <a href="/portal/settlement.html" class="menu-item">
                                <span class="menu-icon">💰</span>
                                <span class="menu-text">我的余额</span>
                            </a>
                            <a href="/space-frontend/my-bookings.html" class="menu-item">
                                <span class="menu-icon">📅</span>
                                <span class="menu-text">我的预约</span>
                            </a>
                            <a href="#" class="menu-item" @click.prevent="showReferralDialog = true">
                                <span class="menu-icon">🎁</span>
                                <span class="menu-text">分享得权益</span>
                            </a>
                            <div class="menu-divider"></div>
                        </template>

                        <!-- 外部用户菜单 -->
                        <template v-else-if="isExternalUser">
                            <a href="#" class="menu-item highlight" @click.prevent="showMembershipDialog = true">
                                <span class="menu-icon">👑</span>
                                <span class="menu-text">会员中心</span>
                                <span class="menu-badge">开通</span>
                            </a>
                            <a href="/portal/balance.html" class="menu-item">
                                <span class="menu-icon">💳</span>
                                <span class="menu-text">充值/缴费</span>
                            </a>
                            <a href="/water/user-coupons.html" class="menu-item">
                                <span class="menu-icon">🎫</span>
                                <span class="menu-text">我的优惠券</span>
                            </a>
                            <a href="#" class="menu-item" @click.prevent="showReferralDialog = true">
                                <span class="menu-icon">🎁</span>
                                <span class="menu-text">邀请好友</span>
                            </a>
                            <div class="menu-divider"></div>
                            <a href="/meeting-frontend/my_bookings.html" class="menu-item">
                                <span class="menu-icon">📅</span>
                                <span class="menu-text">我的预约（会议室）</span>
                            </a>
                            <a href="/portal/orders.html" class="menu-item">
                                <span class="menu-icon">📋</span>
                                <span class="menu-text">我的订单</span>
                            </a>
                            <div class="menu-divider"></div>
                        </template>

                        <!-- 通用菜单项 -->
                        <a href="/portal/change-password.html" class="menu-item">
                            <span class="menu-icon">🔐</span>
                            <span class="menu-text">修改密码</span>
                        </a>
                        <button class="menu-item menu-logout" @click="handleLogout">
                            <span class="menu-icon">🚪</span>
                            <span class="menu-text">退出登录</span>
                        </button>
                    </div>
                </transition>
            </div>

            <div class="header-right" v-else>
                <a href="/portal/admin/login.html" class="login-btn">
                    登录
                </a>
            </div>

            <!-- 点击外部关闭菜单 -->
            <div v-if="showUserMenu || showOfficeMenu" class="menu-backdrop" @click="closeAllMenus"></div>
        </header>
    `,
    props: {
        breadcrumbs: {
            type: Array,
            default: () => []
        },
        backUrl: {
            type: String,
            default: ''
        },
        backText: {
            type: String,
            default: '返回'
        },
        transparent: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            userInfo: null,
            showUserMenu: false,
            showOfficeMenu: false,
            showAddOfficeDialog: false,
            showReferralDialog: false,
            showMembershipDialog: false,
            managedOffices: [],
            currentOfficeId: null,
            isScrolled: false,
            isMobile: false,
            newOffice: {
                name: '',
                location: '',
                description: ''
            }
        };
    },
    computed: {
        isSuperOrAdmin() {
            return this.userInfo?.role === '超级管理员' ||
                   this.userInfo?.role === 'super_admin' ||
                   this.userInfo?.role === '管理员' ||
                   (this.userInfo?.role === 'admin' && this.userInfo?.is_admin);
        },

        isOfficeAdmin() {
            return (this.userInfo?.role === 'office_admin' ||
                    this.userInfo?.role?.includes('办公室管理员')) &&
                    this.managedOffices.length > 0 &&
                    !this.isSuperOrAdmin;
        },

        isInternalUser() {
            return this.userInfo?.user_type === 'internal' &&
                   !this.isSuperOrAdmin &&
                   !this.isOfficeAdmin;
        },

        isExternalUser() {
            if (this.isSuperOrAdmin) return false;
            if (this.isOfficeAdmin) return false;
            if (this.isInternalUser) return false;
            return this.userInfo?.user_type === 'external';
        },

        adminBadgeText() {
            if (this.userInfo?.role === '超级管理员' || this.userInfo?.role === 'super_admin') return '超管';
            if (this.userInfo?.role === '管理员' || this.userInfo?.role === 'admin') return '管理员';
            if (this.userInfo?.role === 'office_admin') return '办管';
            return '管理';
        },

        userRoleLabel() {
            if (this.userInfo?.role === 'super_admin' || this.userInfo?.role === '超级管理员') return '超级管理员';
            if (this.userInfo?.role === 'admin' || this.userInfo?.role === '管理员') return '系统管理员';
            if (this.isOfficeAdmin) return '办公室管理员';
            if (this.isInternalUser) return `${this.userInfo.department} · 内部用户`;
            if (this.isExternalUser) return '外部用户';
            return '用户';
        },

        userOfficeLabel() {
            if (this.isSuperOrAdmin) return '';
            if (this.isOfficeAdmin) return '办公室管理员';
            if (this.isInternalUser) return this.userInfo.department;
            if (this.isExternalUser) return '外部用户';
            return '';
        },

        currentOfficeName() {
            const office = this.managedOffices.find(o => o.office_id === this.currentOfficeId);
            return office?.office_name || '选择办公室';
        }
    },
    mounted() {
        this.loadUserInfo();
        this.loadManagedOffices();
        this.checkMobile();
        window.addEventListener('storage', this.handleStorageChange);
        window.addEventListener('resize', this.checkMobile);
        document.addEventListener('click', this.handleClickOutside);

        if (this.transparent) {
            window.addEventListener('scroll', this.handleScroll, { passive: true });
        }
    },
    beforeUnmount() {
        window.removeEventListener('storage', this.handleStorageChange);
        window.removeEventListener('resize', this.checkMobile);
        document.removeEventListener('click', this.handleClickOutside);
        window.removeEventListener('scroll', this.handleScroll);
    },
    methods: {
        checkMobile() {
            this.isMobile = window.innerWidth < 768;
        },

        handleScroll() {
            this.isScrolled = window.scrollY > 10;
        },

        loadUserInfo() {
            try {
                const userInfo = localStorage.getItem('userInfo');
                if (userInfo) {
                    const parsed = JSON.parse(userInfo);
                    this.userInfo = {
                        ...parsed,
                        avatar: parsed.avatar || '👤',
                        is_admin: parsed.role === '超级管理员' ||
                                 parsed.role === 'super_admin' ||
                                 parsed.role === '管理员' ||
                                 parsed.role === 'admin' ||
                                 parsed.role === 'office_admin' ||
                                 parsed.is_admin
                    };
                } else {
                    this.userInfo = null;
                }
            } catch (e) {
                console.error('加载用户信息失败:', e);
                this.userInfo = null;
            }
        },

        async loadManagedOffices() {
            if (!this.userInfo || this.isSuperOrAdmin || !this.userInfo.id) {
                this.managedOffices = [];
                return;
            }

            try {
                const token = localStorage.getItem('token');
                if (!token) {
                    this.managedOffices = [];
                    return;
                }

                const protocol = window.location.protocol;
                const hostname = window.location.hostname;
                const port = window.location.port || (protocol === 'https:' ? '443' : '80');
                const API_BASE = `${protocol}//${hostname}:${port}/api/v1`;

                const response = await fetch(`${API_BASE}/offices/office-admins/user/${this.userInfo.id}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    this.managedOffices = await response.json();

                    const savedOfficeId = localStorage.getItem('current_office_id');
                    if (savedOfficeId) {
                        this.currentOfficeId = parseInt(savedOfficeId);
                    } else if (this.managedOffices.length > 0) {
                        this.currentOfficeId = this.managedOffices[0].office_id;
                    }
                } else {
                    this.managedOffices = [];
                }
            } catch (e) {
                console.error('加载管理的办公室失败:', e);
                this.managedOffices = [];
            }
        },

        switchOffice(office) {
            if (this.currentOfficeId === office.office_id) {
                this.showOfficeMenu = false;
                return;
            }

            this.currentOfficeId = office.office_id;
            localStorage.setItem('current_office_id', office.office_id);

            window.dispatchEvent(new CustomEvent('office-changed', {
                detail: {
                    officeId: office.office_id,
                    officeName: office.office_name
                }
            }));

            this.showOfficeMenu = false;
            this.showToast(`已切换到 ${office.office_name}`, 'success');

            setTimeout(() => {
                window.location.reload();
            }, 500);
        },

        showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                padding: 12px 20px;
                background: ${type === 'success' ? '#10B981' : '#3B82F6'};
                color: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 10000;
                animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            `;
            document.body.appendChild(toast);

            setTimeout(() => {
                toast.style.animation = 'slideOutRight 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                setTimeout(() => toast.remove(), 300);
            }, 2000);
        },

        handleStorageChange(event) {
            if (event.key === 'userInfo') {
                this.loadUserInfo();
                this.loadManagedOffices();
            }
        },

        toggleUserMenu() {
            this.showUserMenu = !this.showUserMenu;
            this.showOfficeMenu = false;
        },

        toggleOfficeMenu() {
            this.showOfficeMenu = !this.showOfficeMenu;
            this.showUserMenu = false;
        },

        closeAllMenus() {
            this.showUserMenu = false;
            this.showOfficeMenu = false;
        },

        showComingSoon(feature) {
            alert(feature + '功能开发中，敬请期待！');
        },

        handleClickOutside(event) {
            if (!event.target.closest('.global-header')) {
                this.closeAllMenus();
            }
        },

        handleLogout() {
            if (confirm('确定要退出登录吗？')) {
                localStorage.removeItem('token');
                localStorage.removeItem('userInfo');
                localStorage.removeItem('user_id');
                localStorage.removeItem('current_office_id');
                window.location.href = '/portal/admin/login.html';
            }
        }
    }
};

if (typeof window !== 'undefined') {
    window.GlobalHeader = GlobalHeader;
}

// 注入动画关键帧
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
