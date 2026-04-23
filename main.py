import argparse
import sys
from pathlib import Path

from smolagents import OpenAIModel
from tqdm import tqdm

from src import Config, ConsensusEngine, ManagerAgent, save_json
from src.models import WorkerAgent, create_worker
from src.models.schema import DataItem, InputData, TaskConfig
from src.models.mock_model import MockModel


def main():
    parser = argparse.ArgumentParser(description="AgentCompany Label Evaluation System")
    parser.add_argument("input", help="Input JSON file path")
    parser.add_argument("-o", "--output", help="Output JSON file path", default=None)
    parser.add_argument("--endpoint", help="vLLM endpoint", default=None)
    parser.add_argument("--model", help="Model ID", default=None)
    parser.add_argument("--mock", action="store_true", help="Use mock model for testing")
    args = parser.parse_args()

    config = Config()
    if args.endpoint:
        config.vllm_endpoint = args.endpoint
    if args.model:
        config.model_id = args.model

    output_path = args.output or args.input.replace(".json", "_evaluated.json")

    print(f"Loading data from {args.input}...")
    input_data = InputData.from_json(Path(args.input).read_text(encoding="utf-8"))

    items = input_data.items
    if not items:
        print("No items found in input file.")
        sys.exit(1)

    print("Initializing manager agent...")
    if args.mock:
        print("  Using mock model for testing")
        model = MockModel()
    else:
        model = OpenAIModel(
            model_id=config.model_id,
            api_base=config.vllm_endpoint,
            api_key=config.api_key,
        )

    manager = ManagerAgent(model, input_data.task_config)

    print("Analyzing dataset and creating evaluation plan...")
    analysis = manager.analyze_and_plan(items)
    print(f"  Difficulty: {analysis['evaluation_plan']['difficulty_level']}")
    print(f"  Consensus Strategy: {analysis['evaluation_plan']['consensus_strategy']}")
    print(f"  Workers to create: {len(analysis['evaluation_plan']['worker_agents'])}")

    workers_dict = manager.create_workers(model)

    workers = []
    for config_item in manager.get_worker_configs():
        agent = workers_dict[config_item["agent_id"]]
        worker = WorkerAgent(
            agent=agent,
            agent_id=config_item["agent_id"],
            role=config_item["role"],
            focus=config_item["focus"],
            evaluation_instructions=config_item["instructions"],
            task_config=input_data.task_config,
        )
        workers.append(worker)

    consensus_strategy = manager.get_consensus_strategy()
    consensus_engine = ConsensusEngine(strategy_name=consensus_strategy)
    max_rounds = manager.get_max_rounds()

    results = []
    for item in tqdm(items, desc="Evaluating items"):
        result = evaluate_item(
            item=item,
            workers=workers,
            manager=manager,
            consensus_engine=consensus_engine,
            max_rounds=max_rounds,
            task_config=input_data.task_config,
        )
        results.append(result)

    save_json(results, output_path)
    print(f"Results saved to {output_path}")


def evaluate_item(
    item: DataItem,
    workers: list[WorkerAgent],
    manager: ManagerAgent,
    consensus_engine: ConsensusEngine,
    max_rounds: int,
    task_config: TaskConfig,
) -> dict:
    evaluations = []
    for worker in workers:
        eval_result = worker.evaluate(item)
        evaluations.append(eval_result)

    discussion_history = []
    for _ in range(max_rounds):
        if consensus_engine.check_consensus(evaluations):
            break

        new_evaluations = []
        for i, worker in enumerate(workers):
            if i == 0:
                new_evaluations.append(evaluations[i])
                continue

            peer_eval = evaluations[0]
            discussion_result = worker.discuss(peer_eval, item)
            discussion_history.append(discussion_result)

            updated_eval = worker.evaluate(item)
            new_evaluations.append(updated_eval)

        evaluations = new_evaluations

    if consensus_engine.check_consensus(evaluations):
        resolved = consensus_engine.resolve(evaluations, item)
    else:
        resolved = manager.tie_break(item, evaluations, discussion_history)

    return {
        "id": item.id,
        "text": item.text,
        "labels": resolved.get("labels", item.labels),
        "evaluation_summary": {
            "consensus": resolved.get("consensus", "resolved"),
            "reasoning": resolved.get("reasoning", ""),
            "resolved_by": resolved.get("resolved_by", "workers"),
            "worker_count": len(workers),
            "discussion_rounds": len(discussion_history),
        },
    }


if __name__ == "__main__":
    main()