<!--
  ConfirmDialog - 确认对话框组件
  
  用途：统一的水站管理和会议室预定的确认对话框组件
  功能：
  - 支持多种类型（info、warning、danger）
  - 支持自定义标题、消息
  - 支持输入框（可选）
  - 支持异步确认操作
  - 键盘快捷键（Enter确认、Esc取消）
  
  使用示例：
  <ConfirmDialog
    v-model="showDialog"
    title="确认删除"
    message="删除后无法恢复，是否继续？"
    type="danger"
    @confirm="handleConfirm"
    @cancel="handleCancel"
  />
  
  Props:
  - modelValue: Boolean - 是否显示对话框
  - title: String - 对话框标题
  - message: String - 对话框消息
  - type: String - 对话框类型（'info' | 'warning' | 'danger'，默认'info'）
  - confirmText: String - 确认按钮文字（默认'确认'）
  - cancelText: String - 取消按钮文字（默认'取消'）
  - inputLabel: String - 输入框标签（可选）
  - inputPlaceholder: String - 输入框占位符（可选）
  - loading: Boolean - 确认按钮加载状态
  
  Events:
  - update:modelValue: 显示状态变化时触发
  - confirm: 确认时触发，参数为输入框值（如果有）
  - cancel: 取消时触发
-->

<template>
  <div v-if="modelValue" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-content confirm-dialog" @click.stop>
      <!-- 图标 -->
      <div :class="['dialog-icon', `dialog-icon-${type}`]">
        <span v-if="type === 'danger'">⚠</span>
        <span v-else-if="type === 'warning'">⚠</span>
        <span v-else>ℹ</span>
      </div>
      
      <!-- 标题 -->
      <h3 class="dialog-title">{{ title }}</h3>
      
      <!-- 消息 -->
      <p class="dialog-message">{{ message }}</p>
      
      <!-- 输入框（可选） -->
      <div v-if="inputLabel" class="dialog-input-container">
        <label class="dialog-input-label">{{ inputLabel }}</label>
        <input
          ref="inputRef"
          v-model="inputValue"
          type="text"
          :placeholder="inputPlaceholder"
          class="input"
          @keyup.enter="handleConfirm"
        />
      </div>
      
      <!-- 按钮组 -->
      <div class="dialog-actions">
        <button
          @click="handleCancel"
          class="btn btn-outline btn-md"
          :disabled="loading"
        >
          {{ cancelText }}
        </button>
        <button
          @click="handleConfirm"
          :class="['btn', 'btn-md', confirmButtonClass]"
          :disabled="loading"
        >
          <span v-if="loading" class="spinner spinner-sm"></span>
          <span v-else>{{ confirmText }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, nextTick } from 'vue';

export default {
  name: 'ConfirmDialog',
  
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: '确认操作'
    },
    message: {
      type: String,
      default: '是否确认此操作？'
    },
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['info', 'warning', 'danger'].includes(value)
    },
    confirmText: {
      type: String,
      default: '确认'
    },
    cancelText: {
      type: String,
      default: '取消'
    },
    inputLabel: {
      type: String,
      default: ''
    },
    inputPlaceholder: {
      type: String,
      default: ''
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['update:modelValue', 'confirm', 'cancel'],
  
  setup(props, { emit }) {
    const inputValue = ref('');
    const inputRef = ref(null);
    
    const confirmButtonClass = computed(() => {
      switch (props.type) {
        case 'danger':
          return 'btn-danger';
        case 'warning':
          return 'btn-warning';
        default:
          return 'btn-primary';
      }
    });
    
    const handleConfirm = () => {
      emit('confirm', inputValue.value);
    };
    
    const handleCancel = () => {
      emit('cancel');
      emit('update:modelValue', false);
    };
    
    const handleOverlayClick = () => {
      if (!props.loading) {
        handleCancel();
      }
    };
    
    // 监听显示状态，自动聚焦输入框
    watch(() => props.modelValue, async (newVal) => {
      if (newVal && props.inputLabel) {
        await nextTick();
        inputRef.value?.focus();
      }
      if (!newVal) {
        inputValue.value = '';
      }
    });
    
    // 键盘事件监听
    const handleKeydown = (e) => {
      if (props.modelValue) {
        if (e.key === 'Escape') {
          handleCancel();
        } else if (e.key === 'Enter' && !props.loading) {
          handleConfirm();
        }
      }
    };
    
    onMounted(() => {
      window.addEventListener('keydown', handleKeydown);
    });
    
    onUnmounted(() => {
      window.removeEventListener('keydown', handleKeydown);
    });
    
    return {
      inputValue,
      inputRef,
      confirmButtonClass,
      handleConfirm,
      handleCancel,
      handleOverlayClick
    };
  }
}
</script>

<style scoped>
.confirm-dialog {
  max-width: 400px;
  padding: var(--spacing-xl);
}

.dialog-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--spacing-lg);
  font-size: 24px;
}

.dialog-icon-info {
  background-color: var(--info-light);
  color: var(--info);
}

.dialog-icon-warning {
  background-color: var(--warning-light);
  color: var(--warning);
}

.dialog-icon-danger {
  background-color: var(--danger-light);
  color: var(--danger);
}

.dialog-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: var(--spacing-md);
}

.dialog-message {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: var(--spacing-lg);
  line-height: var(--line-height-relaxed);
}

.dialog-input-container {
  margin-bottom: var(--spacing-lg);
}

.dialog-input-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
}

.dialog-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
}

.spinner-sm {
  width: 16px;
  height: 16px;
  border-width: 2px;
  border-top-color: white;
}

@media (max-width: 768px) {
  .confirm-dialog {
    max-width: 100%;
    padding: var(--spacing-lg);
  }
  
  .dialog-actions {
    flex-direction: column;
  }
  
  .dialog-actions .btn {
    width: 100%;
  }
}
</style>