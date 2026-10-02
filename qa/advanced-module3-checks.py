"""Independent oracles for expected returns, views and Black-Litterman."""
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def rejects(function,*args):
    try:
        function(*args)
    except (ValueError,TypeError,np.linalg.LinAlgError):
        return
    raise AssertionError(f'{function.__name__} accepted invalid inputs')


def check_expected_returns(ns):
    from scipy import stats
    np.testing.assert_allclose(ns['sample_mean'],.01,atol=1e-15)
    np.testing.assert_allclose(ns['sample_sd']**2,.001,atol=1e-15)
    np.testing.assert_allclose(ns['mean_se'],np.sqrt(.001/6),atol=1e-15)
    np.testing.assert_allclose(ns['mean_ci'],.01+np.array([-1,1])*stats.t.ppf(.975,5)*np.sqrt(.001/6),atol=1e-15)
    np.testing.assert_allclose(ns['frequency_table']['annual_mean_SE_pct'],100*.2/np.sqrt(5),atol=1e-12)
    np.testing.assert_allclose(ns['annual_se_by_year'],[.2,.1,.05,.025],atol=1e-15)
    simulated = ns['sim_samples']
    np.testing.assert_array_equal(simulated,np.random.default_rng(20261003).normal(.005,.04,size=(10000,60)))
    theory = .04/np.sqrt(60)
    assert abs(ns['sim_means'].std(ddof=1)/theory-1) < .04
    assert abs(ns['sim_coverage']-.95) < .015
    assert abs(np.mean(ns['sim_means']<0)-stats.norm.cdf(-.005/theory)) < .02
    checks = ['mean, sample variance, t interval and annual SE checked against scalar formulas',
              'seeded mean simulation agrees with theoretical standard error, coverage and negative-mean frequency']
    np.testing.assert_allclose(ns['sensitivity_weights'],[[.5,.5],[1.5,-.5],[-.5,1.5]],atol=1e-12)
    np.testing.assert_allclose(ns['sensitivity_long_only'],[[.5,.5],[1,0],[0,1]],atol=1e-12)
    np.testing.assert_allclose(ns['shrunken_weights'],[[1.5,-.5],[1,0],[.6,.4],[.5,.5]],atol=1e-12)
    for mu,w in zip(ns['sensitivity_means'],ns['sensitivity_weights']):
        gradient = mu-3*ns['sensitivity_cov']@w
        np.testing.assert_allclose(gradient[0],gradient[1],atol=1e-14)
    checks += ['sensitive two-asset weights and mean shrinkage checked by hand and constrained FOC']
    covariance = ns['expected_cov']
    np.testing.assert_allclose(covariance@ns['gmv_weights'],np.repeat(ns['gmv_weights']@covariance@ns['gmv_weights'],3),atol=1e-14)
    sharpes = ns['premium_edge_sharpes']
    assert sharpes[0,0] > sharpes[1,0] > sharpes[2,0]
    assert sharpes[0,2] < sharpes[1,2] < sharpes[2,2]
    np.testing.assert_array_equal(sharpes[:,1],0)
    # Here all entries of the analytic tangency direction are positive, so it
    # also solves the long-only ratio problem without an active lower bound.
    for premium,cov,actual in ((np.sqrt(covariance.diagonal()),covariance,ns['diversification_weights']),
                               (ns['market_betas'],ns['capm_cov'],ns['capm_weights'])):
        direction = np.linalg.solve(cov,premium)
        assert direction.min() > 0
        np.testing.assert_allclose(actual,direction/direction.sum(),atol=1e-5)
    np.testing.assert_allclose(ns['capm_weights'],ns['capm_weights_double'],atol=1e-5)
    checks += ['positive/zero/negative common premia preserve the stated Sharpe ordering',
               'maximum diversification and CAPM portfolios agree with analytic positive tangency directions']
    design,excess = ns['factor_design'],ns['asset_excess']
    residual = excess-design@ns['fitted_coefficients']
    np.testing.assert_allclose(design.T@residual,0,atol=1e-15)
    np.testing.assert_allclose(ns['fitted_alpha'],[.001,-.0005,.0008],atol=1e-15)
    np.testing.assert_allclose(ns['fitted_loadings'],[[.7,.3],[1,-.2],[1.3,.5]],atol=1e-15)
    np.testing.assert_allclose(ns['reconstructed_means'],[.0061,.0051,.0093],atol=1e-15)
    np.testing.assert_allclose(ns['factor_forecasts']['cautious'],[.0036,.0045,.0054],atol=1e-15)
    np.testing.assert_allclose(ns['factor_forecasts']['negative_value'],[.003,.0049,.0044],atol=1e-15)
    actual = ns['heldout_returns'].to_numpy()
    for name,forecast in ns['frozen_forecasts'].items():
        squared_errors = [(actual[t,i]-forecast.iloc[i])**2 for t in range(3) for i in range(3)]
        np.testing.assert_allclose(ns['forecast_rmse'][name],np.sqrt(sum(squared_errors)/9),atol=1e-15)
    assert ns['factor_returns'].index.max() < ns['heldout_returns'].index.min()
    checks += ['factor fit satisfies OLS normal equations; forecast scenarios verified term by term',
               'frozen-forecast RMSE reconstructed from nine individual held-out errors']
    return checks


def check_implied(ns):
    s,w,delta,pi = ns['covariance'],ns['benchmark_weights'],ns['risk_aversion'],ns['pi']
    np.testing.assert_allclose(pi,[.063,.034125,.018375],atol=1e-14)
    np.testing.assert_allclose(ns['benchmark_variance'],.018165,atol=1e-14)
    np.testing.assert_allclose(ns['benchmark_excess_mean'],.0454125,atol=1e-14)
    np.testing.assert_allclose(ns['recovered_weights'],w,atol=1e-14)
    np.testing.assert_allclose(ns['utility_at_anchor']-ns['utility_at_perturbation'],ns['utility_loss_formula'],atol=1e-14)
    np.testing.assert_allclose(ns['delta_table']['Cash'],[-1,0,.5],atol=1e-14)
    np.testing.assert_allclose(ns['budget_base'],w,atol=1e-14)
    np.testing.assert_allclose(ns['budget_shifted'],w,atol=1e-14)
    np.testing.assert_allclose(ns['eta_shifted']-ns['eta_base'],.01,atol=1e-14)
    assert not np.allclose(ns['normalized_shifted'],w)
    # Solve the constrained KKT block system independently of the lesson's formula.
    kkt = np.block([[delta*s,np.ones((3,1))],[np.ones((1,3)),np.zeros((1,1))]])
    solution = np.linalg.solve(kkt,np.r_[pi+.01,1])
    np.testing.assert_allclose(solution[:3],ns['budget_shifted'],atol=1e-14)
    np.testing.assert_allclose(solution[3],ns['eta_shifted'],atol=1e-14)
    checks = ['implied returns, benchmark variance, utility loss and cash allocations verified analytically',
              'budget-constrained FOC checked by an independent KKT system; normalization differs']

    np.testing.assert_allclose(ns['view_surprise'],[.006625,-.008875],atol=1e-14)
    np.testing.assert_allclose(ns['Q_raw'],[.045,.02],atol=1e-14)
    np.testing.assert_allclose(ns['prior_view_covariance'],[[.0005,.000175],[.000175,.001925]],atol=1e-14)
    np.testing.assert_allclose(ns['omega'],np.diag([.0005,.001925]),atol=1e-14)
    assert not np.array_equal(ns['omega'],ns['prior_view_covariance'])
    np.testing.assert_allclose(ns['omega_correlated'][0,1],.5*np.sqrt(.0005*.001925),atol=1e-14)
    assert np.linalg.matrix_rank(ns['omega_duplicate']) == 1
    np.testing.assert_allclose(ns['original_standardized_gap'],ns['scaled_standardized_gap'],atol=1e-14)
    np.testing.assert_allclose(ns['pi_percent'],100*pi,atol=1e-14)
    np.testing.assert_allclose(ns['recomputed_pi_percent'],100*pi,atol=1e-14)
    np.testing.assert_allclose(ns['recovered_percent_weights'],w,atol=1e-14)
    np.testing.assert_allclose(ns['omega_percent'],10000*ns['omega'],atol=1e-14)
    checks += ['absolute/relative raw-return conversion and view surprises verified by hand',
               'view-error covariance distinguished from projected prior covariance and repeated information',
               'view-row scaling and percentage-unit/risk-aversion conversion preserve meaning']

    for matrix in (np.array([[1,2],[2,1]]),np.array([[1,0],[2,1]]),np.full((2,2),np.nan)):
        rejects(ns['validate_covariance'],matrix)
    for inputs in ns['invalid_view_cases'].values():
        rejects(ns['validate_views'],*inputs,3)
    rejects(ns['budget_constrained_weights'],pi,s,0)
    rejects(ns['budget_constrained_weights'],pi,s,np.inf)
    checks += ['implied-return/view helpers reject malformed dimensions, nonfinite values and invalid covariance']
    return checks


def precision_posterior(s,pi,P,Q,omega,tau):
    """Small well-conditioned fixture oracle using precision, unlike lesson gain form."""
    prior_precision = np.linalg.inv(tau*s)
    posterior_precision = prior_precision + P.T@np.linalg.solve(omega,P)
    M = np.linalg.inv(posterior_precision)
    mean = np.linalg.solve(posterior_precision,prior_precision@pi+P.T@np.linalg.solve(omega,Q))
    return mean,M


def face_utility_optimum(mean,s,delta):
    candidates = []
    for size in range(1,len(mean)+1):
        for indices in itertools.combinations(range(len(mean)),size):
            kkt = np.block([[delta*s[np.ix_(indices,indices)],np.ones((size,1))],
                            [np.ones((1,size)),np.zeros((1,1))]])
            face = np.linalg.solve(kkt,np.r_[mean[list(indices)],1])[:size]
            if face.min() < -1e-10:
                continue
            weights = np.zeros(len(mean))
            weights[list(indices)] = face
            utility = weights@mean-.5*delta*weights@s@weights
            candidates.append((utility,weights))
    return max(candidates,key=lambda candidate:candidate[0])


def check_bl(ns):
    np.testing.assert_allclose(ns['scalar_posterior_mean'],.056,atol=1e-14)
    np.testing.assert_allclose(ns['scalar_posterior_var'],.00008,atol=1e-14)
    s,pi,P,Q,omega,tau = [ns[name] for name in ('covariance','pi','P','Q','omega','tau')]
    expected_mean,expected_M = precision_posterior(s,pi,P,Q,omega,tau)
    np.testing.assert_allclose(ns['bl_mean'],expected_mean,atol=1e-14)
    np.testing.assert_allclose(ns['bl_M'],expected_M,atol=1e-14)
    np.testing.assert_allclose(ns['bl_predictive'],s+expected_M,atol=1e-14)
    assert np.linalg.eigvalsh(expected_M).min() > 0
    assert np.linalg.eigvalsh(tau*s-expected_M).min() > -1e-14
    assert np.linalg.eigvalsh(ns['bl_predictive']-s).min() > 0
    checks = ['scalar Bayes mean/variance verified by precision weighting',
              'matrix posterior verified independently in precision form; covariance ordering is consistent']

    precise_mean,precise_M,_ = ns['bl_posterior'](s,pi,P,Q,np.zeros((2,2)),tau)
    np.testing.assert_allclose(P@precise_mean,Q,atol=1e-14)
    np.testing.assert_allclose(P@precise_M@P.T,0,atol=1e-14)
    assert np.trace(precise_M) > 1e-5
    weak_mean,weak_M,_ = ns['bl_posterior'](s,pi,P,Q,omega*1e9,tau)
    np.testing.assert_allclose(weak_mean,pi,atol=1e-10)
    np.testing.assert_allclose(weak_M,tau*s,atol=1e-10)
    matching_mean,matching_M,_ = ns['bl_posterior'](s,pi,P,P@pi,omega,tau)
    np.testing.assert_allclose(matching_mean,pi,atol=1e-14)
    assert np.trace(matching_M) < np.trace(tau*s)
    for factor in (.2,4):
        mu,M,pred = ns['bl_posterior'](s,pi,P,Q,omega*factor,tau*factor)
        np.testing.assert_allclose(mu,expected_mean,atol=1e-14)
        np.testing.assert_allclose(M,expected_M*factor,atol=1e-14)
        assert not np.allclose(pred,ns['bl_predictive'])
    checks += ['exact/weak/matching views and uncertainty outside the viewed directions',
               'tau/Omega joint scaling preserves the mean while changing posterior and predictive covariance']

    corr_mean,corr_M = precision_posterior(s,pi,P,Q,ns['omega_correlated'],tau)
    np.testing.assert_allclose(ns['correlated_mean'],corr_mean,atol=1e-14)
    np.testing.assert_allclose(ns['correlated_M'],corr_M,atol=1e-14)
    # Multiplying an entire view equation must not create additional information.
    scaling = np.diag([3,.25])
    scaled = ns['bl_posterior'](s,pi,scaling@P,scaling@Q,scaling@omega@scaling.T,tau)
    np.testing.assert_allclose(scaled[0],expected_mean,atol=1e-14)
    np.testing.assert_allclose(scaled[1],expected_M,atol=1e-14)
    units = ns['bl_posterior'](s*10000,pi*100,P,Q*100,omega*10000,tau)
    np.testing.assert_allclose(units[0],100*expected_mean,atol=1e-12)
    np.testing.assert_allclose(units[1],10000*expected_M,atol=1e-12)
    row = ns['duplicate_rows']
    assert row[1]['C mean uncertainty SD (%)'] < row[0]['C mean uncertainty SD (%)']
    assert abs(row[2]['C mean (%)']-row[0]['C mean (%)']) < .0001
    rejects(ns['bl_posterior'],s,pi,ns['duplicate_P'],ns['duplicate_Q'],np.full((2,2),omega[0,0]),tau)
    checks += ['correlated-view posterior checked by a separate precision oracle',
               'view-row and return-unit transformations preserve posterior information',
               'duplicate independent evidence reduces uncertainty; exactly repeated information is rejected']

    np.testing.assert_allclose(ns['no_view_mean'],pi,atol=1e-14)
    np.testing.assert_allclose(ns['no_view_M'],tau*s,atol=1e-14)
    np.testing.assert_allclose(ns['no_view_fixed_weights'],ns['benchmark_weights'],atol=1e-14)
    np.testing.assert_allclose(ns['no_view_predictive_weights'],ns['benchmark_weights']/(1+tau),atol=1e-14)
    delta = ns['risk_aversion']
    np.testing.assert_allclose(delta*s@ns['fixed_sigma_weights'],expected_mean,atol=1e-14)
    np.testing.assert_allclose(delta*ns['bl_predictive']@ns['predictive_weights'],expected_mean,atol=1e-14)
    for cov,mean in ((ns['bl_predictive'],expected_mean),(s,np.array([.2,.02,.01]))):
        optimum,weights = face_utility_optimum(mean,cov,delta)
        actual = ns['long_only_utility'](mean,cov,delta)
        utility = actual@mean-.5*delta*actual@cov@actual
        np.testing.assert_allclose(utility,optimum,atol=1e-12)
        np.testing.assert_allclose(actual,weights,atol=1e-5)
    checks += ['no-view cash allocation and fixed/predictive utility FOCs checked',
               'fully invested long-only utility agrees with independent KKT face enumeration']
    for bad_tau in (0,-.1,np.nan,np.inf):
        rejects(ns['bl_posterior'],s,pi,P,Q,omega,bad_tau)
    rejects(ns['bl_posterior'],s,pi,P,Q,np.diag([-.1,.1]),tau)
    rejects(ns['bl_posterior'],s,pi,P[:,:2],Q,omega,tau)
    rejects(ns['long_only_utility'],expected_mean,ns['bl_predictive'],0)
    checks += ['BL and allocation helpers reject invalid dimensions, uncertainties and risk aversion']
    return checks


def check_charts(spaces):
    metadata = json.loads((ROOT/'data/advanced-expected-return-figures.json').read_text())
    mean,view = metadata['mean'],metadata['view']
    years = np.linspace(1,20,153)
    sds = np.sort(np.unique(np.r_[np.linspace(0,.08,81),np.sqrt(.0005)]))
    np.testing.assert_allclose(mean['years'],years,atol=1e-14)
    np.testing.assert_allclose(view['view_error_sd_percent'],100*sds,atol=1e-14)
    # Independent one-dimensional precision/gain formula for C-only view.
    c_mean = .018375+.0005/(.0005+sds**2)*(.025-.018375)
    datasets = {
        'advanced-mean-uncertainty':(years,[(mean['annual_mean_standard_error_pp'],20/np.sqrt(years))],(1,20),(0,21)),
        'advanced-view-confidence':(100*sds,[(view['posterior_c_percent'],100*c_mean),
                                             (view['prior_c_percent'],np.full(len(sds),1.8375)),
                                             (view['view_c_percent'],np.full(len(sds),2.5))],(0,8),(1.5,3)),
    }
    np.testing.assert_allclose(mean['annual_sigma'],spaces['expected-return-estimation']['annual_sigma'])
    for name,(xs,series,xlim,ylim) in datasets.items():
        for width,suffix in ((720,''),(400,'-mobile')):
            height = 560 if width == 720 else 540
            root = ET.parse(ROOT/f'assets/charts/{name}{suffix}.svg').getroot()
            lines = root.findall('{http://www.w3.org/2000/svg}polyline')
            assert len(lines) == len(series)
            for line,(ys,expected) in zip(lines,series):
                np.testing.assert_allclose(ys,expected,atol=1e-12)
                coords = np.array([[float(v) for v in xy.split(',')] for xy in line.attrib['points'].split()])
                actual = np.column_stack([60+(np.asarray(xs)-xlim[0])/(xlim[1]-xlim[0])*(width-84),
                                          height-88-(np.asarray(ys)-ylim[0])/(ylim[1]-ylim[0])*(height-273)])
                np.testing.assert_allclose(coords,actual,atol=5.1e-5,rtol=0)
    return ['both chart axes, analytical values, and desktop/mobile SVG coordinates independently verified']


def check_lessons(spaces):
    return [*check_expected_returns(spaces['expected-return-estimation']),
            *check_implied(spaces['implied-returns-views']),*check_bl(spaces['black-litterman']),*check_charts(spaces)]
