"""Tests for listing 16-05-jws-agent-card-sign-verify.

Verifies sign_agent_card and verify_agent_card against an
in-process RSA key pair: correct signature verifies, tampered
card fails, unsigned card raises ValueError.
"""

import importlib.util
import pathlib
import sys

import pytest
from cryptography.exceptions import InvalidSignature

_CHAPTER_ROOT = pathlib.Path(__file__).parent.parent
if str(_CHAPTER_ROOT) not in sys.path:
    sys.path.insert(0, str(_CHAPTER_ROOT))

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

_LISTING_PATH = (
    _CHAPTER_ROOT
    / "listings"
    / "16-05-jws-agent-card-sign-verify.py"
)
_spec = importlib.util.spec_from_file_location(
    "listing_16_05", _LISTING_PATH
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

sign_agent_card = _mod.sign_agent_card
verify_agent_card = _mod.verify_agent_card
jcs_serialize = _mod.jcs_serialize


@pytest.fixture(scope="module")
def key_pair():
    """Generate a fresh RSA-2048 key pair for the test module."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    return private_key, private_key.public_key()


SAMPLE_CARD = {
    "name": "loyalty.hotelpartner.com",
    "version": "1.0",
    "capabilities": ["book_hotel", "search_hotel"],
    "url": "https://loyalty.hotelpartner.com/a2a",
}


def test_sign_then_verify(key_pair):
    """A freshly signed card must verify against the public key."""
    private_key, public_key = key_pair
    signed = sign_agent_card(SAMPLE_CARD, private_key)
    assert "signatures" in signed
    assert len(signed["signatures"]) == 1
    result = verify_agent_card(signed, public_key)
    assert result is True


def test_tampered_card_fails_verification(key_pair):
    """Changing any field after signing must cause verify to fail."""
    private_key, public_key = key_pair
    signed = sign_agent_card(SAMPLE_CARD, private_key)
    tampered = {**signed, "name": "evil.attacker.com"}
    with pytest.raises(InvalidSignature):
        verify_agent_card(tampered, public_key)


def test_unsigned_card_raises_value_error(key_pair):
    """A card with no signatures key must raise ValueError."""
    _, public_key = key_pair
    with pytest.raises(ValueError, match="no signatures"):
        verify_agent_card(SAMPLE_CARD, public_key)


def test_wrong_key_fails_verification():
    """A card signed with one key must not verify with another."""
    key1 = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    key2 = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    signed = sign_agent_card(SAMPLE_CARD, key1)
    with pytest.raises(InvalidSignature):
        verify_agent_card(signed, key2.public_key())


def test_jcs_serialize_is_deterministic():
    """jcs_serialize must produce identical bytes for same dict."""
    card = {"z": 1, "a": 2, "m": 3}
    b1 = jcs_serialize(card)
    b2 = jcs_serialize(card)
    assert b1 == b2
    # Keys must be sorted per RFC 8785
    assert b1 == b'{"a":2,"m":3,"z":1}'


def test_sign_does_not_mutate_original():
    """sign_agent_card must not modify the original card dict."""
    card = {"name": "test.agent.com", "version": "1.0"}
    _ = sign_agent_card(
        card,
        rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        ),
    )
    assert "signatures" not in card
