# AI产业集群服务管理平台 - URL架构规划

## 🌐 **域名与访问地址**

### 生产环境
- **主域名**: https://jhw-ai.com
- **备用域名**: https://www.jhw-ai.com
- **IP访问**: http://120.76.156.83

### 统一访问路径

| 服务 | 用户端 | 管理端 |
|------|--------|--------|
| 首页(Portal) | `/` | - |
| 水站管理 | `/water/` | `/water-admin/` |
| 会议室预定 | `/meeting/` | `/meeting-admin/` |
| VIP餐厅 | `/dining/` | `/dining-admin/` |
| API服务 | `/api/` | - |

### 完整访问地址

#### HTTP访问（IP地址）
```
首页:        http://120.76.156.83/
水站用户端:  http://120.76.156.83/water/
水站管理端:  http://120.76.156.83/water-admin/admin.html
会议室用户:  http://120.76.156.83/meeting/
会议室管理:  http://120.76.156.83/meeting-admin/admin.html
API接口:     http://120.76.156.83/api/
```

#### HTTPS访问（域名）
```
首页:        https://jhw-ai.com/
水站用户端:  https://jhw-ai.com/water/
水站管理端:  https://jhw-ai.com/water-admin/admin.html
会议室用户:  https://jhw-ai.com/meeting/
会议室管理:  https://jhw-ai.com/meeting-admin/admin.html
API接口:     https://jhw-ai.com/api/
```

## 📁 **目录结构**

```
/var/www/jhw-ai.com/
├── portal/              # 首页Portal
│   ├── index.html
│   └── favicon.svg
├── water/               # 水站用户端
│   └── index.html
├── water-admin/         # 水站管理端
│   └── admin.html
├── meeting/             # 会议室用户端
│   └── index.html
├── meeting-admin/       # 会议室管理端
│   └── admin.html
├── backend/             # 后端API服务
│   ├── main.py
│   ├── waterms.db       # 水站数据库
│   ├── meeting.db       # 会议室数据库
│   └── .venv/
└── ssl/                 # SSL证书
    ├── jhw-ai.com.pem
    └── jhw-ai.com.key
```

## 🔗 **Portal首页链接规范**

Portal首页应使用绝对路径，而不是相对路径：

```html
<!-- ❌ 错误的写法（相对路径） -->
<a href="../Service_WaterManage/frontend/index.html">水站管理</a>

<!-- ✅ 正确的写法（绝对路径） -->
<a href="/water/">水站管理</a>
<a href="/water-admin/admin.html">管理后台</a>
```

## 🔐 **部署策略**

### 首次部署
- 部署所有代码和初始数据库
- 配置Nginx、SSL证书
- 配置系统服务

### 增量更新
- ✅ 上传最新代码
- ❌ 不覆盖数据库（保护真实数据）
- ✅ 重启服务

### 数据库保护
- 部署前自动备份
- 增量更新时跳过数据库覆盖
- 提供手动数据库更新选项