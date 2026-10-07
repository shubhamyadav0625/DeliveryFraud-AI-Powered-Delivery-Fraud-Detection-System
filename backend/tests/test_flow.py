def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_full_delivery_fraud_lifecycle(client):
    # 1. Register Customer
    customer_res = client.post("/api/v1/auth/register", json={
        "email": "customer@example.com",
        "password": "Password123!",
        "full_name": "John Customer",
        "role": "CUSTOMER"
    })
    assert customer_res.status_code == 201
    customer_user = customer_res.json()

    # 2. Register Admin
    admin_res = client.post("/api/v1/auth/register", json={
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "Fraud Analyst Admin",
        "role": "ADMIN"
    })
    assert admin_res.status_code == 201

    # 3. Login Customer
    login_res = client.post("/api/v1/auth/login", data={
        "username": "customer@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    customer_token = login_res.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {customer_token}"}

    # 4. Login Admin
    admin_login_res = client.post("/api/v1/auth/login", data={
        "username": "admin@example.com",
        "password": "AdminPassword123!"
    })
    assert admin_login_res.status_code == 200
    admin_token = admin_login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 5. Customer creates Order (Milk x 1, Bread x 1, Eggs x 12)
    order_res = client.post("/api/v1/orders", json={
        "items": [
            {"sku": "SKU-MILK", "item_name": "Organic Milk 1L", "quantity": 1, "unit_price": 3.50, "expected_weight_grams": 1000.0},
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

    # 6. Admin/Warehouse records packing events and scale exit weight
    # Total expected = 1000 + 400 + 600 = 2000g. Measured = 2000g.
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

    # 7. Delivery Partner marks IN_TRANSIT and verifies OTP
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
    assert otp_res.json()["otp_verified"] is True

    # 8. Customer raises claim claiming Bread and Eggs are missing!
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

    # Verify Evidence Fusion Engine outputs high risk due to contradictions!
    # (Items were scanned + weight matched + OTP verified)
    assessment = claim_data["risk_assessment"]
    assert assessment is not None
    assert assessment["risk_score"] >= 70
    assert assessment["recommended_action"] == "MANUAL_REVIEW"
    assert len(assessment["contradicting_evidence"]) >= 2

    # 9. Admin views claim in queue and approves/rejects
    queue_res = client.get("/api/v1/admin/claims", headers=admin_headers)
    assert queue_res.status_code == 200
    assert len(queue_res.json()) >= 1

    dec_res = client.post(f"/api/v1/admin/claims/{claim_id}/decision", json={
        "decision": "REJECTED",
        "decision_notes": "All items scanned during packing, package weight matched 2000g, and OTP was verified at delivery."
    }, headers=admin_headers)
    assert dec_res.status_code == 200
    assert dec_res.json()["decision"] == "REJECTED"
