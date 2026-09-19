/** Numerical conventions for the risk chapter. All return inputs use decimal ratios. */

function finiteNumber(value, name) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new TypeError(`${name} must be a finite number`);
  }
}

function numberArray(values, name, minimumLength = 1) {
  if (!Array.isArray(values)) throw new TypeError(`${name} must be an array`);
  if (values.length < minimumLength) {
    throw new RangeError(`${name} must contain at least ${minimumLength} observations`);
  }
  for (const value of values) finiteNumber(value, `${name} observation`);
}

/**
 * No external cash flows. Simple returns cannot be below -100% in this lesson.
 * Wealth and negative drawdowns include inception. Maximum drawdown is positive.
 * Volatility is sample SD (n - 1); downside deviation uses threshold 0 and all n.
 */
export function summarizePath(returns, initial = 1e6) {
  numberArray(returns, 'returns', 2);
  finiteNumber(initial, 'initial');
  if (initial <= 0) throw new RangeError('initial must be greater than zero');
  if (returns.some(value => value < -1)) {
    throw new RangeError('simple returns must be at least -1');
  }

  const n = returns.length;
  const mean = returns.reduce((sum, value) => sum + value / n, 0);
  const variance = returns.reduce((sum, value) => sum + (value - mean) ** 2 / (n - 1), 0);
  const downsideVariance = returns.reduce((sum, value) => sum + Math.min(value, 0) ** 2 / n, 0);
  const volatility = Math.sqrt(variance);
  const downsideDeviation = Math.sqrt(downsideVariance);
  const wealth = [initial];
  const drawdowns = [0];
  let current = initial;
  let peak = initial;
  let maxDrawdown = 0;

  for (const value of returns) {
    current *= 1 + value;
    if (!Number.isFinite(current)) throw new RangeError('wealth exceeds finite numeric range');
    peak = Math.max(peak, current);
    const drawdown = current / peak - 1;
    wealth.push(current);
    drawdowns.push(drawdown);
    maxDrawdown = Math.max(maxDrawdown, -drawdown);
  }

  const cumulative = current / initial - 1;
  if (![mean, volatility, downsideDeviation, cumulative].every(Number.isFinite)) {
    throw new RangeError('return statistics exceed finite numeric range');
  }
  return { wealth, drawdowns, mean, volatility, downsideDeviation, maxDrawdown, cumulative };
}

// Remove multiplication roundoff at integer ranks, e.g. 100 * 0.14.
// Never round positive tail mass to zero, even at confidence very near 1.
function snapPositiveInteger(value) {
  const nearest = Math.round(value);
  const tolerance = 4 * Number.EPSILON * Math.max(1, Math.abs(value));
  return nearest > 0 && Math.abs(value - nearest) <= tolerance ? nearest : value;
}

/**
 * Equal-probability loss scenarios; positive means loss and negative means gain.
 * VaR uses the inverse empirical CDF. ES averages exactly the worst (1-c) mass,
 * including fractional weight at a boundary observation. It is not the mean of
 * all observations >= VaR. tailMass is measured in observation-equivalents.
 */
export function empiricalTail(losses, confidence = 0.95) {
  numberArray(losses, 'losses');
  finiteNumber(confidence, 'confidence');
  if (confidence <= 0 || confidence >= 1) {
    throw new RangeError('confidence must lie strictly between 0 and 1');
  }

  const sorted = [...losses].sort((a, b) => a - b);
  const n = sorted.length;
  const rank = Math.ceil(snapPositiveInteger(n * confidence));
  const valueAtRisk = sorted[rank - 1];
  const tailMass = snapPositiveInteger(n * (1 - confidence));
  const fullCount = Math.floor(tailMass);
  const fraction = tailMass - fullCount;
  let es = 0;
  for (let offset = 0; offset < fullCount; offset += 1) {
    es += sorted[n - 1 - offset] / tailMass;
  }
  if (fraction > 0) es += sorted[n - 1 - fullCount] * (fraction / tailMass);
  if (!Number.isFinite(es)) throw new RangeError('tail mean exceeds finite numeric range');
  return { var: valueAtRisk, es, tailMass };
}

/** Next-period sigma after observing a zero-mean return innovation. */
export function ewmaUpdate(sigma, shock, lambda) {
  finiteNumber(sigma, 'sigma');
  finiteNumber(shock, 'shock');
  finiteNumber(lambda, 'lambda');
  if (sigma < 0) throw new RangeError('sigma must be nonnegative');
  if (lambda < 0 || lambda > 1) throw new RangeError('lambda must lie between 0 and 1');
  // Endpoints are allowed to demonstrate full replacement versus no update.
  return Math.hypot(Math.sqrt(lambda) * sigma, Math.sqrt(1 - lambda) * shock);
}

/**
 * Includes initial sigma, then one shock update, then periods - 1 zero-residual
 * updates. Length is periods + 1. This is a hypothetical realized update path,
 * not a multi-step EWMA forecast (which integrates unknown future innovations).
 */
export function ewmaDecay(sigma, shock, lambda, periods = 20) {
  if (!Number.isSafeInteger(periods) || periods < 1) {
    throw new RangeError('periods must be a positive safe integer');
  }
  const first = ewmaUpdate(sigma, shock, lambda);
  const path = [sigma, first];
  for (let step = 1; step < periods; step += 1) {
    path.push(ewmaUpdate(path[path.length - 1], 0, lambda));
  }
  return path;
}
