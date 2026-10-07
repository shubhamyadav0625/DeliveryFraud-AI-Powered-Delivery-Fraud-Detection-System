from typing import Dict, Any, List

class FraudRingDetectorService:
    """
    Enterprise Fraud Ring & Syndicate Graph Detection Engine.
    Analyzes shared device fingerprints, delivery addresses, and payment instrument hashes.
    """

    @staticmethod
    def detect_syndicate_cluster(
        customer_id: str,
        address_hash: str,
        device_fingerprint: str,
        known_connections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates graph node degree and cluster density to identify linked fraud rings.
        """
        shared_devices = [conn for conn in known_connections if conn.get("device_fingerprint") == device_fingerprint]
        shared_addresses = [conn for conn in known_connections if conn.get("address_hash") == address_hash]

        linked_accounts = list(set(
            [c.get("customer_id") for c in shared_devices + shared_addresses if c.get("customer_id") != customer_id]
        ))

        is_fraud_ring = len(linked_accounts) >= 3

        return {
            "target_customer_id": customer_id,
            "linked_accounts_count": len(linked_accounts),
            "linked_account_ids": linked_accounts,
            "fraud_ring_detected": is_fraud_ring,
            "cluster_risk_score": 85.0 if is_fraud_ring else (len(linked_accounts) * 20.0),
            "risk_recommendation": "FLAG_FRAUD_SYNDICATE" if is_fraud_ring else "NORMAL_GRAPH"
        }
