# 会议室管理模块开发实施计划

**文档版本**: v1.0  
**制定时间**: 2026-03-31  
**参考模式**: Service_WaterManage (领水登记)

---

## 📋 核心业务模式设计

### 1️⃣ 权限控制策略（参照水站）

| 用户类型 | 访问范围 | 认证要求 | 典型操作 |
|---------|---------|---------|---------|
| **普通用户** | 用户端界面 | ❌ 免登录 | 选择办公室 → 预订会议室 → 查看记录 |
| **办公室管理员** | 管理后台 | ✅ JWT 认证 | 审核预约、查看统计、管理账户 |
| **超级管理员** | 全部功能 | ✅ JWT + 角色检查 | 会议室 CRUD、价格配置、全局统计 |

### 2️⃣ 业务维度：以办公室为账户单位

```
办公室账户 (OfficeAccount)
├── 会议室使用额度 (meeting_hours_quota)
├── 免费时长 (free_hours_per_month: 8h)
├── 已用时长 (used_hours)
├── 收费时长 (charged_hours)
├── 应付金额 (total_amount)
└── 状态 (active/frozen)

会议室预约记录 (MeetingReservation)
├── 关联办公室 (office_id, office_name)
├── 使用时长 (duration_hours)
├── 收费时长 (charged_hours)
├── 金额 (total_amount)
├── 状态 (pending/confirmed/settled/cancelled)
└── 结算状态 (unsettled/settled)
```

### 3️⃣ 状态机设计（参照水站领水）

```
预约状态流转:
pending (待确认) → confirmed (已确认/待使用) → completed (已完成/待结算) → settled (已结算)
                                    ↓
                            cancelled (已取消)

结算状态:
unsettled (待结算) → applied (用户标记已付/待确认) → settled (已结清)
```

---

## 🎯 开发任务分解

### 阶段一：用户端功能完善 (P0 - 1周)

#### 1.1 前端改造 (`Service_MeetingRoom/frontend/index.html`)

| 任务 | 优先级 | 工作量 | 说明 |
|------|-------|--------|------|
| 移除强制登录检查 | P0 | 0.5h | 用户无需登录即可访问 |
| 办公室选择界面 | P0 | 2h | 参照水站：常用/不常用标签 + 卡片网格 |
| 用户身份绑定 | P0 | 1h | 选择办公室后保存到 localStorage |
| 预约记录按办公室筛选 | P0 | 1h | 显示当前办公室的所有预约 |
| 错误提示优化 | P1 | 1h | 友好错误消息 |

**关键代码修改**:
```javascript
// 移除强制登录检查
- created() {
-     this.checkLogin();  // ❌ 删除
-     this.loadData();
- }

// 添加办公室选择
data() {
    return {
        selectedOffice: null,  // ✅ 新增
        offices: [],
        // ...
    }
}

// 加载办公室列表 (参照水站)
async loadOffices() {
    const res = await fetch('http://localhost:8001/api/office/resources?type=office');
    this.offices = res.data?.items || [];
}
```

#### 1.2 后端 API 调整 (`api/meeting.py`)

| 任务 | 优先级 | 工作量 | 说明 |
|------|-------|--------|------|
| 移除用户端认证 | P0 | 1h | GET 接口免认证 |
| 添加办公室筛选 | P0 | 1h | POST/GET 支持 office_id 参数 |
| 添加预约人信息 | P0 | 1h | 记录 pickup_person |
| 保留管理端认证 | P0 | 0.5h | DELETE/PUT 仍需认证 |

**API 权限分类**:

| 端点 | 方法 | 当前认证 | 调整后认证 | 说明 |
|------|------|---------|-----------|------|
| `/rooms` | GET | ❌ | ❌ | 保持免认证 |
| `/rooms/{id}/availability` | GET | ❌ | ❌ | 保持免认证 |
| `/reservations` | POST | ✅ | ❌ | **改为免认证**，传 office_id |
| `/reservations` | GET | ✅ | ❌ | **改为免认证**，查 office_id 的记录 |
| `/reservations/{id}` | DELETE | ✅ | ✅ | 保持认证，取消需审核 |

---

### 阶段二：管理后台开发 (P0 - 2周)

#### 2.1 管理后台重构 (`Service_MeetingRoom/admin/admin.html`)

| 任务 | 优先级 | 工作量 | 说明 |
|------|-------|--------|------|
| JWT 登录页面 | P0 | 2h | 独立 login.html |
| Token 认证机制 | P0 | 2h | 参照水站 admin.html |
| 角色权限显示 | P0 | 1h | super_admin/admin/staff |
| 办公室账户列表 | P0 | 3h | 显示各办公室使用额度 |
| 预约审核功能 | P0 | 3h | 确认/拒绝待审核预约 |
| 结算管理 | P0 | 4h | 按办公室结算、批量确认 |

**登录认证示例** (参照水站):
```javascript
// admin/login.html
async login() {
    const res = await fetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username: this.username, password: this.password })
    });
    const data = await res.json();
    localStorage.setItem('token', data.data.access_token);
    localStorage.setItem('user', JSON.stringify(data.data.user));
    window.location.href = '/Service_MeetingRoom/admin/admin.html';
}

// admin/admin.html - 验证登录
created() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    this.loadDashboard();
}
```

#### 2.2 管理端 API 新增 (`api/meeting.py`)

| 端点 | 方法 | 工作量 | 说明 |
|------|------|--------|------|
| `/admin/reservations/{id}/approve` | POST | 2h | 审核通过预约 |
| `/admin/reservations/{id}/reject` | POST | 2h | 拒绝预约 |
| `/admin/offices` | GET | 1h | 办公室使用统计列表 |
| `/admin/offices/{id}/settlement` | GET | 2h | 办公室结算详情 |
| `/admin/offices/{id}/settlement` | POST | 2h | 确认结算 |
| `/admin/stats` | GET | 3h | 全局统计数据 |

**审核 API 示例**:
```python
@router.post("/admin/reservations/{reservation_id}/approve")
async def approve_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_user),  # ✅ 需要认证
    db: Session = Depends(get_db)
):
    # 权限检查
    if current_user.role not in ["super_admin", "admin"]:
        raise HTTPException(403, "权限不足")
    
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id
    ).first()
    
    reservation.status = "confirmed"
    reservation.confirmed_by = current_user.id
    reservation.confirmed_at = datetime.now()
    
    db.commit()
    return {"code": 200, "message": "审核通过"}
```

---

### 阶段三：数据模型完善 (P0 - 3天)

#### 3.1 OfficeAccount 扩展 (`models/office.py`)

```python
class OfficeAccount(Base):
    __tablename__ = "office_accounts"
    
    id = Column(Integer, primary_key=True)
    office_id = Column(Integer, ForeignKey("office_resources.id"))
    office_name = Column(String(100))
    
    # 会议室额度管理
    meeting_quota_total = Column(Float, default=0)    # 总额度
    meeting_quota_used = Column(Float, default=0)     # 已用
    meeting_quota_remaining = Column(Float, default=0)  # 剩余
    
    # 免费额度
    free_hours_per_month = Column(Float, default=8)  # 每月免费 8 小时
    free_hours_used = Column(Float, default=0)
    
    # 收费统计
    charged_hours_total = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    
    # 状态
    status = Column(String(20), default="active")  # active/frozen
    
    # 管理员
    manager_id = Column(Integer, ForeignKey("users.id"))
    manager_name = Column(String(100))
```

**数据库迁移脚本**:
```bash
# scripts/migrate_meeting_accounts.py
ALTER TABLE office_accounts ADD COLUMN meeting_quota_total REAL DEFAULT 0;
ALTER TABLE office_accounts ADD COLUMN meeting_quota_used REAL DEFAULT 0;
ALTER TABLE office_accounts ADD COLUMN meeting_quota_remaining REAL DEFAULT 0;
ALTER TABLE office_accounts ADD COLUMN free_hours_per_month REAL DEFAULT 8;
ALTER TABLE office_accounts ADD COLUMN free_hours_used REAL DEFAULT 0;
ALTER TABLE office_accounts ADD COLUMN charged_hours_total REAL DEFAULT 0;
```

#### 3.2 Reservation 模型扩展 (`models/reservation.py`)

```python
class Reservation(Base):
    # ... 现有字段 ...
    
    # 结算相关 (参照水站)
    settlement_status = Column(String(20), default="unsettled")
    applied_at = Column(DateTime)  # 用户标记已付时间
    applied_by = Column(Integer, ForeignKey("users.id"))  # 申请人
    confirmed_at = Column(DateTime)  # 管理员确认时间
    confirmed_by = Column(Integer, ForeignKey("users.id"))  # 确认人
    
    # 审核相关
    approved_at = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id"))
    rejected_at = Column(DateTime)
    rejected_by = Column(Integer, ForeignKey("users.id"))
    reject_reason = Column(Text)
```

---

### 阶段四：集成测试 (P1 - 1周)

#### 4.1 用户端测试脚本

```python
# scripts/test_meeting_user_flow.py
"""测试用户预定流程（免登录）"""

def test_user_flow():
    # 1. 访问会议室页面（无需登录）
    # 2. 选择办公室
    # 3. 选择会议室和时段
    # 4. 提交预约
    # 5. 查看预约记录
    
    print("✅ 用户免登录预定流程测试通过")
```

#### 4.2 管理端测试脚本

```python
# scripts/test_meeting_admin_flow.py
"""测试管理员审核流程（需登录）"""

def test_admin_flow():
    # 1. 管理员登录
    # 2. 查看待审核预约
    # 3. 审核通过/拒绝
    # 4. 查看办公室使用统计
    # 5. 确认结算
    
    print("✅ 管理员审核流程测试通过")
```

---

## 📅 实施时间表

| 阶段 | 任务 | 工作日 | 交付物 |
|------|------|-------|--------|
| **Week 1** | 用户端改造 | 5 天 | 免登录预定功能 |
| **Week 2** | 管理后台认证 | 3 天 | 登录页面+Token 验证 |
| **Week 2** | 管理端 API | 2 天 | 审核/结算 API |
| **Week 3** | 数据模型+迁移 | 2 天 | 办公室账户扩展 |
| **Week 3** | 管理后台功能 | 3 天 | 审核+结算界面 |
| **Week 4** | 集成测试 | 3 天 | 测试脚本+Bug 修复 |
| **Week 4** | 文档+部署 | 2 天 | 用户手册+上线 |

**总工期**: 4 周

---

## 🔧 关键代码改动清单

### 1. 用户端前端 (`Service_MeetingRoom/frontend/index.html`)

```diff
@@ -330,10 +330,6 @@
             },
             created() {
-                this.checkLogin();  // ❌ 删除强制登录检查
                 this.loadOffices();  // ✅ 先加载办公室
                 this.loadData();
             },
+            data() {
+                return {
+                    selectedOffice: null,  // ✅ 新增
+                    // ...
+                }
+            },
```

### 2. 管理后台前端 (`Service_MeetingRoom/admin/admin.html`)

```diff
+<!-- 添加认证检查 -->
+created() {
+    const token = localStorage.getItem('token');
+    if (!token) {
+        window.location.href = 'login.html';
+        return;
+    }
+    this.loadDashboard();
+},
```

### 3. 后端 API (`api/meeting.py`)

```diff
 @router.post("/reservations")
 async def create_reservation(
-    current_user: dict = Depends(get_current_user_id),  // ❌ 移除
     office_id: int,
     # ...
 ):
+    # ✅ 可选：记录预约人信息
+    user = get_current_user_optional()
     
 @router.get("/reservations")
 async def list_reservations(
-    current_user: dict = Depends(get_current_user_id),  // ❌ 移除
+    office_id: Optional[int] = None,
 ):
+    # ✅ 按办公室筛选
+    if office_id:
+        query = query.filter(Reservation.office_id == office_id)
```

---

## ✅ 验收标准

### 用户端验收

- [ ] 无需登录即可访问会议室页面
- [ ] 可以选择办公室
- [ ] 可以查看会议室列表
- [ ] 可以预订会议室（填写会议信息）
- [ ] 可以查看本办公室的预约记录
- [ ] 可以取消待使用的预约

### 管理端验收

- [ ] 管理员必须登录才能访问后台
- [ ] 可以查看待审核预约列表
- [ ] 可以审核通过/拒绝预约
- [ ] 可以查看各办公室使用统计
- [ ] 可以确认结算（pending→settled）
- [ ] 可以导出办公室使用报表

### API 验收

- [ ] 用户端 API 无需 Token
- [ ] 管理端 API 需要 JWT Token
- [ ] 权限不足返回 403
- [ ] 所有 API 返回统一格式

---

## 📋 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 用户误操作 | 中 | 添加确认弹窗、操作日志 |
| 恶意预约 | 中 | 限制单办公室同时预约数量 |
| 数据不一致 | 高 | 添加事务、对账机制 |
| 性能问题 | 低 | 添加缓存、分页 |

---

**批准**: _______________  **日期**: _______________
