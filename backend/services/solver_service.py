from services.solver import solve_equation
from models import add_to_history


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

        add_to_history(job["equation"], steps, solution)

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)

    return job