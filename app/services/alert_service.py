"""
Service for managing low stock alerts
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.low_stock_alert import LowStockAlert
from app.models.item import Item
from app.models.user import User
from app.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service to handle low stock alert logic"""
    
    @staticmethod
    def check_and_create_alert(
        db: Session,
        item_id: int,
        user_id: int,
        current_quantity: int,
        alert_threshold: int
    ) -> bool:
        """
        Check if item quantity is low and create alert
        
        Args:
            db: Database session
            item_id: ID of the item
            user_id: ID of the user
            current_quantity: Current quantity of the item
            alert_threshold: Threshold for low stock
            
        Returns:
            bool: True if alert was created/sent, False otherwise
        """
        try:
            # Check if quantity is low
            if current_quantity >= alert_threshold:
                logger.info(f"Item {item_id} quantity is above threshold")
                return False
            
            # Get item and user details
            item = db.query(Item).filter(Item.id == item_id).first()
            user = db.query(User).filter(User.id == user_id).first()
            
            if not item or not user:
                logger.error(f"Item or User not found: item_id={item_id}, user_id={user_id}")
                return False
            
            # Check if notifications are enabled
            if not user.notification_enabled:
                logger.info(f"Notifications disabled for user {user_id}")
                return False
            
            # Check if alert already exists and was sent in last 24 hours
            existing_alert = db.query(LowStockAlert).filter(
                LowStockAlert.item_id == item_id,
                LowStockAlert.user_id == user_id,
                LowStockAlert.is_resolved == False
            ).first()
            
            if existing_alert:
                # If alert was sent in last 24 hours, don't send again
                if existing_alert.last_sent_at:
                    time_since_last_alert = datetime.utcnow() - existing_alert.last_sent_at
                    if time_since_last_alert < timedelta(hours=24):
                        logger.info(f"Alert already sent for item {item_id} in last 24 hours")
                        return False
                
                # Update existing alert
                existing_alert.quantity_at_alert = current_quantity
                existing_alert.last_sent_at = datetime.utcnow()
                existing_alert.next_alert_at = datetime.utcnow() + timedelta(hours=24)
                db.commit()
                alert = existing_alert
            else:
                # Create new alert
                alert = LowStockAlert(
                    item_id=item_id,
                    user_id=user_id,
                    quantity_at_alert=current_quantity,
                    alert_type="BOTH",
                    last_sent_at=datetime.utcnow(),
                    next_alert_at=datetime.utcnow() + timedelta(hours=24),
                    is_resolved=False
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
            
            # Send notifications
            AlertService.send_alert_notifications(
                user=user,
                item=item,
                current_quantity=current_quantity,
                alert_threshold=alert_threshold
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error in check_and_create_alert: {str(e)}")
            return False
    
    @staticmethod
    def send_alert_notifications(
        user: User,
        item: Item,
        current_quantity: int,
        alert_threshold: int
    ) -> None:
        """
        Send notifications (Email and/or WhatsApp) to user
        
        Args:
            user: User model instance
            item: Item model instance
            current_quantity: Current quantity of item
            alert_threshold: Alert threshold
        """
        try:
            notification_service = NotificationService()
            
            # Prepare email
            if user.notification_email:
                email_subject = f"⚠️ Low Stock Alert: {item.name}"
                email_body = NotificationService.create_low_stock_email_template(
                    item_name=item.name,
                    current_quantity=current_quantity,
                    threshold=alert_threshold,
                    user_name=user.email.split("@")[0]
                )
                notification_service.send_email(
                    recipient_email=user.notification_email,
                    subject=email_subject,
                    html_body=email_body,
                    item_name=item.name,
                    current_quantity=current_quantity
                )
            
            # Prepare WhatsApp
            if user.phone_number:
                sms_message = NotificationService.create_low_stock_sms_message(
                    item_name=item.name,
                    current_quantity=current_quantity,
                    threshold=alert_threshold
                )
                notification_service.send_whatsapp(
                    phone_number=user.phone_number,
                    message_text=sms_message,
                    item_name=item.name,
                    current_quantity=current_quantity
                )
            
            logger.info(f"Notifications sent for item {item.id} to user {user.id}")
            
        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")
    
    @staticmethod
    def resolve_alert(db: Session, item_id: int, user_id: int) -> bool:
        """
        Resolve an alert when item is restocked
        
        Args:
            db: Database session
            item_id: ID of the item
            user_id: ID of the user
            
        Returns:
            bool: True if alert was resolved
        """
        try:
            alert = db.query(LowStockAlert).filter(
                LowStockAlert.item_id == item_id,
                LowStockAlert.user_id == user_id,
                LowStockAlert.is_resolved == False
            ).first()
            
            if alert:
                alert.is_resolved = True
                db.commit()
                logger.info(f"Alert resolved for item {item_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resolving alert: {str(e)}")
            return False
    
    @staticmethod
    def get_all_low_stock_items(db: Session, user_id: int = None) -> list:
        """
        Get all items currently in low stock status
        
        Args:
            db: Database session
            user_id: Optional user ID filter
            
        Returns:
            list: List of low stock alert records
        """
        try:
            query = db.query(LowStockAlert).filter(LowStockAlert.is_resolved == False)
            
            if user_id:
                query = query.filter(LowStockAlert.user_id == user_id)
            
            alerts = query.all()
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting low stock items: {str(e)}")
            return []
