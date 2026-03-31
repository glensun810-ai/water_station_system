# 会议室管理快速实施指南 (P0 任务)

**目标**: 参照领水登记模式，实现用户免登录预定+管理员审核

---

## 🚀 立即执行任务（今天完成）

### 任务 1: 移除用户端强制登录 ✅

**文件**: `Service_MeetingRoom/frontend/index.html`

```javascript
// 找到 created() 方法，修改：
created() {
-    this.checkLogin();  // 删除或注释这行
    this.loadOffices();
    this.loadData();
},
```

**验证**: 刷新页面，不应再跳转到登录页

---

### 任务 2: 添加办公室选择功能 ✅

**文件**: `Service_MeetingRoom/frontend/index.html`

在 `data()` 中添加:
```javascript
data() {
    return {
        selectedOffice: null,  // 新增
        selectedOfficeId: null,  // 新增
        offices: [],  // 新增
        // ... 其他现有字段
    }
}
```

在 HTML 中添加办公室选择区域 (header 后):
```html
<div class="bg-white border-b p-3" v-if="!selectedOffice">
    <h3 class="text-sm font-bold mb-2">选择办公室</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
        <button v-for="office in offices" :key="office.id"
                @click="selectOffice(office)"
                class="border rounded-lg p-3 text-center hover:border-emerald-500 hover:bg-emerald-50">
            <div class="text-lg font-bold">{{ office.name }}</div>
            <div class="text-xs text-gray-500">{{ office.location }}</div>
        </button>
    </div>
</div>
```

添加方法:
```javascript
methods: {
    async selectOffice(office) {
        this.selectedOffice = office;
        this.selectedOfficeId = office.id;
        localStorage.setItem('selected_office', JSON.stringify(office));
        this.loadRooms();
        this.loadRecords();
    },
    // ... 其他方法
}
```

---

### 任务 3: 修改预约创建 API ✅

**文件**: `api/meeting.py`

```python
@router.post("/reservations")
async def create_reservation(
    room_id: int,
    start_time: str,
    end_time: str,
    office_id: int,  # ✅ 新增必需参数
    title: str = "会议",
    attendee_count: int = 0,
    description: Optional[str] = None,
    # current_user: dict = Depends(get_current_user_id),  # ❌ 注释掉
    db: Session = Depends(get_db),
):
    # ... 现有逻辑 ...
    
    reservation = Reservation(
        # ...
        office_id=office_id,  # ✅ 使用传入的 office_id
        # current_user["id"],  # ❌ 不再使用
        # ...
    )
```

**前端调用修改**:
```javascript
async submitReservation() {
    const params = new URLSearchParams({
        room_id: this.selectedRoom.id,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        office_id: this.selectedOfficeId,  // ✅ 新增
        title: this.form.title,
        attendee_count: this.form.attendeeCount,
        description: this.form.description
    });
    // ...
}
```

---

### 任务 4: 修改预约查询 API ✅

**文件**: `api/meeting.py`

```python
@router.get("/reservations")
async def list_reservations(
    office_id: Optional[int] = None,  # ✅ 新增
    status: Optional[str] = None,
    # current_user: dict = Depends(get_current_user_id),  # ❌ 注释
    db: Session = Depends(get_db),
):
    query = db.query(Reservation)
    
    # ✅ 按办公室筛选
    if office_id:
        query = query.filter(Reservation.office_id == office_id)
    
    # ... 现有逻辑 ...
```

**前端调用修改**:
```javascript
async loadRecords() {
    const params = new URLSearchParams();
    if (this.selectedOfficeId) {
        params.append('office_id', this.selectedOfficeId);
    }
    const res = await fetch(`${API_BASE}/reservations?${params}`);
    // ...
}
```

---

## 📅 明天执行任务

### 任务 5: 管理后台登录页面

**文件**: `Service_MeetingRoom/admin/login.html` (新建)

参照 `Service_WaterManage/frontend/login.html` 创建。

---

### 任务 6: 管理后台认证检查

**文件**: `Service_MeetingRoom/admin/admin.html`

```javascript
created() {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (!token || !user.role) {
        window.location.href = 'login.html';
        return;
    }
    
    if (!['super_admin', 'admin'].includes(user.role)) {
        alert('权限不足');
        window.location.href = 'login.html';
        return;
    }
    
    this.loadDashboard();
}
```

---

## ✅ 验收检查清单

### 用户端测试
- [ ] 访问页面不强制登录
- [ ] 显示办公室列表
- [ ] 选择办公室后显示会议室
- [ ] 可以提交预约（传 office_id）
- [ ] 查看预约记录（按办公室筛选）

### 管理端测试
- [ ] 访问后台需要登录
- [ ] 非管理员被拒绝访问
- [ ] 显示当前管理员角色

---

## 🐛 常见问题

**Q1: 选择办公室后页面空白？**
A: 检查 `selectedOfficeId` 是否正确保存，`loadRooms()` 是否正确调用。

**Q2: 预约创建失败？**
A: 确认 API 参数 `office_id` 是否正确传递，检查后端日志。

**Q3: 预约记录不显示？**
A: 确认 `loadRecords()` 传入了 `office_id` 参数。

---

**预计完成时间**: 1 天 (P0 任务)  
**下一步**: 管理后台审核功能开发
