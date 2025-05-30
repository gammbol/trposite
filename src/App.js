import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Home from './pages/Home';
import Solver from './pages/Solver';
import Help from './pages/Help';
import Header from './components/Header';
import './styles.css';

function App() {
  return (
    <Router>
      <Header />
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/solve" element={<Solver />} />
          <Route path="/help" element={<Help />} />
        </Routes>
      </AnimatePresence>
    </Router>
  );
}

export default App;

