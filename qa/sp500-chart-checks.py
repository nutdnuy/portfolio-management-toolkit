"""Verify chained annual wealth and the actual geometry of every published SVG."""
import datetime as dt
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'scripts'))
import make_sp500_charts as charts

# A renewed year's percentage change applies to actual entering wealth, not 100.
example=[]
for method in (charts.BENCHMARK,*charts.METHODS.values()):
    example.extend([
        dict(year=2018,method=method,start='2017-12-29',path=[('2018-01-02',50),('2018-12-31',150)]),
        dict(year=2019,method=method,start='2018-12-31',path=[('2019-01-02',90),('2019-12-31',110)])])
for path in charts.chain_years(example).values():
    assert [value for _,value in path]==[100,50,150,135,165]
    assert charts.metrics(path)['max_drawdown_pct']==50

metadata=json.loads((ROOT/'data/sp500-charts.json').read_text())
annual=json.loads((ROOT/'data/sp500-results.json').read_text())
assert metadata['source']==annual['source']
assert metadata['engine_sha256']==annual['engine_sha256']
assert metadata['methods']==list(charts.METHODS.values())
assert metadata['observations']==2012 and len(metadata['files'])==8
start,end=map(dt.date.fromisoformat,metadata['period'])
ns={'s':'http://www.w3.org/2000/svg'}
for filename,info in metadata['files'].items():
    svg=(ROOT/'assets/charts'/filename).read_bytes()
    assert hashlib.sha256(svg).hexdigest()==info['sha256']
    root=ET.fromstring(svg)
    assert root.find('s:title',ns) is not None and root.find('s:desc',ns) is not None
    lines=root.findall('s:polyline',ns)
    assert [line.attrib['data-series'] for line in lines]==[charts.BENCHMARK,info['method']]
    assert lines[0].attrib.get('stroke-dasharray') and not lines[1].attrib.get('stroke-dasharray')
    box=info['layout']; xdates=None
    for line in lines:
        method=line.attrib['data-series']
        points=[tuple(map(float,pair.split(','))) for pair in line.attrib['points'].split()]
        assert len(points)==metadata['observations']
        xx=[p[0] for p in points];assert all(a<b for a,b in zip(xx,xx[1:]))
        if xdates is not None: assert xx==xdates
        xdates=xx
        values=[300*(box['bottom']-yy)/(box['bottom']-box['top']) for _,yy in points]
        assert all(math.isfinite(v) and 0<=v<=300 for v in values)
        assert abs(values[0]-100)<.002
        assert abs(values[-1]-metadata['metrics'][method]['final'])<.002
        cumulative=100
        for result in (r for r in annual['annual'] if r['method']==method):
            cumulative*=result['final']/100
            assert math.isclose(cumulative,metadata['year_end'][method][str(result['year'])],rel_tol=1e-12)
            date=dt.date.fromisoformat(result['end'])
            x=box['left']+(date-start).days/(end-start).days*(box['right']-box['left'])
            index=min(range(len(xx)),key=lambda i:abs(xx[i]-x))
            assert abs(xx[index]-x)<.0006 and abs(values[index]-cumulative)<.002
        reconstructed=charts.metrics([(str(i),v) for i,v in enumerate(values)])
        assert abs(reconstructed['max_drawdown_pct']-metadata['metrics'][method]['max_drawdown_pct'])<.005
    assert abs(xx[0]-box['left'])<.001 and abs(xx[-1]-box['right'])<.001

# Optional exact regeneration from permitted local quotes; CI never needs the raw file.
if len(sys.argv)>1:
    raw=Path(sys.argv[1]);assert hashlib.sha256(raw.read_bytes()).hexdigest()==annual['source']['sha256']
    prices=charts.load_prices(raw)
    results=[r for year in range(2018,2026) for r in charts.simulate_year(prices,year,keep_paths=True)]
    paths=charts.chain_years(results)
    for filename,info in metadata['files'].items():
        assert charts.render(paths,info['method'],info['mobile'])==(ROOT/'assets/charts'/filename).read_text()
    print('All eight SVGs match exact regeneration from the pinned local quotes.')
print('Charts passed: annual compounding, all 2012 points per line, eight year-end values, full-period drawdown, scales and series labels.')
