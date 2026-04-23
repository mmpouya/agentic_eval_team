from enum import Enum
from typing import Any


class TaskType(Enum):
    CLASSIFICATION = "classification"
    TRANSLATION_CHOICE = "translation_choice"
    KEYWORD_EXTRACTION = "keyword_extraction"
    OTHER = "other"


class TaskRouter:
    @staticmethod
    def detect_task_type(item: dict[str, Any]) -> TaskType:
        labels = item.get("labels", {})

        if "options" in labels or "category" in labels:
            return TaskType.CLASSIFICATION
        if "best_translation" in labels:
            return TaskType.TRANSLATION_CHOICE
        if "keywords" in labels or "extracted_keywords" in labels:
            return TaskType.KEYWORD_EXTRACTION
        return TaskType.OTHER

    @staticmethod
    def estimate_difficulty(item: dict[str, Any]) -> float:
        text = item.get("text", "")
        text_length = len(text.split())

        labels = item.get("labels", {})
        if isinstance(labels.get("options"), list):
            text_length *= 1 + len(labels["options"]) * 0.1

        if text_length < 50:
            return 0.3
        elif text_length < 200:
            return 0.5
        elif text_length < 500:
            return 0.7
        return 0.9

    @staticmethod
    def suggest_group_size(difficulty: float, task_type: TaskType) -> int:
        base_size = 2

        if task_type == TaskType.TRANSLATION_CHOICE:
            base_size = 3

        if difficulty > 0.7:
            base_size += 1

        return min(base_size, 5)