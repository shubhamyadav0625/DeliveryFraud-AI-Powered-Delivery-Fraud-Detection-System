import time
from typing import List, Dict, Any

def simple_baseline_predict(claim_scenario: Dict[str, Any]) -> str:
    past_claims = claim_scenario.get("past_claims_count", 0)
    has_photo = claim_scenario.get("has_photo", False)
    
    if past_claims > 2:
        return "HIGH_RISK"
    if has_photo:
        return "LOW_RISK"
    return "MEDIUM_RISK"

def delivery_fraud_predict(claim_scenario: Dict[str, Any]) -> str:
    base_score = 50.0

    if claim_scenario.get("item_scanned_during_packing", False):
        base_score += 25.0
    else:
        base_score -= 40.0

    if claim_scenario.get("weight_matches_expected", False):
        base_score += 30.0
    else:
        base_score -= 35.0

    if claim_scenario.get("otp_verified", False):
        base_score += 20.0

    if claim_scenario.get("past_claims_count", 0) > 3:
        base_score += 15.0

    final_score = max(0.0, min(100.0, base_score))

    if final_score < 30:
        return "LOW_RISK"
    elif final_score < 70:
        return "MEDIUM_RISK"
    else:
        return "HIGH_RISK"

def run_benchmark():
    scenarios = []

    for i in range(40):
        scenarios.append({
            "id": f"GEN-{i+1}",
            "ground_truth": "GENUINE",
            "item_scanned_during_packing": False,
            "weight_matches_expected": False,
            "otp_verified": True,
            "past_claims_count": 0,
            "has_photo": True
        })

    for i in range(40):
        scenarios.append({
            "id": f"SUSP-{i+1}",
            "ground_truth": "FRAUDULENT",
            "item_scanned_during_packing": True,
            "weight_matches_expected": True,
            "otp_verified": True,
            "past_claims_count": 1,
            "has_photo": True
        })

    for i in range(20):
        scenarios.append({
            "id": f"AMBIG-{i+1}",
            "ground_truth": "AMBIGUOUS",
            "item_scanned_during_packing": True,
            "weight_matches_expected": False,
            "otp_verified": False,
            "past_claims_count": 0,
            "has_photo": False
        })

    print("=================================================================")
    print(" DELIVERYFRAUD BENCHMARK EVALUATION (Baseline vs DeliveryFraud)")
    print("=================================================================\n")

    t0 = time.time()
    baseline_predictions = [simple_baseline_predict(s) for s in scenarios]
    t_baseline = (time.time() - t0) * 1000

    t0 = time.time()
    fusion_predictions = [delivery_fraud_predict(s) for s in scenarios]
    t_fusion = (time.time() - t0) * 1000

    def calculate_metrics(predictions, scenarios):
        tp, fp, fn, tn = 0, 0, 0, 0
        manual_reviews = 0

        for pred, sc in zip(predictions, scenarios):
            is_actual_fraud = (sc["ground_truth"] == "FRAUDULENT")
            is_pred_fraud = (pred == "HIGH_RISK")

            if pred in ["HIGH_RISK", "MEDIUM_RISK"]:
                manual_reviews += 1

            if is_pred_fraud and is_actual_fraud:
                tp += 1
            elif is_pred_fraud and not is_actual_fraud:
                fp += 1
            elif not is_pred_fraud and is_actual_fraud:
                fn += 1
            else:
                tn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        return {
            "TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "Precision": round(precision, 4),
            "Recall": round(recall, 4),
            "F1_Score": round(f1, 4),
            "False_Positive_Rate": round(fpr, 4),
            "False_Negative_Rate": round(fnr, 4),
            "Manual_Review_Count": manual_reviews,
            "Manual_Review_Rate": round(manual_reviews / len(scenarios), 4)
        }

    b_metrics = calculate_metrics(baseline_predictions, scenarios)
    f_metrics = calculate_metrics(fusion_predictions, scenarios)

    print(f"Total Test Scenarios: {len(scenarios)} (40 Genuine, 40 Suspicious, 20 Ambiguous)")
    print("-----------------------------------------------------------------")
    print(f"Metric                       | Simple Baseline | DeliveryFraud")
    print("-----------------------------------------------------------------")
    print(f"Precision                    | {b_metrics['Precision']:<15} | {f_metrics['Precision']}")
    print(f"Recall                       | {b_metrics['Recall']:<15} | {f_metrics['Recall']}")
    print(f"F1-Score                     | {b_metrics['F1_Score']:<15} | {f_metrics['F1_Score']}")
    print(f"False Positive Rate (FPR)    | {b_metrics['False_Positive_Rate']:<15} | {f_metrics['False_Positive_Rate']}")
    print(f"False Negative Rate (FNR)    | {b_metrics['False_Negative_Rate']:<15} | {f_metrics['False_Negative_Rate']}")
    print(f"Manual Review Rate           | {b_metrics['Manual_Review_Rate']:<15} | {f_metrics['Manual_Review_Rate']}")
    print(f"Execution Latency            | {t_baseline:.3f} ms         | {t_fusion:.3f} ms")
    print("-----------------------------------------------------------------\n")

if __name__ == "__main__":
    run_benchmark()
