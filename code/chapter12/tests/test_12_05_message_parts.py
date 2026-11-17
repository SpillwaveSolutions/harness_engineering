"""Tests for listing 12-05-message-parts.

Depends on a2a-sdk v1.0+ and base64 (stdlib). The listing will skip
gracefully if a2a-sdk is not installed in the dev environment.

Structural claim from §12.5: the listing exports a function
`build_loyalty_request` that accepts an account_id and pdf_bytes and
returns a Message object with three parts (TextPart, FilePart, DataPart).
"""

from __future__ import annotations


def test_listing_loads(load_listing):
    module = load_listing("12-05-message-parts")
    assert module is not None


def test_build_loyalty_request_is_callable(load_listing):
    module = load_listing("12-05-message-parts")
    assert callable(module.build_loyalty_request)


def test_build_loyalty_request_mixes_three_parts(load_listing):
    module = load_listing("12-05-message-parts")
    message = module.build_loyalty_request("ACC123", b"%PDF-offline")
    assert len(message.parts) == 3
    assert "ACC123" in message.parts[0].text
    assert message.parts[1].filename == "booking_draft.pdf"
    fields = message.parts[2].data.struct_value.fields
    assert fields["accountId"].string_value == "ACC123"
