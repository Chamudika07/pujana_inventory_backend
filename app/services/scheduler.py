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
from app.services.notification_service import NotificationService
import logging
import pytz

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler(daemon=True)


def daily_low_stock_check():
    """
    Daily job to check all low stock items and send email alerts
    Runs every day at 9:00 AM UTC
    """
    logger.info("=" * 60)
    logger.info("🔍 Starting daily low stock check...")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Get all users with notifications enabled
        users = db.query(User).filter(User.notification_enabled == True).all()
        
        logger.info(f"Found {len(users)} users with notifications enabled")
        
        total_alerts_sent = 0
        
        for user in users:
            try:
                # Get all low stock items for this user
                low_stock_items = db.query(Item).filter(
                    Item.quantity < user.alert_threshold
                ).all()
                
                if not low_stock_items:
                    logger.info(f"✅ No low stock items for user {user.email}")
                    continue
                
                # Check if user has notification email
                if not user.notification_email:
                    logger.warning(f"⚠️ User {user.email} has no notification email set")
                    continue
                
                logger.info(f"📧 Sending low stock alert to {user.email}")
                logger.info(f"   Found {len(low_stock_items)} low stock items")
                
                # Create email with all low stock items
                subject = f"⚠️ Low Stock Alert - {len(low_stock_items)} Item(s)"
                
                items_table_html = """
                <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Item Name</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Current Qty</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Alert Level</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Category</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for item in low_stock_items:
                    items_table_html += f"""
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>{item.name}</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: center; color: #e74c3c; font-weight: bold;">{item.quantity}</td>
                            <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{user.alert_threshold}</td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{item.category.name if item.category else 'N/A'}</td>
                        </tr>
                    """
                
                items_table_html += """
                    </tbody>
                </table>
                """
                
                user_name = user.email.split('@')[0]
                html_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
                        <div style="max-width: 600px; margin: 20px auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                            <h2 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">⚠️ Daily Low Stock Alert</h2>
                            
                            <p style="color: #333;">Hi <strong>{user_name}</strong>,</p>
                            
                            <p style="color: #666;">The following items have fallen below your alert threshold of <strong>{user.alert_threshold} units</strong>:</p>
                            
                            {items_table_html}
                            
                            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 5px;">
                                <p style="margin: 5px 0;"><i className="bi bi-exclamation-triangle"></i> <strong>Action Required:</strong> Please restock these items to avoid stockouts.</p>
                            </div>
                            
                            <p style="color: #666; margin-top: 20px;">
                                You can update your notification preferences or adjust the alert threshold in the Settings section of your Pujana Inventory System.
                            </p>
                            
                            <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px;">
                                Pujana Electrical Inventory Management System<br>
                                Automated Daily Alert<br>
                                Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
                            </p>
                        </div>
                    </body>
                </html>
                """
                
                # Send email
                success = NotificationService.send_email(
                    recipient_email=user.notification_email,
                    subject=subject,
                    html_body=html_body,
                    item_name=f"{len(low_stock_items)} items",
                    current_quantity=0
                )
                
                if success:
                    total_alerts_sent += 1
                    logger.info(f"✅ Alert sent to {user.email}")
                else:
                    logger.error(f"❌ Failed to send alert to {user.email}")
                
            except Exception as e:
                logger.error(f"Error processing user {user.email}: {str(e)}")
                continue
        
        logger.info("=" * 60)
        logger.info(f"✅ Daily low stock check completed")
        logger.info(f"   Total alerts sent: {total_alerts_sent}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error in daily_low_stock_check: {str(e)}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler
    This should be called when the FastAPI app starts
    """
    try:
        if not scheduler.running:
            # Schedule the daily check - runs every day at 9:00 AM UTC
            scheduler.add_job(
                func=daily_low_stock_check,
                trigger=CronTrigger(hour=9, minute=0, timezone=pytz.UTC),
                id='daily_low_stock_check',
                name='Daily Low Stock Check',
                replace_existing=True
            )
            
            scheduler.start()
            logger.info("✅ Scheduler started successfully")
            logger.info("📅 Daily low stock check scheduled for 9:00 AM UTC")
        else:
            logger.info("Scheduler is already running")
    
    except Exception as e:
        logger.error(f"❌ Error starting scheduler: {str(e)}", exc_info=True)


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
