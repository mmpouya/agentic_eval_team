import unittest
from src.consensus.strategies import (
    MajorityVoteStrategy,
    DiscussionThenVoteStrategy,
    FullConsensusStrategy,
    UnionStrategy,
    get_strategy,
)
from src.models.schema import TaskConfig, DataItem, InputData


class TestSchemas(unittest.TestCase):
    def test_task_config_defaults(self):
        config = TaskConfig()
        self.assertEqual(config.description, "Evaluate labels for accuracy and quality")
        self.assertEqual(config.consensus_strategy, "discussion_then_vote")
        self.assertEqual(config.max_discussion_rounds, 2)

    def test_data_item_creation(self):
        item = DataItem(id="test_1", text="Hello world", labels={"label": "value"})
        self.assertEqual(item.id, "test_1")
        self.assertEqual(item.text, "Hello world")
        self.assertEqual(item.labels, {"label": "value"})

    def test_input_data_from_dict(self):
        data = InputData(
            task_config=TaskConfig(description="Test task"),
            items=[
                DataItem(id="1", text="Sample text", labels={})
            ]
        )
        self.assertEqual(data.task_config.description, "Test task")
        self.assertEqual(len(data.items), 1)

    def test_input_data_from_json(self):
        json_str = '{"items": [{"id": "1", "text": "test"}]}'
        data = InputData.from_json(json_str)
        self.assertEqual(len(data.items), 1)
        self.assertEqual(data.items[0].id, "1")


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

    def test_discussion_then_vote_threshold(self):
        strategy = DiscussionThenVoteStrategy(threshold=0.6)
        evaluations = [
            {"evaluation": "correct", "confidence": 0.9},
            {"evaluation": "correct", "confidence": 0.8},
            {"evaluation": "incorrect", "confidence": 0.7},
        ]

        self.assertTrue(strategy.check_consensus(evaluations))

    def test_full_consensus_required(self):
        strategy = FullConsensusStrategy()
        dissenting = [{"evaluation": "correct"}, {"evaluation": "incorrect"}]
        self.assertFalse(strategy.check_consensus(dissenting))

    def test_union_strategy(self):
        strategy = UnionStrategy()
        evaluations = [
            {"suggested_changes": {"keywords": ["ai", "ml"]}},
            {"suggested_changes": {"keywords": ["ml", "deep learning"]}},
        ]

        result = strategy.resolve(evaluations, {"labels": {}})

        self.assertIn("ai", result["labels"]["keywords"])
        self.assertIn("ml", result["labels"]["keywords"])


if __name__ == "__main__":
    unittest.main()