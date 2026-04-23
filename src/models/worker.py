from smolagents import CodeAgent, OpenAIModel
from typing import Any


class WorkerAgent:
    def __init__(
        self,
        model: OpenAIModel,
        agent_id: int,
        persona: str = "critical_evaluator",
    ):
        self.agent_id = agent_id
        self.persona = persona
        self._agent = CodeAgent(
            model=model,
            tools=[],
            description=f"Worker agent {agent_id} - {persona}",
        )

    def evaluate(self, item: dict[str, Any], task_prompt: str) -> dict[str, Any]:
        evaluation_prompt = f"""You are Worker {self.agent_id}, a {self.persona}.

{task_prompt}

Data to evaluate:
- ID: {item.get('id', 'unknown')}
- Text: {item.get('text', '')}
- Labels: {item.get('labels', {})}

Provide your evaluation focusing on accuracy and quality."""

        response = self._agent.run(evaluation_prompt)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> dict[str, Any]:
        import json
        import re

        json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "evaluation": "needs_revision",
            "reasoning": response,
            "suggested_changes": {},
            "confidence": 0.5,
            "worker_id": self.agent_id,
        }

    def discuss(
        self, other_evaluation: dict[str, Any], item: dict[str, Any]
    ) -> dict[str, Any]:
        discussion_prompt = f"""You are Worker {self.agent_id}, a {self.persona}.

Another worker has provided this evaluation:
{other_evaluation}

Do you agree or disagree? Provide your stance and reasoning."""

        response = self._agent.run(discussion_prompt)
        return {
            "worker_id": self.agent_id,
            "stance": "agree" if "agree" in response.lower() else "disagree",
            "reasoning": response,
        }