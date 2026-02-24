from solver.services.solvers.sympy_solver import solve_equation
from history.models import Solution
from solver.services.solvers.fallback_solver import fallback_solution


def process_job(job):
    try:
        job["status"] = "processing"

        steps, solution = solve_equation(
            job["equation"],
            job["variable"]
        )

        job["status"] = "done"
        job["result"] = {
            "steps": steps,
            "solution": solution
        }

        # сохраняем в БД
        Solution.objects.create(
            equation=job["equation"],
            solution=solution,
            steps=steps
        )

    except ValueError as e:
        job["status"] = "error"
        job["error"] = str(e)
    except Exception:
        result = fallback_solution(job["equation"])
        job["status"] = "done"
        job["result"] = result

    return job