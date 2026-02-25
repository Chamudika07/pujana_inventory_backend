from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import item as item_model
from app.models import category as category_model
from app.models.user import User
from app import oauth2
from app.database import get_db
from app.schemas import item
from app.services.alert_service import AlertService
from app.services.model_number_service import ModelNumberService
from sqlalchemy import func
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/items",
    tags=['items']
)


# Create Item with auto-generated model number and QR code
@router.post("/", response_model=item.ItemOut)
def create_item(
    item_data: item.ItemCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Create a new item with auto-generated model number and QR code
    """
    try:
        # Validate category exists
        existing_category = db.query(category_model.Category).filter(
            category_model.Category.id == item_data.category_id
        ).first()
        
        if not existing_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {item_data.category_id} does not exist"
            )
        
        # Generate unique model number
        logger.info("📝 Generating unique model number...")
        model_number = ModelNumberService.generate_model_number(db)
        
        # Generate QR code
        logger.info(f"🔲 Generating QR code for {model_number}...")
        qr_code_path = ModelNumberService.generate_qr_code(model_number)
        
        # Create item
        new_item = item_model.Item(
            **item_data.dict(),
            model_number=model_number,
            qr_code_path=qr_code_path
        )
        
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        logger.info(f"✅ Item created: {new_item.id} with model number {model_number}")
        
        # Check for low stock alert
        try:
            user = db.query(User).filter(User.id == current_user).first()
            if user:
                AlertService.check_and_create_alert(
                    db=db,
                    item_id=new_item.id,
                    user_id=current_user,
                    current_quantity=new_item.quantity,
                    alert_threshold=user.alert_threshold
                )
                logger.info(f"✅ Alert check completed for new item {new_item.id}")
        except Exception as e:
            logger.error(f"Error checking low stock alert for new item: {str(e)}")
        
        return new_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating item: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating item: {str(e)}"
        )


# Get all items
@router.get("/", response_model=List[item.ItemOut])
def get_items(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """Get all items"""
    items = db.query(item_model.Item).order_by(item_model.Item.id).all()
    return items


# Get item by ID
@router.get("/{id}", response_model=item.ItemOut)
def get_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """Get item by ID"""
    item_obj = db.query(item_model.Item).filter(item_model.Item.id == id).first()
    
    if not item_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {id} not found"
        )
    
    return item_obj


# Get item by model number
@router.get("/by-model/{model_number}", response_model=item.ItemOut)
def get_item_by_model(
    model_number: str,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Get item by model number
    Example: /items/by-model/MDL-2026-00001
    """
    item_obj = db.query(item_model.Item).filter(
        item_model.Item.model_number == model_number
    ).first()
    
    if not item_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with model number {model_number} not found"
        )
    
    logger.info(f"✅ Retrieved item: {item_obj.model_number}")
    return item_obj


# Update item
@router.put("/{id}", response_model=item.ItemOut)
def update_item(
    id: int,
    updated_item: item.ItemUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """Update item (model_number cannot be changed)"""
    item_query = db.query(item_model.Item).filter(item_model.Item.id == id)
    item_obj = item_query.first()
    
    if not item_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {id} not found"
        )
    
    # Validate category if provided
    if updated_item.category_id:
        existing_category = db.query(category_model.Category).filter(
            category_model.Category.id == updated_item.category_id
        ).first()
        
        if not existing_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {updated_item.category_id} does not exist"
            )
    
    # Update only provided fields
    update_data = updated_item.dict(exclude_unset=True)
    item_query.update(update_data, synchronize_session=False)
    db.commit()
    
    updated_item_obj = item_query.first()
    
    # Check for low stock alert
    try:
        user = db.query(User).filter(User.id == current_user).first()
        if user:
            AlertService.check_and_create_alert(
                db=db,
                item_id=id,
                user_id=current_user,
                current_quantity=updated_item_obj.quantity,
                alert_threshold=user.alert_threshold
            )
            logger.info(f"✅ Alert check completed for updated item {id}")
    except Exception as e:
        logger.error(f"Error checking low stock alert: {str(e)}")
    
    logger.info(f"✅ Item updated: {id}")
    return updated_item_obj


# Delete item
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """Delete item and associated QR code"""
    item_query = db.query(item_model.Item).filter(item_model.Item.id == id)
    item_obj = item_query.first()
    
    if not item_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {id} not found"
        )
    
    # Delete QR code file
    if item_obj.qr_code_path:
        try:
            ModelNumberService.delete_qr_code(item_obj.qr_code_path)
        except Exception as e:
            logger.error(f"Error deleting QR code: {str(e)}")
    
    item_query.delete(synchronize_session=False)
    db.commit()
    
    logger.info(f"✅ Item deleted: {id}")
    return None





