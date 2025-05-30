import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

export default function Header() {
  const location = useLocation();

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="logo">DiffSolver</Link>
        <nav className="nav-links">
          <Link to="/" className={location.pathname === '/' ? 'active' : ''}>Главная</Link>
          <Link to="/solve" className={location.pathname === '/solve' ? 'active' : ''}>Решатель</Link>
          <Link to="/help" className={location.pathname === '/help' ? 'active' : ''}>Справка</Link>
        </nav>
      </div>
    </header>
  );
}

