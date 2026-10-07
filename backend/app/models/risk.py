import uuid
import enum
import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class RecommendedAction(str, enum.Enum):
    APPROVE = "APPROVE"
    VERIFY = "VERIFY"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class DecisionType(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MORE_INFO_REQUESTED = "MORE_INFO_REQUESTED"

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), unique=True, nullable=False)
    risk_score = Column(Integer, nullable=False, default=0)
    confidence_score = Column(Integer, nullable=False, default=80)
    risk_level = Column(String(20), nullable=False, default=RiskLevel.LOW.value)
    
    supporting_evidence_json = Column(Text, nullable=False, default="[]")
    contradicting_evidence_json = Column(Text, nullable=False, default="[]")
    missing_information_json = Column(Text, nullable=False, default="[]")
    primary_reasons_json = Column(Text, nullable=False, default="[]")
    counterfactuals_json = Column(Text, nullable=False, default="[]")
    evidence_graph_json = Column(Text, nullable=False, default="{}")
    factors_json = Column(Text, nullable=False, default="[]")
    pattern_alerts_json = Column(Text, nullable=False, default="[]")
    reliability_scores_json = Column(Text, nullable=False, default="{}")
    
    recommended_action = Column(String(50), nullable=False, default=RecommendedAction.APPROVE.value)
    assessed_at = Column(DateTime, default=datetime.utcnow)

    @property
    def supporting_evidence(self):
        return json.loads(self.supporting_evidence_json or "[]")

    @supporting_evidence.setter
    def supporting_evidence(self, value):
        self.supporting_evidence_json = json.dumps(value or [])

    @property
    def contradicting_evidence(self):
        return json.loads(self.contradicting_evidence_json or "[]")

    @contradicting_evidence.setter
    def contradicting_evidence(self, value):
        self.contradicting_evidence_json = json.dumps(value or [])

    @property
    def missing_information(self):
        return json.loads(self.missing_information_json or "[]")

    @missing_information.setter
    def missing_information(self, value):
        self.missing_information_json = json.dumps(value or [])

    @property
    def primary_reasons(self):
        return json.loads(self.primary_reasons_json or "[]")

    @primary_reasons.setter
    def primary_reasons(self, value):
        self.primary_reasons_json = json.dumps(value or [])

    @property
    def counterfactuals(self):
        return json.loads(self.counterfactuals_json or "[]")

    @counterfactuals.setter
    def counterfactuals(self, value):
        self.counterfactuals_json = json.dumps(value or [])

    @property
    def evidence_graph(self):
        return json.loads(self.evidence_graph_json or "{}")

    @evidence_graph.setter
    def evidence_graph(self, value):
        self.evidence_graph_json = json.dumps(value or {})

    @property
    def factors(self):
        return json.loads(self.factors_json or "[]")

    @factors.setter
    def factors(self, value):
        self.factors_json = json.dumps(value or [])

    @property
    def pattern_alerts(self):
        return json.loads(self.pattern_alerts_json or "[]")

    @pattern_alerts.setter
    def pattern_alerts(self, value):
        self.pattern_alerts_json = json.dumps(value or [])

    @property
    def reliability_scores(self):
        return json.loads(self.reliability_scores_json or "{}")

    @reliability_scores.setter
    def reliability_scores(self, value):
        self.reliability_scores_json = json.dumps(value or {})

    claim = relationship("Claim", back_populates="risk_assessment")

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    analyst_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision = Column(String(50), nullable=False)
    decision_notes = Column(Text, nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow)

    claim = relationship("Claim", back_populates="decisions")
    analyst = relationship("User", back_populates="decisions")
