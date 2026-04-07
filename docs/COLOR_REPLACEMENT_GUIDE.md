# 硬编码颜色替换指南

## 颜色映射表

根据 design-system.css 定义，以下是硬编码颜色与CSS变量的对应关系：

### 主色系（Primary）

| 硬编码 | CSS变量 | 用途 | 出现次数 |
|--------|---------|------|---------|
| `#2563EB` | `var(--primary)` | 主色 | 21处 |
| `#1D4ED8` | `var(--primary-hover)` | 主色悬停 | 10处 |
| `#DBEAFE` | `var(--primary-light)` | 主色浅色 | 12处 |
| `#1E40AF` | `var(--primary-dark)` | 主色深色 | 少量 |
| `#EFF6FF` | 浅蓝背景 | 特殊背景 | 14处 |

### 文字颜色（Text）

| 硬编码 | CSS变量 | 用途 | 出现次数 |
|--------|---------|------|---------|
| `#1E293B` | `var(--text-primary)` | 主要文字 | 15处 |
| `#64748B` | `var(--text-secondary)` | 次要文字 | 9处 |
| `#94A3B8` | `var(--text-tertiary)` | 三级文字 | 4处 |
| `#9ca3af` | `var(--text-tertiary)` | 三级文字(等价) | 4处 |

### 背景颜色（Background）

| 硬编码 | CSS变量 | 用途 | 出现次数 |
|--------|---------|------|---------|
| `#F1F5F9` | `var(--bg-primary)` | 主背景 | 6处 |
| `#F8FAFC` | `var(--bg-secondary)` | 次背景 | 9处 |
| `#FFFFFF` | `var(--bg-card)` | 卡片背景 | 2处 |
| `#E2E8F0` | `var(--border)` | 边框 | 7处 |

### 功能色（Functional）

| 硬编码 | CSS变量 | 用途 |
|--------|---------|------|
| `#10B981` | `var(--success)` | 成功色 |
| `#059669` | `var(--success-dark)` | 成功深色 |
| `#F59E0B` | `var(--warning)` | 警告色 |
| `#FEF3C7` | `var(--warning-light)` | 警告浅色 |
| `#EF4444` | `var(--danger)` | 危险色 |
| `#FCD34D` | 特定警告色 | 徽章等 |
| `#78350F` | 特定文字色 | 徽章文字 |

## 批量替换策略

### 阶段1: 主色系替换（高优先级）

**替换命令示例**：
```bash
# 主色
find . -name "*.html" -o -name "*.css" | xargs sed -i '' 's/#2563EB/var(--primary)/g'

# 主色悬停
find . -name "*.html" -o -name "*.css" | xargs sed -i '' 's/#1D4ED8/var(--primary-hover)/g'

# 主色浅色
find . -name "*.html" -o -name "*.css" | xargs sed -i '' 's/#DBEAFE/var(--primary-light)/g'
```

### 阶段2: 文字颜色替换（高优先级）

**替换命令示例**：
```bash
# 主要文字
find . -name "*.html" -o -name "*.css" | xargs sed -i '' 's/#1E293B/var(--text-primary)/g'

# 次要文字
find . -name "*.html" -o -name "*.css" | xargs sed -i '' 's/#64748B/var(--text-secondary)/g'

# 三级文字
find . -name "*.html" -o -name "*.css" | xargs sed -i '' 's/#94A3B8/var(--text-tertiary)/g'
```

### 阶段3: 背景颜色替换（中优先级）

**替换命令示例**：
```bash
# 主背景
find . -name "*.html" -o -name "*.css" | xargs sed -i '' 's/#F1F5F9/var(--bg-primary)/g'

# 次背景
find . -name "*.html" -o -name "*.css" | xargs sed -i '' 's/#F8FAFC/var(--bg-secondary)/g'

# 边框
find . -name "*.html" -o -name "*.css" | xargs sed -i '' 's/#E2E8F0/var(--border)/g'
```

## 注意事项

### 不应替换的情况

1. **渐变中的颜色**
   ```css
   /* 保持原样 */
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
   ```

2. **特殊场景颜色**
   - 图表颜色
   - 特定品牌色
   - 第三方库颜色

3. **透明度颜色**
   ```css
   rgba(37, 99, 235, 0.5) /* 保持rgba格式 */
   ```

### 验证步骤

1. **替换前备份**
   ```bash
   git add .
   git commit -m "备份：硬编码颜色替换前"
   ```

2. **逐个替换**
   - 一次只替换一个颜色
   - 立即验证视觉效果

3. **功能测试**
   - 检查页面渲染
   - 测试交互功能
   - 验证响应式

## 当前状态

- 硬编码颜色总数：约150处
- 已替换：0处
- 待替换：150处

## 目标

- 减少硬编码颜色至 ≤10处
- 提高主题一致性
- 便于后续主题定制

---

**最后更新**: 2026-04-08  
**状态**: 待执行