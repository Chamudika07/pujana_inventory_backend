from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import oauth2
from app.database import get_db
from app.models.user import User
from app.schemas.payment import (
    CustomerDuePaymentCreate,
    CustomerDueSummaryResponse,
    CustomerLedgerResponse,
    PaymentCreateResult,
    PaymentResponse,
    SupplierLedgerResponse,
    SupplierPayablePaymentCreate,
    SupplierPayableSummaryResponse,
)
from app.services.payment_service import PaymentService


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/customer", response_model=PaymentCreateResult, status_code=status.HTTP_201_CREATED)
def record_customer_payment(
    payload: CustomerDuePaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    try:
        return PaymentService.record_customer_payment(db, payload, current_user)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/customer/{customer_id}", response_model=List[PaymentResponse])
def get_customer_payments(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return PaymentService.list_customer_payments(db, customer_id)


@router.post("/supplier", response_model=PaymentCreateResult, status_code=status.HTTP_201_CREATED)
def record_supplier_payment(
    payload: SupplierPayablePaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    try:
        return PaymentService.record_supplier_payment(db, payload, current_user)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/supplier/{supplier_id}", response_model=List[PaymentResponse])
def get_supplier_payments(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return PaymentService.list_supplier_payments(db, supplier_id)
