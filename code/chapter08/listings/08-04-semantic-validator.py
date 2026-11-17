from datetime import date

from pydantic import BaseModel, field_validator, model_validator


class FlightBookingOutput(BaseModel):
    flight_id: str
    passenger_name: str
    cabin_class: str
    price_usd: float
    departure_date: date
    return_date: date | None = None

    @field_validator("price_usd")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"price_usd must be positive, got {v}")
        return v

    @field_validator("departure_date")
    @classmethod
    def departure_must_be_future(cls, v: date) -> date:
        if v < date.today():
            raise ValueError(f"departure_date {v} is in the past")
        return v

    @model_validator(mode="after")
    def return_after_departure(self) -> "FlightBookingOutput":
        if self.return_date and self.return_date <= self.departure_date:
            raise ValueError(
                f"return_date {self.return_date} must be after "
                f"departure_date {self.departure_date}"
            )
        return self


def main() -> None:
    from datetime import timedelta

    future = date.today() + timedelta(days=30)
    booking = FlightBookingOutput(
        flight_id="AA100",
        passenger_name="Ada Lovelace",
        cabin_class="economy",
        price_usd=499.50,
        departure_date=future,
    )
    print(booking.flight_id)


if __name__ == "__main__":
    main()
