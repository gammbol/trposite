import React, { useState } from 'react';
import { explainWithAI, solveEquation } from '../api';
import { MathComponent } from 'mathjax-react';
import { motion } from 'framer-motion';

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

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
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
                  <MathComponent tex={step.content} display={true} />
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
          <MathComponent tex={solution} display={true} />

          <div className="ai-action">
            <p>
              Нужен подробный разбор? Локальная модель объяснит решение, а
              backend автоматически проверит её итог и при ошибке попросит ИИ
              исправить решение.
            </p>
            <button
              className="ai-button"
              type="button"
              onClick={handleAIExplanation}
              disabled={aiLoading || loading}
            >
              {aiLoading ? 'ИИ решает и проходит проверку...' : 'Объяснить с помощью ИИ'}
            </button>
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
              <span className="verification-badge verified">проверено</span>
            )}
          </div>

          {aiVerification && (
            <div className="verification-summary">
              <span>Confidence: {Math.round((aiVerification.score || 0) * 100)}%</span>
              <span>Попыток: {aiVerification.attempts || 1}</span>
              <span>Модель: {aiVerification.model || 'ollama'}</span>
            </div>
          )}

          <ol>
            {aiSteps.map((step, index) => (
              <li key={index}>
                {step.type === 'math' ? (
                  <MathComponent tex={step.content} display={true} />
                ) : (
                  <p>{step.content}</p>
                )}
              </li>
            ))}
          </ol>

          {aiSolution && (
            <div className="ai-final-answer">
              <h4>Итог ИИ:</h4>
              <MathComponent tex={aiSolution} display={true} />
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
