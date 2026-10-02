"""Run every Module 2–4 example; check notebooks and analytical chart values."""
import importlib.util
import json
from pathlib import Path
import re
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('course_notebooks', ROOT/'scripts/make_course_notebooks.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)
module4_spec = importlib.util.spec_from_file_location('course_module4', ROOT/'qa/course-module4-checks.py')
module4 = importlib.util.module_from_spec(module4_spec)
module4_spec.loader.exec_module(module4)


def compare_stdout(actual, expected):
    """Allow last-digit floating-point differences across OS/BLAS builds."""
    pattern = r'(?<![\w.])[-+]?(?:\d[\d,]*\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'
    actual_numbers = re.findall(pattern, actual)
    expected_numbers = re.findall(pattern, expected)
    assert re.sub(pattern, '<number>', actual) == re.sub(pattern, '<number>', expected), 'Output labels/structure differ'
    assert len(actual_numbers) == len(expected_numbers)
    if actual_numbers:
        np.testing.assert_allclose([float(n.replace(',', '')) for n in actual_numbers],
                                   [float(n.replace(',', '')) for n in expected_numbers], rtol=2e-5, atol=2e-5)


def check_module3(spaces):
    """Check original lesson fixtures without reading exported notebooks."""
    diversification = spaces['diversification-limits']
    cppi = spaces['cppi-dynamic-allocation']
    mc = spaces['monte-carlo']

    # This toy market has fixed constituents/shares and no distributions.
    # Its capitalization growth must equal its lagged cap-weighted return.
    caps = diversification['end_month_cap'].to_numpy()
    asset_returns = diversification['monthly_returns'].to_numpy()
    np.testing.assert_allclose(caps[1:], caps[:-1] * (1 + asset_returns))
    beginning_weights = caps[:-1] / caps[:-1].sum(axis=1, keepdims=True)
    np.testing.assert_allclose(diversification['start_month_weights'], beginning_weights)
    cap_growth = caps[1:].sum(axis=1) / caps[:-1].sum(axis=1) - 1
    np.testing.assert_allclose(diversification['market_returns'], cap_growth)
    np.testing.assert_allclose(diversification['market_returns'],
                               [.039, 205.15 / 207.8 - 1, 209.303 / 205.15 - 1])
    np.testing.assert_allclose(np.prod(1 + diversification['market_returns']),
                               caps[-1].sum() / caps[0].sum())

    # Scalar money bookkeeping is independent of the lesson's vector operations.
    risky_fixture = [.08, -.12, .06, -.25, .10, .04]
    expected_fixed = [1000.0]
    expected_trailing = [1000.0]
    expected_floors = [800.0]
    expected_exposures = []
    peak = 1000.0
    for risky_return in risky_fixture:
        wealth = expected_fixed[-1]
        exposure = min(max(3 * (wealth - 800), 0), wealth)
        expected_exposures.append(exposure)
        expected_fixed.append(exposure * (1 + risky_return) + wealth - exposure)
        trailing_wealth = expected_trailing[-1]
        trailing_exposure = min(max(3 * (trailing_wealth - .8 * peak), 0), trailing_wealth)
        trailing_wealth += trailing_exposure * risky_return
        expected_trailing.append(trailing_wealth)
        peak = max(peak, trailing_wealth)
        expected_floors.append(.8 * peak)
    np.testing.assert_allclose(cppi['cppi_fixed']['wealth'], expected_fixed)
    np.testing.assert_allclose(cppi['cppi_fixed']['risky_before'].iloc[1:], expected_exposures)
    np.testing.assert_allclose(cppi['cppi_trailing']['wealth'], expected_trailing)
    np.testing.assert_allclose(cppi['cppi_trailing']['floor'], expected_floors)
    np.testing.assert_allclose(cppi['cppi_trailing']['floor_before'].iloc[1:], expected_floors[:-1])
    assert cppi['cppi_fixed'].index[0] == 0 and len(cppi['cppi_fixed']) == 7
    np.testing.assert_allclose(cppi['cppi_fixed']['wealth'].iloc[0], 1000)
    np.testing.assert_allclose(cppi['cppi_portfolio_returns'].iloc[0], 1048 / 1000 - 1)
    np.testing.assert_allclose(cppi['cppi_gap']['wealth'].iloc[-1], 600 * .6 + 400)
    np.testing.assert_allclose(800 - cppi['cppi_gap']['wealth'].iloc[-1], 40)
    np.testing.assert_allclose(cppi['cppi_path']([-1], multiplier=1)['wealth'].iloc[-1], 800)
    np.testing.assert_allclose(
        cppi['cppi_path']([0, 0], multiplier=0, cash_annual=.03)['wealth'],
        1000 * 1.03 ** (np.arange(3) / 12),
    )

    # Exact GBM uses price drift log(1+g): E[S_T] also follows deterministic
    # compounding of the specified expected annual growth g.
    prices = mc['mc_prices']
    returns = mc['mc_risky_returns']
    assert prices.shape == (13, 20000) and returns.shape == (12, 20000)
    np.testing.assert_allclose(prices[0], 100)
    assert np.all(prices > 0) and np.all(returns > -1)
    np.testing.assert_allclose(prices[1:] / prices[:-1] - 1, returns, atol=1e-14)
    deterministic_mean = mc['mc_start'] * (1 + mc['mc_growth']) ** mc['mc_years']
    np.testing.assert_allclose(mc['mc_theory_mean'], deterministic_mean)
    np.testing.assert_allclose(deterministic_mean, 119.1016)
    np.testing.assert_allclose(mc['mc_theory_median'], 104.0609630275036)
    assert abs(prices[-1].mean() - deterministic_mean) < 4 * mc['mc_se']

    # Compare the array allocator with scalar accounting on three paths,
    # including the capped exposure cases for each multiplier.
    for multiplier in (1, 2, 3, 4):
        allocation = mc['cppi_many_paths'](returns[:, :3], multiplier=multiplier)
        for path in range(3):
            wealth = 100.0
            assert allocation[0, path] == wealth
            for step in range(12):
                exposure = min(max(multiplier * (wealth - 80), 0), wealth)
                wealth = exposure * (1 + returns[step, path]) + (wealth - exposure) * 1.02 ** .25
                np.testing.assert_allclose(allocation[step + 1, path], wealth)
    np.testing.assert_allclose(
        mc['cppi_many_paths'](np.full((4, 3), -1.0), multiplier=1, cash_annual=0)[-1], 80,
    )
    np.testing.assert_allclose(mc['cppi_many_paths'](np.zeros((4, 3)), multiplier=0)[-1], 102)

    # Count events directly, preserving zero losses in the all-path denominator.
    wealth = mc['mc_cppi']
    losses = [max(80 - value, 0) for value in wealth[-1]]
    positive_losses = [loss for loss in losses if loss > 0]
    grid_events = sum(any(value < 80 for value in path[1:]) for path in wealth.T)
    summary = mc['mc_summary']
    assert len(positive_losses) == 156 and grid_events == 504
    assert summary['Terminal breaches'] == len(positive_losses)
    assert summary['Grid breaches'] == grid_events
    np.testing.assert_allclose(summary['Terminal breach probability'], 156 / 20000)
    np.testing.assert_allclose(summary['Grid breach probability'], 504 / 20000)
    np.testing.assert_allclose(summary['Mean shortfall across all paths'], sum(losses) / 20000)
    np.testing.assert_allclose(summary['Mean shortfall given breach'], sum(positive_losses) / 156)
    np.testing.assert_allclose(summary['Mean shortfall across all paths'],
                               summary['Terminal breach probability'] * summary['Mean shortfall given breach'])
    toy = mc['shortfall_summary'](np.array([[100, 100, 100, 100], [70, 90, 100, 140]]), 100)
    np.testing.assert_allclose(toy[['Terminal breach probability', 'Mean shortfall across all paths',
                                   'Mean shortfall given breach']], [.5, 10, 20])
    no_event = mc['shortfall_summary'](np.array([[100, 100], [80, 90]]), 80)
    assert no_event['Terminal breaches'] == no_event['Grid breaches'] == 0
    assert no_event['Mean shortfall across all paths'] == 0
    assert np.isnan(no_event['Mean shortfall given breach'])
    assert np.isnan(mc['mc_comparison_table'].loc['m=1', 'Mean shortfall given breach'])
    np.testing.assert_allclose(mc['mc_comparison_table'][['Terminal breaches', 'Grid breaches']],
                               [[0, 0], [0, 0], [156, 504], [1248, 3246]])
    return ['cap-weight timing and no-distribution identity',
            'CPPI scalar accounting and initial wealth', 'CPPI gap and trailing-floor timing',
            'CPPI m=1 floor and m=0 cash compounding', 'GBM model moments and positive prices',
            'Monte Carlo CPPI scalar paths m=1..4', 'terminal versus grid breach counts',
            'shortfall denominators and conditional NaN']


def main():
    pages = exporter.course_pages("introduction")
    assert len(pages) == 10, 'Three Module 2, three Module 3, four Module 4 chapters'
    assert [sum(p['module'] == n for p in pages) for n in (2,3,4)] == [3,3,4]
    report=[]
    spaces={}
    for page in pages:
        fresh, ns, outputs = exporter.execute_chapter(page)
        spaces[page['file']]=ns
        saved = json.loads((ROOT/page['notebook']).read_text())
        assert saved['metadata']['lesson'] == fresh['metadata']['lesson'], f'Stale notebook {page["file"]}'
        assert saved['nbformat']==4
        assert len(saved['cells']) == len(fresh['cells'])
        for a,b in zip(saved['cells'],fresh['cells']):
            assert a['cell_type']==b['cell_type'] and a['source']==b['source']
            assert a.get('attachments')==b.get('attachments'), 'Stale figure attachment'
            if a['cell_type']=='code':
                assert a['execution_count']==b['execution_count']
                assert all(o['output_type']=='stream' for o in a['outputs'])
                compare_stdout(''.join(''.join(o['text']) for o in a['outputs']),
                               ''.join(''.join(o['text']) for o in b['outputs']))
        report.append({'page':page['file'],'executed_examples':len(outputs),'notebook_consistent':True})
        print(f'PASS {page["file"]}: {len(outputs)} examples and complete notebook')

    b=spaces['portfolio-basics']; f=spaces['efficient-frontier']; e=spaces['portfolio-estimation']
    np.testing.assert_allclose(b['portfolio_return'],10400/10000-1)
    np.testing.assert_allclose(b['next_buy_hold'],(6600*.9+3800*1.05)/10400-1)
    np.testing.assert_allclose(b['sd_by_formula'],np.std(b['monthly'].to_numpy()@np.array([.6,.4]),ddof=1))
    np.testing.assert_allclose(b['min_weight_a'],.125)
    np.testing.assert_allclose(f['target_weights'],[.34375,.3125,.34375],atol=1e-6)
    msr_raw=np.linalg.solve(e['annual_cov'],e['annual_mu']-.02)
    np.testing.assert_allclose(e['msr_weights'],msr_raw/msr_raw.sum(),atol=1e-6)
    assert not set(e['train'].index)&set(e['test'].index)
    for label,initial in [('GMV',e['fitted_gmv']),('EW',np.ones(3)/3)]:
        holdings=initial.copy(); path=[]
        for row in e['test'].to_numpy():
            for i in range(3):
                holdings[i]*=1+row[i]
            path.append(sum(holdings))
        np.testing.assert_allclose(path,e['holdout_wealth'][label])

    module3_checks = check_module3(spaces)
    module4_checks = module4.check(spaces)

    # Independent closed-form references, separate from the plotting optimizer.
    chart=json.loads((ROOT/'data/course-figures.json').read_text())
    cov=np.array(chart['cov']); mu=np.array(chart['mu'])
    inv_ones=np.linalg.solve(cov,np.ones(3))
    analytical=inv_ones/inv_ones.sum()
    np.testing.assert_allclose(chart['gmv_weights'],analytical,atol=2e-7)
    front=chart['frontier']; weights=np.array(front['weights'])
    np.testing.assert_allclose(weights.sum(axis=1),1,atol=1e-8)
    assert weights.min()>=-1e-8
    np.testing.assert_allclose(weights@mu,front['target'],atol=1e-8)
    np.testing.assert_allclose(np.sqrt(np.einsum('ij,jk,ik->i',weights,cov,weights)),front['sd'],atol=1e-8)
    ten=np.argmin(np.abs(np.array(front['target'])-.10))
    np.testing.assert_allclose(weights[ten],[.34375,.3125,.34375],atol=1e-6)

    # CPPI cushion obeys C_next=C*(1+m*r) where no leverage cap binds.
    c=chart['cppi']; wealth=np.array(c['wealth']); returns=np.array(c['risky_returns'])
    np.testing.assert_allclose(wealth[1:]-800,(wealth[:-1]-800)*(1+3*returns),atol=1e-9)
    assert 1000+3*(1000-800)*(-.4)==760 # A discrete gap can cross the floor.
    d=chart['duration']; yields=np.array(d['yields'])
    short_face=d['cash_pv']/2*1.05**2; long_face=d['cash_pv']/2*1.05**8
    np.testing.assert_allclose(d['liability_pv'],100000/(1+yields)**5,rtol=1e-12)
    np.testing.assert_allclose(d['matched_pv'],short_face/(1+yields)**2+long_face/(1+yields)**8,rtol=1e-12)
    assert np.min(np.array(d['matched_pv'])/d['liability_pv'])>=1-1e-12
    assert (short_face/1.05**2+long_face/1.07**8)/d['cash_pv']<1 # Nonparallel move.
    report_data={'pages':report,'total_executed_examples':sum(p['executed_examples'] for p in report),
                 'independent_checks':['Portfolio return from money balances','buy-and-hold drift',
                                       'sample portfolio variance','analytical two-asset minimum',
                                       'unconstrained tangency portfolio','holdout timing and holdings',
                                       'GMV closed form','target 10% analytical weights','frontier constraints',
                                       *module3_checks,
                                       *module4_checks,
                                       'CPPI cushion recurrence','gap loss','PV repricing','curve twist']}
    out=ROOT/'qa/output';out.mkdir(parents=True,exist_ok=True)
    (out/'course-python-report.json').write_text(json.dumps(report_data,ensure_ascii=False,indent=2)+'\n')
    print(f'PASS {report_data["total_executed_examples"]} executed examples across {len(pages)} independent chapters; analytical chart checks')


if __name__=='__main__':
    main()
