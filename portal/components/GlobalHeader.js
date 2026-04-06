/**
 * GlobalHeader - 全局导航栏组件
 * 功能：
 * 1. 面包屑导航（显示页面层级）
 * 2. 用户信息和下拉菜单
 * 3. 办公室设置功能
 * 4. 响应式设计
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
                <!-- 用户信息 -->
                <div class="user-info-container" @click="toggleUserMenu">
                    <div class="user-avatar">{{ userInfo.avatar || '👤' }}</div>
                    <div class="user-details">
                        <div class="user-name">{{ userInfo.name }}</div>
                        <div class="user-office" v-if="currentOffice">{{ currentOffice }}</div>
                    </div>
                    <div class="user-badge" v-if="userInfo.is_admin">
                        {{ userInfo.role === '超级管理员' ? '超管' : '管理员' }}
                    </div>
                    <span class="dropdown-icon" :class="{ 'dropdown-open': showUserMenu }">▼</span>
                </div>

                <!-- 用户菜单 -->
                <transition name="menu-fade">
                    <div class="user-menu" v-if="showUserMenu" @click.stop>
                        <!-- 办公室设置 -->
                        <div class="menu-group">
                            <div class="menu-group-title">
                                <span class="menu-icon">🏢</span>
                                <span class="menu-text">我的办公室</span>
                            </div>
                            <div class="office-selector">
                                <div class="office-item" 
                                     v-for="office in offices" 
                                     :key="office.id"
                                     :class="{ 'office-selected': selectedOfficeId === office.id }"
                                     @click="selectOffice(office)">
                                    <span class="office-check" v-if="selectedOfficeId === office.id">✓</span>
                                    <span class="office-name">{{ office.name }}</span>
                                    <span class="office-location">{{ office.location }}</span>
                                </div>
                                <button class="office-add-btn" @click="showAddOfficeDialog = true">
                                    <span class="office-add-icon">+</span>
                                    <span class="office-add-text">添加办公室</span>
                                </button>
                            </div>
                        </div>
                        
                        <div class="menu-divider"></div>
                        
                        <!-- 常用功能 -->
                        <a href="/portal/index.html" class="menu-item">
                            <span class="menu-icon">🏠</span>
                            <span class="menu-text">返回首页</span>
                        </a>
                        <a href="/portal/settlement.html" class="menu-item">
                            <span class="menu-icon">💰</span>
                            <span class="menu-text">我的余额</span>
                        </a>
                        <a href="/water/change-password.html" class="menu-item">
                            <span class="menu-icon">🔐</span>
                            <span class="menu-text">修改密码</span>
                        </a>
                        
                        <!-- 管理员菜单 -->
                        <template v-if="userInfo.is_admin">
                            <div class="menu-divider"></div>
                            <div class="menu-group-title">
                                <span class="menu-icon">⚙️</span>
                                <span class="menu-text">管理后台</span>
                            </div>
                            <a href="/water/admin.html" class="menu-item">
                                <span class="menu-icon">💧</span>
                                <span class="menu-text">水站管理</span>
                            </a>
                            <a href="/meeting-frontend/admin.html" class="menu-item">
                                <span class="menu-icon">📅</span>
                                <span class="menu-text">会议室管理</span>
                            </a>
                            <a href="/portal/admin/index.html" class="menu-item">
                                <span class="menu-icon">📊</span>
                                <span class="menu-text">统一管理</span>
                            </a>
                        </template>
                        
                        <div class="menu-divider"></div>
                        
                        <!-- 退出登录 -->
                        <button class="menu-item menu-logout" @click="handleLogout">
                            <span class="menu-icon">🚪</span>
                            <span class="menu-text">退出登录</span>
                        </button>
                    </div>
                </transition>
            </div>

            <div class="header-right" v-else>
                <a href="/water/login.html" class="login-btn">
                    登录
                </a>
            </div>

            <!-- 办公室设置对话框 -->
            <transition name="dialog-fade">
                <div class="office-dialog-overlay" v-if="showAddOfficeDialog" @click="showAddOfficeDialog = false">
                    <div class="office-dialog" @click.stop>
                        <div class="dialog-header">
                            <h3 class="dialog-title">添加办公室</h3>
                            <button class="dialog-close" @click="showAddOfficeDialog = false">✕</button>
                        </div>
                        <div class="dialog-body">
                            <div class="form-group">
                                <label class="form-label">办公室名称</label>
                                <input type="text" 
                                       class="form-input" 
                                       v-model="newOffice.name"
                                       placeholder="例如：总部大楼3层办公室"
                                       required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">办公室位置</label>
                                <input type="text" 
                                       class="form-input" 
                                       v-model="newOffice.location"
                                       placeholder="例如：3层305室"
                                       required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">备注说明</label>
                                <textarea class="form-input form-textarea" 
                                          v-model="newOffice.description"
                                          placeholder="可选填写"
                                          rows="3"></textarea>
                            </div>
                        </div>
                        <div class="dialog-footer">
                            <button class="btn btn-secondary" @click="showAddOfficeDialog = false">取消</button>
                            <button class="btn btn-primary" @click="addNewOffice" :disabled="!newOffice.name || !newOffice.location">
                                添加
                            </button>
                        </div>
                    </div>
                </div>
            </transition>
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
            offices: [],
            selectedOfficeId: null,
            currentOffice: '',
            showAddOfficeDialog: false,
            newOffice: {
                name: '',
                location: '',
                description: ''
            }
        };
    },
    mounted() {
        this.loadUserInfo();
        this.loadOffices();
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
                        is_admin: parsed.role === '超级管理员' || parsed.role === 'admin' || parsed.is_admin
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
        loadOffices() {
            try {
                const officesData = localStorage.getItem('user_offices');
                if (officesData) {
                    const parsed = JSON.parse(officesData);
                    this.offices = parsed.offices || [];
                    this.selectedOfficeId = parsed.selectedOfficeId || null;
                    this.updateCurrentOffice();
                } else {
                    // 初始化默认办公室
                    this.offices = [
                        { id: 1, name: '总部办公室', location: '3层305室', description: '默认办公室' }
                    ];
                    this.selectedOfficeId = 1;
                    this.saveOffices();
                    this.updateCurrentOffice();
                }
            } catch (e) {
                console.error('加载办公室信息失败:', e);
            }
        },
        updateCurrentOffice() {
            const selectedOffice = this.offices.find(o => o.id === this.selectedOfficeId);
            this.currentOffice = selectedOffice ? selectedOffice.name : '';
        },
        selectOffice(office) {
            this.selectedOfficeId = office.id;
            this.saveOffices();
            this.updateCurrentOffice();
            this.showUserMenu = false;
            this.$emit('office-changed', office);
        },
        addNewOffice() {
            const newId = Math.max(...this.offices.map(o => o.id), 0) + 1;
            const office = {
                id: newId,
                name: this.newOffice.name,
                location: this.newOffice.location,
                description: this.newOffice.description || ''
            };
            this.offices.push(office);
            this.selectedOfficeId = newId;
            this.saveOffices();
            this.updateCurrentOffice();
            
            // 重置表单
            this.newOffice = {
                name: '',
                location: '',
                description: ''
            };
            this.showAddOfficeDialog = false;
            this.showUserMenu = false;
            this.$emit('office-added', office);
        },
        saveOffices() {
            const data = {
                offices: this.offices,
                selectedOfficeId: this.selectedOfficeId
            };
            localStorage.setItem('user_offices', JSON.stringify(data));
        },
        handleStorageChange(event) {
            if (event.key === 'userInfo') {
                this.loadUserInfo();
            } else if (event.key === 'user_offices') {
                this.loadOffices();
            }
        },
        toggleUserMenu() {
            this.showUserMenu = !this.showUserMenu;
        },
        handleClickOutside(event) {
            if (!event.target.closest('.global-header')) {
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

// 导出组件
if (typeof window !== 'undefined') {
    window.GlobalHeader = GlobalHeader;
}