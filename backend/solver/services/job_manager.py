jobs = {}

def create_job(equation, variable='x'):
    job_id = str(len(jobs) + 1)
    jobs[job_id] = {"id": job_id, "equation": equation, "variable": variable, "status": "pending"}
    return jobs[job_id]

def get_job(job_id):
    return jobs.get(job_id)