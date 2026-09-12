/**
 * Deterministic teaching models, not a replication of the source thesis.
 * Currency values are arbitrary monetary units. Rates and returns are decimals.
 */

export const SCENARIOS = Object.freeze([
  {
    id: 'rally',
    label: 'ตลาดขาขึ้น',
    description: 'เส้นทางสมมติที่ราคาค่อย ๆ สูงขึ้น มีเดือนติดลบเล็กน้อย เพื่อดูการเพิ่มสัดส่วนสินทรัพย์เสี่ยงของ CPPI',
    returns: [0.03, 0.02, 0.04, 0.01, 0.035, 0.02, 0.03, -0.01, 0.04, 0.02, 0.03, 0.015],
  },
  {
    id: 'crash',
    label: 'ร่วงฉับพลัน',
    description: 'หลังขึ้น 3 เดือน ราคาลดลง 40% ในเดือนที่ 4 ก่อนฟื้นตัว แสดง gap risk ระหว่างจุดปรับพอร์ต; จะติด cash lock หรือไม่ขึ้นกับค่าที่เลือก',
    returns: [0.03, 0.02, 0.04, -0.40, 0.08, 0.06, 0.05, 0.04, 0.06, 0.03, 0.04, 0.03],
  },
  {
    id: 'whipsaw',
    label: 'ขึ้นลงสลับกัน',
    description: 'สลับขึ้น 12% กับลง 10% เพื่อดูผลของการซื้อเพิ่มหลังขึ้นและขายหลังลง; เส้นทางนี้ไม่ได้ทำให้ CPPI ติด cash lock เสมอไป',
    returns: [0.12, -0.10, 0.12, -0.10, 0.12, -0.10, 0.12, -0.10, 0.12, -0.10, 0.12, -0.10],
  },
  {
    id: 'recovery',
    label: 'ลงก่อนแล้วฟื้น',
    description: 'ราคาลดลง 3 เดือน ก่อนฟื้นแรง เพื่อดูว่าเมื่อ CPPI ลดความเสี่ยงแล้วจะร่วมรับการฟื้นตัวได้เท่าไร',
    returns: [-0.12, -0.08, -0.10, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04, 0.03, 0.02],
  },
].map((scenario) => Object.freeze({ ...scenario, returns: Object.freeze(scenario.returns) })));

const MONTHS = 12;

function numberInRange(name, value, minimum, maximum = Infinity, exclusiveMinimum = false) {
  if (typeof value !== 'number' || !Number.isFinite(value)
    || (exclusiveMinimum ? value <= minimum : value < minimum) || value > maximum) {
    throw new RangeError(`${name} must be a finite number ${exclusiveMinimum ? '>' : '>='} ${minimum}${maximum < Infinity ? ` and <= ${maximum}` : ''}.`);
  }
}

function validateParameters({ initial, floorPct, multiplier }) {
  numberInRange('initial', initial, 0, Infinity, true);
  numberInRange('floorPct', floorPct, 0, 100);
  numberInRange('multiplier', multiplier, 0);
}

function allocate(value, floor, multiplier) {
  const cushion = value - floor;
  const exposure = Math.min(value, Math.max(0, multiplier * cushion));
  return { cushion, exposure, safe: value - exposure, weight: value > 0 ? exposure / value : 0 };
}

/** Snapshot at a zero-interest floor; simulate() discounts the terminal floor. */
export function calculateAllocation({ initial = 100, floorPct = 90, multiplier = 3 } = {}) {
  validateParameters({ initial, floorPct, multiplier });
  return allocate(initial, initial * (floorPct / 100), multiplier);
}

function summarize(rows, key, initial) {
  let peak = initial;
  let maxDrawdownPct = 0;
  for (const row of rows) {
    peak = Math.max(peak, row[key]);
    maxDrawdownPct = Math.max(maxDrawdownPct, 100 * (peak - row[key]) / peak);
  }
  const final = rows.at(-1)[key];
  return {
    final,
    returnPct: (final / initial - 1) * 100,
    maxDrawdownPct,
    minValue: Math.min(...rows.map((row) => row[key])),
  };
}

/**
 * Trade at month 0, then after months 1–11 using only information observed so far.
 * Row exposure is the CPPI target at that observation. The month-12 target is
 * shown for explanation only: no maturity trade enters turnover.
 * Optional returns supplies exactly 12 custom monthly returns for reproducibility.
 */
export function simulate({ initial = 100, floorPct = 90, multiplier = 3, scenario = 'crash', rate = 0, returns } = {}) {
  validateParameters({ initial, floorPct, multiplier });
  numberInRange('rate', rate, -1, 1);
  const selected = SCENARIOS.find((entry) => entry.id === scenario);
  if (returns === undefined && !selected) throw new RangeError(`Unknown scenario: ${scenario}`);
  const path = returns === undefined ? [...selected.returns] : returns;
  if (!Array.isArray(path) || path.length !== MONTHS) throw new RangeError('returns must contain exactly 12 monthly returns.');
  for (const monthlyReturn of path) numberInRange('monthly return', monthlyReturn, -1);

  const terminalFloor = initial * (floorPct / 100);
  const floorAt = (month) => terminalFloor * Math.exp(-rate * (1 - month / MONTHS));
  const monthlySafeGrowth = Math.exp(rate / MONTHS);
  const tolerance = Math.max(initial * 1e-10, Number.MIN_VALUE);
  let cppi = initial;
  let asset = 100;
  let buyHold = initial;
  let constantMix = initial;
  let allocation = allocate(cppi, floorAt(0), multiplier);
  let totalTurnover = 0;
  const rows = [{ month: 0, asset, cppi, buyHold, constantMix, floor: floorAt(0), ...allocation, riskyReturn: null, turnover: 0 }];

  for (let month = 1; month <= MONTHS; month += 1) {
    const riskyReturn = path[month - 1];
    const heldRiskyAfterReturn = allocation.exposure * (1 + riskyReturn);
    cppi = heldRiskyAfterReturn + allocation.safe * monthlySafeGrowth;
    asset *= 1 + riskyReturn;
    buyHold *= 1 + riskyReturn;
    constantMix *= 0.60 * (1 + riskyReturn) + 0.40 * monthlySafeGrowth;
    const floor = floorAt(month);
    allocation = allocate(cppi, floor, multiplier);
    const turnover = month < MONTHS ? Math.abs(allocation.exposure - heldRiskyAfterReturn) : 0;
    totalTurnover += turnover;
    const row = { month, asset, cppi, buyHold, constantMix, floor, ...allocation, riskyReturn, turnover };
    if (Object.values(row).some((value) => typeof value === 'number' && !Number.isFinite(value))) {
      throw new RangeError('Inputs produce values outside the supported numerical range.');
    }
    rows.push(row);
  }

  return {
    rows,
    metrics: {
      ...summarize(rows, 'cppi', initial),
      floorBreached: rows.some((row) => row.cppi < row.floor - tolerance),
      totalTurnover,
      // A zero multiplier is a deliberate cash allocation, not cushion exhaustion.
      locked: multiplier > 0 && rows.slice(0, -1).some((row) => row.cushion <= 0),
    },
    benchmarkMetrics: {
      buyHold: summarize(rows, 'buyHold', initial),
      constantMix: summarize(rows, 'constantMix', initial),
    },
    parameters: { initial, floorPct, multiplier, rate, scenario: returns === undefined ? selected.id : 'custom', months: MONTHS },
    assumptions: [
      'เส้นทางผลตอบแทนสมมติ 12 เดือน ไม่ใช่ข้อมูลตลาดหรือผลจำลองจากวิทยานิพนธ์',
      'CPPI ปรับพอร์ตต้นงวดและสิ้นเดือนที่ 1–11 โดยไม่ใช้ผลตอบแทนในอนาคต; ตารางแสดง exposure เป้าหมาย ณ สิ้นเดือนที่ 12 เพื่ออธิบายสูตรเท่านั้น',
      'สินทรัพย์เสี่ยงถูกจำกัดที่ 0–100% ของพอร์ต ไม่มีการกู้ยืมหรือขายชอร์ต และถือหน่วยลงทุนเป็นเศษส่วนได้',
      'floorPct คือมูลค่าเป้าหมาย ณ สิ้นปีเทียบกับเงินตั้งต้น; floor ระหว่างทางคิดลดด้วย rate ซึ่งเป็นอัตราดอกเบี้ยทบต้นต่อเนื่องรายปี',
      'สินทรัพย์ปลอดความเสี่ยงเติบโตตาม exp(rate/12) ต่อเดือน; ไม่คิดค่าธรรมเนียม ภาษี สเปรด หรือ slippage',
      'Buy & Hold ลงทุนสินทรัพย์เสี่ยง 100%; Constant Mix ปรับกลับเป็นสินทรัพย์เสี่ยง 60% และปลอดความเสี่ยง 40% ทุกเดือน',
      'Drawdown และการหลุด floor วัดเฉพาะจุดรายเดือน; มูลค่าระหว่างเดือนอาจต่างจากจุดที่แสดง',
      'Turnover คือผลรวมจำนวนเงินที่ซื้อหรือขายฝั่งสินทรัพย์เสี่ยงในเดือนที่ 1–11 ไม่นับจัดพอร์ตครั้งแรก ไม่ใช่อัตราร้อยละ และไม่หักจากมูลค่าพอร์ต',
      'Cash lock หมายถึง cushion หมดก่อนสิ้นงวดจน exposure เป็นศูนย์; zero multiplier เป็นการเลือกถือสินทรัพย์ปลอดความเสี่ยงโดยตั้งใจ',
    ],
  };
}

/** Buy quantity units of stock and matching European puts, held to expiry. */
export function protectivePut({ spot = 100, strike = 90, premium = 4, terminal = 80, quantity = 1 } = {}) {
  numberInRange('spot', spot, 0, Infinity, true);
  numberInRange('strike', strike, 0);
  numberInRange('premium', premium, 0);
  numberInRange('terminal', terminal, 0);
  numberInRange('quantity', quantity, 0, Infinity, true);
  const stockTerminal = quantity * terminal;
  const putPayoff = quantity * Math.max(strike - terminal, 0);
  const terminalWealth = stockTerminal + putPayoff;
  const initialCost = quantity * (spot + premium);
  const profit = terminalWealth - initialCost;
  const result = { stockTerminal, putPayoff, terminalWealth, initialCost, profit, returnPct: 100 * profit / initialCost };
  if (Object.values(result).some((value) => !Number.isFinite(value))) {
    throw new RangeError('Inputs produce values outside the supported numerical range.');
  }
  return result;
}

/** Standard rectangular CSV, including the parameters needed to reproduce it. */
export function toCSV(result) {
  if (!result || !Array.isArray(result.rows) || !result.parameters) throw new TypeError('toCSV expects a simulate() result.');
  const { initial, floorPct, multiplier, rate, scenario } = result.parameters;
  const headers = ['scenario', 'initial', 'terminal_floor_pct', 'multiplier', 'annual_continuous_rate', 'month', 'risky_return', 'asset_index', 'cppi', 'buy_hold', 'constant_mix_60_40', 'discounted_floor', 'cppi_target_exposure', 'cppi_cushion', 'cppi_safe_target', 'rebalance_turnover'];
  const escape = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
  const data = result.rows.map((row) => [scenario, initial, floorPct, multiplier, rate, row.month, row.riskyReturn, row.asset, row.cppi, row.buyHold, row.constantMix, row.floor, row.exposure, row.cushion, row.safe, row.turnover]);
  return [headers, ...data].map((row) => row.map(escape).join(',')).join('\r\n') + '\r\n';
}
