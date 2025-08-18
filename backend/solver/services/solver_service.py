from .sympy_solver import solve_equation
from history.models import Solution


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

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)

    return job