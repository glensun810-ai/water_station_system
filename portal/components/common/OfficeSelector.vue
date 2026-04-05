<!--
  OfficeSelector - 办公室选择组件
  
  用途：统一的水站管理和会议室预定的办公室选择组件
  功能：
  - 卡片式办公室选择界面
  - 支持v-model双向绑定
  - 支持排除不活跃办公室
  - 显示办公室详细信息（名称、房间号、负责人）
  - 移动端响应式布局
  - 加载状态和错误处理
  
  使用示例：
  <OfficeSelector v-model="selectedOffice" @change="handleOfficeChange" />
  
  Props:
  - modelValue: Object - 当前选中的办公室对象
  - excludeInactive: Boolean - 是否排除不活跃办公室（默认true）
  - apiUrl: String - 自定义API地址（默认'/api/offices'）
  - showLeader: Boolean - 是否显示负责人（默认true）
  - columns: Number - 每行显示列数（默认2，移动端自动调整为1）
  
  Events:
  - update:modelValue: 选中办公室变化时触发
  - change: 办公室选择变化时触发，参数为选中的办公室对象
  - load: 办公室列表加载完成时触发，参数为办公室列表
  
  Slots:
  - empty: 办公室列表为空时的提示内容
  - error: 加载失败时的错误提示内容
-->

<template>
  <div class="office-selector">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p class="text-secondary mt-md">加载办公室列表...</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <slot name="error">
        <div class="card text-center p-xl">
          <div class="text-danger text-2xl mb-md">⚠</div>
          <p class="text-secondary mb-md">{{ error }}</p>
          <button @click="loadOffices" class="btn btn-primary btn-md">重试</button>
        </div>
      </slot>
    </div>
    
    <!-- 空状态 -->
    <div v-else-if="filteredOffices.length === 0" class="empty-container">
      <slot name="empty">
        <div class="card text-center p-xl">
          <div class="text-tertiary text-2xl mb-md">📭</div>
          <p class="text-secondary">暂无可用的办公室</p>
        </div>
      </slot>
    </div>
    
    <!-- 办公室列表 -->
    <div v-else class="office-grid" :style="gridStyle">
      <div 
        v-for="office in filteredOffices" 
        :key="office.id"
        @click="selectOffice(office)"
        :class="['office-card', 'card', 'card-clickable', { 'office-card-active': isSelected(office) }]"
      >
        <!-- 选中标识 -->
        <div v-if="isSelected(office)" class="selected-indicator">
          <svg class="check-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
          </svg>
        </div>
        
        <!-- 办公室信息 -->
        <div class="office-info">
          <div class="office-name">{{ office.name }}</div>
          <div class="office-room text-secondary">{{ office.room_number }}</div>
          <div v-if="showLeader && office.leader_name" class="office-leader text-tertiary">
            <span class="leader-icon">👤</span>
            {{ office.leader_name }}
          </div>
        </div>
        
        <!-- 状态标签 -->
        <div v-if="office.is_active !== undefined" class="status-badge">
          <span v-if="office.is_active" class="badge badge-success">活跃</span>
          <span v-else class="badge badge-warning">停用</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'OfficeSelector',
  
  props: {
    modelValue: {
      type: Object,
      default: null
    },
    excludeInactive: {
      type: Boolean,
      default: true
    },
    apiUrl: {
      type: String,
      default: '/api/offices'
    },
    showLeader: {
      type: Boolean,
      default: true
    },
    columns: {
      type: Number,
      default: 2,
      validator: (value) => value >= 1 && value <= 4
    }
  },
  
  emits: ['update:modelValue', 'change', 'load'],
  
  data() {
    return {
      offices: [],
      loading: false,
      error: null
    }
  },
  
  computed: {
    filteredOffices() {
      if (this.excludeInactive) {
        return this.offices.filter(office => office.is_active !== false);
      }
      return this.offices;
    },
    
    gridStyle() {
      return {
        'grid-template-columns': `repeat(${this.columns}, minmax(0, 1fr))`
      }
    }
  },
  
  mounted() {
    this.loadOffices();
  },
  
  methods: {
    async loadOffices() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await fetch(this.apiUrl);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        this.offices = Array.isArray(data) ? data : [];
        
        this.$emit('load', this.offices);
      } catch (err) {
        console.error('加载办公室列表失败:', err);
        this.error = '加载办公室列表失败，请重试';
      } finally {
        this.loading = false;
      }
    },
    
    selectOffice(office) {
      this.$emit('update:modelValue', office);
      this.$emit('change', office);
    },
    
    isSelected(office) {
      return this.modelValue && this.modelValue.id === office.id;
    }
  }
}
</script>

<style scoped>
.office-selector {
  width: 100%;
}

.loading-container,
.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.office-grid {
  display: grid;
  gap: var(--spacing-md);
}

.office-card {
  position: relative;
  cursor: pointer;
  transition: all var(--transition-base) ease;
  border: 2px solid var(--border);
  padding: var(--spacing-lg);
}

.office-card:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-md);
}

.office-card-active {
  border-color: var(--primary);
  background: linear-gradient(135deg, var(--primary-light) 0%, rgba(219, 234, 254, 0.5) 100%);
  box-shadow: var(--shadow-md);
}

.selected-indicator {
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-sm);
  width: 24px;
  height: 24px;
  background-color: var(--primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.check-icon {
  width: 14px;
  height: 14px;
  color: white;
}

.office-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.office-name {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.office-room {
  font-size: var(--font-size-sm);
}

.office-leader {
  font-size: var(--font-size-xs);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-xs);
}

.leader-icon {
  font-size: 14px;
}

.status-badge {
  position: absolute;
  bottom: var(--spacing-sm);
  right: var(--spacing-sm);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .office-grid {
    grid-template-columns: 1fr !important;
    gap: var(--spacing-sm);
  }
  
  .office-card {
    padding: var(--spacing-md);
  }
  
  .office-card:active {
    transform: scale(0.98);
  }
}
</style>