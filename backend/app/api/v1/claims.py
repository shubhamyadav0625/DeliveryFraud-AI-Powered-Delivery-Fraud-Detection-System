import os
import io
import random
import hashlib
from typing import List
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.order import Order, OrderItem, OrderStatus
from app.models.package import Package
from app.models.delivery import Delivery
from app.models.claim import Claim, ClaimItem, ClaimStatus
from app.models.evidence import EvidenceFile, EvidenceFileType
from app.models.risk import RiskAssessment
from app.models.audit import AuditLog
from app.schemas.claim import ClaimCreate, ClaimResponse, EvidenceFileResponse
from app.services.evidence_fusion import EvidenceFusionEngine
from app.services.behavior_analytics import BehaviorAnalyticsService
from app.services.image_forensics import ImageForensicsService
from app.api.deps import get_current_user

router = APIRouter(prefix="/claims", tags=["Claims & Fraud Verification"])

@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
def raise_claim(
    claim_in: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == claim_in.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if current_user.role != UserRole.ADMIN.value and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if not claim_in.claim_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Claim must target at least one item")

    claim_number = f"CLM-{random.randint(100000, 999999)}"

    claim = Claim(
        order_id=order.id,
        customer_id=current_user.id,
        claim_number=claim_number,
        status=ClaimStatus.SUBMITTED
    )
    db.add(claim)
    db.flush()

    for ci in claim_in.claim_items:
        order_item = db.query(OrderItem).filter(OrderItem.id == ci.order_item_id, OrderItem.order_id == order.id).first()
        if not order_item:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Order item {ci.order_item_id} not found in this order")
        
        claim_item = ClaimItem(
            claim_id=claim.id,
            order_item_id=order_item.id,
            claim_type=ci.claim_type.value,
            claimed_quantity=ci.claimed_quantity,
            customer_reason=ci.customer_reason
        )
        db.add(claim_item)

    db.flush()
    db.refresh(claim)
    order.status = OrderStatus.CLAIMED.value

    # Accurate time-window metrics EXCLUDING current claim
    metrics = BehaviorAnalyticsService.get_customer_claim_metrics(db, current_user.id, exclude_claim_id=claim.id)
    package = db.query(Package).filter(Package.order_id == order.id).first()
    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()

    delivery_agent_claims_count = 0
    if delivery and delivery.delivery_partner_id:
        delivery_agent_claims_count = db.query(Claim).join(Delivery, Claim.order_id == Delivery.order_id).filter(Delivery.delivery_partner_id == delivery.delivery_partner_id).count()

    customer = db.query(User).filter(User.id == current_user.id).first()
    account_age_days = (claim.created_at - customer.created_at).days if customer and customer.created_at else 30

    fusion_result = EvidenceFusionEngine.evaluate_claim(
        claim=claim,
        order=order,
        package=package,
        delivery=delivery,
        customer_past_claims_count=metrics["lifetime_claims"],
        recent_claims_in_window=metrics["claims_14d"],
        delivery_agent_claims_count=delivery_agent_claims_count,
        account_age_days=account_age_days
    )

    risk_assessment = RiskAssessment(
        claim_id=claim.id,
        risk_score=fusion_result["risk_score"],
        confidence_score=fusion_result["confidence_score"],
        risk_level=fusion_result["risk_level"].value,
        recommended_action=fusion_result["recommended_action"].value
    )
    risk_assessment.supporting_evidence = fusion_result["supporting_evidence"]
    risk_assessment.contradicting_evidence = fusion_result["contradicting_evidence"]
    risk_assessment.missing_information = fusion_result["missing_information"]
    risk_assessment.primary_reasons = fusion_result["primary_reasons"]
    risk_assessment.counterfactuals = fusion_result["counterfactuals"]
    risk_assessment.evidence_graph = fusion_result["evidence_graph"]
    risk_assessment.factors = fusion_result["factors"]
    risk_assessment.pattern_alerts = fusion_result["pattern_alerts"]
    risk_assessment.reliability_scores = fusion_result["reliability_scores"]
    db.add(risk_assessment)

    if fusion_result["recommended_action"].value == "APPROVE":
        claim.status = ClaimStatus.APPROVED.value
    elif fusion_result["recommended_action"].value == "VERIFY":
        claim.status = ClaimStatus.VERIFY_REQUESTED.value
    else:
        claim.status = ClaimStatus.INVESTIGATION_REQUIRED.value

    audit = AuditLog(
        claim_id=claim.id,
        user_id=current_user.id,
        action="CLAIM_SUBMITTED_AND_ASSESSED",
        metadata_dict={
            "risk_score": fusion_result["risk_score"],
            "recommended_action": fusion_result["recommended_action"].value
        }
    )
    db.add(audit)

    db.commit()
    db.refresh(claim)
    return claim

@router.post("/{claim_id}/evidence", response_model=EvidenceFileResponse)
def upload_claim_evidence(
    claim_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    if current_user.role != UserRole.ADMIN.value and claim.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    content = file.file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds maximum 10MB limit")

    is_image = "image" in (file.content_type or "")
    perceptual_h = "0000000000000000"
    ela_score = 0.0

    if is_image:
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()  # Validate non-corrupt image decoding
            img = Image.open(io.BytesIO(content))
            perceptual_h = ImageForensicsService.compute_dhash(img)
            forensics = ImageForensicsService.analyze_image_manipulation(content)
            ela_score = forensics.get("tamper_score", 0.0)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image is corrupt or unreadable")

    file_sha256 = hashlib.sha256(content).hexdigest()
    file_extension = os.path.splitext(file.filename)[1] or (".png" if is_image else ".pdf")
    filename = f"{claim_id}_{file_sha256[:10]}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    evidence = EvidenceFile(
        claim_id=claim.id,
        file_path=file_path,
        file_type=EvidenceFileType.IMAGE.value if is_image else EvidenceFileType.DOCUMENT.value,
        perceptual_hash=perceptual_h
    )
    db.add(evidence)

    order = db.query(Order).filter(Order.id == claim.order_id).first()
    package = db.query(Package).filter(Package.order_id == order.id).first() if order else None
    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first() if order else None
    metrics = BehaviorAnalyticsService.get_customer_claim_metrics(db, current_user.id, exclude_claim_id=claim.id)

    # Check for duplicate perceptual hashes across past evidence
    duplicate_score = 0.0
    existing_evidence = db.query(EvidenceFile).filter(EvidenceFile.id != evidence.id).all()
    for ev in existing_evidence:
        if ev.perceptual_hash and ev.perceptual_hash != "0000000000000000":
            dist = ImageForensicsService.calculate_hamming_distance(perceptual_h, ev.perceptual_hash)
            if dist <= 5:
                duplicate_score = 1.0
                break

    if claim.risk_assessment and order:
        fusion_result = EvidenceFusionEngine.evaluate_claim(
            claim=claim,
            order=order,
            package=package,
            delivery=delivery,
            customer_past_claims_count=metrics["lifetime_claims"],
            recent_claims_in_window=metrics["claims_14d"],
            ela_tamper_score=ela_score,
            duplicate_image_score=duplicate_score
        )
        claim.risk_assessment.risk_score = fusion_result["risk_score"]
        claim.risk_assessment.confidence_score = fusion_result["confidence_score"]
        claim.risk_assessment.risk_level = fusion_result["risk_level"].value
        claim.risk_assessment.recommended_action = fusion_result["recommended_action"].value
        claim.risk_assessment.supporting_evidence = fusion_result["supporting_evidence"]
        claim.risk_assessment.contradicting_evidence = fusion_result["contradicting_evidence"]
        claim.risk_assessment.missing_information = fusion_result["missing_information"]
        claim.risk_assessment.primary_reasons = fusion_result["primary_reasons"]
        claim.risk_assessment.counterfactuals = fusion_result["counterfactuals"]
        claim.risk_assessment.evidence_graph = fusion_result["evidence_graph"]
        claim.risk_assessment.factors = fusion_result["factors"]
        claim.risk_assessment.pattern_alerts = fusion_result["pattern_alerts"]
        claim.risk_assessment.reliability_scores = fusion_result["reliability_scores"]

    db.commit()
    db.refresh(evidence)
    return evidence

@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    if current_user.role != UserRole.ADMIN.value and claim.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return claim

@router.get("", response_model=List[ClaimResponse])
def list_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.ADMIN.value:
        return db.query(Claim).order_by(Claim.created_at.desc()).all()
    return db.query(Claim).filter(Claim.customer_id == current_user.id).order_by(Claim.created_at.desc()).all()
