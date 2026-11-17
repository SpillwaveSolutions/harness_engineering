from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI
from google.adk.a2a.executor.a2a_agent_executor import (
    A2aAgentExecutor,
    A2aAgentExecutorConfig,
)
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import (
    InMemorySessionService,
)


def create_adk_a2a_server(agent_card):
    """Wrap an ADK agent as an A2A FastAPI app. Not called at import."""
    agent = LlmAgent(
        name="HotelLoyaltyAgent",
        model="gemini-2.0-flash",
        instruction="You look up hotel loyalty status and redemption options.",
    )
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name="HotelLoyaltyAgent",
    )  # ①
    executor = A2aAgentExecutor(                                    # ②
        runner=runner,
        config=A2aAgentExecutorConfig(),
    )
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )  # ③
    app = FastAPI()
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(agent_card),
        jsonrpc_routes=create_jsonrpc_routes(
            request_handler, rpc_url="/"
        ),
    )
    return app  # ④ card is served from the agent-card routes


def main() -> int:
    from a2a.types import (
        AgentCapabilities,
        AgentCard,
        AgentInterface,
        AgentSkill,
    )

    card = AgentCard(
        name="HotelLoyaltyAgent",
        description="Hotel loyalty status and redemption lookup.",
        version="1.2.0",
        supported_interfaces=[
            AgentInterface(
                url="https://loyalty.hotelpartner.com/a2a",
                protocol_binding="JSONRPC",
                protocol_version="1.0.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
        skills=[AgentSkill(
            id="hotel-loyalty-lookup",
            name="Hotel Loyalty Lookup",
            description="Returns points balance and tier for a guest account.",
            tags=["loyalty", "hotel"],
        )],
    )
    app = create_adk_a2a_server(card)
    print(f"routes={len(app.routes)} status=offline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
