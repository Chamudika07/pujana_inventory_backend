from decimal import Decimal
from typing import Iterable, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillType
from app.models.customer import Customer
from app.models.payment import Payment
from app.schemas.customer import CustomerCreate, CustomerDetailResponse, CustomerListItem, CustomerSummary, CustomerUpdate
from app.services.financial_service import FinancialService


class CustomerService:
    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Customer:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found",
            )
        return customer

    @staticmethod
    def ensure_active_customer(customer: Customer) -> Customer:
        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected customer is inactive",
            )
        return customer

    @staticmethod
    def _build_summary_map(db: Session, customer_ids: Iterable[int]) -> dict[int, CustomerSummary]:
        customer_ids = list(customer_ids)
        if not customer_ids:
            return {}

        rows = (
            db.query(
                Customer.id.label("customer_id"),
                func.count(func.distinct(Bill.id)).label("number_of_bills"),
                func.coalesce(func.sum(Bill.total_amount), 0).label("total_purchases"),
                func.coalesce(func.sum(Bill.paid_amount), 0).label("total_paid"),
                Customer.due_balance.label("due_balance"),
            )
            .outerjoin(Bill, Bill.customer_id == Customer.id)
            .filter(Customer.id.in_(customer_ids))
            .filter(or_(Bill.id.is_(None), Bill.bill_type == BillType.sell))
            .group_by(Customer.id)
            .all()
        )

        summary_map: dict[int, CustomerSummary] = {}
        for row in rows:
            summary_map[row.customer_id] = CustomerSummary(
                number_of_bills=int(row.number_of_bills or 0),
                total_purchases=Decimal(row.total_purchases or 0),
                due_balance=Decimal(row.due_balance or 0),
                total_paid=Decimal(row.total_paid or 0),
            )
        return summary_map

    @staticmethod
    def _to_list_item(customer: Customer, summary: CustomerSummary) -> CustomerListItem:
        return CustomerListItem(
            id=customer.id,
            full_name=customer.full_name,
            phone_number=customer.phone_number,
            email=customer.email,
            customer_type=customer.customer_type.value if hasattr(customer.customer_type, "value") else str(customer.customer_type),
            loyalty_points=customer.loyalty_points,
            due_balance=customer.due_balance,
            is_active=customer.is_active,
            created_at=customer.created_at,
            summary=summary,
        )

    @staticmethod
    def list_customers(
        db: Session,
        *,
        include_inactive: bool = False,
        query: Optional[str] = None,
    ) -> List[CustomerListItem]:
        customer_query = db.query(Customer)
        if not include_inactive:
            customer_query = customer_query.filter(Customer.is_active.is_(True))

        if query:
            q = f"%{query.strip()}%"
            customer_query = customer_query.filter(
                or_(
                    Customer.full_name.ilike(q),
                    Customer.phone_number.ilike(q),
                    Customer.email.ilike(q),
                )
            )

        customers = customer_query.order_by(Customer.full_name.asc()).all()
        summary_map = CustomerService._build_summary_map(db, [customer.id for customer in customers])

        return [
            CustomerService._to_list_item(
                customer,
                summary_map.get(
                    customer.id,
                    CustomerSummary(number_of_bills=0, total_purchases=Decimal("0"), due_balance=customer.due_balance),
                ),
            )
            for customer in customers
        ]

    @staticmethod
    def get_customer_detail(db: Session, customer_id: int) -> CustomerDetailResponse:
        customer = CustomerService.get_customer(db, customer_id)
        summary = CustomerService._build_summary_map(db, [customer.id]).get(
            customer.id,
            CustomerSummary(number_of_bills=0, total_purchases=Decimal("0"), due_balance=customer.due_balance),
        )

        list_item = CustomerService._to_list_item(customer, summary)
        return CustomerDetailResponse(
            **list_item.model_dump(),
            address=customer.address,
            notes=customer.notes,
            updated_at=customer.updated_at,
        )

    @staticmethod
    def create_customer(db: Session, payload: CustomerCreate) -> Customer:
        customer = Customer(**payload.model_dump())
        customer.due_balance = FinancialService.money(customer.due_balance)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def update_customer(db: Session, customer_id: int, payload: CustomerUpdate) -> Customer:
        customer = CustomerService.get_customer(db, customer_id)
        update_data = payload.model_dump(exclude_unset=True)
        update_data.pop("due_balance", None)

        for field, value in update_data.items():
            setattr(customer, field, value)

        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def deactivate_customer(db: Session, customer_id: int) -> None:
        customer = CustomerService.get_customer(db, customer_id)
        customer.is_active = False
        db.commit()
