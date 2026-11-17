"""Tests for listing 10-04-credential-isolation.

The listing defines `CredentialProxy`, a pure dataclass with no external
dependencies. All test assertions run without mocking framework deps.

Load-bearing claims from §10.4:
1. `_is_valid_session` accepts tokens that start with 'sess_' and are exactly
   32 characters long.
2. `_is_valid_session` rejects tokens that don't start with 'sess_'.
3. `_is_valid_session` rejects tokens that are fewer than 32 characters.
4. `_is_valid_session` rejects tokens that are more than 32 characters.
5. `call_booking_api` raises PermissionError for an invalid session token.
6. Vault read happens inside the proxy (agent never touches the real credential):
   `vault_client.read` is called with the secrets path during a valid call.
7. `_redact_token` (used internally) masks the real token in the response body.

Note: `_forward` and `_redact_token` are prose-level helpers (not defined in
the listing body). We inject minimal stubs at module scope to exercise the
async code paths without network calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def proxy_module(load_listing):
    """Return the 10-04 module; skip if it can't be imported."""
    return load_listing("10-04-credential-isolation")


@pytest.fixture
def vault_client():
    """Minimal fake vault client: .read() returns a dict with 'token'."""
    client = MagicMock()
    client.read = MagicMock(return_value={"token": "REAL_SECRET_TOKEN_XYZ"})
    return client


@pytest.fixture
def proxy(proxy_module, vault_client):
    """Instantiate CredentialProxy with the fake vault client."""
    return proxy_module.CredentialProxy(vault_client=vault_client)


# ---------------------------------------------------------------------------
# _is_valid_session
# ---------------------------------------------------------------------------

def test_valid_session_token_accepted(proxy) -> None:
    """A 32-char token starting with 'sess_' is valid."""
    # "sess_" (5) + 27 chars = 32 total
    token = "sess_" + "a" * 27
    assert len(token) == 32
    assert proxy._is_valid_session(token) is True


def test_wrong_prefix_rejected(proxy) -> None:
    """A token that does not start with 'sess_' is rejected."""
    token = "user_" + "a" * 27
    assert len(token) == 32
    assert proxy._is_valid_session(token) is False


def test_too_short_rejected(proxy) -> None:
    """A token shorter than 32 characters is rejected."""
    token = "sess_" + "a" * 10  # only 15 chars
    assert len(token) < 32
    assert proxy._is_valid_session(token) is False


def test_too_long_rejected(proxy) -> None:
    """A token longer than 32 characters is rejected."""
    token = "sess_" + "a" * 40  # 45 chars
    assert len(token) > 32
    assert proxy._is_valid_session(token) is False


# ---------------------------------------------------------------------------
# allowed_hosts allowlist
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_off_allowlist_host_raises_permission_error(
    proxy_module, vault_client
) -> None:
    """call_booking_api raises PermissionError for a non-allowlisted host."""
    proxy = proxy_module.CredentialProxy(vault_client=vault_client)
    valid_token = "sess_" + "d" * 27

    with pytest.raises(PermissionError, match="not in allowlist"):
        await proxy.call_booking_api(
            session_token=valid_token,
            destination_url="https://evil.example.com/exfiltrate",
            method="GET",
            payload={},
        )


def test_default_allowed_hosts_contains_amadeus(proxy_module, vault_client) -> None:
    """Default allowed_hosts includes api.amadeus.com."""
    proxy = proxy_module.CredentialProxy(vault_client=vault_client)
    assert "api.amadeus.com" in proxy.allowed_hosts


# ---------------------------------------------------------------------------
# call_booking_api — invalid session path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_session_raises_permission_error(
    proxy_module, vault_client
) -> None:
    """call_booking_api raises PermissionError for an invalid session token."""
    proxy = proxy_module.CredentialProxy(vault_client=vault_client)
    bad_token = "bad_token"

    with pytest.raises(PermissionError) as caught:
        await proxy.call_booking_api(
            session_token=bad_token,
            destination_url="https://api.amadeus.com/v1/flights",
            method="GET",
            payload={},
        )
    message = str(caught.value)
    assert message == "Invalid session token"
    assert bad_token not in message
    assert "sess_" not in message


# ---------------------------------------------------------------------------
# call_booking_api — valid session path: vault is read, real token stays hidden
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vault_read_called_for_valid_session(
    proxy_module, vault_client
) -> None:
    """vault_client.read is called with the secrets path during a valid call."""
    proxy = proxy_module.CredentialProxy(vault_client=vault_client)
    valid_token = "sess_" + "b" * 27

    # Inject prose-only helpers so the async path can complete
    real_token = "REAL_SECRET_TOKEN_XYZ"
    vault_client.read.return_value = {"token": real_token}

    # _redact_token and _forward are referenced but not defined in the listing.
    # Inject minimal stubs at module level.
    async def fake_forward(method, payload, auth):
        return {"result": f"ok auth={auth}"}

    def fake_redact(response, token):
        return {k: v.replace(token, "REDACTED") if isinstance(v, str) else v
                for k, v in response.items()}

    proxy_module._forward = fake_forward
    proxy_module._redact_token = fake_redact

    response = await proxy.call_booking_api(
        session_token=valid_token,
        destination_url="https://api.amadeus.com/v1/flights",
        method="GET",
        payload={"flight": "AA100"},
    )

    vault_client.read.assert_called_once_with("secret/booking-api/prod")
    # The real token must not appear in the response
    assert real_token not in str(response), (
        "real credential must be redacted before the response leaves the proxy"
    )


@pytest.mark.asyncio
async def test_real_token_redacted_in_response(proxy_module, vault_client) -> None:
    """The real API token is masked before the response is returned."""
    proxy = proxy_module.CredentialProxy(vault_client=vault_client)
    valid_token = "sess_" + "c" * 27
    real_token = "SUPER_SECRET_DO_NOT_LEAK"
    vault_client.read.return_value = {"token": real_token}

    async def fake_forward(method, payload, auth):
        # Simulate a leaky API response that echoes the auth header
        return {"body": f"authenticated with {auth}"}

    def fake_redact(response, token):
        return {k: v.replace(token, "[REDACTED]") if isinstance(v, str) else v
                for k, v in response.items()}

    proxy_module._forward = fake_forward
    proxy_module._redact_token = fake_redact

    result = await proxy.call_booking_api(
        session_token=valid_token,
        destination_url="https://api.amadeus.com/v1/orders",
        method="POST",
        payload={"action": "book"},
    )

    assert real_token not in str(result)
    assert "[REDACTED]" in str(result)


def test_redact_token_walks_nested_values(proxy_module) -> None:
    """The real helper replaces the secret with the placeholder."""
    secret = "SUPER_SECRET_DO_NOT_LEAK"
    response = {
        "body": f"authenticated with {secret}",
        "nested": [secret, {"token": secret}],
    }
    cleaned = proxy_module._redact_token(response, secret)
    assert secret not in str(cleaned)
    assert cleaned["body"] == "authenticated with [redacted]"
    assert cleaned["nested"][0] == "[redacted]"
    assert cleaned["nested"][1]["token"] == "[redacted]"


@pytest.mark.asyncio
async def test_forward_does_not_echo_the_secret(proxy_module) -> None:
    secret = "REAL_SECRET_TOKEN_XYZ"
    result = await proxy_module._forward("POST", {"flight": "AA100"}, auth=secret)
    assert result == {"ok": True, "auth_present": True}
    assert secret not in str(result)
