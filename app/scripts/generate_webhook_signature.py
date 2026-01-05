"""Helper script to generate webhook signatures for testing."""
import hmac
import hashlib
import json
import sys
from app.config import settings


def generate_signature(payload_dict: dict, secret: str = None) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.
    
    Args:
        payload_dict: Webhook payload as dictionary
        secret: Webhook secret (default from settings)
        
    Returns:
        Hex-encoded signature
    """
    if secret is None:
        secret = settings.WEBHOOK_SECRET

    # Convert dict to JSON string (without signature field)
    payload_copy = payload_dict.copy()
    payload_copy.pop('signature', None)  # Remove signature if exists
    payload_str = json.dumps(payload_copy, separators=(',', ':'), sort_keys=True)
    
    # Generate HMAC-SHA256
    signature = hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature


if __name__ == "__main__":
    # Example usage
    example_payload = {
        "transaction_id": 1,
        "bank_reference": "BANK-REF-123",
        "status": "success",
        "error_message": None
    }
    
    if len(sys.argv) > 1:
        # Use command line argument as transaction_id
        example_payload["transaction_id"] = int(sys.argv[1])
    
    signature = generate_signature(example_payload)
    
    print("=" * 80)
    print("WEBHOOK SIGNATURE GENERATOR")
    print("=" * 80)
    print("\nPayload:")
    print(json.dumps(example_payload, indent=2))
    print(f"\nSignature: {signature}")
    print("\n" + "=" * 80)
    print("FULL REQUEST BODY (copy this):")
    print("=" * 80)
    
    full_payload = example_payload.copy()
    full_payload["signature"] = signature
    print(json.dumps(full_payload, indent=2))
    
    print("\n" + "=" * 80)
    print("PowerShell Command:")
    print("=" * 80)
    print(f"""
$body = @'
{json.dumps(full_payload, indent=2)}
'@

Invoke-RestMethod -Uri "http://localhost:8000/webhooks/bank-callback" -Method POST -Body $body -ContentType "application/json"
""")
