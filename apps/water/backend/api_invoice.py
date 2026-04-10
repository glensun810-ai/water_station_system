"""
发票API
提供发票申请、查询、下载等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import logging
import os

from config.database import get_db
from models import User, PaymentOrder
from models.payment_order import PaymentOrder as PaymentOrderModel
from models.invoice import Invoice

router = APIRouter()
logger = logging.getLogger(__name__)


class InvoiceApply(BaseModel):
    order_no: str
    invoice_type: str  # individual or company
    title: str
    tax_no: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    email: str


class InvoiceResponse(BaseModel):
    id: int
    invoice_no: str
    order_id: int
    user_id: int
    invoice_type: str
    title: str
    tax_no: Optional[str]
    amount: float
    email: Optional[str]
    status: str
    issued_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceList(BaseModel):
    invoices: List[InvoiceResponse]
    total: int


def generate_invoice_no():
    """生成发票号码"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = uuid.uuid4().hex[:6].upper()
    return f"INV{timestamp}{random_str}"


@router.post("/api/invoices")
async def apply_invoice(
    invoice_data: InvoiceApply, request: Request, db: Session = Depends(get_db)
):
    """
    申请发票
    """
    try:
        # 获取当前用户
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        user_id = int(user_id)

        # 查询订单
        order = (
            db.query(PaymentOrderModel)
            .filter(PaymentOrderModel.order_no == invoice_data.order_no)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        # 验证订单所属用户
        if order.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权操作此订单")

        # 验证订单状态（只能为已支付的订单开具发票）
        if order.status != "paid":
            raise HTTPException(status_code=400, detail="只能为已支付的订单开具发票")

        # 检查是否已申请发票
        existing_invoice = (
            db.query(Invoice).filter(Invoice.order_id == order.id).first()
        )

        if existing_invoice:
            raise HTTPException(status_code=400, detail="该订单已申请发票")

        # 验证企业发票必填税号
        if invoice_data.invoice_type == "company" and not invoice_data.tax_no:
            raise HTTPException(status_code=400, detail="企业发票必须填写税号")

        # 创建发票记录
        invoice_no = generate_invoice_no()
        invoice = Invoice(
            invoice_no=invoice_no,
            order_id=order.id,
            user_id=user_id,
            invoice_type=invoice_data.invoice_type,
            title=invoice_data.title,
            tax_no=invoice_data.tax_no,
            address=invoice_data.address,
            phone=invoice_data.phone,
            bank_name=invoice_data.bank_name,
            bank_account=invoice_data.bank_account,
            amount=order.amount,
            email=invoice_data.email,
            status="pending",
        )

        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        logger.info(
            f"创建发票申请成功: invoice_no={invoice_no}, order_no={invoice_data.order_no}"
        )

        return {"success": True, "message": "发票申请已提交", "invoice_no": invoice_no}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"申请发票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"申请发票失败: {str(e)}")


@router.get("/api/invoices/{invoice_no}", response_model=InvoiceResponse)
async def get_invoice(invoice_no: str, request: Request, db: Session = Depends(get_db)):
    """
    查询发票详情
    """
    try:
        # 获取当前用户
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        user_id = int(user_id)

        invoice = db.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="发票不存在")

        # 验证发票所属用户
        if invoice.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权查看此发票")

        return {
            "id": invoice.id,
            "invoice_no": invoice.invoice_no,
            "order_id": invoice.order_id,
            "user_id": invoice.user_id,
            "invoice_type": invoice.invoice_type,
            "title": invoice.title,
            "tax_no": invoice.tax_no,
            "amount": float(invoice.amount),
            "email": invoice.email,
            "status": invoice.status,
            "issued_at": invoice.issued_at,
            "created_at": invoice.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询发票详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询发票详情失败: {str(e)}")


@router.get("/api/invoices/user/{user_id}", response_model=InvoiceList)
async def get_user_invoices(
    user_id: int,
    request: Request,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """
    获取用户发票列表
    """
    try:
        # 验证权限
        current_user_id = request.headers.get("X-User-Id")
        if not current_user_id:
            raise HTTPException(status_code=401, detail="未登录")

        current_user_id = int(current_user_id)

        # 只能查看自己的发票（管理员可以查看所有）
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="无权查看此用户发票")

        query = db.query(Invoice).filter(Invoice.user_id == user_id)

        if status:
            query = query.filter(Invoice.status == status)

        total = query.count()
        invoices = (
            query.order_by(Invoice.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "invoices": [
                {
                    "id": invoice.id,
                    "invoice_no": invoice.invoice_no,
                    "order_id": invoice.order_id,
                    "user_id": invoice.user_id,
                    "invoice_type": invoice.invoice_type,
                    "title": invoice.title,
                    "tax_no": invoice.tax_no,
                    "amount": float(invoice.amount),
                    "email": invoice.email,
                    "status": invoice.status,
                    "issued_at": invoice.issued_at,
                    "created_at": invoice.created_at,
                }
                for invoice in invoices
            ],
            "total": total,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取发票列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取发票列表失败: {str(e)}")


@router.get("/api/invoices/{invoice_no}/download")
async def download_invoice(
    invoice_no: str, request: Request, db: Session = Depends(get_db)
):
    """
    下载发票PDF
    """
    try:
        # 获取当前用户
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        user_id = int(user_id)

        invoice = db.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="发票不存在")

        # 验证发票所属用户
        if invoice.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权下载此发票")

        # 验证发票状态
        if invoice.status != "issued":
            raise HTTPException(status_code=400, detail="发票尚未开具")

        # 验证文件是否存在
        if not invoice.file_path or not os.path.exists(invoice.file_path):
            raise HTTPException(status_code=404, detail="发票文件不存在")

        logger.info(f"下载发票: invoice_no={invoice_no}, user_id={user_id}")

        return FileResponse(
            path=invoice.file_path,
            filename=f"{invoice_no}.pdf",
            media_type="application/pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载发票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载发票失败: {str(e)}")


# ==================== 管理员发票处理接口 ====================


@router.post("/api/admin/invoices/{invoice_no}/issue")
async def issue_invoice(
    invoice_no: str, request: Request, db: Session = Depends(get_db)
):
    """
    管理员开具发票
    """
    try:
        # TODO: 添加管理员权限验证

        invoice = db.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="发票不存在")

        if invoice.status != "pending":
            raise HTTPException(status_code=400, detail="发票状态不正确")

        # TODO: 生成发票PDF文件
        # 这里应该调用发票生成服务或第三方发票平台API

        # 更新发票状态
        invoice.status = "issued"
        invoice.issued_at = datetime.now()
        # invoice.issued_by = admin_user_id
        # invoice.file_path = f"/path/to/invoices/{invoice_no}.pdf"

        db.commit()

        logger.info(f"发票开具成功: invoice_no={invoice_no}")

        return {"success": True, "message": "发票已开具"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"开具发票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"开具发票失败: {str(e)}")


@router.post("/api/admin/invoices/{invoice_no}/send")
async def send_invoice(
    invoice_no: str, request: Request, db: Session = Depends(get_db)
):
    """
    管理员发送发票到邮箱
    """
    try:
        # TODO: 添加管理员权限验证

        invoice = db.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="发票不存在")

        if invoice.status != "issued":
            raise HTTPException(status_code=400, detail="发票尚未开具")

        if not invoice.email:
            raise HTTPException(status_code=400, detail="发票邮箱地址为空")

        # TODO: 发送邮件
        # 这里应该调用邮件发送服务

        # 更新发票状态
        invoice.status = "sent"

        db.commit()

        logger.info(f"发票发送成功: invoice_no={invoice_no}, email={invoice.email}")

        return {"success": True, "message": f"发票已发送至 {invoice.email}"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"发送发票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发送发票失败: {str(e)}")
