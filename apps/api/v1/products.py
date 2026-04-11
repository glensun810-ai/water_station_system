"""
产品管理API - v1版本
为前端 products.html 页面提供完整的产品管理接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from config.database import get_db
from models.product import Product, ProductCategory

router = APIRouter(prefix="/products", tags=["产品管理"])

category_router = APIRouter(prefix="/admin/product-categories", tags=["产品分类"])


class ProductBase(BaseModel):
    name: str
    specification: Optional[str] = None
    unit: str = "桶"
    price: float
    cost_price: Optional[float] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    barcode: Optional[str] = None
    promo_threshold: int = 10
    promo_gift: int = 1
    stock_alert: int = 10


class ProductCreate(ProductBase):
    stock: int = 0
    is_active: int = 1


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    barcode: Optional[str] = None
    promo_threshold: Optional[int] = None
    promo_gift: Optional[int] = None
    stock_alert: Optional[int] = None
    is_active: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    stock: int
    stock_alert: Optional[int] = 10
    is_active: int
    is_protected: int = 0
    category_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str
    sort_order: int = 0
    is_active: int = 1


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


@router.get("")
def get_products(
    active_only: bool = Query(False, description="仅返回在售产品"),
    is_active: Optional[int] = Query(
        None, description="状态筛选：1-在售，0-停售，None-全部"
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if active_only or is_active == 1:
        query = query.filter(Product.is_active == 1)
    elif is_active == 0:
        query = query.filter(Product.is_active == 0)

    products = query.all()

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
            "stock_alert": p.stock_alert if p.stock_alert is not None else 10,
            "category_name": p.category.name if p.category else None,
        }
        result.append(product_dict)

    return result


@router.get("/export")
def export_products(
    is_active: Optional[int] = Query(None, description="状态筛选"),
    category_id: Optional[int] = Query(None, description="分类筛选"),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    import json

    query = db.query(Product)

    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    products = query.all()

    export_data = []
    for p in products:
        export_data.append(
            {
                "id": p.id,
                "name": p.name,
                "specification": p.specification,
                "unit": p.unit,
                "price": float(p.price) if p.price else 0.0,
                "stock": p.stock,
                "cost_price": float(p.cost_price) if p.cost_price else None,
                "category_id": p.category_id,
                "promo_threshold": p.promo_threshold or 0,
                "promo_gift": p.promo_gift or 0,
                "is_active": p.is_active,
                "stock_alert": p.stock_alert if p.stock_alert is not None else 10,
            }
        )

    return {
        "data": export_data,
        "export_time": datetime.now().isoformat(),
        "total_count": len(export_data),
    }


@router.post("/batch-active")
def batch_set_active(request: dict, db: Session = Depends(get_db)):
    product_ids = request.get("product_ids", [])
    is_active = request.get("is_active", 1)

    updated_count = 0
    errors = []

    for product_id in product_ids:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.is_active = is_active
            updated_count += 1
        else:
            errors.append(f"产品ID {product_id} 不存在")

    db.commit()

    status_text = "上架" if is_active == 1 else "下架"
    return {
        "updated_count": updated_count,
        "errors": errors if errors else None,
        "message": f"成功将 {updated_count} 个产品{status_text}",
    }


@router.post("/batch-delete")
def batch_delete_products(product_ids: List[int], db: Session = Depends(get_db)):
    deleted_count = 0
    errors = []

    for product_id in product_ids:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            errors.append(f"产品ID {product_id} 不存在")
            continue

        if hasattr(product, "is_protected") and product.is_protected == 1:
            errors.append(f"产品 '{product.name}' 为受保护数据，无法删除")
            continue

        db.delete(product)
        deleted_count += 1

    db.commit()

    return {
        "deleted_count": deleted_count,
        "errors": errors if errors else None,
        "message": f"成功删除 {deleted_count} 个产品",
    }


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return ProductResponse.model_validate(db_product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

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
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    if hasattr(product, "is_protected") and product.is_protected == 1:
        raise HTTPException(status_code=400, detail="该产品为受保护数据，无法删除")

    db.delete(product)
    db.commit()

    return {"message": "删除成功"}


@router.put("/{product_id}/toggle")
def toggle_product_status(product_id: int, db: Session = Depends(get_db)):
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


@category_router.get("", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(ProductCategory).all()
    return [CategoryResponse.model_validate(c) for c in categories]


@category_router.post("", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = ProductCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return CategoryResponse.model_validate(db_category)


@category_router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_db)
):
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
    category = (
        db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    if product_count > 0:
        raise HTTPException(
            status_code=400, detail=f"该分类下有 {product_count} 个产品，无法删除"
        )

    db.delete(category)
    db.commit()

    return {"message": "删除成功"}
