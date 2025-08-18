import uuid

jobs = {}


def create_job(equation, variable='x'):
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "id": job_id,
        "equation": equation,
        "variable": variable,
        "status": "pending",
        "result": None,
        "error": None
    }

    return jobs[job_id]


def get_job(job_id):
    return jobs.get(job_id)