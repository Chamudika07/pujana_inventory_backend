from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from app import oauth2
from app.database import get_db
from typing import List
from app.function.automatic_bill_id_generation import generate_bill_id
from app.models.bill import Bill
from app.models.item import Item
from app.models.inventory import InventoryTransaction
from app.schemas.bill import (
    BillItemAction,
    BillOut,
    BuyRequest,
    SellRequest,
    StartBillResponse,
)


router = APIRouter(
    prefix="/bill",
    tags=["Bill"]
)


def _get_bill_by_code(db: Session, bill_code: str) -> Bill:
    bill = db.query(Bill).filter(Bill.bill_code == bill_code).first()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill not found: {bill_code}",
        )
    return bill


def _get_item_by_model_number(db: Session, model_number: str) -> Item:
    item = db.query(Item).filter(Item.model_number == model_number).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with model number {model_number} not found",
        )
    return item


def _create_transaction(
    *,
    db: Session,
    bill: Bill,
    item: Item,
    quantity: int,
    price,
):
    transaction = InventoryTransaction(
        bill_id=bill.id,
        item_id=item.id,
        quantity=quantity,
        price=price,
        transaction_type=bill.bill_type.value,
    )
    db.add(transaction)


# --get all bills-- #
@router.get("/", response_model=List[BillOut])
def get_bills(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    bills = db.query(Bill).all()
    return bills


@router.post("/start", response_model=StartBillResponse, status_code=status.HTTP_201_CREATED)
def start_bill(
    bill_type: str,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    if bill_type not in {"buy", "sell"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bill_type must be either 'buy' or 'sell'",
        )

    bill = Bill(
        bill_code=generate_bill_id(bill_type),
        bill_type=bill_type,
    )

    db.add(bill)
    db.commit()
    db.refresh(bill)

    return StartBillResponse(
        bill_id=bill.bill_code,
        bill_type=bill.bill_type.value,
        message=f"{bill.bill_type.value.title()} bill started successfully",
    )


@router.post("/item", status_code=status.HTTP_201_CREATED)
def add_item_to_bill(
    data: BillItemAction,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    try:
        bill = _get_bill_by_code(db, data.bill_id)
        item = _get_item_by_model_number(db, data.model_number)

        if data.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0",
            )

        if bill.bill_type.value == "sell":
            if item.quantity < data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Not enough stock",
                )
            item.quantity -= data.quantity
            price = item.selling_price
        else:
            item.quantity += data.quantity
            price = item.buying_price

        _create_transaction(
            db=db,
            bill=bill,
            item=item,
            quantity=data.quantity,
            price=price,
        )

        db.commit()

        return {
            "message": "Item added to bill successfully",
            "bill_id": bill.bill_code,
            "item_id": item.id,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# --create sell inventory -- #
@router.post("/sell")
def sell_item(
    data: SellRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    try:
        bill = Bill(
            bill_code=generate_bill_id("sell"),
            bill_type="sell",
        )

        db.add(bill)
        db.flush()

        item = db.query(Item).filter(Item.id == data.item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )

        if item.quantity < data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough stock",
            )

        item.quantity -= data.quantity

        _create_transaction(
            db=db,
            bill=bill,
            item=item,
            quantity=data.quantity,
            price=data.price,
        )

        db.commit()

        return {
            "message": "Sale completed successfully",
            "bill_code": bill.bill_code,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# --create buy inventory -- #
@router.post("/buy")
def buy_item(
    data: BuyRequest,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    try:
        bill = Bill(
            bill_code=generate_bill_id("buy"),
            bill_type="buy",
        )

        db.add(bill)
        db.flush()

        item = db.query(Item).filter(Item.id == data.item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )

        item.quantity += data.quantity

        _create_transaction(
            db=db,
            bill=bill,
            item=item,
            quantity=data.quantity,
            price=data.price,
        )

        db.commit()

        return {
            "message": "Purchase completed successfully",
            "bill_code": bill.bill_code,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
