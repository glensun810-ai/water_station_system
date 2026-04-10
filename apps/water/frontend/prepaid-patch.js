/**
 * 预付订单管理功能补丁
 * 用于 admin.html 的预付订单管理功能
 */

// 预付订单相关状态
const prepaidOrders = ref([]);
const prepaidFilter = ref({ status: '' });
const showPrepaidCreateModal = ref(false);
const showPrepaidDetailModal = ref(false);
const selectedPrepaidOrder = ref(null);
const prepaidForm = ref({
    user_id: '',
    product_id: '',
    total_qty: 10,
    unit_price: 0,
    discount_amount: 0,
    payment_method: 'offline',
    note: ''
});

// 获取用户名
function getUserName(userId) {
    const user = allUsers.value.find(u => u.id === userId);
    return user ? user.name : 'Unknown';
}

// 获取用户部门
function getUserNameDept(userId) {
    const user = allUsers.value.find(u => u.id === userId);
    return user ? user.department : '';
}

// 获取产品名
function getProductName(productId) {
    const product = products.value.find(p => p.id === productId);
    return product ? `${product.name} (${product.specification})` : 'Unknown';
}

// 产品选择变化时自动填充单价
function onPrepaidProductChange() {
    const product = products.value.find(p => p.id === prepaidForm.value.product_id);
    if (product) {
        prepaidForm.value.unit_price = product.price;
    }
}

// 加载预付订单列表
async function loadPrepaidOrders() {
    try {
        let url = `${API_BASE}/admin/prepaid/orders`;
        const params = new URLSearchParams();
        if (prepaidFilter.value.status) {
            params.append('payment_status', prepaidFilter.value.status);
        }
        if (params.toString()) {
            url += '?' + params.toString();
        }

        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token.value}` }
        });
        if (res.ok) {
            prepaidOrders.value = await res.json();
        }
    } catch (error) {
        console.error('加载预付订单失败:', error);
    }
}

// 提交预付订单
async function submitPrepaidOrder() {
    if (!prepaidForm.value.user_id || !prepaidForm.value.product_id) {
        alert('请选择用户和产品');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/prepaid/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token.value}`
            },
            body: JSON.stringify(prepaidForm.value)
        });

        if (res.ok) {
            alert('预付订单创建成功');
            showPrepaidCreateModal.value = false;
            prepaidForm.value = {
                user_id: '',
                product_id: '',
                total_qty: 10,
                unit_price: 0,
                discount_amount: 0,
                payment_method: 'offline',
                note: ''
            };
            loadPrepaidOrders();
        } else {
            const error = await res.json();
            alert('创建失败：' + (error.detail || '未知错误'));
        }
    } catch (error) {
        console.error('创建预付订单失败:', error);
        alert('网络错误');
    }
}

// 显示订单详情
function showPrepaidDetail(order) {
    selectedPrepaidOrder.value = order;
    showPrepaidDetailModal.value = true;
}

// 确认收款
async function confirmPrepaidPayment(orderId) {
    if (!confirm('确认已收到该订单的预付款吗？')) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/admin/prepaid/orders/${orderId}/confirm`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token.value}` }
        });

        if (res.ok) {
            alert('已确认收款');
            showPrepaidDetailModal.value = false;
            loadPrepaidOrders();
        } else {
            const error = await res.json();
            alert('确认失败：' + (error.detail || '未知错误'));
        }
    } catch (error) {
        console.error('确认收款失败:', error);
        alert('网络错误');
    }
}

// 格式化日期时间
function formatDateTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}
