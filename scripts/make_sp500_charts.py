"""Render daily wealth and drawdown comparisons from the locally held, pinned S&P 500 input.

Usage: python3 scripts/make_sp500_charts.py INPUT.csv
Annual experiments are chained without deposits. Each strategy renews its floor
and allocation at each year boundary; this is NOT one unchanging eight-year floor.
Only derived SVG graphics and aggregate metadata are published, not raw quotes.
"""
import base64
import datetime as dt
import hashlib
import html
import json
import math
import sys
from pathlib import Path
from sp500_backtest import load_prices, simulate_year

ROOT = Path(__file__).resolve().parents[1]
METHODS = {'slpi': 'SLPI', 'cppi': 'CPPI', 'tipp': 'TIPP', 'variable-m': 'Variable m'}
BENCHMARK = 'Buy & Hold'
COLORS = {BENCHMARK: '#00796e', 'strategy': '#6200ee'}


def chain_years(annual):
    """Scale each independent, 100-unit year by actual wealth entering that year."""
    methods = [BENCHMARK, *METHODS.values()]
    years = sorted({r['year'] for r in annual})
    start = next(r['start'] for r in annual if r['year'] == years[0])
    paths = {method: [(start, 100.)] for method in methods}
    for year in years:
        for method in methods:
            result = next(r for r in annual if r['year'] == year and r['method'] == method)
            assert paths[method][-1][0] == result['start'], 'Non-contiguous annual paths'
            base = paths[method][-1][1]
            paths[method].extend((date, base * wealth / 100) for date, wealth, *_ in result['path'])
    return paths


def metrics(path):
    peak, drawdown = 100., 0.
    for _, value in path:
        peak = max(peak, value)
        drawdown = max(drawdown, 100 * (1 - value / peak))
    return {'final': path[-1][1], 'return_pct': path[-1][1] - 100,
            'max_drawdown_pct': drawdown}


def drawdown_path(path):
    """Signed percentage below each portfolio's own running peak, without annual resets."""
    peak = path[0][1]
    result = []
    for date, value in path:
        peak = max(peak, value)
        result.append((date, 100 * (value / peak - 1)))
    return result


def layout(mobile=False, kind='wealth'):
    return dict(width=320 if mobile else 800, height=410 if mobile else 460,
                left=40 if mobile else 60, right=304 if mobile else 774,
                top=158 if mobile else 152, bottom=344 if mobile else 388,
                ymin=-40 if kind == 'drawdown' else 0, ymax=0 if kind == 'drawdown' else 300)


def render(paths, method, mobile=False, kind='wealth'):
    assert kind in ('wealth', 'drawdown')
    is_drawdown = kind == 'drawdown'
    plotted = {name: drawdown_path(path) for name, path in paths.items()} if is_drawdown else paths
    box = layout(mobile, kind)
    w, h, left, right, top, bottom = (box[k] for k in ('width','height','left','right','top','bottom'))
    start, end = (dt.date.fromisoformat(paths[BENCHMARK][i][0]) for i in (0, -1))
    x = lambda date: left + (dt.date.fromisoformat(date)-start).days/(end-start).days*(right-left)
    y = lambda value: bottom - (value-box['ymin'])/(box['ymax']-box['ymin'])*(bottom-top)
    text = lambda xx, yy, value, size=14, extra='': f'<text x="{xx}" y="{yy}" font-size="{size}" {extra}>{html.escape(str(value))}</text>'
    family = base64.b64encode((ROOT/'assets/fonts/roboto-latin-400-normal.woff2').read_bytes()).decode()
    thai = base64.b64encode((ROOT/'assets/fonts/noto-sans-thai-thai-400-normal.woff2').read_bytes()).decode()
    title = f'{method} vs Buy & Hold | S&P 500 | 2018–2025'
    desc = (f'Daily portfolio wealth, initial 100 on {start}, through {end}. Annual floor reset to 90% of entering wealth. '
            f'Buy & Hold ends at {paths[BENCHMARK][-1][1]:.2f}; {method} ends at {paths[method][-1][1]:.2f}. '
            'Price index without dividends; zero interest and costs; 2012 observations including inception.')
    if is_drawdown:
        title = f'Drawdown | {method} vs Buy & Hold | S&P 500 | 2018–2025'
        desc = (f'Daily drawdown, 100 times (wealth / running peak - 1), from {start} through {end}. '
                f'Maximum drawdown: Buy & Hold {metrics(paths[BENCHMARK])["max_drawdown_pct"]:.2f}%; '
                f'{method} {metrics(paths[method])["max_drawdown_pct"]:.2f}%. '
                'Each portfolio has its own peak, including initial wealth 100. Peaks do not reset each year. '
                'Negative values show loss below the peak; zero means at a running high. 2012 observations.')
    scale_description = 'linear drawdown y axis -40% to 0%' if is_drawdown else 'linear wealth y axis 0–300'
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
              f'<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(desc)}</desc>',
              f'<metadata>Source: S&amp;P Dow Jones Indices via FRED SP500, retrieved 2026-09-19. Derived educational calculation. Calendar-date x axis; {scale_description}, common to all four charts. No smoothing or resampling. Annual rules and limitations: portfolio-insurance.html#sp500-test.</metadata>',
              f'<style>@font-face{{font-family:Roboto;src:url(data:font/woff2;base64,{family})}}@font-face{{font-family:Thai;src:url(data:font/woff2;base64,{thai})}}text{{font-family:Roboto,Thai,sans-serif;fill:#212121}}.muted{{fill:#616161}}</style>',
              f'<rect width="{w}" height="{h}" fill="#fff"/>',
              text(18 if mobile else 28, 30, f'Drawdown · {method}' if is_drawdown else f'{method} vs Buy & Hold', 19 if mobile else 25),
              text(18 if mobile else 28, 54, 'S&P 500 · 2018–2025 · จุดสูงสุดตลอดช่วง' if is_drawdown else 'S&P 500 · 2018–2025 · ตั้ง Floor ใหม่ทุกปี', 13 if mobile else 16, 'class="muted"')]
    # Separate strokes and explicit labels distinguish series without color alone.
    for i, name in enumerate((BENCHMARK, method)):
        yy = 81 + i*25
        color = COLORS[BENCHMARK] if i == 0 else COLORS['strategy']
        dash = ' stroke-dasharray="7 4"' if i == 0 else ''
        pieces.append(f'<path d="M 20 {yy-5} H 46" stroke="{color}" stroke-width="3"{dash}/>')
        label = f'{name}   ลึกสุด {metrics(paths[name])["max_drawdown_pct"]:.2f}%' if is_drawdown else f'{name}   {paths[name][-1][1]:.2f}'
        pieces.append(text(54, yy, label, 15 if mobile else 18))
    pieces.append(text(left, top-13, 'Drawdown (%) · ยิ่งลึก ยิ่งลดจากจุดสูงสุด' if is_drawdown else 'มูลค่าพอร์ต · เริ่ม 100 หน่วย', 12 if mobile else 15, 'class="muted"'))
    for value in (range(0, -41, -10) if is_drawdown else range(0, 301, 50)):
        yy = y(value)
        pieces.append(f'<path d="M {left} {yy:.3f} H {right}" stroke="{"#bdbdbd" if value==(0 if is_drawdown else 100) else "#e5e5e5"}" stroke-width="1"/>')
        pieces.append(text(left-8, round(yy+4, 3), value, 12 if mobile else 15, 'text-anchor="end" class="muted"'))
    for year in range(2018, 2026, 2 if mobile else 1):
        xx = x(f'{year}-01-01')
        pieces.append(f'<path d="M {xx:.3f} {top} V {bottom}" stroke="#eeeeee" stroke-width="1"/>')
        pieces.append(text(round(xx,3), bottom+23, year, 12 if mobile else 15, 'text-anchor="middle" class="muted"'))
    for name in (BENCHMARK, method):
        color = COLORS[BENCHMARK] if name == BENCHMARK else COLORS['strategy']
        points = ' '.join(f'{x(date):.3f},{y(value):.3f}' for date,value in plotted[name])
        dash = ' stroke-dasharray="7 4"' if name == BENCHMARK else ''
        pieces.append(f'<polyline data-series="{html.escape(name)}" points="{points}" fill="none" stroke="{color}" stroke-width="{1.8 if mobile else 2.4}" stroke-linejoin="round"{dash}/>')
        pieces.append(f'<circle cx="{right}" cy="{y(plotted[name][-1][1]):.3f}" r="3" fill="{color}"/>')
    pieces.extend([text(18 if mobile else 28, h-25, 'ราคาปิดรายวัน · ไม่รวมปันผลและต้นทุน', 12 if mobile else 14, 'class="muted"'),
                   text(18 if mobile else 28, h-8, 'ที่มา: S&P DJI / FRED · สิ้นสุด 31 ธ.ค. 2025', 11 if mobile else 14, 'class="muted"'), '</svg>\n'])
    return '\n'.join(pieces)


def generate(input_path):
    published = json.loads((ROOT/'data/sp500-results.json').read_text())
    digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    assert digest == published['source']['sha256'], 'Use the input pinned to the annual tables'
    prices = load_prices(input_path)
    annual = [r for year in range(2018,2026) for r in simulate_year(prices,year,keep_paths=True)]
    for actual, expected in zip(annual, published['annual']):
        assert {k:v for k,v in actual.items() if k != 'path'} == expected
    paths = chain_years(annual)
    # Independent telescope: chaining Buy & Hold must equal a single purchase.
    lookup = dict((d.isoformat(), v) for d,v in prices)
    initial = lookup[paths[BENCHMARK][0][0]]
    for date, value in paths[BENCHMARK]:
        assert math.isclose(value, 100*lookup[date]/initial, rel_tol=1e-12)
    metadata = dict(source=published['source'], engine_sha256=published['engine_sha256'],
        generator='scripts/make_sp500_charts.py',
        period=['2017-12-29','2025-12-31'], observations=len(paths[BENCHMARK]),
        methods=list(METHODS.values()), benchmark=BENCHMARK,
        rule='Compound the annual experiments. Reset floor to 90% of entering wealth each year; SLPI re-enters at each year start; TIPP high-water mark resets each year. No deposits or withdrawals.',
        assumptions='Same daily-close execution and lagged volatility as annual tables. Zero interest/costs; no dividends; no OBPI.',
        metrics={name:metrics(path) for name,path in paths.items()},
        year_end={name:{date[:4]:v for date,v in path if date in {r['end'] for r in annual}} for name,path in paths.items()},
        drawdown='Signed percent below own running peak, including inception; no annual reset, not annualized. Common -40% to 0% axis.',
        files={})
    out=ROOT/'assets/charts'
    out.mkdir(exist_ok=True)
    for slug, method in METHODS.items():
        for kind in ('wealth', 'drawdown'):
            for mobile in (False,True):
                filename=f'sp500-{slug}{"-drawdown" if kind == "drawdown" else ""}{"-mobile" if mobile else ""}.svg'
                svg=render(paths,method,mobile,kind)
                (out/filename).write_text(svg,encoding='utf-8')
                metadata['files'][filename]={'sha256':hashlib.sha256(svg.encode()).hexdigest(), 'method':method, 'mobile':mobile, 'kind':kind, 'layout':layout(mobile,kind)}
    (ROOT/'data/sp500-charts.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Generated four wealth and four drawdown charts, desktop/mobile exports; 2012 observations per line. No raw quotes exported.')
    print(json.dumps(metadata['metrics'],indent=2))


if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit(__doc__)
    generate(Path(sys.argv[1]))
