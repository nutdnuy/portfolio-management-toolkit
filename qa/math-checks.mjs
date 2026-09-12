import assert from 'node:assert/strict';
import test from 'node:test';
import { SCENARIOS, calculateAllocation, simulate, protectivePut, toCSV } from '../src/math.mjs';

const flat = Array(12).fill(0);
const close = (actual, expected, tolerance = 1e-9) => assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected}`);

test('initial allocation uses the cushion and caps risky holdings at portfolio wealth', () => {
  assert.deepEqual(calculateAllocation(), { cushion: 10, exposure: 30, safe: 70, weight: 0.3 });
  assert.deepEqual(calculateAllocation({ floorPct: 20, multiplier: 6 }), { cushion: 80, exposure: 100, safe: 0, weight: 1 });
  assert.equal(calculateAllocation({ floorPct: 100 }).exposure, 0);
});

test('flat prices and zero interest preserve each strategy at initial wealth', () => {
  const result = simulate({ returns: flat });
  assert.equal(result.rows.length, 13);
  for (const row of result.rows) {
    assert.equal(row.cppi, 100);
    assert.equal(row.buyHold, 100);
    assert.equal(row.constantMix, 100);
    assert.equal(row.floor, 90);
  }
  assert.deepEqual(result.metrics, { final: 100, returnPct: 0, maxDrawdownPct: 0, minValue: 100, floorBreached: false, totalTurnover: 0, locked: false });
});

test('one-period gains accrue to existing holdings before rebalancing', () => {
  const result = simulate({ returns: [0.1, ...flat.slice(1)] });
  assert.equal(result.rows[1].cppi, 103); // 30 * 1.1 + 70
  assert.equal(result.rows[1].exposure, 39);
  close(result.rows[1].buyHold, 110);
  assert.equal(result.rows[1].constantMix, 106);
  assert.equal(result.metrics.totalTurnover, 6); // Buy 39 - 33, not 39 - 30.
});

test('a 40% gap breaches the floor even with no borrowing and locks out a recovery', () => {
  const result = simulate({ returns: [-0.4, 0.5, ...flat.slice(2)] });
  assert.equal(result.rows[1].cppi, 88);
  assert.equal(result.rows[1].cushion, -2);
  assert.equal(result.rows[1].exposure, 0);
  assert.equal(result.metrics.floorBreached, true);
  assert.equal(result.metrics.locked, true);
  for (const row of result.rows.slice(1)) {
    assert.equal(row.cppi, 88);
    assert.equal(row.exposure, 0);
    assert.ok(row.safe >= 0);
  }
  assert.equal(result.metrics.maxDrawdownPct, 12);
  assert.equal(result.rows[2].buyHold, 90);
});

test('touching the floor is cash lock, but not a floor breach', () => {
  const result = simulate({ multiplier: 2, returns: [-0.5, 1, ...flat.slice(2)] });
  assert.equal(result.metrics.floorBreached, false);
  assert.equal(result.metrics.locked, true);
  assert.equal(result.metrics.final, 90);
  assert.equal(result.rows[1].exposure, 0);
});

test('zero multiplier is a deliberate safe allocation, not a cash-lock event', () => {
  const result = simulate({ multiplier: 0 });
  assert.equal(result.metrics.final, 100);
  assert.equal(result.metrics.locked, false);
});

test('discounted floors and safe assets accrue at the same continuously compounded rate', () => {
  const rate = 0.06;
  const result = simulate({ rate, multiplier: 0, returns: flat });
  close(result.rows[0].floor, 90 * Math.exp(-rate));
  close(result.rows.at(-1).floor, 90);
  close(result.metrics.final, 100 * Math.exp(rate));
  for (let index = 1; index < result.rows.length; index += 1) {
    close(result.rows[index].floor / result.rows[index - 1].floor, Math.exp(rate / 12));
  }
});

test('multiplier one equals a safe floor reserve plus buy-and-hold of the initial cushion', () => {
  const rate = 0.04;
  const result = simulate({ rate, multiplier: 1 });
  const initialFloor = 90 * Math.exp(-rate);
  const initialRisky = 100 - initialFloor;
  for (const row of result.rows) {
    close(row.cppi, initialFloor * Math.exp(rate * row.month / 12) + initialRisky * row.asset / 100);
  }
  assert.equal(result.metrics.floorBreached, false);
  close(result.metrics.totalTurnover, 0);
});

test('future returns cannot alter preceding allocations or returns', () => {
  const first = simulate({ returns: [0.1, -0.1, 0.05, ...Array(9).fill(0.05)] });
  const second = simulate({ returns: [0.1, -0.1, 0.05, ...Array(9).fill(-0.15)] });
  assert.deepEqual(first.rows.slice(0, 4), second.rows.slice(0, 4));
  assert.notEqual(first.metrics.final, second.metrics.final);
});

test('Buy & Hold compounds risky returns; Constant Mix rebalances monthly', () => {
  const result = simulate({ returns: [0.1, -0.1, ...flat.slice(2)] });
  close(result.rows[2].buyHold, 99);
  close(result.rows[2].constantMix, 100 * 1.06 * 0.94);
});

test('defaults keep whipsaw above the floor, while the crash path breaches it', () => {
  const whipsaw = simulate({ scenario: 'whipsaw' });
  assert.equal(whipsaw.metrics.locked, false);
  assert.equal(whipsaw.metrics.floorBreached, false);
  assert.ok(whipsaw.rows.at(-1).cushion < whipsaw.rows[0].cushion);
  assert.equal(simulate({ scenario: 'crash' }).metrics.floorBreached, true);
});

test('maturity has a displayed target but no unnecessary final rebalance in turnover', () => {
  const result = simulate({ returns: [...flat.slice(1), 0.1] });
  assert.equal(result.rows.at(-1).exposure, 39);
  assert.equal(result.rows.at(-1).turnover, 0);
  assert.equal(result.metrics.totalTurnover, 0);
});

test('protective-put payoff, terminal wealth, initial cost, and profit stay distinct', () => {
  const down = protectivePut();
  assert.equal(down.stockTerminal, 80);
  assert.equal(down.putPayoff, 10);
  assert.equal(down.terminalWealth, 90);
  assert.equal(down.initialCost, 104);
  assert.equal(down.profit, -14);
  close(down.returnPct, -14 / 104 * 100);
  const up = protectivePut({ terminal: 120, quantity: 2 });
  assert.equal(up.putPayoff, 0);
  assert.equal(up.terminalWealth, 240);
  assert.equal(up.profit, 32);
  assert.equal(protectivePut({ terminal: 0 }).terminalWealth, 90);
  assert.equal(protectivePut({ terminal: 90 }).terminalWealth, 90);
});

test('all presets are deterministic and exposure remains within portfolio wealth', () => {
  for (const scenario of SCENARIOS) {
    assert.equal(scenario.returns.length, 12);
    for (const floorPct of [0, 80, 90, 100]) {
      for (const multiplier of [0, 1, 3, 6]) {
        const parameters = { scenario: scenario.id, floorPct, multiplier };
        const first = simulate(parameters);
        assert.deepEqual(first, simulate(parameters));
        for (const row of first.rows) {
          assert.ok(row.exposure >= 0 && row.exposure <= row.cppi);
          assert.ok(row.safe >= 0);
        }
      }
    }
  }
});

test('CSV has rectangular rows, reproduction parameters, and all 13 observations', () => {
  const lines = toCSV(simulate()).trimEnd().split('\r\n');
  assert.equal(lines.length, 14);
  const columns = lines[0].split(',').length;
  assert.ok(lines[0].includes('annual_continuous_rate'));
  for (const line of lines) assert.equal(line.split(',').length, columns);
  assert.ok(lines[1].startsWith('"crash","100","90","3","0","0",'));
});

test('invalid inputs fail explicitly instead of producing misleading charts', () => {
  for (const invalid of [0, -1, NaN, Infinity, '100']) assert.throws(() => simulate({ initial: invalid }), RangeError);
  for (const invalid of [-1, 101, Infinity]) assert.throws(() => simulate({ floorPct: invalid }), RangeError);
  assert.throws(() => simulate({ multiplier: -1 }), RangeError);
  assert.throws(() => simulate({ rate: 2 }), RangeError);
  assert.throws(() => simulate({ scenario: 'missing' }), RangeError);
  assert.throws(() => simulate({ returns: [0.1] }), RangeError);
  assert.throws(() => simulate({ returns: [-1.01, ...flat.slice(1)] }), RangeError);
  assert.throws(() => protectivePut({ premium: -1 }), RangeError);
  assert.throws(() => protectivePut({ quantity: 0 }), RangeError);
  assert.throws(() => protectivePut({ terminal: -1 }), RangeError);
  assert.throws(() => toCSV(null), TypeError);
});
