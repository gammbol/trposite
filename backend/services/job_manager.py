import uuid
from datetime import datetime


class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


jobs = {}


def create_job(equation, variable):
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "id": job_id,
        "equation": equation,
        "variable": variable,
        "status": JobStatus.PENDING,
        "result": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat()
    }

    return jobs[job_id]


def get_job(job_id):
    return jobs.get(job_id)


def update_job(job_id, **kwargs):
    if job_id in jobs:
        jobs[job_id].update(kwargs)