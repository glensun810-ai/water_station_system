# 统一错误处理使用指南

## 一、概述

本系统实现了统一的错误处理机制，确保所有API返回一致、清晰的错误响应格式。

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "timestamp": "2026-04-02T10:00:00",
    "path": "/api/users/123",
    "method": "GET",
    "details": {
      // 可选的详细信息
    }
  }
}
```

---

## 二、异常类使用

### 2.1 基本用法

```python
from exceptions import UserNotFoundError, InvalidCredentialsError

# 在API中使用
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        # 抛出业务异常
        raise UserNotFoundError(user_id=user_id)
    
    return user
```

### 2.2 带详细信息的异常

```python
from exceptions import InsufficientBalanceError

@app.post("/transactions")
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    user = get_user(db, transaction.user_id)
    
    if user.balance_credit < transaction.amount:
        # 抛出带详细信息的异常
        raise InsufficientBalanceError(
            required=transaction.amount,
            available=user.balance_credit
        )
    
    # 处理交易
    ...
```

---

## 三、异常类列表

### 用户相关

| 异常类 | 错误码 | 说明 |
|--------|--------|------|
| UserNotFoundError | USER_NOT_FOUND | 用户不存在 |
| UserAlreadyExistsError | USER_ALREADY_EXISTS | 用户已存在 |
| InvalidCredentialsError | INVALID_CREDENTIALS | 凭证无效 |
| UserInactiveError | USER_INACTIVE | 用户已禁用 |

### 产品相关

| 异常类 | 错误码 | 说明 |
|--------|--------|------|
| ProductNotFoundError | PRODUCT_NOT_FOUND | 产品不存在 |
| InsufficientStockError | INSUFFICIENT_STOCK | 库存不足 |
| ProductInactiveError | PRODUCT_INACTIVE | 产品已下架 |

### 交易相关

| 异常类 | 错误码 | 说明 |
|--------|--------|------|
| TransactionNotFoundError | TRANSACTION_NOT_FOUND | 交易不存在 |
| InsufficientBalanceError | INSUFFICIENT_BALANCE | 余额不足 |

### 会议室相关

| 异常类 | 错误码 | 说明 |
|--------|--------|------|
| MeetingRoomNotFoundError | MEETING_ROOM_NOT_FOUND | 会议室不存在 |
| TimeSlotConflictError | TIME_SLOT_CONFLICT | 时间段冲突 |
| InvalidTimeSlotError | INVALID_TIME_SLOT | 时间段无效 |

### 权限相关

| 异常类 | 错误码 | 说明 |
|--------|--------|------|
| PermissionDeniedError | PERMISSION_DENIED | 权限不足 |
| AuthenticationError | AUTHENTICATION_ERROR | 认证失败 |
| TokenExpiredError | TOKEN_EXPIRED | Token已过期 |

---

## 四、示例场景

### 4.1 用户登录

```python
from exceptions import InvalidCredentialsError, UserInactiveError

@app.post("/auth/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == credentials.username).first()
    
    # 用户不存在
    if not user:
        raise InvalidCredentialsError()
    
    # 用户已禁用
    if not user.is_active:
        raise UserInactiveError()
    
    # 密码错误
    if not verify_password(credentials.password, user.password_hash):
        raise InvalidCredentialsError()
    
    # 登录成功
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}
```

### 4.2 创建交易

```python
from exceptions import UserNotFoundError, ProductNotFoundError, InsufficientBalanceError

@app.post("/transactions")
def create_transaction(
    transaction: TransactionCreate, 
    db: Session = Depends(get_db)
):
    # 验证用户
    user = db.query(User).filter(User.id == transaction.user_id).first()
    if not user:
        raise UserNotFoundError(user_id=transaction.user_id)
    
    # 验证产品
    product = db.query(Product).filter(Product.id == transaction.product_id).first()
    if not product:
        raise ProductNotFoundError(product_id=transaction.product_id)
    
    # 检查余额
    total_amount = product.price * transaction.quantity
    if user.balance_credit < total_amount:
        raise InsufficientBalanceError(
            required=total_amount,
            available=user.balance_credit
        )
    
    # 创建交易
    ...
```

### 4.3 会议室预约

```python
from exceptions import (
    MeetingRoomNotFoundError, 
    TimeSlotConflictError, 
    InvalidTimeSlotError
)

@app.post("/meeting/bookings")
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):
    # 验证会议室
    room = db.query(MeetingRoom).filter(MeetingRoom.id == booking.room_id).first()
    if not room:
        raise MeetingRoomNotFoundError(room_id=booking.room_id)
    
    # 验证时间段
    if booking.start_time >= booking.end_time:
        raise InvalidTimeSlotError("开始时间必须早于结束时间")
    
    # 检查冲突
    conflicts = check_time_conflicts(db, booking)
    if conflicts:
        raise TimeSlotConflictError(
            start_time=booking.start_time,
            end_time=booking.end_time,
            conflicts=conflicts
        )
    
    # 创建预约
    ...
```

---

## 五、自定义异常

### 5.1 创建新的异常类

```python
# 在 exceptions.py 中添加

class CouponExpiredError(AppException):
    """优惠券已过期"""
    
    def __init__(self, coupon_code: str):
        super().__init__(
            code="COUPON_EXPIRED",
            message=f"优惠券 '{coupon_code}' 已过期",
            status_code=400
        )


class CouponUsedError(AppException):
    """优惠券已使用"""
    
    def __init__(self, coupon_code: str):
        super().__init__(
            code="COUPON_USED",
            message=f"优惠券 '{coupon_code}' 已使用",
            status_code=400
        )
```

### 5.2 使用自定义异常

```python
from exceptions import CouponExpiredError, CouponUsedError

@app.post("/coupons/apply")
def apply_coupon(coupon_code: str, db: Session = Depends(get_db)):
    coupon = get_coupon(db, coupon_code)
    
    if not coupon:
        raise InvalidParameterError("coupon_code", coupon_code, "优惠券不存在")
    
    if coupon.is_expired():
        raise CouponExpiredError(coupon_code)
    
    if coupon.is_used:
        raise CouponUsedError(coupon_code)
    
    # 应用优惠券
    ...
```

---

## 六、最佳实践

### 6.1 选择合适的异常类

- **使用具体的异常类**：不要使用通用的Exception或AppException
- **优先使用业务异常**：如UserNotFoundError而非404错误
- **包含详细信息**：帮助前端定位问题

### 6.2 错误消息编写

```python
# ✅ 好的错误消息
raise UserNotFoundError(user_id=123)
# 输出: "用户ID 123 不存在"

# ❌ 不好的错误消息
raise AppException("USER_NOT_FOUND", "用户不存在")
# 输出: "用户不存在" (缺少上下文)
```

### 6.3 日志记录

异常处理器会自动记录异常日志，无需手动记录：

```python
# ❌ 不需要
try:
    user = get_user(user_id)
except Exception as e:
    logger.error(f"Error getting user: {e}")
    raise UserNotFoundError(user_id)

# ✅ 直接抛出即可
user = get_user(user_id)
if not user:
    raise UserNotFoundError(user_id)
```

---

## 七、集成到现有应用

### 7.1 注册异常处理器

在main.py中添加：

```python
from error_handlers import register_exception_handlers

app = FastAPI()

# 注册异常处理器
register_exception_handlers(app)
```

### 7.2 替换现有的错误处理

**之前：**
```python
if not user:
    raise HTTPException(status_code=404, detail="User not found")
```

**之后：**
```python
if not user:
    raise UserNotFoundError(user_id=user_id)
```

---

## 八、测试示例

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_user_not_found():
    """测试用户不存在异常"""
    response = client.get("/api/users/99999")
    
    assert response.status_code == 404
    data = response.json()
    
    assert data["success"] is False
    assert data["error"]["code"] == "USER_NOT_FOUND"
    assert "99999" in data["error"]["message"]


def test_insufficient_balance():
    """测试余额不足异常"""
    response = client.post("/api/transactions", json={
        "user_id": 1,
        "product_id": 1,
        "quantity": 100
    })
    
    assert response.status_code == 400
    data = response.json()
    
    assert data["success"] is False
    assert data["error"]["code"] == "INSUFFICIENT_BALANCE"
    assert "required" in data["error"]["details"]
    assert "available" in data["error"]["details"]
```

---

**文档版本：** v1.0  
**更新时间：** 2026年4月2日