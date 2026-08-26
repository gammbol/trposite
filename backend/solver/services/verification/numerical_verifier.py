import math


class NumericalVerifier:
    """Numerical residual check used as an independent secondary signal."""

    SAMPLE_POINTS = (-4.0, -3.0, -2.0, -1.0, -0.5, 0.5, 1.0, 2.0, 3.0, 4.0)
    CONSTANT_VALUES = (0.731, 1.337)
    PARAMETER_VALUE = 1.11111111
    TOLERANCE = 1e-8
    MIN_CHECKED_POINTS = 6

    def verify(self, parsed, candidate_expression, residual_expression) -> dict:
        candidate_constants = sorted(
            candidate_expression.free_symbols - {parsed.variable} - parsed.parameters,
            key=str,
        )

        checked = 0
        skipped = 0
        max_abs_residual = 0.0
        samples = []

        assignments = [
            {
                **{symbol: constant for symbol in candidate_constants},
                **{symbol: self.PARAMETER_VALUE for symbol in parsed.parameters},
            }
            for constant in self.CONSTANT_VALUES
        ]

        if not assignments:
            assignments = [{}]

        for assignment_index, assignment in enumerate(assignments):
            for point in self.SAMPLE_POINTS:
                try:
                    value = (
                        residual_expression
                        .subs(assignment)
                        .subs(parsed.variable, point)
                        .evalf()
                    )
                    numeric = complex(value)
                    magnitude = abs(numeric)
                    if not math.isfinite(magnitude):
                        skipped += 1
                        continue

                    checked += 1
                    max_abs_residual = max(max_abs_residual, magnitude)
                    if len(samples) < 10:
                        samples.append(
                            {
                                "x": point,
                                "assignment": assignment_index + 1,
                                "abs_residual": float(magnitude),
                            }
                        )
                except Exception:
                    skipped += 1

        enough_evidence = checked >= self.MIN_CHECKED_POINTS
        passed = enough_evidence and max_abs_residual <= self.TOLERANCE

        return {
            "passed": passed,
            "checked_points": checked,
            "skipped_points": skipped,
            "minimum_required_points": self.MIN_CHECKED_POINTS,
            "enough_evidence": enough_evidence,
            "max_abs_residual": float(max_abs_residual) if checked else None,
            "tolerance": self.TOLERANCE,
            "samples": samples,
        }
