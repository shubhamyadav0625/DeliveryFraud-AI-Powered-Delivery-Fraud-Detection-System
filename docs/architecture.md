# 🏛️ DeliveryFraud — Architecture & Technical Specifications

## 1. System Overview

DeliveryFraud is an enterprise-grade AI-assisted delivery integrity and fraud intelligence platform. It ingests multi-source data across the e-commerce fulfillment lifecycle—from warehouse item scanning and package scale weighing to doorstep OTP verification, customer evidence uploads, and historical customer behavior—to produce explainable risk assessments.

---

## 2. Component Architecture

```
           +-------------------------------------------------------+
           |               Customer Claim & Evidence               |
           +-------------------------------------------------------+
                                       |
                                       v
           +-------------------------------------------------------+
           |             Evidence Fusion & Risk Engine             |
           |   (Scale Weight + OTP + ELA Forensics + History)      |
           +-------------------------------------------------------+
                                       |
                     +-----------------+-----------------+
                     |                                   |
                     v                                   v
          [Risk Score: 0-100]                  [Confidence Score: 0-100%]
                     |                                   |
                     +-----------------+-----------------+
                                       |
                                       v
           +-------------------------------------------------------+
           |         Explainable AI & Decision Routing             |
           +-------------------------------------------------------+
                                       |
             +-------------------------+-------------------------+
             |                         |                         |
             v                         v                         v
     [LOW RISK: Approve]    [MEDIUM RISK: Verify]    [HIGH RISK: Analyst Queue]
```

### 2.1 Backend Services
- **FastAPI Layer**: Exposes RESTful JSON endpoints (`/api/v1`).
- **Authentication & Security**: OAuth2 JWT Bearer tokens with password hashing via `passlib[bcrypt]`. Role-Based Access Control (RBAC) enforces strict separation between `CUSTOMER`, `DELIVERY_PARTNER`, `FRAUD_ANALYST`, and `ADMIN`.
- **Evidence Fusion Engine (`EvidenceFusionEngine`)**: Integrates rule-based evidence weights with ML probability scores to derive unified claim risk ($0-100$) and evidence confidence ($0-100\%$).
- **Machine Learning Subsystem (`MLFraudModelService`)**: Persists an ensemble classifier trained on 11 numerical feature vectors (customer claim frequency, 14-day velocity, order value, weight delta %, doorstep OTP verification, ELA tamper score, duplicate image score, and delivery agent claims).
- **Perceptual Image Forensics (`ImageForensicsService`)**: Computes Difference Hashing (dHash) for visual similarity matching and Error Level Analysis (ELA) for image edit detection.

### 2.2 Database Schema
- **Users Table**: Manages authentication credentials, full names, and assigned roles.
- **Orders & Order Items**: Stores order metadata, line items, unit prices, and expected item weights.
- **Packages Table**: Records exit-scale weight measurements and tote packing barcode scan events.
- **Deliveries Table**: Tracks handover status, doorstep single-use OTP PIN verification, and assigned courier ID.
- **Claims & Claim Items**: Captures customer refund/dispute filings.
- **Risk Assessments Table**: Stores calculated risk scores, evidence confidence %, supporting/contradicting evidence, factor contribution weights, counterfactuals, and evidence tree graph JSON.
- **Audit Logs Table**: Logs immutable records of analyst decisions, status transitions, and user actions.

---

## 3. Security & Compliance Rules

1. **Public Registration**: Strictly defaults role to `CUSTOMER`. Public callers cannot self-select `ADMIN` or `FRAUD_ANALYST` roles.
2. **Resource Ownership**: Customer endpoints verify that `claim.customer_id == current_user.id` or `order.customer_id == current_user.id`.
3. **Secret Isolation**: Secrets (`SECRET_KEY`, `DATABASE_URL`) are read from environment variables (`.env`).
4. **CORS Control**: Restricts cross-origin requests to explicit domain whitelists defined in `CORS_ORIGINS`.

---

## 4. Machine Learning & Hybrid Scoring Logic

$$\text{Combined Risk Score} = 0.50 \times \text{ML\_Probability\_Pct} + 20.0 + \sum \text{Rule\_Adjustments}$$

Where each rule adjustment is weighted by evidence source reliability:

$$\text{Effective Impact} = \text{Base Impact} \times \text{Reliability\_Score}$$

### Classification Thresholds
- **$0 - 29$**: `LOW` Risk $\rightarrow$ Recommended Action: `APPROVE`
- **$30 - 59$**: `MEDIUM` Risk $\rightarrow$ Recommended Action: `VERIFY`
- **$60 - 79$**: `HIGH` Risk $\rightarrow$ Recommended Action: `MANUAL_REVIEW`
- **$80 - 100$**: `CRITICAL` Risk $\rightarrow$ Recommended Action: `MANUAL_REVIEW`
