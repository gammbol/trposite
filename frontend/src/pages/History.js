import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { clearHistory, deleteHistoryEntry, getHistory } from '../api';
import MathFormula from '../components/MathFormula';
import './History.css';

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function normalizeEntries(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.results)) return payload.results;
  return [];
}

export default function History() {
  const [entries, setEntries] = useState([]);
  const [expanded, setExpanded] = useState(() => new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [clearing, setClearing] = useState(false);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getHistory(100);
      setEntries(normalizeEntries(payload));
    } catch (err) {
      setError(err.message || 'Не удалось загрузить историю');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const toggleExpanded = (id) => {
    setExpanded((current) => {
      const next = new Set(current);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const removeEntry = async (id) => {
    if (!window.confirm('Удалить эту запись из истории?')) return;
    setBusyId(id);
    setError(null);
    try {
      await deleteHistoryEntry(id);
      setEntries((current) => current.filter((entry) => entry.id !== id));
      setExpanded((current) => {
        const next = new Set(current);
        next.delete(id);
        return next;
      });
    } catch (err) {
      setError(err.message || 'Не удалось удалить запись');
    } finally {
      setBusyId(null);
    }
  };

  const removeAll = async () => {
    if (!window.confirm('Удалить всю историю решений?')) return;
    setClearing(true);
    setError(null);
    try {
      await clearHistory();
      setEntries([]);
      setExpanded(new Set());
    } catch (err) {
      setError(err.message || 'Не удалось очистить историю');
    } finally {
      setClearing(false);
    }
  };

  return (
    <main className="page history-page">
      <div className="history-heading">
        <div>
          <h2>История решений</h2>
          <p>
            Все успешные решения сохраняются в SQLite и остаются доступными
            после перезапуска контейнеров.
          </p>
        </div>
        <div className="history-toolbar">
          <button type="button" className="secondary-button" onClick={loadHistory} disabled={loading}>
            {loading ? 'Обновляем…' : 'Обновить'}
          </button>
          {entries.length > 0 && (
            <button type="button" className="history-danger-button" onClick={removeAll} disabled={clearing}>
              {clearing ? 'Очищаем…' : 'Очистить всё'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="error-box history-error">
          <strong>История недоступна.</strong>
          <p>{error}</p>
          <button type="button" className="secondary-button" onClick={loadHistory}>Повторить</button>
        </div>
      )}

      {loading && <div className="history-state">Загружаем историю…</div>}

      {!loading && !error && entries.length === 0 && (
        <div className="history-empty">
          <h3>История пока пуста</h3>
          <p>Решите любое уравнение — результат автоматически появится здесь.</p>
          <Link className="history-solver-link" to="/solve">Перейти к решателю</Link>
        </div>
      )}

      {!loading && entries.length > 0 && (
        <div className="history-list">
          {entries.map((entry) => {
            const isExpanded = expanded.has(entry.id);
            const steps = Array.isArray(entry.steps) ? entry.steps : [];

            return (
              <article className="history-card" key={entry.id}>
                <div className="history-card-header">
                  <div className="history-card-title">
                    <div className="history-meta">
                      <span>#{entry.id}</span>
                      <time>{formatDate(entry.created_at)}</time>
                    </div>
                    <h3>{entry.equation || 'Уравнение не сохранено'}</h3>
                  </div>
                  <button
                    type="button"
                    className="history-delete-button"
                    onClick={() => removeEntry(entry.id)}
                    disabled={busyId === entry.id}
                  >
                    {busyId === entry.id ? 'Удаляем…' : 'Удалить'}
                  </button>
                </div>

                <div className="history-answer">
                  <span className="history-label">Ответ</span>
                  {entry.solution ? <MathFormula tex={entry.solution} /> : <span>—</span>}
                </div>

                <button
                  type="button"
                  className="history-expand-button"
                  onClick={() => toggleExpanded(entry.id)}
                  disabled={steps.length === 0}
                >
                  {steps.length === 0
                    ? 'Шаги не сохранены'
                    : isExpanded
                      ? 'Скрыть шаги'
                      : `Показать шаги (${steps.length})`}
                </button>

                {isExpanded && steps.length > 0 && (
                  <div className="history-steps">
                    <ol>
                      {steps.map((step, index) => (
                        <li key={`${entry.id}-${index}`}>
                          {step?.type === 'math'
                            ? <MathFormula tex={step.content || ''} />
                            : <p>{step?.content || ''}</p>}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}
