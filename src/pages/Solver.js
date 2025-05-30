import React, { useState } from 'react';
import { solveEquation } from '../api';
import { MathComponent } from 'mathjax-react';
import { motion } from 'framer-motion';

export default function Solver() {
  const [equation, setEquation] = useState('');
  const [steps, setSteps] = useState([]);
  const [solution, setSolution] = useState(null);
  const [showHelp, setShowHelp] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSteps([]);
    setSolution(null);
    try {
      const result = await solveEquation(equation);
      setSteps(result.steps || []);
      setSolution(result.solution || '');
    } catch (err) {
      setSteps([{ type: 'text', content: 'Ошибка при обработке запроса' }]);
    }
  };

  return (
    <motion.div className="page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h2>Введите дифференциальное уравнение</h2>

      <form className="form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Пример: y.diff(x) - y = 0"
          value={equation}
          onChange={(e) => setEquation(e.target.value)}
        />
        <button className="primary-button" type="submit">Решить</button>
        <button
          className="secondary-button"
          type="button"
          onClick={() => setShowHelp(!showHelp)}
        >
          Подсказка по синтаксису
        </button>
      </form>

      {showHelp && (
        <div className="help-box">
          <ul>
            <li><code>y.diff(x)</code> — производная y по x</li>
            <li><code>y.diff(x, 2)</code> — вторая производная</li>
            <li>Используйте <code>=</code> для уравнения</li>
            <li>Только <strong>y(x)</strong> — переменная должна быть функцией</li>
          </ul>
        </div>
      )}

      {steps.length > 0 && (
        <div className="solution">
          <h3>Пошаговое решение</h3>
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
        <div className="solution">
          <h3>Общее решение:</h3>
          <MathComponent tex={solution} display={true} />
        </div>
      )}
    </motion.div>
  );
}

