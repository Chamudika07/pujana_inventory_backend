from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app import oauth2
from app.database import get_db
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierDetailResponse, SupplierListItem, SupplierUpdate
from app.services.supplier_service import SupplierService


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)


@router.get("/", response_model=List[SupplierListItem])
def get_suppliers(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return SupplierService.list_suppliers(db, include_inactive=include_inactive)


@router.get("/search", response_model=List[SupplierListItem])
def search_suppliers(
    q: Optional[str] = Query(default=None, min_length=1),
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return SupplierService.list_suppliers(db, include_inactive=include_inactive, query=q)


@router.get("/{id}", response_model=SupplierDetailResponse)
def get_supplier(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return SupplierService.get_supplier_detail(db, id)


@router.post("/", response_model=SupplierDetailResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    supplier = SupplierService.create_supplier(db, payload)
    return SupplierService.get_supplier_detail(db, supplier.id)


@router.put("/{id}", response_model=SupplierDetailResponse)
def update_supplier(
    id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    supplier = SupplierService.update_supplier(db, id, payload)
    return SupplierService.get_supplier_detail(db, supplier.id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    SupplierService.deactivate_supplier(db, id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
