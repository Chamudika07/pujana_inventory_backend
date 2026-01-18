from datetime import datetime
import uuid

def generate_bill_id(bill_type : str):
    date = datetime.now().strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"{bill_type.upper()}-{date}-{short_uuid}"
