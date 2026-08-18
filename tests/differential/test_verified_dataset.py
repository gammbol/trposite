import pytest

from solver.services.verification import MultiStageVerificationEngine


pytestmark = [pytest.mark.differential, pytest.mark.slow]


@pytest.mark.parametrize("reference_mode", [False, True])
def test_curated_ode_dataset_remains_mathematically_valid(ode_dataset, reference_mode):
    engine = MultiStageVerificationEngine()

    for case in ode_dataset:
        kwargs = {}
        if reference_mode:
            kwargs["reference_expression_str"] = engine.solve_reference(
                case["equation"], "x"
            )["expression_str"]

        result = engine.verify(
            case["equation"],
            case["solution"],
            "x",
            **kwargs,
        )

        assert result["verified"] is True, (
            f"{case['id']} failed verification: {result['reasons']}"
        )
