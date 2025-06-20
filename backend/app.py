import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from services.job_manager import create_job, get_job
from services.solver_service import process_job
from models import history, add_to_history

app = Flask(__name__)
CORS(app)  # разрешаем CORS для всех источников (можно ограничить)

def success_response(data, meta=None):
    return {
        "status": "success",
        "data": data,
        "meta": meta or {}
    }

def error_response(message):
    return {
        "status": "error",
        "error": message
    }

@app.route('/api/solve', methods=['POST'])
def solve():
    try:
        data = request.get_json()

        equation = data.get('equation')
        variable = data.get('variable', 'x')

        if not equation:
            return jsonify(error_response("Equation is required")), 400

        job = create_job(equation, variable)

        # имитация async (но пока sync)
        process_job(job)

        return jsonify(success_response(
            {"job_id": job["id"]},
            {"status": job["status"]}
        ))

    except Exception as e:
        return jsonify(error_response(str(e))), 500


@app.route('/api/result/<job_id>', methods=['GET'])
def get_result(job_id):
    job = get_job(job_id)

    if not job:
        return jsonify(error_response("Job not found")), 404

    if job["status"] == "done":
        return jsonify(success_response(
            job["result"],
            {"status": job["status"]}
        ))

    if job["status"] == "error":
        return jsonify(error_response(job["error"])), 500

    return jsonify(success_response(
        None,
        {"status": job["status"]}
    ))


@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(history)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
