import assert from 'node:assert/strict';
import test from 'node:test';
import { summarizePath, empiricalTail, ewmaUpdate, ewmaDecay } from '../src/risk-math.mjs';

const close = (actual, expected, tolerance = 1e-12) => {
  assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)),
    `expected ${actual} to be close to ${expected}`);
};

test('same monthly return set preserves moments and terminal wealth, but not drawdown', () => {
  const a = summarizePath([0.1, 0.1, -0.1, -0.1]);
  const b = summarizePath([0.1, -0.1, 0.1, -0.1]);
  assert.deepEqual(a.wealth, [1e6, 1.1e6, 1.21e6, 1.089e6, 980100]);
  assert.deepEqual(b.wealth, [1e6, 1.1e6, 990000, 1.089e6, 980100]);
  for (const summary of [a, b]) {
    close(summary.mean, 0);
    close(summary.volatility, Math.sqrt(0.04 / 3));
    close(summary.downsideDeviation, Math.sqrt(0.02 / 4));
    close(summary.cumulative, -0.0199);
    assert.equal(summary.drawdowns[0], 0);
    assert.ok(summary.drawdowns.every(value => value <= 0));
  }
  close(a.maxDrawdown, 0.19);
  close(b.maxDrawdown, 0.109);
});

test('inception is a peak, initial-wealth scaling preserves ratio metrics', () => {
  const returns = [-0.1, 0.05, -0.2, 0.3];
  const snapshot = [...returns];
  const base = summarizePath(returns, 100);
  const scaled = summarizePath(returns, 700);
  close(base.drawdowns[1], -0.1);
  for (const key of ['mean', 'volatility', 'downsideDeviation', 'maxDrawdown', 'cumulative']) {
    close(scaled[key], base[key]);
  }
  base.wealth.forEach((value, index) => close(scaled.wealth[index], 7 * value));
  base.drawdowns.forEach((value, index) => close(scaled.drawdowns[index], value));
  assert.deepEqual(returns, snapshot);
});

test('constant positive returns have no downside; a total loss stays at zero wealth', () => {
  const growing = summarizePath([0.05, 0.05, 0.05], 100);
  close(growing.volatility, 0);
  assert.equal(growing.downsideDeviation, 0);
  assert.equal(growing.maxDrawdown, 0);
  const ruined = summarizePath([-1, 0.5], 100);
  assert.deepEqual(ruined.wealth, [100, 0, 0]);
  assert.deepEqual(ruined.drawdowns, [0, -1, -1]);
  assert.equal(ruined.maxDrawdown, 1);
});

test('the tied discrete example keeps VaR fixed while ES responds to severity', () => {
  for (const [extreme, expectedES] of [[200000, 56000], [400000, 96000]]) {
    const losses = [...Array(94).fill(0), ...Array(5).fill(20000), extreme];
    const result = empiricalTail(losses);
    assert.equal(result.var, 20000);
    assert.equal(result.tailMass, 5);
    close(result.es, expectedES);
    assert.notEqual(result.es, (5 * 20000 + extreme) / 6);
  }
});

test('fractional tail mass includes only the required share of the boundary', () => {
  // Worst 1.5 scenarios: 100 + half of 20, divided by 1.5.
  const fractional = empiricalTail([0, 10, 20, 100], 0.625);
  assert.equal(fractional.var, 20);
  assert.equal(fractional.tailMass, 1.5);
  close(fractional.es, 110 / 1.5);
  // A tied boundary has the same result whichever tied observation supplies mass.
  const ties = empiricalTail([100, 20, 0, 20], 0.625);
  assert.equal(ties.var, 20);
  close(ties.es, fractional.es);
});

test('tail calculations preserve sign, scale, translation, and input ordering', () => {
  const losses = [50, -30, 10, -10, 100];
  const copy = [...losses];
  const base = empiricalTail(losses, 0.5);
  const scaled = empiricalTail(losses.map(value => 3 * value), 0.5);
  const shifted = empiricalTail(losses.map(value => value - 200), 0.5);
  close(scaled.var, 3 * base.var);
  close(scaled.es, 3 * base.es);
  close(shifted.var, base.var - 200);
  close(shifted.es, base.es - 200);
  assert.deepEqual(empiricalTail([...losses].reverse(), 0.5), base);
  assert.deepEqual(losses, copy);
  const oneGain = empiricalTail([-10]);
  assert.equal(oneGain.var, -10);
  assert.equal(oneGain.es, -10);
  close(oneGain.tailMass, 0.05);
});

test('inverse ECDF handles integral rank roundoff and very small positive tails', () => {
  const losses = Array.from({ length: 100 }, (_, index) => index + 1);
  assert.equal(empiricalTail(losses, 0.14).var, 14);
  const tiny = empiricalTail([10, 20, 30], 1 - Number.EPSILON);
  assert.equal(tiny.var, 30);
  assert.ok(tiny.tailMass > 0);
  close(tiny.es, 30);
});

test('EWMA updates next-period volatility with squared shocks and correct endpoints', () => {
  close(ewmaUpdate(0.01, -0.04, 0.94), Math.sqrt(0.00019));
  close(ewmaUpdate(0.01, -0.04, 0.97), Math.sqrt(0.000145));
  close(ewmaUpdate(0.01, -0.04, 0.8), 0.02);
  close(ewmaUpdate(0.01, -0.04, 0.94), ewmaUpdate(0.01, 0.04, 0.94));
  assert.equal(ewmaUpdate(0.01, -0.04, 0), 0.04);
  assert.equal(ewmaUpdate(0.01, -0.04, 1), 0.01);
  assert.equal(ewmaUpdate(0, 0, 0.94), 0);
  close(ewmaUpdate(0.03, -0.12, 0.94), 3 * ewmaUpdate(0.01, -0.04, 0.94));
});

test('EWMA decay is a conditional zero-residual scenario, with inception included', () => {
  const path = ewmaDecay(0.01, -0.04, 0.94, 4);
  assert.equal(path.length, 5);
  assert.equal(path[0], 0.01);
  const afterShock = ewmaUpdate(0.01, -0.04, 0.94);
  path.slice(1).forEach((value, index) => close(value, afterShock * 0.94 ** (index / 2)));
  assert.deepEqual(ewmaDecay(0.01, -0.04, 0, 3), [0.01, 0.04, 0, 0]);
  assert.deepEqual(ewmaDecay(0.01, -0.04, 1, 3), [0.01, 0.01, 0.01, 0.01]);
  assert.equal(ewmaDecay(0.01, -0.04, 0.94).length, 21);
});

test('invalid data is rejected explicitly instead of producing silent NaN results', () => {
  for (const input of [null, [], [0.1], [0, NaN], [Infinity, 0], [0, -1.01], new Array(2)]) {
    assert.throws(() => summarizePath(input));
  }
  for (const initial of [0, -1, Infinity, '100']) assert.throws(() => summarizePath([0, 0], initial));
  for (const losses of [[], null, [NaN], [Infinity], ['1']]) assert.throws(() => empiricalTail(losses));
  for (const confidence of [0, 1, -0.1, 1.1, NaN, '0.95']) {
    assert.throws(() => empiricalTail([0, 1], confidence));
  }
  for (const args of [[-1, 0, 0.94], [NaN, 0, 0.94], [0.01, Infinity, 0.94], [0.01, 0, -0.1], [0.01, 0, 1.1]]) {
    assert.throws(() => ewmaUpdate(...args));
  }
  for (const periods of [0, -1, 1.5, Infinity, '4']) {
    assert.throws(() => ewmaDecay(0.01, -0.04, 0.94, periods));
  }
});
