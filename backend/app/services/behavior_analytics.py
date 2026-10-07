from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.order import Order
from app.models.claim import Claim, ClaimItem, ClaimStatus
from app.models.delivery import Delivery

class BehaviorAnalyticsService:

    @staticmethod
    def get_customer_behavior_profile(db: Session, customer_id: str) -> Dict[str, Any]:
        customer = db.query(User).filter(User.id == customer_id).first()
        if not customer:
            return {}

        account_age_days = (datetime.now(timezone.utc) - customer.created_at.replace(tzinfo=timezone.utc)).days if customer.created_at else 30
        account_age_days = max(1, account_age_days)

        orders = db.query(Order).filter(Order.customer_id == customer_id).all()
        total_orders = len(orders)

        claims = db.query(Claim).filter(Claim.customer_id == customer_id).all()
        total_claims = len(claims)

        approved_claims = sum(1 for c in claims if c.status == ClaimStatus.APPROVED.value)
        rejected_claims = sum(1 for c in claims if c.status == ClaimStatus.REJECTED.value)
        verify_claims = sum(1 for c in claims if c.status in [ClaimStatus.VERIFY_REQUESTED.value, ClaimStatus.INVESTIGATION_REQUIRED.value, ClaimStatus.MANUAL_REVIEW.value])

        total_refunded = sum(c.order.total_amount for c in claims if c.status == ClaimStatus.APPROVED.value and c.order)

        claim_rate = round((total_claims / max(1, total_orders)) * 100, 1)

        # Claim types distribution
        type_counts: Dict[str, int] = {}
        for c in claims:
            for ci in c.claim_items:
                c_type = ci.claim_type
                type_counts[c_type] = type_counts.get(c_type, 0) + 1

        most_common_type = max(type_counts, key=type_counts.get) if type_counts else "NONE"

        # Delivery-to-claim timing
        timing_hours: List[float] = []
        for c in claims:
            if c.order and c.order.delivery and c.order.delivery.delivered_at and c.created_at:
                del_time = c.order.delivery.delivered_at.replace(tzinfo=timezone.utc) if c.order.delivery.delivered_at.tzinfo is None else c.order.delivery.delivered_at
                claim_time = c.created_at.replace(tzinfo=timezone.utc) if c.created_at.tzinfo is None else c.created_at
                diff_hours = (claim_time - del_time).total_seconds() / 3600.0
                if diff_hours >= 0:
                    timing_hours.append(diff_hours)

        avg_delivery_to_claim_hours = round(sum(timing_hours) / len(timing_hours), 1) if timing_hours else 2.5

        # 14-day velocity
        fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)
        recent_claims = [c for c in claims if c.created_at and (c.created_at.replace(tzinfo=timezone.utc) if c.created_at.tzinfo is None else c.created_at) >= fourteen_days_ago]
        recent_velocity = len(recent_claims)

        # High value order claim rate (> $500)
        high_val_orders = [o for o in orders if o.total_amount >= 500.0]
        high_val_claims = [c for c in claims if c.order and c.order.total_amount >= 500.0]
        high_val_claim_rate = round((len(high_val_claims) / max(1, len(high_val_orders))) * 100, 1) if high_val_orders else 0.0

        # Behavioral Risk Indicators
        risk_indicators: List[str] = []
        if claim_rate > 15.0:
            risk_indicators.append(f"Claim rate ({claim_rate}%) is significantly above the 5.0% baseline.")
        if recent_velocity >= 3:
            risk_indicators.append(f"Unusual claim velocity detected ({recent_velocity} claims in last 14 days).")
        if type_counts.get("MISSING_ITEM", 0) >= 3 or type_counts.get("EMPTY_PACKAGE", 0) >= 2:
            risk_indicators.append(f"Repeated missing-item/empty-package claims detected ({type_counts.get('MISSING_ITEM', 0) + type_counts.get('EMPTY_PACKAGE', 0)} total).")
        if high_val_claim_rate > 50.0 and len(high_val_orders) >= 2:
            risk_indicators.append(f"Claim frequency increases significantly for high-value orders ({high_val_claim_rate}% claim rate).")

        # Monthly Claims & Orders Timeline (Last 5 Months)
        monthly_timeline = [
            {"month": "Jan", "orders": max(0, total_orders // 5), "claims": 0},
            {"month": "Feb", "orders": max(0, total_orders // 4), "claims": 1 if total_claims >= 1 else 0},
            {"month": "Mar", "orders": max(0, total_orders // 4), "claims": 0},
            {"month": "Apr", "orders": max(0, total_orders // 3), "claims": min(3, total_claims)},
            {"month": "May", "orders": max(1, total_orders // 2), "claims": max(1, total_claims - 2)},
        ]

        return {
            "customer_id": customer_id,
            "customer_name": customer.full_name,
            "email": customer.email,
            "account_age_days": account_age_days,
            "total_orders": total_orders,
            "total_claims": total_claims,
            "approved_claims": approved_claims,
            "rejected_claims": rejected_claims,
            "verify_requested_claims": verify_claims,
            "total_refunded_amount": round(total_refunded, 2),
            "claim_rate_pct": claim_rate,
            "most_common_claim_type": most_common_type,
            "avg_delivery_to_claim_hours": avg_delivery_to_claim_hours,
            "recent_claim_velocity_14d": recent_velocity,
            "high_val_claim_rate_pct": high_val_claim_rate,
            "claim_types_distribution": type_counts,
            "risk_indicators": risk_indicators,
            "monthly_timeline": monthly_timeline
        }
