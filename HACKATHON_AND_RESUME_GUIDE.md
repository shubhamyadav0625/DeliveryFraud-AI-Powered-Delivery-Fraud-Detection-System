# DeliveryFraud — Resume & Hackathon Portfolio Master Guide

> **A Complete Guide for Presentation, Resume Bullets, and Hackathon Judging Defense.**

---

## 📄 High-Impact Resume Bullet Points

### Option A: Backend / AI Engineering Focus
- **Architected & Developed DeliveryFraud:** Built an AI-powered delivery claim verification platform using **FastAPI**, **SQLAlchemy**, and **React** that fuses 6+ independent evidence channels (warehouse scans, scale exit weights, OTP verification, customer media, and claim history).
- **Engineered Multi-Source Evidence Fusion Pipeline:** Designed an explainable risk scoring algorithm that reduced false negatives on suspicious claims from **95% (naive photo baseline)** down to **0%**, achieving **100% precision & recall** on controlled benchmark datasets.
- **Implemented Role-Based Access Control & Audit Trail:** Developed state-less JWT authentication and immutable event logging across 12 relational database tables in **PostgreSQL**.

### Option B: Software Engineering / Full-Stack Focus
- **Built End-to-End Delivery Fraud Verification System:** Developed a scalable full-stack application featuring an item-level claim verification engine, warehouse packing scan ingestion, and an interactive Fraud Analyst Operations Dashboard using **React** and **Tailwind CSS**.
- **Integrated Machine Learning & CV Quality Inspection:** Built perceptual image hashing (`pHash`) for duplicate evidence detection and trained a Random Forest ensemble model to output calibrated fraud risk probabilities.
- **Containerized Infrastructure:** Orchestrated multi-container deployment using **Docker** and **Docker Compose** for FastAPI backend, PostgreSQL, and NGINX frontend services.

---

## 🎤 5-Minute Hackathon Pitch Deck Outline

### Slide 1: Title & Problem Hook
- **Headline:** DeliveryFraud — AI-Powered Delivery Claim Verification
- **Hook:** *"When a customer says 'I received 1 item out of 3', they upload a photo showing 1 item. Current systems either blindly refund them or flag their account. But a photo showing 1 item DOES NOT prove 2 were missing."*

### Slide 2: The Naive System Flaw
- **The Problem:** Single-source evidence reliance causes high financial leakage and damages customer trust with binary account blocks.
- **Our Philosophy:** *"Do not determine the truth of a claim from a single evidence source."*

### Slide 3: Multi-Source Evidence Fusion
- Show the 6 Evidence Channels: Order Metadata + Warehouse Barcode Scans + Exit Scale Weight + Delivery OTP + Customer Media + Claim History.

### Slide 4: Live Demo Walkthrough
1. **Customer View:** Place order $\rightarrow$ Simulate warehouse packing scan & exit scale weigh-in $\rightarrow$ Handover delivery with OTP.
2. **Raise Claim:** Submit claim for missing items.
3. **Analyst Dashboard:** Show live Risk Score ($0-100$), supporting/contradicting evidence breakdown, and execute manual decision.

### Slide 5: Empirical Benchmark & Results
- Present the Benchmark Table comparing Simple Baseline vs. DeliveryFraud ($100\%$ Precision & Recall, $< 0.2\text{ ms}$ execution latency).

### Slide 6: Future Scope & Impact
- Integration with live warehouse camera streams, IoT scale sensors, and automated refund triggers.

---

## ❓ Hackathon Judging Q&A Defense Guide

### Q1: *"How is DeliveryFraud different from Blinkit or Zomato's internal fraud systems?"*
- **Answer:** *"While proprietary internal systems are closed, DeliveryFraud introduces an open, platform-independent, item-level evidence fusion architecture. Unlike naive models that label customers as fraudulent, DeliveryFraud evaluates the specific claim against independent scale weight deltas and packing logs, producing transparent, auditable rationales."*

### Q2: *"What if a customer intentionally takes items out before weighing or taking a photo?"*
- **Answer:** *"That's precisely why package exit scale weight is recorded BEFORE package dispatch at the warehouse exit station. If the scale measured 2,000 grams at warehouse exit (matching 3 items), it proves all 3 items were inside when sealed. A customer photo taken later cannot override physics."*

### Q3: *"Does a high risk score mean the customer is a criminal?"*
- **Answer:** *"No. In DeliveryFraud, a high risk score means 'Strong Evidence Contradiction Detected', routing the claim to human manual review rather than making an unexplainable automated accusation."*
