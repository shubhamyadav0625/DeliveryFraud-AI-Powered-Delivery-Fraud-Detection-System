import pytest
from app.services.evidence_fusion import EvidenceFusionEngine

def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_full_delivery_fraud_lifecycle(client):
    customer_res = client.post("/api/v1/auth/register", json={
        "email": "customer_lifecycle@example.com",
        "password": "Password123!",
        "full_name": "John Customer",
        "role": "CUSTOMER"
    })
    assert customer_res.status_code == 201

    admin_res = client.post("/api/v1/auth/register", json={
        "email": "admin_lifecycle@example.com",
        "password": "AdminPassword123!",
        "full_name": "Fraud Analyst Admin",
        "role": "ADMIN"
    })
    assert admin_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", data={
        "username": "customer_lifecycle@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    customer_token = login_res.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {customer_token}"}

    admin_login_res = client.post("/api/v1/auth/login", data={
        "username": "admin_lifecycle@example.com",
        "password": "AdminPassword123!"
    })
    assert admin_login_res.status_code == 200
    admin_token = admin_login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    order_res = client.post("/api/v1/orders", json={
        "items": [
            {"sku": "SKU-MILK", "item_name": "Organic Whole Milk 1L", "quantity": 1, "unit_price": 3.50, "expected_weight_grams": 1000.0},
            {"sku": "SKU-BREAD", "item_name": "Whole Wheat Bread", "quantity": 1, "unit_price": 2.50, "expected_weight_grams": 400.0},
            {"sku": "SKU-EGGS", "item_name": "Large Eggs 12pk", "quantity": 1, "unit_price": 4.00, "expected_weight_grams": 600.0}
        ]
    }, headers=cust_headers)
    assert order_res.status_code == 201
    order_data = order_res.json()
    order_id = order_data["id"]
    order_items = order_data["items"]
    bread_item_id = next(item["id"] for item in order_items if item["sku"] == "SKU-BREAD")
    eggs_item_id = next(item["id"] for item in order_items if item["sku"] == "SKU-EGGS")

    pkg_res = client.post("/api/v1/packing/record-weight", json={
        "order_id": order_id,
        "measured_weight_grams": 2000.0,
        "seal_intact": True,
        "packing_events": [
            {"sku": "SKU-MILK", "scanned": True, "station_id": "STATION-01"},
            {"sku": "SKU-BREAD", "scanned": True, "station_id": "STATION-01"},
            {"sku": "SKU-EGGS", "scanned": True, "station_id": "STATION-01"}
        ]
    }, headers=admin_headers)
    assert pkg_res.status_code == 201

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

    claim_res = client.post("/api/v1/claims", json={
        "order_id": order_id,
        "claim_items": [
            {"order_item_id": bread_item_id, "claim_type": "MISSING_ITEM", "claimed_quantity": 1, "customer_reason": "Bread missing from bag"},
            {"order_item_id": eggs_item_id, "claim_type": "MISSING_ITEM", "claimed_quantity": 1, "customer_reason": "Eggs missing from bag"}
        ]
    }, headers=cust_headers)
    assert claim_res.status_code == 201
    claim_data = claim_res.json()
    claim_id = claim_data["id"]

    assessment = claim_data["risk_assessment"]
    assert assessment is not None
    assert assessment["risk_score"] >= 40
    assert len(assessment["primary_reasons"]) > 0

    dec_res = client.post(f"/api/v1/admin/claims/{claim_id}/decision", json={
        "decision": "REJECTED",
        "decision_notes": "All items scanned during packing, package weight matched 2000g, and OTP was verified at delivery."
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
