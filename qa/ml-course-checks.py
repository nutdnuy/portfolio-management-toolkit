"""Execute ML lessons, verify complete notebooks, and check independent numerical identities."""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

exporter = load('ml_notebooks', ROOT / 'scripts/make_course_notebooks.py')
notebook_checks = load('ml_notebook_integrity', ROOT / 'qa/advanced-course-checks.py')


def check_fundamentals(spaces):
    f = spaces['ml-foundations']
    assert len(f['labeled_data']) == 6 and len(f['known_at_cutoff']) == 3
    assert (f['known_at_cutoff'].label_known_on <= f['cutoff']).all()
    np.testing.assert_allclose(f['target_return'], [-.02,.01,-.04,.02,.01,.03])
    np.testing.assert_allclose([f['classification_accuracy'],f['expected_net_return'],f['pca_explained_fraction']], [2/3,-.005,.9])
    np.testing.assert_array_equal(f['cluster_assignments'], [0,0,1,1])
    u = spaces['supervised-learning']
    # Solve the normal equations independently of the scalar lesson and sklearn.
    design = np.column_stack([np.ones(len(u['reg_x'])),u['reg_x']])
    np.testing.assert_allclose(np.linalg.solve(design.T@design,design.T@u['reg_y']), [.002,.006])
    np.testing.assert_allclose([u['ols_intercept'],u['ols_slope']], [.002,.006])
    np.testing.assert_array_equal(u['class_confusion'], [[3,1],[0,2]])
    np.testing.assert_array_equal(u['confusion_at_eight'], [[4,0],[1,1]])
    np.testing.assert_array_equal(u['nearest_three'], [4,5,3])
    np.testing.assert_allclose(u['knn_query_probability'],2/3)
    np.testing.assert_allclose(u['linear_svm'].coef_, [[1,0]])
    v = spaces['model-validation']
    np.testing.assert_allclose(v['knn_validation_errors'], [.475,.375,.375,.325,.375,.35])
    assert v['selected_k'] == 9 and v['test_error'] == .4 and v['test_baseline_error'] == .5
    np.testing.assert_allclose(v['final_knn'][0].mean_,v['development_data'][v['feature_columns']].mean())
    np.testing.assert_allclose(v['original_probabilities'],v['perturbed_probabilities'])
    # A scalar nearest-neighbor vote on the train-only standardized geometry.
    training=v['development_data']; test=v['test_data']
    mu=training[v['feature_columns']].mean().to_numpy()
    sd=training[v['feature_columns']].std(ddof=0).to_numpy()
    x=(training[v['feature_columns']].to_numpy()-mu)/sd
    votes=[]
    for row in test[v['feature_columns']].to_numpy():
        order=np.argsort(np.sum((x-(row-mu)/sd)**2,axis=1))[:9]
        votes.append(int(training.next_positive.iloc[order].sum() >= 5))
    np.testing.assert_array_equal(votes,v['test_predictions'])
    b=spaces['ml-portfolio-lab']
    assert b['portfolio_train'].shape==(104,3) and b['portfolio_test'].shape==(52,3)
    assert np.isnan(b['weekly_from_daily'].iloc[1,1])
    np.testing.assert_allclose(b['weekly_from_daily'].iloc[0,0],np.prod(1+b['daily_returns'].A.iloc[:5])-1)
    np.testing.assert_allclose(b['msr_weights'],[0,0,1],atol=1e-6)
    # Interior GMV KKT: all marginal variances equal; budget and covariance positive.
    gradient=b['estimated_weekly_cov'] @ b['gmv_weights']
    np.testing.assert_allclose(gradient,gradient.mean(),atol=1e-9)
    assert b['gmv_weights'].min()>0 and np.linalg.eigvalsh(b['estimated_weekly_cov']).min()>0
    for name in ['EW','GMV','MSR']:
        holdings=b['chosen_weights'][name].to_numpy().copy(); path=[1.]
        for row in b['portfolio_test'].to_numpy():
            holdings=holdings*(1+row);path.append(sum(holdings))
        np.testing.assert_allclose(path,b['heldout_gross_wealth'][name])
        np.testing.assert_allclose(b['heldout_summary'].loc[name,'max_drawdown'],
                                   min(np.array(path)/np.maximum.accumulate(path)-1))
    np.testing.assert_allclose(b['net_buy_hold_ew'].iloc[-1],
                               b['heldout_gross_wealth'].EW.iloc[-1]/1.001)
    # Cash ledger reconstructed from post-period wealth and recorded fees.
    holdings=np.zeros(3); wealth=1.
    for i,row in enumerate(b['portfolio_test'].to_numpy()):
        paid=b['rebalancing_fees'][i];invested=wealth-paid
        np.testing.assert_allclose(paid,.001*np.abs(invested*b['equal_weights']-holdings).sum(),atol=1e-10)
        holdings=invested*b['equal_weights']*(1+row);wealth=sum(holdings)
        np.testing.assert_allclose(wealth,b['net_rebalanced_ew'].iloc[i+1])
    return ['feature/target availability and elementary expected-return/PCA identities',
            'OLS normal equations, hand confusion counts, KNN and linear SVM geometry',
            'chronological KNN selection, independent votes and future invariance',
            'weekly compounding, missing-observation policy and interior GMV KKT',
            'buy-and-hold scalar accounting, initial-inclusive drawdown and fee ledger']


def check_factor(spaces):
    s = spaces['factor-model-estimation']
    np.testing.assert_allclose(s['factor_alpha'], .001, atol=1e-12)
    np.testing.assert_allclose(s['factor_beta'], [.8, -.4], atol=1e-12)
    np.testing.assert_allclose([s['factor_rmse'], s['factor_total_variance']], [.003, .000281])
    np.testing.assert_allclose(s['factor_Omega'][0,1], .0000045)
    observations = s['factor_Y'].to_numpy()
    # Scalar population covariance oracle, independently of the lesson factor decomposition.
    covariance = [[sum((row[i]-observations[:,i].mean())*(row[j]-observations[:,j].mean())
                       for row in observations)/len(observations) for j in range(2)] for i in range(2)]
    np.testing.assert_allclose(s['factor_full_cov'], covariance)
    np.testing.assert_allclose(s['factor_expected_monthly'], .0042)
    np.testing.assert_allclose(s['changed_ols'].coef_, [-.2, 1], atol=1e-10)
    r = spaces['regularized-factor-models']
    np.testing.assert_allclose(r['penalty_ridge'].coef_, [.02/1.5, .007/1.5, 0], atol=1e-12)
    np.testing.assert_allclose(r['penalty_lasso'].coef_, [.015, .002, 0], atol=1e-12)
    np.testing.assert_allclose(r['penalty_elastic'].coef_, [.0175/1.0025, .0045/1.0025, 0], atol=1e-12)
    # Stationarity/KKT for each objective: intercept is unpenalized.
    z, y = r['penalty_Z'], r['penalty_y']
    for model, strength, ratio in [(r['penalty_lasso'], .005, 1), (r['penalty_elastic'], .005, .5)]:
        gradient = z.T @ (model.predict(z)-y)/len(y) + strength*(1-ratio)*model.coef_
        nonzero = np.abs(model.coef_) > 1e-10
        np.testing.assert_allclose(gradient[nonzero]+strength*ratio*np.sign(model.coef_[nonzero]), 0, atol=1e-10)
        assert np.all(np.abs(gradient[~nonzero]) <= strength*ratio+1e-10)
        np.testing.assert_allclose(np.mean(model.predict(z)-y), 0, atol=1e-12)
    np.testing.assert_allclose(r['scale_alpha']+r['scale_X'].to_numpy()@r['scale_beta'],
                               r['scale_model'].predict(r['scale_X']), atol=1e-12)
    assert r['scale_prediction_error'] < 1e-10 and r['raw_prediction_error'] > 1e-4
    assert tuple(r['subset_table'].iloc[0]['Columns']) == (0,1)
    np.testing.assert_allclose(r['subset_table'].iloc[0]['Training MSE'], .000001)
    v = spaces['factor-model-validation']
    assert len(v['development_X']) == 96 and len(v['final_X']) == 24
    assert [(len(a),len(b)) for a,b in v['validation_folds']] == [(60,12),(72,12),(84,12)]
    assert all(a[-1] < b[0] and b[-1] < 96 for a,b in v['validation_folds'])
    assert v['validation_winner'] == 'Ridge'
    assert v['validation_searches']['Ridge'].best_params_ == {'model__alpha':1.0}
    np.testing.assert_allclose(v['fold_scaler_mean'], v['development_X'].iloc[:60].mean())
    assert v['selected_pipeline'].named_steps['scale'].n_samples_seen_ == 96
    np.testing.assert_allclose(v['selected_direct'], v['selected_pipeline'].predict(v['final_X']))
    assert v['probe_coefficient_difference'] < 1e-12
    return ['factor scalar covariance decomposition and correlated residuals',
            'factor units, closed-form loadings and near-collinearity sensitivity',
            'orthogonal Ridge/Lasso/Elastic Net analytical solutions and KKT',
            'standardized model unit invariance and coefficient conversion',
            'chronological factor folds, fold-local scaler and frozen validation winner',
            'factor coefficients unchanged under final-data mutation']


def check_diversification(spaces):
    p = spaces['pca-diversification']
    np.testing.assert_allclose(p['small_variance'], .036)
    np.testing.assert_allclose(np.linalg.eigvalsh(p['small_cov']), [.008,.072])
    np.testing.assert_allclose(p['sample_cov'], np.cov(p['train'].to_numpy().T, ddof=1))
    np.testing.assert_allclose(p['eigenvectors'] @ np.diag(p['eigenvalues']) @ p['eigenvectors'].T,
                               p['sample_cov'], atol=1e-12)
    # Eckart-Young residual from singular values, independent of eigen-based code.
    singular = np.linalg.svd(p['centered'], compute_uv=False)
    np.testing.assert_allclose(p['squared_error'], np.sum(singular[p['n_components_80']:]**2))
    assert p['n_components_80'] == 4
    np.testing.assert_allclose(p['portfolio_variance'], .0001869831881911293)
    np.testing.assert_allclose(p['risk_shares'].sum(), 1)
    assert not np.allclose(p['risk_shares'], p['explained_ratio'])
    np.testing.assert_allclose(p['corr_pc_variance'].sum(), p['portfolio_variance'])
    np.testing.assert_allclose(p['pca'].components_, p['pca_again'].components_)
    c = spaces['asset-clustering']
    d = c['distance']; best = float('inf')
    for medoids in itertools.combinations(range(6),3):
        total = sum(min(float(d[i,j]) for j in medoids) for i in range(6))
        best = min(best, total)
    np.testing.assert_allclose(c['medoid_cost'], best)
    np.testing.assert_array_equal(c['medoids'], [0,2,4])
    np.testing.assert_array_equal(c['medoid_labels'], [0,0,1,1,2,2])
    np.testing.assert_array_equal(sorted(c['kmeans_representatives']), [0,2,4])
    np.testing.assert_allclose(c['full_distances'], d)
    for bad in [0,7,True,1.5]:
        try: c['exact_medoids'](d,bad)
        except ValueError: pass
        else: raise AssertionError('Invalid medoid count accepted')
    n = spaces['asset-networks']
    np.testing.assert_allclose(n['three_partial'][1,2], 0, atol=1e-12)
    np.testing.assert_allclose(n['three_corr'][1,2], .48)
    assert n['chosen_alpha'] == .02 and n['edge_counts'] == [11,7,4,0]
    # Gaussian graphical objective KKT: covariance-S = alpha*sign(precision) off-diagonal.
    delta = n['graph_model'].covariance_ - n['empirical_corr']
    np.testing.assert_allclose(np.diag(delta), 0, atol=1e-8)
    upper = np.triu_indices(6,1)
    active = np.abs(n['precision'][upper]) > 1e-8
    np.testing.assert_allclose(delta[upper][active], n['chosen_alpha']*np.sign(n['precision'][upper][active]), atol=1e-5)
    assert np.all(np.abs(delta[upper][~active]) <= n['chosen_alpha']+1e-5)
    np.testing.assert_allclose(n['precision'] @ n['graph_model'].covariance_, np.eye(6), atol=1e-5)
    assert .29 < n['relative_distance_error'] < .32
    for axis in range(2):
        vector=n['mds_vectors'][:,axis]
        assert vector[np.argmax(np.abs(vector))]>0
    np.testing.assert_allclose(n['precision'], n['repeat_model'].precision_)
    for namespace in (c,n):
        # Sequential wealth oracle and initial observation for drawdown.
        wealth = np.ones(2); paths=[wealth.copy()]
        w = np.column_stack([namespace['all_weights'],namespace['selected_weights']])
        for row in namespace['test'].to_numpy():
            wealth = wealth*(1+row@w); paths.append(wealth.copy())
        paths=np.array(paths)
        np.testing.assert_allclose(namespace['heldout_wealth'], paths)
        np.testing.assert_allclose(namespace['heldout_summary']['Max drawdown'],
                                   np.min(paths/np.maximum.accumulate(paths,axis=0)-1,axis=0))
    return ['two-asset PCA analytical variance and eigenvalues',
            'PCA reconstruction, SVD residual and scale-correct portfolio risk',
            'exact medoid enumeration, validation and cluster membership',
            'full-dimensional distances versus projected distances',
            'partial correlation with common driver and Graphical Lasso KKT',
            'graph/CV future independence and quantified embedding distortion',
            'heldout scalar wealth and nonannualized initial-inclusive drawdown']


def check_regimes(spaces):
    from scipy.stats import norm
    r=spaces['market-regimes']
    np.testing.assert_allclose(r['regime_stationary'] @ r['regime_transition'], [.7,.3])
    # Enumerate all 64 hidden paths; no recursive filter/smoother reused.
    posterior=np.zeros_like(r['regime_filtered']); evidence=0.
    for path in itertools.product(range(2),repeat=6):
        mass=r['regime_stationary'][path[0]]
        for t,state in enumerate(path):
            if t: mass*=r['regime_transition'][path[t-1],state]
            mass*=norm.pdf(r['regime_observed'][t],r['regime_mu'][state],r['regime_sd'][state])
        evidence+=mass
        for t,state in enumerate(path):posterior[t,state]+=mass
    np.testing.assert_allclose(posterior/evidence,r['regime_smoothed'])
    np.testing.assert_allclose(r['regime_filtered'][:-1],r['changed_filtered'][:-1])
    assert abs(r['regime_smoothed'][4,1]-r['changed_smoothed'][4,1])>.4
    np.testing.assert_allclose(r['trend_level'],[.048]*5+[-.06]*5+[.02]*6,atol=2e-7)
    assert 0<=r['trend_gap']<1e-7
    np.testing.assert_allclose(r['trend_y']-r['trend_D'].T@r['trend_dual'],r['trend_level'])
    assert np.max(np.abs(r['trend_dual']))<=r['trend_penalty']+1e-12
    np.testing.assert_allclose(r['fused_level'](r['trend_y'],0)[0],r['trend_y'])
    c=spaces['regime-scenarios']
    np.testing.assert_allclose(c['scenario_mean'],[.02,.027])
    np.testing.assert_allclose(c['scenario_cov'],[[.0274,.00052],[.00052,.003691]])
    second=sum(p*(cov+np.outer(mu,mu)) for p,mu,cov in zip(c['scenario_p'],c['scenario_means'],c['scenario_covs']))
    np.testing.assert_allclose(second-np.outer(c['scenario_mean'],c['scenario_mean']),c['scenario_cov'])
    # Exact probability masses in thousandths become an equal-weight independent tail oracle.
    losses=np.repeat(-c['finite_portfolio'],np.rint(1000*c['finite_p']).astype(int))
    np.testing.assert_allclose([c['finite_es95'],c['finite_es80']],
                               [np.sort(losses)[-50:].mean(),np.sort(losses)[-200:].mean()])
    assert abs(c['scenario_mc_mean_error'])<4*c['scenario_mc_se']
    e=spaces['endowment-simulation']
    np.testing.assert_allclose(e['sequence_early_gain'],[100,115,98.5])
    np.testing.assert_allclose(e['sequence_early_loss'],[100,85,97])
    np.testing.assert_array_equal(e['endowment_iid_states'],e['endowment_uniforms']>=.7)
    for name,returns in [('endowment_markov','endowment_returns'),('endowment_iid','endowment_iid_returns')]:
        result=e[name]
        # Direct real-numeraire ledger for several paths, independent of nominal bookkeeping.
        for i in [0,1,9,77,999]:
            wealth=100.
            for t,row in enumerate(e[returns][i]):
                available=wealth*(1+sum(row*e['endowment_weights']))/1.02
                paid=min(available,2.5);wealth=available-paid
                np.testing.assert_allclose(wealth,result['wealth_real'][i,t+1],atol=1e-11)
                np.testing.assert_allclose([paid,2.5-paid],
                                           [result['paid_real'][i,t],result['unpaid_real'][i,t]],atol=1e-11)
        np.testing.assert_allclose(result['paid_real']+result['unpaid_real'],2.5,atol=1e-12)
        assert result['wealth_real'].min()>=0
    np.testing.assert_allclose(e['endowment_probability'],.70315)
    np.testing.assert_allclose(e['endowment_difference_se'],
                               np.std(e['endowment_paired_difference'],ddof=1)/np.sqrt(20000))
    return ['stationary Markov probabilities and exhaustive hidden-path smoothing oracle',
            'filtering causality and retrospective smoothing revision',
            'TV analytical block levels, zero-penalty boundary and primal-dual certificate',
            'mixture covariance from second moments and exact weighted-tail ES',
            'Monte Carlo mean error against simulation SE',
            'independent real-cashflow ledger, IID state thresholds and paired simulation SE']


def check_prediction(spaces):
    p = spaces['event-probabilities']
    np.testing.assert_allclose([p['brier'],p['qps_twice_brier'],p['odds'],p['cost_threshold']],
                               [.158125,.31625,.25,.2])
    np.testing.assert_allclose(p['auc_manual'], .75)
    assert p['threshold_counts'][.5] == {'TP':1,'FP':0,'TN':2,'FN':1}
    assert p['threshold_counts'][.3] == {'TP':2,'FP':1,'TN':1,'FN':0}
    assert p['eligible'].origin.max() == 5
    assert p['label_exact'].iloc[0] == 0 and p['label_any'].iloc[0] == 1
    r = spaces['recession-models']
    data=r['data']; forecast=r['forecast']; actual=r['actual']
    assert list(data.origin[[0,len(data)-1]]) == [2,238]
    assert np.all(data.label_available-data.origin == 3)
    assert r['selected_name'] == 'Logistic' and len(forecast)==59 and sum(actual)==14
    assert data[(data.origin>=160)&(data.origin<178)].label_available.max() == 180
    np.testing.assert_array_equal(r['final_confusion'], [[44,1],[14,0]])
    np.testing.assert_allclose(r['prediction_metrics']['model_brier'], np.mean((forecast.p-actual)**2))
    for t,probability in zip(forecast.origin,forecast.baseline):
        released=data[data.origin<=t-3].target.to_numpy()
        np.testing.assert_allclose(probability, sum(released)/len(released))
    assert r['future_invariance']
    # Test exact release boundary, not only a remote future mutation.
    boundary=data.copy()
    boundary.loc[boundary.origin==178,'target'] = 1-boundary.loc[boundary.origin==178,'target']
    before=r['rolling_predict'](boundary,r['selected_estimator'],start=180,end=181)
    np.testing.assert_allclose(before.p,forecast.p.iloc[:1])
    f=spaces['feature-selection']
    assert len(f['subsets']) == 14 and f['selected_features']==['indicator_lag1']
    np.testing.assert_allclose(f['selected_test_brier'], .18186684663654, rtol=1e-5)
    assert f['selection_unchanged']
    np.testing.assert_allclose(f['redundant_x'] @ f['coefficient_a'], f['redundant_x'] @ f['coefficient_b'])
    assert np.linalg.matrix_rank(f['redundant_x'])==1
    np.testing.assert_array_equal(np.sort(np.concatenate(f['blocks'])), np.arange(58))
    np.testing.assert_allclose(f['selected_model'][0].mean_,f['training_final'][f['selected_features']].mean())
    return ['horizon target versus interval event and delayed-label eligibility',
            'hand-calculated probability scores, cost threshold and confusion matrices',
            'pairwise AUC independent of metric implementation',
            'rolling selection chronology, true baseline and release boundary',
            'future mutation invariance for probabilities and subset selection',
            'feature redundancy, block permutation coverage and train-only preprocessing']


def check_figures(spaces):
    import xml.etree.ElementTree as ET
    svg_ns={'s':'http://www.w3.org/2000/svg'}
    metadata=json.loads((ROOT/'data/ml-figures.json').read_text())
    regularized=spaces['regularized-factor-models']
    validation=spaces['model-validation']; portfolio=spaces['ml-portfolio-lab']; regime=spaces['market-regimes']
    np.testing.assert_allclose(metadata['knn_validation']['validation_error'],validation['knn_validation_errors'])
    np.testing.assert_allclose(metadata['event_forecast']['p'],spaces['recession-models']['forecast'].p)
    np.testing.assert_allclose(metadata['tv_levels']['fitted'],regime['trend_level'])
    specs=[]
    for method,key,xlim in [('ridge','ridge_path',(0,9)),('lasso','lasso_path',(0,.03))]:
        data=regularized[key]
        for col in ['F1','F2','F3']:
            np.testing.assert_allclose(metadata['factor_paths'][method.title()][col],data[col])
            specs.append(('ml-factor-'+method,col,data['lambda'],100*data[col],xlim,(-.08,2.1)))
    f=spaces['recession-models']['forecast']
    specs += [('ml-event-probabilities',name,f.origin,f[col],(180,238),(-.04,1.04))
              for name,col in [('probability','p'),('released-label-baseline','baseline')]]
    specs += [('ml-knn-validation',name,validation['k_grid'],100*validation[key],(0,26),(-2,52))
              for name,key in [('train','knn_train_errors'),('validation','knn_validation_errors')]]
    for name in ['EW','GMV','MSR','Cash']:
        values=portfolio['heldout_gross_wealth'][name]
        np.testing.assert_allclose(metadata['portfolio_wealth']['series'][name],values)
        specs.append(('ml-portfolio-heldout',name,np.arange(53),values,(0,52),(.96,1.13)))
    specs += [('ml-tv-levels','observed',np.arange(1,17),100*regime['trend_y'],(1,16),(-12,10)),
              ('ml-tv-levels','fitted-level',np.r_[1,np.repeat(np.arange(1.5,16),2),16],
               np.repeat(100*regime['trend_level'],2),(1,16),(-12,10))]
    for width,suffix,height in [(720,'',560),(400,'-mobile',540)]:
        for name,series,x,y,xlim,ylim in specs:
            svg=ET.parse(ROOT/f'assets/charts/{name}{suffix}.svg').getroot()
            points=svg.find(f'.//s:polyline[@data-series="{series}"]',svg_ns).get('points')
            actual=np.array([[float(v) for v in pair.split(',')] for pair in points.split()])
            x,y=np.asarray(x),np.asarray(y)
            assert np.all((x>=xlim[0])&(x<=xlim[1])) and np.all((y>=ylim[0])&(y<=ylim[1])),name
            expected=np.column_stack([60+(x-xlim[0])/(xlim[1]-xlim[0])*(width-84),
                                      height-88-(y-ylim[0])/(ylim[1]-ylim[0])*(height-273)])
            np.testing.assert_allclose(actual,expected,atol=.00006,rtol=0)
        svg=ET.parse(ROOT/f'assets/charts/ml-pca-risk-shares{suffix}.svg').getroot()
        for series,key in [('data-variance','explained_ratio'),('portfolio-variance','risk_shares')]:
            nodes=svg.findall(f'.//s:rect[@data-series="{series}"]',svg_ns)
            values=100*spaces['pca-diversification'][key]
            assert len(nodes)==6
            for i,node in enumerate(nodes):
                np.testing.assert_allclose(float(node.get('data-value')),values[i],rtol=1e-10)
                np.testing.assert_allclose(float(node.get('height')),values[i]/60*(height-273),atol=.00006)
        svg=ET.parse(ROOT/f'assets/charts/ml-partial-correlation{suffix}.svg').getroot()
        nodes=svg.findall('.//s:rect[@data-row]',svg_ns)
        assert len(nodes)==36
        for node in nodes:
            i='ABCDEF'.index(node.get('data-row'));j='ABCDEF'.index(node.get('data-column'))
            np.testing.assert_allclose(float(node.get('data-value')),spaces['asset-networks']['partial'][i,j],rtol=1e-9)
    return ['16 responsive calculated SVGs: saved values, all series coordinates, PCA bar heights and partial-correlation cells']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module',type=int)
    args=parser.parse_args()
    pages=exporter.course_pages('machine-learning',args.module)
    assert pages, 'No Machine Learning pages configured'
    expected={1:4,2:3,3:3,4:3,5:3}
    present=sorted({p['module'] for p in pages})
    for module in present:
        assert sorted(p['lesson'] for p in pages if p['module']==module)==list(range(1,expected[module]+1))
    spaces,report={},[]
    for page in pages:
        fresh,namespace,outputs=exporter.execute_chapter(page)
        spaces[page['file']]=namespace
        count=notebook_checks.check_notebook(page,fresh)
        assert count==len(outputs)
        report.append({'page':page['file'],'examples':count,'notebook_consistent':True})
        print(f'PASS {page["file"]}: {count} executed examples and complete notebook')
    checks=[]
    for module,check in [(1,check_fundamentals),(2,check_factor),(3,check_diversification),(4,check_regimes),(5,check_prediction)]:
        if module in present: checks.extend(check(spaces))
    if len(present)==5: checks.extend(check_figures(spaces))
    result={'course':'machine-learning','modules':present,'pages':report,
            'executed_examples':sum(p['examples'] for p in report),'independent_checks':checks}
    out=ROOT/'qa/output';out.mkdir(parents=True,exist_ok=True)
    (out/'ml-course-python-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'PASS {len(pages)} chapters; {result["executed_examples"]} examples; {len(checks)} independent check groups')

if __name__=='__main__':
    main()
