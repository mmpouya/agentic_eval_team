from typing import Any

from ..tasks.router import TaskType
from .strategies import (
    ConsensusStrategy,
    DiscussionStrategy,
    MajorityVoteStrategy,
    UnionStrategy,
)


class ConsensusEngine:
    def __init__(self):
        self._strategies: dict[TaskType, type[ConsensusStrategy]] = {
            TaskType.CLASSIFICATION: MajorityVoteStrategy,
            TaskType.TRANSLATION_CHOICE: DiscussionStrategy,
            TaskType.KEYWORD_EXTRACTION: UnionStrategy,
            TaskType.OTHER: MajorityVoteStrategy,
        }

    def get_strategy(self, task_type: TaskType) -> ConsensusStrategy:
        strategy_class = self._strategies.get(task_type, MajorityVoteStrategy)
        return strategy_class()

    def check_consensus(self, evaluations: list[dict[str, Any]]) -> bool:
        if len(evaluations) < 2:
            return True

        votes = [e.get("evaluation", "unknown") for e in evaluations]
        unique_votes = set(votes)

        if len(unique_votes) == 1:
            return True

        vote_counts: dict[str, int] = {}
        for v in votes:
            vote_counts[v] = vote_counts.get(v, 0) + 1

        total = len(votes)
        for count in vote_counts.values():
            if count / total >= 0.6:
                return True

        return False

    def resolve(
        self,
        task_type: TaskType,
        evaluations: list[dict[str, Any]],
        item: dict[str, Any],
    ) -> dict[str, Any]:
        strategy = self.get_strategy(task_type)
        return strategy.resolve(evaluations, item)