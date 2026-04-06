"""
Service for generating unique model numbers and QR codes
"""
import json
import os
import re
import qrcode
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.item import Item
import logging

logger = logging.getLogger(__name__)


class ModelNumberService:
    """Service to handle model number and QR code generation"""
    
    QR_CODE_DIR = "static/qrs"
    MODEL_NUMBER_PATTERN = re.compile(r"^MDL-\d{4}-\d{5}$")
    
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
            qr_payload = ModelNumberService.build_qr_payload(model_number)
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_payload)
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
    def build_qr_payload(model_number: str) -> str:
        """Build a standardized QR payload for item scans."""
        return json.dumps(
            {"type": "item", "model_number": model_number},
            separators=(",", ":"),
        )

    @staticmethod
    def is_valid_model_number(model_number: str) -> bool:
        """Validate model number format."""
        return bool(ModelNumberService.MODEL_NUMBER_PATTERN.fullmatch(model_number.strip()))

    @staticmethod
    def resolve_scanned_value(scanned_value: str) -> tuple[str, str]:
        """
        Resolve a scanned QR or barcode value into a model number.

        Supports legacy QR codes containing only the model number and
        structured JSON payloads for future extensibility.
        """
        normalized_value = scanned_value.strip()
        if not normalized_value:
            raise ValueError("Scanned value cannot be empty")

        if ModelNumberService.is_valid_model_number(normalized_value):
            return normalized_value, "plain_model_number"

        try:
            payload = json.loads(normalized_value)
        except json.JSONDecodeError as exc:
            raise ValueError("Unsupported QR code format") from exc

        if not isinstance(payload, dict):
            raise ValueError("QR payload must be a JSON object")

        qr_type = str(payload.get("type", "")).strip().lower()
        model_number = str(payload.get("model_number", "")).strip()

        if qr_type != "item":
            raise ValueError("QR code is not an item code")

        if not ModelNumberService.is_valid_model_number(model_number):
            raise ValueError("QR code contains an invalid model number")

        return model_number, "item_json"
    
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
