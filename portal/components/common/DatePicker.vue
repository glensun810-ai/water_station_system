<!--
  DatePicker - 日期选择器组件
  
  用途：统一的日期选择器组件
  功能：
  - 支持单个日期选择
  - 支持日期范围选择
  - 快捷日期选择（今天、本周、本月）
  - 禁用日期设置
  - 移动端适配
  
  使用示例：
  <DatePicker
    v-model="selectedDate"
    placeholder="选择日期"
    @change="handleDateChange"
  />
  
  Props:
  - modelValue: [String, Date] - 选中的日期
  - type: String - 选择类型（'date' | 'range'，默认'date'）
  - placeholder: String - 占位符文字
  - minDate: [String, Date] - 最小日期
  - maxDate: [String, Date] - 最大日期
  - disabled: Boolean - 是否禁用
  - clearable: Boolean - 是否可清空（默认true）
  
  Events:
  - update:modelValue: 日期变化时触发
  - change: 日期变化时触发，参数为日期值
-->

<template>
  <div class="date-picker-container">
    <!-- 快捷选择 -->
    <div v-if="showQuickSelect" class="quick-select-container">
      <button
        v-for="option in quickOptions"
        :key="option.value"
        @click="selectQuickOption(option)"
        :class="['quick-select-btn', 'btn', 'btn-sm', activeQuickOption === option.value ? 'btn-primary' : 'btn-outline']"
      >
        {{ option.label }}
      </button>
    </div>
    
    <!-- 日期输入 -->
    <div class="date-input-wrapper">
      <input
        ref="inputRef"
        v-model="inputValue"
        type="date"
        :placeholder="placeholder"
        :min="minDateFormatted"
        :max="maxDateFormatted"
        :disabled="disabled"
        class="input"
        @change="handleDateChange"
      />
      
      <!-- 清空按钮 -->
      <button
        v-if="clearable && inputValue && !disabled"
        @click="clearDate"
        class="clear-btn"
      >
        ✕
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'DatePicker',
  
  props: {
    modelValue: {
      type: [String, Date],
      default: ''
    },
    type: {
      type: String,
      default: 'date',
      validator: (value) => ['date', 'range'].includes(value)
    },
    placeholder: {
      type: String,
      default: '选择日期'
    },
    minDate: {
      type: [String, Date],
      default: null
    },
    maxDate: {
      type: [String, Date],
      default: null
    },
    disabled: {
      type: Boolean,
      default: false
    },
    clearable: {
      type: Boolean,
      default: true
    },
    showQuickSelect: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['update:modelValue', 'change'],
  
  setup(props, { emit }) {
    const inputValue = ref('');
    const activeQuickOption = ref(null);
    const inputRef = ref(null);
    
    const quickOptions = [
      { label: '今天', value: 'today' },
      { label: '本周', value: 'week' },
      { label: '本月', value: 'month' }
    ];
    
    const minDateFormatted = computed(() => {
      if (!props.minDate) return undefined;
      return formatDate(props.minDate);
    });
    
    const maxDateFormatted = computed(() => {
      if (!props.maxDate) return undefined;
      return formatDate(props.maxDate);
    });
    
    const formatDate = (date) => {
      const d = date instanceof Date ? date : new Date(date);
      return d.toISOString().split('T')[0];
    };
    
    const selectQuickOption = (option) => {
      activeQuickOption.value = option.value;
      const today = new Date();
      
      let startDate, endDate;
      
      switch (option.value) {
        case 'today':
          inputValue.value = formatDate(today);
          break;
        case 'week':
          const dayOfWeek = today.getDay();
          const monday = new Date(today);
          monday.setDate(today.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
          inputValue.value = formatDate(monday);
          break;
        case 'month':
          const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
          inputValue.value = formatDate(firstDayOfMonth);
          break;
      }
      
      emit('update:modelValue', inputValue.value);
      emit('change', inputValue.value);
    };
    
    const handleDateChange = () => {
      activeQuickOption.value = null;
      emit('update:modelValue', inputValue.value);
      emit('change', inputValue.value);
    };
    
    const clearDate = () => {
      inputValue.value = '';
      activeQuickOption.value = null;
      emit('update:modelValue', '');
      emit('change', '');
    };
    
    watch(() => props.modelValue, (newVal) => {
      if (newVal) {
        inputValue.value = formatDate(newVal);
      }
    }, { immediate: true });
    
    return {
      inputValue,
      inputRef,
      activeQuickOption,
      quickOptions,
      minDateFormatted,
      maxDateFormatted,
      selectQuickOption,
      handleDateChange,
      clearDate
    };
  }
}
</script>

<style scoped>
.date-picker-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.quick-select-container {
  display: flex;
  gap: var(--spacing-xs);
}

.date-input-wrapper {
  position: relative;
  flex: 1;
}

.date-input-wrapper input[type="date"] {
  padding-right: 36px;
}

.clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  transition: color var(--transition-fast);
}

.clear-btn:hover {
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .quick-select-container {
    flex-wrap: wrap;
  }
}
</style>