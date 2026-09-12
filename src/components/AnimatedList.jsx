// Adapted from React Bits AnimatedList, commit 8d1c5fa9e. See vendor/react-bits-LICENSE.txt.
import React, { useEffect, useRef, useState } from 'react';
import { motion, useReducedMotion } from 'motion/react';

export default function AnimatedList({ items = [], onItemSelect }) {
  const reduced = useReducedMotion();
  const [selected, setSelected] = useState(null);
  const seen = useRef(new Set(items.map(item => item.id)));
  useEffect(() => { seen.current = new Set(items.map(item => item.id)); }, [items]);
  const onArrowKey = event => {
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
    const buttons = [...event.currentTarget.querySelectorAll('button')];
    const index = buttons.indexOf(document.activeElement);
    if (index < 0) return;
    event.preventDefault();
    const target = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1
      : Math.max(0, Math.min(buttons.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)));
    buttons[target]?.focus();
  };

  return <div className="rb-history" data-component="AnimatedList">
    <p className="rb-sr-only" role="status">บันทึกแล้ว {items.length} ชุด</p>
    {items.length === 0 ? <p className="rb-empty">บันทึกชุดทดลองเพื่อนำมาเทียบกับครั้งถัดไป</p>
      : <ol className="rb-animated-list" aria-label="ชุดทดลองที่บันทึกไว้" onKeyDown={onArrowKey}>
        {items.map((item, index) => <motion.li key={item.id}
          initial={reduced || seen.current.has(item.id) ? false : { opacity: 0.4, y: 8 }}
          animate={{ opacity: 1, y: 0 }} transition={{ duration: reduced ? 0 : 0.2 }}>
          <button type="button" className="rb-scenario-button" aria-pressed={selected === item.id}
            onClick={() => { setSelected(item.id); onItemSelect?.(item, index); }}>
            <span className="rb-scenario-label">{item.label}</span>
            <span className="rb-recall-label">{selected === item.id ? 'เรียกคืนแล้ว' : 'เรียกคืนค่า'}</span>
          </button>
        </motion.li>)}
      </ol>}
  </div>;
}
