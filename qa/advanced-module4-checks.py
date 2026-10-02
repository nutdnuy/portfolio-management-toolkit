"""Independent numerical references for diversification, Euler risk and budgets."""
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
VOL = np.array([.20,.15,.10,.25])
CORR = np.array([[1,.5,.2,.65],[.5,1,.1,.4],[.2,.1,1,.15],[.65,.4,.15,1]])
COV = np.outer(VOL,VOL)*CORR


def rejects(function,*args):
    try:
        function(*args)
    except (ValueError,TypeError,np.linalg.LinAlgError):
        return
    raise AssertionError(f'{function.__name__} accepted invalid inputs')


def risk_budget_reference(cov,budget):
    """Cyclic coordinate minimization; no SciPy optimizer or gradients from lesson."""
    cov = np.asarray(cov)
    budget = np.asarray(budget)
    x = np.sqrt(budget/cov.diagonal())
    for iteration in range(10000):
        for i in range(len(x)):
            cross = cov[i]@x-cov[i,i]*x[i]
            discriminant = np.sqrt(cross*cross+4*cov[i,i]*budget[i])
            x[i] = 2*budget[i]/(discriminant+cross) if cross >= 0 else (discriminant-cross)/(2*cov[i,i])
        if np.max(np.abs(x*(cov@x)-budget)) < 1e-13:
            return x/x.sum()
    raise AssertionError('Coordinate reference failed to converge')


def minimum_variance_reference(cov,min_enc=1):
    """Enumerate simplex faces; solve ENC constraint using a scalar ridge multiplier."""
    n = len(cov)
    if abs(min_enc-n)<1e-12:
        return np.repeat(1/n,n)
    candidates=[]
    for size in range(1,n+1):
        if size+1e-12 < min_enc:
            continue
        for indices in itertools.combinations(range(n),size):
            face = cov[np.ix_(indices,indices)]
            def weights(lam):
                direction = np.linalg.solve(face+lam*np.eye(size),np.ones(size))
                return direction/direction.sum()
            value=weights(0)
            if value@value > 1/min_enc+1e-12:
                if abs(size-min_enc)<1e-12:
                    value=np.repeat(1/size,size)
                else:
                    upper=1.0
                    while weights(upper)@weights(upper)>1/min_enc:
                        upper*=10
                    lam=brentq(lambda ridge: weights(ridge)@weights(ridge)-1/min_enc,0,upper,xtol=1e-14)
                    value=weights(lam)
            if value.min() < -1e-10:
                continue
            candidate=np.zeros(n);candidate[list(indices)]=value
            candidates.append((candidate@cov@candidate,candidate))
    assert candidates
    return min(candidates,key=lambda pair:pair[0])[1]


def check_methods(ns):
    np.testing.assert_allclose(ns['covariance'],COV,atol=1e-15)
    np.testing.assert_allclose(ns['market_caps_million'],[700,100,100,100],atol=1e-14)
    np.testing.assert_allclose(ns['cap_weights'],[.7,.1,.1,.1],atol=1e-14)
    np.testing.assert_allclose(ns['effective_number'](ns['cap_weights']),1/.52,atol=1e-14)
    np.testing.assert_allclose(ns['effective_number'](ns['equal_weights']),4,atol=1e-14)
    np.testing.assert_allclose(ns['equal_end_wealth'],997500,atol=1e-9)
    np.testing.assert_allclose(ns['equal_rebalance_trades'],[-25625,11875,-5625,19375],atol=1e-9)
    np.testing.assert_allclose(ns['equal_one_way_turnover'],31250/997500,atol=1e-14)
    np.testing.assert_allclose(ns['cap_drift'],np.array([.77,.095,.102,.092])/1.059,atol=1e-14)
    np.testing.assert_allclose(ns['cap_drift'],ns['new_cap_weights'],atol=1e-14)
    checks=['capitalization, ENC, weight drift and zero-cost rebalance trades checked in baht']
    for target,actual in zip(ns['enc_targets'],ns['enc_constrained_weights']):
        expected=minimum_variance_reference(COV,target)
        np.testing.assert_allclose(actual,expected,atol=3e-6)
        assert actual.min()>=0 and abs(actual.sum()-1)<1e-8
        assert ns['effective_number'](actual)>=target-1e-7
    variances=np.einsum('ij,jk,ik->i',ns['enc_constrained_weights'],COV,ns['enc_constrained_weights'])
    assert np.all(np.diff(variances)>=-1e-12)
    np.testing.assert_allclose(ns['gmv_weights'],minimum_variance_reference(COV),atol=3e-6)
    np.testing.assert_allclose(ns['gmv_unconstrained'],minimum_variance_reference(COV),atol=1e-14)
    boundary_cov=np.array([[.04,.05],[.05,.09]])
    for target in (1,1.5,2):
        np.testing.assert_allclose(ns['solve_min_variance'](boundary_cov,target),minimum_variance_reference(boundary_cov,target),atol=3e-6)
    checks+=['GMV with five minimum-ENC levels agrees with independent face/ridge-multiplier solutions',
             'minimum estimated variance cannot fall as ENC constraints tighten; boundary optimum checked']
    decorrelation=minimum_variance_reference(CORR)
    diversification=decorrelation/VOL;diversification/=diversification.sum()
    np.testing.assert_allclose(ns['max_decorrelation_weights'],decorrelation,atol=3e-6)
    np.testing.assert_allclose(ns['max_dr_weights'],diversification,atol=3e-6)
    np.testing.assert_allclose(ns['dr_from_correlation'],diversification,atol=3e-6)
    assert not np.allclose(ns['max_decorrelation_weights'],ns['max_dr_weights'],atol=.001)
    checks+=['maximum decorrelation and maximum DR checked via the standardized-risk transformation']
    for weights in ([2,-1],[.6,.6],[np.nan,1],[]):
        rejects(ns['effective_number'],weights)
    for target in (0,5,np.nan):
        rejects(ns['solve_min_variance'],COV,target)
    checks+=['capital-concentration helpers reject invalid weights and infeasible ENC requests']
    for name, weights in ns['strategy_weights'].items():
        sd = np.sqrt(weights @ COV @ weights)
        expected = [1 / (weights @ weights), sd, weights @ VOL / sd]
        np.testing.assert_allclose(ns['strategy_metrics'][name], expected, atol=1e-12)
    centered = ns['small_returns'] - ns['small_returns'].mean(axis=0)
    np.testing.assert_allclose(ns['small_sample_cov'], centered.T @ centered / 3, atol=1e-15)
    assert np.linalg.matrix_rank(ns['small_sample_cov']) == 3
    altered_vol = VOL.copy(); altered_vol[2] = .08
    altered_cov = np.outer(altered_vol, altered_vol) * CORR
    np.testing.assert_allclose(ns['stressed_covariance'], altered_cov, atol=1e-15)
    for target, key in ((1, 'stressed_gmv_weights'), (3, 'stressed_gmv_enc_weights')):
        np.testing.assert_allclose(ns[key], minimum_variance_reference(altered_cov, target), atol=3e-6)
        baseline = ns['gmv_weights'] if target == 1 else ns['gmv_enc_weights']
        assert ns[key] @ COV @ ns[key] > baseline @ COV @ baseline
    checks += ['six-method comparison uses common risk units; centered sample has rank three',
               'changed volatility reallocates GMV as independently solved, with original-covariance risk evaluated separately']
    return checks


def self_financing_reference(before,target,rate):
    """Solve each linear segment of the absolute-value equation without root finding."""
    before,target=np.asarray(before),np.asarray(target)
    for signs in itertools.product((-1,1),repeat=len(before)):
        signs=np.array(signs)
        scale=(1+rate*(signs@before))/(1+rate*(signs@target))
        trades=scale*target-before
        if 0<=scale<=1+1e-12 and np.all(signs*trades>=-1e-12):
            return scale,trades,rate*np.abs(trades).sum()
    raise AssertionError('No feasible piecewise-linear cost solution')


def check_backtest(ns):
    returns=ns['asset_returns']
    np.testing.assert_allclose(ns['population_covariance'],COV,atol=1e-15)
    original=np.random.default_rng(20261004).uniform(-np.sqrt(3),np.sqrt(3),size=(96,4))
    np.testing.assert_allclose(returns,.005+original@np.linalg.cholesky(COV/12).T,atol=1e-15)
    assert returns.shape==(96,4) and list(returns.index)==list(range(1,97))
    assert np.all(ns['return_lower_bounds']>-1)
    for name,table in ns['weight_schedules'].items():
        assert list(table.index)==list(range(37,97)) and table.shape==(60,4)
        np.testing.assert_allclose(table.sum(axis=1),1,atol=1e-10)
        assert table.to_numpy().min()>=0
        np.testing.assert_allclose(table.loc[:61],ns['changed_schedules'][name].loc[:61],atol=1e-12,rtol=0)
    for month in range(37,97):
        training=returns.loc[month-36:month-1].to_numpy()
        centered=training-training.mean(axis=0)
        cov=centered.T@centered/35
        sd=np.sqrt(cov.diagonal())
        reference_gmv=minimum_variance_reference(cov)
        reference_corr=minimum_variance_reference(cov/np.outer(sd,sd))
        dr=reference_corr/sd;dr/=dr.sum()
        erc=risk_budget_reference(cov,np.repeat(.25,4))
        expected={'EW':np.repeat(.25,4),'IV':(1/sd)/(1/sd).sum(),
                  'GMV':reference_gmv,'ERC':erc,'MaxDR':dr}
        for name,value in expected.items():
            np.testing.assert_allclose(ns['weight_schedules'][name].loc[month],value,atol=3e-6)
    checks=['bounded seeded returns and all 300 decision dates/weight budgets verified',
            'every rolling covariance and five strategy weights checked with explicit centered products, face enumeration and coordinate descent',
            'future perturbation cannot affect weights decided through that month']
    np.testing.assert_allclose(ns['changed_wealth'].loc[:60],ns['net_wealth'].loc[:60],atol=1e-12,rtol=0)
    assert ns['max_next_weight_change']>1e-5
    for bps,wealth_table in ns['cost_wealth'].items():
        rate=bps/10000
        ledger=ns['cost_ledgers'][bps]
        for name,targets in ns['weight_schedules'].items():
            holdings=np.zeros(4);cash=1.0;path=[1.0]
            for month,target in targets.iterrows():
                pre=holdings.sum()+cash
                before=holdings/pre
                scale,trades,fee_fraction=self_financing_reference(before,target.to_numpy(),rate)
                trade_dollars=trades*pre
                fee=fee_fraction*pre
                assert abs(cash-trade_dollars.sum()-fee)<1e-11
                after=holdings+trade_dollars
                assert abs(after.sum()+fee-pre)<1e-11
                holdings=after*(1+returns.loc[month].to_numpy());cash=0.0
                actual=ledger.loc[(name,month)]
                np.testing.assert_allclose(actual['Fee'],fee,atol=1e-12)
                np.testing.assert_allclose([actual[f'Trade {a}'] for a in returns.columns],trades,atol=1e-12)
                np.testing.assert_allclose([actual[f'End value {a}'] for a in returns.columns],holdings,atol=1e-12)
                np.testing.assert_allclose(actual['End wealth'],holdings.sum(),atol=1e-12)
                path.append(holdings.sum())
                if month==37:
                    np.testing.assert_allclose(scale,1/(1+rate),atol=1e-14)
            np.testing.assert_allclose(wealth_table[name],path,atol=1e-12)
        assert wealth_table.shape==(61,5) and (wealth_table.loc[36]==1).all()
    checks+=['all 900 fee-ledger rows reconstructed in dollars using an independent piecewise-linear cost solver',
             'all 15 gross/net wealth paths reconcile initial purchase, fees, held returns and no terminal liquidation']
    np.testing.assert_allclose(ns['toy_scale'],(1-.0006)/(1-.0002),atol=1e-14)
    for label in ('gross','net'):
        wealth_table=ns[label+'_wealth'];summary=ns[label+'_summary']
        for name in wealth_table:
            wealth=wealth_table[name].to_numpy()
            r=np.array([wealth[i+1]/wealth[i]-1 for i in range(60)])
            mean=sum(r)/60;sd=np.sqrt(sum((r-mean)**2)/59)
            peak=wealth[0];max_loss=0
            for value in wealth:
                peak=max(peak,value);max_loss=max(max_loss,1-value/peak)
            np.testing.assert_allclose(summary.loc[name,['CAGR (%)','Annual mean (%)','Annual SD (%)','Sharpe, RF = 0','Max drawdown (%)']].to_numpy(dtype=float),
                                       [100*(wealth[-1]**.2-1),1200*mean,100*np.sqrt(12)*sd,np.sqrt(12)*mean/sd,100*max_loss],atol=1e-10)
    assert np.all(ns['cost_wealth'][50].to_numpy()<=ns['net_wealth'].to_numpy()+1e-12)
    assert np.all(ns['net_wealth'].to_numpy()<=ns['gross_wealth'].to_numpy()+1e-12)
    checks+=['two-asset fee solution checked by hand; CAGR, arithmetic Sharpe, SD and drawdown recalculated from all 60 held returns',
             'higher proportional costs reduce every wealth path with unchanged targets in this fixture']
    rejects(ns['exact_rebalance'],[.5,.5],[.5,.5],-.01)
    rejects(ns['exact_rebalance'],[.5,.5],[.6,.6],.001)
    rejects(ns['make_weight_schedules'],returns,96)
    invalid=returns.copy();invalid.iloc[0,0]=-1
    rejects(ns['make_weight_schedules'],invalid,36)
    checks+=['backtest guards reject invalid costs, nonbudget targets, unusable windows and nonpositive gross returns']
    return checks


def check_components(ns):
    covariance,w=ns['covariance'],ns['weights']
    np.testing.assert_allclose(covariance,COV,atol=1e-15)
    np.testing.assert_allclose(ns['portfolio_variance'],.019845,atol=1e-15)
    # Explicit pair summation gives one diagonal term plus half of each
    # symmetric cross pair to each asset, independently of matrix products.
    parts=np.array([sum(w[i]*w[j]*covariance[i,j] for j in range(4)) for i in range(4)])
    np.testing.assert_allclose(parts,[.013525,.00276,.000935,.002625],atol=1e-15)
    np.testing.assert_allclose(ns['components']['Variance part'],parts,atol=1e-15)
    np.testing.assert_allclose(ns['components']['Component vol'].sum(),np.sqrt(.019845),atol=1e-15)
    np.testing.assert_allclose(ns['components']['Risk share'].sum(),1,atol=1e-15)
    np.testing.assert_allclose(w@(2*covariance@w),2*.019845,atol=1e-15)
    checks=['Euler variance parts checked by explicit pair sums; volatility parts and risk shares add correctly']
    marginal=ns['components']['Marginal vol'].to_numpy()
    np.testing.assert_allclose(ns['free_derivative'],marginal[0],atol=1e-10)
    np.testing.assert_allclose(ns['funded_derivative'],marginal[0]-marginal[2],atol=1e-10)
    np.testing.assert_allclose(ns['monthly_components']['Component vol'],ns['components']['Component vol'].to_numpy()/np.sqrt(12),atol=1e-15)
    np.testing.assert_allclose(ns['percent_components']['Component vol'],100*ns['components']['Component vol'].to_numpy(),atol=1e-14)
    np.testing.assert_allclose(ns['money_components'].sum(),1000000*np.sqrt(.019845),atol=1e-8)
    checks+=['free and funded directional derivatives checked by finite differences; time/return/currency units reconcile']
    hedge=ns['hedge_components']
    np.testing.assert_allclose(hedge['Variance part'],[-.00104,.00666],atol=1e-15)
    np.testing.assert_allclose(ns['hedge_vol'],np.sqrt(.00562),atol=1e-15)
    assert hedge['Risk share'].iloc[0]<0 and hedge['Risk share'].iloc[1]>1
    assert 1/np.sum(hedge['Risk share']**2)<1
    assert abs(ns['hedge_vol']-.09) != abs(hedge['Component vol'].iloc[0])
    rejects(ns['risk_components'],ns['zero_risk_cov'],ns['zero_risk_weights'])
    checks+=['negative contribution, concentration below one, and zero-risk undefined shares are handled explicitly']
    factors=ns['factor_exposure'];factor_cov=ns['factor_cov']
    factor_parts=np.array([sum(factors[i]*factors[j]*factor_cov[i,j] for j in range(2)) for i in range(2)])
    np.testing.assert_allclose(ns['factor_parts'],factor_parts,atol=1e-15)
    np.testing.assert_allclose(ns['residual_parts'],w*w*np.diag(ns['residual_cov']),atol=1e-15)
    np.testing.assert_allclose(sum(ns['factor_breakdown']),ns['factor_model_variance'],atol=1e-15)
    np.testing.assert_allclose(ns['duplicate_shares'],[.25,.25,.5],atol=1e-15)
    np.testing.assert_allclose(ns['base_shares'],[.5,.5],atol=1e-15)
    assert np.linalg.matrix_rank(ns['duplicate_cov'])==2
    np.testing.assert_allclose(ns['duplicate_weights']@ns['duplicate_cov']@ns['duplicate_weights'],ns['base_weights']@ns['base_cov']@ns['base_weights'],atol=1e-15)
    checks+=['factor plus orthogonal residual decomposition matches asset variance',
             'splitting an identical exposure changes label concentration while preserving the investment and variance']
    for cov,weights in ((np.eye(3),w),(np.full((4,4),np.nan),w),(np.array([[1,2],[2,1]]),[.5,.5]),(covariance,[np.inf,0,0,0])):
        rejects(ns['risk_components'],cov,weights)
    checks+=['risk decomposition accepts meaningful PSD duplication and rejects invalid covariance, weights or zero risk']
    return checks


def check_parity(ns):
    np.testing.assert_allclose(ns['covariance'],COV,atol=1e-15)
    np.testing.assert_allclose(ns['risk_shares'](COV,ns['w_inverse_vol']),[.29375,.25,.18125,.275],atol=1e-14)
    np.testing.assert_allclose(np.array(ns['special_cases'])[:,1:],np.tile([1/3,2/3,.5,.5],(3,1)),atol=1e-14)
    np.testing.assert_allclose(ns['risk_shares'](ns['equal_corr_cov'],ns['w_inverse_vol']),.25,atol=1e-14)
    expected_diag=np.sqrt(ns['budget'])/VOL;expected_diag/=expected_diag.sum()
    np.testing.assert_allclose(ns['w_diagonal_budget'],expected_diag,atol=1e-14)
    checks=['inverse-volatility risk shares and two-asset/equal-correlation special cases checked analytically',
            'diagonal risk-budget weights equal normalized sqrt(budget)/volatility']
    for covariance,budget,actual in ((COV,ns['equal_budget'],ns['w_erc']),
                                     (COV,ns['budget'],ns['w_budget']),
                                     (ns['negative_cov'],ns['negative_budget'],ns['w_negative'])):
        reference=risk_budget_reference(covariance,budget)
        np.testing.assert_allclose(actual,reference,atol=1e-7)
        np.testing.assert_allclose(ns['risk_shares'](covariance,actual),budget,atol=1e-7)
        assert actual.min()>0 and abs(actual.sum()-1)<1e-12
        np.testing.assert_allclose(ns['risk_budget_weights'](covariance*10000,budget),actual,atol=1e-8)
        order=np.arange(len(actual))[::-1]
        reordered=ns['risk_budget_weights'](covariance[np.ix_(order,order)],budget[order])
        np.testing.assert_allclose(reordered,actual[order],atol=1e-7)
    checks+=['ERC and unequal positive budgets agree with independent cyclic-coordinate solutions, including negative correlations',
             'risk budgets preserve allocations across return-unit scaling and asset permutation']
    assert ns['w_erc'][2]>.44 and ns['w_capped'][2]<=.3+1e-9
    assert np.max(np.abs(ns['risk_shares'](COV,ns['w_capped'])-.25))>.01
    assert abs(ns['w_capped'].sum()-1)<1e-8 and ns['w_capped'].min()>-1e-8
    np.testing.assert_allclose(ns['scaled_weights'].sum()+ns['cash_weight'],1,atol=1e-14)
    np.testing.assert_allclose(ns['scaled_weights']@COV@ns['scaled_weights'],.2**2,atol=1e-14)
    np.testing.assert_allclose(ns['risk_shares'](COV,ns['scaled_weights']),.25,atol=1e-7)
    cash=100000*ns['cash_weight'];risky=100000*ns['scaled_weights']
    final=sum(holding*(1+r) for holding,r in zip(risky,ns['scenario_returns']))+cash*(1+.04)
    np.testing.assert_allclose(final/100000-1,ns['scenario_return'],atol=1e-14)
    np.testing.assert_allclose(ns['w_stress_erc'],ns['w_inverse_vol'],atol=1e-7)
    assert np.max(np.abs(ns['risk_shares'](ns['stress_cov'],ns['w_erc'])-.25))>.01
    checks+=['a binding asset cap fails exact ERC, while leverage preserves shares and scales model volatility',
             'borrowed-cash scenario reconciles dollar wealth; changed correlation alters old risk shares']
    for budget in (np.array([0,.3,.3,.4]),np.array([-.1,.3,.4,.4]),np.ones(4),np.array([.5,.5]),np.full(4,np.nan)):
        rejects(ns['risk_budget_weights'],COV,budget)
    for covariance in (np.eye(4)[:,:3],np.zeros((4,4)),COV+np.triu(np.ones((4,4)),1),np.full((4,4),np.inf)):
        rejects(ns['risk_budget_weights'],covariance,np.repeat(.25,4))
    checks+=['risk-budget solver rejects nonpositive/malformed budgets and invalid or singular covariance']
    return checks


def check_charts(spaces):
    metadata=json.loads((ROOT/'data/advanced-risk-budget-figures.json').read_text())
    risk=spaces['risk-contributions'];bt=spaces['diversification-backtest']
    weight=np.array([.5,.2,.2,.1]);shares=weight*(COV@weight)/.019845
    np.testing.assert_allclose(metadata['capital_risk']['capital_weight_percent'],100*weight,atol=1e-14)
    np.testing.assert_allclose(metadata['capital_risk']['relative_risk_percent'],100*shares,atol=1e-14)
    np.testing.assert_array_equal(metadata['net_wealth']['month'],np.arange(36,97))
    assert metadata['net_wealth']['cost_bps']==10
    for width,suffix in ((720,''),(400,'-mobile')):
        height=560 if width==720 else 540
        bar_width=20 if width==400 else 36
        root=ET.parse(ROOT/f'assets/charts/advanced-capital-risk{suffix}.svg').getroot()
        rects=[r for r in root.findall('{http://www.w3.org/2000/svg}rect') if 'data-series' in r.attrib]
        assert len(rects)==8
        for rect in rects:
            index=['A','B','C','D'].index(rect.attrib['data-asset'])
            capital=rect.attrib['data-series']=='capital-weight'
            value=100*(weight[index] if capital else shares[index])
            offset=-bar_width if capital else 2
            expected=[60+(index+.5)/4*(width-84)+offset,
                      height-88-value/80*(height-273),bar_width-2,value/80*(height-273)]
            np.testing.assert_allclose([float(rect.attrib[k]) for k in ('x','y','width','height')],expected,atol=5.1e-5,rtol=0)
        root=ET.parse(ROOT/f'assets/charts/advanced-diversification-net-wealth{suffix}.svg').getroot()
        lines=root.findall('{http://www.w3.org/2000/svg}polyline')
        assert len(lines)==5
        for line in lines:
            name=line.attrib['data-series'];values=np.array(metadata['net_wealth']['methods'][name])
            np.testing.assert_allclose(values,bt['net_wealth'][name],atol=1e-12)
            points=np.array([[float(v) for v in xy.split(',')] for xy in line.attrib['points'].split()])
            expected=np.column_stack([60+np.arange(61)/60*(width-84),
                                       height-88-(values-.8)/1.3*(height-273)])
            np.testing.assert_allclose(points,expected,atol=5.1e-5,rtol=0)
    return ['capital-versus-risk bars and all five net-wealth curves match analytical values, month axis and both SVG dimensions']


def check_lessons(spaces):
    return [*check_methods(spaces['diversification-methods']),
            *check_components(spaces['risk-contributions']),*check_parity(spaces['risk-parity']),
            *check_backtest(spaces['diversification-backtest']),*check_charts(spaces)]
