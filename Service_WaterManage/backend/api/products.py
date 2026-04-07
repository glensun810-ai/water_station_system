"""
产品API路由
包含产品查询、创建、更新、删除等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from config.database import get_db
from models.product import Product, ProductCategory
from schemas.product import (
    ProductResponse,
    ProductCreate,
    ProductUpdate,
    CategoryResponse,
    CategoryCreate,
    CategoryUpdate,
)

router = APIRouter(prefix="/api/products", tags=["产品管理"])


@router.get("", response_model=List[ProductResponse])
def get_products(
    active_only: bool = Query(False, description="仅返回在售产品"),
    is_active: Optional[int] = Query(
        None, description="状态筛选：1-在售，0-停售，None-全部"
    ),
    db: Session = Depends(get_db),
):
    """
    获取产品列表

    Args:
        active_only: 仅返回在售产品（用户端使用）
        is_active: 状态筛选（管理端使用）

    Returns:
        产品列表
    """
    query = db.query(Product)

    # 筛选条件
    if active_only or is_active == 1:
        query = query.filter(Product.is_active == 1)
    elif is_active == 0:
        query = query.filter(Product.is_active == 0)

    products = query.all()

    # 构建响应
    result = []
    for p in products:
        product_dict = {
            "id": p.id,
            "name": p.name,
            "specification": p.specification,
            "unit": p.unit,
            "price": p.price,
            "stock": p.stock,
            "cost_price": p.cost_price,
            "image_url": p.image_url,
            "description": p.description,
            "category_id": p.category_id,
            "barcode": p.barcode,
            "promo_threshold": p.promo_threshold,
            "promo_gift": p.promo_gift,
            "is_active": p.is_active,
            "is_protected": p.is_protected if hasattr(p, "is_protected") else 0,
            "category_name": p.category.name if p.category else None,
        }
        result.append(product_dict)

    return result


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    获取单个产品详情

    Args:
        product_id: 产品ID

    Returns:
        产品详情
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    创建产品

    Args:
        product: 产品创建数据

    Returns:
        创建的产品
    """
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return ProductResponse.model_validate(db_product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)
):
    """
    更新产品信息

    Args:
        product_id: 产品ID
        product_update: 更新数据

    Returns:
        更新后的产品
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 更新字段
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return ProductResponse.model_validate(product)


@router.put("/{product_id}/stock")
def update_product_stock(
    product_id: int, stock_update: dict, db: Session = Depends(get_db)
):
    """
    更新产品库存

    Args:
        product_id: 产品ID
        stock_update: 库存更新数据 {"stock": 100}

    Returns:
        更新成功消息
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    stock = stock_update.get("stock")
    if stock is None or stock < 0:
        raise HTTPException(status_code=400, detail="请提供有效的库存数量")

    product.stock = stock
    db.commit()
    db.refresh(product)

    return {"message": "库存已更新", "product_id": product_id, "stock": product.stock}


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    删除产品

    Args:
        product_id: 产品ID

    Returns:
        成功消息
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 检查保护状态
    if hasattr(product, "is_protected") and product.is_protected == 1:
        raise HTTPException(status_code=400, detail="该产品为受保护数据，无法删除")

    db.delete(product)
    db.commit()

    return {"message": "删除成功"}


@router.put("/{product_id}/toggle")
def toggle_product_status(product_id: int, db: Session = Depends(get_db)):
    """切换产品启用/停用状态"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    product.is_active = 0 if product.is_active == 1 else 1
    db.commit()
    db.refresh(product)

    status_text = "已启用" if product.is_active == 1 else "已停用"
    return {
        "product_id": product_id,
        "is_active": product.is_active,
        "message": status_text,
    }


@router.put("/{product_id}/protect")
def toggle_product_protection(product_id: int, db: Session = Depends(get_db)):
    """切换产品保护状态"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    product.is_protected = 0 if product.is_protected == 1 else 1
    db.commit()
    db.refresh(product)

    status_text = "已保护" if product.is_protected == 1 else "已解除保护"
    return {
        "product_id": product_id,
        "is_protected": product.is_protected,
        "message": status_text,
    }


@router.put("/{product_id}/promo-toggle")
def toggle_product_promotion(
    product_id: int, enable: bool, db: Session = Depends(get_db)
):
    """快速启停产品优惠"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    if enable:
        product.promo_threshold = 10
        product.promo_gift = 1
        message = "优惠已开启 (买 10 赠 1)"
    else:
        product.promo_threshold = 0
        product.promo_gift = 0
        message = "优惠已关闭"

    db.commit()
    db.refresh(product)

    return {
        "product_id": product_id,
        "product_name": product.name,
        "promo_threshold": product.promo_threshold,
        "promo_gift": product.promo_gift,
        "message": message,
    }


# ==================== 产品分类API ====================

category_router = APIRouter(prefix="/api/admin/product-categories", tags=["产品分类"])


@category_router.get("", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """获取所有产品分类"""
    categories = db.query(ProductCategory).all()
    return [CategoryResponse.model_validate(c) for c in categories]


@category_router.post("", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """创建产品分类"""
    db_category = ProductCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return CategoryResponse.model_validate(db_category)


@category_router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_db)
):
    """更新产品分类"""
    category = (
        db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return CategoryResponse.model_validate(category)


@category_router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """删除产品分类"""
    category = (
        db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 检查是否有关联产品
    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    if product_count > 0:
        raise HTTPException(
            status_code=400, detail=f"该分类下有 {product_count} 个产品，无法删除"
        )

    db.delete(category)
    db.commit()

    return {"message": "删除成功"}
