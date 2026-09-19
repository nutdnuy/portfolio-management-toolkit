"""Analytic and leakage checks; optional verification of locally held index data."""
import ast
import csv
import datetime as dt
import importlib.util
import json
import math
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('sp500_backtest', ROOT/'scripts/sp500_backtest.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
close = lambda a,b: math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8)
assert close(engine.call_price(100,100,.2,1),7.965567455405804)
assert engine.call_price(80,100,.2,0) == 0
assert engine.call_price(120,100,.2,0) == 20
assert all(close(engine.variable_multiplier(s),m) for s,m in zip((.1,.2,.4),(6,3,1.5)))

# Synthetic business-day prices: small warm-up moves, then a known gap and recovery.
rows=[]; day=dt.date(2018,1,1); value=100.; count=0
while day <= dt.date(2020,12,31):
    if day.weekday() < 5:
        change = .001 if count%2 else -.001
        if day==dt.date(2020,1,1): change=-.4
        if day==dt.date(2020,1,2): change=.5
        value*=1+change;rows.append((day,value));count+=1
    day+=dt.timedelta(days=1)
results=engine.simulate_year(rows,2020,keep_paths=True)
by_name={r['method']:r for r in results}
for name in ('CPPI','TIPP'):
    assert close(by_name[name]['path'][0][1],88)
    assert close(by_name[name]['final'],88)
    assert by_name[name]['floor_breached']
assert close(by_name['SLPI']['final'],60)
assert by_name['SLPI']['rebalance_count']==1
assert by_name['OBPI (model)']['min_value'] >= 90-1e-8
base = next(v for d,v in reversed(rows) if d.year==2019)
assert close(by_name['Buy & Hold']['final'],100*rows[-1][1]/base)

# Changing future quotes must not alter any earlier wealth, floor or exposure.
cutoff=dt.date(2020,6,1)
altered=[(d,v if d<=cutoff else v*1.3) for d,v in rows]
future=engine.simulate_year(altered,2020,keep_paths=True)
for left,right in zip(results,future):
    early=lambda r:[p for p in r['path'] if dt.date.fromisoformat(p[0])<=cutoff]
    assert early(left)==early(right),left['method']
    for date,wealth,floor,exposure in left['path']:
        if left['method']!='OBPI (model)':
            assert -1e-8 <= exposure <= wealth+1e-8
    if left['method']=='TIPP':
        floors=[p[2] for p in left['path']]
        assert floors==sorted(floors)

# Independent published aggregate checks; no network or private data required in CI.
published=json.loads((ROOT/'data/sp500-results.json').read_text())
assert len(published['annual'])==48
assert {r['year'] for r in published['annual']}==set(range(2018,2026))
for r in published['annual']:
    assert close(r['final']-100,r['return_pct'])
    assert 0<=r['max_drawdown_pct']<=100 and r['days']>=240
    assert r['floor_breached']==(r['max_shortfall']>1e-8)
    if r['method']=='OBPI (model)':
        bh=next(b for b in published['annual'] if b['year']==r['year'] and b['method']=='Buy & Hold')
        assert close(r['final'],90+r['call_units']*max(bh['return_pct'],0))
for s in published['summary']:
    group=[r for r in published['annual'] if r['method']==s['method']]
    assert close(s['mean_annual_return_pct'],sum(r['return_pct'] for r in group)/8)
    assert close(s['worst_within_year_drawdown_pct'],max(r['max_drawdown_pct'] for r in group))

if len(sys.argv)>1:
    raw=Path(sys.argv[1])
    assert engine.hashlib.sha256(raw.read_bytes()).hexdigest()==published['source']['sha256']
    prices=engine.load_prices(raw)
    actual=engine.run(prices)
    for key in ('annual','summary','obpi_sensitivity'):
        assert actual[key]==published[key],f'Stale generated {key}'
    print('All 48 empirical rows regenerated exactly from the pinned local input.')
print('S&P 500 checks passed: analytic option price, gap/stop, caps, TIPP floor, no future leakage, and aggregate consistency.')

# Presentation checks bind the public prose, CSV and Notebook to the same result set.
assert published['engine_sha256']==engine.hashlib.sha256((ROOT/'scripts/sp500_backtest.py').read_bytes()).hexdigest()
chapter=(ROOT/'content/portfolio-insurance.md').read_text()
for metric, marker in [('return_pct','return'),('max_drawdown_pct','drawdown')]:
    block=chapter.split('<!-- sp500-'+marker+'-table:start -->')[1].split('<!-- sp500-'+marker+'-table:end -->')[0]
    for year in range(2018,2026):
        group={r['method']:r for r in published['annual'] if r['year']==year}
        expected='| '+str(year)+' | '+' | '.join(f"{group[m][metric]:.2f}%" for m in engine.METHODS)+' |'
        assert expected in block, ('Stale table',metric,year)
block=chapter.split('<!-- sp500-summary-table:start -->')[1].split('<!-- sp500-summary-table:end -->')[0]
for result in published['summary']:
    for key in ('mean_annual_return_pct','worst_within_year_drawdown_pct'):
        assert f"{result[key]:.2f}%" in block
with (ROOT/'data/sp500-results.csv').open(newline='') as handle:
    exported=list(csv.DictReader(handle))
assert len(exported)==48
for actual,expected in zip(exported,published['annual']):
    for key,value in actual.items():
        assert value==('' if expected.get(key) is None else str(expected[key])),(key,value)
notebook=json.loads((ROOT/'notebooks/portfolio-insurance.ipynb').read_text())
found=False
for cell in notebook['cells']:
    if cell['cell_type']=='code' and 'historical_results = ' in cell['source']:
        tree=ast.parse(cell['source'])
        assignment=next(node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='historical_results' for t in node.targets))
        assert ast.literal_eval(assignment.value)==published['annual']
        found=True
assert found,'Notebook omitted derived historical results'
print('Chapter tables, exported CSV, engine fingerprint and Notebook results match the published JSON.')
