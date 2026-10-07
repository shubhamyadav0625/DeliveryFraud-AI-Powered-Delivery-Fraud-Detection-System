from typing import List, Dict, Any
from datetime import datetime, timezone
from app.models.order import Order
from app.models.package import Package
from app.models.delivery import Delivery
from app.models.claim import Claim, ClaimType
from app.models.risk import RiskLevel, RecommendedAction

# Configurable Evidence Reliability Scores (Demo Defaults)
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
    "MEDIUM_MAX": 69,
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
        ela_tamper_score: float = 0.0
    ) -> Dict[str, Any]:
        
        supporting_evidence: List[Dict[str, Any]] = []
        contradicting_evidence: List[Dict[str, Any]] = []
        missing_information: List[Dict[str, Any]] = []
        primary_reasons: List[str] = []
        factors: List[Dict[str, Any]] = []
        pattern_alerts: List[Dict[str, Any]] = []
        counterfactuals: List[Dict[str, Any]] = []

        # Base neutral starting score
        current_score = 30.0

        # --- 1. DELIVERED / HANDOVER EVIDENCE ---
        if delivery:
            if delivery.otp_verified:
                factor = {
                    "code": "DELIVERY_OTP_VERIFIED",
                    "label": "Delivery OTP Verified at Doorstep",
                    "impact": -15,
                    "reliability": RELIABILITY_SCORES["DELIVERY_OTP"]
                }
                factors.append(factor)
                current_score -= 15.0
                contradicting_evidence.append({
                    "code": "DELIVERY_OTP_VERIFIED",
                    "label": "Verified Handover OTP",
                    "description": f"Customer provided valid OTP ({delivery.otp_code}) to delivery partner at dropoff.",
                    "reliability": RELIABILITY_SCORES["DELIVERY_OTP"]
                })
            else:
                factor = {
                    "code": "DELIVERY_OTP_UNVERIFIED",
                    "label": "Delivery Handover OTP Unverified",
                    "impact": 20,
                    "reliability": RELIABILITY_SCORES["DELIVERY_OTP"]
                }
                factors.append(factor)
                current_score += 20.0
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

        # --- 2. WAREHOUSE EXIT SCALE & SCAN EVIDENCE ---
        if package:
            expected_weight = package.total_expected_weight_grams
            measured_weight = package.measured_weight_grams
            weight_delta = measured_weight - expected_weight
            tolerance = 20.0  # grams

            if abs(weight_delta) <= tolerance:
                factor = {
                    "code": "PACKAGE_WEIGHT_MATCHED",
                    "label": "Exit Package Scale Weight Consistent",
                    "impact": -15,
                    "reliability": RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"]
                }
                factors.append(factor)
                current_score -= 15.0
                contradicting_evidence.append({
                    "code": "PACKAGE_WEIGHT_CONSISTENT",
                    "label": "Exit Scale Weight Match",
                    "description": f"Warehouse exit scale measured {measured_weight}g (Expected: {expected_weight}g).",
                    "reliability": RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"]
                })
            elif weight_delta < -tolerance:
                weight_diff_pct = abs(weight_delta) / max(1.0, expected_weight) * 100
                impact = 30 if weight_diff_pct > 25 else 20
                factor = {
                    "code": "PACKAGE_UNDERWEIGHT",
                    "label": f"Package Underweight by {abs(weight_delta):.1f}g",
                    "impact": impact,
                    "reliability": RELIABILITY_SCORES["PACKAGE_SCALE_WEIGHT"]
                }
                factors.append(factor)
                current_score += impact
                primary_reasons.append(f"Warehouse exit scale weight ({measured_weight}g) is significantly under expected order weight ({expected_weight}g).")
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

        # --- 3. CLAIM TYPE & WAREHOUSE ITEM BARCODE SCANS ---
        for c_item in claim.claim_items:
            order_item = c_item.order_item
            disputed_sku = order_item.sku
            claimed_qty = c_item.claimed_quantity
            c_type = c_item.claim_type

            item_scanned = False
            if package and package.packing_events:
                scanned_events = [e for e in package.packing_events if e.sku == disputed_sku and e.scanned]
                if len(scanned_events) >= claimed_qty:
                    item_scanned = True

            if c_type in [ClaimType.MISSING_ITEM.value, ClaimType.EMPTY_PACKAGE.value]:
                if item_scanned and delivery and delivery.otp_verified and package and abs(package.measured_weight_grams - package.total_expected_weight_grams) <= 20.0:
                    factor = {
                        "code": "CONTRADICTORY_MISSING_CLAIM",
                        "label": f"Warehouse Scanned & Weighed ({order_item.item_name})",
                        "impact": 25,
                        "reliability": RELIABILITY_SCORES["WAREHOUSE_SCAN"]
                    }
                    factors.append(factor)
                    current_score += 25.0
                    primary_reasons.append(f"Customer reported item '{order_item.item_name}' missing, but warehouse scans and scale weights confirm item departed in sealed box.")
                    contradicting_evidence.append({
                        "code": "WAREHOUSE_BARCODE_CONFIRMED",
                        "label": f"Barcode Verified ({order_item.item_name})",
                        "description": f"Item SKU {disputed_sku} was scanned into box at packing station STATION-01.",
                        "reliability": RELIABILITY_SCORES["WAREHOUSE_SCAN"]
                    })
            elif c_type == ClaimType.WRONG_ITEM.value:
                if not item_scanned:
                    factor = {
                        "code": "PACKING_SKU_MISMATCH",
                        "label": "Packing Station SKU Mismatch",
                        "impact": 20,
                        "reliability": RELIABILITY_SCORES["WAREHOUSE_SCAN"]
                    }
                    factors.append(factor)
                    current_score += 20.0
                    primary_reasons.append("Warehouse packing logs indicate possible SKU swap during dispatch.")

        # --- 4. BEHAVIORAL & FRAUD PATTERN SIGNALS ---
        if customer_past_claims_count > 3:
            factor = {
                "code": "REPEATED_CLAIM_HISTORY",
                "label": f"Customer Claim Frequency ({customer_past_claims_count} previous claims)",
                "impact": 15,
                "reliability": RELIABILITY_SCORES["BEHAVIORAL_HISTORY"]
            }
            factors.append(factor)
            current_score += 15.0
            primary_reasons.append(f"Customer account has submitted {customer_past_claims_count} previous claims.")
            pattern_alerts.append({
                "type": "HISTORICAL_FREQUENCY",
                "severity": "MEDIUM",
                "message": f"Account claim frequency above baseline ({customer_past_claims_count} historical claims)."
            })

        if recent_claims_in_window >= 3:
            factor = {
                "code": "UNUSUAL_CLAIM_VELOCITY",
                "label": "Unusual Claim Velocity Spike",
                "impact": 20,
                "reliability": RELIABILITY_SCORES["BEHAVIORAL_HISTORY"]
            }
            factors.append(factor)
            current_score += 20.0
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
                "message": f"Potential coordinated pattern detected: 3+ disputed deliveries linked to Delivery Agent ID ({delivery.delivery_partner_id if delivery and delivery.delivery_partner_id else 'PARTNER-09'})."
            })
            factor = {
                "code": "COORDINATED_AGENT_PATTERN",
                "label": "Potential Coordinated Agent Pattern",
                "impact": 15,
                "reliability": 0.85
            }
            factors.append(factor)
            current_score += 15.0

        # --- 5. IMAGE FORENSICS & MEDIA EVIDENCE ---
        if ela_tamper_score > 0.5:
            factor = {
                "code": "IMAGE_FORENSICS_TAMPERED",
                "label": f"Image Editing Forensics Signal ({int(ela_tamper_score * 100)}%)",
                "impact": 20,
                "reliability": RELIABILITY_SCORES["IMAGE_FORENSICS_ELA"]
            }
            factors.append(factor)
            current_score += 20.0
            primary_reasons.append("Digital image forensics detected potential Error Level Analysis (ELA) tampering in uploaded photo.")
            supporting_evidence.append({
                "code": "ELA_IMAGE_TAMPERING",
                "label": "Digital Image Forensics Flag",
                "description": f"High error level compression variance detected ({int(ela_tamper_score * 100)}% anomaly).",
                "reliability": RELIABILITY_SCORES["IMAGE_FORENSICS_ELA"]
            })

        if claim.evidence_files:
            factors.append({
                "code": "CUSTOMER_MEDIA_PROVIDED",
                "label": "Customer Media Uploaded",
                "impact": -5,
                "reliability": RELIABILITY_SCORES["CUSTOMER_PHOTO"]
            })
            current_score -= 5.0
        else:
            missing_information.append({
                "code": "CUSTOMER_MEDIA_MISSING",
                "label": "No Customer Evidence Uploaded",
                "description": "Claim submitted without unboxing photo or video attachment."
            })

        # Final score clamping between 0 and 100
        final_score = int(max(0.0, min(100.0, current_score)))

        # Calculate Evidence Confidence (0 - 100%)
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
        if customer_past_claims_count >= 0:
            confidence_inputs += 1
            confidence_points += RELIABILITY_SCORES["BEHAVIORAL_HISTORY"] * 100

        confidence_score = int(round(confidence_points / max(1, confidence_inputs))) if confidence_inputs > 0 else 45

        # Determine Risk Level & Action Routing
        if final_score <= RISK_THRESHOLDS["LOW_MAX"]:
            risk_level = RiskLevel.LOW
            recommended_action = RecommendedAction.APPROVE
        elif final_score <= RISK_THRESHOLDS["MEDIUM_MAX"]:
            risk_level = RiskLevel.MEDIUM
            recommended_action = RecommendedAction.VERIFY
        else:
            risk_level = RiskLevel.HIGH
            recommended_action = RecommendedAction.MANUAL_REVIEW

        # Default fallback primary reason if empty
        if not primary_reasons:
            if final_score < 30:
                primary_reasons.append("No major anomaly detected. Warehouse scan and delivery handover consistent.")
            else:
                primary_reasons.append("Multiple independent signals indicate potential evidence mismatch.")

        # --- 6. COUNTERFACTUAL SUGGESTIONS ---
        if final_score >= 30:
            counterfactuals.append({
                "signal": "Verified Unboxing Video",
                "impact_description": "Could resolve item missing ambiguity (-30 pts risk reduction)",
                "evidence_category": "CUSTOMER_VIDEO"
            })
            if not (package and abs(package.measured_weight_grams - package.total_expected_weight_grams) <= 20.0):
                counterfactuals.append({
                    "signal": "Matching Warehouse Scale Scan Log",
                    "impact_description": "Could verify physical weight departure (-25 pts risk reduction)",
                    "evidence_category": "WAREHOUSE_WEIGHT"
                })
            if not (delivery and delivery.otp_verified):
                counterfactuals.append({
                    "signal": "Confirmed Delivery Handover OTP",
                    "impact_description": "Could verify doorstep recipient authorization (-20 pts risk reduction)",
                    "evidence_category": "DELIVERY_OTP"
                })

        # --- 7. EVIDENCE RELATIONSHIP GRAPH (JSON Tree) ---
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
            evidence_graph["links"].append({
                "source": f"order_{order.id}", 
                "target": f"pkg_{package.id}", 
                "label": "WEIGHED_AT_EXIT"
            })

        if delivery:
            evidence_graph["nodes"].append({
                "id": f"del_{delivery.id}", 
                "label": f"Delivery OTP: {'VERIFIED' if delivery.otp_verified else 'UNVERIFIED'}", 
                "type": "DELIVERY"
            })
            evidence_graph["links"].append({
                "source": f"order_{order.id}", 
                "target": f"del_{delivery.id}", 
                "label": "DELIVERED_VIA"
            })

        for idx, ef in enumerate(claim.evidence_files or []):
            evidence_graph["nodes"].append({
                "id": f"ev_{ef.id}", 
                "label": f"Customer Photo #{idx+1} ({ef.file_type})", 
                "type": "MEDIA"
            })
            evidence_graph["links"].append({
                "source": f"claim_{claim.id}", 
                "target": f"ev_{ef.id}", 
                "label": "ATTACHED_MEDIA"
            })

        return {
            "risk_score": final_score,
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
            "recommended_action": recommended_action
        }
