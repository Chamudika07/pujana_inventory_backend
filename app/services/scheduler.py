"""
Scheduler for automated low stock alert checks
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.low_stock_alert import LowStockAlert
from app.models.item import Item
from app.models.user import User
from app.services.alert_service import AlertService
import logging
import pytz

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler(daemon=True)


def daily_low_stock_check():
    """
    Daily job to check all low stock alerts and send reminders
    Runs every day at 9:00 AM
    """
    logger.info("🔍 Starting daily low stock check...")
    db = SessionLocal()
    try:
        # Get all unresolved alerts
        alerts = db.query(LowStockAlert).filter(
            LowStockAlert.is_resolved == False
        ).all()
        
        logger.info(f"Found {len(alerts)} unresolved alerts")
        
        for alert in alerts:
            try:
                # Check if item still has low stock
                item = db.query(Item).filter(Item.id == alert.item_id).first()
                user = db.query(User).filter(User.id == alert.user_id).first()
                
                if not item or not user:
                    continue
                
                # If quantity is still low and enough time has passed
                if item.quantity < user.alert_threshold:
                    if alert.next_alert_at and datetime.utcnow() >= alert.next_alert_at:
                        logger.info(f"Sending reminder for item {item.name} to user {user.email}")
                        
                        # Update alert timestamps
                        alert.last_sent_at = datetime.utcnow()
                        alert.next_alert_at = datetime.utcnow() + timedelta(hours=24)
                        db.commit()
                        
                        # Send notifications
                        AlertService.send_alert_notifications(
                            user=user,
                            item=item,
                            current_quantity=item.quantity,
                            alert_threshold=user.alert_threshold
                        )
                else:
                    # Item is now in stock, resolve the alert
                    alert.is_resolved = True
                    db.commit()
                    logger.info(f"Alert resolved for item {item.name} - stock replenished")
                    
            except Exception as e:
                logger.error(f"Error processing alert {alert.id}: {str(e)}")
                continue
        
        logger.info("✅ Daily low stock check completed")
        
    except Exception as e:
        logger.error(f"Error in daily_low_stock_check: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler
    This should be called when the FastAPI app starts
    """
    try:
        if not scheduler.running:
            # Schedule the daily check - runs every day at 9:00 AM
            scheduler.add_job(
                func=daily_low_stock_check,
                trigger=CronTrigger(hour=9, minute=0, timezone=pytz.UTC),
                id='daily_low_stock_check',
                name='Daily Low Stock Check',
                replace_existing=True
            )
            
            scheduler.start()
            logger.info("✅ Scheduler started successfully")
        else:
            logger.info("Scheduler is already running")
    
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")


def stop_scheduler():
    """
    Stop the background scheduler
    This should be called when the FastAPI app shuts down
    """
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("✅ Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")


def add_manual_check_job(check_time_hours: int = 1):
    """
    Add a one-time job to run low stock check after X hours
    
    Args:
        check_time_hours: Hours from now to run the check
    """
    try:
        run_time = datetime.utcnow() + timedelta(hours=check_time_hours)
        scheduler.add_job(
            func=daily_low_stock_check,
            trigger='date',
            run_date=run_time,
            id=f'manual_check_{run_time.timestamp()}',
            replace_existing=True
        )
        logger.info(f"Manual check scheduled for {run_time}")
    except Exception as e:
        logger.error(f"Error scheduling manual check: {str(e)}")
