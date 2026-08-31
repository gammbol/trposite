# Кодовая база DiffSolver

## 1. Назначение документа

Этот документ — подробная карта репозитория. Он отвечает на вопросы:

- где находится конкретная функциональность;
- какие модули являются основными runtime-компонентами;
- какие файлы относятся к legacy/compatibility;
- как проходят запросы;
- какие структуры данных передаются между слоями;
- как добавить новый solver или verification stage;
- какие места требуют особого внимания при изменениях.

---

## 2. Итоговая структура

Ниже показана логическая структура актуального проекта. Стандартные Django/React generated-файлы сокращены там, где они не несут собственной бизнес-логики.

```text
trposite/
├── backend/
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── history/
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── solver/
│   │   ├── migrations/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services/
│   │       ├── job_manager.py
│   │       ├── solver_service.py
│   │       ├── ai/
│   │       │   └── explanation_service.py
│   │       ├── verification/
│   │       │   ├── normalizer.py
│   │       │   ├── symbolic_verifier.py
│   │       │   ├── numerical_verifier.py
│   │       │   ├── equivalence_checker.py
│   │       │   ├── domain_validator.py
│   │       │   ├── scoring.py
│   │       │   ├── engine.py
│   │       │   └── solution_verifier.py
│   │       ├── consensus/
│   │       │   ├── candidate.py
│   │       │   ├── providers.py
│   │       │   ├── grouping.py
│   │       │   ├── ranking.py
│   │       │   └── engine.py
│   │       └── solvers/
│   │           ├── base_solver.py
│   │           ├── sympy_solver.py
│   │           ├── ollama_solver.py
│   │           ├── ai_solver.py
│   │           ├── deepseek_solver.py
│   │           ├── fallback_solver.py
│   │           └── dispatcher.py
│   │
│   ├── manage.py
│   ├── requirements.txt
│   └── requirements-test.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   └── Header.js
│   │   ├── pages/
│   │   │   ├── Home.js
│   │   │   ├── Solver.js
│   │   │   └── Help.js
│   │   ├── App.js
│   │   ├── api.js
│   │   ├── index.js
│   │   └── styles.css
│   ├── backend/                 # legacy Flask snapshot, not active backend
│   ├── package.json
│   └── package-lock.json
│
├── tests/
│   ├── conftest.py
│   ├── datasets/
│   ├── unit/
│   ├── integration/
│   ├── differential/
│   ├── property/
│   ├── fuzz/
│   ├── resilience/
│   ├── regression/
│   └── load/
│
├── scripts/
│   └── run_test_cluster.sh
├── docs/
├── pytest.ini
└── README.md
```

---

# Часть I. Backend

## 3. `backend/manage.py`

Стандартная Django management entrypoint.

Используется для:

```bash
python backend/manage.py runserver
python backend/manage.py migrate
python backend/manage.py makemigrations
python backend/manage.py shell
```

---

## 4. `backend/config/`

### 4.1 `settings.py`

Django project settings.

Отвечает за:

- installed apps;
- middleware;
- database;
- templates/static configuration;
- CORS;
- environment loading;
- external API keys.

Основные приложения:

```text
rest_framework
solver
history
corsheaders
```

Development database — SQLite.

В development CORS ориентирован на React dev server:

```text
http://localhost:3000
```

### Важно про `BASE_DIR` и `.env`

В текущей реализации `settings.py` находится в `backend/config/settings.py`, но `BASE_DIR` вычисляется как `Path(__file__).resolve().parent.parent.parent`. Следовательно, `BASE_DIR` — это **корень репозитория `trposite/`**, а не каталог `backend/`. Из этого следуют конкретные runtime-пути:

```text
BASE_DIR                  -> trposite/
BASE_DIR / ".env"         -> trposite/.env
BASE_DIR / "db.sqlite3"   -> trposite/db.sqlite3
BASE_DIR / "frontend"/... -> trposite/frontend/...
```

Именно `trposite/.env` загружается вызовом `load_dotenv(BASE_DIR / ".env")`. Существующий `backend/.env.example` содержит исторические `DEBUG`/`PORT` значения и не является точным перечнем переменных, используемых нынешними AI/consensus providers. Реальные секреты не должны попадать в Git.

Кроме Django settings, часть provider-specific options читается непосредственно через `os.getenv()`.

---

### 4.2 `urls.py`

Корневой routing backend.

Подключает:

```text
/api/          -> solver.urls
/api/history/  -> history.urls
```

Следовательно solver endpoints получают полный prefix `/api/`.

---

### 4.3 `asgi.py`, `wsgi.py`

Стандартные Django deployment entrypoints.

В development `runserver` скрывает эту деталь, но production WSGI/ASGI server должен использовать один из них.

---

## 5. `backend/history/`

Отдельное Django-приложение для persistent истории.

### 5.1 `models.py`

Модель:

```python
Solution
```

Поля:

| Поле | Тип | Назначение |
|---|---|---|
| `equation` | TextField | исходное уравнение |
| `solution` | TextField | ответ |
| `steps` | JSONField | структурированные шаги |
| `created_at` | DateTimeField | время создания |

### 5.2 `serializers.py`

`SolutionSerializer` преобразует Django model records в JSON для REST API.

### 5.3 `views.py`

`HistoryView.get()`:

1. читает `Solution`;
2. сортирует по `created_at` по убыванию;
3. ограничивает выборку последними 50 записями;
4. сериализует список.

### 5.4 `urls.py`

Внутренний path пустой, а prefix задаётся `config/urls.py`.

Итог:

```text
GET /api/history/
```

### Важное текущее ограничение

Новый `SolveView` напрямую использует `SympySolver` и process-local job state. Автоматическая запись `Solution.objects.create(...)` не является частью этого нового fast path.

То есть:

- database model и read API существуют;
- storage layer готов;
- persistence каждого нового solve требует явного orchestration шага.

Это важно учитывать при тестах истории и дальнейшей разработке.

---

# Часть II. Solver API

## 6. `backend/solver/serializers.py`

Содержит REST input serializers.

### `SolveSerializer`

Поля:

```text
equation: required string
variable: optional string, default "x"
```

### `ExplainSerializer`

Тот же минимальный математический input, но endpoint имеет другой execution path.

### `ConsensusSerializer`

Input независимой multi-solver проверки.

### Почему нет `solver` dropdown field

Это сознательное изменение UX.

Пользователь не выбирает внутренний mathematical engine для обычного solve:

- `/solve/` всегда быстрый SymPy;
- `/explain/` — отдельное AI действие;
- `/consensus/` — отдельная независимая проверка.

---

## 7. `backend/solver/urls.py`

Актуальные routes:

```text
POST /api/solve/
POST /api/explain/
POST /api/consensus/
GET  /api/result/<job_id>/
```

---

## 8. `backend/solver/views.py`

Это HTTP orchestration boundary.

### 8.1 `SolveView`

Главный быстрый endpoint.

Алгоритм:

```text
validate request
↓
create process-local job
↓
SympySolver.solve()
↓
job.status = done/error
↓
return job JSON
```

Успех возвращает `200`.

Ошибка solve/parsing возвращает `422 Unprocessable Entity`.

#### Пример успешной формы response

```json
{
  "id": "uuid",
  "equation": "y.diff(x) - y = 0",
  "variable": "x",
  "status": "done",
  "result": {
    "steps": [
      {"type": "text", "content": "..."},
      {"type": "math", "content": "..."}
    ],
    "solution": "y(x) = ..."
  },
  "error": null
}
```

Frontend поэтому обращается к:

```javascript
result.result?.steps
result.result?.solution
```

---

### 8.2 `ExplainView`

Запускает:

```python
AIExplanationService().explain(...)
```

Успешный response содержит:

```json
{
  "steps": [],
  "solution": "...",
  "solution_expression": "...",
  "verification": {
    "verified": true,
    "score": 1.0,
    "attempts": 1,
    "model": "llama3"
  }
}
```

Если три AI попытки не прошли verifier:

```text
HTTP 422
```

Response также может содержать последнюю `verification` diagnostics.

Infrastructure/provider failure:

```text
HTTP 503
```

---

### 8.3 `ConsensusView`

Вызывает:

```python
ConsensusEngine().evaluate(...)
```

Возвращает:

- reference expression;
- best candidate;
- summary;
- equivalence groups;
- ranked candidates;
- provider statuses.

---

### 8.4 `ResultView`

Legacy/compatibility endpoint для process-local job.

Поведение:

- unknown ID -> 404;
- done -> только `job["result"]`;
- error -> 500;
- pending -> status.

Из-за синхронного `SolveView` этот endpoint не является полноценным async polling protocol в текущем UX.

---

# Часть III. Solver services

## 9. `services/job_manager.py`

Очень простой in-memory state manager.

Global:

```python
jobs = {}
```

`create_job()`:

- генерирует UUID;
- сохраняет equation;
- variable;
- status=`pending`;
- `result=None`;
- `error=None`.

`get_job()` делает lookup.

### Что важно

Это **не task queue**.

Не имеет:

- locking guarantees для multi-process deployment;
- persistence;
- queue ordering;
- workers;
- scheduling;
- durable retry.

---

## 10. `services/solvers/base_solver.py`

Базовый интерфейс/абстракция solver implementations.

Исторически использовался при переходе на class-based solver architecture.

---

## 11. `services/solvers/sympy_solver.py`

Основной быстрый пользовательский solver.

### Работа

1. создаёт independent variable;
2. создаёт `y = Function('y')(x)`;
3. строит local parsing dictionary;
4. делит input по `=`;
5. преобразует обе стороны через `parse_expr`;
6. строит `Eq`;
7. пытается `classify_ode`;
8. вызывает `dsolve`;
9. упрощает rhs;
10. формирует text/math steps;
11. возвращает LaTeX-oriented solution.

### Response shape

```python
{
    "steps": [...],
    "solution": "y(x) = ..."
}
```

### Отличие от verification reference

`MultiStageVerificationEngine.solve_reference()` отдельно вызывает `dsolve` и возвращает **SymPy expression string**, пригодный для machine verification.

Это сделано потому, что frontend-oriented `SympySolver.solution` содержит LaTeX/представление для пользователя, а verifier работает с математическим expression object/string.

---

## 12. `services/solvers/ollama_solver.py`

Адаптер локальной LLM.

### Runtime options

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=180
OLLAMA_HEALTHCHECK_TIMEOUT=1.5
```

### `healthcheck()`

Запрашивает:

```text
GET /api/tags
```

Назначение:

- быстро понять, запущен ли Ollama;
- проверить наличие требуемой модели;
- не ждать полный generation timeout в consensus.

### `_request()`

Запрашивает:

```text
POST /api/generate
```

Параметры включают:

```json
{
  "stream": false,
  "format": "json",
  "options": {"temperature": 0.15}
}
```

### Два режима prompt

#### `build_prompt()`

Самостоятельный candidate generation для consensus.

#### `build_explanation_prompt()`

Объяснение уже известного verified SymPy solution.

При повторной попытке prompt дополнительно содержит machine feedback verifier.

### JSON parsing

Файл специально защищён от характерной LLM-проблемы, когда:

- вокруг JSON есть текст;
- внутри JSON LaTeX содержит `{}`;
- модель создаёт trailing commas;
- модель возвращает несколько фрагментов.

Порядок:

1. обычный `json.loads`;
2. `JSONDecoder.raw_decode` первого полного object;
3. conservative formatting repairs;
4. повторный raw decode;
5. controlled ValueError.

Ручной подсчёт `{` / `}` не используется, потому что фигурные скобки внутри JSON strings не являются structural braces.

---

## 13. Ранние `ai_solver.py`, `deepseek_solver.py`, `fallback_solver.py`, `dispatcher.py`

Эти файлы отражают предыдущую архитектуру, где пользователь мог выбирать solver напрямую.

В актуальном UI основной routing иной:

```text
SolveView -> SympySolver
ExplainView -> AIExplanationService -> Ollama
ConsensusView -> ConsensusEngine -> CandidateProviders
```

Поэтому старый dispatcher не следует считать главным application service.

Удалять compatibility/legacy код следует только после проверки всех импортов и тестов.

---

# Часть IV. Verification subsystem

## 14. `services/verification/normalizer.py`

Ключевой parser/canonicalization layer.

### `VerificationError`

Controlled exception для unsupported/invalid mathematical representation.

### `ParsedEquation`

Хранит:

```text
equation
variable
function
residual_expression
parameters
order
```

### `NormalizedCandidate`

Хранит:

```text
raw
expression
canonical_expression
constants
```

### `parse_equation()`

Требует ровно один `=`.

Поддерживаемые predefined functions:

- exp;
- log;
- sin;
- cos;
- tan;
- sqrt;
- Derivative.

Определяет ODE order через `ode_order`.

### `parse_candidate()`

Принимает либо:

```text
C1*exp(x)
```

либо:

```text
y = C1*exp(x)
```

Если есть `=`, используется rhs.

Также:

- заменяет `^` на `**`;
- объявляет `C`, `C1...C20`;
- canonicalizes expression.

### Canonicalization

Последовательно применяет:

```text
together
trigsimp
powsimp
factor
simplify
```

---

## 15. `symbolic_verifier.py`

Главная проверка математической корректности.

Идея:

```text
original residual F(x, y, y', ...)
↓ substitute y = candidate
.doit()
↓ simplify
expected residual = 0
```

Именно этот stage является частью hard correctness gate.

---

## 16. `numerical_verifier.py`

Независимый secondary signal.

### Sample points

```text
-4, -3, -2, -1, -0.5, 0.5, 1, 2, 3, 4
```

### Constant assignments

```text
0.731
1.337
```

### Parameters

Неизвестные equation parameters получают deterministic testing value:

```text
1.11111111
```

### Tolerance

```text
1e-8
```

### Minimum evidence

Требуется не менее:

```text
6 valid checked points
```

Это исправляет ситуацию, когда почти все sample points попали в singular domain, но один случайный нулевой residual ошибочно считался достаточной проверкой.

---

## 17. `equivalence_checker.py`

Сравнивает candidate с reference family.

Использует canonical constant renaming и symbolic comparison.

Различает:

- exact canonical equivalence;
- compatible general solution family;
- mismatch.

Equivalence помогает scoring/diagnostics, но не заменяет symbolic validity.

---

## 18. `domain_validator.py`

Ищет singularities candidate и исходного equation context.

Дополнительные singularities формируют warnings.

Текущая логика специально не делает domain warning автоматическим reject, потому что корректное локальное решение может иметь ограниченную область определения.

---

## 19. `scoring.py`

Формирует explainable score.

Веса:

```text
symbolic     0.45
numerical    0.20
generality   0.15
equivalence  0.10
domain       0.10
```

Все component confidence и итоговый score clamp-ятся в `[0, 1]`.

---

## 20. `engine.py`

`MultiStageVerificationEngine` собирает все stages.

### `solve_reference()`

Использует `dsolve` и canonical SymPy rhs.

При multi-branch output:

- выбирает первую `Eq` как canonical reference;
- остальные сохраняет в `alternatives`.

### `verify()`

Главная функция подсистемы.

Возвращает:

```json
{
  "verified": true,
  "score": 0.98,
  "candidate": {},
  "symbolic": {},
  "numerical": {},
  "generality": {},
  "equivalence": {},
  "domain": {},
  "scoring": {},
  "reasons": []
}
```

### Hard gate

```python
verified = symbolic["passed"] and generality_passed
```

Это самое важное условие всей архитектуры.

---

## 21. `solution_verifier.py`

Compatibility wrapper вокруг нового multi-stage engine.

Нужен, чтобы код предыдущего этапа, импортировавший `SolutionVerifier`, не сломался одномоментно после рефакторинга.

---

# Часть V. AI subsystem

## 22. `services/ai/explanation_service.py`

`AIExplanationService` оркестрирует verified AI explanation.

### Constants

```text
MAX_ATTEMPTS = 3
```

### `explain()`

1. получает reference через verifier;
2. отправляет equation/reference в Ollama;
3. забирает `solution_expression`;
4. вызывает verifier;
5. если verified — возвращает результат;
6. иначе формирует feedback;
7. повторяет до трёх попыток;
8. после исчерпания attempts выбрасывает `AIExplanationError`.

### `_build_feedback()`

Формирует не просто текст «неправильно», а структурированную диагностику:

- candidate;
- expected reference;
- score;
- symbolic residual;
- numerical status/max residual;
- constants;
- reference relation;
- domain warnings;
- rejection reasons.

---

# Часть VI. Consensus subsystem

## 23. `services/consensus/candidate.py`

Dataclass `SolverCandidate` — унифицированное представление ответа провайдера.

Основные поля:

```text
provider
expression
solution
steps
status
error
verification
group_id
consensus_support
rank_score
```

Property `verified` используется ranking/grouping logic.

---

## 24. `providers.py`

Определяет adapter interface:

```python
CandidateProvider
```

### `SymPyCandidateProvider`

Всегда available.

Использует `VerificationEngine.solve_reference()`.

### `OllamaCandidateProvider`

Availability определяется healthcheck.

Получает machine-readable `solution_expression`.

### `OpenAICompatibleCandidateProvider`

Общий adapter OpenAI-style Chat Completions.

Используется для:

- OpenAI;
- DeepSeek.

Timeout:

```env
LLM_PROVIDER_TIMEOUT=45
```

Bounded retries:

```env
LLM_PROVIDER_MAX_RETRIES=1
```

### `build_default_providers()`

Формирует текущий набор:

```text
SymPy
Ollama
OpenAI
DeepSeek
```

Отсутствующий key -> provider unavailable.

DeepSeek key lookup поддерживает оба имени:

```text
DEEPSEEK_API_KEY
DEEP_SEEK_API_KEY
```

---

## 25. `grouping.py`

`CandidateGrouper` работает **только с verified candidates**.

Цель — определить, какие solver outputs описывают одно математическое семейство, даже если textual expressions отличаются.

После grouping каждой группе назначается support:

```text
group_size / total_verified_candidates
```

---

## 26. `ranking.py`

`CandidateRanker` рассчитывает rank только для verified кандидатов.

Формула:

```text
0.8 * verification_score
+ 0.2 * consensus_support
```

Invalid кандидат получает rank 0.

---

## 27. `consensus/engine.py`

Главный orchestration service.

### Этапы

```text
reference
↓
run providers concurrently
↓
provider status normalization
↓
verify each candidate
↓
exclude invalid from consensus correctness
↓
group equivalent verified families
↓
calculate support
↓
rank
↓
best verified candidate
```

### ThreadPoolExecutor

До 4 providers выполняются параллельно.

### Deterministic output

После concurrent completion candidates сортируются обратно в stable provider order, чтобы response и тестовые snapshots не зависели от network scheduling.

---

# Часть VII. Frontend

## 28. `frontend/package.json`

Основные runtime dependencies:

```text
react 19
react-dom 19
react-router-dom
axios
framer-motion
mathjax-react
react-scripts
```

Scripts:

```bash
npm start
npm run build
npm test
```

---

## 29. `frontend/src/App.js`

Root routing:

```text
/       -> Home
/solve  -> Solver
/help   -> Help
```

`Header` расположен над route content.

`AnimatePresence` используется для transition UX.

---

## 30. `components/Header.js`

Навигация:

- Главная;
- Решатель;
- Справка.

Active link определяется через `useLocation()`.

---

## 31. `pages/Home.js`

Landing page продукта.

Задача:

- объяснить назначение сервиса;
- направить в `/solve`;
- дать переход в help.

---

## 32. `pages/Help.js`

Документирует пользовательский ввод.

Примеры:

```text
y.diff(x) - y = 0
y.diff(x) = x * y
y.diff(x, 2) + y = 0
y.diff(x) = sin(x)
```

---

## 33. `frontend/src/api.js`

Единая transport abstraction между UI и backend.

### API base

```javascript
process.env.REACT_APP_API_URL || 'http://localhost:8000/api'
```

### Exports

```text
solveEquation()
explainWithAI()
verifyWithConsensus()
getHistory()
```

### Error parsing

Fetch-based methods используют единый `parseResponse()`:

- пытается прочитать JSON;
- на non-2xx создаёт Error;
- прикрепляет parsed `data`, чтобы React мог показать verification diagnostics.

History использует Axios.

---

## 34. `pages/Solver.js`

Главная пользовательская страница.

### State groups

#### Fast solve

```text
equation
steps
solution
loading
error
```

#### AI

```text
aiLoading
aiSteps
aiSolution
aiVerification
aiError
```

#### Consensus

```text
consensusLoading
consensusResult
consensusError
```

Разделение предотвращает конфликт UI состояний.

### `handleSubmit()`

- проверяет пустой input;
- сбрасывает старые AI/consensus данные;
- POST `/solve/`;
- читает `result.result.steps` и `result.result.solution`.

### `handleAIExplanation()`

Доступен после успешного solve.

POST `/explain/`.

Показывает:

- detailed steps;
- final solution;
- verified badge;
- confidence;
- attempts;
- model.

### `handleConsensusVerification()`

POST `/consensus/`.

Показывает:

- number of providers;
- responding providers;
- verified count;
- groups;
- consensus reached;
- best candidate;
- per-provider status;
- verification score;
- consensus support;
- provider error.

### Math rendering

`MathComponent` используется вместо вставки raw HTML.

---

## 35. `styles.css`

Содержит общие UI styles и дополнительные classes для:

- solution blocks;
- verification badges;
- AI action;
- consensus button/result;
- provider candidate cards;
- valid/invalid visual differentiation;
- error states.

---

## 36. `frontend/backend/`

Содержит старые Flask-файлы:

```text
app.py
models.py
solver.py
```

Это исторический прототип и **не является актуальным backend**, потому что runtime Django находится в root `backend/`.

При будущей cleanup-работе этот каталог можно удалить после проверки, что он не используется deployment scripts или учебными материалами.

---

# Часть VIII. Тестовый кластер

## 37. `pytest.ini`

Задаёт:

```text
DJANGO_SETTINGS_MODULE=config.settings
pythonpath=backend
testpaths=tests
```

А также markers:

```text
unit
integration
differential
property
fuzz
resilience
regression
slow
```

---

## 38. `backend/requirements-test.txt`

Подключает production dependencies и дополнительно:

```text
pytest
pytest-django
pytest-cov
hypothesis
```

---

## 39. `tests/`

### `unit/`

Проверяет verification/consensus building blocks изолированно.

### `integration/`

Проверяет DRF API boundaries.

### `differential/`

Сравнивает solver candidates и проверяет invariants consensus.

### `property/`

Генерирует целые семейства математических случаев через Hypothesis.

### `fuzz/`

Пытается сломать parser и LLM JSON extraction нестандартным вводом.

### `resilience/`

Моделирует provider outages, timeouts и self-correction failures.

### `regression/`

Фиксирует ранее найденные edge cases.

### `load/`

Отдельный concurrent probe latency/throughput `/api/solve/`.

Подробнее: [testing.md](testing.md).

---

# Часть IX. API contracts

## 40. Solve

### Request

```http
POST /api/solve/
Content-Type: application/json
```

```json
{
  "equation": "y.diff(x) - y = 0",
  "variable": "x"
}
```

### Success

Job envelope с `status=done`, `result.steps`, `result.solution`.

### Failure

`422` и job envelope с `status=error`.

---

## 41. Explain

### Request

```json
{
  "equation": "y.diff(x) - y = 0",
  "variable": "x"
}
```

### Success

```json
{
  "steps": [],
  "solution": "...",
  "solution_expression": "C1*exp(x)",
  "verification": {
    "verified": true,
    "score": 1.0,
    "attempts": 1,
    "model": "llama3",
    "symbolic": {},
    "numerical": {},
    "generality": {},
    "equivalence": {},
    "domain": {}
  }
}
```

---

## 42. Consensus

### Request

Та же форма equation/variable.

### Response high-level

```json
{
  "equation": "...",
  "variable": "x",
  "reference_expression": "...",
  "best_candidate": {},
  "summary": {
    "providers_total": 4,
    "providers_responded": 3,
    "verified_candidates": 2,
    "consensus_groups": 1,
    "consensus_reached": true
  },
  "groups": [],
  "candidates": []
}
```

---

## 43. History

```text
GET /api/history/
```

Возвращает максимум 50 последних persisted `Solution` records.

---

# Часть X. Как расширять код

## 44. Добавление нового consensus provider

1. Реализовать subclass `CandidateProvider`.
2. Реализовать:

```python
available()
solve()
```

3. Возвращать `SolverCandidate`.
4. Обязательно предоставить machine-readable `expression`.
5. Добавить provider в `build_default_providers()`.
6. Добавить unit + resilience + differential tests.

Новый provider **не должен** самостоятельно решать, валиден ли его ответ. Это задача common verifier.

---

## 45. Добавление новой verification проверки

1. Создать изолированный verifier class.
2. Его output должен быть диагностическим dict.
3. Добавить в `MultiStageVerificationEngine.verify()`.
4. Определить, является ли check:
   - hard gate;
   - secondary evidence.
5. Если check участвует в score — добавить вес.
6. Добавить tests.
7. Не изменять hard correctness semantics неявно.

---

## 46. Изменение prompt

При изменении Ollama prompt необходимо проверить:

- strict JSON contract;
- наличие `solution_expression`;
- parser fuzz tests;
- self-correction tests;
- regression tests с LaTeX braces;
- differential correctness.

Prompt change считается изменением API между LLM и backend, а не просто текстовой правкой.

---

## 47. Изменение response schema

Нужно синхронно обновить:

```text
backend serializers/views/service
frontend/src/api.js
frontend/src/pages/Solver.js
integration tests
documentation
```

---

# Часть XI. Технический долг и важные замечания

## 48. Legacy dispatcher

Не путать с `ConsensusEngine`.

`SolverDispatcher` — прежняя схема выбора solver по имени.

`ConsensusEngine` — новая схема независимого получения, математической проверки, grouping и ranking.

---

## 49. History write integration

Если продукт должен гарантированно хранить каждое solve, рекомендуется:

```text
SolveView
  ↓
Solve service
  ├─ SymPy
  ├─ Solution.objects.create
  └─ response
```

Сейчас это не обязательный шаг fast path.

---

## 50. Async execution

AI/consensus являются потенциально долгими.

Для большого deployment следует вынести их в настоящую очередь и возвращать task ID.

`job_manager` для этого недостаточен.

---

## 51. Security

Необходимо учитывать:

- API keys;
- CORS;
- CSRF policy;
- malicious parser inputs;
- resource exhaustion;
- very expensive expressions;
- LLM prompt injection через equation text;
- provider rate limits;
- API authentication/rate limiting.

Current project защищает correctness boundary, но не является законченной Internet-facing security platform.

---

## 52. Связанные документы

- [README](../README.md)
- [Архитектура](architecture.md)
- [Алгоритм](algorithm.md)
- [Тестирование](testing.md)
