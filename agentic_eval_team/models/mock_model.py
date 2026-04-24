from smolagents.models import Model, ChatMessage
from typing import Any


class MockModel(Model):
    def __init__(self, responses: dict[str, str] | None = None):
        self.responses = responses or {}
        self.call_count = 0

    def generate(self, messages: list[ChatMessage], **kwargs) -> ChatMessage:
        self.call_count += 1

        last_message = messages[-1].content if messages else ""

        if isinstance(last_message, list):
            last_message = " ".join(m.get("text", "") for m in last_message if isinstance(m, dict))

        if "tie_break" in last_message.lower() or "manager" in last_message.lower():
            return ChatMessage(
                role="assistant",
                content='Thoughts: Making final decision based on evaluations\n<code>\nresult = {"final_labels": {"category": "reviewed", "sentiment": "neutral"}, "reasoning": "Mock manager tie-break", "confidence": 0.8}\nprint(result)\n</code>'
            )

        if "disagree" in last_message.lower() or "another worker" in last_message.lower():
            return ChatMessage(
                role="assistant",
                content='Thoughts: I agree with the evaluation\n<code>\nresult = {"stance": "agree", "reasoning": "Mock agreement"}\nprint(result)\n</code>'
            )

        return ChatMessage(
            role="assistant",
            content='Thoughts: Evaluated the labels\n<code>\nresult = {"evaluation": "correct", "reasoning": "Mock evaluation - labels appear accurate", "suggested_changes": {}, "confidence": 0.9}\nprint(result)\n</code>'
        )

    def __call__(self, *args, **kwargs):
        return self.generate(*args, **kwargs)