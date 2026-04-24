import requests
import json
import re


class OllamaSolver:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        self.model = "llama3"

    def build_prompt(self, equation):
        return f"""
Ты — строгий преподаватель математики, объясняющий решение дифференциальных уравнений студенту.

Твоя задача — расписать решение МАКСИМАЛЬНО ПОДРОБНО.

❗ КРИТИЧЕСКИЕ ПРАВИЛА:

1. Каждый шаг = ОДНО элементарное действие
2. НЕЛЬЗЯ объединять несколько действий в один шаг
3. НЕЛЬЗЯ пропускать преобразования
4. Любое преобразование должно быть явно показано
5. Каждое преобразование должно сопровождаться формулой
6. Минимум 8–15 шагов даже для простых уравнений
7. Обязательно:
   - определить тип уравнения
   - объяснить выбор метода
   - показать ВСЕ промежуточные преобразования
8. Запрещено:
   - писать "очевидно"
   - писать "сразу получаем"
   - перескакивать к ответу

---

❗ ЖЁСТКОЕ ТРЕБОВАНИЕ К ФОРМАТУ:

Ты ОБЯЗАН вернуть ТОЛЬКО валидный JSON.

Если добавишь любой текст вне JSON — ответ считается неправильным.

НЕ пиши:
- Step 1
- Solution:
- пояснения вне JSON

---

ФОРМАТ ОТВЕТА:

{{
  "steps": [
    {{"type": "text", "content": "Описание действия"}},
    {{"type": "math", "content": "LaTeX формула"}}
  ],
  "solution": "LaTeX финального ответа"
}}

---

ПРИМЕР СТИЛЯ:

{{
  "steps": [
    {{"type": "text", "content": "Переносим все слагаемые в левую часть уравнения"}},
    {{"type": "math", "content": "\\\\frac{{dy}}{{dx}} - y = 0"}},
    {{"type": "text", "content": "Выражаем производную явно"}},
    {{"type": "math", "content": "\\\\frac{{dy}}{{dx}} = y"}},
    {{"type": "text", "content": "Разделяем переменные"}},
    {{"type": "math", "content": "\\\\frac{{1}}{{y}} dy = dx"}}
  ],
  "solution": "y = Ce^x"
}}

---

❗ ОСОБО ВАЖНО:

- Ответ должен быть ПОДРОБНЫМ
- Если шагов меньше 8 — решение считается неправильным
- Ответ будет автоматически парситься JSON-парсером

---

Реши уравнение:

{equation}
"""

    def fix_json(self, text):
        text = re.sub(r'}\s*{', '},{', text)
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        return text

    def extract_json(self, text):
        bracket_count = 0
        json_start = None

        for i, char in enumerate(text):
            if char == "{":
                if json_start is None:
                    json_start = i
                bracket_count += 1
            elif char == "}":
                bracket_count -= 1
                if bracket_count == 0 and json_start is not None:
                    json_str = text[json_start:i + 1]

                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        return json.loads(self.fix_json(json_str))

        raise ValueError(f"Не удалось извлечь JSON:\n{text}")

    def solve(self, equation, variable):
        prompt = self.build_prompt(equation)

        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )

            data = response.json()
            content = data.get("response", "")

            print("OLLAMA RAW RESPONSE:\n", content)

            parsed = self.extract_json(content)

            if "steps" not in parsed or "solution" not in parsed:
                raise ValueError("Неверный формат ответа модели")

            return parsed

        except Exception as e:
            print("OLLAMA ERROR:", str(e))

            return {
                "steps": [
                    {"type": "text", "content": "Ошибка локальной модели"},
                    {"type": "text", "content": str(e)}
                ],
                "solution": "Не удалось получить решение"
            }