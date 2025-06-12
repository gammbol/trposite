from datetime import datetime

history = []

def add_to_history(equation, steps, solution):
    history.append({
        'id': len(history) + 1,
        'equation': equation,
        'steps': steps,
        'solution': solution,
        'created_at': datetime.utcnow().isoformat()
    })

