"""
结算操作日志工具模块
提供操作日志记录功能,用于审计追溯
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import json


class SettlementLogger:
    """结算操作日志记录器"""

    # 操作类型枚举
    OPERATION_TYPES = {
        "apply": "申请结算",
        "approve": "审核通过",
        "reject": "审核拒绝",
        "confirm": "确认收款",
        "batch_confirm": "批量确认收款",
        "cancel": "取消结算",
        "remind": "发送提醒",
        "dispute": "报告争议",
        "resolve_dispute": "解决争议",
    }

    # 目标类型枚举
    TARGET_TYPES = {
        "pickup": "领水记录",
        "application": "结算申请单",
        "office": "办公室",
    }

    def __init__(self, db: Session):
        self.db = db

    def log_operation(
        self,
        operation_type: str,
        target_type: str,
        target_id: int,
        operator_id: int,
        operator_name: str,
        operator_role: str = "admin",
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        operation_detail: Optional[Dict[Any, Any]] = None,
        note: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> bool:
        """
        记录操作日志

        Args:
            operation_type: 操作类型(apply/approve/reject/confirm等)
            target_type: 目标类型(pickup/application/office)
            target_id: 目标ID
            operator_id: 操作人ID
            operator_name: 操作人姓名
            operator_role: 操作人角色(admin/office_manager)
            old_status: 原状态
            new_status: 新状态
            operation_detail: 操作详情(字典)
            note: 备注
            ip_address: IP地址
            device_info: 设备信息

        Returns:
            bool: 是否记录成功
        """
        try:
            # 将操作详情转为JSON字符串
            detail_json = (
                json.dumps(operation_detail, ensure_ascii=False)
                if operation_detail
                else None
            )

            # 执行插入
            self.db.execute(
                text("""
                    INSERT INTO settlement_logs 
                    (operation_type, operation_status, target_type, target_id,
                     old_status, new_status, operator_id, operator_name, operator_role,
                     operation_detail, note, operated_at, ip_address, device_info)
                    VALUES 
                    (:operation_type, 'success', :target_type, :target_id,
                     :old_status, :new_status, :operator_id, :operator_name, :operator_role,
                     :operation_detail, :note, :operated_at, :ip_address, :device_info)
                """),
                {
                    "operation_type": operation_type,
                    "target_type": target_type,
                    "target_id": target_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "operator_id": operator_id,
                    "operator_name": operator_name,
                    "operator_role": operator_role,
                    "operation_detail": detail_json,
                    "note": note,
                    "operated_at": datetime.now(),
                    "ip_address": ip_address,
                    "device_info": device_info,
                },
            )

            self.db.commit()
            return True

        except Exception as e:
            print(f"记录操作日志失败: {e}")
            self.db.rollback()
            return False

    def log_batch_operation(
        self,
        operation_type: str,
        target_type: str,
        target_ids: list,
        operator_id: int,
        operator_name: str,
        operator_role: str = "admin",
        operation_detail: Optional[Dict[Any, Any]] = None,
        note: Optional[str] = None,
    ) -> bool:
        """
        记录批量操作日志

        Args:
            operation_type: 操作类型
            target_type: 目标类型
            target_ids: 目标ID列表
            operator_id: 操作人ID
            operator_name: 操作人姓名
            operator_role: 操作人角色
            operation_detail: 操作详情
            note: 备注

        Returns:
            bool: 是否记录成功
        """
        try:
            detail = {
                "target_count": len(target_ids),
                "target_ids": target_ids,
                **(operation_detail or {}),
            }

            # 为每个目标ID记录一条日志
            for target_id in target_ids:
                self.log_operation(
                    operation_type=operation_type,
                    target_type=target_type,
                    target_id=target_id,
                    operator_id=operator_id,
                    operator_name=operator_name,
                    operator_role=operator_role,
                    operation_detail=detail,
                    note=note,
                )

            return True

        except Exception as e:
            print(f"记录批量操作日志失败: {e}")
            return False

    def get_logs(
        self,
        operation_type: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        operator_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """
        查询操作日志

        Args:
            operation_type: 操作类型筛选
            target_type: 目标类型筛选
            target_id: 目标ID筛选
            operator_id: 操作人ID筛选
            start_date: 开始日期(YYYY-MM-DD)
            end_date: 结束日期(YYYY-MM-DD)
            limit: 返回数量限制

        Returns:
            list: 日志记录列表
        """
        try:
            conditions = []
            params = {}

            if operation_type:
                conditions.append("operation_type = :operation_type")
                params["operation_type"] = operation_type

            if target_type:
                conditions.append("target_type = :target_type")
                params["target_type"] = target_type

            if target_id:
                conditions.append("target_id = :target_id")
                params["target_id"] = target_id

            if operator_id:
                conditions.append("operator_id = :operator_id")
                params["operator_id"] = operator_id

            if start_date:
                conditions.append("DATE(operated_at) >= :start_date")
                params["start_date"] = start_date

            if end_date:
                conditions.append("DATE(operated_at) <= :end_date")
                params["end_date"] = end_date

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT * FROM settlement_logs
                WHERE {where_clause}
                ORDER BY operated_at DESC
                LIMIT :limit
            """

            params["limit"] = limit

            result = self.db.execute(text(query), params)
            logs = result.fetchall()

            # 转换为字典列表
            log_list = []
            for log in logs:
                log_dict = {
                    "id": log.id,
                    "operation_type": log.operation_type,
                    "operation_status": log.operation_status,
                    "target_type": log.target_type,
                    "target_id": log.target_id,
                    "old_status": log.old_status,
                    "new_status": log.new_status,
                    "operator_id": log.operator_id,
                    "operator_name": log.operator_name,
                    "operator_role": log.operator_role,
                    "operation_detail": json.loads(log.operation_detail)
                    if log.operation_detail
                    else None,
                    "note": log.note,
                    "operated_at": str(log.operated_at),
                    "ip_address": log.ip_address,
                    "device_info": log.device_info,
                }
                log_list.append(log_dict)

            return log_list

        except Exception as e:
            print(f"查询操作日志失败: {e}")
            return []


# 使用示例
if __name__ == "__main__":
    from config.database import get_db

    db = next(get_db())
    logger = SettlementLogger(db)

    # 记录单个操作
    logger.log_operation(
        operation_type="confirm",
        target_type="pickup",
        target_id=123,
        operator_id=1,
        operator_name="管理员",
        old_status="applied",
        new_status="settled",
        note="确认收款",
    )

    # 记录批量操作
    logger.log_batch_operation(
        operation_type="batch_confirm",
        target_type="pickup",
        target_ids=[1, 2, 3],
        operator_id=1,
        operator_name="管理员",
        note="批量确认收款",
    )

    # 查询日志
    logs = logger.get_logs(operation_type="confirm", limit=10)
    for log in logs:
        print(log)
