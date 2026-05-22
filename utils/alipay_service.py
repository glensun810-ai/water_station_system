"""
支付宝支付工具类
封装支付宝SDK的支付和退款功能
"""

from alipay import AliPay
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class AlipayService:
    """支付宝支付服务"""

    def __init__(
        self,
        app_id,
        private_key_path,
        alipay_public_key_path,
        debug=False,
        notify_url=None,
        return_url=None,
    ):
        """
        初始化支付宝服务

        Args:
            app_id: 支付宝应用ID
            private_key_path: 应用私钥文件路径
            alipay_public_key_path: 支付宝公钥文件路径
            debug: 是否沙箱环境
            notify_url: 异步通知地址
            return_url: 同步返回地址
        """
        self.app_id = app_id
        self.debug = debug
        self.notify_url = notify_url
        self.return_url = return_url

        # 初始化支付宝客户端
        self.alipay = AliPay(
            appid=app_id,
            app_notify_url=notify_url,
            app_private_key_path=private_key_path,
            alipay_public_key_path=alipay_public_key_path,
            sign_type="RSA2",
            debug=debug,
        )

    def create_payment(self, order_no, amount, subject, body=None):
        """
        创建支付订单

        Args:
            order_no: 订单号
            amount: 金额
            subject: 订单标题
            body: 订单描述

        Returns:
            支付URL或二维码内容
        """
        try:
            # 电脑网站支付
            order_string = self.alipay.api_alipay_trade_page_pay(
                out_trade_no=order_no,
                total_amount=str(amount),
                subject=subject,
                body=body or subject,
                return_url=self.return_url,
                notify_url=self.notify_url,
            )

            # 沙箱环境URL
            if self.debug:
                pay_url = "https://openapi.alipaydev.com/gateway.do?" + order_string
            else:
                pay_url = "https://openapi.alipay.com/gateway.do?" + order_string

            logger.info(f"创建支付宝订单成功: order_no={order_no}, amount={amount}")

            return {"success": True, "pay_url": pay_url}
        except Exception as e:
            logger.error(f"创建支付宝订单失败: {str(e)}")
            return {"success": False, "message": f"创建支付订单失败: {str(e)}"}

    def create_mobile_payment(self, order_no, amount, subject, body=None):
        """
        创建手机网站支付

        Args:
            order_no: 订单号
            amount: 金额
            subject: 订单标题
            body: 订单描述

        Returns:
            支付URL
        """
        try:
            order_string = self.alipay.api_alipay_trade_wap_pay(
                out_trade_no=order_no,
                total_amount=str(amount),
                subject=subject,
                body=body or subject,
                return_url=self.return_url,
                notify_url=self.notify_url,
            )

            if self.debug:
                pay_url = "https://openapi.alipaydev.com/gateway.do?" + order_string
            else:
                pay_url = "https://openapi.alipay.com/gateway.do?" + order_string

            logger.info(f"创建支付宝手机支付订单成功: order_no={order_no}")

            return {"success": True, "pay_url": pay_url}
        except Exception as e:
            logger.error(f"创建支付宝手机支付订单失败: {str(e)}")
            return {"success": False, "message": f"创建支付订单失败: {str(e)}"}

    def query_payment(self, order_no):
        """
        查询支付订单状态

        Args:
            order_no: 订单号

        Returns:
            订单状态信息
        """
        try:
            response = self.alipay.api_alipay_trade_query(out_trade_no=order_no)

            logger.info(f"查询支付宝订单: order_no={order_no}, response={response}")

            return {"success": True, "data": response}
        except Exception as e:
            logger.error(f"查询支付宝订单失败: {str(e)}")
            return {"success": False, "message": f"查询订单失败: {str(e)}"}

    def verify_notify(self, data):
        """
        验证异步通知签名

        Args:
            data: 支付宝异步通知数据

        Returns:
            验证结果
        """
        try:
            # 提取签名
            signature = data.pop("sign")
            data.pop("sign_type", None)

            # 验证签名
            success = self.alipay.verify(data, signature)

            if success and data.get("trade_status") in (
                "TRADE_SUCCESS",
                "TRADE_FINISHED",
            ):
                logger.info(
                    f"支付宝异步通知验证成功: order_no={data.get('out_trade_no')}"
                )
                return {
                    "success": True,
                    "order_no": data.get("out_trade_no"),
                    "trade_no": data.get("trade_no"),
                    "trade_status": data.get("trade_status"),
                    "total_amount": data.get("total_amount"),
                }
            else:
                logger.warning(f"支付宝异步通知验证失败: data={data}")
                return {"success": False, "message": "签名验证失败"}
        except Exception as e:
            logger.error(f"验证支付宝异步通知失败: {str(e)}")
            return {"success": False, "message": f"验证失败: {str(e)}"}

    def refund(self, order_no, refund_amount, refund_reason=None, out_request_no=None):
        """
        申请退款

        Args:
            order_no: 原订单号
            refund_amount: 退款金额
            refund_reason: 退款原因
            out_request_no: 退款请求号（可选，用于部分退款）

        Returns:
            退款结果
        """
        try:
            response = self.alipay.api_alipay_trade_refund(
                out_trade_no=order_no,
                refund_amount=str(refund_amount),
                refund_reason=refund_reason or "用户申请退款",
                out_request_no=out_request_no or f"{order_no}_refund",
            )

            if response.get("code") == "10000":
                logger.info(
                    f"支付宝退款成功: order_no={order_no}, refund_amount={refund_amount}"
                )
                return {
                    "success": True,
                    "refund_no": response.get("out_request_no"),
                    "trade_no": response.get("trade_no"),
                }
            else:
                logger.error(f"支付宝退款失败: response={response}")
                return {
                    "success": False,
                    "message": response.get("sub_msg", "退款失败"),
                }
        except Exception as e:
            logger.error(f"支付宝退款异常: {str(e)}")
            return {"success": False, "message": f"退款失败: {str(e)}"}

    def close_order(self, order_no):
        """
        关闭订单

        Args:
            order_no: 订单号

        Returns:
            关闭结果
        """
        try:
            response = self.alipay.api_alipay_trade_close(out_trade_no=order_no)

            if response.get("code") == "10000":
                logger.info(f"支付宝订单关闭成功: order_no={order_no}")
                return {"success": True}
            else:
                logger.warning(f"支付宝订单关闭失败: response={response}")
                return {
                    "success": False,
                    "message": response.get("sub_msg", "关闭订单失败"),
                }
        except Exception as e:
            logger.error(f"支付宝订单关闭异常: {str(e)}")
            return {"success": False, "message": f"关闭订单失败: {str(e)}"}


# 创建默认实例的工厂函数
def create_alipay_service(config):
    """
    创建支付宝服务实例

    Args:
        config: 配置字典，包含app_id、private_key_path、alipay_public_key_path等

    Returns:
        AlipayService实例
    """
    return AlipayService(
        app_id=config.get("app_id"),
        private_key_path=config.get("private_key_path"),
        alipay_public_key_path=config.get("alipay_public_key_path"),
        debug=config.get("debug", False),
        notify_url=config.get("notify_url"),
        return_url=config.get("return_url"),
    )
