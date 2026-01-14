from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Literal

from src.core.agents.candidate_agent import CandidateAgent
from src.core.agents.recruiter_agent import RecruiterAgent


@dataclass
class ConversationTurn:
    role: Literal["recruiter", "candidate"]
    speaker_name: str
    content: str
    timestamp: str
    is_final: bool = False
    final_evaluation: str | None = None


@dataclass
class ConversationResult:
    conversation_history: list[dict[str, str]]
    final_evaluation: str
    total_turns: int
    match_score: int | None = None
    decision: str | None = None


class ConversationOrchestrator:
    def __init__(self, recruiter: RecruiterAgent, candidate: CandidateAgent):
        self.recruiter = recruiter
        self.candidate = candidate
        self.conversation_history: list[dict[str, str]] = []

    def _parse_evaluation(self, evaluation: str) -> tuple[int | None, str | None]:
        score = None
        decision = None

        if "Rating:" in evaluation:
            try:
                rating_part = evaluation.split("Rating:")[1].split("/")[0].strip()
                score = int(rating_part)
            except (IndexError, ValueError):
                pass

        if "GOOD FIT" in evaluation.upper():
            decision = "GOOD FIT"
        elif "NOT A FIT" in evaluation.upper():
            decision = "NOT A FIT"

        return score, decision

    async def run_conversation_stream(
        self, max_turns: int = 12
    ) -> AsyncGenerator[ConversationTurn, None]:
        turn_count = 0

        recruiter_response = await self.recruiter.respond(self.conversation_history)

        if recruiter_response.is_final_response:
            self.conversation_history.append(
                {"role": "recruiter", "content": recruiter_response.response}
            )
            yield ConversationTurn(
                role="recruiter",
                speaker_name=self.recruiter.name,
                content=recruiter_response.response,
                timestamp=datetime.utcnow().isoformat(),
                is_final=True,
                final_evaluation=recruiter_response.final_evaluation,
            )
            return

        self.conversation_history.append(
            {"role": "recruiter", "content": recruiter_response.response}
        )
        yield ConversationTurn(
            role="recruiter",
            speaker_name=self.recruiter.name,
            content=recruiter_response.response,
            timestamp=datetime.utcnow().isoformat(),
        )

        while turn_count < max_turns:
            candidate_response = await self.candidate.respond(self.conversation_history)
            self.conversation_history.append(
                {"role": "candidate", "content": candidate_response}
            )
            yield ConversationTurn(
                role="candidate",
                speaker_name=self.candidate.name,
                content=candidate_response,
                timestamp=datetime.utcnow().isoformat(),
            )
            turn_count += 1

            recruiter_response = await self.recruiter.respond(self.conversation_history)

            if recruiter_response.is_final_response:
                self.conversation_history.append(
                    {"role": "recruiter", "content": recruiter_response.response}
                )
                yield ConversationTurn(
                    role="recruiter",
                    speaker_name=self.recruiter.name,
                    content=recruiter_response.response,
                    timestamp=datetime.utcnow().isoformat(),
                    is_final=True,
                    final_evaluation=recruiter_response.final_evaluation,
                )
                return

            self.conversation_history.append(
                {"role": "recruiter", "content": recruiter_response.response}
            )
            yield ConversationTurn(
                role="recruiter",
                speaker_name=self.recruiter.name,
                content=recruiter_response.response,
                timestamp=datetime.utcnow().isoformat(),
            )

        self.conversation_history.append(
            {"role": "system", "content": "Please provide your final evaluation now."}
        )
        final_response = await self.recruiter.respond(self.conversation_history)
        self.conversation_history.append(
            {"role": "recruiter", "content": final_response.response}
        )
        yield ConversationTurn(
            role="recruiter",
            speaker_name=self.recruiter.name,
            content=final_response.response,
            timestamp=datetime.utcnow().isoformat(),
            is_final=True,
            final_evaluation=final_response.final_evaluation,
        )

    async def run_conversation(self, max_turns: int = 12) -> ConversationResult:
        final_evaluation = ""

        async for turn in self.run_conversation_stream(max_turns):
            if turn.is_final and turn.final_evaluation:
                final_evaluation = turn.final_evaluation

        score, decision = self._parse_evaluation(final_evaluation)

        return ConversationResult(
            conversation_history=self.conversation_history,
            final_evaluation=final_evaluation,
            total_turns=len(
                [msg for msg in self.conversation_history if msg["role"] == "candidate"]
            ),
            match_score=score,
            decision=decision,
        )
