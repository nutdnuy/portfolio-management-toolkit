"""Independent numerical checks for Advanced covariance and dynamic-risk lessons."""
import json
import itertools
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def rejects(function, *args):
    try:
        function(*args)
    except (ValueError, TypeError):
        return
    raise AssertionError(f'{function.__name__} accepted invalid inputs')


def simplex_minimum(cov):
    """Enumerate every nonempty face, solving its unconstrained GMV analytically."""
    cov = np.asarray(cov)
    candidates = []
    for count in range(1, len(cov)+1):
        for indices in itertools.combinations(range(len(cov)), count):
            face = cov[np.ix_(indices, indices)]
            direction = np.linalg.solve(face, np.ones(count))
            weights = direction/direction.sum()
            if weights.min() < -1e-10:
                continue
            candidate = np.zeros(len(cov))
            candidate[list(indices)] = weights
            candidates.append((float(candidate@cov@candidate), candidate))
    return min(candidates, key=lambda item: item[0])


def check_covariance(ns):
    checks = []
    returns = ns['R'].to_numpy()
    expected = np.array([[.0006,.002/7,0],[.002/7,.0018/7,0],[0,0,.0002/7]])
    np.testing.assert_allclose(ns['S_manual'],expected,atol=1e-16)
    np.testing.assert_allclose(ns['S_pandas'],expected,atol=1e-16)
    np.testing.assert_allclose(ns['S_numpy'],expected,atol=1e-16)
    np.testing.assert_allclose(ns['S_ddof0'],expected*7/8,atol=1e-16)
    np.testing.assert_allclose(ns['correlation'][0,1],.727392967453308,atol=1e-12)
    np.testing.assert_allclose(ns['portfolio_variance'],.0002297142857142857,atol=1e-16)
    actual_portfolio = [sum(r_i*w_i for r_i,w_i in zip(row,ns['w'])) for row in returns]
    mean = sum(actual_portfolio)/len(actual_portfolio)
    variance = sum((r-mean)**2 for r in actual_portfolio)/(len(actual_portfolio)-1)
    np.testing.assert_allclose(ns['portfolio_variance'],variance,atol=1e-16)
    checks += ['hand-derived covariance entries, ddof conversion, correlation and portfolio variance']

    assert np.linalg.matrix_rank(ns['S_wide']) == 3
    assert len(ns['wide_returns']) == 4 and ns['S_wide'].shape == (5,5)
    assert np.linalg.eigvalsh(ns['S_wide']).min() >= -1e-16
    np.testing.assert_allclose(ns['S_pairwise'].to_numpy(),
                               np.array([[4/3,2,2],[2,4/3,-2],[2,-2,4/3]])*.0001,atol=1e-16)
    np.testing.assert_allclose(np.linalg.eigvalsh(ns['S_pairwise']).min(),-8/3*.0001,atol=1e-16)
    for _,row in ns['near_table'].iterrows():
        sd = float(row['SD of B'])
        v_a, v_b, cov_ab = .2**2, sd**2, .99999*.2*sd
        w_a = (v_b-cov_ab)/(v_a+v_b-2*cov_ab)
        np.testing.assert_allclose(row['Weight A'],w_a,atol=1e-8)
        np.testing.assert_allclose(row['Weight B'],1-w_a,atol=1e-8)
        constrained = 1.0 if v_a < v_b else 0.0
        assert row['Long-only weight A'] == constrained
    checks += ['rank bound and non-PSD pairwise-missing-data example',
               'near-singular GMV verified by the two-asset scalar optimum']

    np.testing.assert_allclose(ns['B_hat'],ns['B_true'],atol=1e-14)
    np.testing.assert_allclose(ns['E_hat'],ns['E_true'],atol=1e-14)
    np.testing.assert_allclose(ns['S_factor_full'],ns['S_assets'],atol=1e-16)
    assert np.linalg.norm(ns['Psi']-ns['D_sample']) > 1e-4
    np.testing.assert_allclose(ns['D_regression'],1.4*ns['D_sample'],atol=1e-16)
    factors = ns['F']-ns['F'].mean(axis=0)
    np.testing.assert_allclose(factors.T@ns['E_hat'],0,atol=1e-16)
    weights = ns['factor_weights']
    np.testing.assert_allclose(np.var(ns['Y']@weights,ddof=1),ns['full_sd']**2,atol=1e-16)
    omitted = sum(weights[i]*weights[j]*ns['Psi'][i,j]
                  for i in range(4) for j in range(4) if i != j)
    np.testing.assert_allclose(ns['full_sd']**2-ns['diagonal_sd']**2,omitted,atol=1e-16)
    assert ns['full_sd'] > ns['diagonal_sd']
    assert np.linalg.eigvalsh(ns['S_factor_diagonal']).min() > 0
    checks += ['OLS factor decomposition reconstructs sample covariance with full residual covariance',
               'omitted residual cross terms explain risk difference; regression degrees of freedom checked']
    return checks


def check_shrinkage(ns):
    checks = []
    values = ns['shrink_toy'].to_numpy()
    centered = values-values.mean(axis=0)
    sample = centered.T@centered/(len(values)-1)
    np.testing.assert_allclose(ns['shrink_S'], sample, atol=1e-16)
    sd = np.sqrt(sample.diagonal())
    distinct = [sample[i,j]/(sd[i]*sd[j]) for i in range(3) for j in range(i+1,3)]
    rho = sum(distinct)/3
    target = np.diag(sd)@((1-rho)*np.eye(3)+rho*np.ones((3,3)))@np.diag(sd)
    np.testing.assert_allclose(ns['shrink_rho'], rho, atol=1e-14)
    np.testing.assert_allclose(ns['shrink_F'], target, atol=1e-16)
    np.testing.assert_allclose(ns['shrink_mix'], (sample+target)/2, atol=1e-16)
    for delta in (0, .1, .5, .9, 1):
        result = ns['estimate_covariance'](ns['shrink_toy'], 'shrink', delta)
        np.testing.assert_allclose(result, delta*target+(1-delta)*sample)
        np.testing.assert_allclose(result.diagonal(), sample.diagonal())
        assert np.linalg.eigvalsh(result).min() > 0
    checks += ['sample and constant-correlation target verified from centered products and distinct pairs',
               'shrinkage endpoints, convex mixture, unchanged variances and positive definiteness']

    for matrix in (sample, target, (sample+target)/2, np.diag([.01,.04,.09]),
                   np.array([[.04,.05],[.05,.09]])):
        optimum, analytic_weights = simplex_minimum(matrix)
        weights = ns['gmv_weights'](matrix)
        np.testing.assert_allclose(weights@matrix@weights, optimum, atol=1e-12, rtol=1e-8)
        np.testing.assert_allclose(ns['gmv_weights'](10000*matrix), weights, atol=1e-7)
        assert abs(weights.sum()-1) < 1e-8 and weights.min() > -1e-8
    checks += ['long-only GMV agrees with independent face enumeration, including a boundary optimum',
               'GMV allocation is invariant to a common covariance unit scaling']

    returns = ns['shrink_returns']
    window = ns['shrink_window']
    assert list(ns['shrink_backtest'].index) == list(returns.index[window:])
    assert len(ns['shrink_backtest']) == 60
    for name,weights in ns['shrink_weights'].items():
        np.testing.assert_allclose(weights.sum(axis=1), 1, atol=1e-8)
        assert weights.to_numpy().min() > -1e-8
        realized = (weights.to_numpy()*returns.iloc[window:].to_numpy()).sum(axis=1)
        np.testing.assert_allclose(realized, ns['shrink_backtest'][name], atol=1e-14)
        # Reconstruct dollar holdings and trades instead of reusing weight drift.
        holdings, wealth = None, 1000.0
        turnovers = []
        for w,r in zip(weights.to_numpy(),returns.iloc[window:].to_numpy()):
            targets = wealth*w
            turnovers.append(0.0 if holdings is None else np.abs(targets-holdings).sum()/(2*wealth))
            holdings = targets*(1+r)
            wealth = holdings.sum()
        np.testing.assert_allclose(turnovers,ns['shrink_turnover'][name],atol=1e-12)
        np.testing.assert_allclose(wealth/1000,ns['shrink_wealth'][name].iloc[-1],atol=1e-12)
        cutoff = ns['shrink_first_changed_month']
        np.testing.assert_allclose(weights.loc[:cutoff], ns['changed_weights'][name].loc[:cutoff], atol=1e-8)
    methods = {'Sample GMV':'sample','CC GMV':'constant-correlation','Shrink 0.5':'shrink'}
    for row in (0,59):
        history = returns.iloc[row:row+window]
        for label,method in methods.items():
            cov = ns['estimate_covariance'](history,method)
            optimum,_ = simplex_minimum(cov)
            actual = ns['shrink_weights'][label].iloc[row].to_numpy()
            np.testing.assert_allclose(actual@cov@actual,optimum,atol=1e-12,rtol=1e-8)
    np.testing.assert_allclose(ns['changed_backtest'].loc[ns['shrink_first_changed_month']]
                               -ns['shrink_backtest'].loc[ns['shrink_first_changed_month']], .1, atol=1e-12)
    checks += ['all 60 held returns and turnover values match an independent dollar-holdings ledger',
               'first and last rolling optima verified analytically across all feasible faces',
               'strictly past-only weights and same-month realized-return response']

    for bad_delta in (-.1,1.1,np.nan,np.inf):
        rejects(ns['estimate_covariance'],ns['shrink_toy'],'shrink',bad_delta)
    incomplete = ns['shrink_toy'].copy()
    incomplete.iloc[0,0] = np.nan
    rejects(ns['estimate_covariance'],incomplete)
    constant = ns['shrink_toy'].copy()
    constant['A'] = 1.0
    rejects(ns['estimate_covariance'],constant)
    rejects(ns['gmv_weights'],np.array([[1,2],[2,1]]))
    rejects(ns['rolling_gmv'],returns.iloc[::-1])
    checks += ['covariance helpers reject missing data, zero variance, invalid delta and non-PSD input']
    return checks


def check_dynamic_risk(ns):
    checks = []
    eps = np.asarray(ns['residuals'])
    lam, h0 = ns['lam'], ns['initial_variance']
    expected = [lam**k * h0 + (1-lam) * np.dot(lam**np.arange(k)[::-1], eps[:k]**2)
                for k in range(len(eps)+1)]
    np.testing.assert_allclose(ns['ewma_h'], expected, atol=1e-16, rtol=1e-12)
    np.testing.assert_allclose(ns['rolling_after'].iloc[[5, 9, 10]], [.00058, .00058, .0001])
    np.testing.assert_allclose(ns['ewma_h'][6], .00034, atol=1e-16)
    np.testing.assert_allclose(ns['half_lives'], np.log(.5)/np.log(ns['lambda_choices']))
    np.testing.assert_allclose(ns['raw_weights'].sum()+ns['initial_weight'], 1)
    assert not np.isclose(ns['finite_variance'], ns['recursive_expansion'], atol=1e-8)
    np.testing.assert_allclose(ns['initialization_gap'], ns['expected_gap'], atol=1e-16)
    checks += ['EWMA matches a closed-form weighted sum at every date',
               'rolling-window shock expiry, EWMA half-life and initialization weights']

    omega, alpha, beta = ns['omega'], ns['alpha'], ns['beta']
    expected_garch = [beta**k*h0 + omega*np.sum(beta**np.arange(k))
                      + alpha*np.dot(beta**np.arange(k)[::-1], eps[:k]**2)
                      for k in range(len(eps)+1)]
    np.testing.assert_allclose(ns['garch_h'], expected_garch, atol=1e-16, rtol=1e-12)
    np.testing.assert_allclose(ns['garch_h'][6], .000292, atol=1e-16)
    np.testing.assert_allclose(ns['long_run_variance'], .0001, atol=1e-16)
    np.testing.assert_allclose(ns['arch_h'][1:], .00008 + .20*eps**2, atol=1e-16)
    expected_forecast = [ns['garch_h'][6]]
    for _ in range(59):
        expected_forecast.append(omega+(alpha+beta)*expected_forecast[-1])
    np.testing.assert_allclose(ns['garch_forecast_path'], expected_forecast, atol=1e-16)
    np.testing.assert_allclose(ns['ewma_forecast_path'], np.full(60, .00034), atol=1e-16)
    np.testing.assert_allclose(ns['aggregate_variance'], sum(expected_forecast[:20]))
    assert ns['aggregate_sd'] < ns['constant_today_sd']
    checks += ['GARCH filter matches independent finite-sum solution; ARCH nests correctly',
               'fixed-origin forecasts, long-run variance and additive-horizon variance']

    initial = ns['sigma_initial']
    shocks = ns['two_asset_shocks']
    for k, actual in enumerate(ns['covariance_states']):
        expected_cov = lam**k*initial + sum(
            ((1-lam)*lam**(k-1-j)*np.outer(shocks[j], shocks[j]) for j in range(k)),
            np.zeros_like(initial))
        np.testing.assert_allclose(actual, expected_cov, atol=1e-16)
        assert np.linalg.eigvalsh(actual).min() > 0
        weights = ns['portfolio_weights']
        scalar = lam**k*(weights@initial@weights) + sum(
            (1-lam)*lam**(k-1-j)*float(weights@shocks[j])**2 for j in range(k))
        np.testing.assert_allclose(weights@actual@weights, scalar, atol=1e-16)
    np.testing.assert_allclose(ns['standardized_eps'], ns['innovations'][ns['burn_in']:], atol=1e-14)
    np.testing.assert_allclose(ns['percent_scale'], ns['garch_h']*10000, atol=1e-12)
    np.testing.assert_allclose(ns['changed_ewma'][:11], ns['ewma_h'][:11])
    np.testing.assert_allclose(ns['changed_garch'][:11], ns['garch_h'][:11])
    assert not np.allclose(ns['changed_garch'][11:], ns['garch_h'][11:])
    b = ns['factor_loadings'].T @ ns['factor_portfolio_weights']
    scalar_factor_var = (b**2)@ns['factor_variance_after'] + (ns['factor_portfolio_weights']**2)@ns['specific_variances']
    np.testing.assert_allclose(ns['factor_portfolio_weights']@ns['factor_covariance_after']@ns['factor_portfolio_weights'], scalar_factor_var)
    checks += ['EWMA matrix covariance matches weighted outer products and portfolio variance',
               'GARCH simulation time indices, percentage units and future-data isolation',
               'factor-GARCH portfolio variance matches scalar factor and specific components']

    for invalid in [np.nan, np.inf, -1.0, 0.0]:
        rejects(ns['ewma_variance'], eps, lam, invalid)
        rejects(ns['garch_variance'], eps, omega, alpha, beta, invalid)
    for invalid in [0, 1, -.1, np.nan, np.inf]:
        rejects(ns['ewma_variance'], eps, invalid, h0)
    rejects(ns['garch_variance'], eps, omega, .2, .8, h0)
    rejects(ns['garch_variance'], eps, omega, -.1, .8, h0)
    rejects(ns['garch_variance'], eps, np.nan, alpha, beta, h0)
    rejects(ns['garch_forecast'], .0002, omega, alpha, beta, 0)
    checks += ['dynamic-risk helpers reject nonfinite, nonpositive and unstable parameters']
    return checks


def check_charts(ns):
    metadata = json.loads((ROOT/'data/advanced-covariance-figures.json').read_text())
    np.testing.assert_array_equal(metadata['window']['observed_day'], np.arange(5,19))
    np.testing.assert_array_equal(metadata['forecast']['horizon'], np.arange(1,61))
    datasets = {
        'advanced-risk-window': (
            metadata['window']['observed_day'],
            [(metadata['window']['rolling_next_day_sd_percent'], np.sqrt(ns['rolling_after'].iloc[4:])*100),
             (metadata['window']['ewma_next_day_sd_percent'], np.sqrt(ns['ewma_h'][5:])*100)],
            (5,18), (.8,2.6)),
        'advanced-risk-forecast': (
            metadata['forecast']['horizon'],
            [(metadata['forecast']['garch_sd_percent'], np.sqrt(ns['garch_forecast_path'])*100),
             (metadata['forecast']['ewma_sd_percent'], np.sqrt(ns['ewma_forecast_path'])*100),
             (metadata['forecast']['long_run_sd_percent'], np.full(60,np.sqrt(ns['long_run_variance'])*100))],
            (1,60), (.8,2)),
    }
    for name, (xs, series, xlim, ylim) in datasets.items():
        for width,suffix in ((720,''),(400,'-mobile')):
            height = 560 if width == 720 else 540
            root = ET.parse(ROOT/f'assets/charts/{name}{suffix}.svg').getroot()
            lines = root.findall('{http://www.w3.org/2000/svg}polyline')
            assert len(lines) == len(series)
            for line,(ys, expected) in zip(lines,series):
                np.testing.assert_allclose(ys,expected,atol=1e-12)
                coords = np.array([[float(v) for v in xy.split(',')] for xy in line.attrib['points'].split()])
                actual = np.column_stack([60+(np.asarray(xs)-xlim[0])/(xlim[1]-xlim[0])*(width-84),
                                          height-88-(np.asarray(ys)-ylim[0])/(ylim[1]-ylim[0])*(height-273)])
                np.testing.assert_allclose(coords, actual, atol=5.1e-5, rtol=0)
    return ['all dynamic-risk chart metadata and both SVG sizes match executed lesson values']


def check_lessons(spaces):
    return [*check_covariance(spaces['covariance-estimation']),
            *check_shrinkage(spaces['covariance-shrinkage']),
            *check_dynamic_risk(spaces['time-varying-risk']), *check_charts(spaces['time-varying-risk'])]
