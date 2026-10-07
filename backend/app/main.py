from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api.v1.router import api_v1_router
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import app.models

Base.metadata.create_all(bind=engine)

def seed_demo_users():
    db = SessionLocal()
    try:
        cust = db.query(User).filter(User.email == "customer@demo.com").first()
        if not cust:
            cust = User(
                email="customer@demo.com",
                password_hash=get_password_hash("Password123!"),
                full_name="Demo Customer",
                role=UserRole.CUSTOMER.value
            )
            db.add(cust)
            db.flush()

        admin = db.query(User).filter(User.email == "admin@demo.com").first()
        if not admin:
            admin = User(
                email="admin@demo.com",
                password_hash=get_password_hash("Password123!"),
                full_name="Demo Fraud Analyst",
                role=UserRole.ADMIN.value
            )
            db.add(admin)
            db.flush()

        from app.models.claim import Claim, ClaimItem, ClaimStatus, ClaimType
        from app.models.order import Order, OrderItem, OrderStatus
        from app.models.package import Package
        from app.models.delivery import Delivery, DeliveryStatus
        from app.models.risk import RiskAssessment, RiskLevel, RecommendedAction
        from app.services.evidence_fusion import EvidenceFusionEngine

        existing_claim = db.query(Claim).first()
        if not existing_claim:
            # --- SCENARIO A: Genuine Claim (Low Risk, High Confidence) ---
            ord1 = Order(customer_id=cust.id, order_number="ORD-DEMO-001", total_amount=89.99, status=OrderStatus.CLAIMED.value)
            db.add(ord1)
            db.flush()
            item1 = OrderItem(order_id=ord1.id, sku="SKU-HEADPHONES", item_name="Wireless Headphones", quantity=1, unit_price=89.99, expected_weight_grams=350.0)
            db.add(item1)
            pkg1 = Package(order_id=ord1.id, package_barcode="PKG-001", total_expected_weight_grams=350.0, measured_weight_grams=350.0, seal_intact=True)
            db.add(pkg1)
            del1 = Delivery(order_id=ord1.id, delivery_status=DeliveryStatus.DELIVERED.value, otp_code="123456", otp_verified=True, delivery_partner_id="PARTNER-01")
            db.add(del1)
            clm1 = Claim(order_id=ord1.id, customer_id=cust.id, claim_number="CLM-10001", status=ClaimStatus.APPROVED.value)
            db.add(clm1)
            db.flush()
            ci1 = ClaimItem(claim_id=clm1.id, order_item_id=item1.id, claim_type=ClaimType.MISSING_ITEM.value, claimed_quantity=1, customer_reason="Packaging corner damaged")
            db.add(ci1)
            f1 = EvidenceFusionEngine.evaluate_claim(clm1, ord1, pkg1, del1, customer_past_claims_count=0)
            ra1 = RiskAssessment(claim_id=clm1.id, risk_score=f1["risk_score"], confidence_score=f1["confidence_score"], risk_level=f1["risk_level"], recommended_action=f1["recommended_action"])
            ra1.supporting_evidence = f1["supporting_evidence"]
            ra1.contradicting_evidence = f1["contradicting_evidence"]
            ra1.missing_information = f1["missing_information"]
            ra1.primary_reasons = f1["primary_reasons"]
            ra1.counterfactuals = f1["counterfactuals"]
            ra1.evidence_graph = f1["evidence_graph"]
            ra1.factors = f1["factors"]
            ra1.pattern_alerts = f1["pattern_alerts"]
            ra1.reliability_scores = f1["reliability_scores"]
            db.add(ra1)

            # --- SCENARIO B: Repeated Customer Behavior (Medium Risk) ---
            ord2 = Order(customer_id=cust.id, order_number="ORD-DEMO-002", total_amount=249.00, status=OrderStatus.CLAIMED.value)
            db.add(ord2)
            db.flush()
            item2 = OrderItem(order_id=ord2.id, sku="SKU-SMARTWATCH", item_name="Smartwatch v2", quantity=1, unit_price=249.00, expected_weight_grams=280.0)
            db.add(item2)
            pkg2 = Package(order_id=ord2.id, package_barcode="PKG-002", total_expected_weight_grams=280.0, measured_weight_grams=280.0, seal_intact=True)
            db.add(pkg2)
            del2 = Delivery(order_id=ord2.id, delivery_status=DeliveryStatus.DELIVERED.value, otp_code="654321", otp_verified=True, delivery_partner_id="PARTNER-02")
            db.add(del2)
            clm2 = Claim(order_id=ord2.id, customer_id=cust.id, claim_number="CLM-10002", status=ClaimStatus.VERIFY_REQUESTED.value)
            db.add(clm2)
            db.flush()
            ci2 = ClaimItem(claim_id=clm2.id, order_item_id=item2.id, claim_type=ClaimType.DAMAGED_ITEM.value, claimed_quantity=1, customer_reason="Screen unresponsive")
            db.add(ci2)
            f2 = EvidenceFusionEngine.evaluate_claim(clm2, ord2, pkg2, del2, customer_past_claims_count=4, recent_claims_in_window=3)
            ra2 = RiskAssessment(claim_id=clm2.id, risk_score=f2["risk_score"], confidence_score=f2["confidence_score"], risk_level=f2["risk_level"], recommended_action=f2["recommended_action"])
            ra2.supporting_evidence = f2["supporting_evidence"]
            ra2.contradicting_evidence = f2["contradicting_evidence"]
            ra2.missing_information = f2["missing_information"]
            ra2.primary_reasons = f2["primary_reasons"]
            ra2.counterfactuals = f2["counterfactuals"]
            ra2.evidence_graph = f2["evidence_graph"]
            ra2.factors = f2["factors"]
            ra2.pattern_alerts = f2["pattern_alerts"]
            ra2.reliability_scores = f2["reliability_scores"]
            db.add(ra2)

            # --- SCENARIO C: Delivery Lifecycle Anomaly (High Risk - Exit Weight Mismatch & Unverified OTP) ---
            ord3 = Order(customer_id=cust.id, order_number="ORD-DEMO-003", total_amount=999.00, status=OrderStatus.CLAIMED.value)
            db.add(ord3)
            db.flush()
            item3 = OrderItem(order_id=ord3.id, sku="SKU-IPHONE15", item_name="iPhone 15 Pro (128GB)", quantity=1, unit_price=999.00, expected_weight_grams=450.0)
            db.add(item3)
            pkg3 = Package(order_id=ord3.id, package_barcode="PKG-003", total_expected_weight_grams=450.0, measured_weight_grams=150.0, seal_intact=False) # Underweight!
            db.add(pkg3)
            del3 = Delivery(order_id=ord3.id, delivery_status=DeliveryStatus.DELIVERED.value, otp_code="987654", otp_verified=False, delivery_partner_id="PARTNER-03")
            db.add(del3)
            clm3 = Claim(order_id=ord3.id, customer_id=cust.id, claim_number="CLM-10003", status=ClaimStatus.INVESTIGATION_REQUIRED.value)
            db.add(clm3)
            db.flush()
            ci3 = ClaimItem(claim_id=clm3.id, order_item_id=item3.id, claim_type=ClaimType.EMPTY_PACKAGE.value, claimed_quantity=1, customer_reason="Box was empty on arrival")
            db.add(ci3)
            f3 = EvidenceFusionEngine.evaluate_claim(clm3, ord3, pkg3, del3, customer_past_claims_count=4, recent_claims_in_window=4)
            ra3 = RiskAssessment(claim_id=clm3.id, risk_score=f3["risk_score"], confidence_score=f3["confidence_score"], risk_level=f3["risk_level"], recommended_action=f3["recommended_action"])
            ra3.supporting_evidence = f3["supporting_evidence"]
            ra3.contradicting_evidence = f3["contradicting_evidence"]
            ra3.missing_information = f3["missing_information"]
            ra3.primary_reasons = f3["primary_reasons"]
            ra3.counterfactuals = f3["counterfactuals"]
            ra3.evidence_graph = f3["evidence_graph"]
            ra3.factors = f3["factors"]
            ra3.pattern_alerts = f3["pattern_alerts"]
            ra3.reliability_scores = f3["reliability_scores"]
            db.add(ra3)

            # --- SCENARIO D: Multi-Signal Coordinated Case (High Risk - Agent Collusion & Image Forensics) ---
            ord4 = Order(customer_id=cust.id, order_number="ORD-DEMO-004", total_amount=1299.00, status=OrderStatus.CLAIMED.value)
            db.add(ord4)
            db.flush()
            item4 = OrderItem(order_id=ord4.id, sku="SKU-DSLR-CAMERA", item_name="Sony Alpha Mirrorless Camera", quantity=1, unit_price=1299.00, expected_weight_grams=850.0)
            db.add(item4)
            pkg4 = Package(order_id=ord4.id, package_barcode="PKG-004", total_expected_weight_grams=850.0, measured_weight_grams=850.0, seal_intact=True)
            db.add(pkg4)
            del4 = Delivery(order_id=ord4.id, delivery_status=DeliveryStatus.DELIVERED.value, otp_code="554433", otp_verified=True, delivery_partner_id="PARTNER-09")
            db.add(del4)
            clm4 = Claim(order_id=ord4.id, customer_id=cust.id, claim_number="CLM-10004", status=ClaimStatus.INVESTIGATION_REQUIRED.value)
            db.add(clm4)
            db.flush()
            ci4 = ClaimItem(claim_id=clm4.id, order_item_id=item4.id, claim_type=ClaimType.MISSING_ITEM.value, claimed_quantity=1, customer_reason="Camera box missing inside outer bag")
            db.add(ci4)
            f4 = EvidenceFusionEngine.evaluate_claim(clm4, ord4, pkg4, del4, customer_past_claims_count=5, recent_claims_in_window=4, delivery_agent_claims_count=4, ela_tamper_score=0.84)
            ra4 = RiskAssessment(claim_id=clm4.id, risk_score=f4["risk_score"], confidence_score=f4["confidence_score"], risk_level=f4["risk_level"], recommended_action=f4["recommended_action"])
            ra4.supporting_evidence = f4["supporting_evidence"]
            ra4.contradicting_evidence = f4["contradicting_evidence"]
            ra4.missing_information = f4["missing_information"]
            ra4.primary_reasons = f4["primary_reasons"]
            ra4.counterfactuals = f4["counterfactuals"]
            ra4.evidence_graph = f4["evidence_graph"]
            ra4.factors = f4["factors"]
            ra4.pattern_alerts = f4["pattern_alerts"]
            ra4.reliability_scores = f4["reliability_scores"]
            db.add(ra4)

            # --- SCENARIO E: High Risk + Low Confidence Case (Missing Exit Scale Scan & Missing Customer Photo) ---
            ord5 = Order(customer_id=cust.id, order_number="ORD-DEMO-005", total_amount=799.00, status=OrderStatus.CLAIMED.value)
            db.add(ord5)
            db.flush()
            item5 = OrderItem(order_id=ord5.id, sku="SKU-TABLET", item_name="High-End Tablet 11-inch", quantity=1, unit_price=799.00, expected_weight_grams=600.0)
            db.add(item5)
            # No package weight record, delivery unverified
            del5 = Delivery(order_id=ord5.id, delivery_status=DeliveryStatus.DELIVERED.value, otp_code="778899", otp_verified=False, delivery_partner_id="PARTNER-05")
            db.add(del5)
            clm5 = Claim(order_id=ord5.id, customer_id=cust.id, claim_number="CLM-10005", status=ClaimStatus.VERIFY_REQUESTED.value)
            db.add(clm5)
            db.flush()
            ci5 = ClaimItem(claim_id=clm5.id, order_item_id=item5.id, claim_type=ClaimType.EMPTY_PACKAGE.value, claimed_quantity=1, customer_reason="Received unsealed parcel")
            db.add(ci5)
            f5 = EvidenceFusionEngine.evaluate_claim(clm5, ord5, None, del5, customer_past_claims_count=2, recent_claims_in_window=1)
            # Override confidence score to be low due to missing inputs
            ra5 = RiskAssessment(claim_id=clm5.id, risk_score=f5["risk_score"], confidence_score=40, risk_level=f5["risk_level"], recommended_action=RecommendedAction.VERIFY.value)
            ra5.supporting_evidence = f5["supporting_evidence"]
            ra5.contradicting_evidence = f5["contradicting_evidence"]
            ra5.missing_information = f5["missing_information"]
            ra5.primary_reasons = f5["primary_reasons"]
            ra5.counterfactuals = f5["counterfactuals"]
            ra5.evidence_graph = f5["evidence_graph"]
            ra5.factors = f5["factors"]
            ra5.pattern_alerts = f5["pattern_alerts"]
            ra5.reliability_scores = f5["reliability_scores"]
            db.add(ra5)

        db.commit()
    except Exception as e:
        print("Seed error:", e)
        db.rollback()
    finally:
        db.close()

seed_demo_users()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health Check"])
def health_check():
    return {
        "status": "healthy",
        "system": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
