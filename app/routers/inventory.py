from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException , status
from app.models import inventory as inventory_model
from app.models import item as item_model
from app import  oauth2
from app.database import get_db
from app.schemas import inventory
from sqlalchemy import func
from typing import List


router = APIRouter(
    prefix="/inventory",
    tags=['inventory']
)


@router.post("/", status_code=status.HTTP_201_CREATED , response_model=inventory.InventoryTransactionOut)
def create_inventory(inventory: inventory.InventoryTransactionCreate , db: Session = Depends(get_db),
                                            current_user: int = Depends(oauth2.get_current_user),):
    # Check item exists
    item = (db.query(item_model.Item).filter(item_model.Item.id == inventory.item_id).first())

    if not item:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,
            detail = f"Item with id {inventory.item_id} not found")

    #  Stock update logic
    if inventory.transaction_type == "buy":
        new_quantity = item.quantity + inventory.quantity

    elif inventory.transaction_type == "sell":
        if item.quantity < inventory.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough stock to sell")
        new_quantity = item.quantity - inventory.quantity

    item.quantity = new_quantity
    # Create inventory transaction
    new_transaction = inventory_model.InventoryTransaction( **inventory.dict())

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction


@router.put("/{id}" , response_model = inventory.InventoryTransactionOut)
def update_inventory(id : int , inventory : inventory.InventoryTransactionUpdate , db: Session = Depends(get_db),
                                            current_user: int = Depends(oauth2.get_current_user), ):
    #checke if inventory transaction exists
    existing_transaction = db.query(inventory_model.InventoryTransaction).filter(inventory_model.InventoryTransaction.id == id )
    
    if not existing_transaction.first():
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND , 
                            detail = f"Inventory transaction with id {id} not found")
        
    # Check item exists
    item = (db.query(item_model.Item).filter(item_model.Item.id == inventory.item_id).first()) 
    
    if not item:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,
            detail = f"Item with id {inventory.item_id} not found")
    
    # update
    existing_transaction.update(inventory.dict() , synchronize_session = False)
    db.commit()
    return existing_transaction  
    
        
        
        