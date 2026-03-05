from openai import OpenAI
from django.conf import settings

from .base_solver import BaseSolver


class AISolver(BaseSolver):

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def can_solve(self, equation: str) -> bool:
        # AI используем как fallback
        return True

    def solve(self, equation: str, variable: str = 'x'):
        prompt = f"""
Реши дифференциальное уравнение и покажи шаги решения.

Уравнение:
{equation}

Требования:
1. Покажи решение по шагам
2. Используй математическую нотацию
3. В конце дай итоговый ответ в формате y(x) = ...

Ответ верни в JSON формате:
{{
  "steps": [{{"type": "text", "content": "..."}}, {{"type": "math", "content": "..."}}],
  "solution": "..."
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Ты математик, решающий дифференциальные уравнения."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            content = response.choices[0].message.content

            # 🔥 пытаемся распарсить JSON
            import json
            try:
                parsed = json.loads(content)
                return parsed
            except Exception:
                # fallback если модель вернула текст
                return {
                    "steps": [
                        {"type": "text", "content": content}
                    ],
                    "solution": content
                }

        except Exception as e:
            raise Exception(f"AI solver error: {str(e)}")