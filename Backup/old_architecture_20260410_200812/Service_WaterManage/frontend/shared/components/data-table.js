/**
 * DataTable数据表格组件 v2.0
 * 提供分页、排序、筛选、批量选择功能
 * 特性：ARIA可访问性、键盘导航、响应式设计、边界处理
 */

const DataTable = {
  create(options) {
    const {
      id,
      columns,
      data = [],
      loading = false,
      selectable = false,
      pagination = { page: 1, limit: 20, total: 0 },
      emptyText = '暂无数据',
      onPageChange,
      onSelectionChange,
      onSortChange
    } = options;

    return {
      template: this.generateTemplate(id, columns, selectable, emptyText),
      data() {
        return {
          columns,
          data,
          loading,
          selectable,
          selectedIds: [],
          allSelected: false,
          pagination,
          sortKey: null,
          sortOrder: null
        };
      },
      methods: {
        toggleSelectAll(event) {
          if (event.target.checked) {
            this.selectedIds = this.data.map(item => item.id).filter(id => id != null);
          } else {
            this.selectedIds = [];
          }
          this.allSelected = this.selectedIds.length === this.data.length && this.data.length > 0;
          if (onSelectionChange) {
            onSelectionChange(this.selectedIds);
          }
        },
        toggleSelect(id, event) {
          if (id == null) return;
          const index = this.selectedIds.indexOf(id);
          if (index > -1) {
            this.selectedIds.splice(index, 1);
          } else {
            this.selectedIds.push(id);
          }
          this.allSelected = this.selectedIds.length === this.data.length && this.data.length > 0;
          if (onSelectionChange) {
            onSelectionChange(this.selectedIds);
          }
        },
        isSelected(id) {
          return id != null && this.selectedIds.includes(id);
        },
        sort(key) {
          if (!key) return;
          if (this.sortKey === key) {
            this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
          } else {
            this.sortKey = key;
            this.sortOrder = 'asc';
          }
          if (onSortChange) {
            onSortChange(key, this.sortOrder);
          }
        },
        changePage(page) {
          const totalPages = Math.ceil(this.pagination.total / this.pagination.limit);
          if (page < 1 || page > totalPages) return;
          if (onPageChange) {
            onPageChange(page, this.pagination.limit);
          }
        },
        changeLimit(event) {
          const limit = parseInt(event.target.value, 10);
          if (isNaN(limit) || limit < 1) return;
          if (onPageChange) {
            onPageChange(1, limit);
          }
        },
        totalPages() {
          if (this.pagination.limit <= 0) return 1;
          return Math.ceil(this.pagination.total / this.pagination.limit);
        },
        renderCell(row, column) {
          if (!row || !column) return '-';

          const value = row[column.key];

          if (value === null || value === undefined) {
            return '-';
          }

          if (column.render && typeof column.render === 'function') {
            try {
              return column.render(value, row);
            } catch (error) {
              console.error('Render error:', error);
              return '-';
            }
          }

          if (typeof value === 'number') {
            return value.toLocaleString();
          }

          if (typeof value === 'string' && value.length > 50) {
            return this.escapeHtml(value.substring(0, 50)) + '...';
          }

          return this.escapeHtml(String(value));
        },
        formatStatus(value) {
          if (!value) return '<span class="status-badge neutral">-</span>';
          const statusClass = {
            pending: 'pending',
            applied: 'applied',
            confirmed: 'confirmed',
            settled: 'settled',
            rejected: 'rejected',
            active: 'active',
            inactive: 'inactive'
          };
          const statusText = {
            pending: '待确认',
            applied: '待确认',
            confirmed: '已确认',
            settled: '已结算',
            rejected: '已拒绝',
            active: '活跃',
            inactive: '已停用'
          };
          const cls = statusClass[value] || 'neutral';
          const text = statusText[value] || value;
          return `<span class="status-badge ${cls}">${this.escapeHtml(text)}</span>`;
        },
        formatMoney(value) {
          if (value === null || value === undefined) return '¥0.00';
          const num = Number(value);
          if (isNaN(num)) return '¥0.00';
          return '¥' + num.toFixed(2);
        },
        formatDate(value) {
          if (!value) return '-';
          try {
            const date = new Date(value);
            if (isNaN(date.getTime())) return '-';
            return Utils.formatDateTime(date);
          } catch {
            return '-';
          }
        },
        escapeHtml(text) {
          if (!text) return '';
          const div = document.createElement('div');
          div.textContent = String(text);
          return div.innerHTML;
        },
        handleRowKeydown(event, row, index) {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            if (this.selectable && row.id != null) {
              this.toggleSelect(row.id);
            }
          }
        }
      },
      mounted() {
        if (onSelectionChange && typeof onSelectionChange === 'function') {
          this.$watch('selectedIds', (val) => {
            onSelectionChange(val);
          });
        }
      }
    };
  },

  generateTemplate(id, columns, selectable, emptyText) {
    let headerCells = '';

    if (selectable) {
      headerCells += `
        <th style="width: 2.5rem;" scope="col">
          <input type="checkbox"
            v-model="allSelected"
            @change="toggleSelectAll"
            aria-label="全选">
        </th>
      `;
    }

    columns.forEach((col, index) => {
      const sortable = col.sortable ? `@click="sort('${col.key}')"` : '';
      const sortIcon = col.sortable ? '<i class="fas fa-sort" style="margin-left: 0.25rem; opacity: 0.3;" aria-hidden="true"></i>' : '';
      const width = col.width ? `style="width: ${col.width}"` : '';
      const scope = 'scope="col"';

      headerCells += `
        <th ${width} ${sortable} ${scope}
          ${col.sortable ? 'role="columnheader" aria-sort="none"' : ''}>
          ${col.label}
          ${sortIcon}
        </th>
      `;
    });

    let bodyRows = `
      <tbody v-if="!loading && data.length > 0">
        <tr v-for="(row, index) in data" :key="row.id || index"
          @keydown="handleRowKeydown($event, row, index)"
          :tabindex="selectable ? '0' : '-1'"
          :role="selectable ? 'checkbox' : 'row'"
          :aria-selected="selectable ? isSelected(row.id) : undefined">
    `;

    if (selectable) {
      bodyRows += `
        <td>
          <input type="checkbox"
            :checked="isSelected(row.id)"
            @change="toggleSelect(row.id, $event)"
            :aria-label="'选择 ' + (row.name || row.id || '行')">
        </td>
      `;
    }

    columns.forEach(col => {
      bodyRows += `
        <td :role="'cell'">${col.slot ? `<slot name="${col.slot}" :row="row"></slot>` : `{{ renderCell(row, ${JSON.stringify(col)}) }}`}</td>
      `;
    });

    bodyRows += `
        </tr>
      </tbody>
    `;

    const template = `
      <div class="table-container" id="${id}" role="region" aria-label="数据表格">
        <div v-if="loading" class="loading-spinner" role="status" aria-label="加载中">
          <span class="sr-only">正在加载数据...</span>
        </div>

        <table class="table" v-if="!loading" role="grid">
          <thead>
            <tr>
              ${headerCells}
            </tr>
          </thead>
          ${bodyRows}
          <tbody v-if="!loading && data.length === 0">
            <tr>
              <td :colspan="${columns.length + (selectable ? 1 : 0)}">
                <div class="empty-state" role="status">
                  <div class="empty-state-icon" aria-hidden="true">
                    <i class="fas fa-inbox"></i>
                  </div>
                  <div class="empty-state-title">${emptyText}</div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="pagination" v-if="!loading && pagination.total > 0" role="navigation" aria-label="分页导航">
          <button class="pagination-btn"
            @click="changePage(pagination.page - 1)"
            :disabled="pagination.page === 1"
            aria-label="上一页"
            :aria-disabled="pagination.page === 1">
            <i class="fas fa-chevron-left" aria-hidden="true"></i>
          </button>

          <template v-for="p in totalPages()" :key="p">
            <button class="pagination-btn"
              @click="changePage(p)"
              :class="{ active: pagination.page === p }"
              :aria-label="'第' + p + '页'"
              :aria-current="pagination.page === p ? 'page' : undefined">
              {{ p }}
            </button>
          </template>

          <button class="pagination-btn"
            @click="changePage(pagination.page + 1)"
            :disabled="pagination.page >= totalPages()"
            aria-label="下一页"
            :aria-disabled="pagination.page >= totalPages()">
            <i class="fas fa-chevron-right" aria-hidden="true"></i>
          </button>

          <span class="pagination-info" aria-live="polite">
            共 {{ pagination.total }} 条
          </span>

          <select class="form-select"
            style="width: auto; padding: 0.375rem 0.75rem;"
            @change="changeLimit($event)"
            aria-label="每页显示条数">
            <option value="10">10条/页</option>
            <option value="20" selected>20条/页</option>
            <option value="50">50条/页</option>
            <option value="100">100条/页</option>
          </select>
        </div>
      </div>
    `;

    return template;
  },

  registerVueComponent(name, options) {
    if (typeof Vue !== 'undefined') {
      Vue.component(name, this.create(options));
    }
  }
};

if (typeof window !== 'undefined') {
  window.DataTable = DataTable;
}