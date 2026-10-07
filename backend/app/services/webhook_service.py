import hmac
import hashlib
import json
import time
from typing import Dict, Any, List

class WebhookDispatcherService:
    """
    Enterprise Webhooks & Partner API Event Notification Subsystem.
    Dispatches real-time HMAC-signed HTTP event notifications to enterprise platforms (Blinkit, Zepto, Amazon).
    """

    SUPPORTED_EVENTS = [
        "claim.created",
        "claim.assessed",
        "fraud.alert_high_risk",
        "decision.recorded"
    ]

    @staticmethod
    def generate_hmac_signature(payload_json: str, secret_key: str) -> str:
        """
        Generates HMAC-SHA256 signature header for webhook authenticity verification.
        """
        return hmac.new(
            secret_key.encode("utf-8"),
            payload_json.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def create_webhook_payload(event_type: str, data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        return {
            "event_id": f"evt_{int(time.time() * 1000)}",
            "event_type": event_type,
            "tenant_id": tenant_id,
            "timestamp": int(time.time()),
            "data": data
        }
