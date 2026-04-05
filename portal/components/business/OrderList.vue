<!--
  OrderList - 订单列表组件
  
  用途：统一的水站领水记录和会议室预约记录查询组件
  功能：
  - Tab切换（我的订单/全部订单）
  - 状态筛选
  - 关键词搜索
  - 列表展示
  - 详情查看
  - 移动端适配
  
  使用示例：
  <OrderList
    :api-url="'/api/user/orders'"
    :type="'water'"
    :tabs="orderTabs"
    @item-click="handleItemClick"
  />
  
  Props:
  - apiUrl: String - API地址
  - type: String - 订单类型（'water' | 'meeting'）
  - tabs: Array - Tab配置 [{ label: '我的订单', value: 'mine' }]
  - statusOptions: Array - 状态选项
  - showSearch: Boolean - 是否显示搜索框（默认true）
  - showStatusFilter: Boolean - 是否显示状态筛选（默认true）
  
  Events:
  - item-click: 订单项点击时触发
  - load: 数据加载完成时触发
-->

<template>
  <div class="order-list-container">
    <!-- Tab切换 -->
    <div v-if="tabs && tabs.length > 0" class="tab-container mb-md">
      <FilterButton
        v-model="activeTab"
        :options="tabs"
        type="segment"
        @change="handleTabChange"
      />
    </div>
    
    <!-- 筛选器 -->
    <div class="filter-container mb-md">
      <!-- 搜索框 -->
      <div v-if="showSearch" class="search-wrapper">
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索订单编号、产品名称..."
          class="input"
          @input="handleSearch"
        />
      </div>
      
      <!-- 状态筛选 -->
      <div v-if="showStatusFilter" class="status-filter-wrapper">
        <select v-model="statusFilter" class="select" @change="handleFilterChange">
          <option value="">全部状态</option>
          <option
            v-for="status in statusOptions"
            :key="status.value"
            :value="status.value"
          >
            {{ status.label }}
          </option>
        </select>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p class="text-secondary mt-md">加载订单列表...</p>
    </div>
    
    <!-- 空状态 -->
    <div v-else-if="filteredOrders.length === 0" class="empty-container">
      <div class="text-tertiary text-2xl mb-md">📭</div>
      <p class="text-secondary">暂无订单记录</p>
    </div>
    
    <!-- 订单列表 -->
    <div v-else class="order-list">
      <div
        v-for="order in filteredOrders"
        :key="order.id"
        @click="handleItemClick(order)"
        class="order-item card card-clickable mb-sm"
      >
        <!-- 订单头部 -->
        <div class="order-header flex items-center justify-between mb-sm">
          <span class="order-no text-secondary">{{ order.order_no || order.booking_no }}</span>
          <span :class="['status-tag', `status-${order.status}`]">
            {{ getStatusText(order.status) }}
          </span>
        </div>
        
        <!-- 订单主体 -->
        <div class="order-body">
          <div class="order-title font-semibold mb-xs">
            {{ order.product_name || order.room_name || order.meeting_title }}
          </div>
          
          <div class="order-info flex items-center gap-md text-sm text-secondary">
            <span v-if="order.quantity">
              <span class="text-tertiary">数量:</span> {{ order.quantity }}
            </span>
            <span v-if="order.duration">
              <span class="text-tertiary">时长:</span> {{ order.duration }}小时
            </span>
            <span v-if="order.booking_date">
              <span class="text-tertiary">日期:</span> {{ order.booking_date }}
            </span>
          </div>
          
          <div class="order-amount text-right mt-sm">
            <span class="text-tertiary text-sm">金额: </span>
            <span class="font-bold text-lg text-primary">¥{{ (order.total_fee || order.amount || 0).toFixed(2) }}</span>
          </div>
        </div>
        
        <!-- 订单时间 -->
        <div class="order-time text-xs text-tertiary mt-sm">
          {{ formatTime(order.created_at) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import FilterButton from './FilterButton.vue';

export default {
  name: 'OrderList',
  
  components: {
    FilterButton
  },
  
  props: {
    apiUrl: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'water',
      validator: (value) => ['water', 'meeting'].includes(value)
    },
    tabs: {
      type: Array,
      default: () => []
    },
    statusOptions: {
      type: Array,
      default: () => [
        { label: '待确认', value: 'pending' },
        { label: '已确认', value: 'confirmed' },
        { label: '已完成', value: 'completed' },
        { label: '已取消', value: 'cancelled' }
      ]
    },
    showSearch: {
      type: Boolean,
      default: true
    },
    showStatusFilter: {
      type: Boolean,
      default: true
    }
  },
  
  emits: ['item-click', 'load'],
  
  setup(props, { emit }) {
    const orders = ref([]);
    const loading = ref(false);
    const activeTab = ref(props.tabs[0]?.value || '');
    const keyword = ref('');
    const statusFilter = ref('');
    
    const filteredOrders = computed(() => {
      let result = orders.value;
      
      if (keyword.value) {
        const searchKey = keyword.value.toLowerCase();
        result = result.filter(order => 
          (order.order_no || order.booking_no || '').toLowerCase().includes(searchKey) ||
          (order.product_name || order.room_name || '').toLowerCase().includes(searchKey)
        );
      }
      
      if (statusFilter.value) {
        result = result.filter(order => order.status === statusFilter.value);
      }
      
      return result;
    });
    
    const loadOrders = async () => {
      loading.value = true;
      try {
        const res = await fetch(props.apiUrl);
        const data = await res.json();
        orders.value = Array.isArray(data) ? data : (data.items || []);
        emit('load', orders.value);
      } catch (error) {
        console.error('加载订单失败:', error);
      } finally {
        loading.value = false;
      }
    };
    
    const handleTabChange = () => {
      loadOrders();
    };
    
    const handleSearch = () => {
      // 搜索逻辑已在computed中处理
    };
    
    const handleFilterChange = () => {
      // 筛选逻辑已在computed中处理
    };
    
    const handleItemClick = (order) => {
      emit('item-click', order);
    };
    
    const getStatusText = (status) => {
      const statusMap = {
        'pending': '待确认',
        'confirmed': '已确认',
        'completed': '已完成',
        'cancelled': '已取消',
        'settled': '已结算'
      };
      return statusMap[status] || status;
    };
    
    const formatTime = (time) => {
      if (!time) return '';
      const date = new Date(time);
      return date.toLocaleString('zh-CN');
    };
    
    onMounted(() => {
      loadOrders();
    });
    
    return {
      orders,
      loading,
      activeTab,
      keyword,
      statusFilter,
      filteredOrders,
      handleTabChange,
      handleSearch,
      handleFilterChange,
      handleItemClick,
      getStatusText,
      formatTime
    };
  }
}
</script>

<style scoped>
.order-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.filter-container {
  display: flex;
  gap: var(--spacing-md);
}

.search-wrapper {
  flex: 1;
}

.status-filter-wrapper {
  min-width: 150px;
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.order-list {
  flex: 1;
  overflow-y: auto;
}

.order-item {
  padding: var(--spacing-md);
}

.order-header {
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-light);
}

.order-body {
  padding: var(--spacing-sm) 0;
}

.order-amount {
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-light);
}

@media (max-width: 768px) {
  .filter-container {
    flex-direction: column;
  }
  
  .status-filter-wrapper {
    min-width: 100%;
  }
  
  .order-item:active {
    transform: scale(0.98);
  }
}
</style>