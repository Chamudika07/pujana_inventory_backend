from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from app import oauth2
from app.database import get_db
from app.models.low_stock_alert import LowStockAlert
from app.models.user import User
from app.models.item import Item
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService
from app.schemas.low_stock_alert import (
    LowStockAlertOut,
    AlertStatsOut,
    UserPreferencesUpdate
)
from typing import List
from sqlalchemy import func
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
@router.patch("/{alert_id}/resolve", response_model=LowStockAlertOut)
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


# Delete alert
@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Delete an alert
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
    
    db.delete(alert)
    db.commit()


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
        for item_obj in items:
            if AlertService.check_and_create_alert(
                db=db,
                item_id=item_obj.id,
                user_id=current_user,
                current_quantity=item_obj.quantity,
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


# Test email endpoint
@router.post("/test-email", response_model=dict)
def test_email(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    """
    Test email notification - sends a test email to the user's notification email
    """
    try:
        user = db.query(User).filter(User.id == current_user).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.notification_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notification email not set. Please set it in your preferences."
            )
        
        logger.info(f"📧 Sending test email to {user.notification_email}")
        
        # Get low stock items for this user
        low_stock_items = db.query(Item).filter(Item.quantity < user.alert_threshold).all()
        
        # Create items HTML table
        items_html = ""
        if low_stock_items:
            items_html = """
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Item Name</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Current Qty</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Alert Level</th>
                    </tr>
                </thead>
                <tbody>
            """
            for item in low_stock_items:
                items_html += f"""
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">{item.name}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center; color: #e74c3c; font-weight: bold;">{item.quantity}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{user.alert_threshold}</td>
                    </tr>
                """
            items_html += """
                </tbody>
            </table>
            """
        else:
            items_html = """
            <div style="background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <p style="color: #155724; margin: 0;">✅ No items are currently low in stock. Great job!</p>
            </div>
            """
        
        # Create test email
        subject = "🧪 Test Email - Pujana Inventory System"
        user_name = user.email.split('@')[0] if user.email else "User"
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
                <div style="max-width: 600px; margin: 20px auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #28a745; border-bottom: 2px solid #28a745; padding-bottom: 10px;">✅ Test Email Successful!</h2>
                    
                    <p style="color: #333;">Hi <strong>{user_name}</strong>,</p>
                    
                    <p style="color: #666;">This is a test email to verify that email notifications are working correctly in your Pujana Inventory System.</p>
                    
                    <div style="background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; border-radius: 5px;">
                        <p style="margin: 5px 0;"><strong>Email Configuration:</strong> ✅ Working</p>
                        <p style="margin: 5px 0;"><strong>Sent to:</strong> {user.notification_email}</p>
                        <p style="margin: 5px 0;"><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <h4 style="color: #333; margin-top: 25px; margin-bottom: 15px;">📦 Items Low in Stock</h4>
                    {items_html}
                    
                    <p style="color: #666; margin-top: 20px;">You will receive alerts when items fall below your alert threshold of <strong>{user.alert_threshold} units</strong>.</p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px;">
                        Pujana Inventory Management System<br>
                        This is an automated test email
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Send test email
        logger.info(f"📧 Calling NotificationService.send_email...")
        success = NotificationService.send_email(
            recipient_email=user.notification_email,
            subject=subject,
            html_body=html_body,
            item_name="Test Email",
            current_quantity=0
        )
        
        if success:
            logger.info(f"✅ Test email sent successfully to {user.notification_email}")
            return {
                "message": "✅ Test email sent successfully!",
                "recipient": user.notification_email,
                "status": "success"
            }
        else:
            logger.error(f"❌ NotificationService returned False")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test email. Check the logs for details."
            )
    
    except HTTPException as he:
        logger.error(f"❌ HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in test_email: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending test email: {str(e)}"
        )
