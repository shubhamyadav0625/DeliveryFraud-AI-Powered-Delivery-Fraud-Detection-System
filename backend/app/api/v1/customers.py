from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.api.deps import require_role, get_current_user
from app.services.behavior_analytics import BehaviorAnalyticsService

router = APIRouter(prefix="/customers", tags=["Customer Behavior Intelligence"])

@router.get("/{customer_id}/history")
def get_customer_history_and_analytics(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    if current_user.role != UserRole.ADMIN.value and current_user.id != customer_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    profile = BehaviorAnalyticsService.get_customer_behavior_profile(db, customer_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return profile
