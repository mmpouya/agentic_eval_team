import argparse
import sys
from pathlib import Path

from smolagents import OpenAIModel

from src import Config, ConsensusEngine, ManagerAgent, save_json
from src.models import WorkerAgent, create_worker
from src.models.schema import DataItem, InputData, TaskConfig
from src.models.mock_model import MockModel
from src.evaluation.runner import AsyncEvaluationRunner


def main():
    parser = argparse.ArgumentParser(description="AgentCompany Label Evaluation System")
    parser.add_argument("input", help="Input JSON file path")
    parser.add_argument("-o", "--output", help="Output JSON file path", default=None)
    parser.add_argument("--endpoint", help="vLLM endpoint", default=None)
    parser.add_argument("--model", help="Model ID", default=None)
    parser.add_argument("--mock", action="store_true", help="Use mock model for testing")
    parser.add_argument("--parallel", type=int, default=4, help="Max parallel workers for item processing")
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
    consensus_engine = ConsensusEngine(
        strategy_name=consensus_strategy,
        threshold=input_data.task_config.consensus_threshold
    )
    max_rounds = manager.get_max_rounds()

    print(f"Processing {len(items)} items with {args.parallel} parallel workers...")
    runner = AsyncEvaluationRunner(
        workers=workers,
        manager=manager,
        consensus_engine=consensus_engine,
        max_rounds=max_rounds,
        task_config=input_data.task_config,
        max_workers=args.parallel,
    )

    results = runner.evaluate_items(items)
    save_json(results, output_path)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()