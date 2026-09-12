// Adapted from React Bits BlurText, commit 8d1c5fa9e. See vendor/react-bits-LICENSE.txt.
import React, { Fragment } from 'react';
import { motion, useReducedMotion } from 'motion/react';

// Inline semantics let the caller own the single correct heading level.
export default function BlurText({ text = '', className = '' }) {
  const reduced = useReducedMotion();
  return <span className={`rb-blur-text ${className}`} data-component="BlurText">
    <span className="rb-sr-only">{text}</span>
    <span aria-hidden="true">{text.split(/(\s+)/).map((segment, index) => /^\s+$/.test(segment)
      ? <Fragment key={index}>{segment}</Fragment>
      : <motion.span className="rb-blur-word" key={index}
        initial={reduced ? false : { opacity: 0.65, y: 5, filter: 'blur(2px)' }}
        whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }} viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: reduced ? 0 : 0.3, delay: reduced ? 0 : Math.min(index * 0.025, 0.2) }}>
        {segment}
      </motion.span>)}</span>
  </span>;
}
