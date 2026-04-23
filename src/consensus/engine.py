from typing import Any, Union
from pydantic import BaseModel

from .strategies import (
    ConsensusStrategy,
    get_strategy,
)


class ConsensusEngine:
    def __init__(self, strategy_name: str = "discussion_then_vote", **kwargs):
        self.strategy = get_strategy(strategy_name, **kwargs)

    def check_consensus(self, evaluations: list[dict[str, Any]]) -> bool:
        return self.strategy.check_consensus(evaluations)

    def resolve(
        self,
        evaluations: list[dict[str, Any]],
        item: Union[dict, BaseModel],
    ) -> dict[str, Any]:
        return self.strategy.resolve(evaluations, item)

    def set_strategy(self, strategy_name: str, **kwargs) -> None:
        self.strategy = get_strategy(strategy_name, **kwargs)