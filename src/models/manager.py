import json
from typing import Any

from smolagents import CodeAgent, OpenAIModel

from ..tasks.router import TaskRouter, TaskType


class ManagerAgent:
    def __init__(self, model: OpenAIModel):
        self.model = model
        self.router = TaskRouter()
        self._agent = CodeAgent(
            model=model,
            tools=[],
            description="Manager agent for label evaluation orchestration",
        )

    def analyze_dataset(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        task_types: dict[str, int] = {}
        difficulty_dist: dict[str, int] = {"low": 0, "medium": 0, "high": 0}

        for item in items:
            task_type = self.router.detect_task_type(item)
            difficulty = self.router.estimate_difficulty(item)

            type_name = task_type.value
            task_types[type_name] = task_types.get(type_name, 0) + 1

            if difficulty < 0.4:
                difficulty_dist["low"] += 1
            elif difficulty < 0.7:
                difficulty_dist["medium"] += 1
            else:
                difficulty_dist["high"] += 1

        return {
            "total_items": len(items),
            "task_types": task_types,
            "difficulty_distribution": difficulty_dist,
        }

    def plan_evaluation(self, dataset_info: dict[str, Any]) -> dict[str, Any]:
        task_types = dataset_info.get("task_types", {})
        difficulty_dist = dataset_info.get("difficulty_distribution", {})

        strategy = f"Process items by task type. "
        if "classification" in task_types:
            strategy += "Use majority voting for classification. "
        if "translation_choice" in task_types:
            strategy += "Allow discussion rounds for translation choice. "
        if "keyword_extraction" in task_types:
            strategy += "Take union of extracted keywords. "
        if difficulty_dist.get("high", 0) > 0:
            strategy += f"Assign more workers ({4-5}) to high-difficulty items."

        return {"strategy": strategy, "estimated_rounds": 2}

    def determine_group_size(self, item: dict[str, Any]) -> int:
        task_type = self.router.detect_task_type(item)
        difficulty = self.router.estimate_difficulty(item)
        return self.router.suggest_group_size(difficulty, task_type)

    def tie_break(
        self,
        item: dict[str, Any],
        evaluations: list[dict[str, Any]],
        discussion: list[dict[str, Any]],
    ) -> dict[str, Any]:
        prompt = f"""As the manager, resolve the disagreement for this item.

Item: {item.get('id', 'unknown')}
Text: {item.get('text', '')}
Current Labels: {item.get('labels', {})}

Worker Evaluations:
{json.dumps(evaluations, indent=2)}

Discussion History:
{json.dumps(discussion, indent=2)}

Make a final decision on the correct labels. Output JSON with final_label and reasoning."""

        response = self._agent.run(prompt)
        return self._parse_tie_break(response, item)

    def _parse_tie_break(
        self, response: str, item: dict[str, Any]
    ) -> dict[str, Any]:
        import re

        labels = item.get("labels", {})

        try:
            import json

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if "final_label" in parsed:
                    labels = parsed["final_label"]
                    reasoning = parsed.get("reasoning", "")
                else:
                    labels = parsed
                    reasoning = response
            else:
                reasoning = response
        except Exception:
            reasoning = response

        return {"labels": labels, "reasoning": reasoning, "resolved_by": "manager"}