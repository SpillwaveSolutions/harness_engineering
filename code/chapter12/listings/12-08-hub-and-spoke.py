import asyncio
import json
import os
import sys
from dataclasses import dataclass

from a2a.client import Client as A2AClient
from anthropic import Anthropic


@dataclass
class SpokeResult:
    spoke_name: str
    artifacts: dict
    task_id: str


class TravelCoordinator:
    """Hub agent: decomposes travel requests and delegates to spoke agents."""

    def __init__(self, flight_client: A2AClient, loyalty_client: A2AClient):
        self.flight_client = flight_client      # ① flight-search spoke
        self.loyalty_client = loyalty_client    # ② hotel-loyalty spoke
        if os.environ.get("ANTHROPIC_API_KEY"):
            self.llm = Anthropic()
        else:
            print(
                "ANTHROPIC_API_KEY is unset; hub synthesis stays offline.",
                file=sys.stderr,
            )
            self.llm = None

    async def handle_request(self, user_request: str, account_id: str) -> dict:
        # Orchestration logic: decide which spokes to call, in parallel
        flight_task = self._delegate_flight_search(user_request)
        loyalty_task = self._delegate_loyalty_check(account_id)

        results = await asyncio.gather(flight_task, loyalty_task)

        # Synthesis: hub owns the merge
        return self._synthesize(results, user_request)   # ③

    async def _delegate_flight_search(self, request: str) -> SpokeResult:
        return SpokeResult(
            spoke_name="flight-search",
            artifacts={"request": request, "status": "offline"},
            task_id="offline-flight",
        )

    async def _delegate_loyalty_check(self, account_id: str) -> SpokeResult:
        return SpokeResult(
            spoke_name="hotel-loyalty",
            artifacts={"account_id": account_id, "status": "offline"},
            task_id="offline-loyalty",
        )

    def _synthesize(self, results: list[SpokeResult], request: str) -> dict:
        return {
            "request": request,
            "status": "ok",
            "spokes": [
                {
                    "name": item.spoke_name,
                    "task_id": item.task_id,
                    "artifacts": item.artifacts,
                }
                for item in results
            ],
        }


def main() -> int:
    coordinator = TravelCoordinator(
        flight_client=object(),
        loyalty_client=object(),
    )
    result = asyncio.run(
        coordinator.handle_request("SFO next week", "ACC123")
    )
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
