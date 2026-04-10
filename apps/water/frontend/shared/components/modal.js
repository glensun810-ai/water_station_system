/**
 * Modal模态框组件 v2.0
 * 提供模态框的打开、关闭、表单集成功能
 * 特性：ARIA可访问性、键盘导航、焦点管理、移动端优化
 */

class ModalClass {
  constructor() {
    this.modals = {};
    this.init();
  }

  init() {
    this.addStyles();
    this.setupGlobalKeyHandler();
  }

  addStyles() {
    if (!document.querySelector('#modal-animation-styles')) {
      const style = document.createElement('style');
      style.id = 'modal-animation-styles';
      style.textContent = `
        @keyframes toast-slide-out {
          from { opacity: 1; transform: translateX(0); }
          to { opacity: 0; transform: translateX(100%); }
        }
      `;
      document.head.appendChild(style);
    }
  }

  setupGlobalKeyHandler() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        Object.keys(this.modals).forEach(id => {
          const modalData = this.modals[id];
          if (modalData && modalData.backdrop.classList.contains('show')) {
            this.close(id);
          }
        });
      }
    });
  }

  create(options) {
    const { id, title, content, width = '35rem', onClose, ariaLabel } = options;

    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    backdrop.id = `modal-backdrop-${id}`;
    backdrop.setAttribute('role', 'dialog');
    backdrop.setAttribute('aria-modal', 'true');
    backdrop.setAttribute('aria-labelledby', `modal-title-${id}`);
    backdrop.setAttribute('aria-label', ariaLabel || title || '模态框');

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.maxWidth = width;
    modal.setAttribute('role', 'document');

    modal.innerHTML = `
      <div class="modal-header">
        <h3 class="modal-title" id="modal-title-${id}">${this.escapeHtml(title)}</h3>
        <button class="modal-close" aria-label="关闭对话框" title="关闭（按Esc键）">
          <i class="fas fa-times" aria-hidden="true"></i>
        </button>
      </div>
      <div class="modal-body">
        ${content}
      </div>
    `;

    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);

    const closeBtn = modal.querySelector('.modal-close');
    closeBtn.addEventListener('click', () => this.close(id));

    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        this.close(id);
      }
    });

    this.modals[id] = {
      backdrop,
      modal,
      onClose,
      previousActiveElement: null
    };

    return { backdrop, modal };
  }

  open(id) {
    const modalData = this.modals[id];
    if (modalData) {
      modalData.previousActiveElement = document.activeElement;
      modalData.backdrop.classList.add('show');
      document.body.style.overflow = 'hidden';

      setTimeout(() => {
        const firstFocusable = modalData.modal.querySelector(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (firstFocusable) {
          firstFocusable.focus();
        }
      }, 100);

      this.trapFocus(modalData.modal);
    }
  }

  close(id) {
    const modalData = this.modals[id];
    if (modalData) {
      modalData.backdrop.classList.remove('show');
      document.body.style.overflow = '';

      if (modalData.previousActiveElement) {
        modalData.previousActiveElement.focus();
      }

      if (modalData.onClose) {
        modalData.onClose();
      }
    }
  }

  destroy(id) {
    const modalData = this.modals[id];
    if (modalData) {
      if (modalData.backdrop.parentNode) {
        modalData.backdrop.parentNode.removeChild(modalData.backdrop);
      }
      delete this.modals[id];
    }
  }

  trapFocus(element) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    element.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstFocusable) {
            lastFocusable.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastFocusable) {
            firstFocusable.focus();
            e.preventDefault();
          }
        }
      }
    });
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  confirm(options) {
    const {
      title = '确认操作',
      message,
      confirmText = '确认',
      cancelText = '取消',
      onConfirm,
      onCancel,
      type = 'warning',
      danger = false
    } = options;

    const id = `confirm-${Date.now()}`;
    const icons = {
      warning: 'fas fa-exclamation-triangle',
      danger: 'fas fa-times-circle',
      info: 'fas fa-info-circle',
      success: 'fas fa-check-circle'
    };

    const colors = {
      warning: 'var(--color-warning-500)',
      danger: 'var(--color-error-500)',
      info: 'var(--color-info-500)',
      success: 'var(--color-success-500)'
    };

    const escapedMessage = this.escapeHtml(message);

    const content = `
      <div style="text-align: center; padding: var(--spacing-4);">
        <div style="width: 3rem; height: 3rem; margin: 0 auto var(--spacing-4); border-radius: var(--radius-full); background-color: ${colors[type]}20; display: flex; align-items: center; justify-content: center;" aria-hidden="true">
          <i class="${icons[type]}" style="font-size: 1.5rem; color: ${colors[type]};"></i>
        </div>
        <p style="margin: 0; color: var(--color-gray-700); overflow-wrap: break-word; word-wrap: break-word;">${escapedMessage}</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-outline" onclick="Modal.cancelConfirm('${id}')" autofocus>${cancelText}</button>
        <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" onclick="Modal.doConfirm('${id}')">${confirmText}</button>
      </div>
    `;

    this.create({
      id,
      title,
      content,
      width: '25rem',
      ariaLabel: `确认对话框: ${title}`
    });
    this.open(id);

    this.modals[id].onConfirm = onConfirm;
    this.modals[id].onCancel = onCancel;
  }

  doConfirm(id) {
    const modalData = this.modals[id];
    if (modalData && modalData.onConfirm) {
      modalData.onConfirm();
    }
    this.destroy(id);
  }

  cancelConfirm(id) {
    const modalData = this.modals[id];
    if (modalData && modalData.onCancel) {
      modalData.onCancel();
    }
    this.destroy(id);
  }

  form(options) {
    const { id, title, fields, onSubmit, width = '35rem' } = options;

    let formHTML = `<form id="modal-form-${id}" novalidate>`;
    fields.forEach(field => {
      const escapedLabel = this.escapeHtml(field.label);
      const escapedHint = field.hint ? this.escapeHtml(field.hint) : '';
      const escapedValue = field.value ? this.escapeHtml(field.value) : '';
      const escapedPlaceholder = field.placeholder ? this.escapeHtml(field.placeholder) : '';

      formHTML += `
        <div class="form-group">
          <label class="form-label" for="field-${field.name}">
            ${escapedLabel}
            ${field.required ? '<span class="required" aria-label="必填">*</span>' : ''}
          </label>
          ${this.createFieldInput(field, escapedValue, escapedPlaceholder)}
          ${escapedHint ? `<div class="form-hint">${escapedHint}</div>` : ''}
          <div class="form-error" id="error-${field.name}" role="alert" aria-live="polite"></div>
        </div>
      `;
    });
    formHTML += `
      <div class="modal-footer">
        <button type="button" class="btn btn-outline" onclick="Modal.close('${id}')">取消</button>
        <button type="submit" class="btn btn-primary">提交</button>
      </div>
    `;
    formHTML += '</form>';

    this.create({
      id,
      title,
      content: formHTML,
      width,
      ariaLabel: `表单对话框: ${title}`
    });
    this.open(id);

    const form = document.getElementById('modal-form-' + id);
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const formData = {};
      const errors = {};

      fields.forEach(field => {
        const input = form.querySelector(`[name="${field.name}"]`);
        formData[field.name] = input.value;

        if (field.required && !input.value.trim()) {
          errors[field.name] = `${field.label}为必填项`;
          input.setAttribute('aria-invalid', 'true');
          document.getElementById(`error-${field.name}`).textContent = errors[field.name];
        } else {
          input.setAttribute('aria-invalid', 'false');
          document.getElementById(`error-${field.name}`).textContent = '';
        }
      });

      if (Object.keys(errors).length > 0) {
        const firstErrorField = Object.keys(errors)[0];
        form.querySelector(`[name="${firstErrorField}"]`).focus();
        return;
      }

      if (onSubmit) {
        try {
          const submitBtn = form.querySelector('[type="submit"]');
          submitBtn.disabled = true;
          submitBtn.textContent = '提交中...';

          await onSubmit(formData);
          this.close(id);
        } catch (error) {
          Toast.error(error.message || '提交失败');
          submitBtn.disabled = false;
          submitBtn.textContent = '提交';
        }
      }
    });

    this.modals[id].onClose = () => this.destroy(id);
  }

  createFieldInput(field, value, placeholder) {
    const commonAttrs = `
      id="field-${field.name}"
      name="${field.name}"
      ${field.required ? 'required aria-required="true"' : ''}
      ${placeholder ? `placeholder="${placeholder}"` : ''}
    `;

    switch (field.type) {
      case 'select':
        let options = '';
        if (field.options && Array.isArray(field.options)) {
          field.options.forEach(opt => {
            const optValue = this.escapeHtml(opt.value);
            const optLabel = this.escapeHtml(opt.label);
            options += `<option value="${optValue}" ${opt.value === field.value ? 'selected' : ''}>${optLabel}</option>`;
          });
        }
        return `<select class="form-select" ${commonAttrs}>${options}</select>`;

      case 'textarea':
        return `<textarea class="form-textarea" ${commonAttrs} rows="${field.rows || 4}" aria-describedby="error-${field.name}">${value}</textarea>`;

      case 'number':
        return `<input type="number" class="form-input" ${commonAttrs} value="${value}" ${field.min !== undefined ? `min="${field.min}"` : ''} ${field.max !== undefined ? `max="${field.max}"` : ''} step="${field.step || 1}" aria-describedby="error-${field.name}">`;

      case 'email':
        return `<input type="email" class="form-input" ${commonAttrs} value="${value}" autocomplete="email" aria-describedby="error-${field.name}">`;

      case 'password':
        return `<input type="password" class="form-input" ${commonAttrs} value="${value}" autocomplete="new-password" aria-describedby="error-${field.name}">`;

      default:
        return `<input type="${field.type || 'text'}" class="form-input" ${commonAttrs} value="${value}" aria-describedby="error-${field.name}">`;
    }
  }
}

const Modal = new ModalClass();

if (typeof window !== 'undefined') {
  window.Modal = Modal;
}