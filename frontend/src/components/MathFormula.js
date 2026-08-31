import React, { useEffect, useRef } from 'react';

export default function MathFormula({ tex, inline = false }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    let cancelled = false;
    let retryTimer = null;

    if (!container || !tex) {
      return undefined;
    }

    const render = async () => {
      if (cancelled) {
        return;
      }

      const mathJax = window.MathJax;
      if (!mathJax || typeof mathJax.typesetPromise !== 'function') {
        // MathJax is loaded with a defer script before the CRA bundle. This is
        // only a safety fallback for unusually slow script loading.
        retryTimer = window.setTimeout(render, 50);
        return;
      }

      if (typeof mathJax.typesetClear === 'function') {
        mathJax.typesetClear([container]);
      }

      container.textContent = inline ? `\\(${tex}\\)` : `\\[${tex}\\]`;

      try {
        await mathJax.typesetPromise([container]);
      } catch (error) {
        console.error('MathJax typesetting failed:', error);
      }
    };

    render();

    return () => {
      cancelled = true;
      if (retryTimer !== null) {
        window.clearTimeout(retryTimer);
      }
      if (window.MathJax && typeof window.MathJax.typesetClear === 'function') {
        window.MathJax.typesetClear([container]);
      }
    };
  }, [tex, inline]);

  if (!tex) {
    return null;
  }

  return inline
    ? <span ref={containerRef} className="math-formula" />
    : <div ref={containerRef} className="math-formula" />;
}
