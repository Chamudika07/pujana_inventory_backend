"""
Service for generating unique model numbers and QR codes
"""
import os
import qrcode
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.item import Item
import logging

logger = logging.getLogger(__name__)


class ModelNumberService:
    """Service to handle model number and QR code generation"""
    
    QR_CODE_DIR = "static/qrs"
    
    @staticmethod
    def ensure_qr_directory():
        """Ensure QR code directory exists"""
        try:
            os.makedirs(ModelNumberService.QR_CODE_DIR, exist_ok=True)
            logger.info(f"✅ QR code directory ensured: {ModelNumberService.QR_CODE_DIR}")
        except Exception as e:
            logger.error(f"❌ Failed to create QR directory: {str(e)}")
            raise
    
    @staticmethod
    def generate_model_number(db: Session) -> str:
        """
        Generate a unique model number in format: MDL-<YEAR>-<5 digit incremental number>
        Example: MDL-2026-00001
        
        Args:
            db: Database session
            
        Returns:
            str: Generated model number
        """
        try:
            current_year = datetime.now().year
            
            # Get the highest sequence number for current year
            last_item = db.query(Item).filter(
                Item.model_number.like(f'MDL-{current_year}-%')
            ).order_by(Item.id.desc()).first()
            
            if last_item:
                # Extract sequence number from last model number
                parts = last_item.model_number.split('-')
                if len(parts) == 3:
                    try:
                        last_sequence = int(parts[2])
                        next_sequence = last_sequence + 1
                    except ValueError:
                        next_sequence = 1
                else:
                    next_sequence = 1
            else:
                next_sequence = 1
            
            # Format with leading zeros (5 digits)
            model_number = f"MDL-{current_year}-{next_sequence:05d}"
            
            logger.info(f"✅ Generated model number: {model_number}")
            return model_number
            
        except Exception as e:
            logger.error(f"❌ Error generating model number: {str(e)}")
            raise
    
    @staticmethod
    def generate_qr_code(model_number: str) -> str:
        """
        Generate QR code image for model number
        
        Args:
            model_number: Model number string
            
        Returns:
            str: Path to saved QR code image
        """
        try:
            # Ensure directory exists
            ModelNumberService.ensure_qr_directory()
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(model_number)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Generate file path
            qr_filename = f"{model_number}.png"
            qr_path = os.path.join(ModelNumberService.QR_CODE_DIR, qr_filename)
            
            # Save image
            img.save(qr_path)
            
            logger.info(f"✅ Generated QR code: {qr_path}")
            return qr_path
            
        except Exception as e:
            logger.error(f"❌ Error generating QR code for {model_number}: {str(e)}")
            raise
    
    @staticmethod
    def delete_qr_code(qr_code_path: str) -> bool:
        """
        Delete QR code image file
        
        Args:
            qr_code_path: Path to QR code file
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            if qr_code_path and os.path.exists(qr_code_path):
                os.remove(qr_code_path)
                logger.info(f"✅ Deleted QR code: {qr_code_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error deleting QR code {qr_code_path}: {str(e)}")
            return False
