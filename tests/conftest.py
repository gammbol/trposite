from pathlib import Path
import json

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "tests" / "datasets"


@pytest.fixture(scope="session")
def ode_dataset():
    with (DATASET_DIR / "verified_odes.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def simple_equation():
    return "Derivative(y, x) - y = 0"


@pytest.fixture
def simple_solution():
    return "C1*exp(x)"
