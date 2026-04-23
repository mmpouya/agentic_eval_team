import json
import random
from typing import Any

from smolagents import CodeAgent, OpenAIModel

from .schema import DataItem, EvaluationPlan, TaskConfig
from .tools import assess_difficulty, plan_evaluation_strategy, create_worker


class ManagerAgent:
    def __init__(self, model: OpenAIModel, task_config: TaskConfig):
        self.model = model
        self.task_config = task_config
        self._tools = [assess_difficulty, plan_evaluation_strategy]
        self._agent = CodeAgent(
            model=model,
            tools=self._tools,
            description="Manager agent for label evaluation orchestration",
            planning_interval=5,
        )
        self._workers: dict[int, Any] = {}
        self._evaluation_plan: EvaluationPlan | None = None

    def analyze_and_plan(self, items: list[DataItem]) -> dict[str, Any]:
        samples = self._sample_items(items, 5)
        task_description = self.task_config.description

        difficulty_result = assess_difficulty(samples, task_description)

        dataset_summary = {
            "total_items": len(items),
            "sample_size": len(samples),
        }

        plan_result = plan_evaluation_strategy(dataset_summary, difficulty_result, self.task_config)

        self._evaluation_plan = plan_result

        return {
            "difficulty_assessment": difficulty_result,
            "evaluation_plan": plan_result.model_dump(),
        }

    def create_workers(self, model: OpenAIModel) -> dict[int, Any]:
        if not self._evaluation_plan:
            raise ValueError("Must call analyze_and_plan before create_workers")

        for config in self._evaluation_plan.worker_agents:
            worker = create_worker(
                model=model,
                agent_id=config["agent_id"],
                role=config["role"],
                focus=config["focus"],
                evaluation_instructions=config["instructions"],
            )
            self._workers[config["agent_id"]] = worker

        return self._workers

    def get_consensus_strategy(self) -> str:
        if not self._evaluation_plan:
            return "discussion_then_vote"
        return self._evaluation_plan.consensus_strategy

    def get_max_rounds(self) -> int:
        if not self._evaluation_plan:
            return 2
        return self._evaluation_plan.max_discussion_rounds

    def get_worker_configs(self) -> list[dict[str, Any]]:
        if not self._evaluation_plan:
            return []
        return self._evaluation_plan.worker_agents

    def tie_break(
        self,
        item: DataItem,
        evaluations: list[dict[str, Any]],
        discussion: list[dict[str, Any]],
    ) -> dict[str, Any]:
        prompt = f"""As the manager, resolve the disagreement for this item.

Item ID: {item.id}
Text: {item.text}
Current Labels: {json.dumps(item.labels, indent=2)}

Worker Evaluations:
{json.dumps(evaluations, indent=2)}

Discussion History:
{json.dumps(discussion, indent=2)}

Task: {self.task_config.description}

Evaluate the arguments and make a final decision. Output JSON with:
- final_labels: The corrected labels
- reasoning: Why this decision was made
- confidence: Your confidence level (0.0-1.0)"""

        response = self._agent.run(prompt)
        return self._parse_tie_break_response(response, item)

    def _parse_tie_break_response(self, response: str, item: DataItem) -> dict[str, Any]:
        import re

        labels = item.labels

        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if "final_labels" in parsed:
                    labels = parsed["final_labels"]
                    reasoning = parsed.get("reasoning", "")
                    confidence = parsed.get("confidence", 0.5)
                elif "final_label" in parsed:
                    labels = parsed["final_label"]
                    reasoning = parsed.get("reasoning", "")
                    confidence = parsed.get("confidence", 0.5)
                else:
                    labels = parsed
                    reasoning = response
                    confidence = 0.5
            else:
                reasoning = response
                confidence = 0.5
        except Exception:
            reasoning = response
            confidence = 0.5

        return {
            "labels": labels,
            "reasoning": reasoning,
            "confidence": confidence,
            "resolved_by": "manager",
        }

    @staticmethod
    def _sample_items(items: list[DataItem], n: int) -> list[DataItem]:
        if len(items) <= n:
            return items
        return random.sample(items, n)