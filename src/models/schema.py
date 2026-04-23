from pydantic import BaseModel, Field
from typing import Any, Literal


class TaskConfig(BaseModel):
    description: str = Field(default="Evaluate labels for accuracy and quality")
    evaluation_criteria: list[str] = Field(default_factory=lambda: ["accuracy", "reasonableness"])
    consensus_strategy: str = Field(default="discussion_then_vote")
    max_discussion_rounds: int = Field(default=2)


class DataItem(BaseModel):
    id: str
    text: str
    labels: dict[str, Any] = Field(default_factory=dict)


class InputData(BaseModel):
    task_config: TaskConfig = Field(default_factory=TaskConfig)
    items: list[DataItem] = Field(default_factory=list)

    @classmethod
    def from_json(cls, json_str: str) -> "InputData":
        import json
        parsed = json.loads(json_str)
        if isinstance(parsed, list):
            return cls(items=[DataItem(**item) for item in parsed])
        return cls(**parsed)


class EvaluationResult(BaseModel):
    evaluation: str
    reasoning: str
    suggested_changes: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.5
    worker_id: int | None = None
    role: str | None = None


class DiscussionResult(BaseModel):
    worker_id: int
    role: str | None = None
    stance: str
    reasoning: str


class ItemEvaluationResult(BaseModel):
    id: str
    text: str
    labels: dict[str, Any]
    evaluation_summary: dict[str, Any]


class EvaluationPlan(BaseModel):
    difficulty_level: str
    reasoning: str
    recommended_strategies: list[str]
    estimated_rounds: int
    worker_agents: list[dict[str, Any]] = Field(default_factory=list)
    consensus_strategy: str
    max_discussion_rounds: int