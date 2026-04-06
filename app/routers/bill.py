from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import oauth2
from app.database import get_db
from app.models.bill import Bill
from app.models.user import User
from app.schemas.bill import BillCreateRequest, BillCreateResponse, BillOut
from app.services.billing_service import BillingService


router = APIRouter(
    prefix="/bill",
    tags=["Bill"],
)


@router.get("/", response_model=List[BillOut])
def get_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return db.query(Bill).order_by(Bill.created_at.desc()).all()


@router.post("/", response_model=BillCreateResponse, status_code=status.HTTP_201_CREATED)
def create_bill(
    payload: BillCreateRequest,
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
    )
