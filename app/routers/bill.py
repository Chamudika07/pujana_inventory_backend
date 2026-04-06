from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import oauth2
from app.database import get_db
from app.models.bill import Bill
from app.models.user import User
from app.schemas.bill import (
    BillCreate,
    BillCreateResponse,
    BillDetailResponse,
    BillLineItemResponse,
    BillResponse,
    PaymentSummary,
)
from app.schemas.payment import PaymentCreate, PaymentCreateResult, PaymentResponse
from app.services.billing_service import BillingService
from app.services.payment_service import PaymentService


router = APIRouter(prefix="/bills", tags=["Bills"])


def _serialize_bill_line_items(bill: Bill) -> list[BillLineItemResponse]:
    return [
        BillLineItemResponse(
            id=transaction.id,
            item_id=transaction.item_id,
            item_name=transaction.items.name,
            model_number=transaction.items.model_number,
            quantity=transaction.quantity,
            unit_price=transaction.price,
            line_total=transaction.quantity * transaction.price,
            transaction_type=transaction.transaction_type,
            created_at=transaction.created_at,
        )
        for transaction in bill.inventory_transactions
    ]


def _serialize_bill_detail(bill: Bill) -> BillDetailResponse:
    return BillDetailResponse(
        id=bill.id,
        bill_id=bill.bill_code,
        bill_code=bill.bill_code,
        bill_type=bill.bill_type.value,
        customer_id=bill.customer_id,
        supplier_id=bill.supplier_id,
        customer=bill.customer,
        supplier=bill.supplier,
        subtotal_amount=bill.subtotal_amount,
        discount_amount=bill.discount_amount,
        tax_amount=bill.tax_amount,
        total_amount=bill.total_amount,
        paid_amount=bill.paid_amount,
        due_amount=bill.due_amount,
        payment_status=bill.payment_status.value,
        payment_mode_summary=bill.payment_mode_summary,
        notes=bill.notes,
        finalized_at=bill.finalized_at,
        created_by=bill.created_by,
        created_at=bill.created_at,
        items=_serialize_bill_line_items(bill),
        payments=[PaymentSummary.model_validate(payment) for payment in bill.payments],
    )


@router.get("/", response_model=List[BillResponse])
@router.get("", response_model=List[BillResponse], include_in_schema=False)
@router.get("/legacy", response_model=List[BillResponse], include_in_schema=False)
def get_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return BillingService.list_bills(db)


@router.get("/due", response_model=List[BillResponse])
def get_due_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return BillingService.list_due_bills(db)


@router.get("/payable", response_model=List[BillResponse])
def get_payable_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return BillingService.list_payable_bills(db)


@router.get("/{bill_id}", response_model=BillDetailResponse)
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    bill = BillingService.get_bill(db, bill_id)
    return _serialize_bill_detail(bill)


@router.post("/", response_model=BillCreateResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=BillCreateResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_bill(
    payload: BillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    try:
        bill = BillingService.create_bill(
            db=db,
            user=current_user,
            bill_type=payload.bill_type,
            items=payload.items,
            customer_id=payload.customer_id,
            supplier_id=payload.supplier_id,
            discount_amount=payload.discount_amount,
            tax_amount=payload.tax_amount,
            initial_paid_amount=payload.initial_paid_amount,
            payment_method=payload.payment_method,
            payment_mode_summary=payload.payment_mode_summary,
            notes=payload.notes,
            finalized_at=payload.finalized_at,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    return BillCreateResponse(
        bill_id=bill.bill_code,
        bill_type=bill.bill_type.value,
        message=f"{bill.bill_type.value.title()} bill created successfully",
        total_items=len(payload.items),
        subtotal_amount=bill.subtotal_amount,
        discount_amount=bill.discount_amount,
        tax_amount=bill.tax_amount,
        total_amount=bill.total_amount,
        paid_amount=bill.paid_amount,
        due_amount=bill.due_amount,
        payment_status=bill.payment_status.value,
    )


@router.get("/{bill_id}/payments", response_model=List[PaymentResponse])
def get_bill_payments(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return PaymentService.list_bill_payments(db, bill_id)


@router.post("/{bill_id}/payments", response_model=PaymentCreateResult, status_code=status.HTTP_201_CREATED)
def add_bill_payment(
    bill_id: int,
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    try:
        return PaymentService.add_bill_payment(db, bill_id, payload, current_user)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
