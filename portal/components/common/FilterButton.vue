<!--
  FilterButton - 筛选按钮组件
  
  用途：统一的筛选按钮组件，用于Tab切换和状态筛选
  功能：
  - 支持多种样式（segment、tab、card）
  - 支持徽章显示
  - 支持图标
  - 移动端适配
  
  使用示例：
  <FilterButton
    v-model="activeFilter"
    :options="filterOptions"
    type="segment"
    @change="handleFilterChange"
  />
  
  Props:
  - modelValue: [String, Number] - 当前选中的值
  - options: Array - 选项数组 [{ label: '待确认', value: 'pending', count: 5, icon: '⏳' }]
  - type: String - 按钮类型（'segment' | 'tab' | 'card'，默认'segment'）
  - showCount: Boolean - 是否显示数量徽章（默认false）
  - disabled: Boolean - 是否禁用
  
  Events:
  - update:modelValue: 选中值变化时触发
  - change: 筛选变化时触发，参数为选中值和选项对象
-->

<template>
  <div :class="['filter-button-container', `filter-button-${type}`]">
    <div
      v-for="option in options"
      :key="option.value"
      @click="handleClick(option)"
      :class="[
        'filter-button-item',
        { 
          'filter-button-active': modelValue === option.value,
          'filter-button-disabled': disabled
        }
      ]"
    >
      <!-- 图标 -->
      <span v-if="option.icon" class="filter-button-icon">{{ option.icon }}</span>
      
      <!-- 标签 -->
      <span class="filter-button-label">{{ option.label }}</span>
      
      <!-- 数量徽章 -->
      <span v-if="showCount && option.count !== undefined" class="filter-button-count">
        {{ option.count }}
      </span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FilterButton',
  
  props: {
    modelValue: {
      type: [String, Number],
      required: true
    },
    options: {
      type: Array,
      required: true,
      validator: (value) => {
        return value.every(opt => 'label' in opt && 'value' in opt);
      }
    },
    type: {
      type: String,
      default: 'segment',
      validator: (value) => ['segment', 'tab', 'card'].includes(value)
    },
    showCount: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['update:modelValue', 'change'],
  
  methods: {
    handleClick(option) {
      if (!this.disabled && this.modelValue !== option.value) {
        this.$emit('update:modelValue', option.value);
        this.$emit('change', option.value, option);
      }
    }
  }
}
</script>

<style scoped>
.filter-button-container {
  display: flex;
  gap: var(--spacing-sm);
}

.filter-button-segment {
  background-color: var(--bg-primary);
  padding: var(--spacing-xs);
  border-radius: var(--radius-lg);
}

.filter-button-tab {
  border-bottom: 2px solid var(--border);
}

.filter-button-card {
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.filter-button-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast) ease;
  user-select: none;
}

.filter-button-segment .filter-button-item {
  background-color: transparent;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.filter-button-segment .filter-button-active {
  background-color: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.filter-button-tab .filter-button-item {
  border-bottom: 2px solid transparent;
  padding: var(--spacing-md) var(--spacing-lg);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  margin-bottom: -2px;
}

.filter-button-tab .filter-button-active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

.filter-button-card .filter-button-item {
  background-color: var(--bg-card);
  border: 2px solid var(--border);
  padding: var(--spacing-md) var(--spacing-lg);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
  min-width: 120px;
  justify-content: center;
}

.filter-button-card .filter-button-active {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: var(--text-inverse);
  border-color: transparent;
  box-shadow: var(--shadow-md);
}

.filter-button-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.filter-button-icon {
  font-size: 16px;
}

.filter-button-label {
  font-size: var(--font-size-sm);
}

.filter-button-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background-color: var(--danger);
  color: var(--text-inverse);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;
}

@media (max-width: 768px) {
  .filter-button-container {
    overflow-x: auto;
    scrollbar-width: none;
  }
  
  .filter-button-container::-webkit-scrollbar {
    display: none;
  }
  
  .filter-button-item:active {
    transform: scale(0.95);
  }
}
</style>