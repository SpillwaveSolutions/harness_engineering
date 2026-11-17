# Travel-booking tools in LangChain Deep Agents.
# These take kwargs. The SDK tools in 17-04 take one args dict.

from deepagents import create_deep_agent


async def search_flights(
    origin: str, destination: str, date: str
) -> dict:
    """Search flights. Offline reference, no network."""
    return {
        "status": "offline",
        "reference": "OFFLINE-SEARCH",
        "origin": origin,
        "destination": destination,
        "date": date,
    }


async def book_flight(
    flight_id: str, passenger_name: str
) -> dict:
    """Book a flight. Offline reference, no network."""
    return {
        "status": "offline",
        "reference": "OFFLINE-BOOKING",
        "flight_id": flight_id,
        "passenger_name": passenger_name,
    }


agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",    # ①
    tools=[search_flights, book_flight],    # ②
    system_prompt="You are a travel-booking assistant...",
)

# Swap model provider without changing any other code:
# model="openai:gpt-4o" works here — same tool definitions, same prompt
