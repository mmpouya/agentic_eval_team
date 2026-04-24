from typing import Any
from smolagents import CodeAgent, OpenAIModel, tool

from .schema import DataItem, EvaluationPlan, TaskConfig


@tool
def assess_difficulty(
    sample_items: list[DataItem],
    task_description: str,
) -> dict[str, Any]:
    """Assess the difficulty of a labeling task by analyzing sample items.

    Args:
        sample_items: A sample of items (5-10) from the dataset to analyze
        task_description: Description of what kind of labeling task this is

    Returns:
        A dictionary containing difficulty assessment
    """
    if not sample_items:
        return {
            "difficulty_level": "medium",
            "reasoning": "No samples provided, using default medium difficulty",
            "recommended_strategies": ["discussion_then_vote"],
            "estimated_rounds": 2,
        }

    total_length = sum(len(item.text.split()) for item in sample_items)
    avg_length = total_length / len(sample_items)

    label_complexity = sum(
        1 for item in sample_items
        if len(item.labels) > 2
    )

    difficulty_score = 0
    if avg_length > 200:
        difficulty_score += 0.3
    if avg_length > 500:
        difficulty_score += 0.2
    if label_complexity > len(sample_items) * 0.5:
        difficulty_score += 0.2
    if len(sample_items) > 1:
        for i in range(len(sample_items)):
            for j in range(i + 1, len(sample_items)):
                if sample_items[i].labels != sample_items[j].labels:
                    difficulty_score += 0.1

    difficulty_score = min(difficulty_score, 1.0)

    if difficulty_score < 0.4:
        level = "low"
        strategies = ["majority_vote"]
        rounds = 1
    elif difficulty_score < 0.7:
        level = "medium"
        strategies = ["discussion_then_vote"]
        rounds = 2
    else:
        level = "high"
        strategies = ["discussion_then_vote", "manager_tiebreaker"]
        rounds = 3

    return {
        "difficulty_level": level,
        "difficulty_score": difficulty_score,
        "reasoning": f"Avg text length: {avg_length:.0f} words, Label complexity: {label_complexity}/{len(sample_items)} items complex",
        "recommended_strategies": strategies,
        "estimated_rounds": rounds,
        "task_description": task_description,
    }


@tool
def plan_evaluation_strategy(
    dataset_summary: dict[str, Any],
    difficulty_assessment: dict[str, Any],
    task_config: TaskConfig,
) -> EvaluationPlan:
    """Plan the overall evaluation strategy based on dataset and difficulty.

    Args:
        dataset_summary: Summary statistics of the entire dataset
        difficulty_assessment: The difficulty assessment from assess_difficulty
        task_config: The user's task configuration

    Returns:
        A comprehensive evaluation plan
    """
    total_items = dataset_summary.get("total_items", 0)
    difficulty = difficulty_assessment.get("difficulty_level", "medium")
    strategies = difficulty_assessment.get("recommended_strategies", [])

    consensus_strategy = task_config.consensus_strategy or (strategies[0] if strategies else "discussion_then_vote")
    max_rounds = task_config.max_discussion_rounds or difficulty_assessment.get("estimated_rounds", 2)

    base_roles = [
        {"role": "strict_evaluator", "focus": "accuracy and correctness", "instructions": "Evaluate whether labels are factually correct."},
        {"role": "creative_reviewer", "focus": "edge cases and alternatives", "instructions": "Consider edge cases and alternative label interpretations."},
    ]

    if difficulty == "high":
        base_roles.extend([
            {"role": "domain_expert", "focus": "technical accuracy", "instructions": "Check for domain-specific correctness."},
            {"role": "lenient_reviewer", "focus": "practical acceptability", "instructions": "Evaluate whether the label is practically acceptable."},
        ])

    worker_agents = [
        {"agent_id": i + 1, **role_config}
        for i, role_config in enumerate(base_roles)
    ]

    return EvaluationPlan(
        difficulty_level=difficulty,
        reasoning=difficulty_assessment.get("reasoning", ""),
        recommended_strategies=strategies,
        estimated_rounds=max_rounds,
        worker_agents=worker_agents,
        consensus_strategy=consensus_strategy,
        max_discussion_rounds=max_rounds,
    )


def create_worker(
    model: OpenAIModel,
    agent_id: int,
    role: str,
    focus: str,
    evaluation_instructions: str,
) -> CodeAgent:
    """Programmatically create a worker agent."""
    system_prompt = f"""You are Worker {agent_id}, a {role}.

Your focus: {focus}

{evaluation_instructions}

Always provide your evaluation in JSON format with keys: evaluation (correct/incorrect/needs_revision), reasoning, suggested_changes, confidence (0.0-1.0)."""

    return CodeAgent(
        model=model,
        tools=[],
        description=f"Worker {agent_id} - {role}",
    )