// Adapted from React Bits CountUp, commit 8d1c5fa9e. See vendor/react-bits-LICENSE.txt.
import React, { useCallback, useEffect, useRef } from 'react';
import { useReducedMotion, useSpring } from 'motion/react';

export default function CountUp({ to, digits = 2, className = '' }) {
  const visual = useRef(null);
  const reduceMotion = useReducedMotion();
  const value = Number.isFinite(to) ? to : 0;
  const precision = Math.max(0, Math.min(8, Math.trunc(digits)));
  const spring = useSpring(value, { stiffness: 160, damping: 30 });
  const format = useCallback(number => Number.isFinite(to)
    ? new Intl.NumberFormat('en-US', { minimumFractionDigits: precision, maximumFractionDigits: precision }).format(number)
    : '—', [precision, to]);

  useEffect(() => {
    if (reduceMotion) {
      spring.jump(value);
      if (visual.current) visual.current.textContent = format(value);
      return;
    }
    const unsubscribe = spring.on('change', latest => {
      if (visual.current) visual.current.textContent = format(latest);
    });
    spring.set(value);
    return unsubscribe;
  }, [value, format, reduceMotion, spring]);

  return <span className={`rb-count-up ${className}`} data-component="CountUp">
    <span aria-hidden="true" ref={visual}>{format(value)}</span>
    <span className="rb-sr-only">{format(value)}</span>
  </span>;
}
