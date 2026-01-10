from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException , status
from app.models import category as category_model
from app import  oauth2
from app.database import get_db
from app.schemas import category

router = APIRouter(
    prefix="/categories",
    tags=['Categories']
)


# Create Category
@router.post("/", response_model=category.CategoryOut)
def create_category(category: category.CategoryCreate, db: Session = Depends(get_db),
                    current_user: int = Depends(oauth2.get_current_user)):
    
    # check if category name already exists
    exiting_category = db.query(category_model.Category).filter(category_model.Category.name == category.name).first()
    
    if exiting_category:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Category with name {category.name} already exists")
        
    # create category object
    new_category = category_model.Category(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return new_category