from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException , status 
from app import  oauth2
from app.database import get_db
from app.models.bill import Bill 
from app.models.user import User
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

router = APIRouter(
    prefix = '/print',
    tags = ['bill_print-PDF']
)


# -- print bill as PDF -- #
@router.get("/pdf/{bill_id}")
def print_bill_pdf( bill_id: str , db: Session = Depends(get_db) , current_user: User = Depends(oauth2.get_current_user)):
    #filter database
    bill = db.query(Bill).filter(Bill.bill_code == bill_id).first()

    
    if not bill:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail = f"Bill not found : {bill_id}")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "PUJANA ELECTRICAL")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, height - 70, f"Bill ID: {bill.bill_code}")
    pdf.drawString(50, height - 85, f"Bill Type: {bill.bill_type.value.upper()}")
    if bill.customer:
        pdf.drawString(50, height - 100, f"Customer: {bill.customer.full_name} ({bill.customer.phone_number})")
    elif bill.supplier:
        pdf.drawString(50, height - 100, f"Supplier: {bill.supplier.supplier_name} ({bill.supplier.phone_number})")

    # Table Header
    y = height - 145 if bill.customer or bill.supplier else height - 130
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, "Item")
    pdf.drawString(250, y, "Qty")
    pdf.drawString(300, y, "Price")
    pdf.drawString(370, y, "Total")

    pdf.line(50, y - 5, 450, y - 5)

    #  Items
    pdf.setFont("Helvetica", 10)
    y -= 25
    grand_total = 0

    for t in bill.inventory_transactions:
        total = t.quantity * t.price
        grand_total += total

        pdf.drawString(50, y, t.items.name)
        pdf.drawString(250, y, str(t.quantity))
        pdf.drawString(300, y, f"{t.price:.2f}")
        pdf.drawString(370, y, f"{total:.2f}")

        y -= 20

        if y < 100:
            pdf.showPage()
            y = height - 50

    # Financial summary
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(220, y - 20, "Subtotal:")
    pdf.drawString(370, y - 20, f"{bill.subtotal_amount:.2f}")
    pdf.drawString(220, y - 40, "Discount:")
    pdf.drawString(370, y - 40, f"{bill.discount_amount:.2f}")
    pdf.drawString(220, y - 60, "Tax:")
    pdf.drawString(370, y - 60, f"{bill.tax_amount:.2f}")
    pdf.drawString(220, y - 80, "Grand Total:")
    pdf.drawString(370, y - 80, f"{bill.total_amount:.2f}")
    pdf.drawString(220, y - 100, "Paid:")
    pdf.drawString(370, y - 100, f"{bill.paid_amount:.2f}")
    pdf.drawString(220, y - 120, "Due:")
    pdf.drawString(370, y - 120, f"{bill.due_amount:.2f}")
    pdf.drawString(220, y - 140, "Status:")
    pdf.drawString(370, y - 140, bill.payment_status.value.replace("_", " ").title())

    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={bill.bill_code}.pdf"
        }
    )
