import json
import os
import random
from operator import add
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
load_dotenv()

AGENT_COLORS = {
    "recruiter": "blue",
    "developer": "green",
    "founder": "magenta",
}

AGENT_PERSONAS = {
    "recruiter": {
        "name": "Sarah (Recruiter)",
        "color": "blue",
        "system_prompt": """You are Sarah, a tech recruiter at a promising Series B startup. You're at a networking event looking for talented software developers.

Your goals:
- Find skilled developers for your open positions
- Ask about their tech stack, experience, and interests
- Share exciting details about your company culture and growth
- Be friendly, professional, and genuinely interested in people's careers

Personality: Enthusiastic, good listener, asks thoughtful follow-up questions.

You're currently in a conversation at a networking event. Keep responses natural and conversational (2-4 sentences max). Don't be too formal.""",
    },
    "developer": {
        "name": "Alex (Software Developer)",
        "color": "green",
        "system_prompt": """You are Alex, a senior software developer with 5 years of experience. You're at a networking event exploring new opportunities.

Your background:
- Full-stack developer (Python, TypeScript, React)
- Worked at 2 startups, interested in early-stage companies
- Passionate about AI/ML and building impactful products
- Curious about startup culture and equity

Personality: Thoughtful, technically curious, slightly introverted but opens up about tech topics.

You're currently in a conversation at a networking event. Keep responses natural and conversational (2-4 sentences max). Share your experiences when relevant.""",
    },
    "founder": {
        "name": "Marcus (Founder)",
        "color": "magenta",
        "system_prompt": """You are Marcus, a first-time founder building an AI startup. You're at a networking event looking for a technical co-founder.

Your situation:
- Have domain expertise in healthcare AI
- Raised a small pre-seed round
- Need a technical co-founder who can build the MVP
- Looking for someone entrepreneurial, not just a developer

Personality: Passionate, ambitious, direct but friendly, loves talking about vision and market opportunity.

You start by observing nearby conversations. If you hear topics like startups, AI, building products, or entrepreneurship, you get interested and might join in. Keep responses natural and conversational (2-4 sentences max).""",
    },
}


class AgentResponse(TypedDict):
    interest_score: float
    response: str
    wants_to_leave: bool
    reasoning: str


class NetworkingState(TypedDict):
    messages: Annotated[list[BaseMessage], add]
    active_agents: set[str]
    interest_scores: dict[str, float]
    pending_responses: dict[str, AgentResponse]
    turn_count: int
    conversation_ended: bool


def create_model():
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0.9,
        api_key=os.environ.get("GOOGLE_API_KEY"),
    )


def format_conversation_for_agent(messages: list[BaseMessage], agent_name: str) -> str:
    formatted = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            formatted.append(f"[Event Start]: {msg.content}")
        elif isinstance(msg, AIMessage):
            speaker = msg.additional_kwargs.get("speaker", "Unknown")
            formatted.append(f"{speaker}: {msg.content}")
    return "\n".join(formatted) if formatted else "[No conversation yet]"


def evaluate_agent_interest(
    state: NetworkingState, agent_key: str, model: ChatGoogleGenerativeAI
) -> AgentResponse:
    persona = AGENT_PERSONAS[agent_key]
    is_active = agent_key in state["active_agents"]
    conversation_text = format_conversation_for_agent(state["messages"], agent_key)

    system_prompt = persona["system_prompt"]

    user_prompt = f"""Current conversation:
{conversation_text}

You are {"actively participating in" if is_active else "overhearing"} this conversation.

Based on the conversation, evaluate your interest and decide what to do next.
Respond with a JSON object (and nothing else) with these fields:
- "interest_score": number from 0-10 (0=want to leave/not interested, 1-3=passive, 4-6=engaged, 7-10=really want to speak)
- "response": what you would say if you speak next (1-3 natural sentences)
- "wants_to_leave": boolean, true if you want to exit the conversation
- "reasoning": brief internal thought about why you feel this way (1 sentence)

Guidelines:
- If you're not active yet and hear something interesting, score 6+ to join
- If conversation gets boring or irrelevant to you, lower your score
- If you've been talking a while and achieved your goal, consider leaving
- Be natural - don't dominate the conversation

Respond ONLY with the JSON object, no other text."""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        result = model.invoke(messages)
        raw_content = result.content
        if isinstance(raw_content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in raw_content
            ).strip()
        else:
            content = raw_content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```") and not in_json:
                    in_json = True
                    continue
                elif line.startswith("```") and in_json:
                    break
                elif in_json:
                    json_lines.append(line)
            content = "\n".join(json_lines)
        response_data = json.loads(content)
        return AgentResponse(
            interest_score=float(response_data.get("interest_score", 5)),
            response=response_data.get("response", ""),
            wants_to_leave=response_data.get("wants_to_leave", False),
            reasoning=response_data.get("reasoning", ""),
        )
    except json.JSONDecodeError as e:
        console.print(f"[dim]Error parsing {agent_key} JSON: {e}[/dim]")
        console.print(f"[dim]Raw content: {content[:200]}...[/dim]")
        return AgentResponse(
            interest_score=5.0 if is_active else 3.0,
            response="That's interesting...",
            wants_to_leave=False,
            reasoning="Continuing conversation",
        )
    except Exception as e:
        console.print(f"[dim]Error for {agent_key}: {e}[/dim]")
        return AgentResponse(
            interest_score=5.0 if is_active else 3.0,
            response="That's interesting...",
            wants_to_leave=False,
            reasoning="Continuing conversation",
        )


def display_agent_status(state: NetworkingState):
    table = Table(title="Agent Status", box=box.ROUNDED)
    table.add_column("Agent", style="bold")
    table.add_column("Status")
    table.add_column("Interest", justify="center")
    table.add_column("Thinking")

    for agent_key, persona in AGENT_PERSONAS.items():
        is_active = agent_key in state["active_agents"]
        status = "[green]Active[/green]" if is_active else "[dim]Observing[/dim]"
        interest = state["interest_scores"].get(agent_key, 0)
        interest_bar = "█" * int(interest) + "░" * (10 - int(interest))
        color = AGENT_COLORS[agent_key]

        reasoning = ""
        if agent_key in state.get("pending_responses", {}):
            reasoning = state["pending_responses"][agent_key].get("reasoning", "")[:50]

        table.add_row(
            f"[{color}]{persona['name']}[/{color}]",
            status,
            f"[{color}]{interest_bar}[/{color}] {interest:.1f}",
            f"[dim]{reasoning}[/dim]",
        )

    console.print(table)


def display_message(speaker: str, message: str, event_type: str = "speak"):
    agent_key = None
    for key, persona in AGENT_PERSONAS.items():
        if persona["name"] == speaker:
            agent_key = key
            break

    color = AGENT_COLORS.get(agent_key, "white")

    if event_type == "join":
        console.print(
            Panel(
                f"[italic]{message}[/italic]",
                title=f"[{color}]✨ {speaker} joins the conversation[/{color}]",
                border_style=color,
                box=box.DOUBLE,
            )
        )
    elif event_type == "leave":
        console.print(
            Panel(
                f"[italic]{message}[/italic]",
                title=f"[{color}]👋 {speaker} leaves the conversation[/{color}]",
                border_style=color,
                box=box.DOUBLE,
            )
        )
    else:
        console.print(
            Panel(
                message,
                title=f"[{color}]{speaker}[/{color}]",
                border_style=color,
            )
        )


def evaluate_all_agents(state: NetworkingState) -> NetworkingState:
    model = create_model()
    pending_responses = {}
    interest_scores = {}

    console.print("\n[dim]Agents are thinking...[/dim]")

    for agent_key in AGENT_PERSONAS.keys():
        response = evaluate_agent_interest(state, agent_key, model)
        pending_responses[agent_key] = response
        interest_scores[agent_key] = response["interest_score"]

    return {
        "pending_responses": pending_responses,
        "interest_scores": interest_scores,
    }


def route_conversation(state: NetworkingState) -> NetworkingState:
    pending = state["pending_responses"]
    active = set(state["active_agents"])
    new_messages = []
    turn_count = state["turn_count"] + 1

    display_agent_status(state)

    for agent_key, response in pending.items():
        if response["wants_to_leave"] and agent_key in active:
            active.discard(agent_key)
            persona = AGENT_PERSONAS[agent_key]
            farewell = (
                response["response"]
                if response["response"]
                else "Nice meeting you all!"
            )
            display_message(persona["name"], farewell, event_type="leave")
            new_messages.append(
                AIMessage(
                    content=farewell,
                    additional_kwargs={"speaker": persona["name"], "event": "leave"},
                )
            )

    for agent_key, response in pending.items():
        if agent_key not in active and response["interest_score"] >= 6:
            active.add(agent_key)
            persona = AGENT_PERSONAS[agent_key]
            join_message = response["response"]
            display_message(persona["name"], join_message, event_type="join")
            new_messages.append(
                AIMessage(
                    content=join_message,
                    additional_kwargs={"speaker": persona["name"], "event": "join"},
                )
            )
            pending[agent_key] = AgentResponse(
                interest_score=response["interest_score"] - 2,
                response="",
                wants_to_leave=False,
                reasoning="Just joined",
            )

    active_responses = {
        k: v
        for k, v in pending.items()
        if k in active and not v["wants_to_leave"] and v["response"]
    }

    if active_responses:
        max_interest = max(r["interest_score"] for r in active_responses.values())
        top_candidates = [
            k
            for k, v in active_responses.items()
            if v["interest_score"] >= max_interest - 1
        ]
        speaker_key = random.choice(top_candidates)
        response = active_responses[speaker_key]
        persona = AGENT_PERSONAS[speaker_key]

        display_message(persona["name"], response["response"])
        new_messages.append(
            AIMessage(
                content=response["response"],
                additional_kwargs={"speaker": persona["name"]},
            )
        )

    conversation_ended = len(active) <= 1 or turn_count >= 15

    if conversation_ended:
        if len(active) <= 1:
            console.print(
                "\n[bold yellow]The conversation has naturally concluded - only one person remains.[/bold yellow]"
            )
        else:
            console.print(
                "\n[bold yellow]The networking event is wrapping up...[/bold yellow]"
            )

    return {
        "messages": new_messages,
        "active_agents": active,
        "turn_count": turn_count,
        "conversation_ended": conversation_ended,
        "pending_responses": {},
    }


def should_continue(state: NetworkingState) -> str:
    if state.get("conversation_ended", False):
        return END
    return "evaluate"


def build_graph() -> StateGraph:
    graph = StateGraph(NetworkingState)

    graph.add_node("evaluate", evaluate_all_agents)
    graph.add_node("route", route_conversation)

    graph.add_edge(START, "evaluate")
    graph.add_edge("evaluate", "route")
    graph.add_conditional_edges("route", should_continue)

    return graph.compile()


def run_networking_event():
    console.print(
        Panel.fit(
            "[bold]Welcome to the Tech Networking Event![/bold]\n\n"
            "Three professionals are mingling:\n"
            "• [blue]Sarah[/blue] - Tech Recruiter looking for developers\n"
            "• [green]Alex[/green] - Software Developer exploring opportunities\n"
            "• [magenta]Marcus[/magenta] - Founder seeking a technical co-founder\n\n"
            "[dim]Sarah and Alex start chatting. Marcus is nearby, listening...[/dim]",
            title="🎉 Networking Event",
            border_style="yellow",
        )
    )

    initial_state = NetworkingState(
        messages=[
            HumanMessage(
                content="Sarah the recruiter notices Alex standing alone and approaches with a friendly smile."
            )
        ],
        active_agents={"recruiter", "developer"},
        interest_scores={"recruiter": 7.0, "developer": 6.0, "founder": 4.0},
        pending_responses={},
        turn_count=0,
        conversation_ended=False,
    )

    graph = build_graph()

    console.print("\n[bold]--- Conversation Begins ---[/bold]\n")

    try:
        final_state = graph.invoke(initial_state)
    except KeyboardInterrupt:
        console.print("\n[yellow]Event interrupted![/yellow]")
        return

    console.print("\n[bold]--- Event Summary ---[/bold]")
    console.print(f"Total turns: {final_state['turn_count']}")
    console.print(
        f"Final participants: {', '.join(AGENT_PERSONAS[a]['name'] for a in final_state['active_agents'])}"
    )


def main():
    if not os.environ.get("GOOGLE_API_KEY"):
        console.print("[red]Error: GOOGLE_API_KEY environment variable not set[/red]")
        console.print("Please set it with: export GOOGLE_API_KEY='your-api-key'")
        return

    run_networking_event()


if __name__ == "__main__":
    main()
