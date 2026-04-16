import React, { useState } from 'react';
import { solveEquation } from '../api';
import { MathComponent } from 'mathjax-react';
import { motion } from 'framer-motion';

export default function Solver() {
  const [equation, setEquation] = useState('');
  const [steps, setSteps] = useState([]);
  const [solution, setSolution] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [solver, setSolver] = useState("sympy");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!equation.trim()) {
      setError("Введите уравнение");
      return;
    }

    setLoading(true);
    setError(null);
    setSteps([]);
    setSolution(null);

    try {
      const result = await solveEquation({
        equation,
        variable: "x",
        solver
      });

      console.log(result)

      setSteps(result.result.steps || []);
      setSolution(result.result.solution || '');

    } catch (err) {
      setError("Ошибка при обработке запроса");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      className="page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <h2>Решение дифференциальных уравнений</h2>

      {/* --- FORM --- */}
      <form className="form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Пример: y.diff(x) - y = 0"
          value={equation}
          onChange={(e) => setEquation(e.target.value)}
        />

        <div className="controls">
          <select
            value={solver}
            onChange={(e) => setSolver(e.target.value)}
          >
            <option value="sympy">⚡ SymPy (быстро)</option>
            <option value="ai">🧠 AI (умнее)</option>
          </select>

          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Решаем..." : "Решить"}
          </button>

          <button
            className="secondary-button"
            type="button"
            onClick={() => setShowHelp(!showHelp)}
          >
            {showHelp ? "Скрыть подсказку" : "Подсказка"}
          </button>
        </div>
      </form>

      {/* --- ERROR --- */}
      {error && (
        <div className="error-box">
          <p>{error}</p>
        </div>
      )}

      {/* --- HELP --- */}
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

      {/* --- STEPS --- */}
      {steps.length > 0 && (
        <div className="solution">
          <h3>Пошаговое решение</h3>

          <ol>
            {steps.map((step, index) => (
              <li key={index}>
                {step.type === "math" ? (
                  <MathComponent tex={step.content} display={true} />
                ) : (
                  <p>{step.content}</p>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* --- FINAL SOLUTION --- */}
      {solution && (
        <div className="solution final">
          <h3>Ответ:</h3>
          <MathComponent tex={solution} display={true} />
        </div>
      )}
    </motion.div>
  );
}