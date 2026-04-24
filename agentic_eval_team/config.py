import os
from dataclasses import dataclass


@dataclass
class Config:
    vllm_endpoint: str = os.getenv("VLLM_ENDPOINT", "http://localhost:8000/v1")
    api_key: str = os.getenv("VLLM_API_KEY", "dummy")
    model_id: str = os.getenv("MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct")