/**
 * 辅助组件集合 v2.0
 * 分页、状态标签、搜索栏、批量操作栏、统计卡片
 * 特性：ARIA可访问性、响应式设计、边界处理
 */

const StatusBadge = {
  render(status, customText = null) {
    if (!status) {
      return '<span class="status-badge neutral">-</span>';
    }

    const statusClass = {
      pending: 'pending',
      applied: 'applied',
      confirmed: 'confirmed',
      settled: 'settled',
      rejected: 'rejected',
      active: 'active',
      inactive: 'inactive',
      unpaid: 'pending',
      paid: 'confirmed'
    };

    const statusText = {
      pending: '待确认',
      applied: '待确认',
      confirmed: '已确认',
      settled: '已结算',
      rejected: '已拒绝',
      active: '活跃',
      inactive: '已停用',
      unpaid: '未付款',
      paid: '已付款'
    };

    const cls = statusClass[status] || 'neutral';
    const text = customText || statusText[status] || status;

    const escapedText = this.escapeHtml(text);

    return `<span class="status-badge ${cls}" role="status" aria-label="${escapedText}">${escapedText}</span>`;
  },

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
  }
};

const Pagination = {
  render(pagination, onChange) {
    if (!pagination || pagination.total <= 0) {
      return '';
    }

    const limit = pagination.limit || 20;
    const page = pagination.page || 1;
    const total = pagination.total || 0;

    const totalPages = Math.ceil(total / limit);
    if (totalPages <= 0) return '';

    let buttons = '';

    const maxButtons = 5;
    let startPage = Math.max(1, page - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);

    if (endPage - startPage < maxButtons - 1) {
      startPage = Math.max(1, endPage - maxButtons + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      const activeClass = i === page ? 'active' : '';
      const ariaCurrent = i === page ? 'aria-current="page"' : '';
      buttons += `<button class="pagination-btn ${activeClass}"
        onclick="(${onChange})(${i})"
        aria-label="第${i}页"
        ${ariaCurrent}>${i}</button>`;
    }

    return `
      <div class="pagination" role="navigation" aria-label="分页导航">
        <button class="pagination-btn"
          onclick="(${onChange})(${page - 1})"
          ${page === 1 ? 'disabled aria-disabled="true"' : ''}
          aria-label="上一页">
          <i class="fas fa-chevron-left" aria-hidden="true"></i>
        </button>
        ${buttons}
        <button class="pagination-btn"
          onclick="(${onChange})(${page + 1})"
          ${page >= totalPages ? 'disabled aria-disabled="true"' : ''}
          aria-label="下一页">
          <i class="fas fa-chevron-right" aria-hidden="true"></i>
        </button>
        <span class="pagination-info" aria-live="polite">共 ${total} 条</span>
      </div>
    `;
  }
};

const SearchBar = {
  render(placeholder = '搜索...', onSearch) {
    const escapedPlaceholder = this.escapeHtml(placeholder);

    return `
      <div class="search-bar" role="search">
        <i class="fas fa-search search-icon" aria-hidden="true"></i>
        <input type="search"
          class="form-input"
          placeholder="${escapedPlaceholder}"
          aria-label="${escapedPlaceholder}"
          onkeyup="if(event.key==='Enter') (${onSearch})(this.value)">
      </div>
    `;
  },

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
  }
};

const ActionBar = {
  render(selectedCount, actions) {
    if (selectedCount === 0) return '';

    let actionButtons = '';
    if (actions && Array.isArray(actions)) {
      actions.forEach((action, index) => {
        const type = action.type || 'outline';
        const icon = action.icon || 'check';
        const label = action.label || '操作';
        const onClick = action.onClick || '';

        const escapedLabel = this.escapeHtml(label);

        actionButtons += `
          <button class="btn btn-sm btn-${type}"
            onclick="${onClick}"
            aria-label="${escapedLabel}">
            <i class="fas fa-${icon}" aria-hidden="true"></i>
            ${escapedLabel}
          </button>
        `;
      });
    }

    return `
      <div class="action-bar" role="toolbar" aria-label="批量操作工具栏">
        <span class="action-bar-count" aria-live="polite">已选择 ${selectedCount} 项</span>
        <div class="action-bar-actions" role="group">
          ${actionButtons}
        </div>
      </div>
    `;
  },

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
  }
};

const StatCard = {
  render(options) {
    if (!options) return '';

    const {
      icon = 'chart-bar',
      iconType = 'primary',
      value = 0,
      label = '',
      trend = null
    } = options;

    const escapedValue = this.escapeHtml(String(value));
    const escapedLabel = this.escapeHtml(label);

    const trendHTML = trend !== null
      ? `<div style="font-size: 0.75rem; margin-top: 0.5rem; color: ${trend > 0 ? 'var(--color-success-500)' : 'var(--color-error-500)'}">
          <i class="fas fa-${trend > 0 ? 'arrow-up' : 'arrow-down'}" aria-hidden="true"></i>
          ${Math.abs(trend)}%
        </div>`
      : '';

    return `
      <div class="stat-card" role="article" aria-label="${escapedLabel}">
        <div class="stat-card-icon ${iconType}" aria-hidden="true">
          <i class="fas fa-${icon}"></i>
        </div>
        <div class="stat-card-value" aria-label="数值: ${escapedValue}">${escapedValue}</div>
        <div class="stat-card-label">${escapedLabel}</div>
        ${trendHTML}
      </div>
    `;
  },

  renderGrid(cards) {
    if (!cards || !Array.isArray(cards) || cards.length === 0) {
      return '';
    }

    let cardHTMLs = '';
    cards.forEach(card => {
      cardHTMLs += `<div class="col-span-1">${this.render(card)}</div>`;
    });

    return `
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        role="region"
        aria-label="统计卡片">
        ${cardHTMLs}
      </div>
    `;
  },

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
  }
};

if (typeof window !== 'undefined') {
  window.StatusBadge = StatusBadge;
  window.Pagination = Pagination;
  window.SearchBar = SearchBar;
  window.ActionBar = ActionBar;
  window.StatCard = StatCard;
}