import requests
import json
import re


class OllamaSolver:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        self.model = "llama3"  # можешь заменить на mistral

    def build_prompt(self, equation):
        return f"""
Ты — математический решатель дифференциальных уравнений.

Твоя задача:
решать уравнения строго пошагово, как преподаватель.

ЖЁСТКИЕ ПРАВИЛА:
1. Никакой воды, только математические шаги
2. Каждый шаг — одно действие
3. Не пропускай шаги
4. Используй LaTeX для формул
5. Не пиши ничего вне JSON
6. Определи тип уравнения (если возможно)
7. Укажи метод решения
8. Доведи до общего решения

ФОРМАТ ОТВЕТА (ОБЯЗАТЕЛЕН):

{{
  "steps": [
    {{"type": "text", "content": "Описание шага"}},
    {{"type": "math", "content": "LaTeX формула"}}
  ],
  "solution": "LaTeX финального ответа"
}}

Пример:
{{
  "steps": [
    {{"type": "text", "content": "Перепишем уравнение"}},
    {{"type": "math", "content": "\\\\frac{{dy}}{{dx}} = y"}}
  ],
  "solution": "y = Ce^x"
}}

Теперь реши уравнение:

{equation}
"""

    def extract_json(self, text):
        """
        Пытаемся достать JSON из ответа модели
        """
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            raise ValueError("JSON не найден в ответе модели")

        return json.loads(match.group())

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

            parsed = self.extract_json(content)

            # 🔥 базовая валидация
            if "steps" not in parsed or "solution" not in parsed:
                raise ValueError("Неверный формат ответа модели")

            return parsed

        except Exception as e:
            print("OLLAMA RAW RESPONSE:", content)
            return {
                "steps": [
                    {"type": "text", "content": "Ошибка локальной модели"},
                    {"type": "text", "content": str(e)}
                ],
                "solution": "Не удалось получить решение"
            }