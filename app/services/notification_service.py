"""
Notification Service for Email and WhatsApp alerts
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from typing import List, Optional
import requests
import logging

logger = logging.getLogger(__name__)

# Email Configuration (using Gmail - you can change this)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Twilio Configuration (for WhatsApp)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "")


class NotificationService:
    """Service to handle email and WhatsApp notifications"""
    
    @staticmethod
    def send_email(
        recipient_email: str,
        subject: str,
        html_body: str,
        item_name: str = "",
        current_quantity: int = 0
    ) -> bool:
        """
        Send email notification for low stock alert
        
        Args:
            recipient_email: Email address of recipient
            subject: Email subject
            html_body: HTML content of email
            item_name: Name of the item (for logging)
            current_quantity: Current quantity of item
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not EMAIL_SENDER or not EMAIL_PASSWORD:
                logger.warning("Email credentials not configured")
                return False
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = EMAIL_SENDER
            message["To"] = recipient_email
            
            # Attach HTML body
            part = MIMEText(html_body, "html")
            message.attach(part)
            
            # Send email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, recipient_email, message.as_string())
            
            logger.info(f"✅ Email sent to {recipient_email} for item: {item_name} (qty: {current_quantity})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_whatsapp(
        phone_number: str,
        message_text: str,
        item_name: str = "",
        current_quantity: int = 0
    ) -> bool:
        """
        Send WhatsApp message notification using Twilio
        
        Args:
            phone_number: Phone number with country code (e.g., +919876543210)
            message_text: Message to send
            item_name: Name of the item (for logging)
            current_quantity: Current quantity of item
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_NUMBER:
                logger.warning("Twilio credentials not configured. Skipping WhatsApp.")
                return False
            
            # Format phone number with 'whatsapp:' prefix for Twilio
            whatsapp_number = f"whatsapp:{phone_number}"
            from_number = f"whatsapp:{TWILIO_WHATSAPP_NUMBER}"
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
            
            data = {
                "From": from_number,
                "To": whatsapp_number,
                "Body": message_text
            }
            
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            response = requests.post(url, data=data, auth=auth)
            
            if response.status_code == 201:
                logger.info(f"✅ WhatsApp sent to {phone_number} for item: {item_name} (qty: {current_quantity})")
                return True
            else:
                logger.error(f"❌ Twilio error: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp to {phone_number}: {str(e)}")
            return False
    
    @staticmethod
    def create_low_stock_email_template(
        item_name: str,
        current_quantity: int,
        threshold: int,
        user_name: str = "Customer"
    ) -> str:
        """Create HTML email template for low stock alert"""
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4;">
                <div style="max-width: 600px; margin: 20px auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">⚠️ Low Stock Alert</h2>
                    
                    <p style="color: #333;">Hi <strong>{user_name}</strong>,</p>
                    
                    <p style="color: #666;">The following item has low stock:</p>
                    
                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 5px;">
                        <p style="margin: 5px 0;"><strong>Item Name:</strong> {item_name}</p>
                        <p style="margin: 5px 0;"><strong>Current Quantity:</strong> <span style="color: #e74c3c; font-size: 18px; font-weight: bold;">{current_quantity}</span></p>
                        <p style="margin: 5px 0;"><strong>Alert Threshold:</strong> {threshold}</p>
                    </div>
                    
                    <p style="color: #666; margin-top: 20px;">Please restock this item to avoid stockouts.</p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px;">
                        This is an automated alert from your Inventory Management System.<br>
                        Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </body>
        </html>
        """
        return html
    
    @staticmethod
    def create_low_stock_sms_message(
        item_name: str,
        current_quantity: int,
        threshold: int,
        company_name: str = "Pujana"
    ) -> str:
        """Create SMS/WhatsApp message for low stock alert"""
        message = f"""
{company_name} Inventory Alert 🚨

Item: {item_name}
Current Stock: {current_quantity}
Alert Level: {threshold}

⚠️ Stock is low! Please restock soon.

Reply HELP for more info.
        """.strip()
        return message
