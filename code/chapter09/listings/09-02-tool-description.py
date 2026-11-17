SEARCH_FLIGHTS_DESCRIPTION = """
Search available flights matching the given criteria.

Use this tool when the user wants to find flights between two airports
on a specific date. Accepts IATA airport codes (e.g., JFK, LHR) and
ISO-8601 dates (YYYY-MM-DD). Returns a list of flights sorted by
departure time with price, duration, and cabin class.

Use search_loyalty_history instead if the user is asking about past
bookings, earned miles, or account history. This tool only surfaces
available future flights -- it has no visibility into account data.

Example: search_flights(origin="JFK", destination="LHR",
                        date="2026-09-15", cabin_class="economy")
"""

SEARCH_LOYALTY_DESCRIPTION = """
Retrieve a customer's loyalty program history and mile balance.

Use this tool when the user asks about past trips, mile balances,
tier status, or redemption history. Returns a structured record with
total_miles, tier, and a list of recent transactions.

Do NOT use this tool to search for future flights or check availability
-- use search_flights for that. This tool requires an authenticated
session; call get_session_token first if the session field is empty.

Example: search_loyalty_history(customer_id="C-10042", months=6)
"""


def main() -> None:
    print("search_flights" in SEARCH_FLIGHTS_DESCRIPTION)
    print("search_loyalty_history" in SEARCH_LOYALTY_DESCRIPTION)


if __name__ == "__main__":
    main()
