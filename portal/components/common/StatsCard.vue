<!--
  StatsCard - 统计卡片组件
  
  用途：统一的水站管理和会议室预定的Dashboard统计卡片组件
  功能：
  - 显示统计数据（标题、数值、副标题）
  - 支持图标展示
  - 支持多种颜色主题
  - 支持趋势指示（上升/下降/持平）
  - 支持点击交互
  - 移动端响应式布局
  
  使用示例：
  <StatsCard 
    title="今日预约" 
    :value="23" 
    icon="📅"
    color="primary"
    :trend="10"
    @click="handleClick"
  />
  
  Props:
  - title: String - 统计标题
  - value: [Number, String] - 统计数值
  - subtitle: String - 副标题（可选）
  - icon: String - 图标（emoji或class名）
  - iconType: String - 图标类型（'emoji' | 'class'，默认'emoji'）
  - color: String - 颜色主题（'primary' | 'success' | 'warning' | 'danger' | 'info'，默认'primary'）
  - trend: Number - 趋势值（正数上升，负数下降，0持平）
  - trendLabel: String - 趋势标签（默认'较昨日'）
  - clickable: Boolean - 是否可点击（默认false）
  - loading: Boolean - 加载状态（默认false）
  
  Events:
  - click: 点击卡片时触发
  
  Slots:
  - icon: 自定义图标内容
  - value: 自定义数值内容
  - trend: 自定义趋势内容
  - footer: 卡片底部内容
-->

<template>
  <div 
    @click="handleClick"
    :class="[
      'stats-card',
      'card',
      `stats-card-${color}`,
      { 'stats-card-clickable': clickable, 'stats-card-loading': loading }
    ]"
  >
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner spinner-sm"></div>
    </div>
    
    <!-- 卡片内容 -->
    <template v-else>
      <!-- 顶部：图标和标题 -->
      <div class="stats-card-header">
        <div class="stats-card-icon-wrapper">
          <slot name="icon">
            <span v-if="iconType === 'emoji'" class="stats-card-icon">{{ icon }}</span>
            <i v-else :class="['stats-card-icon', icon]"></i>
          </slot>
        </div>
        <div class="stats-card-title">{{ title }}</div>
      </div>
      
      <!-- 中部：数值和副标题 -->
      <div class="stats-card-body">
        <div class="stats-card-value">
          <slot name="value">
            {{ formattedValue }}
          </slot>
        </div>
        <div v-if="subtitle" class="stats-card-subtitle">{{ subtitle }}</div>
      </div>
      
      <!-- 底部：趋势指示 -->
      <div v-if="trend !== undefined && trend !== null" class="stats-card-footer">
        <slot name="trend">
          <div class="trend-container" :class="trendClass">
            <span class="trend-icon">{{ trendIcon }}</span>
            <span class="trend-value">{{ Math.abs(trend) }}%</span>
            <span class="trend-label">{{ trendLabel }}</span>
          </div>
        </slot>
      </div>
      
      <!-- 自定义底部内容 -->
      <slot name="footer"></slot>
    </template>
  </div>
</template>

<script>
export default {
  name: 'StatsCard',
  
  props: {
    title: {
      type: String,
      required: true
    },
    value: {
      type: [Number, String],
      default: 0
    },
    subtitle: {
      type: String,
      default: ''
    },
    icon: {
      type: String,
      default: '📊'
    },
    iconType: {
      type: String,
      default: 'emoji',
      validator: (value) => ['emoji', 'class'].includes(value)
    },
    color: {
      type: String,
      default: 'primary',
      validator: (value) => ['primary', 'success', 'warning', 'danger', 'info'].includes(value)
    },
    trend: {
      type: Number,
      default: undefined
    },
    trendLabel: {
      type: String,
      default: '较昨日'
    },
    clickable: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['click'],
  
  computed: {
    formattedValue() {
      if (typeof this.value === 'number') {
        return this.value.toLocaleString();
      }
      return this.value;
    },
    
    trendClass() {
      if (this.trend > 0) return 'trend-up';
      if (this.trend < 0) return 'trend-down';
      return 'trend-flat';
    },
    
    trendIcon() {
      if (this.trend > 0) return '↑';
      if (this.trend < 0) return '↓';
      return '→';
    }
  },
  
  methods: {
    handleClick() {
      if (this.clickable && !this.loading) {
        this.$emit('click');
      }
    }
  }
}
</script>

<style scoped>
.stats-card {
  position: relative;
  overflow: hidden;
  cursor: default;
  transition: all var(--transition-base) ease;
  border: 1px solid var(--border);
}

.stats-card-clickable {
  cursor: pointer;
}

.stats-card-clickable:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.stats-card-clickable:active {
  transform: translateY(0);
}

.stats-card-loading {
  opacity: 0.8;
  pointer-events: none;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.spinner-sm {
  width: 24px;
  height: 24px;
  border-width: 3px;
}

/* 颜色主题 */
.stats-card-primary {
  border-left: 4px solid var(--primary);
}

.stats-card-primary .stats-card-icon-wrapper {
  background-color: var(--primary-light);
  color: var(--primary);
}

.stats-card-success {
  border-left: 4px solid var(--success);
}

.stats-card-success .stats-card-icon-wrapper {
  background-color: var(--success-light);
  color: var(--success-dark);
}

.stats-card-warning {
  border-left: 4px solid var(--warning);
}

.stats-card-warning .stats-card-icon-wrapper {
  background-color: var(--warning-light);
  color: var(--warning-dark);
}

.stats-card-danger {
  border-left: 4px solid var(--danger);
}

.stats-card-danger .stats-card-icon-wrapper {
  background-color: var(--danger-light);
  color: var(--danger-dark);
}

.stats-card-info {
  border-left: 4px solid var(--info);
}

.stats-card-info .stats-card-icon-wrapper {
  background-color: var(--info-light);
  color: var(--info-dark);
}

/* 头部样式 */
.stats-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.stats-card-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stats-card-icon {
  font-size: 24px;
}

.stats-card-title {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* 内容区域 */
.stats-card-body {
  margin-bottom: var(--spacing-md);
}

.stats-card-value {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  margin-bottom: var(--spacing-xs);
}

.stats-card-subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

/* 趋势区域 */
.stats-card-footer {
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-light);
}

.trend-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-xs);
}

.trend-icon {
  font-size: 14px;
  font-weight: 600;
}

.trend-value {
  font-weight: 600;
}

.trend-label {
  color: var(--text-tertiary);
  margin-left: var(--spacing-xs);
}

.trend-up {
  color: var(--success);
}

.trend-down {
  color: var(--danger);
}

.trend-flat {
  color: var(--text-tertiary);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .stats-card {
    padding: var(--spacing-md);
  }
  
  .stats-card-icon-wrapper {
    width: 40px;
    height: 40px;
  }
  
  .stats-card-icon {
    font-size: 20px;
  }
  
  .stats-card-value {
    font-size: var(--font-size-2xl);
  }
  
  .stats-card-title {
    font-size: var(--font-size-xs);
  }
  
  .stats-card-clickable:active {
    transform: scale(0.98);
  }
}
</style>