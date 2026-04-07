/**
 * GlobalHeader - 全局导航栏组件（优化版）
 * 
 * 设计理念：极简主义 + 角色驱动 + 渐进式信息披露
 * 
 * 功能：
 * 1. 面包屑导航
 * 2. 角色驱动的用户菜单
 * 3. 办公室切换（仅办公室管理员）
 * 4. 会员功能（外部用户）
 */

const GlobalHeader = {
    template: `
        <header class="global-header" v-cloak>
            <div class="header-left">
                <!-- Logo和面包屑 -->
                <div class="breadcrumb-nav">
                    <a href="/portal/index.html" class="breadcrumb-item breadcrumb-home">
                        <span class="breadcrumb-icon">🏢</span>
                        <span class="breadcrumb-text">AI产业集群空间服务</span>
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
                <transition name="menu-fade">
                    <div class="user-menu" v-if="showUserMenu" @click.stop>
                        <!-- 用户身份信息 -->
                        <div class="menu-user-info">
                            <div class="user-name">{{ userInfo.name }}</div>
                            <div class="user-role-label">{{ userRoleLabel }}</div>
                        </div>
                        
                        <div class="menu-divider"></div>

                        <!-- 超级管理员/系统管理员菜单 -->
                        <template v-if="isSuperOrAdmin">
                            <a href="/portal/admin/index.html" class="menu-item">
                                <span class="menu-icon">📊</span>
                                <span class="menu-text">管理后台</span>
                            </a>
                            <a href="/portal/admin/login-logs.html" class="menu-item">
                                <span class="menu-icon">📝</span>
                                <span class="menu-text">登录日志</span>
                            </a>
                            <div class="menu-divider"></div>
                        </template>

                        <!-- 办公室管理员菜单 -->
                        <template v-else-if="isOfficeAdmin">
                            <a href="/water/admin.html" class="menu-item">
                                <span class="menu-icon">💧</span>
                                <span class="menu-text">水站管理</span>
                            </a>
                            <a href="/meeting-frontend/admin.html" class="menu-item">
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
                            <a href="#" class="menu-item">
                                <span class="menu-icon">💳</span>
                                <span class="menu-text">充值/缴费</span>
                            </a>
                            <a href="#" class="menu-item">
                                <span class="menu-icon">🎫</span>
                                <span class="menu-text">我的优惠券</span>
                            </a>
                            <a href="#" class="menu-item" @click.prevent="showReferralDialog = true">
                                <span class="menu-icon">🎁</span>
                                <span class="menu-text">邀请好友</span>
                            </a>
                            <div class="menu-divider"></div>
                            <a href="#" class="menu-item">
                                <span class="menu-icon">📅</span>
                                <span class="menu-text">我的预约（会议室）</span>
                            </a>
                            <a href="#" class="menu-item">
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
                <a href="/Service_WaterManage/frontend/login.html" class="login-btn">
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
            managedOffices: [],  // 办公室管理员管理的办公室列表
            currentOfficeId: null,  // 当前选中的办公室ID
            newOffice: {
                name: '',
                location: '',
                description: ''
            }
        };
    },
    computed: {
        // 是否是超级管理员或系统管理员
        isSuperOrAdmin() {
            return this.userInfo?.role === '超级管理员' || 
                   (this.userInfo?.role === '管理员' && this.userInfo?.is_admin);
        },
        
        // 是否是办公室管理员
        isOfficeAdmin() {
            return this.userInfo?.role?.includes('管理员') && 
                   this.managedOffices.length > 0 &&
                   !this.isSuperOrAdmin;
        },
        
        // 是否是内部用户
        isInternalUser() {
            return this.userInfo?.department && 
                   !this.userInfo?.is_admin && 
                   this.managedOffices.length === 0;
        },
        
        // 是否是外部用户
        isExternalUser() {
            return !this.userInfo?.department && 
                   !this.userInfo?.is_admin && 
                   this.managedOffices.length === 0;
        },
        
        // 管理员徽章文本
        adminBadgeText() {
            if (this.userInfo?.role === '超级管理员') return '超管';
            if (this.userInfo?.role === '管理员') return '管理员';
            return '管理';
        },
        
        // 用户角色标签
        userRoleLabel() {
            if (this.isSuperOrAdmin) return this.userInfo.role;
            if (this.isOfficeAdmin) return '办公室管理员';
            if (this.isInternalUser) return `${this.userInfo.department} · 内部用户`;
            if (this.isExternalUser) return '外部用户';
            return '用户';
        },
        
        // 用户办公室标签
        userOfficeLabel() {
            if (this.isSuperOrAdmin) return '';
            if (this.isOfficeAdmin) return '办公室管理员';
            if (this.isInternalUser) return this.userInfo.department;
            if (this.isExternalUser) return '外部用户';
            return '';
        },
        
        // 当前办公室名称
        currentOfficeName() {
            const office = this.managedOffices.find(o => o.office_id === this.currentOfficeId);
            return office?.office_name || '选择办公室';
        }
    },
    mounted() {
        this.loadUserInfo();
        this.loadManagedOffices();
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
                        is_admin: parsed.role === '超级管理员' || 
                                 parsed.role === '管理员' || 
                                 parsed.role === 'admin' ||
                                 parsed.is_admin
                    };
                    console.log('用户信息已加载:', this.userInfo);
                } else {
                    this.userInfo = null;
                }
            } catch (e) {
                console.error('加载用户信息失败:', e);
                this.userInfo = null;
            }
        },
        
        async loadManagedOffices() {
            // 只有办公室管理员才加载管理的办公室
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
                const API_BASE = `${protocol}//${hostname}:${port}/api`;
                
                const response = await fetch(`${API_BASE}/office-admins/user/${this.userInfo.id}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    this.managedOffices = await response.json();
                    
                    // 从localStorage恢复当前选中的办公室
                    const savedOfficeId = localStorage.getItem('current_office_id');
                    if (savedOfficeId) {
                        this.currentOfficeId = parseInt(savedOfficeId);
                    } else if (this.managedOffices.length > 0) {
                        // 默认选中第一个办公室
                        this.currentOfficeId = this.managedOffices[0].office_id;
                    }
                    
                    console.log('管理的办公室已加载:', this.managedOffices);
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
            
            // 更新当前办公室
            this.currentOfficeId = office.office_id;
            localStorage.setItem('current_office_id', office.office_id);
            
            // 触发全局事件
            window.dispatchEvent(new CustomEvent('office-changed', {
                detail: {
                    officeId: office.office_id,
                    officeName: office.office_name
                }
            }));
            
            // 关闭菜单
            this.showOfficeMenu = false;
            
            // 显示提示
            this.showToast(`已切换到 ${office.office_name}`, 'success');
            
            // 刷新页面以更新数据
            setTimeout(() => {
                window.location.reload();
            }, 500);
        },
        
        showToast(message, type = 'info') {
            // 简单的toast提示
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
                animation: slideIn 0.3s ease;
            `;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease';
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
        
        handleClickOutside(event) {
            if (!event.target.closest('.global-header')) {
                this.closeAllMenus();
            }
        },
        
        handleLogout() {
            if (confirm('确定要退出登录吗？')) {
                localStorage.removeItem('token');
                localStorage.removeItem('userInfo');
                localStorage.removeItem('current_office_id');
                window.location.href = '/portal/index.html';
            }
        }
    }
};

// 导出组件
if (typeof window !== 'undefined') {
    window.GlobalHeader = GlobalHeader;
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);