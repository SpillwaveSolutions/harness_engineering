"""Tests for listing 08-04-semantic-validator.

Pure Pydantic v2 model — fully importable and testable without any framework
deps. Covers the four load-bearing semantic claims from §8.4:

1. A well-formed booking passes validation.
2. Negative `price_usd` is rejected by the `field_validator`.
3. A past `departure_date` is rejected by the `field_validator`.
4. A `return_date` on or before `departure_date` is rejected by the
   `model_validator` (which runs after individual field validators).
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError


def test_valid_booking_passes(load_listing) -> None:
    """A future-dated booking with positive price and proper return ordering passes."""
    module = load_listing("08-04-semantic-validator")
    future = date.today() + timedelta(days=30)
    later = future + timedelta(days=7)
    booking = module.FlightBookingOutput(
        flight_id="AA100",
        passenger_name="Ada Lovelace",
        cabin_class="economy",
        price_usd=499.50,
        departure_date=future,
        return_date=later,
    )
    assert booking.flight_id == "AA100"
    assert booking.price_usd == 499.50
    assert booking.return_date == later


def test_negative_price_rejected(load_listing) -> None:
    """price_usd=-150 raises ValidationError from price_must_be_positive."""
    module = load_listing("08-04-semantic-validator")
    future = date.today() + timedelta(days=30)
    with pytest.raises(ValidationError) as exc_info:
        module.FlightBookingOutput(
            flight_id="AA100",
            passenger_name="Ada Lovelace",
            cabin_class="economy",
            price_usd=-150.0,
            departure_date=future,
        )
    assert "price_usd must be positive" in str(exc_info.value)


def test_past_departure_rejected(load_listing) -> None:
    """departure_date in the past raises ValidationError."""
    module = load_listing("08-04-semantic-validator")
    past = date.today() - timedelta(days=1)
    with pytest.raises(ValidationError) as exc_info:
        module.FlightBookingOutput(
            flight_id="AA100",
            passenger_name="Ada Lovelace",
            cabin_class="economy",
            price_usd=499.50,
            departure_date=past,
        )
    assert "is in the past" in str(exc_info.value)


def test_return_before_or_equal_departure_rejected(load_listing) -> None:
    """return_date on or before departure_date raises via the model_validator."""
    module = load_listing("08-04-semantic-validator")
    future = date.today() + timedelta(days=30)

    # Return strictly before departure.
    with pytest.raises(ValidationError) as exc_info:
        module.FlightBookingOutput(
            flight_id="AA100",
            passenger_name="Ada Lovelace",
            cabin_class="economy",
            price_usd=499.50,
            departure_date=future,
            return_date=future - timedelta(days=1),
        )
    assert "must be after departure_date" in str(exc_info.value)

    # Return equal to departure.
    with pytest.raises(ValidationError) as exc_info:
        module.FlightBookingOutput(
            flight_id="AA100",
            passenger_name="Ada Lovelace",
            cabin_class="economy",
            price_usd=499.50,
            departure_date=future,
            return_date=future,
        )
    assert "must be after departure_date" in str(exc_info.value)
