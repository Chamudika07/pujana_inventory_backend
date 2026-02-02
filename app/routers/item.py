from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException , status
from app.models import item as item_model
from app.models import category as category_model
from app import  oauth2
from app.database import get_db
from app.schemas import item
from app.services.alert_service import AlertService
from sqlalchemy import func
from typing import List


router = APIRouter(
    prefix="/items",
    tags=['items']
)


#Item Creater
@router.post("/" , response_model = item.ItemOut)
def create_item(item : item.ItemCreate , db: Session = Depends(get_db),
                    current_user: int = Depends(oauth2.get_current_user)):
    
    # check if category name already exists
    existing_item = (db.query(
        item_model.Item)
            .filter(func.lower(item_model.Item.model_number) == item.model_number.lower()).first())
    
    if existing_item:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Item with name {item.model_number} already exists")
        
    existing_category = db.query(category_model.Category).filter(category_model.Category.id == item.category_id).first()
    
    if not existing_category:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND ,
                            detail = f"Category with id {item.category_id} does not exist")
        
    new_item = item_model.Item(**item.dict())
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return new_item




#get all items
@router.get("/" , response_model = List[item.ItemOut])
def get_items(db: Session = Depends(get_db),
                   current_user: int = Depends(oauth2.get_current_user)):
    
    items = db.query(item_model.Item).order_by(item_model.Item.id).all()
    
    return items



    
#get item by id 
# Get Category by ID
@router.get("/{id}", response_model=item.ItemOut)
def get_item(id: int, db: Session = Depends(get_db),
                 current_user: int = Depends(oauth2.get_current_user)):
    
    item = db.query(item_model.Item).filter(item_model.Item.id == id).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"item with id {id} not found")
    
    return item




# Delete Item
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(id: int, db: Session = Depends(get_db),
                    current_user: int = Depends(oauth2.get_current_user)):
    
    item_query = db.query(item_model.Item).filter(item_model.Item.id == id)
    item = item_query.first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"item with id {id} not found")
    
    item_query.delete(synchronize_session=False)
    db.commit()
    
    return None
    
    
    
    
# Update Item
@router.put("/{id}", response_model=item.ItemOut)
def update_item(id: int, updated_item: item.ItemCreate , db: Session = Depends(get_db),
                    current_user: int = Depends(oauth2.get_current_user)):
    
    item_query = db.query(item_model.Item).filter(item_model.Item.id == id)
    item_obj = item_query.first()
    
    
    
    if not item_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"item with id {id} not found")
    
    # check if updated model_number already exists
    existing_category = db.query(category_model.Category).filter(category_model.Category.id == updated_item.category_id).first()
    
    if not existing_category:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND ,
                            detail = f"Category with id {item_obj.category_id} does not exist")
    
    item_query.update(updated_item.dict(), synchronize_session=False)
    db.commit()
    
    updated_item_obj = item_query.first()
    
    # Trigger low stock alert check when quantity is updated
    if updated_item.quantity != item_obj.quantity:
        try:
            # Get current user's alert threshold
            from app.models.user import User
            user = db.query(User).filter(User.id == current_user).first()
            if user:
                AlertService.check_and_create_alert(
                    db=db,
                    item_id=id,
                    user_id=current_user,
                    current_quantity=updated_item.quantity,
                    alert_threshold=user.alert_threshold
                )
        except Exception as e:
            print(f"Error checking low stock alert: {str(e)}")
    
    return updated_item_obj
    
    
    
    
    
    