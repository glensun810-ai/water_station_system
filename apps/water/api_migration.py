"""
Migration and Dual-Write API Routes - 迁移和双写 API 路由
提供数据迁移、双写管理、一致性校验等接口
"""
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Optional
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models_unified import UserAccount, AccountWallet, SettlementBatch, TransactionV2
from dual_write_service import DualWriteService, get_dual_write_service

router = APIRouter(prefix="/api/migration", tags=["migration"])


# ==================== 依赖注入 ====================
def get_db_session():
    """获取数据库会话（用于非 FastAPI 路由）"""
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 数据迁移 API ====================

@router.post("/migrate-all")
async def migrate_all_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db_session)):
    """
    执行完整数据迁移
    
    包括：
    - 创建表结构
    - 迁移用户账户
    - 迁移预付订单
    - 迁移交易记录
    - 迁移优惠配置
    
    注意：此操作可能耗时较长，建议在后台执行
    """
    try:
        from migrate_full import DataMigration
        
        migration = DataMigration()
        
        # 执行迁移
        result = migration.run_full_migration(backup=True)
        
        if result['success']:
            return {
                "success": True,
                "message": "迁移成功完成",
                "stats": {
                    "users_migrated": result['stats']['users_migrated'],
                    "wallets_migrated": result['stats']['wallets_migrated'],
                    "transactions_migrated": result['stats']['transactions_migrated'],
                    "promotion_configs_migrated": result['stats']['orders_migrated'],
                    "duration": (result['stats']['end_time'] - result['stats']['start_time']).total_seconds()
                },
                "verification": result.get('verification', {})
            }
        else:
            raise HTTPException(status_code=500, detail=f"迁移失败：{result.get('error', '未知错误')}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"迁移失败：{str(e)}")


@router.post("/migrate/users")
def migrate_users(db: Session = Depends(get_db_session)):
    """迁移用户账户"""
    try:
        from migrate_full import DataMigration
        migration = DataMigration()
        count = migration.migrate_users()
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate/wallets")
def migrate_wallets(db: Session = Depends(get_db_session)):
    """迁移预付订单到钱包"""
    try:
        from migrate_full import DataMigration
        migration = DataMigration()
        count = migration.migrate_prepaid_orders()
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate/transactions")
def migrate_transactions(batch_size: int = 1000, db: Session = Depends(get_db_session)):
    """迁移交易记录"""
    try:
        from migrate_full import DataMigration
        migration = DataMigration()
        count = migration.migrate_transactions(batch_size)
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate/promotions")
def migrate_promotions(db: Session = Depends(get_db_session)):
    """迁移优惠配置"""
    try:
        from migrate_full import DataMigration
        migration = DataMigration()
        count = migration.migrate_promotion_configs()
        return {"success": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 双写管理 API ====================

@router.post("/dual-write/sync-user/{user_id}")
def sync_user_account(user_id: int, db: Session = Depends(get_db_session)):
    """同步单个用户账户"""
    service = DualWriteService(db)
    result = service.sync_user_account(user_id)
    
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get('error', '同步失败'))


@router.post("/dual-write/sync-order/{order_id}")
def sync_prepaid_order(order_id: int, db: Session = Depends(get_db_session)):
    """同步单个预付订单到钱包"""
    service = DualWriteService(db)
    result = service.sync_wallet_from_prepaid_order(order_id)
    
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get('error', '同步失败'))


@router.post("/dual-write/sync-transaction/{transaction_id}")
def sync_transaction(transaction_id: int, db: Session = Depends(get_db_session)):
    """同步单个交易记录"""
    service = DualWriteService(db)
    result = service.sync_transaction_v2(transaction_id)
    
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get('error', '同步失败'))


@router.post("/dual-write/batch-sync-users")
def batch_sync_users(limit: int = 100, db: Session = Depends(get_db_session)):
    """批量同步用户账户"""
    service = DualWriteService(db)
    result = service.batch_sync_users(limit)
    return result


@router.post("/dual-write/batch-sync-orders")
def batch_sync_orders(limit: int = 100, db: Session = Depends(get_db_session)):
    """批量同步预付订单"""
    service = DualWriteService(db)
    result = service.batch_sync_prepaid_orders(limit)
    return result


@router.post("/dual-write/batch-sync-transactions")
def batch_sync_transactions(limit: int = 500, db: Session = Depends(get_db_session)):
    """批量同步交易记录"""
    service = DualWriteService(db)
    result = service.batch_sync_transactions(limit)
    return result


@router.get("/dual-write/stats")
def get_dual_write_stats(db: Session = Depends(get_db_session)):
    """获取双写统计信息"""
    service = DualWriteService(db)
    return service.get_sync_stats()


# ==================== 数据一致性校验 API ====================

@router.get("/verify/consistency")
def verify_data_consistency(db: Session = Depends(get_db_session)):
    """校验数据一致性"""
    service = DualWriteService(db)
    result = service.verify_data_consistency()
    
    if result.get('consistent', False):
        return {
            "consistent": True,
            "message": "数据一致性校验通过",
            "checked_at": result.get('checked_at')
        }
    else:
        return {
            "consistent": False,
            "message": "发现数据不一致",
            "issues": result.get('issues', []),
            "checked_at": result.get('checked_at')
        }


@router.get("/verify/stats")
def get_migration_stats(db: Session = Depends(get_db_session)):
    """获取迁移统计信息"""
    try:
        conn = db.bind.connect()
        
        stats = {}
        
        # 新表统计
        conn.execute(text("SELECT 'user_account' as table_name, COUNT(*) as count FROM user_account"))
        
        stats['user_accounts'] = conn.execute(text("SELECT COUNT(*) FROM user_account")).scalar()
        stats['wallets'] = conn.execute(text("SELECT COUNT(*) FROM account_wallet")).scalar()
        stats['transactions_v2'] = conn.execute(text("SELECT COUNT(*) FROM transactions_v2")).scalar()
        stats['promotion_configs_v2'] = conn.execute(text("SELECT COUNT(*) FROM promotion_config_v2")).scalar()
        
        # 旧表统计
        stats['users'] = conn.execute(text("SELECT COUNT(*) FROM users WHERE is_active = 1")).scalar()
        stats['prepaid_orders'] = conn.execute(text("SELECT COUNT(*) FROM prepaid_orders WHERE payment_status = 'paid' AND is_active = 1")).scalar()
        stats['transactions'] = conn.execute(text("SELECT COUNT(*) FROM transactions WHERE is_deleted = 0")).scalar()
        
        # 计算迁移比例
        if stats['users'] > 0:
            stats['user_migration_rate'] = round(stats['user_accounts'] / stats['users'] * 100, 2)
        else:
            stats['user_migration_rate'] = 0
        
        if stats['prepaid_orders'] > 0:
            stats['wallet_migration_rate'] = round(stats['wallets'] / stats['prepaid_orders'] * 100, 2)
        else:
            stats['wallet_migration_rate'] = 0
        
        if stats['transactions'] > 0:
            stats['transaction_migration_rate'] = round(stats['transactions_v2'] / stats['transactions'] * 100, 2)
        else:
            stats['transaction_migration_rate'] = 0
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 回滚 API ====================

@router.post("/rollback")
def rollback_migration(db: Session = Depends(get_db_session)):
    """
    回滚迁移（从备份恢复）
    
    ⚠️ 警告：此操作会删除所有新表数据并从备份恢复
    """
    try:
        from migrate_full import DataMigration
        migration = DataMigration()
        
        success = migration.rollback()
        
        if success:
            return {
                "success": True,
                "message": "回滚成功完成"
            }
        else:
            raise HTTPException(status_code=500, detail="回滚失败，未找到备份文件")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统状态 API ====================

@router.get("/status")
def get_migration_status(db: Session = Depends(get_db_session)):
    """获取迁移状态"""
    try:
        # 检查新表是否存在
        tables = db.execute(text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('user_account', 'account_wallet', 'transactions_v2', 'promotion_config_v2')
        """)).fetchall()
        
        existing_tables = [t[0] for t in tables]
        
        # 检查迁移进度
        stats = get_migration_stats(db)
        
        # 判断迁移状态
        if len(existing_tables) == 0:
            status = "not_started"
            message = "迁移未开始"
        elif stats.get('user_migration_rate', 0) >= 100 and stats.get('wallet_migration_rate', 0) >= 100:
            status = "completed"
            message = "迁移已完成"
        else:
            status = "in_progress"
            message = "迁移进行中"
        
        return {
            "status": status,
            "message": message,
            "tables_created": existing_tables,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables")
def list_tables(db: Session = Depends(get_db_session)):
    """列出所有表"""
    try:
        tables = db.execute(text("""
        SELECT name, 
               (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name = m.name) as index_count
        FROM sqlite_master m
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """)).fetchall()
        
        return [
            {"name": t[0], "index_count": t[1]}
            for t in tables
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
