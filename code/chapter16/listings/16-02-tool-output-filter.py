import re

from pydantic import BaseModel, field_validator


class FlightSearchResult(BaseModel):
    """Typed output schema for search_flights.

    Only these fields reach the model.
    """
    flight_id: str
    airline: str
    origin: str
    destination: str
    departure_time: str
    price_usd: float

    @field_validator("airline", "origin", "destination", mode="before")
    @classmethod
    def strip_html_and_instructions(cls, v: str) -> str:  # ①
        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", "", str(v))
        # Remove HTML comments (common injection carrier)
        clean = re.sub(r"<!--.*?-->", "", clean, flags=re.DOTALL)
        # Reject inputs that contain instruction-pattern triggers
        INJECTION_PATTERNS = [
            r"\bAGENT\b.*?:",
            r"ignore\s+previous",
            r"remember\s+that",
            r"store\s+this",
        ]
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, clean, re.IGNORECASE):
                raise ValueError(
                    f"Injection pattern detected in field: {pattern}"
                )
        return clean.strip()

def filter_search_flights_output(raw: dict) -> FlightSearchResult:
    """PostToolUse hook: structural-type the raw tool response."""
    return FlightSearchResult(  # ②
        flight_id=raw.get("flights", [{}])[0].get("id", ""),
        airline=raw.get("flights", [{}])[0].get("airline", ""),
        origin=raw.get("origin", ""),
        destination=raw.get("destination", ""),
        departure_time=(
            raw.get("flights", [{}])[0].get("departs", "")
        ),
        price_usd=float(
            raw.get("flights", [{}])[0].get("price", 0.0)
        ),
    )
