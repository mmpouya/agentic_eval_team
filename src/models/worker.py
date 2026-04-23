import time
from smolagents import CodeAgent

from .schema import DataItem, TaskConfig
from .mock_model import MockModel


def _get_api_exceptions():
    try:
        from openai import APIError as OpenAIAPIError
        from httpx import ConnectError, ReadTimeout
        return (OpenAIAPIError, ConnectError, ReadTimeout, Exception)
    except ImportError:
        return (Exception,)


class WorkerAgent:
    def __init__(
        self,
        agent: CodeAgent | MockModel,
        agent_id: int,
        role: str,
        focus: str,
        evaluation_instructions: str,
        task_config: TaskConfig,
        max_retries: int = 3,
    ):
        self._agent = agent
        self.agent_id = agent_id
        self.role = role
        self.focus = focus
        self.evaluation_instructions = evaluation_instructions
        self.task_config = task_config
        self.max_retries = max_retries

    def evaluate(self, item: DataItem) -> dict:
        criteria = ", ".join(self.task_config.evaluation_criteria)

        prompt = f"""You are Worker {self.agent_id}, a {self.role}.
Focus: {self.focus}

Task: {self.task_config.description}
Evaluation Criteria: {criteria}

{self.evaluation_instructions}

Data Item:
- ID: {item.id}
- Text: {item.text}
- Labels: {item.labels}

Provide your evaluation in JSON format with these exact keys:
{{"evaluation": "correct" or "incorrect" or "needs_revision", "reasoning": "...", "suggested_changes": {{...}}, "confidence": 0.0-1.0}}"""

        return self._call_with_retry(self._agent.run, prompt)

    def _call_with_retry(self, func, *args, **kwargs):
        delay = 1.0
        exceptions = _get_api_exceptions()
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = func(*args, **kwargs)
                if isinstance(response, dict):
                    return response
                return self._parse_response(response)
            except exceptions as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(delay)
                    delay *= 2
                else:
                    return self._fallback_response(str(last_error))

        return self._fallback_response(str(last_error))

    def _parse_response(self, response: str) -> dict:
        import json
        import re

        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                result["worker_id"] = self.agent_id
                result["role"] = self.role
                return result
            except json.JSONDecodeError:
                pass

        return {
            "evaluation": "needs_revision",
            "reasoning": response,
            "suggested_changes": {},
            "confidence": 0.5,
            "worker_id": self.agent_id,
            "role": self.role,
        }

    def _fallback_response(self, error_message: str) -> dict:
        return {
            "evaluation": "needs_revision",
            "reasoning": f"Error during evaluation: {error_message}",
            "suggested_changes": {},
            "confidence": 0.0,
            "worker_id": self.agent_id,
            "role": self.role,
            "error": error_message,
        }

    def discuss(self, other_evaluation: dict, item: DataItem) -> dict:
        prompt = f"""You are Worker {self.agent_id}, a {self.role}.

Another worker has provided this evaluation:
{other_evaluation}

Do you agree or disagree with this evaluation? Consider your role as a {self.role} with focus on {self.focus}.

Provide your stance and reasoning."""

        response = self._call_with_retry(self._agent.run, prompt)
        return {
            "worker_id": self.agent_id,
            "role": self.role,
            "stance": "agree" if "agree" in response.get("reasoning", "").lower() else "disagree",
            "reasoning": response.get("reasoning", ""),
        }