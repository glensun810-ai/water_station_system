"""
产品相关API
使用ProductService处理业务逻辑
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from config.database import get_db
from services import ProductService
from api_new import require_admin, require_user
from models import User

router = APIRouter(prefix="/v2/products", tags=["Products (New Architecture)"])


class ProductCreate(BaseModel):
    name: str
    category_id: int
    price: float
    service_type: str
    description: Optional[str] = None
    unit: Optional[str] = None
    stock: int = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    stock: Optional[int] = None
    is_active: Optional[int] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    category_id: int
    price: float
    service_type: str
    description: Optional[str]
    unit: Optional[str]
    stock: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    id: int
    name: str
    service_type: str
    description: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    获取产品列表
    """
    product_service = ProductService(db)
    products = product_service.get_products(skip, limit)
    return products


@router.get("/category/{category_id}", response_model=List[ProductResponse])
async def get_products_by_category(
    category_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    根据分类获取产品
    """
    product_service = ProductService(db)
    products = product_service.get_products_by_category(category_id, skip, limit)
    return products


@router.get("/service-type/{service_type}", response_model=List[ProductResponse])
async def get_products_by_service_type(
    service_type: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    根据服务类型获取产品
    """
    product_service = ProductService(db)
    products = product_service.get_products_by_service_type(service_type, skip, limit)
    return products


@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    搜索产品
    """
    product_service = ProductService(db)
    products = product_service.search_products(keyword, skip, limit)
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    获取单个产品
    """
    product_service = ProductService(db)
    product = product_service.get_product(product_id)

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")

    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    创建产品
    """
    product_service = ProductService(db)
    product = product_service.create_product(product_data.model_dump())
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    更新产品信息
    """
    product_service = ProductService(db)

    update_dict = product_data.model_dump(exclude_unset=True)
    product = product_service.update_product(product_id, update_dict)

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    删除产品（软删除）
    """
    product_service = ProductService(db)

    success = product_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")


@router.put("/{product_id}/stock")
async def update_stock(
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    更新库存
    """
    product_service = ProductService(db)

    success = product_service.update_stock(product_id, quantity)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")

    return {"message": "库存已更新", "product_id": product_id, "new_quantity": quantity}


# 分类相关API
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    db: Session = Depends(get_db),
):
    """
    获取所有分类
    """
    product_service = ProductService(db)
    categories = product_service.get_categories()
    return categories


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    """
    获取单个分类
    """
    product_service = ProductService(db)
    category = product_service.get_category(category_id)

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")

    return category


@router.post(
    "/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    name: str,
    service_type: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    创建分类
    """
    product_service = ProductService(db)

    category_data = {
        "name": name,
        "service_type": service_type,
        "description": description,
    }

    category = product_service.create_category(category_data)
    return category
