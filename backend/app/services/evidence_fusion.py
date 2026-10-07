from typing import List, Dict, Any
from datetime import datetime, timezone
from app.models.order import Order
from app.models.package import Package
from app.models.delivery import Delivery
from app.models.claim import Claim, ClaimType
from app.models.risk import RiskLevel, RecommendedAction
from app.services.ml_fraud_model import MLFraudModelService

# Configurable Evidence Reliability Scores
RELIABILITY_SCORES = {
    "WAREHOUSE_SCAN": 0.95,
    "PACKAGE_SCALE_WEIGHT": 0.95,
    "DELIVERY_OTP": 0.90,
    "DELIVERY_LOCATION": 0.90,
    "CUSTOMER_PHOTO": 0.60,
    "CUSTOMER_TEXT": 0.45,
    "IMAGE_FORENSICS_ELA": 0.85,
    "BEHAVIORAL_HISTORY": 0.80,
}

# Configurable Risk Thresholds
RISK_THRESHOLDS = {
    "LOW_MAX": 29,
    "MEDIUM_MAX": 59,
    "HIGH_MAX": 79,
}

class EvidenceFusionEngine:

    @staticmethod
    def evaluate_claim(
        claim: Claim, 
        order: Order, 
        package: Package | None, 
        delivery: Delivery | None,
        customer_past_claims_count: int = 0,
        recent_claims_in_window: int = 0,
        delivery_agent_claims_count: int = 0,
        ela_tamper_score: float = 0.0,
        duplicate_image_score: float = 0.0,
        account_age_days: int = 30
    ) -> Dict[str, Any]:

        supporting_evidence: List[Dict[str, Any]] = []
        contradicting_evidence: List[Dict[str, Any]] = []
        missing_information: List[Dict[str, Any]] = []
        primary_reasons: List[str] = []
        factors: List[Dict[str, Any]] = []
        pattern_alerts: List[Dict[str, Any]] = []

        # 1. Extract Feature Vector & Run Real ML Model
        weight_delta_pct = 0.0
        if package and package.total_expected_weight_grams > 0:
            weight_delta_pct = abs(package.measured_weight_grams - package.total_expected_weight_grams) / package.total_expected_weight_grams * 100.0

        claim_type_code = 0
        if claim.claim_items:
            ct = claim.claim_items[0].claim_type
            if ct == ClaimType.WRONG_ITEM.value:
                claim_type_code = 1
            elif ct == ClaimType.DAMAGED_ITEM.value:
                claim_type_code = 2
            elif ct == ClaimType.EMPTY_PACKAGE.value:
                claim_type_code = 3

        ml_features = {
            "customer_claim_count": customer_past_claims_count,
            "customer_recent_claim_count_14d": recent_claims_in_window,
            "customer_account_age_days": account_age_days,
            "order_amount": order.total_amount if order else 100.0,
            "weight_delta_pct": weight_delta_pct,
            "otp_verified": delivery.otp_verified if delivery else False,
            "image_tamper_score": ela_tamper_score,
            "duplicate_image_score": duplicate_image_score,
            "delivery_agent_claims_count": delivery_agent_claims_count,
            "delivery_to_claim_hours": 2.5,
            "claim_type_code": claim_type_code
        }

        ml_prob_pct, ml_risk_score, ml_metrics = MLFraudModelService.predict_fraud_probability(ml_features)

        # 2. Rule-Based & Reliability-Weighted Adjustments
        rule_adjustment = 0.0

        # --- DELIVERED / HANDOVER EVIDENCE ---
        if delivery:
            if delivery.otp_verified:
                eff_impact = -15.0 * RELIABILITY_SCORES["DELIVERY_OTP"]
                rule_adjustment += eff_impact
                factors.append({
                    "code": "DELIVERY_OTP_VERIFIED",
                    "label": "Delivery OTP Verified at Doorstep",
                    "impact": round(eff_impact, 1),
                    "reliability": RELIABILITY_SCORES["DELIVERY_OTP"]
                })
                contradicting_evidence.append({
                    "code": "DELIVERY_OTP_VERIFIED",
                    "label": "Verified Handover OTP",
                    "description": f"Customer provided valid OTP ({delivery.otp_code}) to delivery partner.",
                    "reliability": RELIABILITY_SCORES["DELIVERY_OTP"]
                })
            else:
                eff_impact = 20.0 * RELIABILITY_SCORES["DELIVERY_OTP"]
                rule_adjustment += eff_impact
                factors.append({
                    "code": "DELIVERY_OTP_UNVERIFIED",
                    "label": "Delivery Handover OTP Unverified",
                    "impact": round(eff_impact, 1),
                    "reliability": RELIABILITY_SCORES["DELIVERY_OTP"]
                })
                primary_reasons.append("Delivery OTP handover was not verified at time of dropoff.")
                supporting_evidence.append({
                    "code": "DELIVERY_OTP_UNVERIFIED",
                    "label": "Unverified Delivery Handover",
                    "description": "Delivery dropoff completed without single-use OTP confirmation.",
                    "reliability": RELIABILITY_SCORES["DELIVERY_OTP"]
                })
        else:
            missing_information.append({
                "code": "MISSING_DELIVERY_RECORD",
                "label": "Missing Delivery Log",
                "description": "No formal delivery handover record found for this order."
            })

        # --- WAREHOUSE EXIT SCALE EVIDENCE ---
        if package:
            expected_weight = package.total_expected_weight_grams
            measured_weight = package.measured_weight_grams
            weight_delta = measured_weight - expected_weight
            tolerance = 20.0

            if abs(weight_delta) <= tolerance:
                eff_impact = -15.0 * RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"]
                rule_adjustment += eff_impact
                factors.append({
                    "code": "PACKAGE_WEIGHT_MATCHED",
                    "label": "Exit Package Scale Weight Consistent",
                    "impact": round(eff_impact, 1),
                    "reliability": RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"]
                })
                contradicting_evidence.append({
                    "code": "PACKAGE_WEIGHT_CONSISTENT",
                    "label": "Exit Scale Weight Match",
                    "description": f"Warehouse exit scale measured {measured_weight}g (Expected: {expected_weight}g).",
                    "reliability": RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"]
                })
            elif weight_delta < -tolerance:
                impact_base = 30.0 if weight_delta_pct > 25.0 else 20.0
                eff_impact = impact_base * RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"]
                rule_adjustment += eff_impact
                factors.append({
                    "code": "PACKAGE_UNDERWEIGHT",
                    "label": f"Package Underweight by {abs(weight_delta):.1f}g ({weight_delta_pct:.1f}%)",
                    "impact": round(eff_impact, 1),
                    "reliability": RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"]
                })
                primary_reasons.append(f"Warehouse exit scale weight ({measured_weight}g) is under expected weight ({expected_weight}g).")
                supporting_evidence.append({
                    "code": "PACKAGE_UNDERWEIGHT",
                    "label": "Warehouse Exit Underweight",
                    "description": f"Package weighed {measured_weight}g at exit scale vs expected {expected_weight}g.",
                    "reliability": RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"]
                })
        else:
            missing_information.append({
                "code": "MISSING_PACKAGE_SCALE_RECORD",
                "label": "Missing Exit Scale Log",
                "description": "No warehouse exit scale weight was recorded for this shipment."
            })

        # --- BEHAVIORAL & HISTORY SIGNALS ---
        if customer_past_claims_count == 0:
            missing_information.append({
                "code": "INSUFFICIENT_HISTORY",
                "label": "First-Time Customer Claim",
                "description": "Customer account has no historical claims record (Insufficient History)."
            })
        elif customer_past_claims_count > 3:
            eff_impact = 15.0 * RELIABILITY_SCORES["BEHAVIORAL_HISTORY"]
            rule_adjustment += eff_impact
            factors.append({
                "code": "REPEATED_CLAIM_HISTORY",
                "label": f"Customer Claim Frequency ({customer_past_claims_count} previous claims)",
                "impact": round(eff_impact, 1),
                "reliability": RELIABILITY_SCORES["BEHAVIORAL_HISTORY"]
            })
            primary_reasons.append(f"Customer account has submitted {customer_past_claims_count} previous claims.")

        if recent_claims_in_window >= 3:
            eff_impact = 20.0 * RELIABILITY_SCORES["BEHAVIORAL_HISTORY"]
            rule_adjustment += eff_impact
            factors.append({
                "code": "UNUSUAL_CLAIM_VELOCITY",
                "label": "Unusual Claim Velocity Spike (14 days)",
                "impact": round(eff_impact, 1),
                "reliability": RELIABILITY_SCORES["BEHAVIORAL_HISTORY"]
            })
            primary_reasons.append(f"Unusual claim velocity detected: {recent_claims_in_window} claims raised in last 14 days.")
            pattern_alerts.append({
                "type": "VELOCITY_SPIKE",
                "severity": "HIGH",
                "message": f"Suspicious claim velocity spike ({recent_claims_in_window} claims in 14 days)."
            })

        if delivery_agent_claims_count >= 3:
            pattern_alerts.append({
                "type": "POTENTIAL_COORDINATED_PATTERN",
                "severity": "HIGH",
                "message": f"Potential agent pattern detected: {delivery_agent_claims_count} claims linked to Delivery Agent."
            })
            eff_impact = 15.0 * 0.85
            rule_adjustment += eff_impact
            factors.append({
                "code": "COORDINATED_AGENT_PATTERN",
                "label": "Potential Coordinated Agent Pattern",
                "impact": round(eff_impact, 1),
                "reliability": 0.85
            })

        # --- IMAGE FORENSICS SIGNALS ---
        if ela_tamper_score > 0.5:
            eff_impact = 20.0 * RELIABILITY_SCORES["IMAGE_FORENSICS_ELA"]
            rule_adjustment += eff_impact
            factors.append({
                "code": "IMAGE_FORENSICS_TAMPERED",
                "label": f"Image Editing Forensics Signal ({int(ela_tamper_score * 100)}%)",
                "impact": round(eff_impact, 1),
                "reliability": RELIABILITY_SCORES["IMAGE_FORENSICS_ELA"]
            })
            primary_reasons.append("Digital image forensics detected potential ELA tampering in uploaded photo.")
            supporting_evidence.append({
                "code": "ELA_IMAGE_TAMPERING",
                "label": "Digital Image Forensics Flag",
                "description": f"High error level compression variance detected ({int(ela_tamper_score * 100)}% anomaly).",
                "reliability": RELIABILITY_SCORES["IMAGE_FORENSICS_ELA"]
            })

        if duplicate_image_score > 0.8:
            eff_impact = 25.0 * 0.95
            rule_adjustment += eff_impact
            factors.append({
                "code": "DUPLICATE_IMAGE_DETECTED",
                "label": "Duplicate / Visually Similar Image Detected",
                "impact": round(eff_impact, 1),
                "reliability": 0.95
            })
            primary_reasons.append("Perceptual image hashing detected duplicate image used in previous claims.")

        # 3. Compute Hybrid Score (60% ML + 40% Rules & Adjustments)
        raw_combined = (ml_prob_pct * 0.50) + 20.0 + rule_adjustment
        final_score = int(max(0.0, min(100.0, raw_combined)))

        # Evidence Confidence Calculation
        confidence_inputs = 0
        confidence_points = 0.0
        if package:
            confidence_inputs += 1
            confidence_points += RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"] * 100
        if delivery:
            confidence_inputs += 1
            confidence_points += RELIABILITY_SCORES["DELIVERY_OTP"] * 100
        if claim.evidence_files:
            confidence_inputs += 1
            confidence_points += RELIABILITY_SCORES["CUSTOMER_PHOTO"] * 100
        if customer_past_claims_count > 0:
            confidence_inputs += 1
            confidence_points += RELIABILITY_SCORES["BEHAVIORAL_HISTORY"] * 100

        confidence_score = int(round(confidence_points / max(1, confidence_inputs))) if confidence_inputs > 0 else 40

        # Classification Risk Levels
        if final_score <= RISK_THRESHOLDS["LOW_MAX"]:
            risk_level = RiskLevel.LOW
            recommended_action = RecommendedAction.APPROVE
        elif final_score <= RISK_THRESHOLDS["MEDIUM_MAX"]:
            risk_level = RiskLevel.MEDIUM
            recommended_action = RecommendedAction.VERIFY
        elif final_score <= RISK_THRESHOLDS["HIGH_MAX"]:
            risk_level = RiskLevel.HIGH
            recommended_action = RecommendedAction.MANUAL_REVIEW
        else:
            risk_level = RiskLevel.CRITICAL
            recommended_action = RecommendedAction.MANUAL_REVIEW

        # 4. Dynamic Counterfactual Recalculation
        counterfactuals: List[Dict[str, Any]] = []
        if final_score >= 30:
            # Counterfactual 1: What if Doorstep OTP was verified?
            if not (delivery and delivery.otp_verified):
                simulated_adj = rule_adjustment - (15.0 * RELIABILITY_SCORES["DELIVERY_OTP"])
                simulated_score = int(max(0.0, min(100.0, (ml_prob_pct * 0.50) + 20.0 + simulated_adj)))
                diff = final_score - simulated_score
                if diff > 0:
                    counterfactuals.append({
                        "signal": "Verified Doorstep Delivery OTP",
                        "simulated_risk_score": simulated_score,
                        "risk_reduction_points": diff,
                        "impact_description": f"Verifying OTP reduces risk score from {final_score} to {simulated_score} (-{diff} pts)"
                    })

            # Counterfactual 2: What if Exit Scale Weight matched?
            if not (package and abs(package.measured_weight_grams - package.total_expected_weight_grams) <= 20.0):
                simulated_adj = rule_adjustment - (25.0 * RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"])
                simulated_score = int(max(0.0, min(100.0, (ml_prob_pct * 0.50) + 20.0 + simulated_adj)))
                diff = final_score - simulated_score
                if diff > 0:
                    counterfactuals.append({
                        "signal": "Matching Warehouse Scale Scan Log",
                        "simulated_risk_score": simulated_score,
                        "risk_reduction_points": diff,
                        "impact_description": f"Consistent exit scale weight reduces risk score from {final_score} to {simulated_score} (-{diff} pts)"
                    })

        # 5. Evidence Relationship Graph
        evidence_graph = {
            "claim_id": claim.id,
            "claim_number": claim.claim_number,
            "nodes": [
                {"id": f"claim_{claim.id}", "label": f"Claim {claim.claim_number}", "type": "CLAIM"},
                {"id": f"order_{order.id}", "label": f"Order {order.order_number} (${order.total_amount:.2f})", "type": "ORDER"},
                {"id": f"customer_{claim.customer_id}", "label": f"Customer ID: {claim.customer_id[:8]}...", "type": "CUSTOMER"},
            ],
            "links": [
                {"source": f"claim_{claim.id}", "target": f"order_{order.id}", "label": "REFERENCES_ORDER"},
                {"source": f"claim_{claim.id}", "target": f"customer_{claim.customer_id}", "label": "RAISED_BY"},
            ]
        }

        if package:
            evidence_graph["nodes"].append({
                "id": f"pkg_{package.id}", 
                "label": f"Warehouse Exit Scale ({package.measured_weight_grams}g / {package.total_expected_weight_grams}g)", 
                "type": "WAREHOUSE"
            })
            evidence_graph["links"].append({"source": f"order_{order.id}", "target": f"pkg_{package.id}", "label": "WEIGHED_AT_EXIT"})

        if delivery:
            evidence_graph["nodes"].append({
                "id": f"del_{delivery.id}", 
                "label": f"Delivery OTP: {'VERIFIED' if delivery.otp_verified else 'UNVERIFIED'}", 
                "type": "DELIVERY"
            })
            evidence_graph["links"].append({"source": f"order_{order.id}", "target": f"del_{delivery.id}", "label": "DELIVERED_VIA"})

        if not primary_reasons:
            primary_reasons.append("No major anomaly detected. Warehouse scan and delivery handover consistent.")

        return {
            "risk_score": final_score,
            "ml_probability_pct": ml_prob_pct,
            "confidence_score": confidence_score,
            "risk_level": risk_level,
            "supporting_evidence": supporting_evidence,
            "contradicting_evidence": contradicting_evidence,
            "missing_information": missing_information,
            "primary_reasons": primary_reasons,
            "counterfactuals": counterfactuals,
            "evidence_graph": evidence_graph,
            "factors": factors,
            "pattern_alerts": pattern_alerts,
            "reliability_scores": RELIABILITY_SCORES,
            "recommended_action": recommended_action,
            "ml_metrics": ml_metrics
        }
