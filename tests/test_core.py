import unittest
from unittest.mock import MagicMock, patch
import json

from src.tasks.router import TaskRouter, TaskType
from src.consensus.engine import ConsensusEngine
from src.consensus.strategies import MajorityVoteStrategy, UnionStrategy


class TestTaskRouter(unittest.TestCase):
    def setUp(self):
        self.router = TaskRouter()

    def test_classification_detection(self):
        item = {"text": "test", "labels": {"category": "news"}}
        self.assertEqual(self.router.detect_task_type(item), TaskType.CLASSIFICATION)

    def test_translation_choice_detection(self):
        item = {"text": "test", "labels": {"best_translation": "A"}}
        self.assertEqual(self.router.detect_task_type(item), TaskType.TRANSLATION_CHOICE)

    def test_keyword_extraction_detection(self):
        item = {"text": "test", "labels": {"keywords": ["ai", "ml"]}}
        self.assertEqual(self.router.detect_task_type(item), TaskType.KEYWORD_EXTRACTION)

    def test_difficulty_estimation(self):
        short_text = {"text": "short"}
        medium_text = {"text": " ".join(["word"] * 100)}
        long_text = {"text": " ".join(["word"] * 600)}

        short_difficulty = self.router.estimate_difficulty(short_text)
        medium_difficulty = self.router.estimate_difficulty(medium_text)
        long_difficulty = self.router.estimate_difficulty(long_text)

        self.assertLess(short_difficulty, medium_difficulty)
        self.assertLess(medium_difficulty, long_difficulty)

    def test_group_size_suggestion(self):
        easy_task = TaskType.CLASSIFICATION
        hard_task = TaskType.TRANSLATION_CHOICE

        easy_size = self.router.suggest_group_size(0.3, easy_task)
        hard_size = self.router.suggest_group_size(0.8, hard_task)

        self.assertLessEqual(easy_size, hard_size)


class TestConsensusEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ConsensusEngine()

    def test_consensus_check_full_agreement(self):
        evaluations = [
            {"evaluation": "correct"},
            {"evaluation": "correct"},
        ]
        self.assertTrue(self.engine.check_consensus(evaluations))

    def test_consensus_check_no_consensus(self):
        evaluations = [
            {"evaluation": "correct"},
            {"evaluation": "incorrect"},
        ]
        self.assertFalse(self.engine.check_consensus(evaluations))

    def test_consensus_check_majority(self):
        evaluations = [
            {"evaluation": "correct"},
            {"evaluation": "correct"},
            {"evaluation": "incorrect"},
        ]
        self.assertTrue(self.engine.check_consensus(evaluations))


class TestStrategies(unittest.TestCase):
    def test_majority_vote_strategy(self):
        strategy = MajorityVoteStrategy()
        evaluations = [
            {"evaluation": "correct", "confidence": 0.9},
            {"evaluation": "correct", "confidence": 0.8},
            {"evaluation": "needs_revision", "confidence": 0.7},
        ]
        item = {"labels": {"category": "news"}}

        result = strategy.resolve(evaluations, item)

        self.assertEqual(result["consensus"], "correct")
        self.assertEqual(result["votes"]["correct"], 2)

    def test_union_strategy(self):
        strategy = UnionStrategy()
        evaluations = [
            {"suggested_changes": {"keywords": ["ai", "ml"]}},
            {"suggested_changes": {"keywords": ["ml", "deep learning"]}},
        ]
        item = {"labels": {}}

        result = strategy.resolve(evaluations, item)

        self.assertIn("ai", result["labels"]["keywords"])
        self.assertIn("ml", result["labels"]["keywords"])
        self.assertIn("deep learning", result["labels"]["keywords"])


if __name__ == "__main__":
    unittest.main()