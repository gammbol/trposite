import os

from openai import OpenAI


class DeepSeekSolver:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("DEEP_SEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

    def solve(self, equation, variable):
        prompt = f"""
Реши дифференциальное уравнение и покажи шаги:

{equation}

Верни JSON:
{{
  "steps": [{{"type": "text", "content": "..."}}, ...],
  "solution": "..."
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            content = response.choices[0].message.content

            import re
            import json

            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                raise ValueError("Invalid response format")

            return parsed

        except Exception as e:
            return {
                "steps": [
                    {"type": "text", "content": "Ошибка DeepSeek"},
                    {"type": "text", "content": str(e)}
                ],
                "solution": "Ошибка при решении"
            }