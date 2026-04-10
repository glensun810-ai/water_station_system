"""
自定义异常类 - 用于业务逻辑异常处理
"""


class InsufficientBalanceError(Exception):
    """
    余额不足异常
    
    当用户账户余额不足以完成操作时抛出此异常
    """
    
    def __init__(self, message: str, required: int = 0, available: int = 0):
        """
        初始化异常
        
        Args:
            message: 错误描述信息
            required: 需要的数量
            available: 可用的数量
        """
        self.message = message
        self.required = required
        self.available = available
        super().__init__(self.message)
    
    def __str__(self):
        return self.message


class WalletNotFoundError(Exception):
    """
    钱包不存在异常
    """
    
    def __init__(self, user_id: int, product_id: int, wallet_type: str):
        self.user_id = user_id
        self.product_id = product_id
        self.wallet_type = wallet_type
        super().__init__(f"钱包不存在：用户{user_id}, 产品{product_id}, 类型{wallet_type}")


class InvalidOperationError(Exception):
    """
    无效操作异常
    """
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
