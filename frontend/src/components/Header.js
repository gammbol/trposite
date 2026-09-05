import React from 'react';
import { Link, useLocation } from 'react-router-dom';

import './Header.css';

export default function Header() {
  const location = useLocation();
  const active = (path) => (location.pathname === path ? 'active' : '');

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">DiffSolver</Link>
        <nav className="nav-links" aria-label="Основная навигация">
          <Link to="/" className={active('/')}>Главная</Link>
          <Link to="/solve" className={active('/solve')}>Решатель</Link>
          <Link to="/history" className={active('/history')}>История решений</Link>
          <Link to="/help" className={active('/help')}>Справка</Link>
        </nav>
      </div>
    </header>
  );
}
