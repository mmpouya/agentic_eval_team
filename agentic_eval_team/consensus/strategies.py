from abc import ABC, abstractmethod
from typing import Any, Union
from pydantic import BaseModel


class ConsensusStrategy(ABC):
    @abstractmethod
    def resolve(
        self, evaluations: list[dict[str, Any]], item: Union[dict, BaseModel]
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    def check_consensus(self, evaluations: list[dict[str, Any]]) -> bool:
        pass


def _get_labels(item: Union[dict, BaseModel]) -> dict[str, Any]:
    if isinstance(item, dict):
        return item.get("labels", {})
    return item.labels


class MajorityVoteStrategy(ConsensusStrategy):
    def resolve(
        self, evaluations: list[dict[str, Any]], item: Union[dict, BaseModel]
    ) -> dict[str, Any]:
        votes = [e.get("evaluation", "unknown") for e in evaluations]
        vote_counts: dict[str, int] = {}
        for v in votes:
            vote_counts[v] = vote_counts.get(v, 0) + 1

        winner = max(vote_counts, key=vote_counts.get)
        labels = _get_labels(item)

        if winner == "correct":
            pass
        elif winner == "needs_revision":
            best_eval = max(evaluations, key=lambda x: x.get("confidence", 0))
            if best_eval.get("suggested_changes"):
                labels.update(best_eval["suggested_changes"])

        return {
            "labels": labels,
            "consensus": winner,
            "votes": vote_counts,
            "reasoning": f"Majority vote: {winner} ({vote_counts[winner]}/{len(votes)})",
        }

    def check_consensus(self, evaluations: list[dict[str, Any]]) -> bool:
        if len(evaluations) < 2:
            return True
        votes = [e.get("evaluation", "unknown") for e in evaluations]
        return len(set(votes)) == 1


class DiscussionThenVoteStrategy(ConsensusStrategy):
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold

    def resolve(
        self, evaluations: list[dict[str, Any]], item: Union[dict, BaseModel]
    ) -> dict[str, Any]:
        votes = [e.get("evaluation", "unknown") for e in evaluations]
        vote_counts: dict[str, int] = {}
        for v in votes:
            vote_counts[v] = vote_counts.get(v, 0) + 1

        total = len(votes)
        for vote_value, count in vote_counts.items():
            if count / total >= self.threshold:
                labels = _get_labels(item)
                if vote_value == "needs_revision":
                    best_eval = max(evaluations, key=lambda x: x.get("confidence", 0))
                    if best_eval.get("suggested_changes"):
                        labels.update(best_eval["suggested_changes"])
                return {
                    "labels": labels,
                    "consensus": vote_value,
                    "votes": vote_counts,
                    "reasoning": f"Threshold reached: {vote_value} ({count}/{total} >= {self.threshold})",
                }

        return {
            "labels": _get_labels(item),
            "consensus": "no_consensus",
            "votes": vote_counts,
            "reasoning": f"No threshold reached: max is {max(vote_counts.values())}/{total}",
        }

    def check_consensus(self, evaluations: list[dict[str, Any]]) -> bool:
        if len(evaluations) < 2:
            return True
        votes = [e.get("evaluation", "unknown") for e in evaluations]
        vote_counts: dict[str, int] = {}
        for v in votes:
            vote_counts[v] = vote_counts.get(v, 0) + 1
        total = len(votes)
        for count in vote_counts.values():
            if count / total >= self.threshold:
                return True
        return False


class FullConsensusStrategy(ConsensusStrategy):
    def resolve(
        self, evaluations: list[dict[str, Any]], item: Union[dict, BaseModel]
    ) -> dict[str, Any]:
        votes = [e.get("evaluation", "unknown") for e in evaluations]
        unique_votes = set(votes)

        if len(unique_votes) == 1:
            return {
                "labels": _get_labels(item),
                "consensus": list(unique_votes)[0],
                "reasoning": "Full consensus achieved",
            }

        return {
            "labels": _get_labels(item),
            "consensus": "no_consensus",
            "reasoning": f"No full consensus: {len(unique_votes)} different opinions",
        }

    def check_consensus(self, evaluations: list[dict[str, Any]]) -> bool:
        if len(evaluations) < 2:
            return True
        votes = [e.get("evaluation", "unknown") for e in evaluations]
        return len(set(votes)) == 1


class UnionStrategy(ConsensusStrategy):
    def resolve(
        self, evaluations: list[dict[str, Any]], item: Union[dict, BaseModel]
    ) -> dict[str, Any]:
        all_keywords: set[str] = set()
        for e in evaluations:
            if "suggested_changes" in e:
                suggested = e["suggested_changes"]
                if "keywords" in suggested:
                    all_keywords.update(suggested["keywords"])

        labels = _get_labels(item)
        if "keywords" not in labels:
            labels["keywords"] = []
        labels["keywords"] = list(all_keywords)

        return {
            "labels": labels,
            "consensus": "union",
            "keywords_found": list(all_keywords),
            "reasoning": f"Union of {len(evaluations)} workers' keyword extractions",
        }

    def check_consensus(self, evaluations: list[dict[str, Any]]) -> bool:
        if len(evaluations) < 2:
            return True
        all_keywords: set[str] = set()
        for e in evaluations:
            if "suggested_changes" in e and "keywords" in e["suggested_changes"]:
                all_keywords.update(e["suggested_changes"]["keywords"])
        return len(all_keywords) > 0


CONSENSUS_STRATEGIES = {
    "majority_vote": MajorityVoteStrategy,
    "discussion_then_vote": DiscussionThenVoteStrategy,
    "full_consensus": FullConsensusStrategy,
    "union": UnionStrategy,
}


def get_strategy(strategy_name: str, **kwargs) -> ConsensusStrategy:
    strategy_class = CONSENSUS_STRATEGIES.get(strategy_name, DiscussionThenVoteStrategy)
    return strategy_class(**kwargs)