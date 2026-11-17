import asyncio
from dataclasses import dataclass, field

import httpx


async def _forward(method: str, payload: dict, auth: str) -> dict:
    """Hand the booking call off without logging the vault token."""
    del method, payload
    return {"ok": True, "auth_present": bool(auth)}


def _redact_token(response, token: str):
    """Replace every occurrence of the real token with ``[redacted]``.

    An empty token is not a secret to search for. Replacing ``""`` would
    rewrite every string, so the response is returned unchanged.
    """
    if not token:
        return response
    if isinstance(response, dict):
        return {
            key: _redact_token(value, token)
            for key, value in response.items()
        }
    if isinstance(response, list):
        return [_redact_token(value, token) for value in response]
    if isinstance(response, tuple):
        return tuple(_redact_token(value, token) for value in response)
    if isinstance(response, str):
        return response.replace(token, "[redacted]")
    return response


@dataclass
class CredentialProxy:
    """Harness-side proxy: agent calls this; real credentials never leave."""

    vault_client: object  # HashiCorp Vault or AWS Secrets Manager client
    allowed_hosts: frozenset[str] = field(
        default_factory=lambda: frozenset({"api.amadeus.com"})
    )

    async def call_booking_api(
        self,
        session_token: str,      # ① placeholder the agent sees
        destination_url: str,    # agent-controlled URL, validated below
        method: str,
        payload: dict,
    ) -> dict:
        # ② Allowlist check: refuse off-list destinations even if compromised.
        host = httpx.URL(destination_url).host
        if host not in self.allowed_hosts:
            raise PermissionError(f"Host {host!r} not in allowlist")
        # ③ Validate session; reject unknown or expired tokens immediately.
        # The error text must not contain any part of the token.
        if not self._is_valid_session(session_token):
            raise PermissionError("Invalid session token")

        # ④ Fetch real credential from vault. The agent never touches this path.
        real_token = self.vault_client.read("secret/booking-api/prod")["token"]

        # ⑤ Redact before logging: if a real token leaks into a response body,
        # it never reaches the audit trail.
        response = await _forward(method, payload, auth=real_token)
        return _redact_token(response, real_token)

    def _is_valid_session(self, token: str) -> bool:
        # Short-lived session tokens from the harness session manager
        return token.startswith("sess_") and len(token) == 32


def main() -> int:
    proxy = CredentialProxy(vault_client=object())
    try:
        asyncio.run(proxy.call_booking_api(
            session_token="not-a-session",
            destination_url="https://api.amadeus.com/v1/flights",
            method="GET",
            payload={},
        ))
    except PermissionError as exc:
        print(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
