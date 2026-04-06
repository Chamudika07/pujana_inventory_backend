from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import oauth2
from app.database import get_db
from app.models.user import User
from app.schemas.payment import DueDashboardSummaryResponse
from app.services.payment_service import PaymentService


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/dues-summary", response_model=DueDashboardSummaryResponse)
def dues_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_user),
):
    return PaymentService.dashboard_due_summary(db)
