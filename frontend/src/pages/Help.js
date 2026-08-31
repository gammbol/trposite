import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Help() {
  const navigate = useNavigate();
  return (
    <div className="page">
      <h1>Помощь и синтаксис</h1>
      <p style={{ marginBottom: '1.5rem', color: '#4a4a4a' }}>
        Здесь вы найдёте краткую справку по синтаксису, используемому для ввода дифференциальных уравнений.
        Мы используем правила библиотеки <strong>SymPy</strong> — синтаксис максимально приближен к Python.
      </p>
      <div className="help-box">
        <h2>📘 Основной синтаксис</h2>
        <ul>
          <li><code>y.diff(x)</code> — производная y по x</li>
          <li><code>y.diff(x, 2)</code> — вторая производная y по x</li>
          <li><code>y</code> должна быть <strong>функцией от x</strong>, то есть <code>y = Function('y')(x)</code></li>
          <li><code>=</code> обязательно: <code>y.diff(x) = x + y</code></li>
        </ul>
      </div>
      <div className="help-box">
        <h2>🧪 Примеры уравнений</h2>
        <ul>
          <li><code>y.diff(x) - y = 0</code></li>
          <li><code>y.diff(x) = x * y</code></li>
          <li><code>y.diff(x, 2) + y = 0</code> (ОДУ второго порядка)</li>
          <li><code>y.diff(x) = sin(x)</code> — поддерживаются функции: <code>sin</code>, <code>cos</code>, <code>exp</code>, <code>log</code></li>
        </ul>
      </div>
      <div className="help-box">
        <h2>🔗 Полезные ссылки</h2>
        <ul>
          <li><a href="https://docs.sympy.org/latest/tutorial/calculus.html" target="_blank" rel="noreferrer">
            Документация SymPy по дифференцированию
          </a></li>
          <li><a href="https://sympy.org/en/index.html" target="_blank" rel="noreferrer">
            Главная страница SymPy
          </a></li>
        </ul>
      </div>
      <button className="primary-button" onClick={() => navigate('/solve')} style={{ marginTop: '2rem' }}>
        Перейти к решению уравнений
      </button>
    </div>
  );
}
