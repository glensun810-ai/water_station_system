/**
 * P1 阶段功能补丁 - 回收站功能 JavaScript 代码
 * 
 * 使用方法：
 * 1. 找到 admin.html 中的 setup() 函数
 * 2. 在 const remindList = ref([]); 后面添加回收站状态
 * 3. 在 loadTransactions 函数后面添加回收站方法
 * 4. 在 return 语句中添加回收站相关导出
 */

// ==================== 回收站状态变量 ====================
// 在 setup() 函数中添加以下代码：
/*
const trashList = ref([]); // 回收站列表
const selectedTrash = ref([]); // 已选择的回收站记录
const selectAllTrash = ref(false); // 全选状态
*/

// ==================== 回收站方法 ====================
// 在 setup() 函数中添加以下方法：

// 加载回收站数据
const loadTrashList = async () => {
    try {
        const res = await fetch(`${API_BASE}/admin/trash?days=30`, {
            headers: getAuthHeaders()
        });
        trashList.value = await res.json();
    } catch (e) {
        console.error('Failed to load trash list:', e);
    }
};

// 回收站全选/反选
const toggleSelectAllTrash = () => {
    if (selectAllTrash.value) {
        selectedTrash.value = trashList.value.map(t => t.id);
    } else {
        selectedTrash.value = [];
    }
};

const updateSelectAll = () => {
    selectAllTrash.value = selectedTrash.value.length === trashList.value.length;
};

// 恢复单条记录
const restoreOneFromTrash = async (id) => {
    try {
        const storedToken = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/admin/trash/restore`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${storedToken}`
            },
            body: JSON.stringify({ transaction_ids: [id] })
        });
        const data = await res.json();
        if (res.ok) {
            alert(data.message || '恢复成功');
            loadTrashList();
            loadTransactions();
        } else {
            alert(`恢复失败：${data.detail || '未知错误'}`);
        }
    } catch (e) {
        alert('恢复失败，请稍后重试');
    }
};

// 批量恢复
const batchRestoreTrash = async () => {
    if (selectedTrash.value.length === 0) {
        alert('请先选择要恢复的记录');
        return;
    }
    try {
        const storedToken = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/admin/trash/restore`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${storedToken}`
            },
            body: JSON.stringify({ transaction_ids: selectedTrash.value })
        });
        const data = await res.json();
        if (res.ok) {
            alert(data.message || '批量恢复成功');
            selectedTrash.value = [];
            selectAllTrash.value = false;
            loadTrashList();
            loadTransactions();
        } else {
            alert(`恢复失败：${data.detail || '未知错误'}`);
        }
    } catch (e) {
        alert('恢复失败，请稍后重试');
    }
};

// 永久删除单条
const permanentlyDeleteOne = async (id) => {
    if (!confirm('⚠️ 永久确认\n\n确定要永久删除这条记录吗？此操作不可恢复！')) {
        return;
    }
    try {
        const storedToken = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/admin/trash/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${storedToken}`
            }
        });
        const data = await res.json();
        if (res.ok) {
            alert(data.message || '已永久删除');
            loadTrashList();
        } else {
            alert(`删除失败：${data.detail || '未知错误'}`);
        }
    } catch (e) {
        alert('删除失败，请稍后重试');
    }
};

// 批量永久删除
const batchPermanentlyDelete = async () => {
    if (selectedTrash.value.length === 0) {
        alert('请先选择要删除的记录');
        return;
    }
    if (!confirm(`⚠️ 永久确认\n\n确定要永久删除 ${selectedTrash.value.length} 条记录吗？此操作不可恢复！`)) {
        return;
    }
    try {
        const storedToken = localStorage.getItem('token');
        for (const id of selectedTrash.value) {
            await fetch(`${API_BASE}/admin/trash/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${storedToken}`
                }
            });
        }
        alert('批量永久删除成功');
        selectedTrash.value = [];
        selectAllTrash.value = false;
        loadTrashList();
    } catch (e) {
        alert('删除失败，请稍后重试');
    }
};

// ==================== 结算预览功能 ====================
// 状态变量
/*
const showSettlementPreview = ref(false);
const settlementMethod = ref('cash');
*/

// 计算属性
/*
const calculateTotalAmount = computed(() => {
    return selectedTransactions.value.reduce((sum, t) => sum + t.actual_price, 0);
});
*/

// 显示结算预览
/*
const showSettlementPreviewModal = () => {
    if (selectedTransactions.value.length === 0) {
        alert('请先选择要结算的记录');
        return;
    }
    settlementMethod.value = 'cash';
    showSettlementPreview.value = true;
};
*/

// 确认结算（带预览）
/*
const confirmSettlementWithPreview = async () => {
    try {
        const storedToken = localStorage.getItem('token');
        const res = await fetch(`${API_BASE}/admin/settle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${storedToken}`
            },
            body: JSON.stringify({
                transaction_ids: selectedTransactions.value,
                payment_method: settlementMethod.value
            })
        });
        const data = await res.json();
        if (res.ok) {
            alert('结算成功！');
            showSettlementPreview.value = false;
            selectedTransactions.value = [];
            loadTransactions();
        } else {
            alert(`结算失败：${data.detail || '未知错误'}`);
        }
    } catch (e) {
        alert('结算失败，请稍后重试');
    }
};
*/

// ==================== 全局快捷键 ====================
// 在 mounted 钩子中添加：
/*
const setupKeyboardShortcuts = () => {
    document.addEventListener('keydown', (e) => {
        // 忽略输入框中的快捷键
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // G + X 导航快捷键
        if (e.key === 'g' || e.key === 'G') {
            const handleNextKey = (event) => {
                const nextKey = event.key.toLowerCase();
                if (nextKey === 'd') {
                    activeTab.value = 'dashboard';
                    showToast('已跳转到数据看板', 'success');
                } else if (nextKey === 't') {
                    activeTab.value = 'transactions';
                    showToast('已跳转到交易记录', 'success');
                } else if (nextKey === 'i') {
                    activeTab.value = 'inventory';
                    showToast('已跳转到库存管理', 'success');
                }
                document.removeEventListener('keydown', handleNextKey);
            };
            document.addEventListener('keydown', handleNextKey, { once: true });
        }
        
        // / 聚焦搜索框
        if (e.key === '/' && !e.metaKey && !e.ctrlKey) {
            e.preventDefault();
            // focusSearch(); // 需要实现 focusSearch 函数
        }
        
        // ? 显示快捷键帮助
        if (e.key === '?' && !e.metaKey && !e.ctrlKey) {
            e.preventDefault();
            showShortcutsHelp.value = true;
        }
        
        // ESC 关闭弹窗
        if (e.key === 'Escape') {
            // closeAllModals(); // 需要实现 closeAllModals 函数
        }
    });
};

// 在 onMounted 中调用
setupKeyboardShortcuts();
*/

// ==================== 导出语句 ====================
// 在 return 语句中添加：
/*
return {
    // ... 其他导出
    
    // 回收站相关
    trashList,
    selectedTrash,
    selectAllTrash,
    loadTrashList,
    toggleSelectAllTrash,
    updateSelectAll,
    restoreOneFromTrash,
    batchRestoreTrash,
    permanentlyDeleteOne,
    batchPermanentlyDelete,
    
    // 结算预览相关
    showSettlementPreview,
    settlementMethod,
    calculateTotalAmount,
    showSettlementPreviewModal,
    confirmSettlementWithPreview,
    
    // ...
};
*/
