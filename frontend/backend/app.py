from flask import Flask, request, jsonify
from flask_cors import CORS
from solver import solve_equation
from models import history, add_to_history

app = Flask(__name__)
CORS(app)  # разрешаем CORS для всех источников (можно ограничить)

@app.route('/api/solve', methods=['POST'])
def solve():
    try:
        data = request.get_json()
        print(f"[API] Получены данные: {data}")

        equation = data.get('equation')
        variable = data.get('variable', 'x')

        if not equation:
            return jsonify({'error': 'Уравнение не передано'}), 400

        steps, solution = solve_equation(equation, variable)
        add_to_history(equation, steps, solution)

        return jsonify({
            'steps': steps,
            'solution': solution
        })

    except Exception as e:
        print(f"[ОШИБКА] {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(history)


if __name__ == '__main__':
    app.run(port=5050,debug=True)

