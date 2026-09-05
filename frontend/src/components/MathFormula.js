import React, { useEffect, useRef } from 'react';

export default function MathFormula({ tex, inline = false }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !tex) return undefined;

    let cancelled = false;
    let retryTimer = null;
    let retries = 0;

    // Always show a readable fallback immediately. If MathJax is unavailable,
    // history/solver pages still display the stored solution instead of an
    // empty element forever.
    container.textContent = tex;

    const render = async () => {
      if (cancelled) return;

      const mathJax = window.MathJax;
      if (!mathJax || typeof mathJax.typesetPromise !== 'function') {
        retries += 1;
        if (retries <= 100) retryTimer = window.setTimeout(render, 50);
        return;
      }

      if (typeof mathJax.typesetClear === 'function') {
        mathJax.typesetClear([container]);
      }

      container.textContent = inline ? `\\(${tex}\\)` : `\\[${tex}\\]`;

      try {
        await mathJax.typesetPromise([container]);
      } catch (error) {
        container.textContent = tex;
        console.error('MathJax typesetting failed:', error);
      }
    };

    render();

    return () => {
      cancelled = true;
      if (retryTimer !== null) window.clearTimeout(retryTimer);
      if (window.MathJax && typeof window.MathJax.typesetClear === 'function') {
        window.MathJax.typesetClear([container]);
      }
    };
  }, [tex, inline]);

  if (!tex) return null;
  return inline
    ? <span ref={containerRef} className="math-formula">{tex}</span>
    : <div ref={containerRef} className="math-formula">{tex}</div>;
}
