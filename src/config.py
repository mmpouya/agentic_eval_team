import os
from dataclasses import dataclass


@dataclass
class Config:
    vllm_endpoint: str = os.getenv("VLLM_ENDPOINT", "http://localhost:8000/v1")
    api_key: str = os.getenv("VLLM_API_KEY", "dummy")
    model_id: str = os.getenv("MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct")
    max_workers: int = int(os.getenv("MAX_WORKERS", "5"))
    discussion_rounds: int = int(os.getenv("DISCUSSION_ROUNDS", "2"))
    consensus_threshold: float = float(os.getenv("CONSENSUS_THRESHOLD", "0.6"))
    output_dir: str = os.getenv("OUTPUT_DIR", "./output")