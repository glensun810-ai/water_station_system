/**
 * 表单验证器
 * 提供表单验证规则和验证方法
 */

const Validator = {
  rules: {
    required: (value, message = '此字段为必填项') => {
      if (value === null || value === undefined || value === '') {
        return message;
      }
      if (Array.isArray(value) && value.length === 0) {
        return message;
      }
      return null;
    },

    email: (value, message = '请输入有效的邮箱地址') => {
      if (!value) return null;
      const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return regex.test(value) ? null : message;
    },

    phone: (value, message = '请输入有效的手机号码') => {
      if (!value) return null;
      const regex = /^1[3-9]\d{9}$/;
      return regex.test(value) ? null : message;
    },

    minLength: (min) => (value, message = `最少需要${min}个字符`) => {
      if (!value) return null;
      return value.length >= min ? null : message;
    },

    maxLength: (max) => (value, message = `最多允许${max}个字符`) => {
      if (!value) return null;
      return value.length <= max ? null : message;
    },

    min: (minValue) => (value, message = `最小值为${minValue}`) => {
      if (!value) return null;
      return Number(value) >= minValue ? null : message;
    },

    max: (maxValue) => (value, message = `最大值为${maxValue}`) => {
      if (!value) return null;
      return Number(value) <= maxValue ? null : message;
    },

    pattern: (regex, message = '格式不正确') => (value) => {
      if (!value) return null;
      return regex.test(value) ? null : message;
    },

    numeric: (value, message = '请输入数字') => {
      if (!value) return null;
      return !isNaN(parseFloat(value)) && isFinite(value) ? null : message;
    },

    integer: (value, message = '请输入整数') => {
      if (!value) return null;
      return Number.isInteger(Number(value)) ? null : message;
    },

    positiveNumber: (value, message = '请输入正数') => {
      if (!value) return null;
      return Number(value) > 0 ? null : message;
    },

    url: (value, message = '请输入有效的URL') => {
      if (!value) return null;
      try {
        new URL(value);
        return null;
      } catch {
        return message;
      }
    },

    date: (value, message = '请输入有效的日期') => {
      if (!value) return null;
      const date = new Date(value);
      return !isNaN(date.getTime()) ? null : message;
    },

    sameAs: (otherValue, fieldName, message) => (value) => {
      if (!value) return null;
      return value === otherValue ? null : message || `与${fieldName}不匹配`;
    },

    custom: (validatorFn) => validatorFn
  },

  validateField(value, rules) {
    for (const rule of rules) {
      if (typeof rule === 'function') {
        const error = rule(value);
        if (error) return error;
      }
    }
    return null;
  },

  validateForm(formData, schema) {
    const errors = {};
    let isValid = true;

    for (const [field, rules] of Object.entries(schema)) {
      const value = formData[field];
      const error = this.validateField(value, rules);

      if (error) {
        errors[field] = error;
        isValid = false;
      }
    }

    return { isValid, errors };
  },

  validateAsync(formData, schema) {
    return Promise.resolve(this.validateForm(formData, schema));
  },

  createValidator(schema) {
    return {
      schema,
      errors: {},
      validate(formData) {
        const result = Validator.validateForm(formData, this.schema);
        this.errors = result.errors;
        return result.isValid;
      },
      hasError(field) {
        return !!this.errors[field];
      },
      getError(field) {
        return this.errors[field] || '';
      },
      clearErrors() {
        this.errors = {};
      },
      clearFieldError(field) {
        delete this.errors[field];
      }
    };
  }
};

if (typeof window !== 'undefined') {
  window.Validator = Validator;
}