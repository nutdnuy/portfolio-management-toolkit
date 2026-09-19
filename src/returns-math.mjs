/** Realized returns for a positive, self-financing wealth series. */
export function calculateReturns(initial, returns) {
  if (!Number.isFinite(initial) || initial <= 0) throw new RangeError('Initial wealth must be positive.');
  if (!Array.isArray(returns) || returns.length !== 2 || returns.some(r => !Number.isFinite(r) || r <= -1)) {
    throw new RangeError('Two finite returns greater than -100% are required.');
  }
  const gross = returns.map(r => 1 + r);
  const logs = returns.map(r => Math.log1p(r));
  const wealth = [initial];
  for (const g of gross) wealth.push(wealth.at(-1) * g);
  if (wealth.some(v => !Number.isFinite(v) || v <= 0)) throw new RangeError('Wealth is outside the supported numeric range.');
  const logSum = logs[0] + logs[1];
  return {initial, returns: [...returns], gross, logs, wealth, logSum,
    cumulative: wealth[2] / initial - 1, fromLog: Math.expm1(logSum),
    naiveSum: returns[0] + returns[1], gains: [wealth[1]-wealth[0], wealth[2]-wealth[1]]};
}
