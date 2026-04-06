from decimal import Decimal
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.function.automatic_bill_id_generation import generate_bill_id
from app.models.bill import Bill
from app.models.customer import Customer
from app.models.inventory import InventoryTransaction
from app.models.item import Item
from app.models.user import User
from app.services.alert_service import AlertService
from app.services.customer_service import CustomerService


class BillingService:
    @staticmethod
    def create_bill(
        *,
        db: Session,
        user: User,
        bill_type: str,
        items: Iterable,
        customer_id: int | None = None,
    ) -> Bill:
        if bill_type not in {"buy", "sell"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="bill_type must be either 'buy' or 'sell'",
            )

        items = list(items)
        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one bill item is required",
            )

        customer: Customer | None = None
        if customer_id is not None:
            if bill_type != "sell":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="customer_id can only be used with sell bills",
                )
            customer = CustomerService.ensure_active_customer(CustomerService.get_customer(db, customer_id))

        bill = Bill(
            bill_code=generate_bill_id(bill_type),
            bill_type=bill_type,
            customer_id=customer.id if customer else None,
        )
        db.add(bill)
        db.flush()

        for line in items:
            item = db.query(Item).filter(Item.model_number == line.model_number).with_for_update().first()

            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item with model number {line.model_number} not found",
                )

            if line.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity must be greater than 0 for {line.model_number}",
                )

            if bill_type == "sell":
                if item.quantity < line.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Not enough stock for {item.model_number}",
                    )
                item.quantity -= line.quantity
                price = item.selling_price
            else:
                item.quantity += line.quantity
                price = item.buying_price

            db.add(
                InventoryTransaction(
                    bill_id=bill.id,
                    item_id=item.id,
                    quantity=line.quantity,
                    price=Decimal(price),
                    transaction_type=bill_type,
                )
            )

            if item.quantity < user.alert_threshold:
                AlertService.upsert_low_stock_alert(
                    db=db,
                    item_id=item.id,
                    user_id=user.id,
                    current_quantity=item.quantity,
                )
            else:
                AlertService.resolve_alert(db=db, item_id=item.id, user_id=user.id)

        db.commit()
        db.refresh(bill)
        return bill
