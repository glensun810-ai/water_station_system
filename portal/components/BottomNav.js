/**
 * BottomNav - 统一底部导航组件
 * 
 * 用于所有前端页面，确保用户可以快速返回首页
 * 
 * 使用方式：
 * <bottom-nav :active="activeNav"></bottom-nav>
 */

const BottomNav = {
    template: `
        <nav class="bottom-nav-container" v-cloak>
            <div class="bottom-nav">
                <a href="/portal/index.html" class="nav-item" :class="{ 'nav-active': active === 'home' }">
                    <span class="nav-icon">🏠</span>
                    <span class="nav-label">首页</span>
                </a>
                <a href="/portal/water/index.html" class="nav-item" :class="{ 'nav-active': active === 'water' }">
                    <span class="nav-icon">💧</span>
                    <span class="nav-label">水站</span>
                </a>
                <a href="/space-frontend/index.html" class="nav-item" :class="{ 'nav-active': active === 'space' }">
                    <span class="nav-icon">🏢</span>
                    <span class="nav-label">空间服务</span>
                </a>
                <a href="/portal/index.html#my-center" class="nav-item" :class="{ 'nav-active': active === 'my' }">
                    <span class="nav-icon">👤</span>
                    <span class="nav-label">我的</span>
                </a>
            </div>
        </nav>
    `,
    props: {
        active: {
            type: String,
            default: 'home'
        }
    }
};

if (typeof window !== 'undefined') {
    window.BottomNav = BottomNav;
}