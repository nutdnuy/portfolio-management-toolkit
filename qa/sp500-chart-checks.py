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
assert metadata['observations']==2012 and len(metadata['files'])==16
start,end=map(dt.date.fromisoformat,metadata['period'])
# Recovery returns to zero; crossing a year boundary must retain the old peak.
probe=[('2018-01-01',100),('2018-12-31',120),('2019-01-02',90),('2019-12-31',120),('2020-01-02',150)]
assert [v for _,v in charts.drawdown_path(probe)]==[0,0,-25,0,0]
for path in charts.chain_years(example).values():
    assert math.isclose(charts.drawdown_path(path)[3][1],-10)

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
        if info['kind']=='drawdown':
            assert box['ymin']==-40 and box['ymax']==0
            values=[-40*(yy-box['top'])/(box['bottom']-box['top']) for _,yy in points]
            assert all(-40<=v<=0 for v in values) and values[0]==0
            assert abs(-min(values)-metadata['metrics'][method]['max_drawdown_pct'])<.001
            # Independently recover wealth from the published companion SVG, then
            # derive its running peak; this checks all dates, not just the trough.
            wealth_file=filename.replace('-drawdown','')
            wealth_root=ET.fromstring((ROOT/'assets/charts'/wealth_file).read_bytes())
            companion=next(el for el in wealth_root.findall('s:polyline',ns) if el.attrib['data-series']==method)
            wealth_points=[tuple(map(float,p.split(','))) for p in companion.attrib['points'].split()]
            assert xx==[x for x,_ in wealth_points]
            wealth=[300*(box['bottom']-y)/(box['bottom']-box['top']) for _,y in wealth_points]
            peak=wealth[0]
            for v,d in zip(wealth,values):
                peak=max(peak,v)
                assert abs(d-100*(v/peak-1))<.004
            continue
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
        assert charts.render(paths,info['method'],info['mobile'],info['kind'])==(ROOT/'assets/charts'/filename).read_text()
    print('All 16 SVGs match exact regeneration from the pinned local quotes.')
print('Charts passed: annual compounding, all 2012 points per line, eight year-end values, full-period drawdown, every drawdown point against wealth, scales and series labels.')
