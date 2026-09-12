// Adapted from React Bits Stepper, commit 8d1c5fa9e. See vendor/react-bits-LICENSE.txt.
import React, { Children, useId, useRef, useState } from 'react';
import { motion, useReducedMotion } from 'motion/react';

const defaultLabels = ['กำหนด Floor', 'หา Cushion', 'จัดสรรเงิน'];

export default function Stepper({ children }) {
  const steps = Children.toArray(children);
  const [current, setCurrent] = useState(0);
  const [direction, setDirection] = useState(1);
  const reduced = useReducedMotion();
  const id = useId();
  const panel = useRef(null);
  const active = Math.min(current, Math.max(0, steps.length - 1));
  const labels = steps.map((step, index) => step.props?.['data-step-title'] || defaultLabels[index] || `Step ${index + 1}`);
  const goTo = target => {
    if (target === active || target < 0 || target >= steps.length) return;
    setDirection(target > active ? 1 : -1);
    setCurrent(target);
    // The panel persists, so moving focus announces the new named learning stage.
    requestAnimationFrame(() => panel.current?.focus({ preventScroll: true }));
  };
  if (!steps.length) return null;

  return <div className="rb-stepper" data-component="Stepper">
    <ol className="rb-step-indicators" aria-label="ลำดับการคำนวณ">
      {steps.map((_, index) => <li key={index}>
        <button type="button" id={`${id}-step-${index}`} aria-current={active === index ? 'step' : undefined}
          aria-controls={`${id}-panel`} onClick={() => goTo(index)} className="rb-step-indicator">
          <span className="rb-step-number" aria-hidden="true">{index + 1}</span>
          <span>{labels[index]}</span>
        </button>
      </li>)}
    </ol>
    <section className="rb-step-panel" id={`${id}-panel`} ref={panel} tabIndex={-1} aria-labelledby={`${id}-step-${active}`}>
      <motion.div key={active} initial={reduced ? false : { opacity: 0.7, x: direction * 12 }}
        animate={{ opacity: 1, x: 0 }} transition={{ duration: reduced ? 0 : 0.18 }}>
        {steps[active]}
      </motion.div>
    </section>
    <div className="rb-step-footer">
      <button type="button" className="rb-button" disabled={active === 0} onClick={() => goTo(active - 1)}>ย้อนกลับ</button>
      <span className="rb-step-progress" role="status">ขั้น {active + 1} จาก {steps.length}</span>
      <button type="button" className="rb-button rb-button-primary" disabled={active === steps.length - 1} onClick={() => goTo(active + 1)}>ถัดไป</button>
    </div>
  </div>;
}

export function Step({ children, ...props }) { return <div {...props}>{children}</div>; }
