from services.solver.dispatcher import SolverDispatcher

dispatcher = SolverDispatcher()


def process_job(job):
    try:
        job["status"] = "processing"

        result = dispatcher.solve(
            job["equation"],
            job["variable"]
        )

        job["status"] = "done"
        job["result"] = result

        add_to_history(job["equation"], steps, solution)

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)

    return job