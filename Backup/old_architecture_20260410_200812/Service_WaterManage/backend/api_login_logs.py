"""
用户登录日志管理API
提供登录日志查询、统计和分析功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
from collections import defaultdict

from config.database import get_db
from utils.jwt import verify_token

router = APIRouter(prefix="/api/logs", tags=["login_logs"])
security = HTTPBearer(auto_error=False)


class LoginLogItem(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    role: Optional[str] = None
    login_time: str
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    login_method: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    logout_time: Optional[str] = None
    session_duration: Optional[int] = None


class LoginLogListResponse(BaseModel):
    total: int
    items: List[LoginLogItem]
    page: int
    page_size: int
    has_more: bool


class LoginStatistics(BaseModel):
    total_logins: int
    successful_logins: int
    failed_logins: int
    unique_users: int
    unique_ips: int
    avg_session_duration: Optional[float] = None
    most_active_users: List[dict]
    most_common_devices: List[dict]
    login_timeline: List[dict]


def parse_user_agent(user_agent: str) -> dict:
    """解析User-Agent字符串，提取设备信息"""
    if not user_agent:
        return {"device_type": "Unknown", "browser": "Unknown", "os": "Unknown"}

    result = {"device_type": "Desktop", "browser": "Unknown", "os": "Unknown"}

    # 检测移动设备
    mobile_keywords = ["Mobile", "Android", "iPhone", "iPad", "Windows Phone"]
    if any(keyword in user_agent for keyword in mobile_keywords):
        if "iPad" in user_agent:
            result["device_type"] = "Tablet"
        else:
            result["device_type"] = "Mobile"

    # 检测浏览器
    browser_patterns = [
        ("Chrome", "Chrome"),
        ("Safari", "Safari"),
        ("Firefox", "Firefox"),
        ("Edge", "Edg"),
        ("Opera", "Opera"),
        ("IE", "MSIE"),
    ]
    for browser_name, pattern in browser_patterns:
        if pattern in user_agent:
            result["browser"] = browser_name
            break

    # 检测操作系统
    os_patterns = [
        ("Windows 10", "Windows NT 10"),
        ("Windows", "Windows"),
        ("Mac OS X", "Mac OS X"),
        ("Linux", "Linux"),
        ("Android", "Android"),
        ("iOS", "iPhone OS"),
    ]
    for os_name, pattern in os_patterns:
        if pattern in user_agent:
            result["os"] = os_name
            break

    return result


def check_admin_permission(
    credentials: HTTPAuthorizationCredentials, db: Session
) -> dict:
    """检查管理员权限"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期")

    user_id = payload.get("sub")
    role = payload.get("role")

    if role not in ["super_admin", "admin"]:
        raise HTTPException(status_code=403, detail="权限不足")

    return {"user_id": user_id, "role": role}


@router.get("/login", response_model=LoginLogListResponse)
def get_login_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    device_type: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    查询登录日志列表

    支持筛选：
    - user_id: 用户ID
    - username: 用户名（模糊搜索）
    - status: 登录状态（success/failure）
    - start_date: 开始日期
    - end_date: 结束日期
    - device_type: 设备类型（Desktop/Mobile/Tablet）
    """
    check_admin_permission(credentials, db)

    offset = (page - 1) * page_size

    query = """
        SELECT id, user_id, username, role, login_time, ip_address, 
               device_type, browser, os, login_method, status, 
               failure_reason, logout_time, session_duration
        FROM user_login_logs
        WHERE 1=1
    """
    params = {}

    if user_id:
        query += " AND user_id = :user_id"
        params["user_id"] = user_id

    if username:
        query += " AND username LIKE :username"
        params["username"] = f"%{username}%"

    if status:
        query += " AND status = :status"
        params["status"] = status

    if start_date:
        query += " AND login_time >= :start_date"
        params["start_date"] = start_date

    if end_date:
        query += " AND login_time <= :end_date"
        params["end_date"] = end_date

    if device_type:
        query += " AND device_type = :device_type"
        params["device_type"] = device_type

    query += " ORDER BY login_time DESC LIMIT :limit OFFSET :offset"
    params["limit"] = page_size
    params["offset"] = offset

    result = db.execute(text(query), params)
    logs = result.fetchall()

    # 查询总数
    count_query = """
        SELECT COUNT(*) as total
        FROM user_login_logs
        WHERE 1=1
    """
    count_params = {}

    if user_id:
        count_query += " AND user_id = :user_id"
        count_params["user_id"] = user_id

    if username:
        count_query += " AND username LIKE :username"
        count_params["username"] = f"%{username}%"

    if status:
        count_query += " AND status = :status"
        count_params["status"] = status

    if start_date:
        count_query += " AND login_time >= :start_date"
        count_params["start_date"] = start_date

    if end_date:
        count_query += " AND login_time <= :end_date"
        count_params["end_date"] = end_date

    if device_type:
        count_query += " AND device_type = :device_type"
        count_params["device_type"] = device_type

    total_result = db.execute(text(count_query), count_params)
    total = total_result.fetchone()[0]

    items = []
    for log in logs:
        items.append(
            LoginLogItem(
                id=log.id,
                user_id=log.user_id,
                username=log.username or "Unknown",
                role=log.role or "Unknown",
                login_time=log.login_time or datetime.now().isoformat(),
                ip_address=log.ip_address,
                device_type=log.device_type,
                browser=log.browser,
                os=log.os,
                login_method=log.login_method,
                status=log.status,
                failure_reason=log.failure_reason,
                logout_time=log.logout_time,
                session_duration=log.session_duration,
            )
        )

    return LoginLogListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/statistics", response_model=LoginStatistics)
def get_login_statistics(
    days: int = Query(7, ge=1, le=30),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    获取登录统计信息

    - days: 统计最近N天的数据
    """
    check_admin_permission(credentials, db)

    start_date = datetime.now() - timedelta(days=days)

    # 基础统计
    stats_query = """
        SELECT 
            COUNT(*) as total_logins,
            COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_logins,
            COUNT(CASE WHEN status = 'failure' THEN 1 END) as failed_logins,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT ip_address) as unique_ips,
            AVG(session_duration) as avg_session_duration
        FROM user_login_logs
        WHERE login_time >= :start_date
    """

    stats_result = db.execute(text(stats_query), {"start_date": start_date.isoformat()})
    stats = stats_result.fetchone()

    # 最活跃用户（Top 5）
    active_users_query = """
        SELECT username, COUNT(*) as login_count
        FROM user_login_logs
        WHERE login_time >= :start_date AND status = 'success'
        GROUP BY username
        ORDER BY login_count DESC
        LIMIT 5
    """

    active_users_result = db.execute(
        text(active_users_query), {"start_date": start_date.isoformat()}
    )
    most_active_users = [
        {"username": row.username, "count": row.login_count}
        for row in active_users_result.fetchall()
    ]

    # 设备类型分布
    devices_query = """
        SELECT device_type, COUNT(*) as count
        FROM user_login_logs
        WHERE login_time >= :start_date AND device_type IS NOT NULL
        GROUP BY device_type
        ORDER BY count DESC
    """

    devices_result = db.execute(
        text(devices_query), {"start_date": start_date.isoformat()}
    )
    most_common_devices = [
        {"device_type": row.device_type, "count": row.count}
        for row in devices_result.fetchall()
    ]

    # 登录时间线（按小时统计）
    timeline_query = """
        SELECT 
            DATE(login_time) as date,
            HOUR(login_time) as hour,
            COUNT(*) as count
        FROM user_login_logs
        WHERE login_time >= :start_date AND status = 'success'
        GROUP BY DATE(login_time), HOUR(login_time)
        ORDER BY date, hour
    """

    try:
        timeline_result = db.execute(
            text(timeline_query), {"start_date": start_date.isoformat()}
        )
        login_timeline = [
            {"date": row.date, "hour": row.hour, "count": row.count}
            for row in timeline_result.fetchall()
        ]
    except:
        login_timeline = []

    return LoginStatistics(
        total_logins=stats.total_logins or 0,
        successful_logins=stats.successful_logins or 0,
        failed_logins=stats.failed_logins or 0,
        unique_users=stats.unique_users or 0,
        unique_ips=stats.unique_ips or 0,
        avg_session_duration=stats.avg_session_duration,
        most_active_users=most_active_users,
        most_common_devices=most_common_devices,
        login_timeline=login_timeline,
    )


@router.delete("/{log_id}")
def delete_login_log(
    log_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """删除单条登录日志（仅超级管理员）"""
    user_info = check_admin_permission(credentials, db)

    if user_info["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="仅超级管理员可以删除日志")

    db.execute(text("DELETE FROM user_login_logs WHERE id = :id"), {"id": log_id})
    db.commit()

    return {"message": "删除成功"}


@router.delete("/batch")
def batch_delete_login_logs(
    log_ids: List[int],
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """批量删除登录日志（仅超级管理员）"""
    user_info = check_admin_permission(credentials, db)

    if user_info["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="仅超级管理员可以删除日志")

    if not log_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的日志")

    db.execute(
        text("DELETE FROM user_login_logs WHERE id IN :ids"), {"ids": tuple(log_ids)}
    )
    db.commit()

    return {"message": f"成功删除 {len(log_ids)} 条日志"}
