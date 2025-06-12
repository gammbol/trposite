import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from services.solver_service import solve
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
        print(f"[API] Получены данные: {data}")

        equation = data.get('equation')
        variable = data.get('variable', 'x')

        if not equation:
            return jsonify({'error': 'Уравнение не передано'}), 400

        if not isinstance(equation, str):
            return jsonify({'error': 'Некорректный формат уравнения'}), 400

        result = solve(equation, variable)
        steps = result["steps"]
        solution = result["solution"]

        add_to_history(equation, steps, solution)

        return jsonify(success_response(
            {
                "steps": steps,
                "solution": solution
            },
            {
                "equation": equation,
                "variable": variable
            }
        ))

    except Exception as e:
        print(f"[ОШИБКА] {str(e)}")
        return jsonify(error_response(str(e))), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(history)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
