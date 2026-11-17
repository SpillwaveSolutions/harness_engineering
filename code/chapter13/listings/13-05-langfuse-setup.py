import os
import sys

from langfuse import get_client


def setup_langfuse():
    """Register Langfuse only when both keys are present.

    Importing this module does not call ``get_client()``.
    """
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        print(
            "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are unset; "
            "Langfuse export is disabled.",
            file=sys.stderr,
        )
        return None
    # Langfuse SDK auto-registers an OTel span processor on get_client().
    return get_client()


def main() -> int:
    client = setup_langfuse()
    print("configured" if client is not None else "offline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
