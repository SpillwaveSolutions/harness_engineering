import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class SourceChannel(str, Enum):
    USER_INPUT = "user_input"
    TOOL_OUTPUT = "tool_output"
    MODEL_INFERENCE = "model_inference"

@dataclass
class ProvenanceEnvelope:  # ①
    session_id: str
    tenant_id: str
    timestamp: str
    source_channel: SourceChannel
    # 0.0 = untrusted tool output, 1.0 = direct user statement
    trust_score: float
    content_hash: str

INJECTION_TRIGGERS = [
    r"\bAGENT\b.*?:",
    r"ignore\s+previous",
    r"remember\s+that",
    r"store\s+this\s+preference",
    r"override\s+(system|instructions)",
    r"<!-- .*? -->",
]
MAX_CHUNK_BYTES = 2048

def validate_memory_write(
    content: str,
    tenant_id: str,
    session_id: str,
    source_channel: SourceChannel,
) -> ProvenanceEnvelope:
    """Write-time validator. Raises ValueError on rejected writes."""
    # ② Length check: long chunks are steganographic carriers
    encoded_len = len(content.encode("utf-8"))
    if encoded_len > MAX_CHUNK_BYTES:
        raise ValueError(
            f"Memory write exceeds max chunk size "
            f"({encoded_len} bytes)"
        )
    # ③ Instruction-pattern detection
    for pattern in INJECTION_TRIGGERS:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            raise ValueError(
                f"Injection pattern rejected at write time: "
                f"{pattern!r}"
            )
    # ④ Assign trust score by source channel
    trust_scores = {
        SourceChannel.USER_INPUT: 0.9,
        SourceChannel.MODEL_INFERENCE: 0.6,
        # Lowest: untrusted external data
        SourceChannel.TOOL_OUTPUT: 0.2,
    }
    return ProvenanceEnvelope(
        session_id=session_id,
        tenant_id=tenant_id,
        timestamp=datetime.now(UTC).isoformat(),
        source_channel=source_channel,
        trust_score=trust_scores[source_channel],
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
    )
