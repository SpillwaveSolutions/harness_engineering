import json

from a2a.types import Message, Part, Role
from google.protobuf.struct_pb2 import Struct, Value


def data_part(payload: dict) -> Part:
    """A Part whose content is a protobuf Struct."""
    struct = Struct()
    struct.update(payload)
    return Part(data=Value(struct_value=struct))


def build_loyalty_request(account_id: str, pdf_bytes: bytes) -> Message:
    return Message(
        message_id=f"loyalty-{account_id}",
        role=Role.ROLE_USER,
        parts=[
            Part(                                          # ①
                text=f"Check loyalty status for account {account_id}"
            ),
            Part(                                          # ②
                raw=pdf_bytes,
                media_type="application/pdf",
                filename="booking_draft.pdf",
            ),
            data_part({                                    # ④
                "accountId": account_id,
                "requestType": "full_status",
                "includeRedemption": True,
            }),
        ],
    )


def main() -> int:
    message = build_loyalty_request("ACC123", b"%PDF-offline")
    print(json.dumps({
        "message_id": message.message_id,
        "role": int(message.role),
        "parts": len(message.parts),
        "text": message.parts[0].text,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
