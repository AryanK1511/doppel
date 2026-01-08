import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent import BasicAgent
from agent_executor import BasicAgentExecutor


def main():
    skill = AgentSkill(
        id="hello-world",
        name="Greet",
        description="Return a greeting",
        tags=["greeting", "hello", "world"],
        examples=[
            "Hello",
            "Hello, how are you?",
            "Hello, how can I help you today?",
        ],
    )

    agent_card = AgentCard(
        name="basic-agent",
        description="A simple agent that returns a greeting",
        url="http://localhost:8000/",
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[skill],
        version="0.1.0",
        capabilities=AgentCapabilities(),
    )

    request_handler = DefaultRequestHandler(
        agent_executor=BasicAgentExecutor(BasicAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
