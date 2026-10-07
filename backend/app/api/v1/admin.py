from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.claim import Claim, ClaimStatus
from app.models.risk import Decision, RiskAssessment
from app.models.audit import AuditLog
from app.schemas.claim import DecisionCreate, DecisionResponse, ClaimResponse
from app.api.deps import require_role

router = APIRouter(prefix="/admin", tags=["Fraud Analyst & Admin Dashboard"])

@router.get("/claims", response_model=List[ClaimResponse])
def get_analyst_claim_queue(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    query = db.query(Claim).outerjoin(RiskAssessment, Claim.id == RiskAssessment.claim_id)
    if status_filter and status_filter.strip() != "":
        query = query.filter(Claim.status == status_filter.strip())
    
    # Sort by Risk Score Descending first, then created_at desc
    claims = query.order_by(RiskAssessment.risk_score.desc().nullslast(), Claim.created_at.desc()).all()
    return claims

@router.post("/claims/{claim_id}/decision", response_model=DecisionResponse)
def record_analyst_decision(
    claim_id: str,
    decision_in: DecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    decision = Decision(
        claim_id=claim.id,
        analyst_id=current_user.id,
        decision=decision_in.decision,
        decision_notes=decision_in.decision_notes
    )
    db.add(decision)

    if decision_in.decision == "APPROVED":
        claim.status = ClaimStatus.APPROVED.value
    elif decision_in.decision == "REJECTED":
        claim.status = ClaimStatus.REJECTED.value
    elif decision_in.decision in ["MORE_INFO_REQUESTED", "REQUEST_MORE_EVIDENCE"]:
        claim.status = ClaimStatus.VERIFY_REQUESTED.value
    elif decision_in.decision == "ESCALATE":
        claim.status = ClaimStatus.INVESTIGATION_REQUIRED.value

    current_risk_score = claim.risk_assessment.risk_score if claim.risk_assessment else 0

    audit = AuditLog(
        claim_id=claim.id,
        user_id=current_user.id,
        action="ANALYST_DECISION_RECORDED",
        metadata_dict={
            "decision": decision_in.decision,
            "analyst_id": current_user.id,
            "notes": decision_in.decision_notes,
            "risk_score_at_decision": current_risk_score
        }
    )
    db.add(audit)

    db.commit()
    db.refresh(decision)
    return decision

@router.get("/analytics")
def get_system_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
) -> Dict[str, Any]:
    total_claims = db.query(Claim).count()
    approved_claims = db.query(Claim).filter(Claim.status == ClaimStatus.APPROVED).count()
    rejected_claims = db.query(Claim).filter(Claim.status == ClaimStatus.REJECTED).count()
    verify_claims = db.query(Claim).filter(Claim.status == ClaimStatus.VERIFY_REQUESTED).count()
    manual_review_claims = db.query(Claim).filter(Claim.status == ClaimStatus.MANUAL_REVIEW).count()

    assessments = db.query(RiskAssessment).all()
    avg_risk_score = (sum(a.risk_score for a in assessments) / len(assessments)) if assessments else 0.0

    return {
        "total_claims": total_claims,
        "approved_claims": approved_claims,
        "rejected_claims": rejected_claims,
        "verify_requested_claims": verify_claims,
        "manual_review_claims": manual_review_claims,
        "average_risk_score": round(avg_risk_score, 2),
        "high_risk_claim_ratio": round((manual_review_claims / total_claims), 2) if total_claims > 0 else 0.0
    }
