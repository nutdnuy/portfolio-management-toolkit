"""Build a self-contained, executed notebook from the canonical Thai chapter.

Calculations require Python's standard library only. IPython is used optionally
to show deterministic SVG charts when a reader runs the notebook interactively.
"""
import contextlib
import hashlib
import html
import io
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "content/portfolio-insurance.md"
MODEL = ROOT / "src/math.mjs"
OUTPUT = ROOT / "notebooks/portfolio-insurance.ipynb"

MODEL_CODE = r'''import csv
import html
import io
import math

# The same illustrative monthly paths as the website, copied into this file.
SCENARIOS = __SCENARIOS__

def close(actual, expected, tolerance=1e-9):
    assert math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance), (actual, expected)

def number_in_range(name, value, minimum, maximum=math.inf, exclusive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value > maximum
            or (value <= minimum if exclusive else value < minimum)):
        raise ValueError(f"Invalid {name}: {value!r}")

def allocate(value, floor, multiplier):
    cushion = value - floor
    exposure = min(value, max(0, multiplier * cushion))
    return dict(cushion=cushion, exposure=exposure, safe=value-exposure,
                weight=exposure/value if value > 0 else 0)

def calculate_allocation(initial=100, floor_pct=90, multiplier=3):
    number_in_range("initial", initial, 0, exclusive=True)
    number_in_range("floor_pct", floor_pct, 0, 100)
    number_in_range("multiplier", multiplier, 0)
    return allocate(initial, initial * (floor_pct / 100), multiplier)

def summarize(rows, key, initial):
    peak, drawdown = initial, 0
    for row in rows:
        peak = max(peak, row[key])
        drawdown = max(drawdown, 100 * (peak-row[key]) / peak)
    final = rows[-1][key]
    return dict(final=final, returnPct=(final/initial-1)*100,
                maxDrawdownPct=drawdown, minValue=min(row[key] for row in rows))

def simulate(initial=100, floor_pct=90, multiplier=3, scenario="crash", rate=0, returns=None):
    """One year; rebalance at 0 and after months 1–11, using observed values only.

    rate: annual continuously compounded decimal, supported from -1 to +1.
    floor_pct: terminal floor as a percentage of initial wealth.
    exposure in row 12: illustrative target only; no maturity trade is counted.
    """
    calculate_allocation(initial, floor_pct, multiplier)  # Validate inputs.
    number_in_range("rate", rate, -1, 1)
    if returns is None and scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    path = SCENARIOS[scenario][:] if returns is None else list(returns)
    if len(path) != 12:
        raise ValueError("Exactly 12 monthly returns are required.")
    for monthly_return in path:
        number_in_range("monthly return", monthly_return, -1)
    terminal_floor = initial * (floor_pct / 100)
    floor_at = lambda month: terminal_floor * math.exp(-rate * (1-month/12))
    safe_growth = math.exp(rate/12)
    cppi = buy_hold = constant_mix = initial
    asset = 100
    allocation = allocate(cppi, floor_at(0), multiplier)
    rows = [dict(month=0, asset=asset, cppi=cppi, buyHold=buy_hold,
                 constantMix=constant_mix, floor=floor_at(0), **allocation,
                 riskyReturn=None, turnover=0)]
    total_turnover = 0
    for month, monthly_return in enumerate(path, start=1):
        held_risky = allocation["exposure"] * (1+monthly_return)
        cppi = held_risky + allocation["safe"] * safe_growth
        asset *= 1+monthly_return
        buy_hold *= 1+monthly_return
        constant_mix *= 0.60 * (1+monthly_return) + 0.40 * safe_growth
        floor = floor_at(month)
        allocation = allocate(cppi, floor, multiplier)
        turnover = abs(allocation["exposure"]-held_risky) if month < 12 else 0
        total_turnover += turnover
        row = dict(month=month, asset=asset, cppi=cppi, buyHold=buy_hold,
                   constantMix=constant_mix, floor=floor, **allocation,
                   riskyReturn=monthly_return, turnover=turnover)
        if not all(math.isfinite(v) for v in row.values() if isinstance(v, (int, float))):
            raise ValueError("Inputs exceed the supported numerical range.")
        rows.append(row)
    metrics = summarize(rows, "cppi", initial)
    metrics.update(floorBreached=any(row["cppi"] < row["floor"]-initial*1e-10 for row in rows),
                   totalTurnover=total_turnover,
                   locked=multiplier > 0 and any(row["cushion"] <= 0 for row in rows[:-1]))
    return dict(rows=rows, metrics=metrics,
                benchmarkMetrics={key: summarize(rows, key, initial) for key in ("buyHold", "constantMix")},
                parameters=dict(initial=initial, floorPct=floor_pct, multiplier=multiplier,
                                rate=rate, scenario=scenario if returns is None else "custom", months=12))

def protective_put(spot=100, strike=90, premium=4, terminal=80, quantity=1):
    """Stock plus a matching European put held to expiry; no dividends or costs.

    The supplied premium is an assumption, not an option-pricing model.
    """
    for name, value in (("spot", spot), ("quantity", quantity)):
        number_in_range(name, value, 0, exclusive=True)
    for name, value in (("strike", strike), ("premium", premium), ("terminal", terminal)):
        number_in_range(name, value, 0)
    stock_terminal = quantity * terminal
    payoff = quantity * max(strike-terminal, 0)
    wealth = stock_terminal + payoff
    cost = quantity * (spot+premium)
    profit = wealth-cost
    result = dict(stockTerminal=stock_terminal, putPayoff=payoff, terminalWealth=wealth,
                  initialCost=cost, profit=profit, returnPct=profit/cost*100)
    if not all(math.isfinite(v) for v in result.values()):
        raise ValueError("Inputs exceed the supported numerical range.")
    return result

def cppi_csv(result):
    """Return CSV text without writing a file or sending any data anywhere."""
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    names = ["month", "riskyReturn", "asset", "cppi", "buyHold", "constantMix",
             "floor", "exposure", "cushion", "safe", "turnover"]
    parameters = result["parameters"]
    writer.writerow([*parameters, *names])
    for row in result["rows"]:
        writer.writerow([*parameters.values(), *(row[name] for name in names)])
    return out.getvalue()

print("Python standard library models ready. All paths are illustrative, not market data.")
print("No borrowing, no shorting, fractional units allowed; monthly observations; zero trading costs.")'''

CHART_CODE = r'''def chart_svg(rows, series, x_key="month", title="CPPI experiment", x_label="Month"):
    """Render observed values as SVG; lines connect observations, not hidden data."""
    width, height = 800, 420
    left, right, top, bottom = 66, 24, 64, 108
    values = [row[key] for row in rows for key, label, color, dash in series]
    lo = math.floor((min(values)-5)/10)*10
    hi = math.ceil((max(values)+5)/10)*10
    xs = [row[x_key] for row in rows]
    x = lambda value: left+(value-min(xs))/(max(xs)-min(xs))*(width-left-right)
    y = lambda value: top+(hi-value)/(hi-lo)*(height-top-bottom)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="420" viewBox="0 0 800 420" role="img" aria-label="{html.escape(title)}">',
             f'<title>{html.escape(title)}</title>',
             '<rect width="800" height="420" fill="#FFFFFF"/>',
             '<g font-family="Roboto, Arial, sans-serif" fill="#212121">',
             f'<text x="{left}" y="26" font-size="20" font-weight="600">{html.escape(title)}</text>',
             f'<text x="{left}" y="48" font-size="13">Value in units · {len(rows)} observations · illustrative only</text>']
    for index in range(5):
        value = lo+(hi-lo)*index/4
        parts.append(f'<line x1="{left}" x2="{width-right}" y1="{y(value):.3f}" y2="{y(value):.3f}" stroke="#DEDEDE"/>')
        parts.append(f'<text x="{left-12}" y="{y(value)+5:.3f}" font-size="14" text-anchor="end">{value:g}</text>')
    for index in (0, len(rows)//3, 2*len(rows)//3, len(rows)-1):
        value = xs[index]
        parts.append(f'<text x="{x(value):.3f}" y="{height-bottom+25}" font-size="14" text-anchor="middle">{value:g}</text>')
    for key, label, color, dash in series:
        points = " ".join(f'{x(row[x_key]):.3f},{y(row[key]):.3f}' for row in rows)
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.8" stroke-dasharray="{dash}"/>')
    parts.append(f'<text x="{width-right}" y="{height-bottom+47}" font-size="14" text-anchor="end">{html.escape(x_label)}</text>')
    for index, (key, label, color, dash) in enumerate(series):
        column, row = index % 2, index // 2
        lx, ly = left+column*345, height-40+row*24
        parts.append(f'<line x1="{lx}" x2="{lx+30}" y1="{ly-4}" y2="{ly-4}" stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/>')
        parts.append(f'<text x="{lx+40}" y="{ly}" font-size="14">{html.escape(label)}</text>')
    return "".join(parts)+"</g></svg>"

def show_svg(svg):
    # The generator captures rich output; an ordinary notebook uses IPython.
    capture = globals().get("_portfolio_svg_capture")
    if capture is not None:
        capture(svg)
        return
    try:
        from IPython.display import SVG, display
    except ImportError:
        print("SVG chart available in the returned string; numerical tables are shown below.")
    else:
        display(SVG(svg))

CPPI_SERIES = [("cppi", "CPPI", "#6200EE", ""),
               ("buyHold", "Buy & hold (100% risky)", "#008577", "8 5"),
               ("constantMix", "Constant mix (60/40)", "#555555", "2 4"),
               ("floor", "Target floor", "#B00020", "6 4")]
print("Deterministic SVG charts ready; no image or chart service is called.")'''

SNIPPETS = {
    "put-lab": r'''# Change these assumptions, then run this cell again.
spot, strike, premium, terminal = 100, 90, 4, 80
put_result = protective_put(spot=spot, strike=strike, premium=premium, terminal=terminal)
if premium < max(strike-spot, 0):
    print("This assumed premium violates the zero-interest no-arbitrage lower bound.")
    print("Read the result only as arithmetic for that hypothetical input, not a tradable price.")
for key, label in [("putPayoff", "Put payoff"), ("terminalWealth", "Terminal wealth"),
                   ("initialCost", "Initial cost"), ("profit", "Profit / loss"), ("returnPct", "Return (%)")]:
    print(f"{label:<20}: {put_result[key]:.6f}")
put_rows = []
for price in range(0, 201, 5):
    item = protective_put(spot=spot, strike=strike, premium=premium, terminal=price)
    put_rows.append(dict(price=price, wealth=item["terminalWealth"], cost=item["initialCost"], stock=price))
show_svg(chart_svg(put_rows, [("wealth", "Stock + put at expiry", "#6200EE", ""),
                            ("stock", "Stock only at expiry", "#008577", "8 5"),
                            ("cost", "Initial cost of stock + put", "#B00020", "6 4")],
                   x_key="price", title="Protective put: terminal wealth and initial cost",
                   x_label="Stock price at expiry (units)"))
print("This is a payoff diagram across terminal prices, not a time-series path.")''',
    "allocation-guide": r'''# Worked allocation: initial 100, floor 90, multiplier 3, zero interest.
initial, floor_pct, multiplier = 100, 90, 3
first = calculate_allocation(initial, floor_pct, multiplier)
monthly_return = -0.10
held_risky_after_return = first["exposure"] * (1+monthly_return)
next_value = held_risky_after_return + first["safe"]
second = allocate(next_value, initial*floor_pct/100, multiplier)
print(f"Initial: cushion={first['cushion']:.2f}; risky={first['exposure']:.2f}; safe={first['safe']:.2f}")
print(f"After a 10% risky-asset fall: wealth={next_value:.2f}; risky before trade={held_risky_after_return:.2f}")
print(f"New risky target={second['exposure']:.2f}; sell={held_risky_after_return-second['exposure']:.2f}; safe={second['safe']:.2f}")
close(next_value, 97); close(second["exposure"], 21)
print("No future return was used to choose the preceding month's allocation.")''',
    "cppi-lab": r'''# Editable controls: rally, crash, whipsaw, or recovery; initial wealth 100.
scenario, floor_pct, multiplier, rate = "crash", 90, 3, 0
result = simulate(scenario=scenario, floor_pct=floor_pct, multiplier=multiplier, rate=rate)
metrics = result["metrics"]
print(f"Scenario={scenario}; terminal floor={floor_pct}%; m={multiplier}; annual continuous rate={rate:.2%}")
print(f"CPPI final={metrics['final']:.6f}; return={metrics['returnPct']:.6f}%; max monthly drawdown={metrics['maxDrawdownPct']:.6f}%")
print(f"Floor breached={metrics['floorBreached']}; cash locked={metrics['locked']}; rebalance turnover={metrics['totalTurnover']:.6f} units")
show_svg(chart_svg(result["rows"], CPPI_SERIES, title=f"CPPI and benchmarks: {scenario}"))
print("Month   CPPI      Buy/hold  Mix60/40  Floor     Risky target  Cushion")
for row in result["rows"]:
    print(f"{row['month']:>5} {row['cppi']:>9.4f} {row['buyHold']:>9.4f} {row['constantMix']:>9.4f} {row['floor']:>9.4f} {row['exposure']:>12.4f} {row['cushion']:>9.4f}")
print("Month 12 exposure is a formula target only; no final trade enters turnover.")
csv_text = cppi_csv(result)  # Optionally save this string to a file of your choice.
print("\nSame parameters, four illustrative paths:")
for path in SCENARIOS:
    comparison = simulate(scenario=path, floor_pct=floor_pct, multiplier=multiplier, rate=rate)
    stats = comparison["metrics"]
    print(f"{path:<10} final={stats['final']:.5f}, breach={stats['floorBreached']}, cash lock={stats['locked']}")''',
    "reflection-list": r'''# Compare parameter choices on a fixed path; this is not a strategy ranking.
print("Crash path, initial=100, terminal floor=90%, r=0:")
for m in [1, 2, 2.5, 3, 6]:
    experiment = simulate(multiplier=m)
    stats = experiment["metrics"]
    print(f"m={m:<3}: final={stats['final']:>9.5f}, max drawdown={stats['maxDrawdownPct']:>8.4f}%, breach={stats['floorBreached']}, lock={stats['locked']}")
print("A larger multiplier can also increase gap exposure. No scenario here supplies event probabilities.")''',
}

SECTION_SNIPPETS = {
    "how-to-compare": SNIPPETS["reflection-list"],
    "tipp": r'''# The chapter's illustrative ratchet rule, not a replication of the thesis.
current_value, high_water_mark, protection_fraction, multiplier = 120, 120, 0.90, 3
fixed_floor = 90
ratchet_floor = protection_fraction*high_water_mark
tipp_allocation = allocate(current_value, ratchet_floor, multiplier)
cppi_allocation = allocate(current_value, fixed_floor, multiplier)
close(ratchet_floor, 108); close(tipp_allocation["exposure"], 36)
close(cppi_allocation["exposure"], 90)
print(f"At wealth 120: TIPP floor={ratchet_floor:.2f}, cushion={tipp_allocation['cushion']:.2f}, risky target={tipp_allocation['exposure']:.2f}")
print(f"Fixed-floor CPPI: floor={fixed_floor:.2f}, cushion={cppi_allocation['cushion']:.2f}, risky target={cppi_allocation['exposure']:.2f}")
print("A higher floor leaves less risky exposure; monthly rebalancing still leaves gap risk.")''',
    "floor-and-cushion": r'''initial, terminal_floor, annual_rate = 100, 90, 0
for month in [0, 6, 12]:
    floor = terminal_floor * math.exp(-annual_rate*(1-month/12))
    print(f"Month {month:>2}: discounted floor={floor:.2f}")
print(f"Initial cushion={initial-terminal_floor*math.exp(-annual_rate):.2f}")''',
    "option-budget": r'''# Same strike and expiry, zero interest and dividends: stock + put = bond + call.
spot, strike, assumed_put_premium = 100, 90, 4
implied_call_premium = spot + assumed_put_premium - strike
print(f"Parity-implied Call premium={implied_call_premium:.2f}; full stock+put cost=104.00")
budget, floor = 100, 90
call_units = (budget-floor)/implied_call_premium
print(f"With budget {budget}, reserve {floor} and buy {call_units:.6f} Call units, not one whole Call.")
for terminal_price in [80, 90, 120]:
    call_payoff = max(terminal_price-strike, 0)
    same_quantity = strike + call_payoff
    protected_budget = floor + call_units*call_payoff
    close(same_quantity, protective_put(terminal=terminal_price)["terminalWealth"])
    print(f"S_T={terminal_price}: full-parity wealth={same_quantity:.2f}; fixed-budget wealth={protected_budget:.2f}")''',
}

# This block is inserted before CHECK_CODE in the notebook generator.
# Keep examples self-contained and distinct from the 12-month teaching model.
SECTION_SNIPPETS["floor-and-cushion"] += r'''

# Discount the same terminal target; do not confuse time decay with a ratchet.
floor_target, annual_rate = 90, 0.05
floor_today = floor_target * math.exp(-annual_rate)
floor_half_year = floor_target * math.exp(-annual_rate * 0.5)
close(floor_today, 85.61064820506427)
close(floor_half_year, 87.77789208254994)
close(floor_today * math.exp(annual_rate), floor_target)
print(f"5% continuous rate: floor today={floor_today:.6f}, in six months={floor_half_year:.6f}, at maturity={floor_target:.6f}")
print(f"Initial cushion={100-floor_today:.6f}; investing 90 today instead gives {90*math.exp(annual_rate):.6f} at maturity.")
'''

SECTION_SNIPPETS["option-budget"] += r'''

# Match both the initial budget and the desired floor before comparing.
scaled_units = 100 / 104
expected_values = [
    (80, 90, 86.53846153846153, 90),
    (100, 100, 96.15384615384616, 97.14285714285714),
    (120, 120, 115.38461538461539, 111.42857142857143),
]
print("Terminal stock | full stock+put (cost 104) | scaled (cost 100) | fixed-floor OBPI (cost 100)")
for terminal_stock, full_expected, scaled_expected, obpi_expected in expected_values:
    full = max(terminal_stock, 90)
    scaled = scaled_units * full
    fixed_floor = 90 + (10/14) * max(terminal_stock-90, 0)
    close(full, full_expected); close(scaled, scaled_expected); close(fixed_floor, obpi_expected)
    print(f"{terminal_stock:>14} {full:>27.6f} {scaled:>19.6f} {fixed_floor:>27.6f}")
close(90 + (10/14)*(104-90), 100)
new_call_premium = 20
parity_put_premium = new_call_premium - 100 + 90
close(parity_put_premium, 10)
close(90 + (10/new_call_premium)*(120-90), 105)
print("Call premium 20 implies Put premium 10 at the same spot/strike/rate, not the former Put premium 4.")
'''

SECTION_SNIPPETS["cppi-rule"] = r'''# Optional continuous, unconstrained CPPI: not the capped monthly simulator.
def continuous_cushion(cushion0, rate, drift, sigma, multiplier, time, brownian_endpoint):
    growth = (rate + multiplier*(drift-rate) - 0.5*multiplier**2*sigma**2)*time
    return cushion0 * math.exp(growth + multiplier*sigma*brownian_endpoint)

print("Illustrative Brownian endpoints at t=1 (not sampled scenarios or probabilities):")
for endpoint in [-1, 0, 0.25, 1]:
    cushion = continuous_cushion(10, 0.05, 0.08, 0.20, 3, 1, endpoint)
    assert cushion > 0
    print(f"W_1={endpoint:>5}: C_1={cushion:.6f}")
close(continuous_cushion(10, 0.05, 0.08, 0.20, 3, 1, 0.25), 11.162780704588712)
# When m=1, the cushion is simply the initial risky holding's value.
close(continuous_cushion(10, 0.05, 0.08, 0.20, 1, 1, 0.25),
      10*math.exp((0.08-0.5*0.2**2) + 0.2*0.25))
print("This result assumes continuous trading/prices, no costs, and unconstrained exposure. It does not validate the discrete simulator's floor.")
'''

SECTION_SNIPPETS["cppi-example"] = r'''# Four rebalancing periods, all before maturity.
returns = [-0.10, 0.20, -0.10, 0.10]
value, floor, multiplier, turnover = 100, 90, 3, 0
positions = allocate(value, floor, multiplier)
expected = [
    (27, 97, 7, 21, -6, 76),
    (25.2, 101.2, 11.2, 33.6, 8.4, 67.6),
    (30.24, 97.84, 7.84, 23.52, -6.72, 74.32),
    (25.872, 100.192, 10.192, 30.576, 4.704, 69.616),
]
print("Period | held risky | wealth | cushion | new risky | trade | new safe")
for step, (asset_return, answer) in enumerate(zip(returns, expected), 1):
    held_risky = positions["exposure"]*(1+asset_return)
    value = held_risky + positions["safe"]
    positions = allocate(value, floor, multiplier)
    trade = positions["exposure"]-held_risky
    turnover += abs(trade)
    values = (held_risky, value, positions["cushion"], positions["exposure"], trade, positions["safe"])
    for actual, target in zip(values, answer):
        close(actual, target)
    close(positions["exposure"]+positions["safe"], value)
    print(step, " | ".join(f"{number:.3f}" for number in values))
close(turnover, 25.824)
print(f"Turnover excluding initial allocation={turnover:.3f} monetary units, not fees.")
# Cross-check the same four steps in the chapter's monthly simulator.
same_steps = simulate(returns=returns+[0]*8)
for row, answer in zip(same_steps["rows"][1:5], expected):
    close(row["cppi"], answer[1]); close(row["exposure"], answer[3])
flat_path = simulate(returns=[0]*12)
round_trip = simulate(returns=[0.10, -1/11]+[0]*10)
close(round_trip["rows"][2]["asset"], 100)
close(round_trip["rows"][2]["cppi"], 99.45454545454545)
close(flat_path["rows"][2]["cppi"], 100)
print("Stock ends at 100 in both paths; flat CPPI=100, round-trip CPPI=99.454545.")
'''

SECTION_SNIPPETS["gap-risk"] = r'''# A one-period snapshot: F_now=90, not the preceding example's terminal floor.
rate, dt, value_now, floor_now, multiplier = 0.06, 1/12, 100, 90, 3
gross_safe = math.exp(rate*dt)
safe_return = gross_safe - 1
positions = allocate(value_now, floor_now, multiplier)
threshold = -1/multiplier + (multiplier-1)/multiplier*safe_return
close(threshold, -0.3299916527603993)
next_value = positions["exposure"]*(1-0.33) + positions["safe"]*gross_safe
next_floor = floor_now*gross_safe
close(next_value, 90.45087646015807)
close(next_floor, 90.45112687734608)
assert next_value < next_floor
print(f"Monthly gap threshold at 6% continuous annual rate: risky return < {threshold:.6%}")
print(f"After -33%: wealth={next_value:.9f}, floor={next_floor:.9f}, cushion={next_value-next_floor:.9f}")
# Use actual exposure when the cap binds.
capped = allocate(100, 50, 3)
close(capped["exposure"], 100)
capped_threshold = -capped["cushion"]/capped["exposure"]
close(capped_threshold, -0.5)
close(capped["exposure"]*(1+capped_threshold)+capped["safe"], 50)
print(f"With V=100/F=50/m=3/r=0, capped exposure=100 and floor-touch return={capped_threshold:.2%}.")
# Cash lock can grow in money while staying locked relative to the growing floor.
for initial_cushion in [0, -2]:
    assert gross_safe*initial_cushion <= 0
'''

SECTION_SNIPPETS["tipp"] += r'''

# Matched initial wealth/exposure, then each portfolio follows its own rule.
cppi_value = tipp_value = high_water = 100
cppi_floor = tipp_floor = 90
cppi_pos = allocate(cppi_value, cppi_floor, 3)
tipp_pos = allocate(tipp_value, tipp_floor, 3)
expected = [(106, 106, 95.4, 48, 31.8), (101.2, 102.82, 95.4, 33.6, 22.26)]
print("Return | CPPI wealth | TIPP wealth | TIPP floor | CPPI risky | TIPP risky")
for asset_return, answers in zip([0.20, -0.10], expected):
    cppi_value = cppi_pos["exposure"]*(1+asset_return)+cppi_pos["safe"]
    tipp_value = tipp_pos["exposure"]*(1+asset_return)+tipp_pos["safe"]
    high_water = max(high_water, tipp_value)
    tipp_floor = max(tipp_floor, 0.90*high_water)
    cppi_pos = allocate(cppi_value, cppi_floor, 3)
    tipp_pos = allocate(tipp_value, tipp_floor, 3)
    actual = (cppi_value, tipp_value, tipp_floor, cppi_pos["exposure"], tipp_pos["exposure"])
    for result, target in zip(actual, answers):
        close(result, target)
    print(f"{asset_return:>6.0%} | " + " | ".join(f"{x:.3f}" for x in actual))
close(tipp_pos["safe"], 80.56)
cppi_recovery = cppi_value + cppi_pos["exposure"]*0.30
tipp_recovery = tipp_value + tipp_pos["exposure"]*0.30
close(cppi_recovery, 111.28); close(tipp_recovery, 109.498)
print(f"Next +30%: CPPI={cppi_recovery:.3f}, TIPP={tipp_recovery:.3f}.")
print("These are the chapter's illustrative ratchet rules; the website's 12-month lab remains CPPI only.")
'''


SECTION_SNIPPETS["cppi-rule"] += r'''

# Illustrative inverse-volatility multiplier; inputs are known before the next return.
def variable_multiplier(sigma, base=3.0, reference=0.20, lower=1.0, upper=6.0):
    if not all(math.isfinite(x) for x in (sigma, base, reference, lower, upper)):
        raise ValueError("Inputs must be finite")
    if sigma <= 0 or reference <= 0 or base <= 0 or not 0 <= lower <= upper:
        raise ValueError("Positive volatility/base and ordered nonnegative bounds required")
    return min(upper, max(lower, base * reference / sigma))

print("Estimated annual volatility | Multiplier | Risky | Safe")
for sigma, expected_m, expected_risky in [(0.10, 6, 60), (0.20, 3, 30), (0.40, 1.5, 15)]:
    m_variable = variable_multiplier(sigma)
    risky = min(100, max(0, m_variable * (100 - 90)))
    close(m_variable, expected_m); close(risky, expected_risky)
    print(f"{sigma:>27.0%} {m_variable:>12.2f} {risky:>7.2f} {100-risky:>7.2f}")

# Change these two inputs for a one-period experiment. No volatility forecast is fitted.
estimated_sigma_before_trade = 0.40
next_risky_return = -0.10
if not math.isfinite(next_risky_return) or next_risky_return < -1:
    raise ValueError("Simple return must be finite and at least -100%")
m_variable = variable_multiplier(estimated_sigma_before_trade)
variable_exposure = min(100, max(0, m_variable * 10))
variable_end = 100 + variable_exposure * next_risky_return
fixed_end = 100 + 30 * next_risky_return
print(f"One-period wealth: variable={variable_end:.2f}; fixed m=3={fixed_end:.2f}")

# Independent analytic checks keep the published examples testable after input edits.
close(variable_multiplier(0.01), 6); close(variable_multiplier(2), 1)
close(100 + 15 * -0.10, 98.5); close(100 + 30 * -0.10, 97)
close(100 + 15 * 0.10, 101.5); close(100 + 30 * 0.10, 103)
close(1.5 * (98.5 - 90), 12.75)
close(15 * 0.9 - 12.75, 0.75)
close(100 + 15 * -0.70, 89.5)
for invalid in [0, -0.2, float("nan"), float("inf")]:
    try:
        variable_multiplier(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid volatility must fail")
print("Variable multiplier checks passed, including cap/floor, rebalance, and a floor-breaching gap.")
'''

SECTION_SNIPPETS["strategies"] = r'''# Passive and constant mix start from the same 60/40 allocation.
held_risky, safe = 60*1.1, 40
total = held_risky + safe
mix_target = 0.6*total
trade = mix_target-held_risky
close(total, 106); close(mix_target, 63.6); close(trade, -2.4)
print(f"Passive risky weight={held_risky/total:.6%}; constant mix sells {-trade:.2f} units.")
estimated_cost = 0.001*60
close(estimated_cost, 0.06)
print(f"60 units of turnover at a hypothetical 0.1% cost -> {estimated_cost:.2f} units of direct cost.")
print("A full cost model must deduct costs when trading and recompute the cushion/exposure, not merely subtract this at maturity.")
'''

SECTION_SNIPPETS["study-design"] = r'''# One GBM time step at fixed illustrative shocks, not a Monte Carlo replication.
mu, sigma, dt, spot = 0.15, 0.20, 1/252, 100
daily_log_sd = sigma*math.sqrt(dt)
close(daily_log_sd, 0.01259881576697424)
print(f"Daily log-return standard deviation={daily_log_sd:.6%}")
for z in [-1, 0, 1]:
    next_spot = spot*math.exp((mu-0.5*sigma**2)*dt+sigma*math.sqrt(dt)*z)
    assert next_spot > 0
    print(f"Z={z:+}: next price={next_spot:.6f}")
print(f"Under this constant-parameter GBM, expected one-year simple return=exp(mu)-1={math.expm1(mu):.6%}, not exactly mu.")
'''

SECTION_SNIPPETS["eut-cpt"] = r'''# New teaching examples, separate from the thesis tables.
utility_a = math.log(100)
utility_b = 0.5*math.log(50)+0.5*math.log(170)
certainty_equivalent = math.exp(utility_b)
close(utility_b, 4.523910721239204)
close(certainty_equivalent, 92.19544457292888)
assert (50+170)/2 > 100 and utility_b < utility_a
print(f"EUT: sure 100 utility={utility_a:.6f}; risky 50/170 utility={utility_b:.6f}; CE={certainty_equivalent:.6f}")

def prospect_value(change, alpha=0.88, beta=0.88, loss_aversion=2.25):
    return change**alpha if change >= 0 else -loss_aversion*(-change)**beta

def decision_weight(probability, eta):
    assert 0 <= probability <= 1 and eta > 0
    return probability**eta/(probability**eta+(1-probability)**eta)**(1/eta)

gain_value, loss_value = prospect_value(10), prospect_value(-10)
mean_value = (gain_value+loss_value)/2
gain_weight, loss_weight = decision_weight(0.5, 0.61), decision_weight(0.5, 0.69)
mixed_cpt = gain_weight*gain_value + loss_weight*loss_value
close(gain_value, 7.5857757502918375)
close(loss_value, -17.067995438156636)
close(mean_value, -4.741109843932399)
close(mixed_cpt, -4.557781610517452)
print(f"v(+10)={gain_value:.6f}; v(-10)={loss_value:.6f}; mean value={mean_value:.6f}")
print(f"Mixed CPT: gain weight={gain_weight:.6f}; loss weight={loss_weight:.6f}; score={mixed_cpt:.6f}")
high_gain_weight = decision_weight(0.10, 0.61)
low_gain_weight = decision_weight(1, 0.61)-high_gain_weight
close(high_gain_weight, 0.18630256637717418)
close(low_gain_weight, 0.8136974336228258)
close(low_gain_weight+high_gain_weight, 1)
print(f"Gains 10(p=.9)/100(p=.1): cumulative weights={low_gain_weight:.6f}/{high_gain_weight:.6f}.")
print("Weights are decision weights, not recalibrated market probabilities. Mixed gain/loss weights need not add to one.")
'''

SECTION_SNIPPETS["robo-advisors"] = r'''# Two-asset teaching illustration, not the thesis risk decomposition.
weight_a = weight_b = 0.5
sigma_a = sigma_b = 0.20
for correlation, expected_sigma in [(0, math.sqrt(0.02)), (1, 0.20)]:
    variance = weight_a**2*sigma_a**2 + weight_b**2*sigma_b**2
    variance += 2*weight_a*weight_b*sigma_a*sigma_b*correlation
    sigma_portfolio = math.sqrt(variance)
    close(sigma_portfolio, expected_sigma)
    print(f"Correlation={correlation}: portfolio annual volatility={sigma_portfolio:.6%}")
'''

SECTION_SNIPPETS["how-to-compare"] += r'''

# Equal-probability toy outcomes for measurement; not the four lab scenarios.
terminal_sets = {"A": [70, 90, 100, 110, 130], "B": [80, 95, 100, 105, 120]}
for name, terminal_values in terminal_sets.items():
    losses = [max(90-v, 0) for v in terminal_values]
    positive_losses = [loss for loss in losses if loss > 0]
    probability = len(positive_losses)/len(losses)
    expected_loss = sum(losses)/len(losses)
    conditional_loss = sum(positive_losses)/len(positive_losses) if positive_losses else None
    close(sum(terminal_values)/len(terminal_values), 100)
    close(probability, 0.2)
    close(expected_loss, 4 if name == "A" else 2)
    close(conditional_loss, 20 if name == "A" else 10)
    close(expected_loss, probability*conditional_loss)
    print(f"{name}: mean=100, breach={probability:.0%}, mean shortfall={expected_loss:.2f}, conditional shortfall={conditional_loss:.2f}")

def sampled_max_drawdown(values):
    peak, max_loss = values[0], 0
    for value in values:
        peak = max(peak, value)
        max_loss = max(max_loss, 1-value/peak)
    return max_loss

close(sampled_max_drawdown([100, 120, 108]), 0.1)
close(sampled_max_drawdown([100, 105, 108]), 0)
print("Both sample paths end at +8%; sampled MDD is 10% versus 0%. Terminal outcomes alone cannot supply MDD.")
'''


SECTION_SNIPPETS["sp500-test"] = '# Saved derived results, not a re-run of historical market data.\n# For a full re-run, use the linked sp500-backtest.py with your own permitted input CSV.\nhistorical_results = [{\'year\': 2018, \'method\': \'Buy & Hold\', \'start\': \'2017-12-29\', \'end\': \'2018-12-31\', \'days\': 251, \'final\': 93.76274026503486, \'return_pct\': -6.237259734965136, \'max_drawdown_pct\': 19.778213767806875, \'min_value\': 87.93728329861119, \'floor_breached\': True, \'max_shortfall\': 2.0627167013888084, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2018, \'method\': \'SLPI\', \'start\': \'2017-12-29\', \'end\': \'2018-12-31\', \'days\': 251, \'final\': 87.93728329861119, \'return_pct\': -12.062716701388808, \'max_drawdown_pct\': 19.778213767806875, \'min_value\': 87.93728329861119, \'floor_breached\': True, \'max_shortfall\': 2.0627167013888084, \'first_exit\': \'2018-12-24\', \'rebalance_count\': 1, \'risky_turnover\': 87.9372832986112}, {\'year\': 2018, \'method\': \'CPPI\', \'start\': \'2017-12-29\', \'end\': \'2018-12-31\', \'days\': 251, \'final\': 97.5476061992414, \'return_pct\': -2.4523938007585997, \'max_drawdown_pct\': 6.162668561206319, \'min_value\': 96.2697634056735, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 250, \'risky_turnover\': 111.94422734394212}, {\'year\': 2018, \'method\': \'TIPP\', \'start\': \'2017-12-29\', \'end\': \'2018-12-31\', \'days\': 251, \'final\': 98.25335423297818, \'return_pct\': -1.7466457670218176, \'max_drawdown_pct\': 5.020906857460094, \'min_value\': 97.21467763285547, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 250, \'risky_turnover\': 88.5634355886223}, {\'year\': 2018, \'method\': \'Variable m\', \'start\': \'2017-12-29\', \'end\': \'2018-12-31\', \'days\': 251, \'final\': 96.67259419632649, \'return_pct\': -3.327405803673514, \'max_drawdown_pct\': 9.075321450367092, \'min_value\': 95.70491398208304, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 250, \'risky_turnover\': 417.6357256569539}, {\'year\': 2018, \'method\': \'OBPI (model)\', \'start\': \'2017-12-29\', \'end\': \'2018-12-31\', \'days\': 251, \'final\': 90.0, \'return_pct\': -10.0, \'max_drawdown_pct\': 28.61189116392273, \'min_value\': 90.0, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': None, \'option_sigma\': 0.06670114253007703, \'call_premium\': 2.6677737538854203, \'call_units\': 3.7484438046651145}, {\'year\': 2019, \'method\': \'Buy & Hold\', \'start\': \'2018-12-31\', \'end\': \'2019-12-31\', \'days\': 252, \'final\': 128.87807407702897, \'return_pct\': 28.87807407702897, \'max_drawdown_pct\': 6.836103916383496, \'min_value\': 97.64804435845784, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2019, \'method\': \'SLPI\', \'start\': \'2018-12-31\', \'end\': \'2019-12-31\', \'days\': 252, \'final\': 128.87807407702897, \'return_pct\': 28.87807407702897, \'max_drawdown_pct\': 6.836103916383496, \'min_value\': 97.64804435845784, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2019, \'method\': \'CPPI\', \'start\': \'2018-12-31\', \'end\': \'2019-12-31\', \'days\': 252, \'final\': 110.4125408907653, \'return_pct\': 10.4125408907653, \'max_drawdown_pct\': 2.9563210233625625, \'min_value\': 99.29252904089921, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 251, \'risky_turnover\': 126.32073439772489}, {\'year\': 2019, \'method\': \'TIPP\', \'start\': \'2018-12-31\', \'end\': \'2019-12-31\', \'days\': 252, \'final\': 107.4566332387571, \'return_pct\': 7.456633238757107, \'max_drawdown_pct\': 1.9597950036950418, \'min_value\': 99.2950728008607, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 251, \'risky_turnover\': 70.91068030769742}, {\'year\': 2019, \'method\': \'Variable m\', \'start\': \'2018-12-31\', \'end\': \'2019-12-31\', \'days\': 252, \'final\': 111.39858726444045, \'return_pct\': 11.398587264440451, \'max_drawdown_pct\': 6.1462326816024255, \'min_value\': 99.51728724998448, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 228, \'risky_turnover\': 631.619581881268}, {\'year\': 2019, \'method\': \'OBPI (model)\', \'start\': \'2018-12-31\', \'end\': \'2019-12-31\', \'days\': 252, \'final\': 132.50513785173737, \'return_pct\': 32.50513785173737, \'max_drawdown_pct\': 8.822819938499137, \'min_value\': 98.20718281679854, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': None, \'option_sigma\': 0.17050713778154272, \'call_premium\': 6.794019625994125, \'call_units\': 1.4718827072179328}, {\'year\': 2020, \'method\': \'Buy & Hold\', \'start\': \'2019-12-31\', \'end\': \'2020-12-31\', \'days\': 253, \'final\': 116.25892199406964, \'return_pct\': 16.258921994069638, \'max_drawdown_pct\': 33.92495902426057, \'min_value\': 69.2526263007695, \'floor_breached\': True, \'max_shortfall\': 20.747373699230494, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2020, \'method\': \'SLPI\', \'start\': \'2019-12-31\', \'end\': \'2020-12-31\', \'days\': 253, \'final\': 85.01228805427795, \'return_pct\': -14.987711945722054, \'max_drawdown_pct\': 18.888413094517364, \'min_value\': 85.01228805427795, \'floor_breached\': True, \'max_shortfall\': 4.9877119457220545, \'first_exit\': \'2020-03-09\', \'rebalance_count\': 1, \'risky_turnover\': 85.01228805427795}, {\'year\': 2020, \'method\': \'CPPI\', \'start\': \'2019-12-31\', \'end\': \'2020-12-31\', \'days\': 253, \'final\': 100.76190685975524, \'return_pct\': 0.7619068597552427, \'max_drawdown_pct\': 8.663796123536482, \'min_value\': 92.66468468853242, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 252, \'risky_turnover\': 134.88660387266972}, {\'year\': 2020, \'method\': \'TIPP\', \'start\': \'2019-12-31\', \'end\': \'2020-12-31\', \'days\': 253, \'final\': 100.7647573169417, \'return_pct\': 0.7647573169416972, \'max_drawdown_pct\': 7.673677788693977, \'min_value\': 93.59833061334615, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 252, \'risky_turnover\': 117.62124214511326}, {\'year\': 2020, \'method\': \'Variable m\', \'start\': \'2019-12-31\', \'end\': \'2020-12-31\', \'days\': 253, \'final\': 104.20633516513662, \'return_pct\': 4.206335165136622, \'max_drawdown_pct\': 7.003544873205558, \'min_value\': 95.20796780017845, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 230, \'risky_turnover\': 399.2235341885655}, {\'year\': 2020, \'method\': \'OBPI (model)\', \'start\': \'2019-12-31\', \'end\': \'2020-12-31\', \'days\': 253, \'final\': 122.57461686766118, \'return_pct\': 22.574616867661177, \'max_drawdown_pct\': 14.988303041540652, \'min_value\': 90.00202245700409, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': None, \'option_sigma\': 0.12502354411550934, \'call_premium\': 4.991285717994359, \'call_units\': 2.0034917985056335}, {\'year\': 2021, \'method\': \'Buy & Hold\', \'start\': \'2020-12-31\', \'end\': \'2021-12-31\', \'days\': 252, \'final\': 126.89273629085734, \'return_pct\': 26.892736290857343, \'max_drawdown_pct\': 5.212532648585433, \'min_value\': 98.52452164097049, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2021, \'method\': \'SLPI\', \'start\': \'2020-12-31\', \'end\': \'2021-12-31\', \'days\': 252, \'final\': 126.89273629085734, \'return_pct\': 26.892736290857343, \'max_drawdown_pct\': 5.212532648585433, \'min_value\': 98.52452164097049, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2021, \'method\': \'CPPI\', \'start\': \'2020-12-31\', \'end\': \'2021-12-31\', \'days\': 252, \'final\': 109.39566935252694, \'return_pct\': 9.395669352526937, \'max_drawdown_pct\': 2.4335186199935577, \'min_value\': 99.55735649229115, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 251, \'risky_turnover\': 134.65803930481067}, {\'year\': 2021, \'method\': \'TIPP\', \'start\': \'2020-12-31\', \'end\': \'2021-12-31\', \'days\': 252, \'final\': 106.91208325620306, \'return_pct\': 6.912083256203061, \'max_drawdown_pct\': 1.5276418194605568, \'min_value\': 99.55735649229115, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 251, \'risky_turnover\': 82.61561841501873}, {\'year\': 2021, \'method\': \'Variable m\', \'start\': \'2020-12-31\', \'end\': \'2021-12-31\', \'days\': 252, \'final\': 112.945732342685, \'return_pct\': 12.945732342685005, \'max_drawdown_pct\': 4.859866619457676, \'min_value\': 99.1147129845823, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 208, \'risky_turnover\': 559.5399698496437}, {\'year\': 2021, \'method\': \'OBPI (model)\', \'start\': \'2020-12-31\', \'end\': \'2021-12-31\', \'days\': 252, \'final\': 109.49537243109293, \'return_pct\': 9.495372431092932, \'max_drawdown_pct\': 4.141911103275675, \'min_value\': 99.14656336378566, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': None, \'option_sigma\': 0.34751563663108054, \'call_premium\': 13.794420386638159, \'call_units\': 0.7249307850358403}, {\'year\': 2022, \'method\': \'Buy & Hold\', \'start\': \'2021-12-31\', \'end\': \'2022-12-30\', \'days\': 251, \'final\': 80.55717576759594, \'return_pct\': -19.442824232404064, \'max_drawdown_pct\': 25.42509631902862, \'min_value\': 75.05024988565269, \'floor_breached\': True, \'max_shortfall\': 14.94975011434731, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2022, \'method\': \'SLPI\', \'start\': \'2021-12-31\', \'end\': \'2022-12-30\', \'days\': 251, \'final\': 88.65590472873453, \'return_pct\': -11.344095271265473, \'max_drawdown_pct\': 11.90561569124542, \'min_value\': 88.65590472873453, \'floor_breached\': True, \'max_shortfall\': 1.3440952712654735, \'first_exit\': \'2022-02-23\', \'rebalance_count\': 1, \'risky_turnover\': 88.65590472873453}, {\'year\': 2022, \'method\': \'CPPI\', \'start\': \'2021-12-31\', \'end\': \'2022-12-30\', \'days\': 251, \'final\': 94.3843286709165, \'return_pct\': -5.615671329083497, \'max_drawdown_pct\': 6.498613313140089, \'min_value\': 93.68018220827624, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 250, \'risky_turnover\': 105.8736597785329}, {\'year\': 2022, \'method\': \'TIPP\', \'start\': \'2021-12-31\', \'end\': \'2022-12-30\', \'days\': 251, \'final\': 94.48239020660061, \'return_pct\': -5.517609793399387, \'max_drawdown_pct\': 6.388870645244282, \'min_value\': 93.79013472864828, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 250, \'risky_turnover\': 103.84363111749181}, {\'year\': 2022, \'method\': \'Variable m\', \'start\': \'2021-12-31\', \'end\': \'2022-12-30\', \'days\': 251, \'final\': 94.2525590403308, \'return_pct\': -5.7474409596692055, \'max_drawdown_pct\': 6.401056252458492, \'min_value\': 93.80917179431589, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 250, \'risky_turnover\': 177.55327077147084}, {\'year\': 2022, \'method\': \'OBPI (model)\', \'start\': \'2021-12-31\', \'end\': \'2022-12-30\', \'days\': 251, \'final\': 90.0, \'return_pct\': -10.0, \'max_drawdown_pct\': 10.5482471981038, \'min_value\': 90.0, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': None, \'option_sigma\': 0.13111735628943777, \'call_premium\': 5.219926105605758, \'call_units\': 1.9157359314456288}, {\'year\': 2023, \'method\': \'Buy & Hold\', \'start\': \'2022-12-30\', \'end\': \'2023-12-29\', \'days\': 250, \'final\': 124.23049876285987, \'return_pct\': 24.230498762859867, \'max_drawdown_pct\': 10.276620410724846, \'min_value\': 99.18218518036204, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2023, \'method\': \'SLPI\', \'start\': \'2022-12-30\', \'end\': \'2023-12-29\', \'days\': 250, \'final\': 124.23049876285987, \'return_pct\': 24.230498762859867, \'max_drawdown_pct\': 10.276620410724846, \'min_value\': 99.18218518036204, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2023, \'method\': \'CPPI\', \'start\': \'2022-12-30\', \'end\': \'2023-12-29\', \'days\': 250, \'final\': 108.21710926812801, \'return_pct\': 8.217109268128013, \'max_drawdown_pct\': 4.438685847127244, \'min_value\': 99.75045784534726, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 249, \'risky_turnover\': 126.97547469962765}, {\'year\': 2023, \'method\': \'TIPP\', \'start\': \'2022-12-30\', \'end\': \'2023-12-29\', \'days\': 250, \'final\': 106.25637436648734, \'return_pct\': 6.256374366487336, \'max_drawdown_pct\': 2.8612126857772258, \'min_value\': 99.75371026368943, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 249, \'risky_turnover\': 81.63084180955325}, {\'year\': 2023, \'method\': \'Variable m\', \'start\': \'2022-12-30\', \'end\': \'2023-12-29\', \'days\': 250, \'final\': 110.93702914440992, \'return_pct\': 10.93702914440992, \'max_drawdown_pct\': 8.341719693211635, \'min_value\': 99.68500136245086, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 227, \'risky_turnover\': 572.2050468768298}, {\'year\': 2023, \'method\': \'OBPI (model)\', \'start\': \'2022-12-30\', \'end\': \'2023-12-29\', \'days\': 250, \'final\': 115.25169413346656, \'return_pct\': 15.251694133466557, \'max_drawdown_pct\': 11.078498311636874, \'min_value\': 99.09670009965333, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': None, \'option_sigma\': 0.24143956924871382, \'call_premium\': 9.595593323279886, \'call_units\': 1.0421450412804576}, {\'year\': 2024, \'method\': \'Buy & Hold\', \'start\': \'2023-12-29\', \'end\': \'2024-12-31\', \'days\': 252, \'final\': 123.30900681994953, \'return_pct\': 23.30900681994953, \'max_drawdown_pct\': 8.485142574816496, \'min_value\': 98.29868150437228, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2024, \'method\': \'SLPI\', \'start\': \'2023-12-29\', \'end\': \'2024-12-31\', \'days\': 252, \'final\': 123.30900681994953, \'return_pct\': 23.30900681994953, \'max_drawdown_pct\': 8.485142574816496, \'min_value\': 98.29868150437228, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2024, \'method\': \'CPPI\', \'start\': \'2023-12-29\', \'end\': \'2024-12-31\', \'days\': 252, \'final\': 107.85877279018138, \'return_pct\': 7.858772790181376, \'max_drawdown_pct\': 3.7170172043692995, \'min_value\': 99.49510312819616, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 251, \'risky_turnover\': 129.34203425908743}, {\'year\': 2024, \'method\': \'TIPP\', \'start\': \'2023-12-29\', \'end\': \'2024-12-31\', \'days\': 252, \'final\': 106.08787851429426, \'return_pct\': 6.08787851429426, \'max_drawdown_pct\': 2.4029373123866438, \'min_value\': 99.49510312819616, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 251, \'risky_turnover\': 75.30710571325812}, {\'year\': 2024, \'method\': \'Variable m\', \'start\': \'2023-12-29\', \'end\': \'2024-12-31\', \'days\': 252, \'final\': 112.97757371942525, \'return_pct\': 12.977573719425251, \'max_drawdown_pct\': 6.997211689023186, \'min_value\': 99.00656227345125, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 196, \'risky_turnover\': 558.2045163562586}, {\'year\': 2024, \'method\': \'OBPI (model)\', \'start\': \'2023-12-29\', \'end\': \'2024-12-31\', \'days\': 252, \'final\': 134.12340530463777, \'return_pct\': 34.12340530463777, \'max_drawdown_pct\': 14.215478396352088, \'min_value\': 98.3071861743009, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': None, \'option_sigma\': 0.13197293322632964, \'call_premium\': 5.282685381832842, \'call_units\': 1.8929766354040327}, {\'year\': 2025, \'method\': \'Buy & Hold\', \'start\': \'2024-12-31\', \'end\': \'2025-12-31\', \'days\': 250, \'final\': 116.38780406111908, \'return_pct\': 16.387804061119084, \'max_drawdown_pct\': 18.90220779115093, \'min_value\': 84.71750178096892, \'floor_breached\': True, \'max_shortfall\': 5.282498219031083, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': 0.0}, {\'year\': 2025, \'method\': \'SLPI\', \'start\': \'2024-12-31\', \'end\': \'2025-12-31\', \'days\': 250, \'final\': 86.26996257840091, \'return_pct\': -13.730037421599093, \'max_drawdown_pct\': 17.416078709015903, \'min_value\': 86.26996257840091, \'floor_breached\': True, \'max_shortfall\': 3.730037421599093, \'first_exit\': \'2025-04-04\', \'rebalance_count\': 1, \'risky_turnover\': 86.26996257840092}, {\'year\': 2025, \'method\': \'CPPI\', \'start\': \'2024-12-31\', \'end\': \'2025-12-31\', \'days\': 250, \'final\': 104.23164612063515, \'return_pct\': 4.231646120635148, \'max_drawdown_pct\': 5.425593887993241, \'min_value\': 95.83626726342581, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 249, \'risky_turnover\': 111.94825343957115}, {\'year\': 2025, \'method\': \'TIPP\', \'start\': \'2024-12-31\', \'end\': \'2025-12-31\', \'days\': 250, \'final\': 103.63220836120767, \'return_pct\': 3.632208361207674, \'max_drawdown_pct\': 4.850769923520226, \'min_value\': 96.35967184220355, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 249, \'risky_turnover\': 87.5005489639421}, {\'year\': 2025, \'method\': \'Variable m\', \'start\': \'2024-12-31\', \'end\': \'2025-12-31\', \'days\': 250, \'final\': 103.66857204828764, \'return_pct\': 3.6685720482876434, \'max_drawdown_pct\': 6.4173233947985135, \'min_value\': 95.21442147350047, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 249, \'risky_turnover\': 443.11015800906296}, {\'year\': 2025, \'method\': \'OBPI (model)\', \'start\': \'2024-12-31\', \'end\': \'2025-12-31\', \'days\': 250, \'final\': 122.46573011505211, \'return_pct\': 22.46573011505211, \'max_drawdown_pct\': 13.41523497182907, \'min_value\': 90.53777178742604, \'floor_breached\': False, \'max_shortfall\': 0.0, \'first_exit\': None, \'rebalance_count\': 0, \'risky_turnover\': None, \'option_sigma\': 0.1266121925532293, \'call_premium\': 5.047723862375491, \'call_units\': 1.9810909377467283}]\nfor method in sorted({row["method"] for row in historical_results}):\n    group = [row for row in historical_results if row["method"] == method]\n    average = sum(row["return_pct"] for row in group)/len(group)\n    worst = max(row["max_drawdown_pct"] for row in group)\n    breaches = sum(row["floor_breached"] for row in group)\n    print(f"{method}: mean annual return {average:.2f}%; worst within-year drawdown {worst:.2f}%; breach years {breaches}/8")\nprint("Annual resets, price-only S&P 500, zero rate/costs; OBPI uses theoretical option prices.")\n'


CHECK_CODE = r'''# Independent analytic checks. These do not depend on your editable controls above.
flat = [0.0]*12
close(simulate(returns=flat)["metrics"]["final"], 100)
close(simulate()["metrics"]["final"], 87.411904)
assert simulate()["metrics"]["floorBreached"] and simulate()["metrics"]["locked"]
gap = simulate(returns=[-0.4, 0.5]+[0]*10)
close(gap["rows"][1]["cppi"], 88)
assert all(row["exposure"] == 0 and row["cppi"] == 88 for row in gap["rows"][1:])
touch = simulate(multiplier=2, returns=[-0.5, 1]+[0]*10)
assert touch["metrics"]["locked"] and not touch["metrics"]["floorBreached"]
assert not simulate(scenario="whipsaw")["metrics"]["locked"]
safe = simulate(multiplier=0, rate=0.06, returns=flat)
close(safe["rows"][0]["floor"], 90*math.exp(-0.06))
close(safe["rows"][-1]["floor"], 90)
close(safe["metrics"]["final"], 100*math.exp(0.06))
no_lookahead_a = simulate(returns=[0.1, -0.1, 0.05]+[0.05]*9)
no_lookahead_b = simulate(returns=[0.1, -0.1, 0.05]+[-0.15]*9)
assert no_lookahead_a["rows"][:4] == no_lookahead_b["rows"][:4]
one = simulate(multiplier=1, rate=0.04)
reserve = 90*math.exp(-0.04)
for row in one["rows"]:
    close(row["cppi"], reserve*math.exp(0.04*row["month"]/12)+(100-reserve)*row["asset"]/100)
close(one["metrics"]["totalTurnover"], 0)
put_check = protective_put()
for key, expected in {"putPayoff": 10, "terminalWealth": 90, "initialCost": 104, "profit": -14}.items():
    close(put_check[key], expected)
assert len(list(csv.reader(io.StringIO(cppi_csv(simulate()))))) == 14
for invalid in [dict(initial=0), dict(floor_pct=101), dict(multiplier=-1), dict(returns=[-1.1]+[0]*11)]:
    try:
        simulate(**invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(f"Invalid inputs accepted: {invalid}")
print("All analytic checks passed: gap risk, cash lock, floor discounting, no lookahead, payoff vs profit, and CSV.")
print("Default crash CPPI = 87.411904; default put payoff / wealth / profit = 10 / 90 / -14.")'''


def scenario_data(model_text):
    matches = re.findall(r"id:\s*'([^']+)'.*?returns:\s*(\[[^\]]+\])", model_text, flags=re.S)
    paths = {name: json.loads(values) for name, values in matches}
    if set(paths) != {"rally", "crash", "whipsaw", "recovery"} or any(len(v) != 12 for v in paths.values()):
        raise ValueError("Could not read all four 12-month scenarios from src/math.mjs.")
    return paths


FIGURE_PATTERN = re.compile(r'<figure\b([^>]*)>(.*?)</figure>', flags=re.S)
ATTRIBUTE_PATTERN = re.compile(r'''([\w:-]+)\s*=\s*(["'])(.*?)\2''', flags=re.S)
DIAGRAM_NAME_PATTERN = re.compile(r'[a-z0-9][a-z0-9-]*\.svg')
ATTACHMENT_PATTERN = re.compile(r'!\[(?:\\.|[^\]\\])*\]\(attachment:([^)]+)\)')


def figure_markdown(match):
    """Turn a canonical lesson figure into a portable image and its caption."""
    attributes = {name: html.unescape(value) for name, _, value in ATTRIBUTE_PATTERN.findall(match[1])}
    if "lesson-figure" not in attributes.get("class", "").split():
        raise ValueError("A chapter figure must use the lesson-figure class.")
    content = re.fullmatch(r'\s*<img\b([^>]*)>\s*<figcaption\b[^>]*>(.*?)</figcaption>\s*', match[2], flags=re.S)
    if content is None:
        raise ValueError("A lesson figure must contain one image followed by its plain-text caption.")
    image_attributes = {name: html.unescape(value) for name, _, value in ATTRIBUTE_PATTERN.findall(content[1])}
    asset = re.fullmatch(r'assets/diagrams/([a-z0-9][a-z0-9-]*\.svg)', image_attributes.get("src", ""))
    if asset is None:
        raise ValueError("Lesson figures must use local SVG files in assets/diagrams/.")
    alt = " ".join(image_attributes.get("alt", "").split())
    if not alt:
        raise ValueError(f"Missing diagram alt text: {asset[1]}")
    if re.search(r'<[^>]+>', content[2]):
        raise ValueError(f"Diagram caption must be plain text: {asset[1]}")
    caption = " ".join(html.unescape(content[2]).split())
    if not caption:
        raise ValueError(f"Missing diagram caption: {asset[1]}")
    alt = alt.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    anchor = ""
    if "id" in attributes:
        if not re.fullmatch(r'[a-z][a-z0-9-]*', attributes["id"]):
            raise ValueError("A lesson figure ID must be an English kebab-case anchor.")
        anchor = f'<a id="{attributes["id"]}"></a>\n\n'
    return f'\n\n{anchor}![{alt}](attachment:{asset[1]})\n\n{caption}\n\n'


def markdown_attachments(text):
    """Embed each referenced SVG verbatim; readers need no separate asset files."""
    attachments = {}
    for filename in ATTACHMENT_PATTERN.findall(text):
        if not DIAGRAM_NAME_PATTERN.fullmatch(filename):
            raise ValueError(f"Invalid diagram attachment filename: {filename}")
        svg = (ROOT / "assets/diagrams" / filename).read_bytes().decode("utf-8")
        attachments[filename] = {"image/svg+xml": svg}
    return attachments


def clean_markdown(text):
    text = FIGURE_PATTERN.sub(figure_markdown, text)
    text = re.sub(r'<noscript\b[^>]*>.*?</noscript>', '', text, flags=re.S)
    text = re.sub(r'<a\b[^>]*\bdownload\b[^>]*>.*?</a>', '', text, flags=re.S)
    text = re.sub(r'^.*\[.*?\]\([^)]*\.ipynb\).*$', '', text, flags=re.M)
    text = re.sub(r'<section\b[^>]*\bid="([^"]+)"[^>]*>', r'<a id="\1"></a>\n', text)
    text = re.sub(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.S)
    text = re.sub(r'<summary\b[^>]*>(.*?)</summary>', r'**\1**\n', text, flags=re.S)
    text = text.replace('<strong>', '**').replace('</strong>', '**')
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</?(?:div|section|details|p|span)\b[^>]*>', '\n', text)
    def local_link(match):
        target = match[1]
        if target.startswith('portfolio-insurance.html#'):
            return '](' + target.split('.html', 1)[1] + ')'
        return '](../' + target + ')'
    text = re.sub(r'\]\(((?:[\w-]+\.html)(?:#[^)]*)?)\)', local_link, text)
    text = re.sub(r'\]\((downloads/[^)]+)\)', r'](../\1)', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def build_notebook():
    source = CHAPTER.read_text(encoding="utf-8")
    model_text = MODEL.read_text(encoding="utf-8")
    body = re.sub(r"\A---\n.*?\n---\n", "", source, flags=re.S)
    cells, namespace = [], {}

    def markdown(text, source_role="chapter"):
        cleaned = clean_markdown(text)
        if cleaned:
            cell = dict(cell_type="markdown", metadata={"toolkit_role": source_role}, source=cleaned)
            attachments = markdown_attachments(cleaned)
            if attachments:
                cell["attachments"] = attachments
            cells.append(cell)

    def code(text, hidden=False):
        count = 1+sum(cell["cell_type"] == "code" for cell in cells)
        captured, outputs = io.StringIO(), []
        def flush():
            value = captured.getvalue()
            if value:
                outputs.append(dict(output_type="stream", name="stdout", text=value))
                captured.seek(0)
                captured.truncate(0)
        def capture_svg(svg):
            flush()
            outputs.append(dict(output_type="display_data", metadata={},
                                data={"image/svg+xml": svg, "text/plain": "Deterministic chart; numerical values are printed in this notebook."}))
        namespace["_portfolio_svg_capture"] = capture_svg
        with contextlib.redirect_stdout(captured):
            exec(compile(text, f"portfolio_cell_{count}", "exec"), namespace)
        flush()
        metadata = {"jupyter": {"source_hidden": True}} if hidden else {}
        cells.append(dict(cell_type="code", metadata=metadata, source=text,
                          execution_count=count, outputs=outputs))

    markdown("# Notebook: Portfolio Insurance\n\nคำอธิบายและสมการต่อไปนี้มาจากบทเรียนเดียวกับเว็บไซต์ **Portfolio Management Toolkit Notes** ใช้ Python 3 และ standard library สำหรับคำนวณ เลือก **Run All** ได้โดยไม่ต้องดาวน์โหลดข้อมูลหรือติดตั้งแพ็กเกจคำนวณ กราฟ SVG ฝังอยู่ในไฟล์และใช้ IPython เพื่อแสดงผลเมื่อมีให้ใช้\n\nเซลล์ตั้งต้นเก็บฟังก์ชันร่วม ส่วนเซลล์ทดลองอยู่ถัดจากเนื้อหาที่เกี่ยวข้อง ปรับค่าตัวแปรแล้วรันตามลำดับ ตัวเลขทั้งหมดในห้องทดลองเป็นตัวอย่างสมมติ ไม่ใช่ข้อมูลตลาดหรือการทำซ้ำวิทยานิพนธ์\n\nลิงก์ไปหน้าอื่นใช้ไฟล์ในชุดเว็บไซต์ที่อยู่ระดับเหนือโฟลเดอร์ `notebooks/`; การคำนวณใน Notebook ทำงานได้แม้แยกไฟล์นี้ออกมา", source_role="introduction")
    code(MODEL_CODE.replace("__SCENARIOS__", json.dumps(scenario_data(model_text), ensure_ascii=False, indent=4)), hidden=True)
    code(CHART_CODE, hidden=True)

    # Split at known mounts and selected closing section boundaries, retaining
    # every prose segment (including content outside section wrappers).
    sections = list(re.finditer(r'<section\b[^>]*id="([^"]+)"[^>]*>(.*?)</section>', body, flags=re.S))
    if not sections:
        raise ValueError("The canonical chapter must be ready with its section IDs before generation.")
    required = {"put-lab", "allocation-guide", "cppi-lab"}
    mounts_seen, position = set(), 0
    markdown(body[:sections[0].start()])
    for section in sections:
        if position and position < section.start():
            markdown(body[position:section.start()])
        section_id, text = section.groups()
        text = f'<a id="{section_id}"></a>\n' + text
        cursor = 0
        for mount in re.finditer(r'<div\b[^>]*id="([^"]+)"[^>]*>\s*</div>', text):
            mount_id = mount[1]
            markdown(text[cursor:mount.start()])
            if mount_id not in SNIPPETS:
                raise ValueError(f"Unmapped interactive mount: {mount_id}")
            if mount_id in mounts_seen:
                raise ValueError(f"Duplicate interactive mount: {mount_id}")
            mounts_seen.add(mount_id)
            code(SNIPPETS[mount_id])
            cursor = mount.end()
        markdown(text[cursor:])
        if section_id in SECTION_SNIPPETS:
            code(SECTION_SNIPPETS[section_id])
        position = section.end()
    markdown(body[position:])
    if mounts_seen != required:
        raise ValueError(f"Expected all lesson mounts before generation; found {sorted(mounts_seen)}")
    markdown("## ตรวจผลคำนวณ\n\nเซลล์นี้ตรวจตัวอย่างที่ทราบคำตอบ การหลุด floor การติด cash lock การคิดลด และการใช้เฉพาะข้อมูลที่มีอยู่ ณ เวลาจัดพอร์ต ผลตรวจอ้างอิงค่าเริ่มต้นของตัวอย่าง จึงแยกจากตัวควบคุมที่แก้ได้ข้างต้น", source_role="validation")
    code(CHECK_CODE)
    for index, cell in enumerate(cells):
        cell["id"] = f"portfolio-insurance-{index:02d}"
    notebook = dict(nbformat=4, nbformat_minor=5, cells=cells, metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": sys.version.split()[0], "file_extension": ".py"},
        "source": {"path": "content/portfolio-insurance.md", "sha256": hashlib.sha256(source.encode()).hexdigest(),
                   "model_path": "src/math.mjs", "model_sha256": hashlib.sha256(model_text.encode()).hexdigest()},
        "execution": {"method": "Python exec in a shared namespace; captured stdout and SVG outputs", "generator": "scripts/make_notebook.py"},
        "visual_generation": {"route": "no-image-generator", "method": "Deterministic SVG charts and self-contained SVG lesson diagram attachments; QuantCorner light chart palette"},
    })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    count = sum(cell["cell_type"] == "code" for cell in cells)
    charts = sum(output.get("output_type") == "display_data" for cell in cells for output in cell.get("outputs", []))
    diagrams = sum(len(cell.get("attachments", {})) for cell in cells)
    print(f"Wrote {OUTPUT.name}: {len(cells)} cells; {count} executed code cells; {charts} embedded SVG charts; {diagrams} SVG diagram attachments.")
    return notebook


if __name__ == "__main__":
    build_notebook()
