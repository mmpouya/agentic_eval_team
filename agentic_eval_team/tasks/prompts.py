from typing import Any


SYSTEM_PROMPT = """You are a label evaluation worker agent. Your role is to carefully analyze data items and provide thoughtful evaluations of their labels. Be critical, fair, and thorough in your analysis."""

EVALUATION_PROMPT = """Task: {task_description}

Data Item:
{text}

Current Labels:
{labels}

Please evaluate the labels and provide your assessment. Consider:
1. Are the labels accurate?
2. Are they consistent with the content?
3. Are there any improvements needed?

Respond in JSON format:
{{"evaluation": "correct|incorrect|needs_revision", "reasoning": "...", "suggested_changes": {{...}}, "confidence": 0.0-1.0}}"""


def get_evaluation_prompt(item: dict[str, Any], task_type: str) -> str:
    return EVALUATION_PROMPT.format(
        task_description=f"Evaluate {task_type} task",
        text=item.get("text", ""),
        labels=item.get("labels", {})
    )


MANAGER_ANALYSIS_PROMPT = """Analyze the following dataset to understand the tasks and design an evaluation strategy.

Dataset Summary:
- Total items: {total_items}
- Task types detected: {task_types}
- Difficulty distribution: {difficulty_dist}

For each item, you need to:
1. Determine the appropriate number of workers (2-5)
2. Design the evaluation strategy
3. Monitor the discussion and provide tie-breaking when needed

Respond with a JSON plan specifying group sizes and strategies."""

DISCUSSION_PROMPT = """Worker {worker_id} Evaluation:
{evaluation}

Do you agree or disagree with this evaluation? Provide reasoning."""

CONSENSUS_PROMPT = """Discussion Summary:
{discussion}

Workers haven't reached consensus. As the manager, make a final decision based on all arguments.

Output: {{"final_label": {{...}}, "reasoning": "..."}}"""