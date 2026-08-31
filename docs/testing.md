# Тестирование DiffSolver

## 1. Назначение документа

Этот документ описывает тестовую стратегию проекта полностью: цели, риски, структуру тестового кластера, используемые методики, datasets, mocks, fault injection, coverage, нагрузочные проверки, команды запуска, критерии успешности и правила добавления новых тестов.

Тестирование в DiffSolver — отдельная инженерная подсистема, а не набор нескольких unit tests.

Главная причина: проект сочетает математические вычисления, parsing, web API, внешние LLM providers, локальный runtime и собственный verification/consensus algorithm. Ошибка может возникнуть на любом из этих уровней и внешне выглядеть одинаково как «неверный ответ».

---

## 2. Цели тестирования

Тестовый кластер должен давать уверенность в следующих свойствах:

1. математически правильные решения принимаются verifier;
2. математически неправильные решения отклоняются;
3. частное решение не принимается как общее решение ОДУ более высокого порядка;
4. разные формы записи одного решения корректно сравниваются;
5. consensus не способен сделать неправильный ответ валидным;
6. несколько одинаковых ошибочных providers не могут переголосовать правильный кандидат;
7. self-correction действительно повторяет генерацию после ошибки и имеет верхнюю границу попыток;
8. malformed input не приводит к uncontrolled backend exceptions;
9. malformed LLM JSON обрабатывается контролируемо;
10. network/provider failures изолированы;
11. отсутствие API-ключей не ломает систему;
12. выключенная Ollama определяется быстро;
13. REST API сохраняет ожидаемые контракты;
14. history endpoint соблюдает порядок выдачи;
15. ранее найденные дефекты не появляются повторно;
16. fast SymPy endpoint выдерживает базовую concurrent нагрузку.

---

## 3. Почему одних unit tests недостаточно

Unit tests способны проверить отдельную функцию, но не доказывают корректность всей системы.

Пример цепочки:

```text
React
↓
DRF serializer
↓
view
↓
LLM
↓
JSON parser
↓
normalizer
↓
verification
↓
consensus
↓
response
```

Каждый компонент может пройти unit tests отдельно, а integration contract между двумя соседними слоями — сломаться.

Поэтому кластер использует несколько независимых методик.

---

## 4. Структура тестов

```text
tests/
├── conftest.py
├── datasets/
│   └── verified_odes.json
├── unit/
│   ├── test_normalizer.py
│   ├── test_symbolic_verifier.py
│   ├── test_equivalence_checker.py
│   ├── test_domain_validator.py
│   ├── test_scoring.py
│   ├── test_verification_engine.py
│   └── test_consensus_grouping_and_ranking.py
├── integration/
│   ├── test_solver_api.py
│   ├── test_explain_api.py
│   ├── test_consensus_api.py
│   └── test_history_api.py
├── differential/
│   ├── test_verified_dataset.py
│   └── test_consensus_engine.py
├── property/
│   └── test_generated_linear_odes.py
├── fuzz/
│   ├── test_parser_fuzz.py
│   └── test_llm_json_parser.py
├── resilience/
│   ├── test_provider_failures.py
│   ├── test_self_correction.py
│   └── test_ollama_availability.py
├── regression/
│   ├── test_known_edge_cases.py
│   └── test_stabilization_regressions.py
└── load/
    └── load_solve.py
```

---

## 5. Конфигурация pytest

Корневой `pytest.ini` задаёт:

```ini
DJANGO_SETTINGS_MODULE = config.settings
pythonpath = backend
testpaths = tests
```

Это позволяет импортировать Django apps как в реальном backend runtime.

Включены strict settings:

```text
--strict-markers
--strict-config
```

Ошибочная marker/config запись поэтому не игнорируется молча.

---

## 6. Test markers

Определены категории:

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

Пример выборочного запуска:

```bash
pytest -m unit
pytest -m resilience
pytest -m "differential or regression"
```

Даже если конкретный файл не использует marker-декоратор на каждой функции, структура каталогов позволяет запускать нужный слой по path.

---

## 7. Установка тестового окружения

Из корня репозитория:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-test.txt
```

`requirements-test.txt` включает production dependencies и:

```text
pytest
pytest-django
pytest-cov
hypothesis
```

---

## 8. Полный автоматизированный прогон

```bash
./scripts/run_test_cluster.sh
```

Скрипт запускает:

```text
unit
differential
property
fuzz
integration
resilience
regression
```

Load test специально не включён в обычный suite, потому что требует запущенный HTTP server и измеряет runtime характеристики, а не deterministic correctness.

---

## 9. Отчёты

`run_test_cluster.sh` создаёт:

```text
.pytest_cache/reports/coverage.xml
.pytest_cache/reports/junit.xml
```

Также в терминал выводится coverage с missing lines.

Coverage собирается для:

```text
solver
history
```

### Назначение XML

`coverage.xml` можно использовать в CI/code quality tools.

`junit.xml` можно импортировать в CI test reports.

---

# Часть I. Unit testing

## 10. Цель unit layer

Проверить чистую бизнес-логику отдельно от HTTP, базы и внешних LLM.

Особенно важно для Verification Engine: если базовый математический primitive работает неправильно, integration tests не смогут точно локализовать причину.

---

## 11. `test_normalizer.py`

Проверяет:

### First-order parsing

Verifier должен корректно определить:

- функцию;
- variable;
- order=1.

### Second-order parsing

Уравнение второго порядка должно давать order=2.

### Candidate syntax normalization

Проверяется поддержка:

```text
^
```

и arbitrary constants.

### Invalid equation format

Уравнение без ровно одного `=` должно породить controlled `VerificationError`.

### Empty candidate

Пустой machine-readable candidate отклоняется до математических проверок.

---

## 12. `test_symbolic_verifier.py`

Проверяет два базовых математических инварианта:

### Valid candidate

После подстановки residual точно ноль.

### Invalid candidate

Ненулевой residual не должен быть принят.

Это один из наиболее критичных unit modules.

---

## 13. `test_equivalence_checker.py`

Проверяет:

- произвольные имена integration constants не должны ломать equivalence;
- разные solution families не должны ошибочно считаться exact-equivalent.

Это защищает consensus/grouping от string-comparison ошибок.

---

## 14. `test_domain_validator.py`

Два типа singularity:

### Shared singularity

Если singularity обусловлена уже исходным уравнением, candidate не должен получать ложное предупреждение как будто он создал новую проблему.

### Candidate-only singularity

Если solution вносит дополнительную singularity, она должна попасть в diagnostics.

---

## 15. `test_scoring.py`

Проверяет:

- все component confidence=1 -> score=1;
- symbolic failure должен существенно снижать confidence;
- final stabilization regression отдельно проверяет bounded interval `[0,1]`.

Важно: эти тесты проверяют score, но verified state определяется отдельными hard gates.

---

## 16. `test_verification_engine.py`

End-to-end внутри mathematical subsystem без HTTP.

Проверяет:

### Valid general solution

Correct first-order candidate принимается.

### Wrong solution

Mathematically incorrect candidate отклоняется.

### Generality

Для second-order ОДУ candidate без второй arbitrary constant отклоняется, даже если представляет частное решение.

---

## 17. `test_consensus_grouping_and_ranking.py`

Проверяет:

- equivalent verified candidates образуют одну consensus group;
- invalid candidate не может выиграть ranking даже при искусственно заданной высокой consensus support.

Последний test непосредственно защищает главный конкурентный инвариант проекта.

---

# Часть II. Integration testing

## 18. Цель

Проверить Django/DRF boundaries и реальные response contracts, но не выполнять дорогие внешние LLM calls.

---

## 19. `test_solver_api.py`

Проверяет:

### Fast solve success

`POST /api/solve/` с валидным equation должен вернуть SymPy result.

### Missing equation

Serializer должен отклонить request без required field.

### Unknown job

`GET /api/result/<unknown>/` -> 404.

---

## 20. `test_explain_api.py`

Использует fake explanation service через monkeypatch.

Это важно: integration test проверяет **контракт DRF endpoint**, а не доступность реальной Llama.

Преимущества:

- test deterministic;
- не нужен GPU;
- не нужен Ollama;
- не платится API;
- CI может работать offline.

---

## 21. `test_consensus_api.py`

Аналогично использует fake consensus engine.

Проверяет JSON boundary и то, что view корректно делегирует business service.

---

## 22. `test_history_api.py`

Создаёт records и проверяет:

```text
newest first
```

То есть Django query ordering является частью публичного API contract.

---

# Часть III. Differential testing

## 23. Что такое differential testing в этом проекте

Один mathematical input проверяется через независимые representations/solvers/invariants.

Это особенно подходит DiffSolver, потому что цель проекта — сравнение heterogeneous candidates.

---

## 24. `test_verified_dataset.py`

Использует curated dataset эталонных ОДУ.

Каждый case имеет:

```json
{
  "id": "...",
  "category": "...",
  "equation": "...",
  "solution": "..."
}
```

Dataset прогоняется с reference mode и без него.

Цель:

- candidate должен быть валиден относительно исходного ОДУ;
- optional reference comparison не должен ломать правильный ответ.

---

## 25. Dataset categories

Набор включает:

### First order linear

```text
Derivative(y, x) - y = 0
Derivative(y, x) + y = 0
```

### Direct integration

```text
Derivative(y, x) - 2*x = 0
Derivative(y, x) - cos(x) = 0
Derivative(y, x) - exp(x) = 0
```

### Separable / variable coefficient

```text
Derivative(y, x) + 2*x*y = 0
```

### Singular domain

```text
Derivative(y, x) - 1/x = 0
```

### Second order

```text
Derivative(y, (x, 2)) + y = 0
Derivative(y, (x, 2)) - y = 0
Derivative(y, (x, 2)) = 0
```

---

## 26. `test_consensus_engine.py`

Самый важный differential scenario:

### Wrong majority cannot overrule valid minority

Моделируется ситуация, где несколько providers возвращают одно неверное expression, а один — корректное.

Expected behaviour:

```text
wrong majority -> invalid -> cannot win
correct minority -> verified -> eligible best
```

Это тест конкурентной особенности проекта, а не библиотечного поведения.

### Equivalent valid candidates

Проверяется рост consensus support, когда несколько независимых providers дают эквивалентное подтверждённое семейство.

---

# Часть IV. Property-based testing

## 27. Почему property-based testing

Hand-written examples проверяют только конкретные значения.

Hypothesis генерирует множество вариантов из заданного пространства и ищет counterexamples автоматически.

---

## 28. `test_generated_linear_odes.py`

### Exponential families

Генерируется ненулевой integer coefficient и проверяется семейство first-order linear ODE.

Цель — verifier должен сохранять invariant для множества коэффициентов, а не только для `1`.

### Direct integral families

Генерируются slopes в диапазоне.

Проверяется solution family для автоматически построенных equations.

---

## 29. Что даёт Hypothesis

Если test упал, Hypothesis пытается shrink input до минимального контрпримера.

Это помогает обнаруживать cases вроде:

- coefficient `-1`;
- zero-like boundary;
- sign transformations;
- small values, которые ручной набор легко пропустить.

---

# Часть V. Fuzz testing

## 30. Parser fuzzing

`test_parser_fuzz.py` генерирует случайные строки из безопасного alphabet.

Проверяется, что random input:

- либо корректно parse;
- либо приводит к ожидаемому controlled exception boundary;
- но не «прорывается» неожиданным классом ошибки наружу.

Проверяются отдельно:

- equation parser;
- candidate parser.

---

## 31. LLM JSON fuzz/regression testing

`test_llm_json_parser.py` проверяет:

### Clean payload

Обычный валидный JSON.

### Surrounding text

LLM может написать текст до/после JSON. Parser должен извлечь первый полный object.

### Incomplete object

Broken JSON должен привести к controlled error.

---

## 32. Почему JSON parser критичен

LLM output — недоверенный transport format.

Особенно сложны LaTeX strings:

```text
\frac{1}{x}
\left\{ ... \right\}
```

Фигурные скобки внутри строки не являются JSON structural braces.

Именно тестирование этого случая привело к переходу на `JSONDecoder.raw_decode()`.

---

# Часть VI. Resilience и fault injection

## 33. Цель

Проверить поведение системы, когда внешние компоненты не работают.

Correctness проекта включает не только «правильный ответ при идеальных условиях», но и controlled degradation.

---

## 34. `test_provider_failures.py`

Моделируются providers:

- good;
- timeout/error;
- disabled/unavailable.

Проверяется, что consensus:

- продолжает выполнение;
- сохраняет статусы;
- не падает целиком из-за одного provider.

---

## 35. Cloud provider without key

Отдельно проверяется:

```text
no API key -> unavailable
```

а не uncontrolled client initialization error.

---

## 36. `test_ollama_availability.py`

Проверяет:

### Offline Ollama

Provider должен сообщить unavailable до expensive generation.

### Fast healthcheck

Consensus должен использовать short healthcheck path.

Это regression от проблемы, когда выключенная Ollama заставляла ждать полный model timeout.

---

## 37. `test_self_correction.py`

Используются fake models.

### Correcting model

Первая попытка неправильна, следующая использует feedback и исправляется.

Expected:

```text
attempt 1 -> rejected
attempt 2 -> verified
```

### Always wrong model

Все попытки неправильны.

Expected:

```text
exactly MAX_ATTEMPTS
then AIExplanationError
```

Это проверяет bounded-loop invariant.

---

# Часть VII. Regression testing

## 38. Назначение

Любой найденный реальный дефект должен получить regression test до/вместе с исправлением.

Иначе bug может вернуться при следующем refactoring.

---

## 39. `test_known_edge_cases.py`

### Constant renaming

Разные arbitrary constant names не должны ухудшать reference equivalence.

### Missing integration constant

Second-order candidate с одной constant должен быть rejected.

### Invalid high-score candidate

Даже если synthetic score/support высокий, invalid candidate не может подняться выше verified.

---

## 40. `test_stabilization_regressions.py`

Фиксирует проблемы, найденные после запуска test cluster.

### Braces inside JSON string

Ollama parser должен корректно обработать LaTeX braces.

### OpenAI-compatible parser

Должен извлекать object при trailing text и braces в strings.

### Score boundaries

Итоговый verification score всегда:

```text
0 <= score <= 1
```

### Numerical evidence

Numerical verifier не может принять candidate по единственной случайной valid sample point.

---

# Часть VIII. Load testing

## 41. Почему load probe отдельно

Load testing зависит от:

- hardware;
- OS;
- Python version;
- server configuration;
- background load.

Поэтому он не должен быть обычным deterministic pytest assertion suite.

---

## 42. `tests/load/load_solve.py`

Тестирует fast endpoint:

```text
POST /api/solve/
```

Использует `ThreadPoolExecutor`.

Параметры:

```text
--url
--requests
--workers
--timeout
--min-success-rate
```

Defaults:

```text
requests = 100
workers = 10
timeout = 10s
min success rate = 99%
```

---

## 43. Метрики load probe

Выводит:

- requests count;
- success rate;
- wall time;
- throughput requests/sec;
- mean latency;
- p50 latency;
- p95 latency;
- max latency.

Если success rate ниже threshold, process завершится с failure code.

---

## 44. Пример запуска

Сначала backend:

```bash
source .venv/bin/activate
python backend/manage.py runserver
```

Затем:

```bash
python tests/load/load_solve.py --requests 200 --workers 20
```

Для сравнения результатов нужно фиксировать:

- hardware;
- Python version;
- server mode;
- commit hash;
- equation payload;
- concurrency.

Без этого сравнивать req/s между машинами некорректно.

---

# Часть IX. Risk-based coverage

## 45. Карта рисков

| Риск | Основные тесты |
|---|---|
| Неверный residual принят | symbolic unit, verification engine, dataset |
| Частное решение принято как общее | verification unit, regression |
| Эквивалентные решения считаются разными | equivalence unit, consensus differential |
| Ошибочное большинство выигрывает | differential consensus, ranking regression |
| LLM невалидный JSON | fuzz, stabilization regression |
| Ollama offline тормозит запрос | resilience Ollama |
| Cloud provider недоступен | resilience provider failures |
| Self-correction бесконечен | resilience self-correction |
| DRF contract сломан | integration |
| History order изменился | history integration |
| Parser падает на случайном input | fuzz/property |
| Algorithm работает только на 2-3 примерах | dataset + property |
| Низкая availability под concurrent solve | load probe |

---

## 46. Testing pyramid в проекте

У проекта не классическая чистая pyramid, потому что mathematical differential/property tests имеют особенно высокую ценность.

Логически:

```text
                Load / manual
            Resilience / regression
       Integration / differential
       Property-based / fuzz
              Unit
```

Unit layer самый быстрый, но differential layer является критичным для собственной алгоритмической особенности.

---

# Часть X. Mocking policy

## 47. Что mock-ается

В автоматических integration/resilience tests допустимо mock-ать:

- Ollama generation;
- OpenAI;
- DeepSeek;
- slow/unavailable providers;
- AIExplanationService на view boundary;
- ConsensusEngine на view boundary.

---

## 48. Что нельзя mock-ать в математических correctness tests

Если цель test — доказать поведение verifier, нельзя подменять:

- SolutionNormalizer;
- SymbolicVerifier;
- MultiStageVerificationEngine;
- ranking invariant.

Иначе test проверял бы mock, а не алгоритм.

---

## 49. Почему реальные облачные API не нужны в CI

Причины:

- нестабильная сеть;
- rate limits;
- стоимость;
- model updates;
- nondeterminism;
- секреты;
- latency.

Реальный provider smoke test можно выполнять отдельно вручную/staging, но он не должен определять корректность core suite.

---

# Часть XI. Manual testing

## 50. Минимальный smoke checklist

После крупных изменений:

### Backend

```text
[ ] server starts
[ ] migrations apply
[ ] /api/solve/ works
[ ] invalid equation produces controlled error
[ ] /api/history/ works
```

### Frontend

```text
[ ] Home opens
[ ] Help opens
[ ] Solver accepts input
[ ] SymPy steps render
[ ] MathJax renders formulas
[ ] errors are visible
```

### Ollama

```text
[ ] offline -> quick unavailable/error
[ ] online + model -> AI button works
[ ] explanation shows verification badge
[ ] attempts displayed
```

### Consensus

```text
[ ] no cloud keys does not break flow
[ ] provider statuses visible
[ ] verified candidates count shown
[ ] best candidate appears only if verified
```

---

## 51. Suggested manual ODE set

```text
y.diff(x) - y = 0
y.diff(x) + y = 0
y.diff(x) = 2*x
y.diff(x) + 2*x*y = 0
y.diff(x) = 1/x
y.diff(x, 2) + y = 0
y.diff(x, 2) - y = 0
y.diff(x, 2) = 0
```

Дополнительно нужны intentionally invalid inputs:

```text
"
abc
x + 1
x = 1 = 2
y.diff(x) =
y.diff(x, 999999) = 0
```

Последний тип inputs полезен также для resource-limit/security testing.

---

# Часть XII. Coverage

## 52. Что означает code coverage

Coverage показывает, какие строки/branches выполнялись тестами.

Coverage **не означает математическую корректность**.

100% line coverage может существовать при неправильных assertions.

Поэтому проект сочетает coverage с:

- differential invariants;
- property generation;
- fuzzing;
- curated mathematical dataset.

---

## 53. Coverage targets

Проект не должен оптимизироваться под искусственный процент любой ценой.

Приоритет покрытия:

1. Verification Engine;
2. Consensus Engine;
3. AI correction orchestration;
4. DRF endpoints;
5. parser/error handling;
6. history;
7. utility/legacy paths по мере необходимости.

---

## 54. Как смотреть пропуски

`run_test_cluster.sh` использует:

```text
--cov-report=term-missing
```

Поэтому терминал показывает номера непокрытых строк.

---

# Часть XIII. Критерии успешности

## 55. Перед merge/финальным коммитом

Минимально:

```text
1. pytest cluster exits 0
2. no unexpected warnings/errors
3. regression suite passes
4. wrong-majority invariant passes
5. self-correction bound passes
6. API integration contracts pass
7. coverage report generated
```

Если менялся performance-critical fast path, дополнительно запускается load probe.

---

## 56. Когда test failure блокирующий

Всегда блокирующие failures:

- symbolic validity;
- generality;
- invalid candidate ranking;
- self-correction unbounded;
- provider failure crashes consensus;
- API returns 500 вместо controlled expected error;
- regression test previously fixed bug.

---

# Часть XIV. Как добавлять тесты

## 57. Новый bug

Правильный workflow:

```text
reproduce bug
↓
write failing regression test
↓
fix code
↓
prove test passes
↓
run wider affected suites
```

---

## 58. Новый solver provider

Добавить tests:

```text
unit availability/config
resilience no-key/offline/timeout
provider JSON parsing
consensus integration with provider
wrong candidate verification
```

Не обязательно делать real network calls.

---

## 59. Новый класс ОДУ

1. Добавить curated dataset cases.
2. Добавить property strategy, если возможно.
3. Проверить valid candidate.
4. Создать intentionally wrong candidate.
5. Проверить order/generality.
6. Проверить domain edge cases.
7. Проверить consensus grouping.

---

## 60. Изменение scoring weights

Нужно проверить:

- score bounds;
- full confidence;
- penalty behaviour;
- invalid candidate rank remains zero;
- existing dataset;
- differential ranking cases.

Изменение weights не должно неявно менять `verified` semantics.

---

## 61. Изменение JSON parser

Обязательно прогнать:

```text
tests/fuzz/test_llm_json_parser.py
tests/regression/test_stabilization_regressions.py
tests/resilience
```

И добавить case, который послужил причиной изменения.

---

# Часть XV. CI readiness

## 62. Минимальный CI pipeline

Проект уже подготовлен к типичному pipeline:

```text
checkout
↓
setup Python
↓
pip install requirements-test
↓
pytest cluster
↓
collect JUnit XML
↓
collect coverage XML
↓
frontend npm ci
↓
frontend build/test
```

External LLM secrets для core CI не требуются, потому что expensive/non-deterministic calls mock-аются.

---

## 63. Recommended CI split

### Fast PR checks

```text
unit
integration
regression
```

### Full checks

```text
differential
property
fuzz
resilience
coverage
```

### Scheduled/staging

```text
load
real Ollama smoke
optional real cloud provider smoke
```

---

# Часть XVI. Результаты и интерпретация

## 64. Как фиксировать результат прогона

Для воспроизводимости записывайте:

```text
commit hash
date
Python version
OS
SymPy version
pytest version
number of passed/failed/skipped
coverage
hardware для load
```

---

## 65. Почему документация не фиксирует один вечный pass count

Количество тестов меняется вместе с проектом.

Жёсткая запись вида:

```text
«в проекте всегда 38 тестов»
```

быстро становится ложной после добавления даже одного regression case.

Поэтому источником истины является текущий command:

```bash
./scripts/run_test_cluster.sh
```

а JUnit report фиксирует результат конкретной ревизии.

В ходе разработки test cluster использовался для обнаружения и закрытия реальных failure modes, включая JSON/LaTeX parsing, недостаточное numerical evidence и provider availability/timeout behaviour.

---

# Часть XVII. Ограничения тестового кластера

## 66. Не покрывается формально

Текущий suite не является доказательством для всех возможных ОДУ.

Ограничения:

- finite curated dataset;
- ограниченное Hypothesis generation space;
- нет formal proof correctness SymPy itself;
- UI browser E2E не является центральной частью текущего Python cluster;
- нет длительных soak tests;
- нет distributed/multi-process concurrency tests;
- нет security penetration suite;
- реальные LLM models могут измениться независимо от repository code;
- load probe использует development-style HTTP path и не заменяет production benchmarking.

---

## 67. Что стоит добавить далее

- Playwright/Cypress end-to-end frontend tests;
- mutation testing verifier rules;
- long-running soak tests;
- adversarial symbolic complexity dataset;
- timeout/resource limits для pathological SymPy input;
- randomized domain-aware numerical sampling;
- benchmark corpus с ground truth;
- provider quality statistics по категориям ОДУ;
- CI matrix нескольких Python/SymPy versions;
- production load test через Gunicorn/Uvicorn + reverse proxy.

---

## 68. Связанные документы

- [README](../README.md)
- [Архитектура](architecture.md)
- [Кодовая база](codebase.md)
- [Алгоритм](algorithm.md)
