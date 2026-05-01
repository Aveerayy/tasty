from __future__ import annotations

from pathlib import Path

import yaml


class ContractRegistry:
    def __init__(self, base_dir: str = "contracts") -> None:
        self.base_dir = Path(base_dir)

    def load(self, contract_name: str) -> dict:
        path = self.base_dir / f"{contract_name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Contract not found: {contract_name}")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


contracts = ContractRegistry()
