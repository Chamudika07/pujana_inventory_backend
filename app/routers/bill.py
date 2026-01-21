from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException , status
from app import  oauth2
from app.database import get_db
from sqlalchemy import func
from typing import Literal , List
from app.function.automatic_bill_id_generation import generate_bill_id
from app.models.bill import Bill 
from app.models.item import Item
from app.models.inventory import InventoryTransaction
from app.schemas.bill import BillOut , BillItemAction , BillItemOut


router = APIRouter(
    prefix = '/bill',
    tags = ['bill']
)

#get all bills
@router.get("/", response_model = List[BillOut])
def get_bills(db : Session = Depends(get_db) , 
              current_user : int = Depends(oauth2.get_current_user)):
    
    bills = db.query(Bill).all()
    
    return bills




#bill Print API
@router.get("/{bill_id}" )
def print_bill(bill_id : str , db : Session = Depends(get_db) ,
            current_user : int = Depends(oauth2.get_current_user)):
    
    bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
    
    if not bill:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND ,
                            detail = f"Bill with id {bill_id} not found")
    
    transaction = bill.inventory_transactions
    total_amount = 0
    items = []
    
    for t in transaction:
        total = t.quantity * t.price
        total_amount += total 
        
        items.append({
            "item" : t.items.name ,
            "quantity" : t.quantity , 
            "price" : t.price ,
             "total" : total
        })
        
    return {
        "bill_id": bill.bill_id,
        "bill_type": bill.bill_type,
        "items": items,
        "grand_total": total_amount
    }





#start bill Api (buy or sell button click)
@router.post("/start")
def start_bill(bill_type : Literal["buy" , "sell"],
               db : Session = Depends(get_db),
               current_user : int = Depends(oauth2.get_current_user)):
    
    bill_id = generate_bill_id(bill_type)
    
    bill = Bill(bill_id = bill_id , bill_type = bill_type)
    
    db.add(bill)
    db.commit()
    db.refresh(bill)
    
    return {
        "bill_id" : bill.bill_id ,
        "bull_type" : bill.bill_type ,
        "message" : f"{bill_type.upper()} bill started "
    }
    
    
#add items to bill will be implemented in inventory router
@router.post("/item" , response_model = BillItemOut)
def add_item_to_bill(data : BillItemAction , db : Session = Depends(get_db) , 
                    current_user : int = Depends(oauth2.get_current_user)):
    
    bill = db.query(Bill).filter(Bill.bill_id == data.bill_id).first()
    if not bill:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND , 
                            detail = f"Bill with id {data.bill_id} not found")
        
    item = db.query(Item).filter(Item.model_number == data.model_number).first()
    if not item:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND , 
                        detail = f"Item with model number {data.model_number} not found")
        
    if bill.bill_type == "buy":
        item.quantity += data.quantity
        price = item.buying_price
        
    elif bill.bill_type == "sell":
        if item.quantity < data.quantity:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST ,
                            detail = f"Insufficient stock for item {data.model_number}")
        item.quantity -= data.quantity
        price = item.selling_price
    
    transaction = InventoryTransaction(
        bill_id = bill.bill_id ,
        item_id = item.id , 
        transaction_type = bill.bill_type ,
        quantity = data.quantity ,
        price = price
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction
         
    
        
