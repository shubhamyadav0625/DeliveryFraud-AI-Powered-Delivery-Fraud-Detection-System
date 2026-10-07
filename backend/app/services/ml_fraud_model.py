from typing import Dict, Any
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

class MLFraudClassifier:
    """
    Phase 7: Machine Learning Fraud Risk Classification Model.
    Uses trained Random Forest ensemble to output risk probability based on feature vectors.
    """

    def __init__(self):
        if HAS_SKLEARN:
            self.model = RandomForestClassifier(n_estimators=50, random_state=42)
            self._train_baseline_model()
        else:
            self.model = None

    def _train_baseline_model(self):
        X_train = np.array([
            [0, 0, 1, 0, 1],
            [0, 0, 0, 1, 1],
            [0, 1, 1, 0, 1],
            [0, 0, 1, 0, 0],
            [1, 1, 1, 1, 1],
            [1, 1, 1, 4, 1],
            [1, 1, 1, 0, 1],
            [1, 1, 1, 2, 1],
        ])
        y_train = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        self.model.fit(X_train, y_train)

    def predict_risk_probability(self, features: Dict[str, Any]) -> float:
        if not HAS_SKLEARN or not self.model:
            # Fallback heuristic calculation if scikit-learn is not installed
            score = 50.0
            if features.get("item_scanned_during_packing", False): score += 20.0
            if features.get("weight_matches_expected", False): score += 25.0
            return float(round(min(100.0, max(0.0, score)), 2))

        vec = np.array([[
            1 if features.get("item_scanned_during_packing", False) else 0,
            1 if features.get("weight_matches_expected", False) else 0,
            1 if features.get("otp_verified", False) else 0,
            features.get("past_claims_count", 0),
            1 if features.get("has_photo", False) else 0
        ]])
        
        prob = self.model.predict_proba(vec)[0][1]
        return float(round(prob * 100, 2))
