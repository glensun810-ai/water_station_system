"""
会议室管理后台改进关键代码示例
管理端支付管理、结算管理、统计分析功能
"""

# ==========================================
# 一、管理后台新增标签页导航
# ==========================================

<!-- 在admin.html中修改标签页 -->
<div class="flex space-x-4 mb-6 border-b bg-white rounded-t-lg px-4 pt-4">
    <button @click="currentTab = 'rooms'" 
            :class="currentTab === 'rooms' ? 'border-green-500 text-green-600' : ''"
            class="px-4 py-2 border-b-2 font-medium transition">
        会议室管理
    </button>
    <button @click="currentTab = 'bookings'" 
            :class="currentTab === 'bookings' ? 'border-green-500 text-green-600' : ''"
            class="px-4 py-2 border-b-2 font-medium transition">
        预约记录
    </button>
    <button @click="currentTab = 'payments'" 
            :class="currentTab === 'payments' ? 'border-green-500 text-green-600' : ''"
            class="px-4 py-2 border-b-2 font-medium transition">
        💳 支付管理
    </button>
    <button @click="currentTab = 'settlements'" 
            :class="currentTab === 'settlements' ? 'border-green-500 text-green-600' : ''"
            class="px-4 py-2 border-b-2 font-medium transition">
        📊 结算管理
    </button>
    <button @click="currentTab = 'stats'" 
            :class="currentTab === 'stats' ? 'border-green-500 text-green-600' : ''"
            class="px-4 py-2 border-b-2 font-medium transition">
        📈 统计分析
    </button>
</div>

# ==========================================
# 二、支付管理页面
# ==========================================

<div v-if="currentTab === 'payments'" class="space-y-6">
    <!-- 快速统计卡片 -->
    <div class="grid md:grid-cols-4 gap-4">
        <div class="bg-white rounded-xl shadow p-6">
            <div class="text-sm text-gray-500 mb-2">待确认收款</div>
            <div class="text-3xl font-bold text-orange-600">{{ paymentStats.pending_count || 0 }}</div>
        </div>
        <div class="bg-white rounded-xl shadow p-6">
            <div class="text-sm text-gray-500 mb-2">本月已收款</div>
            <div class="text-3xl font-bold text-green-600">¥{{ paymentStats.month_confirmed || 0 }}</div>
        </div>
        <div class="bg-white rounded-xl shadow p-6">
            <div class="text-sm text-gray-500 mb-2">待收款总额</div>
            <div class="text-3xl font-bold text-red-600">¥{{ paymentStats.total_unpaid || 0 }}</div>
        </div>
        <div class="bg-white rounded-xl shadow p-6">
            <div class="text-sm text-gray-500 mb-2">本月收款笔数</div>
            <div class="text-3xl font-bold text-blue-600">{{ paymentStats.month_count || 0 }}</div>
        </div>
    </div>
    
    <!-- 筛选和批量操作 -->
    <div class="bg-white rounded-xl shadow p-4">
        <div class="flex justify-between items-center">
            <div class="flex gap-4">
                <select v-model="paymentFilter.status" class="border rounded px-3 py-2">
                    <option value="">全部状态</option>
                    <option value="pending">待确认</option>
                    <option value="confirmed">已确认</option>
                </select>
                <select v-model="paymentFilter.payment_method" class="border rounded px-3 py-2">
                    <option value="">全部方式</option>
                    <option value="微信支付">微信支付</option>
                    <option value="支付宝">支付宝</option>
                    <option value="银行转账">银行转账</option>
                </select>
                <input type="date" v-model="paymentFilter.start_date" class="border rounded px-3 py-2">
                <input type="date" v-model="paymentFilter.end_date" class="border rounded px-3 py-2">
            </div>
            
            <button v-if="selectedPayments.length > 0"
                    @click="batchConfirmPayments"
                    class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
                批量确认收款 ({{ selectedPayments.length }}笔)
            </button>
        </div>
    </div>
    
    <!-- 支付记录表格 -->
    <div class="bg-white rounded-xl shadow overflow-hidden">
        <table class="w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="text-left py-3 px-4">
                        <input type="checkbox" @change="selectAllPayments">
                    </th>
                    <th class="text-left py-3 px-4 font-semibold">支付单号</th>
                    <th class="text-left py-3 px-4 font-semibold">预约编号</th>
                    <th class="text-left py-3 px-4 font-semibold">办公室</th>
                    <th class="text-left py-3 px-4 font-semibold">会议室</th>
                    <th class="text-left py-3 px-4 font-semibold">金额</th>
                    <th class="text-left py-3 px-4 font-semibold">支付方式</th>
                    <th class="text-left py-3 px-4 font-semibold">支付凭证</th>
                    <th class="text-left py-3 px-4 font-semibold">状态</th>
                    <th class="text-left py-3 px-4 font-semibold">操作</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="payment in filteredPayments" class="border-b hover:bg-gray-50">
                    <td class="py-3 px-4">
                        <input type="checkbox" 
                               v-model="selectedPayments" 
                               :value="payment.id"
                               :disabled="payment.status !== 'pending'">
                    </td>
                    <td class="py-3 px-4 font-mono text-sm">{{ payment.payment_no }}</td>
                    <td class="py-3 px-4 font-mono text-sm">{{ payment.booking_no }}</td>
                    <td class="py-3 px-4">{{ payment.office_name || '外部用户' }}</td>
                    <td class="py-3 px-4">{{ payment.room_name }}</td>
                    <td class="py-3 px-4 font-semibold text-blue-600">¥{{ payment.amount.toFixed(2) }}</td>
                    <td class="py-3 px-4">{{ payment.payment_method }}</td>
                    <td class="py-3 px-4">
                        <button v-if="payment.payment_evidence"
                                @click="viewEvidence(payment)"
                                class="text-blue-600 hover:text-blue-700">
                            查看凭证
                        </button>
                        <span v-else class="text-gray-400">无</span>
                    </td>
                    <td class="py-3 px-4">
                        <span :class="getPaymentStatusClass(payment.status)" 
                              class="px-3 py-1 rounded-full text-sm font-medium">
                            {{ getPaymentStatusText(payment.status) }}
                        </span>
                    </td>
                    <td class="py-3 px-4 space-x-2">
                        <button v-if="payment.status === 'pending'"
                                @click="confirmPayment(payment.id)"
                                class="text-green-600 hover:text-green-700 font-medium">
                            确认收款
                        </button>
                        <button @click="viewPaymentDetail(payment)"
                                class="text-blue-600 hover:text-blue-700">
                            详情
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>

# ==========================================
# 三、结算管理页面
# ==========================================

<div v-if="currentTab === 'settlements'" class="space-y-6">
    <!-- 快速统计 -->
    <div class="grid md:grid-cols-3 gap-4">
        <div class="bg-white rounded-xl shadow p-6">
            <div class="text-sm text-gray-500 mb-2">待结算批次</div>
            <div class="text-3xl font-bold text-orange-600">{{ settlementStats.pending || 0 }}</div>
        </div>
        <div class="bg-white rounded-xl shadow p-6">
            <div class="text-sm text-gray-500 mb-2">本月结算金额</div>
            <div class="text-3xl font-bold text-green-600">¥{{ settlementStats.month_amount || 0 }}</div>
        </div>
        <div class="bg-white rounded-xl shadow p-6">
            <div class="text-sm text-gray-500 mb-2">已结算批次</div>
            <div class="text-3xl font-bold text-blue-600">{{ settlementStats.confirmed || 0 }}</div>
        </div>
    </div>
    
    <!-- 自动结算操作 -->
    <div class="bg-white rounded-xl shadow p-4">
        <div class="flex justify-between items-center">
            <h3 class="font-semibold text-gray-800">自动生成月度结算</h3>
            <button @click="autoGenerateMonthlySettlement"
                    class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                📅 自动生成本月结算
            </button>
        </div>
    </div>
    
    <!-- 结算批次列表 -->
    <div class="bg-white rounded-xl shadow overflow-hidden">
        <table class="w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="text-left py-3 px-4 font-semibold">结算批次号</th>
                    <th class="text-left py-3 px-4 font-semibold">办公室</th>
                    <th class="text-left py-3 px-4 font-semibold">结算周期</th>
                    <th class="text-left py-3 px-4 font-semibold">预约数</th>
                    <th class="text-left py-3 px-4 font-semibold">总时长</th>
                    <th class="text-left py-3 px-4 font-semibold">总金额</th>
                    <th class="text-left py-3 px-4 font-semibold">已付金额</th>
                    <th class="text-left py-3 px-4 font-semibold">免费时长</th>
                    <th class="text-left py-3 px-4 font-semibold">状态</th>
                    <th class="text-left py-3 px-4 font-semibold">操作</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="settlement in settlements" class="border-b hover:bg-gray-50">
                    <td class="py-3 px-4 font-mono text-sm">{{ settlement.batch_no }}</td>
                    <td class="py-3 px-4">{{ settlement.office_name }}</td>
                    <td class="py-3 px-4">
                        <div class="text-sm">{{ settlement.settlement_period_start }}</div>
                        <div class="text-xs text-gray-500">至 {{ settlement.settlement_period_end }}</div>
                    </td>
                    <td class="py-3 px-4">{{ settlement.total_bookings }}</td>
                    <td class="py-3 px-4">{{ settlement.total_hours }}小时</td>
                    <td class="py-3 px-4 font-semibold text-blue-600">¥{{ settlement.total_amount.toFixed(2) }}</td>
                    <td class="py-3 px-4 font-semibold text-green-600">¥{{ settlement.paid_amount.toFixed(2) }}</td>
                    <td class="py-3 px-4 text-purple-600">{{ settlement.free_hours }}小时</td>
                    <td class="py-3 px-4">
                        <span :class="getSettlementClass(settlement.status)" 
                              class="px-3 py-1 rounded-full text-sm font-medium">
                            {{ getSettlementText(settlement.status) }}
                        </span>
                    </td>
                    <td class="py-3 px-4 space-x-2">
                        <button @click="viewSettlementDetail(settlement.id)"
                                class="text-blue-600 hover:text-blue-700">
                            查看明细
                        </button>
                        <button @click="exportSettlement(settlement.id)"
                                class="text-green-600 hover:text-green-700">
                            导出
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>

# ==========================================
# 四、增强的统计分析页面
# ==========================================

<div v-if="currentTab === 'stats'" class="space-y-6">
    <!-- 日期范围选择 -->
    <div class="bg-white rounded-xl shadow p-4">
        <div class="flex items-center gap-4">
            <label class="text-sm font-medium">统计周期：</label>
            <input type="date" v-model="statsStartDate" class="border rounded px-3 py-2">
            <input type="date" v-model="statsEndDate" class="border rounded px-3 py-2">
            <button @click="loadStatistics"
                    class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                查询
            </button>
        </div>
    </div>
    
    <!-- 总览统计 -->
    <div class="grid md:grid-cols-6 gap-4">
        <div class="bg-white rounded-xl shadow p-4">
            <div class="text-xs text-gray-500 mb-1">总预约数</div>
            <div class="text-2xl font-bold text-blue-600">{{ stats.overview.total_bookings }}</div>
        </div>
        <div class="bg-white rounded-xl shadow p-4">
            <div class="text-xs text-gray-500 mb-1">总时长</div>
            <div class="text-2xl font-bold text-purple-600">{{ stats.overview.total_hours }}h</div>
        </div>
        <div class="bg-white rounded-xl shadow p-4">
            <div class="text-xs text-gray-500 mb-1">总收入</div>
            <div class="text-2xl font-bold text-green-600">¥{{ stats.overview.actual_revenue }}</div>
        </div>
        <div class="bg-white rounded-xl shadow p-4">
            <div class="text-xs text-gray-500 mb-1">已付款</div>
            <div class="text-2xl font-bold text-green-600">{{ stats.overview.paid_bookings }}</div>
        </div>
        <div class="bg-white rounded-xl shadow p-4">
            <div class="text-xs text-gray-500 mb-1">待收款</div>
            <div class="text-2xl font-bold text-red-600">¥{{ stats.overview.unpaid_amount }}</div>
        </div>
        <div class="bg-white rounded-xl shadow p-4">
            <div class="text-xs text-gray-500 mb-1">免费时长</div>
            <div class="text-2xl font-bold text-purple-600">{{ stats.overview.total_free_hours }}h</div>
        </div>
    </div>
    
    <!-- 会议室使用统计 -->
    <div class="bg-white rounded-xl shadow p-6">
        <h3 class="font-bold text-lg mb-4">各会议室使用情况</h3>
        <table class="w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="text-left py-3 px-4">会议室</th>
                    <th class="text-left py-3 px-4">预约数</th>
                    <th class="text-left py-3 px-4">总时长</th>
                    <th class="text-left py-3 px-4">总收入</th>
                    <th class="text-left py-3 px-4">使用率</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="room in stats.room_statistics" class="border-b">
                    <td class="py-3 px-4 font-medium">{{ room.room_name }}</td>
                    <td class="py-3 px-4">{{ room.booking_count }}</td>
                    <td class="py-3 px-4">{{ room.total_hours }}小时</td>
                    <td class="py-3 px-4 font-semibold text-blue-600">¥{{ room.total_revenue }}</td>
                    <td class="py-3 px-4">
                        <div class="flex items-center gap-2">
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div class="bg-blue-600 h-2 rounded-full" 
                                     :style="{ width: room.usage_rate + '%' }">
                                </div>
                            </div>
                            <span class="text-sm font-medium">{{ room.usage_rate }}%</span>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <!-- 办公室统计 -->
    <div class="bg-white rounded-xl shadow p-6">
        <h3 class="font-bold text-lg mb-4">各办公室会议室费用</h3>
        <table class="w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="text-left py-3 px-4">办公室</th>
                    <th class="text-left py-3 px-4">预约数</th>
                    <th class="text-left py-3 px-4">总时长</th>
                    <th class="text-left py-3 px-4">原价金额</th>
                    <th class="text-left py-3 px-4">实际金额</th>
                    <th class="text-left py-3 px-4">折扣金额</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="office in stats.office_statistics" class="border-b">
                    <td class="py-3 px-4 font-medium">{{ office.office_name }}</td>
                    <td class="py-3 px-4">{{ office.booking_count }}</td>
                    <td class="py-3 px-4">{{ office.total_hours }}小时</td>
                    <td class="py-3 px-4 text-gray-600">¥{{ office.total_fee }}</td>
                    <td class="py-3 px-4 font-semibold text-green-600">¥{{ office.actual_fee }}</td>
                    <td class="py-3 px-4 text-purple-600">¥{{ office.total_fee - office.actual_fee }}</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <!-- 操作日志 -->
    <div class="bg-white rounded-xl shadow p-6">
        <h3 class="font-bold text-lg mb-4">最近操作日志</h3>
        <table class="w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="text-left py-3 px-4">操作类型</th>
                    <th class="text-left py-3 px-4">操作描述</th>
                    <th class="text-left py-3 px-4">操作人</th>
                    <th class="text-left py-3 px-4">操作时间</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="log in operationLogs.slice(0, 10)" class="border-b">
                    <td class="py-3 px-4">
                        <span :class="getOperationTypeClass(log.operation_type)"
                              class="px-2 py-1 rounded text-xs font-medium">
                            {{ log.operation_type }}
                        </span>
                    </td>
                    <td class="py-3 px-4 text-sm">{{ log.operation_desc }}</td>
                    <td class="py-3 px-4 text-sm">{{ log.operator }}</td>
                    <td class="py-3 px-4 text-sm text-gray-500">{{ formatDate(log.created_at) }}</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>

# ==========================================
# 五、JavaScript管理逻辑
# ==========================================

const adminApp = {
    data() {
        return {
            currentTab: 'rooms',
            paymentStats: {},
            paymentFilter: {},
            selectedPayments: [],
            payments: [],
            settlementStats: {},
            settlements: [],
            stats: {
                overview: {},
                room_statistics: [],
                office_statistics: []
            },
            operationLogs: []
        }
    },
    
    methods: {
        // 加载支付统计
        async loadPaymentStats() {
            try {
                const response = await fetch(`${API_BASE}/statistics/enhanced?start_date=${this.statsStartDate}&end_date=${this.statsEndDate}`);
                const data = await response.json();
                
                if (data.success) {
                    this.paymentStats = {
                        pending_count: data.data.overview.pending_payment_bookings || 0,
                        month_confirmed: data.data.overview.actual_revenue || 0,
                        total_unpaid: data.data.overview.unpaid_bookings * 100 || 0,
                        month_count: data.data.overview.paid_bookings || 0
                    };
                }
            } catch (error) {
                console.error('加载支付统计失败:', error);
            }
        },
        
        // 加载支付记录
        async loadPayments() {
            try {
                const params = new URLSearchParams(this.paymentFilter);
                const response = await fetch(`${API_BASE}/payments?${params}`);
                const data = await response.json();
                
                if (data.success) {
                    this.payments = data.data.payments;
                }
            } catch (error) {
                console.error('加载支付记录失败:', error);
            }
        },
        
        // 确认收款
        async confirmPayment(paymentId) {
            if (!confirm('确认收款？此操作不可撤销。')) return;
            
            try {
                const response = await fetch(`${API_BASE}/payment/confirm`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ payment_id: paymentId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('收款确认成功！');
                    this.loadPayments();
                    this.loadPaymentStats();
                } else {
                    alert('确认失败：' + result.message);
                }
            } catch (error) {
                console.error('确认收款失败:', error);
                alert('操作失败，请重试');
            }
        },
        
        // 批量确认收款
        async batchConfirmPayments() {
            if (this.selectedPayments.length === 0) {
                alert('请选择要确认的支付记录');
                return;
            }
            
            if (!confirm(`确认批量收款 ${this.selectedPayments.length} 笔？此操作不可撤销。`)) return;
            
            try {
                const response = await fetch(`${API_BASE}/payment/batch-confirm`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.selectedPayments)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(`成功确认 ${result.message}`);
                    this.selectedPayments = [];
                    this.loadPayments();
                    this.loadPaymentStats();
                }
            } catch (error) {
                console.error('批量确认失败:', error);
            }
        },
        
        // 自动生成月度结算
        async autoGenerateMonthlySettlement() {
            const now = new Date();
            const yearMonth = now.toISOString().slice(0, 7);
            
            if (!confirm(`自动生成 ${yearMonth} 月度结算批次？`)) return;
            
            try {
                // 获取本月所有未结算的预约
                const response = await fetch(`${API_BASE}/bookings/enhanced?payment_status=paid&start_date=${yearMonth}-01&end_date=${yearMonth}-31`);
                const bookingsData = await response.json();
                
                if (!bookingsData.success || bookingsData.data.bookings.length === 0) {
                    alert('本月没有已付款的预约记录');
                    return;
                }
                
                // 按办公室分组
                const officeGroups = {};
                bookingsData.data.bookings.forEach(booking => {
                    if (!officeGroups[booking.office_id]) {
                        officeGroups[booking.office_id] = {
                            office_id: booking.office_id,
                            office_name: booking.office_name || '外部用户',
                            bookings: []
                        };
                    }
                    officeGroups[booking.office_id].bookings.push(booking.id);
                });
                
                // 为每个办公室创建结算批次
                for (const officeId in officeGroups) {
                    const group = officeGroups[officeId];
                    
                    const settlementResponse = await fetch(`${API_BASE}/settlement/create`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            office_id: group.office_id,
                            booking_ids: group.bookings,
                            settlement_period_start: `${yearMonth}-01`,
                            settlement_period_end: `${yearMonth}-31`,
                            remark: `${yearMonth}月会议室费用结算`
                        })
                    });
                    
                    const result = await settlementResponse.json();
                    
                    if (result.success) {
                        console.log(`结算批次创建成功：${result.data.batch_no}`);
                    }
                }
                
                alert('月度结算批次自动生成完成！');
                this.loadSettlements();
                
            } catch (error) {
                console.error('自动结算失败:', error);
                alert('自动结算失败，请重试');
            }
        },
        
        // 加载统计数据
        async loadStatistics() {
            try {
                const response = await fetch(`${API_BASE}/statistics/enhanced?start_date=${this.statsStartDate}&end_date=${this.statsEndDate}`);
                const data = await response.json();
                
                if (data.success) {
                    this.stats = data.data;
                    this.operationLogs = await this.loadOperationLogs();
                }
            } catch (error) {
                console.error('加载统计失败:', error);
            }
        },
        
        // 查看支付凭证
        viewEvidence(payment) {
            if (payment.payment_evidence) {
                // 如果是图片URL，显示图片
                if (payment.payment_evidence.startsWith('http') || payment.payment_evidence.startsWith('data:image')) {
                    window.open(payment.payment_evidence, '_blank');
                } else {
                    alert(`支付凭证：\n${payment.payment_evidence}`);
                }
            }
        },
        
        // 导出结算单
        exportSettlement(batchId) {
            alert('结算单导出功能开发中...');
            // TODO: 实现导出功能
        },
        
        // 状态样式函数
        getPaymentStatusClass(status) {
            const classes = {
                'pending': 'bg-orange-100 text-orange-800',
                'confirmed': 'bg-green-100 text-green-800'
            };
            return classes[status] || 'bg-gray-100 text-gray-800';
        },
        
        getPaymentStatusText(status) {
            const texts = {
                'pending': '待确认',
                'confirmed': '已确认'
            };
            return texts[status] || status;
        },
        
        getSettlementClass(status) {
            const classes = {
                'pending': 'bg-yellow-100 text-yellow-800',
                'confirmed': 'bg-green-100 text-green-800'
            };
            return classes[status] || 'bg-gray-100 text-gray-800';
        },
        
        getSettlementText(status) {
            const texts = {
                'pending': '待确认',
                'confirmed': '已确认'
            };
            return texts[status] || status;
        },
        
        getOperationTypeClass(type) {
            const classes = {
                'payment_submit': 'bg-blue-100 text-blue-800',
                'payment_confirm': 'bg-green-100 text-green-800',
                'booking_delete': 'bg-red-100 text-red-800',
                'settlement_create': 'bg-purple-100 text-purple-800'
            };
            return classes[type] || 'bg-gray-100 text-gray-800';
        }
    },
    
    mounted() {
        // 初始化日期范围
        const now = new Date();
        this.statsStartDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
        this.statsEndDate = now.toISOString().slice(0, 10);
        
        // 加载初始数据
        this.loadStatistics();
        this.loadPayments();
    }
};