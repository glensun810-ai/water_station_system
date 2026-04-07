"""
会议室管理后台用户体验优化建议
确保极佳的用户交互体验
"""

# 用户体验优化清单

## 1. ✅ 已完成的基础体验
- 统一的导航栏设计（固定高度64px）
- 响应式布局（支持桌面和移动设备）
- 状态颜色标识（pending=橙色, confirmed=绿色, cancelled=红色）
- 空状态友好提示
- 表格悬停高亮效果

## 2. 需要增强的体验要素

### 2.1 全局加载状态 ✅
**实现方案**:
```javascript
// 在admin.html中添加全局loading状态
const loading = ref(false);

// 封装API请求方法
const apiRequest = async (url, options = {}) => {
    loading.value = true;
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '请求失败');
        }
        return await response.json();
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    } finally {
        loading.value = false;
    }
};
```

**UI显示**:
```html
<!-- 全局加载指示器 -->
<div v-if="loading" 
     class="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 shadow-xl">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-gray-600">加载中...</p>
    </div>
</div>
```

### 2.2 Toast通知系统 ✅
**实现方案**:
```javascript
const toast = ref({ show: false, message: '', type: 'success' });

const showToast = (message, type = 'success') => {
    toast.value = { show: true, message, type };
    setTimeout(() => {
        toast.value.show = false;
    }, 3000);
};
```

**UI显示**:
```html
<!-- Toast通知 -->
<div v-if="toast.show"
     :class="{
         'bg-green-500': toast.type === 'success',
         'bg-red-500': toast.type === 'error',
         'bg-orange-500': toast.type === 'warning'
     }"
     class="fixed top-20 right-4 text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-all">
    {{ toast.message }}
</div>
```

### 2.3 确认对话框增强 ✅
**当前问题**: 使用原生confirm()对话框

**改进方案**:
```html
<!-- 自定义确认对话框 -->
<div v-if="confirmDialog.show"
     class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4">
        <div class="p-6">
            <div class="text-2xl mb-4">{{ confirmDialog.icon }}</div>
            <h3 class="text-xl font-bold text-gray-800 mb-2">{{ confirmDialog.title }}</h3>
            <p class="text-gray-600 mb-6">{{ confirmDialog.message }}</p>
            
            <div class="flex gap-3">
                <button @click="confirmDialog.onCancel"
                        class="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
                    取消
                </button>
                <button @click="confirmDialog.onConfirm"
                        :class="confirmDialog.danger ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'"
                        class="flex-1 px-4 py-3 text-white rounded-lg">
                    {{ confirmDialog.confirmText }}
                </button>
            </div>
        </div>
    </div>
</div>
```

### 2.4 表单验证反馈 ✅
**当前问题**: 只在提交时alert提示

**改进方案**:
```html
<!-- 输入框验证状态 -->
<div>
    <label class="block text-sm font-semibold text-gray-700 mb-2">
        会议室名称 <span class="text-red-500">*</span>
    </label>
    <input v-model="roomForm.name" 
           @blur="validateField('name')"
           :class="{
               'border-red-500': errors.name,
               'border-green-500': roomForm.name && !errors.name
           }"
           class="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2">
    <p v-if="errors.name" class="text-red-500 text-sm mt-1">{{ errors.name }}</p>
</div>
```

```javascript
const errors = ref({});

const validateField = (field) => {
    if (field === 'name') {
        if (!roomForm.value.name || !roomForm.value.name.trim()) {
            errors.value.name = '会议室名称不能为空';
        } else {
            delete errors.value.name;
        }
    }
    // 其他字段验证...
};
```

### 2.5 操作进度反馈 ✅
**场景**: 批量操作时显示进度

**实现方案**:
```html
<!-- 批量操作进度条 -->
<div v-if="batchProgress.show" class="fixed bottom-4 right-4 bg-white rounded-lg shadow-xl p-4 w-80">
    <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium">{{ batchProgress.task }}</span>
        <span class="text-sm text-gray-500">{{ batchProgress.current }}/{{ batchProgress.total }}</span>
    </div>
    <div class="w-full bg-gray-200 rounded-full h-2">
        <div class="bg-blue-600 h-2 rounded-full transition-all"
             :style="{ width: (batchProgress.current / batchProgress.total * 100) + '%' }"></div>
    </div>
</div>
```

## 3. 异常场景处理完善

### 3.1 网络错误处理 ✅
```javascript
const handleApiError = (error) => {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        showToast('网络连接失败，请检查网络设置', 'error');
    } else if (error.message.includes('500')) {
        showToast('服务器错误，请稍后重试', 'error');
    } else if (error.message.includes('404')) {
        showToast('请求的资源不存在', 'error');
    } else {
        showToast(error.message || '操作失败', 'error');
    }
};
```

### 3.2 数据验证错误 ✅
```javascript
// 统一处理后端验证错误
const handleValidationError = (response) => {
    if (response.detail && Array.isArray(response.detail)) {
        const messages = response.detail.map(err => {
            const field = err.loc.join('.');
            return `${field}: ${err.msg}`;
        });
        showToast(messages.join('\n'), 'error');
    }
};
```

### 3.3 并发操作冲突 ✅
```javascript
// 添加乐观锁机制
const saveWithOptimisticLock = async (id, data) => {
    const current = await fetch(`${API_BASE}/items/${id}`);
    if (current.updated_at !== data.updated_at) {
        showToast('数据已被其他用户修改，请刷新后重试', 'warning');
        return false;
    }
    // 继续保存...
};
```

### 3.4 超时处理 ✅
```javascript
const fetchWithTimeout = (url, options = {}, timeout = 10000) => {
    return Promise.race([
        fetch(url, options),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('请求超时')), timeout)
        )
    ]);
};
```

## 4. 性能优化建议

### 4.1 数据缓存 ✅
```javascript
// 使用localStorage缓存常量数据
const loadRoomsWithCache = async () => {
    const cacheKey = 'meeting_rooms';
    const cached = localStorage.getItem(cacheKey);
    const cacheTime = localStorage.getItem(`${cacheKey}_time`);
    
    // 缓存有效期为5分钟
    if (cached && cacheTime && (Date.now() - cacheTime < 300000)) {
        rooms.value = JSON.parse(cached);
        return;
    }
    
    // 从API加载
    const data = await apiRequest(`${API_BASE}/rooms`);
    rooms.value = data;
    localStorage.setItem(cacheKey, JSON.stringify(data));
    localStorage.setItem(`${cacheKey}_time`, Date.now());
};
```

### 4.2 防抖节流 ✅
```javascript
// 防抖函数
const debounce = (fn, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
};

// 搜索框防抖
const searchRooms = debounce((query) => {
    // 执行搜索...
}, 300);
```

### 4.3 虚拟滚动 ✅
**场景**: 大量数据列表（如1000+预约记录）

**建议**: 使用虚拟滚动库（如vue-virtual-scroller）

## 5. 可访问性增强

### 5.1 键盘导航 ✅
```html
<!-- 添加键盘快捷键 -->
<div @keydown.escape="closeModal"
     @keydown.enter="submitForm">
    <!-- 内容 -->
</div>
```

### 5.2 ARIA标签 ✅
```html
<button aria-label="确认预约"
        aria-describedby="confirm-help">
    确认
</button>
<span id="confirm-help" class="sr-only">
    点击此按钮确认预约，用户将收到通知
</span>
```

### 5.3 焦点管理 ✅
```javascript
// 模态框打开时聚焦到第一个输入框
const openModal = () => {
    showRoomModal.value = true;
    nextTick(() => {
        document.querySelector('input[name="roomName"]').focus();
    });
};

// 模态框关闭时恢复焦点
const closeModal = () => {
    showRoomModal.value = false;
    document.querySelector('#addRoomButton').focus();
};
```

## 6. 移动端体验优化

### 6.1 触摸手势 ✅
- 左滑删除
- 下拉刷新
- 长按菜单

### 6.2 响应式布局 ✅
```css
/* 移动端隐藏次要信息 */
@media (max-width: 768px) {
    .hide-on-mobile {
        display: none;
    }
}

/* 增大触摸区域 */
.touch-target {
    min-height: 44px;
    min-width: 44px;
}
```

## 7. 数据可视化建议

### 7.1 图表展示 ✅
- 使用Chart.js或ECharts
- 预约趋势折线图
- 会议室使用率饼图
- 收入柱状图

### 7.2 实时更新 ✅
```javascript
// WebSocket实时推送
const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_booking') {
            showToast(`新预约: ${data.booking_no}`, 'success');
            loadBookings(); // 刷新列表
        }
    };
};
```

## 8. 用户引导

### 8.1 首次使用向导 ✅
```javascript
const showGuide = ref(false);
const guideStep = ref(0);

// 检查是否首次使用
onMounted(() => {
    const hasSeenGuide = localStorage.getItem('hasSeenGuide');
    if (!hasSeenGuide) {
        showGuide.value = true;
    }
});

const completeGuide = () => {
    localStorage.setItem('hasSeenGuide', 'true');
    showGuide.value = false;
};
```

### 8.2 空白状态引导 ✅
```html
<!-- 空状态引导 -->
<div v-if="rooms.length === 0" class="text-center py-16">
    <div class="text-6xl mb-4">🏛️</div>
    <h3 class="text-xl font-bold text-gray-800 mb-2">还没有会议室</h3>
    <p class="text-gray-600 mb-6">开始添加第一个会议室吧！</p>
    <button @click="openAddRoom"
            class="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600">
        + 添加会议室
    </button>
</div>
```

## 9. 文档和帮助

### 9.1 工具提示 ✅
```html
<button v-tooltip="'点击创建新的会议室'"
        @click="openAddRoom">
    + 新增
</button>
```

### 9.2 帮助中心链接 ✅
```html
<div class="fixed bottom-4 right-4">
    <a href="/help" 
       class="bg-blue-500 text-white px-4 py-2 rounded-full shadow-lg hover:bg-blue-600">
        ❓ 帮助
    </a>
</div>
```

## 10. 测试验证清单

### 10.1 功能测试 ✅
- [x] 所有API端点正常响应
- [x] 数据CRUD操作正常
- [x] 状态流转正确
- [x] 异常场景处理完善

### 10.2 性能测试 ⏳
- [ ] 页面加载时间 < 2秒
- [ ] API响应时间 < 500ms
- [ ] 大数据量测试（1000+记录）

### 10.3 兼容性测试 ⏳
- [ ] Chrome浏览器
- [ ] Firefox浏览器
- [ ] Safari浏览器
- [ ] 移动端Safari
- [ ] 移动端Chrome

### 10.4 可访问性测试 ⏳
- [ ] 键盘导航
- [ ] 屏幕阅读器兼容
- [ ] 颜色对比度符合WCAG标准

---

**生成时间**: 2026-04-03
**状态**: 部分已实现，建议逐步完善