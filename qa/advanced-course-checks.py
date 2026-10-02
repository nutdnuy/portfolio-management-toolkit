"""Execute Advanced lessons and verify notebooks and independent finance identities."""
import difflib
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


exporter = load_module('advanced_course_notebooks', ROOT / 'scripts/make_course_notebooks.py')
intro_checks = load_module('introduction_course_checks', ROOT / 'qa/course-checks.py')


def normalize_stdout_alignment(text):
    """Ignore horizontal table padding, preserving every line and token."""
    return '\n'.join(re.sub(r'[ \t]+', ' ', line).strip(' \t') for line in text.split('\n'))


def compare_stdout(actual, expected):
    # A rounded -0.0 versus +0.0 can shift pandas column padding across BLAS
    # builds. Keep the shared numeric count/tolerances and label checks intact.
    intro_checks.compare_stdout(normalize_stdout_alignment(actual),
                                normalize_stdout_alignment(expected))


def check_notebook(page, fresh):
    """Pin all lesson content, executed cells and embedded figures to the source."""
    saved = json.loads((ROOT / page['notebook']).read_text())
    source = ROOT / 'content' / (page['file'] + '.md')
    assert all(ord(char) >= 32 or char in '\n\t\r' for char in source.read_text()), \
        f'Unexpected control character in lesson: {page["file"]}'
    lesson = saved['metadata']['lesson']
    assert lesson == fresh['metadata']['lesson'], f'Stale notebook: {page["file"]}'
    assert lesson['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert lesson['source'] == str(source.relative_to(ROOT))
    assert saved['nbformat'] == fresh['nbformat'] == 4
    assert saved['nbformat_minor'] == fresh['nbformat_minor']
    assert len(saved['cells']) == len(fresh['cells']), f'Cell count: {page["file"]}'
    code_count = 0
    for index, (actual, expected) in enumerate(zip(saved['cells'], fresh['cells'])):
        label = f'{page["file"]}: cell {index + 1}'
        for key in ('cell_type', 'id', 'source'):
            assert actual[key] == expected[key], f'{label}: {key}'
        assert actual.get('attachments') == expected.get('attachments'), f'{label}: figure attachment'
        if actual['cell_type'] == 'code':
            code_count += 1
            assert actual['execution_count'] == expected['execution_count'] == code_count, label
            assert all(output['output_type'] == 'stream' and output['name'] == 'stdout'
                       for output in actual['outputs']), f'{label}: unexpected output type'
            actual_stdout = ''.join(''.join(output['text']) for output in actual['outputs'])
            expected_stdout = ''.join(''.join(output['text']) for output in expected['outputs'])
            try:
                compare_stdout(actual_stdout, expected_stdout)
            except AssertionError as error:
                difference = difflib.unified_diff(
                    normalize_stdout_alignment(actual_stdout).splitlines(),
                    normalize_stdout_alignment(expected_stdout).splitlines(),
                    fromfile='saved stdout', tofile='fresh stdout', n=1, lineterm='')
                excerpt = '\n'.join(itertools.islice(difference, 10))[:1000]
                raise AssertionError(f'{label}: stale stdout\n{excerpt}') from error
    return code_count


def simplex_reference(x, y, center=True):
    """Solve a small long-only regression by enumerating every simplex face.

    Eliminate the sum-to-one constraint on each face, solve its normal equations,
    and retain feasible solutions. This does not call the chapter's optimizer.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x_mean = x.mean(axis=0) if center else np.zeros(x.shape[1])
    y_mean = y.mean() if center else 0.0
    centered_x, centered_y = x - x_mean, y - y_mean
    candidates = []
    for size in range(1, x.shape[1] + 1):
        for active in itertools.combinations(range(x.shape[1]), size):
            weights = np.zeros(x.shape[1])
            baseline = active[-1]
            if size > 1:
                differences = centered_x[:, active[:-1]] - centered_x[:, [baseline]]
                response = centered_y - centered_x[:, baseline]
                free_weights = np.linalg.solve(differences.T @ differences, differences.T @ response)
                weights[list(active[:-1])] = free_weights
            weights[baseline] = 1 - weights.sum()
            if weights.min() >= -1e-12:
                alpha = y_mean - x_mean @ weights
                residual = y - alpha - x @ weights
                candidates.append((residual @ residual, weights, alpha))
    assert candidates, 'The simplex vertices must always be feasible'
    _, weights, alpha = min(candidates, key=lambda candidate: candidate[0])
    return weights, alpha


def check_factor(namespace):
    x, y = namespace['x'], namespace['y']
    np.testing.assert_allclose(x, np.arange(12) / 100 - .05)
    np.testing.assert_allclose(namespace['returns']['RF'], .002)
    np.testing.assert_allclose(y, namespace['returns']['Fund'] - namespace['returns']['RF'])
    np.testing.assert_allclose(x, namespace['returns']['Market'] - namespace['returns']['RF'])
    expected_residual = np.tile([1, -1, -1, 1], 3) * .004
    np.testing.assert_allclose(y, .001 + 1.2 * x + expected_residual)
    np.testing.assert_allclose([namespace['alpha'], namespace['beta']], [.001, 1.2])
    np.testing.assert_allclose(namespace['residual'], expected_residual, atol=1e-15)
    np.testing.assert_allclose(namespace['fitted'], .001 + 1.2 * x, atol=1e-15)
    x_mean, y_mean = sum(x) / len(x), sum(y) / len(y)
    x_squares = sum((value - x_mean) ** 2 for value in x)
    covariance_numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
    independent_beta = covariance_numerator / x_squares
    np.testing.assert_allclose(namespace['beta_cov'], independent_beta)
    np.testing.assert_allclose(namespace['beta_rho'], independent_beta)
    np.testing.assert_allclose(namespace['sse'], 12 * .004 ** 2)
    independent_tss = 1.2 ** 2 * x_squares + 12 * .004 ** 2
    np.testing.assert_allclose(namespace['tss'], independent_tss)
    np.testing.assert_allclose(namespace['r_squared'], 1 - 12 * .004 ** 2 / independent_tss)
    np.testing.assert_allclose(sum(namespace['residual']), 0, atol=1e-14)
    np.testing.assert_allclose(sum(a * e for a, e in zip(x, namespace['residual'])), 0, atol=1e-14)

    # Estimate error variance with n-2 degrees of freedom, then propagate it
    # separately to the intercept and slope instead of calling linregress again.
    error_variance = 12 * .004 ** 2 / 10
    se_beta = np.sqrt(error_variance / x_squares)
    se_alpha = np.sqrt(error_variance * (1 / 12 + x_mean ** 2 / x_squares))
    np.testing.assert_allclose(namespace['fit'].stderr, se_beta)
    np.testing.assert_allclose(namespace['fit'].intercept_stderr, se_alpha)
    assert namespace['degrees_freedom'] == 10
    np.testing.assert_allclose(namespace['critical'], 2.2281388519649385)
    np.testing.assert_allclose(namespace['alpha_interval'],
                               .001 + np.array([-1, 1]) * 2.2281388519649385 * se_alpha)
    assert namespace['alpha_interval'][0] < 0 < namespace['alpha_interval'][1]

    risk = namespace['risk_comparison']
    np.testing.assert_allclose(risk['Beta'], [1.2, 1.2, 0], atol=1e-14)
    residual_variance = 12 * .004 ** 2 / 11
    np.testing.assert_allclose(risk['Monthly SD'] ** 2,
                               [(1.2 ** 2 * x_squares / 11 + residual_variance),
                                (1.2 ** 2 * x_squares / 11 + 9 * residual_variance),
                                4 * residual_variance])
    np.testing.assert_allclose(namespace['capm_expected'], [.055, .08, .09, .015])
    np.testing.assert_allclose(namespace['portfolio_beta'], .6 * 1.2 + .4 * .5)
    np.testing.assert_allclose(namespace['portfolio_excess'],
                               .0008 + .92 * x + .4 * expected_residual, atol=1e-15)
    np.testing.assert_allclose(namespace['fit_percent'].slope, 1.2)
    np.testing.assert_allclose(namespace['fit_percent'].intercept, .1)
    return ['monthly excess returns and planted alpha/beta',
            'OLS covariance identity and orthogonal residuals',
            'explained variance, residual variance and R-squared',
            'OLS standard errors and intercept interval with n-2 degrees of freedom',
            'equal beta versus unequal total risk and zero-beta residual risk',
            'annual CAPM scenario and constant-weight portfolio beta',
            'percentage-unit scaling preserves beta and rescales alpha']


def check_multifactor(namespace):
    factors = namespace['F']
    design = namespace['X']
    y = namespace['y_multi']
    coef = namespace['coef']
    np.testing.assert_allclose(namespace['smb_example'], ((.018 + .010 + .006) - (.012 + .008 + .002)) / 3)
    np.testing.assert_allclose(namespace['hml_example'], ((.018 + .012) - (.006 + .002)) / 2)
    np.testing.assert_allclose(namespace['comparison']['Expected return'], .07)
    np.testing.assert_allclose(namespace['asset_sds'] ** 2, (.8 * .16) ** 2 + np.array([0, .05, .15]) ** 2)
    assert factors.shape == (16, 3)
    assert list(factors.columns) == ['Mkt-RF', 'SMB', 'HML']
    assert design.shape == (len(factors), 4)
    np.testing.assert_allclose(design[:, 0], 1)
    np.testing.assert_allclose(design[:, 1:], factors)
    np.testing.assert_allclose(coef, [0, 1.1, .8, -.4], atol=1e-12)
    residual = np.asarray(y) - np.asarray(design) @ coef
    np.testing.assert_allclose(residual, np.repeat([-1, 1], 8) * .002, atol=1e-14)
    np.testing.assert_allclose(namespace['residual_multi'], residual, atol=1e-14)
    np.testing.assert_allclose(np.asarray(design).T @ residual, 0, atol=1e-12)

    # Regress each omitted factor on the market using scalar centered sums.
    # Their intercepts enter the one-factor alpha; their slopes enter its beta.
    market = factors['Mkt-RF'].to_numpy()
    market_mean = sum(market) / len(market)
    market_ss = sum((value - market_mean) ** 2 for value in market)
    expected_one_factor = np.array([coef[0], coef[1]], dtype=float)
    for index, name in enumerate(('SMB', 'HML'), 2):
        factor = factors[name].to_numpy()
        factor_mean = sum(factor) / len(factor)
        projection_beta = sum((a - market_mean) * (b - factor_mean)
                              for a, b in zip(market, factor)) / market_ss
        projection_alpha = factor_mean - projection_beta * market_mean
        expected_one_factor += coef[index] * np.array([projection_alpha, projection_beta])
    np.testing.assert_allclose(namespace['one_factor_coef'], expected_one_factor, atol=1e-12)
    np.testing.assert_allclose(namespace['one_factor_coef'], [.00312, 1.42], atol=1e-12)
    np.testing.assert_allclose([namespace['alpha_from_omission'], namespace['beta_from_omission']],
                               expected_one_factor, atol=1e-12)

    # Frisch-Waugh-Lovell removes the other columns first. It independently
    # recovers each partial loading from a one-variable covariance ratio.
    for column in range(1, 4):
        controls = np.delete(np.asarray(design), column, axis=1)
        factor = np.asarray(design)[:, column]
        control_gram = controls.T @ controls
        partial_x = factor - controls @ np.linalg.solve(control_gram, controls.T @ factor)
        partial_y = y - controls @ np.linalg.solve(control_gram, controls.T @ y)
        partial_loading = sum(partial_x * partial_y) / sum(partial_x ** 2)
        np.testing.assert_allclose(coef[column], partial_loading, atol=1e-12)
    capm_residual = np.asarray(y) - expected_one_factor[0] - expected_one_factor[1] * market
    assert sum(residual ** 2) < sum(capm_residual ** 2)
    total_squares = sum((value - sum(y) / len(y)) ** 2 for value in y)
    np.testing.assert_allclose(namespace['r2_market'], 1 - sum(capm_residual ** 2) / total_squares)
    np.testing.assert_allclose(namespace['r2_multi'], 1 - sum(residual ** 2) / total_squares)
    np.testing.assert_allclose(namespace['first_breakdown'].sum(), -.0299)
    np.testing.assert_allclose(namespace['first_breakdown'].sum(), namespace['rf_multi'] + y[0])

    # The authored signs are mutually orthogonal. Combine their loadings first
    # to calculate variance without reusing the covariance matrix expression.
    factor_variance = 16 / 15 * ((.025 * (1.1 + .8 * .3 + (-.4) * (-.2))) ** 2
                                + (.8 * .010) ** 2 + (-.4 * .012) ** 2)
    np.testing.assert_allclose(namespace['factor_variance'], factor_variance)
    np.testing.assert_allclose(namespace['residual_variance'], 16 / 15 * .002 ** 2)
    np.testing.assert_allclose(namespace['total_variance'], factor_variance + 16 / 15 * .002 ** 2)
    assert namespace['diagonal_only'] < factor_variance
    np.testing.assert_allclose(namespace['coef_percent_smb'], [0, 1.1, .008, -.4], atol=1e-12)
    assert namespace['rank_duplicate'] == 4 and namespace['X_duplicate'].shape == (16, 5)
    duplicate = namespace['coef_duplicate']
    np.testing.assert_allclose(duplicate[2] + 2 * duplicate[4], .8, atol=1e-12)
    np.testing.assert_allclose(namespace['X_duplicate'] @ duplicate, design @ coef, atol=1e-12)
    np.testing.assert_allclose(namespace['train_coef'], [-.00085, 1.1 - 1 / 60, .8, -.4 - 1 / 12], atol=1e-12)
    np.testing.assert_allclose(namespace['heldout_errors'], .004, atol=1e-12)
    np.testing.assert_allclose(namespace['heldout_rmse'], .004)
    np.testing.assert_allclose([namespace['expected_excess'], namespace['expected_total']], [.0056, .0076])
    return ['six-portfolio SMB and HML spread arithmetic',
            'SML equal-beta returns versus residual-risk SD',
            'multifactor intercept, factor order and planted exposures',
            'multifactor residual normal equations',
            'omitted factor projections explain CAPM alpha and beta',
            'partial factor loadings from independent residualization',
            'nested regression fit and total-return attribution',
            'correlated factor variance from orthogonal authored shocks',
            'factor-unit rescaling and duplicated-column identification',
            'held-out conditional errors and assumed-premium scenario']


def check_style(namespace):
    """Identify known mixtures and check the constrained fit on every face."""
    x, y = namespace['style_X'], namespace['style_y']
    fit = namespace['style_fit']
    assert x.shape == (32, 3) and y.shape == (32,)
    assert x.index.equals(y.index) and x.index.is_unique
    train_x, train_y = x.iloc[:16], y.iloc[:16]
    test_x, test_y = x.iloc[16:], y.iloc[16:]
    assert not set(train_x.index) & set(test_x.index)
    weights, alpha = fit(train_x, train_y)
    reference_weights, reference_alpha = simplex_reference(train_x, train_y)
    np.testing.assert_allclose(weights, [.5, .3, .2], atol=2e-5)
    np.testing.assert_allclose(weights, reference_weights, atol=2e-5)
    np.testing.assert_allclose(namespace['style_w'], reference_weights, atol=2e-5)
    np.testing.assert_allclose(alpha, reference_alpha, atol=1e-7)
    np.testing.assert_allclose(alpha, .001, atol=1e-7)
    train_residual = train_y.to_numpy() - float(alpha) - train_x.to_numpy() @ weights
    np.testing.assert_allclose(namespace['style_train_error'], train_residual, atol=1e-12)
    np.testing.assert_allclose(train_residual.mean(), 0, atol=1e-12)
    np.testing.assert_allclose(train_x.to_numpy().T @ train_residual, 0, atol=1e-7)

    # Re-estimating the later sample must reveal the deliberately changed mix.
    later_weights, _ = fit(test_x, test_y)
    np.testing.assert_allclose(later_weights, [.2, .6, .2], atol=2e-5)
    fixed_residual = test_y.to_numpy() - float(alpha) - test_x.to_numpy() @ weights
    np.testing.assert_allclose(namespace['style_test_error'], fixed_residual, atol=1e-12)
    np.testing.assert_allclose(np.mean(fixed_residual ** 2),
                               (.3 * .025) ** 2 + (.3 * .030) ** 2 + .002 ** 2 + .0003 ** 2,
                               atol=1e-10)
    refit_weights, refit_alpha = simplex_reference(test_x, test_y)
    refit_residual = test_y.to_numpy() - refit_alpha - test_x.to_numpy() @ refit_weights
    assert np.mean(fixed_residual ** 2) > np.mean(refit_residual ** 2)

    # Mean shifts should change the intercept, never a centered style estimate.
    shifted_weights, shifted_alpha = fit(train_x, train_y + .002)
    np.testing.assert_allclose(shifted_weights, weights, atol=2e-5)
    np.testing.assert_allclose(shifted_alpha - alpha, .002, atol=1e-7)

    # An unconstrained negative exposure forces the long-only solution onto a
    # boundary. Enumerating faces independently checks that boundary is optimal.
    outside_y = 1.5 * train_x.iloc[:, 0] - .5 * train_x.iloc[:, 1] + .001
    for response, centered in ((train_y, False), (outside_y, True)):
        actual_weights, actual_alpha = fit(train_x, response, center=centered)
        expected_weights, expected_alpha = simplex_reference(train_x, response, center=centered)
        actual_weights = np.asarray(actual_weights)
        np.testing.assert_allclose(actual_weights.sum(), 1, atol=1e-8)
        assert actual_weights.min() >= -1e-8
        actual_error = response.to_numpy() - actual_alpha - train_x.to_numpy() @ actual_weights
        expected_error = response.to_numpy() - expected_alpha - train_x.to_numpy() @ expected_weights
        np.testing.assert_allclose(actual_error @ actual_error,
                                   expected_error @ expected_error, atol=1e-10, rtol=1e-6)
        if centered:
            assert actual_weights.min() < 1e-6
        else:
            assert actual_alpha == 0
            np.testing.assert_allclose(namespace['style_raw_w'], expected_weights, atol=2e-5)

    # Sample TE removes the mean active return; RMSE retains it. Their squared
    # identity includes the n/(n-1) distinction for the sample denominator.
    active = train_y.to_numpy() - train_x.to_numpy() @ weights
    mean_active = sum(active) / len(active)
    centered_squares = sum((value - mean_active) ** 2 for value in active)
    sample_te = np.sqrt(centered_squares / (len(active) - 1))
    rmse = np.sqrt(sum(value ** 2 for value in active) / len(active))
    np.testing.assert_allclose(namespace['style_active'], active, atol=1e-12)
    np.testing.assert_allclose(namespace['style_te'], sample_te)
    np.testing.assert_allclose(namespace['style_rmse'], rmse)
    np.testing.assert_allclose(rmse ** 2,
                               (len(active) - 1) / len(active) * sample_te ** 2 + mean_active ** 2)
    total_squares = sum((value - sum(train_y) / len(train_y)) ** 2 for value in train_y)
    np.testing.assert_allclose(namespace['style_r2_var'], 1 - centered_squares / total_squares)
    np.testing.assert_allclose(namespace['style_r2_zero'], 1 - sum(active ** 2) / total_squares)
    for end in range(16, len(x) + 1):
        window_x, window_y = x.iloc[end - 16:end], y.iloc[end - 16:end]
        reference_weights, reference_alpha = simplex_reference(window_x, window_y)
        np.testing.assert_allclose(namespace['style_rolling'].iloc[end - 16], reference_weights, atol=2e-5)
        if end < len(x):
            row = namespace['style_next'].iloc[end - 16]
            assert row['Estimated through'] == x.index[end - 1]
            assert namespace['style_next'].index[end - 16] == x.index[end]
            np.testing.assert_allclose(row['Explained return'],
                                       x.iloc[end] @ reference_weights + reference_alpha, atol=1e-7)
    return ['style known training mixture and mean extra return',
            'style simplex optimum by independent face enumeration',
            'style holdout timing and changed exposures',
            'centered style invariance to constant active return',
            'style long-only boundary and uncentered objective',
            'sample tracking error versus RMSE identity',
            'variance versus zero-intercept goodness of fit',
            'rolling style windows and next-period explanation timing']


def fee_reference(holdings, target, rate):
    """Find post-fee wealth by solving each possible trade-sign linear equation."""
    holdings, target = np.asarray(holdings), np.asarray(target)
    before = sum(holdings)
    for signs in itertools.product((-1, 1), repeat=len(holdings)):
        signs = np.asarray(signs)
        after = (before + rate * sum(signs * holdings)) / (1 + rate * sum(signs * target))
        trades = after * target - holdings
        if 0 <= after <= before + 1e-12 and np.all(signs * trades >= -1e-12):
            return after, before - after
    raise AssertionError('No self-financing post-fee solution found')


def check_smart_beta(namespace):
    stocks = namespace['stocks']
    caps = stocks['Price'].to_numpy() * stocks['Shares_million'].to_numpy()
    np.testing.assert_allclose(caps, [500, 250, 150, 100])
    np.testing.assert_allclose(namespace['cw'], caps / sum(caps))
    np.testing.assert_allclose(namespace['ew'], [.25] * 4)
    for label, key in (('CW', 'cw'), ('EW', 'ew')):
        hhi = sum(weight ** 2 for weight in namespace[key])
        np.testing.assert_allclose(namespace['concentration'].loc[label], [hhi, 1 / hhi])
    np.testing.assert_allclose(namespace['risk_share'], np.array([1, 4, 9, 16]) / 30)

    # Cash accounting with fixed shares and no distributions reproduces both
    # capitalization growth and the changed composition of a buy-and-hold fund.
    returns = namespace['one_period_r'].to_numpy()
    later_caps = caps * (1 + returns)
    np.testing.assert_allclose(namespace['cw_return'], sum(later_caps) / sum(caps) - 1)
    np.testing.assert_allclose(namespace['cw_drift'], later_caps / sum(later_caps))
    holdings = 25000 * (1 + returns)
    np.testing.assert_allclose(namespace['ew_drift'], holdings / sum(holdings))
    np.testing.assert_allclose(namespace['ew_return'], sum(holdings) / 100000 - 1)
    after, fee = fee_reference(holdings, np.ones(4) / 4, .001)
    np.testing.assert_allclose([after, fee], [104990, 10])
    np.testing.assert_allclose(namespace['rebalanced_holdings'], np.full(4, after / 4))
    np.testing.assert_allclose(namespace['rebalance_fee'], fee)
    np.testing.assert_allclose(sum(namespace['rebalanced_holdings']) + namespace['rebalance_fee'], sum(holdings))
    np.testing.assert_allclose(after / 100000 - 1, .0499)
    for target in (np.ones(4) / 4, np.array([0., 0., 0., 1.])):
        expected_after, expected_fee = fee_reference(holdings, target, .002)
        actual_holdings, actual_fee = namespace['rebalance_with_fee'](holdings, target, .002)
        np.testing.assert_allclose(actual_holdings, target * expected_after)
        np.testing.assert_allclose(actual_fee, expected_fee, atol=1e-10)

    # Binding limits identify the least-squares projection directly: C reaches
    # .225, B reaches .375, and A receives the remaining .4.
    np.testing.assert_allclose(namespace['upper'], [.75, .375, .225, 0])
    np.testing.assert_allclose(namespace['capped_weights'], [.4, .375, .225, 0], atol=1e-8)
    assert namespace['naive_renormalized'][2] > namespace['upper'][2]

    simulated = namespace['sim_returns']
    known_caps = namespace['cap_before']
    assert simulated.shape == known_caps.shape == (72, 4)
    assert simulated.index.equals(known_caps.index)
    cap_states = [caps.copy()]
    for row in simulated.to_numpy():
        cap_states.append(cap_states[-1] * (1 + row))
    np.testing.assert_allclose(known_caps, cap_states[:-1])

    # This independent scalar ledger chooses weights solely from the preceding
    # 60 rows and applies fees before the held month's asset returns.
    for rule, path in namespace['paths'].items():
        scalar_holdings = None
        expected_returns, expected_fees, expected_turnovers = [], [], []
        expected_wealth = [1.0]
        for t in range(60, len(simulated)):
            history = simulated.iloc[t - 60:t].to_numpy()
            if rule == 'CW':
                target = np.asarray(cap_states[t]) / sum(cap_states[t])
            elif rule == 'EW':
                target = np.ones(4) / 4
            else:
                assert rule == 'LowVol-EW'
                means = [sum(history[:, j]) / 60 for j in range(4)]
                variances = [sum((value - means[j]) ** 2 for value in history[:, j]) / 59
                             for j in range(4)]
                chosen = sorted(range(4), key=lambda j: variances[j])[:2]
                target = np.array([.5 if j in chosen else 0 for j in range(4)])
            np.testing.assert_allclose(namespace['target_paths'][rule].iloc[t - 60], target)
            if scalar_holdings is None:
                scalar_holdings = list(target)
            before = sum(scalar_holdings)
            turnover = sum(abs(target[j] - scalar_holdings[j] / before) for j in range(4)) / 2
            after_fee, fee = fee_reference(scalar_holdings, target, .001)
            scalar_holdings = [after_fee * target[j] * (1 + simulated.iloc[t, j]) for j in range(4)]
            expected_returns.append(sum(scalar_holdings) / before - 1)
            expected_wealth.append(sum(scalar_holdings))
            expected_fees.append(fee)
            expected_turnovers.append(turnover)
        np.testing.assert_allclose(path['Wealth'], expected_wealth[1:])
        np.testing.assert_allclose(path['Net return'], expected_returns, atol=1e-14)
        np.testing.assert_allclose(path['Fee'], expected_fees, atol=1e-14)
        np.testing.assert_allclose(path['One-way turnover'], expected_turnovers, atol=1e-14)
        assert list(path['Train last']) == list(simulated.index[59:71])
        assert list(path.index) == list(simulated.index[60:72])
        np.testing.assert_allclose(np.prod(1 + np.asarray(expected_returns)), expected_wealth[-1])

        summary = namespace['backtest_summary'].loc[rule]
        active = np.asarray(expected_returns) - namespace['paths']['CW']['Net return'].to_numpy()
        active_mean = sum(active) / 12
        annual_te_percent = 100 * np.sqrt(sum((value - active_mean) ** 2 for value in active) / 11 * 12)
        np.testing.assert_allclose(summary['TE vs CW (%)'], annual_te_percent, atol=1e-11)
        np.testing.assert_allclose(summary['Total return (%)'], 100 * (expected_wealth[-1] - 1))
        np.testing.assert_allclose(summary['Fees per initial 100k'], 100000 * sum(expected_fees), atol=1e-8)
        running_peak, worst_drawdown = 1.0, 0.0
        for wealth in expected_wealth[1:]:
            running_peak = max(running_peak, wealth)
            worst_drawdown = min(worst_drawdown, wealth / running_peak - 1)
        np.testing.assert_allclose(summary['Max drawdown (%)'], 100 * worst_drawdown)
    np.testing.assert_allclose(namespace['paths']['CW']['Fee'], 0, atol=1e-14)
    np.testing.assert_allclose(namespace['paths']['CW']['One-way turnover'], 0, atol=1e-14)
    return ['cap weighting, HHI and unequal risk contributions under equal weights',
            'cap growth and buy-and-hold drift from cash holdings',
            'self-financing fees by independent trade-sign enumeration',
            'gross versus net return denominator', 'capped weight projection and normalization violation',
            'known market caps use pre-period prices', 'walk-forward scalar holdings and 60-month timing',
            'tracking error from net active returns and sample denominator',
            'wealth compounding, initial drawdown and cost aggregation',
            'cap-weight drift needs no rebalance in the no-distribution fixture']


def check_lessons(spaces):
    return [*check_factor(spaces['factor-investing']),
            *check_multifactor(spaces['multifactor-models']),
            *check_style(spaces['style-analysis']),
            *check_smart_beta(spaces['smart-beta'])]


def check_charts(spaces):
    chart = json.loads((ROOT / 'data/advanced-figures.json').read_text())
    factor = spaces['factor-investing']
    style = spaces['style-analysis']
    np.testing.assert_allclose(chart['factor']['market_excess'], factor['x'])
    np.testing.assert_allclose(chart['factor']['fund_excess'], factor['y'])
    np.testing.assert_allclose([chart['factor']['intercept'], chart['factor']['beta']], [.001, 1.2])
    assert chart['style']['month_end'] == list(range(16, 33))
    assert chart['style']['columns'] == list(style['style_X'].columns)
    np.testing.assert_allclose(chart['style']['rolling_weights'], style['style_rolling'], atol=2e-5)

    # Check the actual plotted coordinates too. SVG rounding is 4 decimal
    # places for lines and 3 for scatter dots; both responsive sizes are tested.
    svg_namespace = {'s': 'http://www.w3.org/2000/svg'}
    for width, suffix in ((720, ''), (400, '-mobile')):
        height = 560 if width == 720 else 540

        def projected(xs, ys, x_limits, y_limits):
            return np.column_stack([
                60 + (np.asarray(xs) - x_limits[0]) / (x_limits[1] - x_limits[0]) * (width - 84),
                height - 88 - (np.asarray(ys) - y_limits[0]) / (y_limits[1] - y_limits[0]) * (height - 273),
            ])

        factor_svg = ET.parse(ROOT / f'assets/charts/advanced-factor-fit{suffix}.svg').getroot()
        assert factor_svg.attrib['viewBox'] == f'0 0 {width} {height}'
        lines = factor_svg.findall('s:polyline', svg_namespace)
        assert len(lines) == 1 and lines[0].attrib['data-series'] == 'fitted-excess-return'
        line_points = np.array([[float(value) for value in pair.split(',')]
                                for pair in lines[0].attrib['points'].split()])
        np.testing.assert_allclose(line_points, projected(factor['x'] * 100, factor['fitted'] * 100,
                                                         (-6, 7), (-7, 9)), atol=5.1e-5, rtol=0)
        dots = factor_svg.findall('s:circle', svg_namespace)
        assert len(dots) == 12
        dot_points = [[float(dot.attrib['cx']), float(dot.attrib['cy'])] for dot in dots]
        np.testing.assert_allclose(dot_points, projected(factor['x'] * 100, factor['y'] * 100,
                                                        (-6, 7), (-7, 9)), atol=5.1e-4, rtol=0)

        style_svg = ET.parse(ROOT / f'assets/charts/advanced-style-drift{suffix}.svg').getroot()
        assert style_svg.attrib['viewBox'] == f'0 0 {width} {height}'
        lines = style_svg.findall('s:polyline', svg_namespace)
        assert len(lines) == 3
        for column, line in enumerate(lines):
            assert line.attrib['data-series'] == chart['style']['columns'][column]
            points = [[float(value) for value in pair.split(',')] for pair in line.attrib['points'].split()]
            expected = projected(chart['style']['month_end'],
                                 np.asarray(chart['style']['rolling_weights'])[:, column] * 100,
                                 (16, 32), (0, 70))
            np.testing.assert_allclose(points, expected, atol=5.1e-5, rtol=0)
    return ['factor chart values match executed lesson and analytical line',
            'style chart values match every executed rolling fit',
            'desktop and mobile SVG lines and scatter points match numerical metadata']


def check_empirical_aggregates():
    """Pin published aggregates to the separate local audit, without private CSVs.

    The local audit compounded 7,307 daily records into 348 complete months and
    independently compared NumPy, SciPy and statsmodels estimates. CI verifies
    that saved results match that audit; it does not recompute raw market data.
    """
    report = json.loads((ROOT / 'data/advanced-factor-results.json').read_text())
    assert report['archive_sha256'] == '8f11b5617ce180f82120d18e29276e9f13341734bacb529359db5efece908e8f'
    assert report['files_sha256'] == {
        'brka_d_ret.csv': '047410a705aa38c708a8f24b87cf4dae699da8def3795cff2a86b8bf10a3f488',
        'F-F_Research_Data_Factors_m.csv': 'd79d118bf62fce739f5730293b6bdef23342e521bdb29937db3dde48e5954950',
    }
    assert report['sample'] == {'start': '1990-01', 'end': '2018-12', 'months': 29 * 12}
    expected = {
        'CAPM': (['alpha', 'Mkt-RF'], [.0060694257903239875, .5779457613060572], .18143358720233438),
        'FF3': (['alpha', 'Mkt-RF', 'SMB', 'HML'],
                [.00516539717929987, .7096050666739301, -.48293687928081463, .40528319044807626],
                .31729316429420207),
    }
    for name, (columns, coefficients, r_squared) in expected.items():
        actual = report['models'][name]
        assert list(actual['coefficients']) == columns
        np.testing.assert_allclose(list(actual['coefficients'].values()), coefficients, atol=1e-12, rtol=1e-10)
        np.testing.assert_allclose(actual['r_squared'], r_squared, atol=1e-12, rtol=1e-10)
    return ['empirical archive and CSV hashes plus complete 1990-2018 monthly sample',
            'published CAPM and FF3 aggregates match the independent local audit']


def main():
    pages = exporter.course_pages('advanced')
    module_counts = {1: 4, 2: 3, 3: 3}
    assert set(page['module'] for page in pages) == set(module_counts)
    for module, count in module_counts.items():
        assert sorted(page['lesson'] for page in pages if page['module'] == module) == list(range(1, count + 1))
    spaces, report = {}, []
    for page in pages:
        fresh, namespace, outputs = exporter.execute_chapter(page)
        spaces[page['file']] = namespace
        code_count = check_notebook(page, fresh)
        assert code_count == len(outputs)
        report.append({'page': page['file'], 'executed_examples': code_count,
                       'notebook_consistent': True})
        print(f'PASS {page["file"]}: {code_count} examples and complete notebook')

    module2 = load_module('advanced_module2_checks', ROOT / 'qa/advanced-module2-checks.py')
    module3 = load_module('advanced_module3_checks', ROOT / 'qa/advanced-module3-checks.py')
    independent_checks = [*check_lessons(spaces), *check_charts(spaces), *check_empirical_aggregates(),
                          *module2.check_lessons(spaces), *module3.check_lessons(spaces)]
    report_data = {
        'course': 'advanced', 'modules': sorted(module_counts), 'pages': report,
        'total_executed_examples': sum(page['executed_examples'] for page in report),
        'independent_checks': independent_checks,
        'empirical_validation': 'Saved aggregates checked against the prior local audit; raw CSVs are not required or reprocessed by CI',
    }
    out = ROOT / 'qa/output'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'advanced-course-python-report.json').write_text(
        json.dumps(report_data, ensure_ascii=False, indent=2) + '\n')
    print(f'PASS {report_data["total_executed_examples"]} executed examples across '
          f'{len(pages)} independent chapters; {len(independent_checks)} independent checks')


if __name__ == '__main__':
    main()
