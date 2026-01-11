from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException , status
from app.models import item as item_model
from app import  oauth2
from app.database import get_db
from app.schemas import item
from sqlalchemy import func


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
        
    new_item = item_model.Item(**item.dict())
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return new_item
    
    
    
    
    
    
    
    
    
    
    