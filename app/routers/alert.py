from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from app import oauth2
from app.database import get_db
from app.models.low_stock_alert import LowStockAlert
from app.models.user import User
from app.models.item import Item
from app.services.alert_service import AlertService
from app.schemas.low_stock_alert import (
    LowStockAlertOut,
    AlertStatsOut,
    UserPreferencesUpdate
)
from typing import List
from sqlalchemy import func

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"]
)


# Get all low stock alerts for current user
@router.get("/", response_model=List[LowStockAlertOut])
def get_user_alerts(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
    show_resolved: bool = False
):
    """
    Get all low stock alerts for the current user
    
    Query Parameters:
    - show_resolved: If True, show resolved alerts as well
    """
    query = db.query(LowStockAlert).filter(LowStockAlert.user_id == current_user)
    
    if not show_resolved:
        query = query.filter(LowStockAlert.is_resolved == False)
    
    alerts = query.order_by(LowStockAlert.created_at.desc()).all()
    return alerts


# Get alert statistics
@router.get("/stats", response_model=AlertStatsOut)
def get_alert_stats(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Get statistics about low stock alerts for current user
    """
    total_alerts = db.query(LowStockAlert).filter(
        LowStockAlert.user_id == current_user
    ).count()
    
    active_alerts = db.query(LowStockAlert).filter(
        LowStockAlert.user_id == current_user,
        LowStockAlert.is_resolved == False
    ).count()
    
    resolved_alerts = db.query(LowStockAlert).filter(
        LowStockAlert.user_id == current_user,
        LowStockAlert.is_resolved == True
    ).count()
    
    # Count items that are currently low stock
    low_stock_items = db.query(func.count(Item.id)).filter(
        Item.quantity < 5  # Default threshold
    ).scalar()
    
    return {
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "resolved_alerts": resolved_alerts,
        "low_stock_items": low_stock_items
    }


# Get specific alert by ID
@router.get("/{alert_id}", response_model=LowStockAlertOut)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Get a specific alert by ID
    """
    alert = db.query(LowStockAlert).filter(
        LowStockAlert.id == alert_id,
        LowStockAlert.user_id == current_user
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return alert


# Resolve an alert (mark as fixed)
@router.put("/{alert_id}/resolve", response_model=LowStockAlertOut)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Resolve an alert (mark item as restocked)
    """
    alert = db.query(LowStockAlert).filter(
        LowStockAlert.id == alert_id,
        LowStockAlert.user_id == current_user
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.is_resolved = True
    db.commit()
    db.refresh(alert)
    
    return alert


# Update user notification preferences
@router.put("/preferences/update", response_model=dict)
def update_preferences(
    preferences: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Update user notification preferences
    
    Fields that can be updated:
    - phone_number: User's phone number (for WhatsApp alerts)
    - notification_email: Email for receiving alerts
    - notification_enabled: Enable/disable notifications
    - alert_threshold: Quantity threshold for alerts (default: 5)
    """
    user = db.query(User).filter(User.id == current_user).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update only provided fields
    update_data = preferences.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Preferences updated successfully",
        "phone_number": user.phone_number,
        "notification_email": user.notification_email,
        "notification_enabled": user.notification_enabled,
        "alert_threshold": user.alert_threshold
    }


# Get user preferences
@router.get("/preferences/get", response_model=dict)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Get current user's notification preferences
    """
    user = db.query(User).filter(User.id == current_user).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "phone_number": user.phone_number,
        "notification_email": user.notification_email,
        "notification_enabled": user.notification_enabled,
        "alert_threshold": user.alert_threshold
    }


# Manual trigger low stock check (for admin/testing)
@router.post("/trigger-check", response_model=dict)
def trigger_low_stock_check(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Manually trigger low stock check for current user
    (Usually this runs automatically daily, but can be triggered manually)
    """
    try:
        user = db.query(User).filter(User.id == current_user).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get all items for this user
        items = db.query(Item).filter(Item.quantity < user.alert_threshold).all()
        
        count = 0
        for item in items:
            if AlertService.check_and_create_alert(
                db=db,
                item_id=item.id,
                user_id=current_user,
                current_quantity=item.quantity,
                alert_threshold=user.alert_threshold
            ):
                count += 1
        
        return {
            "message": "Low stock check completed",
            "items_checked": len(items),
            "alerts_sent": count
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering check: {str(e)}"
        )
