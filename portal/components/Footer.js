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
                    <p>服务热线：18718052868</p>
                </div>
                <div class="footer-section">
                    <h4>帮助支持</h4>
                    <a href="/portal/help.html">使用指南</a>
                    <a href="/portal/faq.html">常见问题</a>
                    <a href="javascript:void(0)" @click="showContactDialog">联系客服</a>
                </div>
            </div>
            <div class="footer-bottom">
                <p class="footer-company">&copy; {{ currentYear }} {{ companyName }} 版权所有</p>
                <div class="footer-beian">
                    <a v-if="gonganBeian"
                       :href="'https://beian.mps.gov.cn/#/query/webSearch?code=' + gonganBeianCode"
                       target="_blank"
                       rel="noopener noreferrer"
                       class="beian-link">
                        <svg class="beian-icon" viewBox="0 0 20 20" width="16" height="16" fill="none">
                            <rect x="3" y="3" width="14" height="14" rx="2" fill="#3B82F6"/>
                            <path d="M6 10.5L8.5 13L14 7.5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        {{ gonganBeian }}
                    </a>
                    <a v-if="icpNo"
                       href="https://beian.miit.gov.cn/"
                       target="_blank"
                       rel="noopener noreferrer"
                       class="beian-link">
                        {{ icpNo }}
                    </a>
                </div>
            </div>
        </footer>
    `,
    props: {
        icpNo: { type: String, default: '' },
        companyName: {
            type: String,
            default: '深圳云程企航商务服务有限公司'
        },
        gonganBeian: {
            type: String,
            default: '粤公网安备44030002012802号'
        },
        gonganBeianCode: {
            type: String,
            default: '44030002012802'
        }
    },
    data() {
        return {
            currentYear: new Date().getFullYear()
        };
    },
    methods: {
        showContactDialog() {
            alert('客服热线：18718052868\n工作时间：周一至周五 9:00-18:00');
        }
    }
};

if (typeof window !== 'undefined') {
    window.GlobalFooter = GlobalFooter;
}
