import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from tqdm import tqdm

from agentic_eval_team.models import WorkerAgent
from agentic_eval_team.consensus import ConsensusEngine
from agentic_eval_team.models.schema import DataItem, TaskConfig


class AsyncEvaluationRunner:
    def __init__(
        self,
        workers: list[WorkerAgent],
        manager: Any,
        consensus_engine: ConsensusEngine,
        max_rounds: int,
        task_config: TaskConfig,
        max_workers: int = 4,
    ):
        self.workers = workers
        self.manager = manager
        self.consensus_engine = consensus_engine
        self.max_rounds = max_rounds
        self.task_config = task_config
        self.max_workers = max_workers

    def evaluate_items(self, items: list[DataItem], progress_callback=None) -> list[dict]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._evaluate_single, item): item for item in items}

            with tqdm(total=len(items), desc="Evaluating items") as pbar:
                for future in futures:
                    result = future.result()
                    results.append(result)
                    pbar.update(1)

                    if progress_callback:
                        progress_callback(result)

        results.sort(key=lambda x: x["id"])
        return results

    def _evaluate_single(self, item: DataItem) -> dict:
        evaluations = []
        for worker in self.workers:
            eval_result = worker.evaluate(item)
            evaluations.append(eval_result)

        discussion_history = []
        for _ in range(self.max_rounds):
            if self.consensus_engine.check_consensus(evaluations):
                break

            new_evaluations = []
            for worker in self.workers:
                peer_eval = evaluations[0]
                discussion_result = worker.discuss(peer_eval, item)
                discussion_history.append(discussion_result)

                updated_eval = worker.evaluate(item)
                new_evaluations.append(updated_eval)

            evaluations = new_evaluations

        if self.consensus_engine.check_consensus(evaluations):
            resolved = self.consensus_engine.resolve(evaluations, item)
        else:
            resolved = self.manager.tie_break(item, evaluations, discussion_history)

        return {
            "id": item.id,
            "text": item.text,
            "labels": resolved.get("labels", item.labels),
            "evaluation_summary": {
                "consensus": resolved.get("consensus", "resolved"),
                "reasoning": resolved.get("reasoning", ""),
                "resolved_by": resolved.get("resolved_by", "workers"),
                "worker_count": len(self.workers),
                "discussion_rounds": len(discussion_history),
            },
        }