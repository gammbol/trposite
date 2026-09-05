import React, { useState } from 'react';
import { explainWithAI, solveEquation, verifyWithConsensus } from '../api';
import MathFormula from '../components/MathFormula';

export default function Solver() {
  const [equation, setEquation] = useState('');
  const [steps, setSteps] = useState([]);
  const [solution, setSolution] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSteps, setAiSteps] = useState([]);
  const [aiSolution, setAiSolution] = useState(null);
  const [aiVerification, setAiVerification] = useState(null);
  const [aiError, setAiError] = useState(null);

  const [consensusLoading, setConsensusLoading] = useState(false);
  const [consensusResult, setConsensusResult] = useState(null);
  const [consensusError, setConsensusError] = useState(null);

  const resetAI = () => {
    setAiSteps([]);
    setAiSolution(null);
    setAiVerification(null);
    setAiError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!equation.trim()) {
      setError('Введите уравнение');
      return;
    }

    setLoading(true);
    setError(null);
    setSteps([]);
    setSolution(null);
    resetAI();
    setConsensusResult(null);
    setConsensusError(null);

    try {
      const result = await solveEquation({
        equation,
        variable: 'x',
      });

      setSteps(result.result?.steps || []);
      setSolution(result.result?.solution || '');
    } catch (err) {
      setError(err.message || 'Ошибка при обработке запроса');
    } finally {
      setLoading(false);
    }
  };

  const handleAIExplanation = async () => {
    if (!equation.trim() || !solution) {
      return;
    }

    setAiLoading(true);
    resetAI();

    try {
      const result = await explainWithAI({
        equation,
        variable: 'x',
      });

      setAiSteps(result.steps || []);
      setAiSolution(result.solution || '');
      setAiVerification(result.verification || null);
    } catch (err) {
      setAiError(err.message || 'Не удалось получить объяснение ИИ');
      if (err.data?.verification) {
        setAiVerification(err.data.verification);
      }
    } finally {
      setAiLoading(false);
    }
  };

  const handleConsensusVerification = async () => {
    if (!equation.trim() || !solution) {
      return;
    }

    setConsensusLoading(true);
    setConsensusError(null);
    setConsensusResult(null);

    try {
      const result = await verifyWithConsensus({
        equation,
        variable: 'x',
      });
      setConsensusResult(result);
    } catch (err) {
      setConsensusError(err.message || 'Не удалось выполнить независимую проверку');
    } finally {
      setConsensusLoading(false);
    }
  };

  return (
    <div className="page">
      <h2>Решение дифференциальных уравнений</h2>
      <p className="solver-subtitle">
        Сначала система быстро получает решение через SymPy. После этого его
        можно отдельно разобрать с помощью локального ИИ.
      </p>

      <form className="form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Пример: y.diff(x) - y = 0"
          value={equation}
          onChange={(e) => setEquation(e.target.value)}
        />

        <div className="controls">
          <button className="primary-button" type="submit" disabled={loading || aiLoading}>
            {loading ? 'Решаем...' : 'Решить'}
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => setShowHelp(!showHelp)}
          >
            {showHelp ? 'Скрыть подсказку' : 'Подсказка'}
          </button>
        </div>
      </form>

      {error && (
        <div className="error-box">
          <p>{error}</p>
        </div>
      )}

      {showHelp && (
        <div className="help-box">
          <ul>
            <li><code>y.diff(x)</code> — производная</li>
            <li><code>y.diff(x, 2)</code> — вторая производная</li>
            <li>Используйте <code>=</code> для уравнения</li>
            <li><strong>y(x)</strong> — обязательная функция</li>
          </ul>
        </div>
      )}

      {steps.length > 0 && (
        <div className="solution">
          <div className="solution-header">
            <h3>Пошаговое решение SymPy</h3>
            <span className="verification-badge verified">быстрое решение</span>
          </div>
          <ol>
            {steps.map((step, index) => (
              <li key={index}>
                {step.type === 'math' ? (
                  <MathFormula tex={step.content} />
                ) : (
                  <p>{step.content}</p>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}

      {solution && (
        <div className="solution final">
          <h3>Ответ:</h3>
          <MathFormula tex={solution} />
          <div className="ai-action">
            <p>
              Нужен подробный разбор? Локальная модель объяснит решение, а
              backend сохранит проверенный SymPy-ответ неизменным и нормализует
              математические шаги объяснения перед отображением.
            </p>
            <button
              className="ai-button"
              type="button"
              onClick={handleAIExplanation}
              disabled={aiLoading || loading}
            >
              {aiLoading ? 'ИИ готовит объяснение...' : 'Объяснить с помощью ИИ'}
            </button>
            <button
              className="consensus-button"
              type="button"
              onClick={handleConsensusVerification}
              disabled={consensusLoading || aiLoading || loading}
            >
              {consensusLoading ? 'Сравниваем решатели...' : 'Проверить другими методами'}
            </button>
          </div>
        </div>
      )}

      {consensusError && (
        <div className="error-box">
          <strong>Независимая проверка не завершена.</strong>
          <p>{consensusError}</p>
        </div>
      )}

      {consensusResult && (
        <div className="solution consensus-result">
          <div className="solution-header">
            <h3>Независимая проверка решателями</h3>
            {consensusResult.summary?.consensus_reached && (
              <span className="verification-badge verified">консенсус достигнут</span>
            )}
          </div>
          <div className="verification-summary">
            <span>Ответили: {consensusResult.summary?.providers_responded || 0}/{consensusResult.summary?.providers_total || 0}</span>
            <span>Проверено: {consensusResult.summary?.verified_candidates || 0}</span>
            <span>Групп решений: {consensusResult.summary?.consensus_groups || 0}</span>
          </div>
          {consensusResult.best_candidate && (
            <div className="consensus-best">
              <strong>Лучший подтверждённый кандидат:</strong>
              <span>{consensusResult.best_candidate.provider}</span>
              <span>rank {Math.round((consensusResult.best_candidate.rank_score || 0) * 100)}%</span>
            </div>
          )}
          <div className="candidate-grid">
            {(consensusResult.candidates || []).map((candidate) => (
              <div
                className={`candidate-card ${candidate.verified ? 'candidate-valid' : 'candidate-invalid'}`}
                key={candidate.provider}
              >
                <div className="candidate-title">
                  <strong>{candidate.provider}</strong>
                  <span>{candidate.verified ? '✓ verified' : candidate.status}</span>
                </div>
                {candidate.verification && (
                  <p>Verification: {Math.round((candidate.verification.score || 0) * 100)}%</p>
                )}
                {candidate.consensus_support > 0 && (
                  <p>Consensus support: {Math.round(candidate.consensus_support * 100)}%</p>
                )}
                {candidate.error && <p className="candidate-error">{candidate.error}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {aiError && (
        <div className="error-box ai-error-box">
          <strong>AI-объяснение не прошло проверку.</strong>
          <p>{aiError}</p>
        </div>
      )}

      {aiSteps.length > 0 && (
        <div className="solution ai-solution">
          <div className="solution-header">
            <h3>Подробное объяснение ИИ</h3>
            {aiVerification?.verified && (
              <span className="verification-badge verified">итог проверен</span>
            )}
          </div>
          {aiVerification && (
            <div className="verification-summary">
              <span>Проверка ответа: {Math.round((aiVerification.score || 0) * 100)}%</span>
              <span>Попыток: {aiVerification.attempts || 1}</span>
              <span>Модель: {aiVerification.model || 'ollama'}</span>
            </div>
          )}
          <ol>
            {aiSteps.map((step, index) => (
              <li key={index}>
                {step.type === 'math' ? (
                  <MathFormula tex={step.content} />
                ) : (
                  <p>{step.content}</p>
                )}
              </li>
            ))}
          </ol>
          {aiSolution && (
            <div className="ai-final-answer">
              <h4>Проверенный итог SymPy:</h4>
              <MathFormula tex={aiSolution} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
