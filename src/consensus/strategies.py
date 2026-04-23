from abc import ABC, abstractmethod
from typing import Any


class ConsensusStrategy(ABC):
    @abstractmethod
    def resolve(
        self, evaluations: list[dict[str, Any]], item: dict[str, Any]
    ) -> dict[str, Any]:
        pass


class MajorityVoteStrategy(ConsensusStrategy):
    def resolve(
        self, evaluations: list[dict[str, Any]], item: dict[str, Any]
    ) -> dict[str, Any]:
        votes = [e.get("evaluation", "unknown") for e in evaluations]
        vote_counts: dict[str, int] = {}
        for v in votes:
            vote_counts[v] = vote_counts.get(v, 0) + 1

        winner = max(vote_counts, key=vote_counts.get)
        labels = item.get("labels", {})

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


class DiscussionStrategy(ConsensusStrategy):
    def resolve(
        self, evaluations: list[dict[str, Any]], item: dict[str, Any]
    ) -> dict[str, Any]:
        labels = item.get("labels", {})
        discussion_text = "\n".join(
            [f"Worker {i+1}: {e.get('reasoning', '')}" for i, e in enumerate(evaluations)]
        )

        return {
            "labels": labels,
            "consensus": "discussion",
            "discussion": discussion_text,
            "reasoning": "All workers discussed their positions",
        }


class UnionStrategy(ConsensusStrategy):
    def resolve(
        self, evaluations: list[dict[str, Any]], item: dict[str, Any]
    ) -> dict[str, Any]:
        all_keywords: set[str] = set()
        for e in evaluations:
            if "suggested_changes" in e:
                suggested = e["suggested_changes"]
                if "keywords" in suggested:
                    all_keywords.update(suggested["keywords"])

        labels = item.get("labels", {})
        if "keywords" not in labels:
            labels["keywords"] = []
        labels["keywords"] = list(all_keywords)

        return {
            "labels": labels,
            "consensus": "union",
            "keywords_found": list(all_keywords),
            "reasoning": f"Union of {len(evaluations)} workers' keyword extractions",
        }