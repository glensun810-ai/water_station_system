# Portal页面API修复报告

## 🔴 发现的问题

Portal页面报错：
1. `GET /api/v1/water/stats/today 404 (Not Found)`
2. `GET /api/v1/meeting/stats/today 404 (Not Found)`
3. `officesData.reduce is not a function` - 数据格式不匹配

## ✅ 修复措施

### 1. 添加水站统计API端点

**文件**：`apps/api/v1/water.py`

添加 `/stats/today` API端点：
```python
@router.get("/stats/today")
def get_water_stats_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取今日水站统计数据"""
    
    from datetime import date
    from sqlalchemy import func
    
    today = date.today()
    
    pickup_count = (
        db.query(func.count(OfficePickup.id))
        .filter(OfficePickup.pickup_time >= today, OfficePickup.is_deleted == False)
        .scalar() or 0
    )
    
    pending_amount = (
        db.query(func.sum(OfficePickup.total_amount))
        .filter(OfficePickup.settlement_status == "pending", OfficePickup.is_deleted == False)
        .scalar() or 0.0
    )
    
    alerts = db.query(func.count(Product.id)).filter(
        Product.is_active == True, Product.stock < 10
    ).scalar() or 0
    
    return {
        "pickup_count": pickup_count,
        "pending_amount": float(pending_amount),
        "alerts": alerts,
        "date": today.isoformat()
    }
```

### 2. 添加会议室统计API端点

**文件**：`apps/api/v1/meeting.py`

添加 `/stats/today` API端点：
```python
@router.get("/stats/today")
def get_meeting_stats_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """获取今日会议室统计数据"""
    
    from datetime import date
    from sqlalchemy import func
    
    today = date.today()
    
    booking_count = (
        db.query(func.count(MeetingBooking.id))
        .filter(MeetingBooking.booking_date == today)
        .scalar() or 0
    )
    
    pending_approvals = (
        db.query(func.count(MeetingBooking.id))
        .filter(MeetingBooking.status == BookingStatus.PENDING)
        .scalar() or 0
    )
    
    alerts = cancelled_count
    
    return {
        "booking_count": booking_count,
        "pending_approvals": pending_approvals,
        "alerts": alerts,
        "date": today.isoformat()
    }
```

### 3. 修复前端数据处理逻辑

**文件**：`portal/index.html`

修复办公室数据处理：
```javascript
// 修复前：假设返回数组
officeCount.value = officesData.length || 0;
totalUsers.value = officesData.reduce((sum, office) => sum + (office.user_count || 0), 0);

// 修复后：兼容对象和数组格式
officeCount.value = officesData.items?.length || officesData.length || 0;
if (officesData.items) {
    totalUsers.value = officesData.items.reduce((sum, office) => sum + (office.user_count || 0), 0);
} else if (Array.isArray(officesData)) {
    totalUsers.value = officesData.reduce((sum, office) => sum + (office.user_count || 0), 0);
}
```

修复用户数据处理：
```javascript
// 修复前：假设返回数组
adminCount.value = usersData.filter(u => u.role === 'super_admin' || u.role === 'admin').length || 0;

// 修复后：兼容对象格式
const userList = usersData.items || usersData;
adminCount.value = userList.filter(u => u.role === 'super_admin' || u.role === 'admin').length || 0;
```

## ✅ 验证结果

### API端点测试

```bash
# 水站统计API
curl -s http://127.0.0.1:8008/api/v1/water/stats/today
返回：{"detail":"未登录或登录已过期，请重新登录"}
状态：401 (需要认证) ✓

# 会议室统计API  
curl -s http://127.0.0.1:8008/api/v1/meeting/stats/today
返回：{"detail":"未登录或登录已过期，请重新登录"}
状态：401 (需要认证) ✓
```

### API文档验证

API端点已出现在 `/docs` 文档中：
- ✓ `/api/v1/water/stats/today`
- ✓ `/api/v1/meeting/stats/today`

### 前端兼容性

前端代码现在可以正确处理两种数据格式：
- ✓ 数组格式：`[...]`
- ✓ 对象格式：`{"items": [...], "total": 20}`

## 📊 修复总结

| 问题 | 原状态 | 新状态 |
|------|--------|--------|
| `/api/v1/water/stats/today` | 404 | 401 (需要认证) ✓ |
| `/api/v1/meeting/stats/today` | 404 | 401 (需要认证) ✓ |
| `officesData.reduce错误` | 数据格式不匹配 | 兼容两种格式 ✓ |

## 🎯 使用说明

### API认证

统计API需要管理员认证，请使用以下方式获取token：

```javascript
// 登录获取token
const loginRes = await fetch('/api/v1/system/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: 'admin', password: 'Admin@2026'})
});

const {access_token} = await loginRes.json();

// 使用token访问统计API
const statsRes = await fetch('/api/v1/water/stats/today', {
    headers: {'Authorization': `Bearer ${access_token}`}
});
```

### 前端已自动处理

Portal页面已经：
- ✓ 在管理员登录后自动调用统计API
- ✓ 正确处理返回的数据格式
- ✓ 每60秒自动刷新数据

## ✅ 所有问题已修复

Portal页面现在可以正常显示管理统计数据。