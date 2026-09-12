"""Build a self-contained, executed notebook from the canonical Thai chapter.

Calculations require Python's standard library only. IPython is used optionally
to show deterministic SVG charts when a reader runs the notebook interactively.
"""
import contextlib
import hashlib
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


def clean_markdown(text):
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
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def build_notebook():
    source = CHAPTER.read_text(encoding="utf-8")
    model_text = MODEL.read_text(encoding="utf-8")
    body = re.sub(r"\A---\n.*?\n---\n", "", source, flags=re.S)
    cells, namespace = [], {}

    def markdown(text, source_role="chapter"):
        cleaned = clean_markdown(text)
        if cleaned:
            cells.append(dict(cell_type="markdown", metadata={"toolkit_role": source_role}, source=cleaned))

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

    markdown("# Notebook: Portfolio Insurance\n\nคำอธิบายและสมการต่อไปนี้มาจากบทเรียนเดียวกับเว็บไซต์ **Portfolio Management Toolkit** ใช้ Python 3 และ standard library สำหรับคำนวณ เลือก **Run All** ได้โดยไม่ต้องดาวน์โหลดข้อมูลหรือติดตั้งแพ็กเกจคำนวณ กราฟ SVG ฝังอยู่ในไฟล์และใช้ IPython เพื่อแสดงผลเมื่อมีให้ใช้\n\nเซลล์ตั้งต้นเก็บฟังก์ชันร่วม ส่วนเซลล์ทดลองอยู่ถัดจากเนื้อหาที่เกี่ยวข้อง ปรับค่าตัวแปรแล้วรันตามลำดับ ตัวเลขทั้งหมดในห้องทดลองเป็นตัวอย่างสมมติ ไม่ใช่ข้อมูลตลาดหรือการทำซ้ำวิทยานิพนธ์\n\nลิงก์ไปหน้าอื่นใช้ไฟล์ในชุดเว็บไซต์ที่อยู่ระดับเหนือโฟลเดอร์ `notebooks/`; การคำนวณใน Notebook ทำงานได้แม้แยกไฟล์นี้ออกมา", source_role="introduction")
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
        "visual_generation": {"route": "no-image-generator", "method": "Deterministic SVG from displayed numerical observations; QuantCorner light chart palette"},
    })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    count = sum(cell["cell_type"] == "code" for cell in cells)
    charts = sum(output.get("output_type") == "display_data" for cell in cells for output in cell.get("outputs", []))
    print(f"Wrote {OUTPUT.name}: {len(cells)} cells; {count} executed code cells; {charts} embedded SVG charts.")
    return notebook


if __name__ == "__main__":
    build_notebook()
