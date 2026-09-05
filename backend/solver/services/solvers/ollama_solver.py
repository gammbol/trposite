import json
import os
import re

import requests

from .base_solver import BaseSolver


class OllamaSolver(BaseSolver):
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.url = f"{self.base_url}/api/generate"
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "180"))
        self.healthcheck_timeout = float(os.getenv("OLLAMA_HEALTHCHECK_TIMEOUT", "1.5"))

    def healthcheck(self) -> tuple[bool, str | None]:
        """Fast availability probe used before expensive consensus runs."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.healthcheck_timeout,
            )
            response.raise_for_status()
            payload = response.json()
            models = {
                item.get("name", "").split(":", 1)[0]
                for item in payload.get("models", [])
            }
            requested = self.model.split(":", 1)[0]
            if models and requested not in models:
                return False, f"Ollama запущена, но модель '{self.model}' не установлена."
            return True, None
        except requests.RequestException as exc:
            return False, f"Ollama недоступна: {exc}"
        except (TypeError, ValueError, KeyError) as exc:
            return False, f"Ollama вернула некорректный healthcheck-ответ: {exc}"

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

ПРЕДЫДУЩАЯ ПОПЫТКА БЫЛА ОТКЛОНЕНА BACKEND-ВАЛИДАТОРОМ.
Исправь только объяснение по следующему feedback:
{correction_feedback}
"""

        return f"""
Ты — преподаватель дифференциальных уравнений.

Исходное уравнение:
{equation}

Независимая переменная: {variable}

Уже проверенное SymPy решение:
y = {verified_solution}

ВАЖНО: ТЫ НЕ РЕШАЕШЬ УРАВНЕНИЕ ЗАНОВО.
Твоя единственная задача — объяснить понятным русским языком, как прийти
ИМЕННО к указанному выше проверенному ответу. Нельзя менять коэффициенты,
константы, знак, функцию или финальное семейство решений.

Правила содержания:
1. Весь обычный текст пиши только на русском языке.
2. Сначала назови тип ОДУ и объясни выбор метода.
3. Затем последовательно объясни преобразования, необходимые для получения
   уже известного проверенного ответа.
4. Один текстовый шаг должен описывать одно действие или одну идею.
5. Не придумывай лишние преобразования только ради количества шагов.
6. Не пиши «очевидно», «сразу получаем» и не перескакивай через ключевые этапы.
7. Последний математический шаг должен соответствовать проверенному ответу
   y = {verified_solution}.

КРИТИЧЕСКОЕ ПРАВИЛО ФОРМАТА МАТЕМАТИКИ:
- НЕ ПИШИ LaTeX вообще;
- НЕ используй обратный слеш, символы $...$ и любые команды LaTeX;
- поле content у математического шага должно содержать ТОЛЬКО простой
  SymPy/Python-подобный синтаксис;
- степень: **, например exp(-4*x) или x**2;
- функции: exp(x), log(x), sin(x), cos(x), tan(x);
- производная: Derivative(y, x);
- интеграл: Integral(exp(x), x);
- равенство можно писать одним знаком =;
- произвольные константы: C1, C2, ...;
- не вставляй Unicode-математику.

Правильные примеры math.content:
Derivative(y, x) + 4*y = exp(x)*cos(x)
y = C1*exp(-4*x) + exp(x)*(5*cos(x) + sin(x))/26
A*cos(x) + B*sin(x)

Верни ТОЛЬКО валидный JSON и ТОЛЬКО поле steps:
{{
  "steps": [
    {{"type": "text", "content": "Определяем тип уравнения и выбираем метод."}},
    {{"type": "math", "content": "Derivative(y, x) + 4*y = exp(x)*cos(x)"}}
  ]
}}

Не возвращай поля solution, solution_expression, answer, latex или final_answer.
Финальный ответ формирует backend из уже проверенного SymPy-решения.
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

        if "steps" not in parsed:
            raise ValueError("Ollama вернула ответ без steps.")
        if not isinstance(parsed.get("steps"), list):
            raise ValueError("Ollama вернула steps в неверном формате.")

        return parsed

    @staticmethod
    def fix_json(text):
        # Conservative repairs for common LLM formatting errors. Never attempt
        # to rewrite string contents because that can corrupt LaTeX.
        text = re.sub(r'}\s*{', '},{', text)
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        return text

    @staticmethod
    def _raw_decode_first_object(text: str):
        """
        Decode the first complete JSON object with JSONDecoder instead of manual
        brace counting. This correctly handles braces occurring inside strings,
        e.g. LaTeX expressions such as ``\\left\\{{ ... \\right\\}}``.
        """
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
        raise json.JSONDecodeError("No complete JSON object found", text, 0)

    def extract_json(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Ollama вернула пустой JSON payload.")

        stripped = text.strip()
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        try:
            return self._raw_decode_first_object(stripped)
        except json.JSONDecodeError:
            fixed = self.fix_json(stripped)
            try:
                return self._raw_decode_first_object(fixed)
            except json.JSONDecodeError as exc:
                preview = stripped[:500]
                raise ValueError(
                    "Не удалось извлечь корректный JSON из ответа Ollama. "
                    f"Начало ответа: {preview}"
                ) from exc
