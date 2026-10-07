# 🛡️ DeliveryFraud — AI-Powered Delivery Integrity & Fraud Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.0-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, explainable AI multi-source evidence fusion platform that helps delivery platforms (e.g., e-commerce, quick-commerce, logistics providers) detect, analyze, prioritize, and investigate post-delivery fraudulent claims.

---

## 🌟 Key Features

- **Multi-Source Evidence Fusion Engine**: Fuses warehouse packing scans, exit scale package weights, doorstep OTP verifications, digital photo forensics (ELA), and customer behavioral signals into a unified risk assessment.
- **Dual Metric Risk & Confidence Scoring**:
  - **Risk Score ($0–100$)**: Likelihood of claim anomaly (LOW, MEDIUM, HIGH).
  - **Evidence Confidence Score ($0–100\%$)**: Completeness and reliability weighting of available evidence.
- **Customer Behavioral Intelligence**: Analyzes customer account age, historical claim rate %, 14-day claim velocity spikes, and high-value order claim anomalies.
- **Delivery Lifecycle Event Timeline**: Reconstructs the complete chronological event trail from `ORDER_CREATED` $\rightarrow$ `PACKED` $\rightarrow$ `PACKAGE_WEIGHT_RECORDED` $\rightarrow$ `HANDOVER` $\rightarrow$ `OTP_VERIFIED` $\rightarrow$ `DELIVERED` $\rightarrow$ `CLAIM_CREATED`.
- **Explainable AI & Counterfactual Suggestions**: Highlights exact reasons for suspicion and suggests *"What evidence would change this decision?"* to reduce uncertainty.
- **Evidence Relationship Tree Graph**: Node-and-link visualization connecting claims, orders, customer profiles, warehouse scale weight records, OTP handovers, and attached evidence media.
- **13-Section Fraud Analyst Control Center**: Interactive human-in-the-loop investigation interface with mandatory decision rationale logging for full audit compliance.

---

## 🏗️ Architecture & Tech Stack

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

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy ORM, Pydantic v2, SQLite.
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons.
- **Security & Audit**: OAuth2 JWT Authentication, Role-Based Access Control (CUSTOMER / ADMIN), Immutable Audit Logging.

---

## 🧪 Demonstration Scenarios

The system includes pre-configured realistic investigation scenarios:

| Scenario | Claim Type | Disputed Item | Exit Scale Weight | Doorstep OTP | Risk Score | Confidence | Recommended Action |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **Scenario A** | Missing Item | Wireless Headphones | Matched ($350\text{g}$) | Verified | **15/100** | **95%** | `APPROVE` |
| **Scenario B** | Damaged Item | Smartwatch v2 | Matched ($280\text{g}$) | Verified | **45/100** | **85%** | `VERIFY_REQUESTED` |
| **Scenario C** | Empty Package | iPhone 15 Pro | Underweight ($150\text{g}$ vs $450\text{g}$) | Unverified | **85/100** | **90%** | `INVESTIGATION_REQUIRED` |
| **Scenario D** | Missing Camera | Sony Alpha Camera | Matched ($850\text{g}$) | Agent Alert | **100/100** | **88%** | `INVESTIGATION_REQUIRED` |
| **Scenario E** | Unsealed Parcel | High-End Tablet | Scale Scan Missing | Unverified | **65/100** | **40%** | `VERIFY_REQUESTED` |

---

## 🛠️ Quickstart Installation

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Backend API interactive documentation will be live at: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend Web UI will be live at: `http://localhost:3000`

---

## 📂 Project Directory Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI REST endpoints (v1/auth, v1/claims, v1/customers, v1/admin)
│   │   ├── core/         # JWT Security & Password Hashing
│   │   ├── models/       # SQLAlchemy DB Models (User, Order, Package, Delivery, Claim, Risk)
│   │   ├── schemas/      # Pydantic Schemas
│   │   ├── services/     # Evidence Fusion Engine & Behavioral Analytics Service
│   │   ├── main.py       # Application Entrypoint & DB Seeder
│   │   └── database.py   # Database Session & Engine Configuration
│   ├── tests/            # Pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/          # Fetch API client
│   │   ├── components/   # UI Components (AdminDashboard, CustomerClaimView, OrderFlow)
│   │   └── App.jsx       # App Navigation & Layout
│   └── package.json
├── .gitignore
└── README.md
```

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
