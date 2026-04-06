"""
Unified Account Service - 统一账户服务
实现统一账户管理、余额扣款、领取逻辑
"""
from typing import Dict, Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import json
from fastapi import HTTPException

from models_unified import UserAccount, AccountWallet, SettlementBatch, TransactionV2, PromotionConfigV2
from discount_strategy import discount_context, get_product, ProductInfo
from exceptions import InsufficientBalanceError


class AccountService:
    """
    账户服务类
    
    提供统一的账户管理、余额查询、扣款等功能
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_account(self, user_id: int) -> UserAccount:
        """获取或创建用户账户"""
        account = self.db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
        if not account:
            account = UserAccount(user_id=user_id)
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
        return account
    
    def get_account(self, user_id: int) -> Optional[UserAccount]:
        """获取用户账户"""
        return self.db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
    
    def get_wallet(self, user_id: int, product_id: int, wallet_type: str) -> Optional[AccountWallet]:
        """获取用户钱包"""
        return self.db.query(AccountWallet).filter(
            AccountWallet.user_id == user_id,
            AccountWallet.product_id == product_id,
            AccountWallet.wallet_type == wallet_type
        ).first()
    
    def get_or_create_wallet(self, user_id: int, product_id: int, wallet_type: str) -> AccountWallet:
        """获取或创建用户钱包"""
        wallet = self.db.query(AccountWallet).filter(
            AccountWallet.user_id == user_id,
            AccountWallet.product_id == product_id,
            AccountWallet.wallet_type == wallet_type
        ).first()
        
        if not wallet:
            wallet = AccountWallet(
                user_id=user_id,
                product_id=product_id,
                wallet_type=wallet_type,
                available_qty=0,
                locked_qty=0,
                total_consumed=0
            )
            self.db.add(wallet)
            self.db.commit()
            self.db.refresh(wallet)
        
        return wallet
    
    def get_wallet_balance(self, user_id: int, product_id: int, wallet_type: str) -> int:
        """获取钱包可用余额"""
        wallet = self.get_wallet(user_id, product_id, wallet_type)
        if not wallet:
            return 0
        return wallet.available_qty
    
    def get_total_balance(self, user_id: int, product_id: int) -> Dict:
        """
        获取用户某产品的总余额信息
        
        Returns:
            dict: {
                'credit_available': 信用可用余额,
                'prepaid_available': 预付可用余额,
                'total_available': 总可用余额,
                'credit_locked': 信用锁定余额,
                'prepaid_locked': 预付锁定余额
            }
        """
        credit_wallet = self.get_wallet(user_id, product_id, 'credit')
        prepaid_wallet = self.get_wallet(user_id, product_id, 'prepaid')
        
        return {
            'credit_available': credit_wallet.available_qty if credit_wallet else 0,
            'prepaid_available': prepaid_wallet.available_qty if prepaid_wallet else 0,
            'total_available': (credit_wallet.available_qty if credit_wallet else 0) + 
                              (prepaid_wallet.available_qty if prepaid_wallet else 0),
            'credit_locked': credit_wallet.locked_qty if credit_wallet else 0,
            'prepaid_locked': prepaid_wallet.locked_qty if prepaid_wallet else 0,
        }
    
    def add_prepaid_balance(self, user_id: int, product_id: int, paid_quantity: int, 
                           free_quantity: int = 0, unit_price: float = 0) -> Dict:
        """
        增加预付余额（支持买赠优惠）
        
        Args:
            user_id: 用户 ID
            product_id: 产品 ID
            paid_quantity: 付费数量
            free_quantity: 赠送数量
            unit_price: 单价
            
        Returns:
            dict: 充值结果
        """
        wallet = self.get_or_create_wallet(user_id, product_id, 'prepaid')
        
        # 更新余额
        wallet.paid_qty += paid_quantity
        wallet.free_qty += free_quantity
        wallet.available_qty = wallet.paid_qty + wallet.free_qty
        wallet.total_consumed += 0  # 充值时不增加消费
        
        self.db.commit()
        self.db.refresh(wallet)
        
        total_amount = paid_quantity * unit_price
        
        return {
            'wallet_id': wallet.id,
            'paid_qty': paid_quantity,
            'free_qty': free_quantity,
            'total_qty': paid_quantity + free_quantity,
            'available_qty': wallet.available_qty,
            'total_amount': total_amount,
            'unit_price': unit_price
        }
    
    def add_credit_balance(self, user_id: int, product_id: int, quantity: int) -> Dict:
        """
        增加信用余额（授信）
        
        Args:
            user_id: 用户 ID
            product_id: 产品 ID
            quantity: 授信数量
            
        Returns:
            dict: 授信结果
        """
        wallet = self.get_or_create_wallet(user_id, product_id, 'credit')
        
        # 更新余额
        wallet.available_qty += quantity
        wallet.total_consumed += 0  # 授信时不增加消费
        
        self.db.commit()
        self.db.refresh(wallet)
        
        return {
            'wallet_id': wallet.id,
            'wallet_type': 'credit',
            'quantity': quantity,
            'available_qty': wallet.available_qty
        }
    
    def adjust_wallet_balance(self, user_id: int, product_id: int, wallet_type: str, 
                             quantity: int, note: str = None) -> Dict:
        """
        调整钱包余额（通用方法，支持充值和授信）
        
        Args:
            user_id: 用户 ID
            product_id: 产品 ID
            wallet_type: 钱包类型 ('credit' 或 'prepaid')
            quantity: 调整数量（正数增加，负数减少）
            note: 备注
            
        Returns:
            dict: 调整结果
            
        Raises:
            ValueError: 余额不足时抛出
            InsufficientBalanceError: 预付余额不足时抛出
        """
        if wallet_type not in ['credit', 'prepaid']:
            raise ValueError(f"不支持的钱包类型：{wallet_type}")
        
        if quantity > 0:
            # 增加余额
            if wallet_type == 'prepaid':
                # 预付充值：直接增加付费桶数量
                return self.add_prepaid_balance(
                    user_id=user_id,
                    product_id=product_id,
                    paid_quantity=quantity,
                    free_quantity=0,  # 通过 API 时会计算优惠
                    unit_price=0  # 这里不需要价格
                )
            else:
                # 信用授信
                return self.add_credit_balance(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity
                )
        else:
            # 减少余额
            return self.deduct_balance(
                user_id=user_id,
                product_id=product_id,
                wallet_type=wallet_type,
                quantity=abs(quantity)
            )
    
    def deduct_balance(self, user_id: int, product_id: int, wallet_type: str, quantity: int) -> Dict:
        """
        扣减余额
        
        Args:
            user_id: 用户 ID
            product_id: 产品 ID
            wallet_type: 钱包类型 ('credit' 或 'prepaid')
            quantity: 扣减数量
            
        Returns:
            dict: 扣款结果
            
        Raises:
            ValueError: 余额不足时抛出
        """
        wallet = self.get_wallet(user_id, product_id, wallet_type)
        if not wallet or wallet.available_qty < quantity:
            raise ValueError(f"{wallet_type}余额不足：需要{quantity}，可用{wallet.available_qty if wallet else 0}")
        
        wallet.available_qty -= quantity
        wallet.total_consumed += quantity
        self.db.commit()
        self.db.refresh(wallet)
        
        return {
            'wallet_id': wallet.id,
            'wallet_type': wallet_type,
            'deducted_qty': quantity,
            'remaining_qty': wallet.available_qty
        }
    
    def consume_balance(self, user_id: int, product_id: int, quantity: int) -> Dict:
        """
        统一扣款逻辑 - 严格遵循"先扣付费，后扣赠送"的顺序
            
        扣款优先级：
        1. 优先使用付费数量（已付款）
        2. 再使用赠送数量（免费）
        3. 不足时使用信用余额（标准价）
            
        Args:
            user_id: 用户 ID
            product_id: 产品 ID
            quantity: 消费数量
                
        Returns:
            dict: {
                'paid_qty': 付费消费数量，
                'gift_qty': 赠送消费数量，
                'credit_qty': 信用消费数量，
                'wallet_id': 主要扣款钱包 ID,
                'wallet_type': 主要扣款钱包类型
            }
                
        Raises:
            InsufficientBalanceError: 总余额不足时抛出
        """
        product = get_product(self.db, product_id)
        if not product:
            raise ValueError(f"产品不存在：{product_id}")
            
        # 1. 获取预付钱包
        prepaid_wallet = self.get_wallet(user_id, product_id, 'prepaid')
        paid_available = prepaid_wallet.paid_qty if prepaid_wallet else 0
        free_available = prepaid_wallet.free_qty if prepaid_wallet else 0
            
        # 2. 【修正】优先使用付费数量
        consumed_paid = min(quantity, paid_available)
        wallet_id = None
        wallet_type = 'prepaid'
            
        if consumed_paid > 0:
            wallet_id = prepaid_wallet.id
            
        # 3. 【修正】再使用赠送数量
        remaining_after_paid = quantity - consumed_paid
        consumed_free = min(remaining_after_paid, free_available)
            
        if consumed_free > 0 and wallet_id is None:
            wallet_id = prepaid_wallet.id
            
        # 4. 剩余部分使用信用余额
        remaining = quantity - consumed_paid - consumed_free
        consumed_credit = 0
            
        if remaining > 0:
            credit_wallet = self.get_wallet(user_id, product_id, 'credit')
            credit_available = credit_wallet.available_qty if credit_wallet else 0
                
            if credit_available < remaining:
                # 【修正】抛出自定义异常
                raise InsufficientBalanceError(
                    f"总余额不足：需要{quantity}桶，付费{consumed_paid}桶，赠送{consumed_free}桶，"
                    f"信用{credit_available}桶，缺口{remaining - credit_available}桶",
                    required=quantity,
                    available=consumed_paid + consumed_free + credit_available
                )
                
            # 扣减信用余额
            credit_wallet.available_qty -= remaining
            credit_wallet.total_consumed += remaining
            if wallet_id is None:
                wallet_id = credit_wallet.id
                wallet_type = 'credit'
            consumed_credit = remaining
            
        # 5. 扣减预付钱包
        if consumed_paid > 0 or consumed_free > 0:
            if prepaid_wallet:
                prepaid_wallet.paid_qty -= consumed_paid
                prepaid_wallet.free_qty -= consumed_free
                prepaid_wallet.available_qty = prepaid_wallet.paid_qty + prepaid_wallet.free_qty
                prepaid_wallet.total_consumed += (consumed_paid + consumed_free)
            
        self.db.commit()
            
        if prepaid_wallet:
            self.db.refresh(prepaid_wallet)
        if consumed_credit > 0 and credit_wallet:
            self.db.refresh(credit_wallet)
            
        # 6. 【修正】返回明细信息
        return {
            'paid_qty': consumed_paid,      # 付费桶扣除数量
            'gift_qty': consumed_free,      # 赠送桶扣除数量
            'credit_qty': consumed_credit,  # 信用桶扣除数量
            'wallet_id': wallet_id,
            'wallet_type': wallet_type,
            'total_qty': quantity
        }


class PickupService:
    """
    领取服务类
    
    提供统一的领取逻辑，支持双模式
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.account_service = AccountService(db)
    
    def calculate_pickup(self, user_id: int, product_id: int, quantity: int) -> Dict:
        """
        计算领取详情（不实际扣款）
        
        Args:
            user_id: 用户 ID
            product_id: 产品 ID
            quantity: 领取数量
            
        Returns:
            dict: 领取详情
        """
        product = get_product(self.db, product_id)
        if not product:
            raise ValueError(f"产品不存在：{product_id}")
        
        # 获取余额信息
        balance = self.account_service.get_total_balance(user_id, product_id)
        
        # 计算扣款分配
        consumed_prepaid = min(quantity, balance['prepaid_available'])
        consumed_credit = quantity - consumed_prepaid
        
        # 检查余额是否充足
        if consumed_credit > balance['credit_available']:
            raise ValueError(
                f"余额不足：需要{quantity}，预付{consumed_prepaid}，信用{balance['credit_available']}，"
                f"缺口{consumed_credit - balance['credit_available']}"
            )
        
        # 计算价格（预付部分享受优惠）
        prepaid_result = discount_context.calculate_discount(
            self.db, product_id, consumed_prepaid, 'prepaid', user_id
        ) if consumed_prepaid > 0 else {
            'unit_price': product.price,
            'paid_qty': 0,
            'free_qty': 0,
            'total_price': 0,
            'discount_desc': ''
        }
        
        credit_result = discount_context.calculate_discount(
            self.db, product_id, consumed_credit, 'credit', user_id
        ) if consumed_credit > 0 else {
            'unit_price': product.price,
            'paid_qty': 0,
            'free_qty': 0,
            'total_price': 0,
            'discount_desc': ''
        }
        
        return {
            'quantity': quantity,
            'prepaid': {
                'qty': consumed_prepaid,
                'unit_price': prepaid_result['unit_price'],
                'total_price': prepaid_result['total_price'],
                'free_qty': prepaid_result['free_qty'],
                'discount_desc': prepaid_result['discount_desc']
            },
            'credit': {
                'qty': consumed_credit,
                'unit_price': credit_result['unit_price'],
                'total_price': credit_result['total_price'],
                'free_qty': credit_result['free_qty'],
                'discount_desc': credit_result['discount_desc']
            },
            'total_price': prepaid_result['total_price'] + credit_result['total_price'],
            'balance_after': {
                'prepaid': balance['prepaid_available'] - consumed_prepaid,
                'credit': balance['credit_available'] - consumed_credit
            }
        }
    
    def record_pickup(self, user_id: int, product_id: int, quantity: int, 
                     note: str = None) -> Dict:
        """
        记录领取（统一领取逻辑）- 在事务中完成，记录详细的领用明细
        
        Args:
            user_id: 用户 ID
            product_id: 产品 ID
            quantity: 领取数量
            note: 备注
            
        Returns:
            dict: 领取结果
        """
        product = get_product(self.db, product_id)
        if not product:
            raise ValueError(f"产品不存在：{product_id}")
        
        try:
            # 1. 计算扣款（先付费后赠送）
            consume_result = self.account_service.consume_balance(user_id, product_id, quantity)
            
            # 2. 创建交易记录（区分付费桶和赠送桶）
            transactions = []
            
            # 2.1 付费部分交易记录
            if consume_result['paid_qty'] > 0:
                prepaid_price_info = discount_context.calculate_discount(
                    self.db, product_id, consume_result['paid_qty'], 'prepaid', user_id
                )
                
                txn_prepaid = TransactionV2(
                    user_id=user_id,
                    product_id=product_id,
                    wallet_id=consume_result['wallet_id'],
                    quantity=consume_result['paid_qty'],
                    unit_price=prepaid_price_info['unit_price'],
                    actual_price=prepaid_price_info['total_price'],
                    mode='prepaid',
                    wallet_type='prepaid',
                    status='settled',  # 预付模式直接结算
                    settlement_status='settled',
                    paid_amount=prepaid_price_info['total_price'],
                    remaining_amount=0.0,
                    discount_desc=prepaid_price_info['discount_desc'],
                    free_qty=prepaid_price_info['free_qty'],
                    # 【新增】领用明细
                    paid_qty_deducted=consume_result['paid_qty'],
                    gift_qty_deducted=0,  # 付费桶不享受赠送
                    financial_amount=prepaid_price_info['total_price']
                )
                self.db.add(txn_prepaid)
                transactions.append(txn_prepaid)
            
            # 2.2 赠送部分交易记录（金额为 0）
            if consume_result['gift_qty'] > 0:
                txn_gift = TransactionV2(
                    user_id=user_id,
                    product_id=product_id,
                    wallet_id=consume_result['wallet_id'],
                    quantity=consume_result['gift_qty'],
                    unit_price=0.0,  # 赠送桶单价为 0
                    actual_price=0.0,  # 金额为 0
                    mode='prepaid',
                    wallet_type='prepaid',
                    status='settled',
                    settlement_status='settled',
                    paid_amount=0.0,
                    remaining_amount=0.0,
                    discount_desc='赠送桶免费',
                    free_qty=0,
                    # 【新增】领用明细
                    paid_qty_deducted=0,
                    gift_qty_deducted=consume_result['gift_qty'],
                    financial_amount=0.0  # 赠送桶对应 0 元
                )
                self.db.add(txn_gift)
                transactions.append(txn_gift)
            
            # 2.3 信用部分交易记录
            if consume_result['credit_qty'] > 0:
                credit_price_info = discount_context.calculate_discount(
                    self.db, product_id, consume_result['credit_qty'], 'credit', user_id
                )
                
                txn_credit = TransactionV2(
                    user_id=user_id,
                    product_id=product_id,
                    wallet_id=consume_result['wallet_id'],
                    quantity=consume_result['credit_qty'],
                    unit_price=credit_price_info['unit_price'],
                    actual_price=credit_price_info['total_price'],
                    mode='credit',
                    wallet_type='credit',
                    status='pending',  # 信用模式待结算
                    settlement_status='pending',
                    paid_amount=0.0,
                    remaining_amount=credit_price_info['total_price'],
                    discount_desc=credit_price_info['discount_desc'],
                    free_qty=credit_price_info['free_qty'],
                    # 【新增】领用明细
                    paid_qty_deducted=0,
                    gift_qty_deducted=0,
                    financial_amount=credit_price_info['total_price']
                )
                self.db.add(txn_credit)
                transactions.append(txn_credit)
            
            self.db.commit()
            
            # 刷新获取 ID
            for txn in transactions:
                self.db.refresh(txn)
            
            return {
                'transactions': [
                    {
                        'id': txn.id,
                        'mode': txn.mode,
                        'quantity': txn.quantity,
                        'actual_price': txn.actual_price,
                        'status': txn.status,
                        'discount_desc': txn.discount_desc,
                        'paid_qty_deducted': txn.paid_qty_deducted,
                        'gift_qty_deducted': txn.gift_qty_deducted,
                        'financial_amount': txn.financial_amount
                    }
                    for txn in transactions
                ],
                'consume_result': consume_result,
                'message': f"领取成功：{quantity} {product.unit}"
            }
            
        except InsufficientBalanceError as e:
            # 【新增】异常处理
            raise HTTPException(status_code=400, detail=str(e))
    
    def get_user_pickup_balance(self, user_id: int, product_id: int = None) -> Dict:
        """
        获取用户领取余额信息
        
        Args:
            user_id: 用户 ID
            product_id: 产品 ID（可选，为 None 时返回所有产品）
            
        Returns:
            dict: 余额信息
        """
        # 获取所有产品或指定产品
        if product_id:
            products = [get_product(self.db, product_id)]
        else:
            result = self.db.execute(
                text("SELECT id, name, specification, unit, price FROM products WHERE is_active = 1")
            ).fetchall()
            products = [ProductInfo(id=r[0], name=r[1], price=r[4], specification=r[2] or '', unit=r[3] or 'unit') 
                       for r in result]
        
        result = {
            'user_id': user_id,
            'products': []
        }
        
        for product in products:
            if not product:
                continue
            
            balance = self.account_service.get_total_balance(user_id, product.id)
            
            result['products'].append({
                'product_id': product.id,
                'product_name': product.name,
                'specification': product.specification,
                'unit': product.unit,
                'price': product.price,
                'balance': balance
            })
        
        return result


class SettlementService:
    """
    结算服务类
    
    提供先用后付模式的结算功能
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.account_service = AccountService(db)
    
    def apply_settlement(self, user_id: int, transaction_ids: List[int]) -> SettlementBatch:
        """
        申请结算
        
        Args:
            user_id: 用户 ID
            transaction_ids: 交易 ID 列表
            
        Returns:
            SettlementBatch: 结算批次
        """
        # 查询交易记录
        transactions = self.db.query(TransactionV2).filter(
            TransactionV2.id.in_(transaction_ids),
            TransactionV2.user_id == user_id,
            TransactionV2.mode == 'credit',
            TransactionV2.status == 'pending'
        ).all()
        
        if not transactions:
            raise ValueError("没有可结算的交易记录")
        
        # 计算总金额
        total_amount = sum(t.actual_price for t in transactions)
        
        # 创建结算批次
        batch_no = f"BATCH_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id}"
        batch = SettlementBatch(
            batch_no=batch_no,
            user_id=user_id,
            transaction_ids=json.dumps(transaction_ids),
            total_amount=total_amount,
            status='pending'
        )
        
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        
        # 更新交易记录状态：已支付待确认（对应旧系统 settlement_applied=1）
        for txn in transactions:
            txn.status = 'applied'
            txn.settlement_batch_id = batch.id
        self.db.commit()
        
        return batch
    
    def confirm_settlement(self, batch_id: int, confirmed_by: int) -> SettlementBatch:
        """
        确认结算
        
        Args:
            batch_id: 批次 ID
            confirmed_by: 确认人 ID（管理员）
            
        Returns:
            SettlementBatch: 结算批次
        """
        batch = self.db.query(SettlementBatch).filter(SettlementBatch.id == batch_id).first()
        if not batch:
            raise ValueError("结算批次不存在")
        
        if batch.status != 'pending':
            raise ValueError(f"结算批次状态不正确：{batch.status}")
        
        batch.status = 'completed'
        batch.confirmed_at = datetime.now()
        batch.confirmed_by = confirmed_by

        # 批次确认后，将批次内交易标记为已结算
        try:
            transaction_ids = json.loads(batch.transaction_ids)
        except Exception:
            transaction_ids = []
        if transaction_ids:
            txns = self.db.query(TransactionV2).filter(
                TransactionV2.id.in_(transaction_ids),
                TransactionV2.user_id == batch.user_id,
                TransactionV2.mode == 'credit'
            ).all()
            for txn in txns:
                txn.status = 'settled'
                txn.settlement_status = 'settled'
                txn.paid_amount = txn.actual_price
                txn.remaining_amount = 0.0

        self.db.commit()
        
        return batch
    
    def get_pending_settlements(self, user_id: int = None) -> List[SettlementBatch]:
        """
        获取待结算列表
        
        Args:
            user_id: 用户 ID（可选）
            
        Returns:
            list: 待结算批次列表
        """
        query = self.db.query(SettlementBatch).filter(SettlementBatch.status == 'pending')
        
        if user_id:
            query = query.filter(SettlementBatch.user_id == user_id)
        
        return query.all()


def get_account_service(db: Session) -> AccountService:
    """获取账户服务实例"""
    return AccountService(db)


def get_pickup_service(db: Session) -> PickupService:
    """获取领取服务实例"""
    return PickupService(db)


def get_settlement_service(db: Session) -> SettlementService:
    """获取结算服务实例"""
    return SettlementService(db)
