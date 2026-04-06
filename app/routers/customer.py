from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app import oauth2
from app.database import get_db
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerDetailResponse, CustomerListItem, CustomerUpdate
from app.schemas.payment import CustomerDueSummaryResponse, CustomerLedgerResponse
from app.services.customer_service import CustomerService
from app.services.payment_service import PaymentService


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get("/", response_model=List[CustomerListItem])
def get_customers(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return CustomerService.list_customers(db, include_inactive=include_inactive)


@router.get("/search", response_model=List[CustomerListItem])
def search_customers(
    q: Optional[str] = Query(default=None, min_length=1),
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return CustomerService.list_customers(db, include_inactive=include_inactive, query=q)


@router.get("/{id}", response_model=CustomerDetailResponse)
def get_customer(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return CustomerService.get_customer_detail(db, id)


@router.get("/{id}/ledger", response_model=CustomerLedgerResponse)
def get_customer_ledger(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return PaymentService.customer_ledger(db, id)


@router.get("/{id}/due-summary", response_model=CustomerDueSummaryResponse)
def get_customer_due_summary(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return PaymentService.customer_summary(db, id)


@router.post("/", response_model=CustomerDetailResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    customer = CustomerService.create_customer(db, payload)
    return CustomerService.get_customer_detail(db, customer.id)


@router.put("/{id}", response_model=CustomerDetailResponse)
def update_customer(
    id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    customer = CustomerService.update_customer(db, id, payload)
    return CustomerService.get_customer_detail(db, customer.id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    CustomerService.deactivate_customer(db, id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
