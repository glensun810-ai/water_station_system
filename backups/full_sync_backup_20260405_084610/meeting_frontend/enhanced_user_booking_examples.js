"""
会议室管理支付功能集成指南
用户端预约页面改进关键代码
"""

# ==========================================
# 一、费用明细显示组件（Vue.js）
# ==========================================

<!-- 在预约信息填写区域添加费用明细卡片 -->
<div v-if="selectedRoom && booking.booking_date && booking.start_time && booking.end_time" 
     class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl shadow-sm border border-blue-200 p-6 mb-6">
    <h2 class="text-lg font-semibold text-slate-800 mb-4 flex items-center">
        <svg class="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
        </svg>
        费用明细
    </h2>
    
    <div class="space-y-3">
        <!-- 基础费用 -->
        <div class="flex justify-between items-center py-2 border-b border-blue-100">
            <div class="flex items-center">
                <span class="text-slate-600">会议室费用</span>
                <span class="ml-2 text-xs text-slate-400">({{ calculatedDuration }}小时 × ¥{{ selectedRoom.price_per_hour }}/小时)</span>
            </div>
            <span class="text-lg font-semibold text-slate-800">¥{{ baseFee.toFixed(2) }}</span>
        </div>
        
        <!-- 会员折扣 -->
        <div v-if="userType === 'internal' && discountAmount > 0" 
             class="flex justify-between items-center py-2 border-b border-blue-100">
            <div class="flex items-center">
                <span class="text-green-600">会员折扣 (20%)</span>
                <span class="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">内部员工专享</span>
            </div>
            <span class="text-lg font-semibold text-green-600">-¥{{ discountAmount.toFixed(2) }}</span>
        </div>
        
        <!-- 免费时长 -->
        <div v-if="freeHoursAvailable > 0" class="flex justify-between items-center py-2 border-b border-blue-100">
            <div class="flex items-center">
                <span class="text-purple-600">使用免费时长</span>
                <span class="ml-2 text-xs text-purple-500">
                    (本月剩余{{ freeHoursAvailable }}小时)
                </span>
            </div>
            <div class="text-right">
                <div class="flex items-center gap-2">
                    <input type="number" 
                           v-model.number="freeHoursToUse" 
                           :max="Math.min(freeHoursAvailable, calculatedDuration)"
                           :min="0"
                           :step="0.5"
                           class="w-20 px-2 py-1 border border-purple-300 rounded text-sm text-center">
                    <span class="text-sm text-slate-600">小时</span>
                </div>
                <span class="text-lg font-semibold text-purple-600">
                    -¥{{ (freeHoursToUse * selectedRoom.price_per_hour).toFixed(2) }}
                </span>
            </div>
        </div>
        
        <!-- 实际应付 -->
        <div class="flex justify-between items-center py-3 bg-white rounded-lg px-4 mt-3">
            <span class="text-lg font-bold text-slate-800">实际应付金额</span>
            <span class="text-2xl font-bold text-blue-600">¥{{ actualFee.toFixed(2) }}</span>
        </div>
        
        <!-- 费用说明 -->
        <div class="text-sm text-slate-500 mt-2">
            <p v-if="userType === 'internal'">
                * 内部员工享受会员价格{{ selectedRoom.member_price_per_hour || (selectedRoom.price_per_hour * 0.8) }}元/小时
            </p>
            <p v-if="selectedRoom.free_hours_per_month > 0">
                * 该会议室每月提供{{ selectedRoom.free_hours_per_month }}小时免费时长
            </p>
        </div>
    </div>
</div>

# ==========================================
# 二、支付模式选择组件
# ==========================================

<!-- 在费用明细后添加支付模式选择 -->
<div v-if="actualFee > 0" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6">
    <h2 class="text-lg font-semibold text-slate-800 mb-4 flex items-center">
        <svg class="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
        </svg>
        选择支付方式
    </h2>
    
    <div class="grid grid-cols-2 gap-4">
        <!-- 先用后付 -->
        <button @click="paymentMode = 'credit'"
                :class="[
                    'p-6 rounded-xl border-2 transition text-center',
                    paymentMode === 'credit' 
                        ? 'border-blue-500 bg-blue-50 shadow-md' 
                        : 'border-gray-200 hover:border-gray-300'
                ]">
            <div class="text-3xl mb-2">📅</div>
            <div class="font-bold text-gray-800 mb-1">先用后付</div>
            <div class="text-sm text-gray-500">本月月底统一结算</div>
            <div class="mt-3 pt-3 border-t border-gray-100">
                <div class="text-xs text-blue-600 font-medium">
                    推荐内部员工使用
                </div>
            </div>
        </button>
        
        <!-- 立即支付 -->
        <button @click="paymentMode = 'immediate'"
                :class="[
                    'p-6 rounded-xl border-2 transition text-center',
                    paymentMode === 'immediate' 
                        ? 'border-green-500 bg-green-50 shadow-md' 
                        : 'border-gray-200 hover:border-gray-300'
                ]">
            <div class="text-3xl mb-2">💳</div>
            <div class="font-bold text-gray-800 mb-1">立即支付</div>
            <div class="text-sm text-gray-500">预约确认后立即付款</div>
            <div class="mt-3 pt-3 border-t border-gray-100">
                <div class="text-xs text-green-600 font-medium">
                    外部用户请使用此方式
                </div>
            </div>
        </button>
    </div>
    
    <!-- 支付说明 -->
    <div class="mt-4 p-4 bg-slate-50 rounded-lg text-sm text-slate-600">
        <p v-if="paymentMode === 'credit'">
            <strong>先用后付说明：</strong>
            选择此方式后，您可以先使用会议室，月底系统将自动生成结算单，
            请在收到结算通知后及时完成付款。
        </p>
        <p v-if="paymentMode === 'immediate'">
            <strong>立即支付说明：</strong>
            选择此方式后，管理员确认预约后，您需要立即提交支付申请
            （上传支付凭证），管理员确认收款后预约生效。
        </p>
    </div>
</div>

# ==========================================
# 三、JavaScript计算逻辑（Vue.js）
# ==========================================

const bookingForm = {
    data() {
        return {
            paymentMode: 'credit',  // 默认先用后付
            freeHoursToUse: 0,      // 使用免费时长
            freeHoursAvailable: 0,  // 可用免费时长
            calculatedDuration: 0,  // 计算时长
        }
    },
    
    computed: {
        // 基础费用
        baseFee() {
            if (!this.selectedRoom || !this.calculatedDuration) return 0;
            return this.selectedRoom.price_per_hour * this.calculatedDuration;
        },
        
        // 会员折扣金额
        discountAmount() {
            if (this.userType !== 'internal' || !this.selectedRoom) return 0;
            const memberPrice = this.selectedRoom.member_price_per_hour || 
                                (this.selectedRoom.price_per_hour * 0.8);
            return (this.selectedRoom.price_per_hour - memberPrice) * this.calculatedDuration;
        },
        
        // 免费时长减免金额
        freeHoursDiscount() {
            if (!this.selectedRoom || !this.freeHoursToUse) return 0;
            return this.freeHoursToUse * this.selectedRoom.price_per_hour;
        },
        
        // 实际应付金额
        actualFee() {
            let fee = this.baseFee;
            fee -= this.discountAmount;
            fee -= this.freeHoursDiscount;
            return Math.max(0, fee);
        },
        
        // 是否可以提交
        canSubmit() {
            return this.selectedRoom &&
                   this.booking.booking_date &&
                   this.booking.start_time &&
                   this.booking.end_time &&
                   this.timeValidation?.is_valid &&
                   this.actualFee >= 0 &&
                   !this.submitting;
        }
    },
    
    methods: {
        // 计算时长
        calculateDuration() {
            if (!this.booking.start_time || !this.booking.end_time) {
                this.calculatedDuration = 0;
                return;
            }
            
            const start = this.booking.start_time.split(':');
            const end = this.booking.end_time.split(':');
            
            const startMinutes = parseInt(start[0]) * 60 + parseInt(start[1]);
            const endMinutes = parseInt(end[0]) * 60 + parseInt(end[1]);
            
            const diffMinutes = endMinutes - startMinutes;
            this.calculatedDuration = Math.max(0, diffMinutes / 60);
            
            // 自动填充免费时长（如果可用）
            if (this.freeHoursAvailable > 0 && this.calculatedDuration > 0) {
                this.freeHoursToUse = Math.min(
                    this.freeHoursAvailable,
                    this.calculatedDuration
                );
            }
        },
        
        // 提交预约（改进版）
        async submitBooking() {
            if (!this.canSubmit || this.submitting) return;
            
            this.submitting = true;
            
            try {
                const bookingData = {
                    room_id: this.selectedRoom.id,
                    user_type: this.userType,
                    user_name: this.userType === 'internal' 
                        ? this.offices.find(o => o.id === this.selectedOfficeId)?.name 
                        : this.externalName,
                    user_phone: this.userType === 'external' ? this.externalPhone : '',
                    office_id: this.userType === 'internal' ? this.selectedOfficeId : null,
                    booking_date: this.booking.booking_date,
                    start_time: this.booking.start_time,
                    end_time: this.booking.end_time,
                    meeting_title: this.booking.meeting_title,
                    attendees_count: this.booking.attendees_count,
                    
                    // 新增支付相关字段
                    payment_mode: this.paymentMode,
                    payment_status: this.paymentMode === 'credit' ? 'unpaid' : 'unpaid',
                    actual_fee: this.actualFee,
                    discount_amount: this.discountAmount,
                    is_free: this.freeHoursToUse > 0 ? 1 : 0,
                    free_hours_used: this.freeHoursToUse
                };
                
                const response = await fetch(`${API_BASE}/bookings`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bookingData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // 显示详细预约成功信息
                    let successMessage = `
预定成功！

预约编号：${result.booking_no}
会议室：${result.room_name}
日期：${result.booking_date}
时间：${result.start_time}-${result.end_time}
时长：${result.duration}小时

费用明细：
原价：¥${result.total_fee.toFixed(2)}
${this.discountAmount > 0 ? `会员折扣：-¥${this.discountAmount.toFixed(2)}\n` : ''}
${this.freeHoursToUse > 0 ? `免费时长(${this.freeHoursToUse}小时)：-¥${this.freeHoursDiscount.toFixed(2)}\n` : ''}
实际应付：¥${result.actual_fee.toFixed(2)}
                    `;
                    
                    // 支付提示
                    if (this.paymentMode === 'immediate') {
                        successMessage += `
\n支付提示：
您选择了"立即支付"方式，预约已提交等待管理员确认。
确认后请在"我的预约"页面提交支付申请。
                        `;
                    } else {
                        successMessage += `
\n支付提示：
您选择了"先用后付"方式，本月月底系统将自动生成结算单。
请注意查看结算通知并及时完成付款。
                        `;
                    }
                    
                    alert(successMessage);
                    this.resetForm();
                    this.selectedRoom = null;
                } else {
                    alert(`预定失败：${result.detail || '未知错误'}`);
                }
            } catch (error) {
                console.error('提交预约失败:', error);
                alert('提交失败，请检查网络连接后重试');
            } finally {
                this.submitting = false;
            }
        },
        
        // 获取可用免费时长
        async loadFreeQuota() {
            if (this.userType !== 'internal' || !this.selectedOfficeId || !this.selectedRoom) {
                this.freeHoursAvailable = 0;
                return;
            }
            
            try {
                const yearMonth = new Date().toISOString().slice(0, 7); // 2026-04
                const response = await fetch(
                    `${API_BASE}/free-quota?office_id=${this.selectedOfficeId}&room_id=${this.selectedRoom.id}&year_month=${yearMonth}`
                );
                
                const data = await response.json();
                if (data.success) {
                    this.freeHoursAvailable = data.data?.remaining_free_hours || 
                                             this.selectedRoom.free_hours_per_month || 0;
                }
            } catch (error) {
                console.error('获取免费时长失败:', error);
                // 使用会议室默认免费时长
                this.freeHoursAvailable = this.selectedRoom.free_hours_per_month || 0;
            }
        }
    },
    
    watch: {
        // 监听时间变化，自动计算时长和费用
        'booking.start_time': function() {
            this.calculateDuration();
        },
        'booking.end_time': function() {
            this.calculateDuration();
        },
        
        // 监听会议室选择，加载免费时长
        selectedRoom: function() {
            this.loadFreeQuota();
        },
        
        // 监听办公室选择，加载免费时长
        selectedOfficeId: function() {
            this.loadFreeQuota();
        }
    }
};

# ==========================================
# 四、我的预约页面改进（显示支付状态）
# ==========================================

<!-- 在预约列表表格中添加支付状态列 -->
<table class="w-full">
    <thead>
        <tr class="bg-slate-50">
            <th class="text-left py-3 px-4 font-semibold text-slate-700">预约编号</th>
            <th class="text-left py-3 px-4 font-semibold text-slate-700">会议室</th>
            <th class="text-left py-3 px-4 font-semibold text-slate-700">时间</th>
            <th class="text-left py-3 px-4 font-semibold text-slate-700">费用</th>
            <th class="text-left py-3 px-4 font-semibold text-slate-700">预约状态</th>
            <th class="text-left py-3 px-4 font-semibold text-slate-700">支付状态</th>
            <th class="text-left py-3 px-4 font-semibold text-slate-700">操作</th>
        </tr>
    </thead>
    <tbody>
        <tr v-for="booking in bookings" class="border-b hover:bg-slate-50">
            <td class="py-3 px-4 font-mono text-sm">{{ booking.booking_no }}</td>
            <td class="py-3 px-4">{{ booking.room_name }}</td>
            <td class="py-3 px-4">
                <div>{{ booking.booking_date }}</div>
                <div class="text-sm text-slate-500">{{ booking.start_time }}-{{ booking.end_time }}</div>
            </td>
            <td class="py-3 px-4 font-semibold text-blue-600">¥{{ booking.actual_fee.toFixed(2) }}</td>
            <td class="py-3 px-4">
                <span :class="getBookingStatusClass(booking.status)" 
                      class="px-2 py-1 rounded-full text-xs font-medium">
                    {{ getBookingStatusText(booking.status) }}
                </span>
            </td>
            <td class="py-3 px-4">
                <span :class="getPaymentStatusClass(booking.payment_status)" 
                      class="px-2 py-1 rounded-full text-xs font-medium">
                    {{ getPaymentStatusText(booking.payment_status) }}
                </span>
            </td>
            <td class="py-3 px-4">
                <!-- 提交支付按钮 -->
                <button v-if="booking.payment_status === 'unpaid' && booking.status === 'confirmed'"
                        @click="showPaymentModal(booking)"
                        class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
                    提交支付
                </button>
                
                <!-- 查看详情按钮 -->
                <button @click="viewBookingDetail(booking)"
                        class="px-3 py-1 text-blue-600 hover:text-blue-700 text-sm ml-2">
                    详情
                </button>
            </td>
        </tr>
    </tbody>
</table>

# ==========================================
# 五、支付申请弹窗组件
# ==========================================

<!-- 支付申请弹窗 -->
<div v-if="showPaymentModalFlag" 
     class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
     @click.self="closePaymentModal">
    <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full m-4">
        <!-- 头部 -->
        <div class="p-6 border-b">
            <div class="flex justify-between items-center">
                <h3 class="text-xl font-bold text-slate-800">提交支付申请</h3>
                <button @click="closePaymentModal" class="text-slate-400 hover:text-slate-600">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        </div>
        
        <!-- 预约信息 -->
        <div class="p-6 bg-slate-50">
            <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                    <span class="text-slate-600">预约编号：</span>
                    <span class="font-semibold">{{ currentBooking.booking_no }}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-600">会议室：</span>
                    <span class="font-semibold">{{ currentBooking.room_name }}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-600">预约时间：</span>
                    <span class="font-semibold">{{ currentBooking.booking_date }} {{ currentBooking.start_time }}-{{ currentBooking.end_time }}</span>
                </div>
                <div class="flex justify-between pt-2 border-t border-slate-200">
                    <span class="text-slate-800 font-medium">应付金额：</span>
                    <span class="text-xl font-bold text-blue-600">¥{{ currentBooking.actual_fee.toFixed(2) }}</span>
                </div>
            </div>
        </div>
        
        <!-- 支付表单 -->
        <div class="p-6 space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">支付方式 *</label>
                <select v-model="paymentForm.payment_method" 
                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                    <option value="">请选择支付方式</option>
                    <option value="微信支付">微信支付</option>
                    <option value="支付宝">支付宝</option>
                    <option value="银行转账">银行转账</option>
                    <option value="现金">现金支付</option>
                </select>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">支付凭证（可选）</label>
                <div class="border-2 border-dashed border-slate-300 rounded-lg p-4 text-center hover:border-blue-400 transition">
                    <input type="file" 
                           @change="handleFileUpload"
                           accept="image/*"
                           class="hidden"
                           ref="fileInput">
                    <button @click="$refs.fileInput.click()" 
                            class="text-blue-600 hover:text-blue-700">
                        <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                        </svg>
                        <div class="text-sm">点击上传支付截图</div>
                    </button>
                    <div v-if="paymentForm.payment_evidence" class="mt-3">
                        <img :src="paymentForm.payment_evidence" class="max-h-32 mx-auto rounded">
                    </div>
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">支付备注</label>
                <textarea v-model="paymentForm.payment_remark"
                          rows="3"
                          placeholder="请输入支付备注，例如：转账时间、转账金额等"
                          class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </textarea>
            </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="p-6 border-t bg-slate-50 flex gap-3">
            <button @click="submitPayment"
                    :disabled="!paymentForm.payment_method || submittingPayment"
                    :class="[
                        'flex-1 px-6 py-3 rounded-lg font-medium transition',
                        paymentForm.payment_method && !submittingPayment
                            ? 'bg-blue-500 text-white hover:bg-blue-600'
                            : 'bg-slate-300 text-slate-500 cursor-not-allowed'
                    ]">
                {{ submittingPayment ? '提交中...' : '提交支付申请' }}
            </button>
            <button @click="closePaymentModal"
                    class="px-6 py-3 bg-slate-200 text-slate-700 rounded-lg font-medium hover:bg-slate-300">
                取消
            </button>
        </div>
    </div>
</div>

# ==========================================
# 六、状态显示辅助函数
# ==========================================

methods: {
    // 预约状态样式
    getBookingStatusClass(status) {
        const classes = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'confirmed': 'bg-green-100 text-green-800',
            'active': 'bg-blue-100 text-blue-800',
            'completed': 'bg-slate-100 text-slate-800',
            'cancelled': 'bg-red-100 text-red-800'
        };
        return classes[status] || 'bg-gray-100 text-gray-800';
    },
    
    getBookingStatusText(status) {
        const texts = {
            'pending': '待确认',
            'confirmed': '已确认',
            'active': '进行中',
            'completed': '已完成',
            'cancelled': '已取消'
        };
        return texts[status] || status;
    },
    
    // 支付状态样式
    getPaymentStatusClass(paymentStatus) {
        const classes = {
            'unpaid': 'bg-red-100 text-red-800',
            'applied': 'bg-blue-100 text-blue-800',
            'paid': 'bg-green-100 text-green-800'
        };
        return classes[paymentStatus] || 'bg-gray-100 text-gray-800';
    },
    
    getPaymentStatusText(paymentStatus) {
        const texts = {
            'unpaid': '待付款',
            'applied': '待确认收款',
            'paid': '已付款'
        };
        return texts[paymentStatus] || paymentStatus;
    },
    
    // 提交支付申请
    async submitPayment() {
        if (!this.paymentForm.payment_method) {
            alert('请选择支付方式');
            return;
        }
        
        this.submittingPayment = true;
        
        try {
            const response = await fetch(`${API_BASE}/payment/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    booking_id: this.currentBooking.id,
                    payment_method: this.paymentForm.payment_method,
                    payment_evidence: this.paymentForm.payment_evidence,
                    payment_remark: this.paymentForm.payment_remark
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert(`
支付申请已提交！

支付单号：${result.data.payment_no}
支付金额：¥${this.currentBooking.actual_fee.toFixed(2)}
支付方式：${this.paymentForm.payment_method}

管理员将在收到您的支付凭证后确认收款。
您可以在"我的预约"页面查看支付状态。
                `);
                this.closePaymentModal();
                this.loadMyBookings(); // 刷新预约列表
            } else {
                alert(`提交失败：${result.message || '未知错误'}`);
            }
        } catch (error) {
            console.error('提交支付失败:', error);
            alert('提交失败，请检查网络连接后重试');
        } finally {
            this.submittingPayment = false;
        }
    },
    
    // 文件上传处理
    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // 这里可以上传到服务器，简化示例直接使用本地URL
        const reader = new FileReader();
        reader.onload = (e) => {
            this.paymentForm.payment_evidence = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}