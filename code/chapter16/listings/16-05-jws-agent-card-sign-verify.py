import base64
import json

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import (
    padding,
    rsa,
)


def jcs_serialize(card_without_signatures: dict) -> bytes:
    """RFC 8785 JCS: canonical JSON, sorted keys, no whitespace."""
    return json.dumps(
        card_without_signatures,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")  # ①

def sign_agent_card(
    card: dict, private_key: rsa.RSAPrivateKey
) -> dict:
    """Attach a JWS signature to the Agent Card."""
    card_to_sign = {
        k: v for k, v in card.items() if k != "signatures"
    }
    payload = base64.urlsafe_b64encode(
        jcs_serialize(card_to_sign)
    ).rstrip(b"=")
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
    ).rstrip(b"=")
    signing_input = header + b"." + payload
    sig_bytes = private_key.sign(
        signing_input, padding.PKCS1v15(), hashes.SHA256()
    )
    signature = (
        base64.urlsafe_b64encode(sig_bytes).rstrip(b"=").decode()
    )
    return {
        **card,
        "signatures": [
            {
                "protected": header.decode(),
                "signature": signature,
            }
        ],
    }

def verify_agent_card(
    card: dict, public_key: rsa.RSAPublicKey
) -> bool:
    """Return True only if JWS signature verifies against payload."""
    signatures = card.get("signatures", [])
    if not signatures:
        raise ValueError(
            "Agent Card has no signatures: reject this card"
        )  # ②
    card_to_verify = {
        k: v for k, v in card.items() if k != "signatures"
    }
    payload = base64.urlsafe_b64encode(
        jcs_serialize(card_to_verify)
    ).rstrip(b"=")
    sig_entry = signatures[0]
    header = sig_entry["protected"].encode()
    signing_input = header + b"." + payload
    sig_bytes = base64.urlsafe_b64decode(
        sig_entry["signature"] + "=="  # Re-pad for urlsafe_b64decode
    )
    public_key.verify(
        sig_bytes, signing_input, padding.PKCS1v15(), hashes.SHA256()
    )
    # cryptography.verify() raises on failure; reaching here = valid
    return True
