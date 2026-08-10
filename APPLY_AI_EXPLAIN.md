# SymPy-first + verified AI explanation patch

Архив предназначен для распаковки **в корень существующего репозитория `trposite`**.

## Что меняется

- `/api/solve/` больше не принимает выбор solver и всегда использует SymPy.
- Во frontend удалён выпадающий список solver'ов.
- После успешного SymPy-решения появляется кнопка **«Объяснить с помощью ИИ»**.
- Добавлен `POST /api/explain/`.
- `/api/explain/` использует локальную Ollama (`llama3`).
- AI обязан вернуть `solution_expression` в SymPy-синтаксисе.
- Backend независимо подставляет AI-решение в исходное ОДУ.
- Если решение неверно, backend передаёт модели невязку и причины ошибки и повторяет запрос.
- Максимум 3 попытки самокоррекции.
- Непроверенный AI-ответ пользователю как корректный не выдаётся.

## Установка

Из корня проекта:

```powershell
pip install -r backend/requirements.txt
```

Убедиться, что Ollama запущена и модель существует:

```powershell
ollama pull llama3
ollama serve
```

Backend:

```powershell
cd backend
python manage.py runserver
```

Frontend в другом терминале:

```powershell
cd frontend
npm install
npm start
```

## Быстрая проверка

Уравнение:

```text
y.diff(x) - y = 0
```

1. Нажать `Решить` — результат должен прийти через SymPy.
2. Нажать `Объяснить с помощью ИИ`.
3. После ответа должен появиться статус `проверено`, confidence и число попыток.

