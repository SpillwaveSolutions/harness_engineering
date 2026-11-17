import os
import sys

from playwright.sync_api import sync_playwright


def verify_booking_ui(flight_id: str, passenger_name: str) -> dict:
    """
    Independent UI verification. Runs out-of-band; the agent never sees these assertions.
    """
    if os.environ.get("HARNESS_LIVE_API") != "1":
        print(
            "offline: HARNESS_LIVE_API is not 1; browser not started",
            file=sys.stderr,
            flush=True,
        )
        return {
            "status": "offline",
            "flight_id": flight_id,
            "passenger_name": passenger_name,
        }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"https://booking.example.com/confirm/{flight_id}")

        # Assert the booking button is enabled (not disabled by async validation)
        confirm_btn = page.locator("[data-testid='confirm-booking']")
        assert not confirm_btn.get_attribute("disabled"), \
            "Booking button disabled — async validation failed"                # ①

        # Assert the correct POST fires on click
        with page.expect_request("**/api/bookings") as request_info:
            confirm_btn.click()
        request = request_info.value
        assert request.method == "POST", "Expected POST to /api/bookings"       # ②

        # Assert no console errors
        errors = []
        page.on("console", lambda msg: errors.append(msg.text)
                if msg.type == "error" else None)
        assert not errors, f"Console errors: {errors}"                          # ③

        browser.close()
        return {"status": "pass", "flight_id": flight_id}
