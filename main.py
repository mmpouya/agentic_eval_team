import argparse
import os
import sys
from pathlib import Path

from smolagents import OpenAIModel
from tqdm import tqdm

from src import Config, ConsensusEngine, ManagerAgent, WorkerAgent, load_json, save_json
from src.tasks import TaskType


def main():
    parser = argparse.ArgumentParser(description="AgentCompany Label Evaluation System")
    parser.add_argument("input", help="Input JSON file path")
    parser.add_argument("-o", "--output", help="Output JSON file path", default=None)
    parser.add_argument("--endpoint", help="vLLM endpoint", default=None)
    parser.add_argument("--model", help="Model ID", default=None)
    args = parser.parse_args()

    config = Config()
    if args.endpoint:
        config.vllm_endpoint = args.endpoint
    if args.model:
        config.model_id = args.model

    output_path = args.output or args.input.replace(".json", "_evaluated.json")

    print(f"Loading data from {args.input}...")
    data = load_json(args.input)

    print("Initializing agents...")
    model = OpenAIModel(
        model_id=config.model_id,
        api_base=config.vllm_endpoint,
        api_key=config.api_key,
    )

    manager = ManagerAgent(model)
    consensus_engine = ConsensusEngine()

    print("Analyzing dataset...")
    dataset_info = manager.analyze_dataset(data)
    print(f"  Total items: {dataset_info['total_items']}")
    print(f"  Task types: {dataset_info['task_types']}")

    personas = ["strict_evaluator", "creative_reviewer", "detail_analyst", "pragmatic_checker", "deep_thinker"]

    results = []
    for item in tqdm(data, desc="Evaluating items"):
        result = evaluate_item(
            item, manager, consensus_engine, model, personas, config
        )
        results.append(result)

    save_json(results, output_path)
    print(f"Results saved to {output_path}")


def evaluate_item(item, manager, consensus_engine, model, personas, config):
    item_id = item.get("id", "unknown")
    task_type = manager.router.detect_task_type(item)
    group_size = manager.determine_group_size(item)

    workers = [
        WorkerAgent(model, i + 1, personas[i % len(personas)])
        for i in range(group_size)
    ]

    evaluations = []
    for worker in workers:
        eval_result = worker.evaluate(item, f"Evaluate {task_type.value} task")
        evaluations.append(eval_result)

    discussion = []
    for round_num in range(config.discussion_rounds):
        if consensus_engine.check_consensus(evaluations):
            break

        for i, worker in enumerate(workers):
            if i == 0:
                continue
            other_eval = evaluations[0]
            discussion_result = worker.discuss(other_eval, item)
            discussion.append(discussion_result)

    if consensus_engine.check_consensus(evaluations):
        resolved = consensus_engine.resolve(task_type, evaluations, item)
    else:
        resolved = manager.tie_break(item, evaluations, discussion)

    return {
        "id": item_id,
        "text": item.get("text", ""),
        "labels": resolved.get("labels", item.get("labels", {})),
        "evaluation_summary": {
            "task_type": task_type.value,
            "group_size": group_size,
            "consensus": resolved.get("consensus", "resolved"),
            "reasoning": resolved.get("reasoning", ""),
            "resolved_by": resolved.get("resolved_by", "workers"),
        },
    }


if __name__ == "__main__":
    main()