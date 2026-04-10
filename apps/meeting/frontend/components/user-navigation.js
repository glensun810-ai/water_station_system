// 用户端统一导航组件
// 使用方法：在所有用户端页面引入此组件

const UserNavigation = {
    template: `
        <nav class="bg-white shadow-sm border-b border-slate-200 sticky top-0 z-50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <!-- 左侧导航 - 固定不变 -->
                    <div class="flex items-center space-x-3">
                        <a href="../../portal/index.html" 
                           class="flex items-center space-x-1 px-3 py-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition text-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                            </svg>
                            <span>首页</span>
                        </a>
                        
                        <div class="h-6 w-px bg-slate-300"></div>
                        
                        <h1 class="text-lg font-bold text-slate-800">{{ currentPageTitle }}</h1>
                    </div>
                    
                    <!-- 右侧导航 - 固定不变 -->
                    <div class="flex items-center space-x-2">
                        <!-- 核心导航按钮 - 始终保持一致 -->
                        <a href="index.html" 
                           :class="currentPage === 'booking' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
                           class="px-4 py-2 rounded-lg text-sm font-medium transition">
                            📋 预约
                        </a>
                        
                        <a href="calendar.html" 
                           :class="currentPage === 'calendar' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
                           class="px-4 py-2 rounded-lg text-sm font-medium transition">
                            📅 日历
                        </a>
                        
                        <a href="my_bookings.html" 
                           :class="currentPage === 'bookings' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
                           class="px-4 py-2 rounded-lg text-sm font-medium transition">
                            📝 我的预约
                        </a>
                    </div>
                </div>
            </div>
        </nav>
    `,
    props: {
        currentPage: {
            type: String,
            required: true,
            validator: (value) => ['booking', 'calendar', 'bookings'].includes(value)
        }
    },
    computed: {
        currentPageTitle() {
            const titles = {
                'booking': '会议室预定',
                'calendar': '日历视图',
                'bookings': '我的预约'
            };
            return titles[this.currentPage];
        }
    }
};

// 导出组件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UserNavigation;
}