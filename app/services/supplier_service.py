from decimal import Decimal
from typing import Iterable, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillType
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierDetailResponse, SupplierListItem, SupplierSummary, SupplierUpdate
from app.services.financial_service import FinancialService


class SupplierService:
    @staticmethod
    def get_supplier(db: Session, supplier_id: int) -> Supplier:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with id {supplier_id} not found",
            )
        return supplier

    @staticmethod
    def ensure_active_supplier(supplier: Supplier) -> Supplier:
        if not supplier.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected supplier is inactive",
            )
        return supplier

    @staticmethod
    def _build_summary_map(db: Session, supplier_ids: Iterable[int]) -> dict[int, SupplierSummary]:
        supplier_ids = list(supplier_ids)
        if not supplier_ids:
            return {}

        rows = (
            db.query(
                Supplier.id.label("supplier_id"),
                func.count(func.distinct(Bill.id)).label("number_of_purchase_bills"),
                func.coalesce(func.sum(Bill.total_amount), 0).label("total_purchased_amount"),
                func.coalesce(func.sum(Bill.paid_amount), 0).label("total_paid"),
                Supplier.payable_balance.label("payable_balance"),
            )
            .outerjoin(Bill, Bill.supplier_id == Supplier.id)
            .filter(Supplier.id.in_(supplier_ids))
            .filter(or_(Bill.id.is_(None), Bill.bill_type == BillType.buy))
            .group_by(Supplier.id)
            .all()
        )

        summary_map: dict[int, SupplierSummary] = {}
        for row in rows:
            summary_map[row.supplier_id] = SupplierSummary(
                number_of_purchase_bills=int(row.number_of_purchase_bills or 0),
                total_purchased_amount=Decimal(row.total_purchased_amount or 0),
                payable_balance=Decimal(row.payable_balance or 0),
                total_paid=Decimal(row.total_paid or 0),
            )
        return summary_map

    @staticmethod
    def _to_list_item(supplier: Supplier, summary: SupplierSummary) -> SupplierListItem:
        return SupplierListItem(
            id=supplier.id,
            supplier_name=supplier.supplier_name,
            company_name=supplier.company_name,
            contact_person=supplier.contact_person,
            phone_number=supplier.phone_number,
            email=supplier.email,
            payable_balance=supplier.payable_balance,
            is_active=supplier.is_active,
            created_at=supplier.created_at,
            summary=summary,
        )

    @staticmethod
    def list_suppliers(
        db: Session,
        *,
        include_inactive: bool = False,
        query: Optional[str] = None,
    ) -> List[SupplierListItem]:
        supplier_query = db.query(Supplier)
        if not include_inactive:
            supplier_query = supplier_query.filter(Supplier.is_active.is_(True))

        if query:
            q = f"%{query.strip()}%"
            supplier_query = supplier_query.filter(
                or_(
                    Supplier.supplier_name.ilike(q),
                    Supplier.company_name.ilike(q),
                    Supplier.contact_person.ilike(q),
                    Supplier.phone_number.ilike(q),
                    Supplier.email.ilike(q),
                )
            )

        suppliers = supplier_query.order_by(Supplier.supplier_name.asc()).all()
        summary_map = SupplierService._build_summary_map(db, [supplier.id for supplier in suppliers])

        return [
            SupplierService._to_list_item(
                supplier,
                summary_map.get(
                    supplier.id,
                    SupplierSummary(
                        number_of_purchase_bills=0,
                        total_purchased_amount=Decimal("0"),
                        payable_balance=supplier.payable_balance,
                    ),
                ),
            )
            for supplier in suppliers
        ]

    @staticmethod
    def get_supplier_detail(db: Session, supplier_id: int) -> SupplierDetailResponse:
        supplier = SupplierService.get_supplier(db, supplier_id)
        summary = SupplierService._build_summary_map(db, [supplier.id]).get(
            supplier.id,
            SupplierSummary(
                number_of_purchase_bills=0,
                total_purchased_amount=Decimal("0"),
                payable_balance=supplier.payable_balance,
            ),
        )

        list_item = SupplierService._to_list_item(supplier, summary)
        return SupplierDetailResponse(
            **list_item.model_dump(),
            address=supplier.address,
            notes=supplier.notes,
            updated_at=supplier.updated_at,
        )

    @staticmethod
    def create_supplier(db: Session, payload: SupplierCreate) -> Supplier:
        supplier = Supplier(**payload.model_dump())
        supplier.payable_balance = FinancialService.money(supplier.payable_balance)
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        return supplier

    @staticmethod
    def update_supplier(db: Session, supplier_id: int, payload: SupplierUpdate) -> Supplier:
        supplier = SupplierService.get_supplier(db, supplier_id)
        update_data = payload.model_dump(exclude_unset=True)
        update_data.pop("payable_balance", None)

        for field, value in update_data.items():
            setattr(supplier, field, value)

        db.commit()
        db.refresh(supplier)
        return supplier

    @staticmethod
    def deactivate_supplier(db: Session, supplier_id: int) -> None:
        supplier = SupplierService.get_supplier(db, supplier_id)
        supplier.is_active = False
        db.commit()
