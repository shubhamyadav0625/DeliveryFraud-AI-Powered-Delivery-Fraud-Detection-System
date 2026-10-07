import pytest
from app.models.user import UserRole
from app.services.image_forensics import ImageForensicsService
from app.services.ml_fraud_model import MLFraudModelService
from app.services.evidence_fusion import EvidenceFusionEngine

def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_public_registration_prevents_privilege_escalation(client):
    # Public user attempts to register as ADMIN
    res = client.post("/api/v1/auth/register", json={
        "email": "hacker_attempt@example.com",
        "password": "Password123!",
        "full_name": "Attacker",
        "role": "ADMIN"  # Attempting privilege escalation
    })
    assert res.status_code == 201
    user_data = res.json()
    # Must be forced to CUSTOMER role
    assert user_data["role"] == UserRole.CUSTOMER.value

def test_full_delivery_fraud_lifecycle(client):
    # Customer registration
    customer_res = client.post("/api/v1/auth/register", json={
        "email": "customer_lifecycle@example.com",
        "password": "Password123!",
        "full_name": "John Customer",
        "role": "CUSTOMER"
    })
    assert customer_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", data={
        "username": "customer_lifecycle@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    customer_token = login_res.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {customer_token}"}

    # Admin login (seeded admin)
    admin_login_res = client.post("/api/v1/auth/login", data={
        "username": "admin@demo.com",
        "password": "Password123!"
    })
    assert admin_login_res.status_code == 200
    admin_token = admin_login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Order Creation
    order_res = client.post("/api/v1/orders", json={
        "items": [
            {"sku": "SKU-MILK", "item_name": "Organic Whole Milk 1L", "quantity": 1, "unit_price": 3.50, "expected_weight_grams": 1000.0},
            {"sku": "SKU-BREAD", "item_name": "Whole Wheat Bread", "quantity": 1, "unit_price": 2.50, "expected_weight_grams": 400.0}
        ]
    }, headers=cust_headers)
    assert order_res.status_code == 201
    order_data = order_res.json()
    order_id = order_data["id"]
    bread_item_id = next(item["id"] for item in order_data["items"] if item["sku"] == "SKU-BREAD")

    # Record packing weight
    pkg_res = client.post("/api/v1/packing/record-weight", json={
        "order_id": order_id,
        "measured_weight_grams": 1400.0,
        "seal_intact": True,
        "packing_events": [
            {"sku": "SKU-MILK", "scanned": True, "station_id": "STATION-01"},
            {"sku": "SKU-BREAD", "scanned": True, "station_id": "STATION-01"}
        ]
    }, headers=admin_headers)
    assert pkg_res.status_code == 201

    # Delivery & OTP Verification
    delivery_res = client.post("/api/v1/deliveries/update-status", json={
        "order_id": order_id,
        "delivery_status": "IN_TRANSIT"
    }, headers=admin_headers)
    assert delivery_res.status_code == 200
    otp_code = delivery_res.json()["otp_code"]

    otp_res = client.post("/api/v1/deliveries/verify-otp", json={
        "order_id": order_id,
        "otp_code": otp_code
    }, headers=admin_headers)
    assert otp_res.status_code == 200

    # Claim Creation
    claim_res = client.post("/api/v1/claims", json={
        "order_id": order_id,
        "claim_items": [
            {"order_item_id": bread_item_id, "claim_type": "MISSING_ITEM", "claimed_quantity": 1, "customer_reason": "Bread missing"}
        ]
    }, headers=cust_headers)
    assert claim_res.status_code == 201
    claim_data = claim_res.json()
    claim_id = claim_data["id"]

    assessment = claim_data["risk_assessment"]
    assert assessment is not None
    assert "risk_score" in assessment
    assert "confidence_score" in assessment

    # Decision Recording
    dec_res = client.post(f"/api/v1/admin/claims/{claim_id}/decision", json={
        "decision": "REJECTED",
        "decision_notes": "All items scanned during packing, package weight matched 1400g, and OTP was verified at delivery."
    }, headers=admin_headers)
    assert dec_res.status_code == 200

def test_rbac_security_restrictions(client):
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "customer_rbac@example.com",
        "password": "Password123!",
        "full_name": "RBAC Customer",
        "role": "CUSTOMER"
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", data={
        "username": "customer_rbac@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    customer_token = login_res.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {customer_token}"}

    # Customer trying to access admin queue should receive 403 Forbidden
    res = client.get("/api/v1/admin/claims", headers=cust_headers)
    assert res.status_code == 403

def test_image_dhash_and_hamming_distance():
    hash1 = "ffff0000ffff0000"
    hash2 = "ffff0000ffff0001"
    dist = ImageForensicsService.calculate_hamming_distance(hash1, hash2)
    assert dist == 1

def test_ml_model_prediction():
    features = {
        "customer_claim_count": 4,
        "customer_recent_claim_count_14d": 3,
        "customer_account_age_days": 10,
        "order_amount": 999.0,
        "weight_delta_pct": 40.0,
        "otp_verified": False,
        "image_tamper_score": 0.8,
        "duplicate_image_score": 0.5,
        "delivery_agent_claims_count": 4,
        "delivery_to_claim_hours": 0.5,
        "claim_type_code": 3
    }
    prob_pct, risk_score, metrics = MLFraudModelService.predict_fraud_probability(features)
    assert prob_pct >= 50.0
    assert "precision" in metrics
    assert "recall" in metrics
