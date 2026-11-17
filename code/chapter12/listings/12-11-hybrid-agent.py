from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# MCP surface: serves tool-calling callers (sub-second deterministic ops)
mcp = FastMCP("HotelLoyaltyMCP")


@mcp.tool()
def get_loyalty_balance(account_id: str) -> dict:
    """Fast deterministic lookup -- no LLM reasoning."""
    return {
        "account_id": account_id,
        "points": 0,
        "tier": "unknown",
        "status": "offline",
    }


# A2A surface: serves peer agents delegating reasoning tasks.
def build_a2a_app(agent_card, executor) -> FastAPI:
    app = FastAPI()
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(agent_card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )
    return app


# Mount both on the same FastAPI app -- separate path prefixes
def create_hybrid_server(agent_card, executor) -> FastAPI:
    app = FastAPI()
    app.mount("/mcp", mcp.sse_app())               # ① MCP at /mcp
    app.mount("/a2a", build_a2a_app(agent_card, executor))  # ② A2A at /a2a
    return app


def main() -> int:
    balance = get_loyalty_balance("ACC123")
    print(balance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
