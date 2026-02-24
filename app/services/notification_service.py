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
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Email Configuration (using Gmail - you can change this)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

logger.info(f"📧 Email Configuration Loaded:")
logger.info(f"   SMTP_SERVER: {SMTP_SERVER}")
logger.info(f"   SMTP_PORT: {SMTP_PORT}")
logger.info(f"   EMAIL_SENDER: {EMAIL_SENDER if EMAIL_SENDER else '❌ NOT SET'}")
logger.info(f"   EMAIL_PASSWORD: {'✅ SET' if EMAIL_PASSWORD else '❌ NOT SET'}")

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
            logger.info("=" * 60)
            logger.info("🔄 STARTING EMAIL SEND PROCESS")
            logger.info("=" * 60)
            
            # Re-check configuration at send time
            sender = os.getenv("EMAIL_SENDER", "")
            password = os.getenv("EMAIL_PASSWORD", "")
            
            # Check configuration
            if not sender:
                logger.error("❌ EMAIL_SENDER not configured in .env")
                logger.error("Please set EMAIL_SENDER in your .env file")
                return False
            
            if not password:
                logger.error("❌ EMAIL_PASSWORD not configured in .env")
                logger.error("Please set EMAIL_PASSWORD in your .env file")
                return False
            
            if not recipient_email:
                logger.error("❌ Recipient email is empty")
                return False
            
            logger.info(f"📧 Recipient: {recipient_email}")
            logger.info(f"📧 Subject: {subject}")
            logger.info(f"📧 From: {sender}")
            logger.info(f"📧 SMTP: {SMTP_SERVER}:{SMTP_PORT}")
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender
            message["To"] = recipient_email
            
            # Attach HTML body
            part = MIMEText(html_body, "html")
            message.attach(part)
            
            logger.info("📝 Message created successfully")
            
            # Send email
            logger.info("🔌 Connecting to SMTP server...")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                logger.info("✅ Connected to SMTP server")
                
                logger.info("🔐 Starting TLS...")
                server.starttls()
                logger.info("✅ TLS started")
                
                logger.info(f"🔑 Logging in with {sender}...")
                server.login(sender, password)
                logger.info("✅ Login successful")
                
                logger.info(f"📤 Sending email to {recipient_email}...")
                result = server.sendmail(sender, recipient_email, message.as_string())
                logger.info(f"✅ Email sent. Server response: {result}")
            
            logger.info(f"✅ Email sent successfully!")
            logger.info(f"   To: {recipient_email}")
            logger.info(f"   Item: {item_name}")
            logger.info(f"   Quantity: {current_quantity}")
            logger.info("=" * 60)
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error("=" * 60)
            logger.error(f"❌ SMTP Authentication Error")
            logger.error(f"Error: {str(e)}")
            logger.error("Possible causes:")
            logger.error("  1. EMAIL_SENDER is incorrect")
            logger.error("  2. EMAIL_PASSWORD is incorrect")
            logger.error("  3. Gmail App Password (not regular password) is required")
            logger.error("  4. 2FA might be enabled - use App Passwords instead")
            logger.error("=" * 60)
            return False
        except smtplib.SMTPException as e:
            logger.error("=" * 60)
            logger.error(f"❌ SMTP Error: {str(e)}")
            logger.error("=" * 60)
            return False
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ Failed to send email to {recipient_email}")
            logger.error(f"Exception: {type(e).__name__}")
            logger.error(f"Error: {str(e)}")
            logger.error("=" * 60)
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
            if not TWILIO_ACCOUNT_SID:
                logger.warning("⚠️ TWILIO_ACCOUNT_SID not configured. Skipping WhatsApp.")
                return False
            
            if not TWILIO_AUTH_TOKEN:
                logger.warning("⚠️ TWILIO_AUTH_TOKEN not configured. Skipping WhatsApp.")
                return False
            
            if not TWILIO_WHATSAPP_NUMBER:
                logger.warning("⚠️ TWILIO_WHATSAPP_NUMBER not configured. Skipping WhatsApp.")
                return False
            
            if not phone_number:
                logger.warning("⚠️ Phone number is empty. Skipping WhatsApp.")
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
            logger.info(f"📱 Sending WhatsApp to {phone_number}...")
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
        user_name: str = "Customer",
        additional_low_items: list = None
    ) -> str:
        """Create HTML email template for low stock alert"""
        
        # Create table for additional low stock items if provided
        additional_items_html = ""
        if additional_low_items:
            additional_items_html = """
            <h4 style="color: #333; margin-top: 20px; margin-bottom: 15px;">Other Low Stock Items:</h4>
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
            for item in additional_low_items:
                additional_items_html += f"""
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">{item.get('name', 'N/A')}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center; color: #e74c3c; font-weight: bold;">{item.get('quantity', 0)}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{item.get('threshold', 5)}</td>
                    </tr>
                """
            additional_items_html += """
                </tbody>
            </table>
            """
        
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
                    
                    {additional_items_html}
                    
                    <p style="color: #666; margin-top: 20px;">Please restock these items to avoid stockouts.</p>
                    
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
