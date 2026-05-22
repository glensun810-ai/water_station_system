/**
 * Footer - 统一页脚组件
 *
 * 展示网站底部信息：服务入口、联系方式、版权、备案号
 */
const GlobalFooter = {
    template: `
        <footer class="global-footer" v-cloak>
            <div class="footer-content">
                <div class="footer-section">
                    <h4>服务导航</h4>
                    <a href="/portal/index.html">首页</a>
                    <a href="/space-frontend/index.html">空间服务</a>
                    <a href="/portal/water/index.html">用水服务</a>
                    <a href="/portal/membership-plans.html">会员套餐</a>
                </div>
                <div class="footer-section">
                    <h4>用户中心</h4>
                    <a href="/portal/orders.html">我的订单</a>
                    <a href="/portal/settlement.html">我的余额</a>
                    <a href="/portal/invoices.html">我的发票</a>
                    <a href="/portal/change-password.html">修改密码</a>
                </div>
                <div class="footer-section">
                    <h4>关于我们</h4>
                    <p>AI产业集群空间服务</p>
                    <p>进化湾 · 智慧空间管理平台</p>
                    <p>服务热线：400-XXX-XXXX</p>
                </div>
                <div class="footer-section">
                    <h4>帮助支持</h4>
                    <a href="/portal/help.html">使用指南</a>
                    <a href="/portal/faq.html">常见问题</a>
                    <a href="javascript:void(0)" @click="showContactDialog">联系客服</a>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; {{ currentYear }} 进化湾 AI产业集群空间服务 版权所有</p>
                <p v-if="icpNo">ICP备案号：{{ icpNo }}</p>
            </div>
        </footer>
    `,
    props: {
        icpNo: { type: String, default: '' }
    },
    data() {
        return {
            currentYear: new Date().getFullYear()
        };
    },
    methods: {
        showContactDialog() {
            alert('客服热线：400-XXX-XXXX\n工作时间：周一至周五 9:00-18:00');
        }
    }
};

if (typeof window !== 'undefined') {
    window.GlobalFooter = GlobalFooter;
}
