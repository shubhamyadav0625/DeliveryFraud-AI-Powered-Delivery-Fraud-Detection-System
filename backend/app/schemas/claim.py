from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from app.models.claim import ClaimType, ClaimStatus

class ClaimItemCreate(BaseModel):
    order_item_id: str
    claim_type: ClaimType
    claimed_quantity: int = 1
    customer_reason: Optional[str] = None

class ClaimItemResponse(ClaimItemCreate):
    id: str
    claim_id: str

    model_config = ConfigDict(from_attributes=True)

class ClaimCreate(BaseModel):
    order_id: str
    claim_items: List[ClaimItemCreate]

class EvidenceFileResponse(BaseModel):
    id: str
    claim_id: str
    file_path: str
    file_type: str
    perceptual_hash: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RiskAssessmentResponse(BaseModel):
    id: str
    claim_id: str
    risk_score: int
    confidence_score: int = 80
    risk_level: str
    supporting_evidence: List[Any] = []
    contradicting_evidence: List[Any] = []
    missing_information: List[Any] = []
    primary_reasons: List[Any] = []
    counterfactuals: List[Any] = []
    evidence_graph: Any = {}
    factors: List[Any] = []
    pattern_alerts: List[Any] = []
    reliability_scores: Any = {}
    recommended_action: str
    assessed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClaimResponse(BaseModel):
    id: str
    order_id: str
    customer_id: str
    claim_number: str
    status: str
    created_at: datetime
    claim_items: List[ClaimItemResponse]
    evidence_files: List[EvidenceFileResponse] = []
    risk_assessment: Optional[RiskAssessmentResponse] = None

    model_config = ConfigDict(from_attributes=True)

class DecisionCreate(BaseModel):
    decision: str
    decision_notes: Optional[str] = None

class DecisionResponse(BaseModel):
    id: str
    claim_id: str
    analyst_id: Optional[str] = None
    decision: str
    decision_notes: Optional[str] = None
    decided_at: datetime

    model_config = ConfigDict(from_attributes=True)
