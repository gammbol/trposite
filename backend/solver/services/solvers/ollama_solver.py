import json
import re

import requests

from .base_solver import BaseSolver


class OllamaSolver(BaseSolver):
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"
        self.model = "llama3"
        self.timeout = 180

    def _request(self, prompt):
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.15,
                },
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        content = data.get("response", "")
        if not content:
            raise ValueError("Ollama вернула пустой ответ.")

        return self.extract_json(content)

    def build_prompt(self, equation, variable="x"):
        return f"""
Ты — строгий преподаватель математики, решающий дифференциальные уравнения.

Реши уравнение максимально подробно:
{equation}

Независимая переменная: {variable}

Каждый шаг должен описывать ровно одно математическое действие. Не пропускай
преобразования. Обязательно укажи тип уравнения, выбранный метод, все
промежуточные преобразования и итоговое общее решение.

Верни ТОЛЬКО корректный JSON следующего вида:
{{
  "steps": [
    {{"type": "text", "content": "описание действия"}},
    {{"type": "math", "content": "LaTeX формула"}}
  ],
  "solution": "LaTeX финального ответа",
  "solution_expression": "правая часть y(x) в синтаксисе SymPy"
}}

Пример solution_expression: C1*exp(x), а не LaTeX.
"""

    def build_explanation_prompt(
        self,
        equation,
        variable,
        verified_solution,
        correction_feedback=None,
    ):
        correction_block = ""
        if correction_feedback:
            correction_block = f"""

ВАЖНО: предыдущая попытка была отклонена верификатором.
Вот машинный feedback:
{correction_feedback}
"""

        return f"""
Ты — строгий преподаватель дифференциальных уравнений.

Исходное уравнение:
{equation}

Независимая переменная: {variable}

SymPy уже получил общее решение:
{verified_solution}

Твоя задача НЕ угадывать новый ответ, а максимально подробно объяснить, как
получить математически эквивалентное решение.

Правила:
1. Каждый элементарный переход — отдельный шаг.
2. Нельзя писать «очевидно», «сразу получаем» или пропускать преобразования.
3. Сначала определи тип ОДУ и объясни выбор метода.
4. Покажи преобразование исходного уравнения в форму выбранного метода.
5. Покажи все необходимые операции: переносы, деления, умножения,
   интегрирование, интегрирующий множитель и т.д.
6. После каждой содержательной операции показывай формулу в LaTeX.
7. Финальное решение должно удовлетворять исходному уравнению и содержать
   необходимое число произвольных констант.
8. Для простого уравнения всё равно дай не менее 8 содержательных элементов
   массива steps (текст и формулы считаются отдельными элементами).
9. Не добавляй текст вне JSON.

Верни ТОЛЬКО валидный JSON:
{{
  "steps": [
    {{"type": "text", "content": "подробное описание одного действия"}},
    {{"type": "math", "content": "LaTeX формула"}}
  ],
  "solution": "LaTeX итогового общего решения",
  "solution_expression": "ТОЛЬКО правая часть y(x) в синтаксисе SymPy"
}}

Критически важно для solution_expression:
- это НЕ LaTeX;
- используй ** для степени;
- используй exp(x), log(x), sin(x), cos(x);
- произвольные константы называй C1, C2 и т.д.;
- не пиши y(x)=, только правую часть;
- пример: C1*exp(x) или x**2/4 + C1/x**2.
{correction_block}
"""

    def solve(self, equation, variable="x"):
        return self._request(self.build_prompt(equation, variable))

    def explain(
        self,
        equation,
        variable="x",
        verified_solution="",
        correction_feedback=None,
    ):
        parsed = self._request(
            self.build_explanation_prompt(
                equation,
                variable,
                verified_solution,
                correction_feedback,
            )
        )

        if "steps" not in parsed or "solution" not in parsed:
            raise ValueError("Ollama вернула ответ без steps или solution.")
        if "solution_expression" not in parsed:
            raise ValueError("Ollama не вернула solution_expression для верификации.")

        return parsed

    @staticmethod
    def fix_json(text):
        text = re.sub(r'}\s*{', '},{', text)
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        return text

    def extract_json(self, text):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        bracket_count = 0
        json_start = None

        for index, char in enumerate(text):
            if char == "{":
                if json_start is None:
                    json_start = index
                bracket_count += 1
            elif char == "}" and json_start is not None:
                bracket_count -= 1
                if bracket_count == 0:
                    json_str = text[json_start:index + 1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        return json.loads(self.fix_json(json_str))

        raise ValueError(f"Не удалось извлечь JSON из ответа Ollama: {text}")
