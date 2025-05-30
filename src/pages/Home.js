import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const navigate = useNavigate();

  return (
    <motion.div className="page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <section className="hero">
        <h1>Добро пожаловать в DiffSolver</h1>
        <p>
          Это современный веб-инструмент для пошагового решения дифференциальных уравнений.
          Приложение идеально подходит для студентов, преподавателей и всех, кто изучает математический анализ.
        </p>
        <p style={{ marginTop: '1rem' }}>
          Вы можете начать с ввода уравнения, получить полное пошаговое решение и использовать справку по синтаксису.
        </p>
        <div style={{ marginTop: '2rem' }}>
          <button className="primary-button" onClick={() => navigate('/solve')}>
            Перейти к решателю
          </button>
          <button className="secondary-button" onClick={() => navigate('/help')}>
            Справка
          </button>
        </div>
      </section>
    </motion.div>
  );
}

