"""Independent numerical checks for the four Module 4 lesson namespaces."""
import numpy as np
from scipy.integrate import solve_ivp


def check(spaces):
    """Return passed check names; raise AssertionError on a numerical mismatch."""
    passed = []

    def record(name, condition, value=None):
        assert condition, name
        passed.append(name)

    a=spaces['asset-liability'];b=spaces['bonds-duration'];c=spaces['interest-rate-models'];g=spaces['goal-based-allocation']
    record('Dated-liability PV independently discounted',np.isclose(a['liability_pv'],120000/1.03**2+180000/1.03**4+300000/1.03**6),float(a['liability_pv']))
    record('Funding ratio uses present-value denominator',np.isclose(a['funding_ratio'],500000/524284.45472597075),float(a['funding_ratio']))
    record('Nominal/real goal PV identity',np.isclose(a['pv_nominal_method'],300000*(1.02/1.03)**6) and np.isclose(a['pv_real_method'],a['pv_nominal_method']),float(a['pv_real_method']))
    record('Underfunded matching remains 90%',np.allclose(a['matched_assets']/a['single_liability_values'],.9))
    record('Coupon PV sum',np.isclose(b['price'],40/1.05+40/1.05**2+1040/1.05**3),float(b['price']))
    record('Yield recovery',np.isclose(b['recovered_yield'],.05))
    record('Semiannual nominal convention',np.isclose(b['price_by_years'],sum([20/1.025**j for j in range(1,7)])+1000/1.025**6),float(b['price_by_years']))
    record('Coupon total returns and terminal coupon counting',np.allclose(b['holding_returns'],.05) and np.isclose(b['terminal_with_reinvestment'],1126.1) and b['ex_coupon_prices'][-1]==0)
    h=1e-6
    pplus=b['bond_value'](b['cashflows'],.05+h);pminus=b['bond_value'](b['cashflows'],.05-h)
    fd=-(pplus-pminus)/(2*h*b['price'])
    record('Modified duration vs independent finite difference',np.isclose(fd,b['modified'],rtol=1e-8),float(fd))
    record('Market-value duration and PV match',np.isclose(b['short_weight']*2+(1-b['short_weight'])*8,5) and np.isclose(b['short_face']/1.05**2+b['long_face']/1.05**8,100000/1.05**5))
    record('Nonparallel curve twist can underfund',b['twisted_assets']/b['twisted_liability']<1,float(b['twisted_assets']/b['twisted_liability']))
    record('Feller holds but Euler can be negative',2*c['kappa']*c['theta']>=c['sigma']**2 and c['raw_euler_next']<0,float(c['raw_euler_next']))
    k,th,s,r0,T=c['kappa'],c['theta'],c['sigma'],c['r0'],c['horizon']
    dec=np.exp(-k*T)
    var=r0*s*s/k*dec*(1-dec)+th*s*s/(2*k)*(1-dec)**2
    se=np.sqrt(var/c['rates'].shape[1]);z=(c['rates'][-1].mean()-(th+(r0-th)*dec))/se
    record('Exact-transition mean within five Monte Carlo standard errors',abs(z)<5,{'mean':float(c['rates'][-1].mean()),'analytic':float(c['expected_rate_at_five']),'z':float(z)})
    record('CIR arrays nonnegative and time rows correct',c['rates'].shape==(61,2000) and np.all(c['rates']>=0) and np.allclose(c['times'],np.arange(61)/12))
    sol=solve_ivp(lambda t,x:[1-k*x[0]-.5*s*s*x[0]**2,-k*th*x[0]],(0,T),[0,0],rtol=1e-11,atol=1e-13)
    ode_price=np.exp(sol.y[1,-1]-sol.y[0,-1]*r0)
    record('CIR closed-form price against independent Riccati ODE',np.isclose(c['zc_prices'][0,0],ode_price,rtol=1e-10),float(ode_price))
    record('Zero-volatility CIR limit',np.isclose(c['cir_zcb_price'](.03,5,.4,.04,0),np.exp(-(.04*5+(.03-.04)*(1-np.exp(-.4*5))/.4))))
    record('ZCB terminal payoff and return telescoping',np.allclose(c['zc_prices'][-1],1) and np.allclose(c['terminal_growth'],1/c['zc_prices'][0]))
    record('Matched 95% funding all dates; no extra cash period',np.allclose(c['bond_funding'],.95) and np.allclose(c['cash_assets'][0],c['initial_assets']) and c['cash_assets'].shape==(61,2000))
    record('CIR coupon initial price equals sum of five ZCBs',np.isclose(c['coupon_prices'][0,0],sum((40+(1000 if j==5 else 0))*float(c['cir_zcb_price'](r0,j,k,th,s)) for j in range(1,6))),float(c['coupon_prices'][0,0]))
    record('CIR coupon final redemption counted once',np.all(c['coupon_prices'][-1]==0) and c['coupon_payments'][-1]==1040 and np.sum(c['coupon_payments'])==1200 and np.all(np.isfinite(c['coupon_returns'])))
    manual=np.zeros(2000)
    for j in [12,24,36,48,60]:
        growth=np.exp(np.sum(c['rates'][j:60]/12,axis=0))
        manual+=c['coupon_payments'][j]*growth
    record('Coupon-saving wealth agrees with independently accumulated payment tranches',np.allclose(manual,c['one_bond_total_wealth'][-1]))
    record('Fixed-mix vs buy-and-hold hand calculation',np.isclose(g['toy_rebalanced'],99.64) and np.isclose(g['toy_buy_and_hold'],99.4))
    record('Goal floor first weight based on beginning-of-period PV',np.isclose(g['dynamic_weights'][0,0],3*(1-1/1.03**5)),float(g['dynamic_weights'][0,0]))
    record('Unlevered multiplier-one matching floor',np.all(g['funded_wealth']>=g['terminal_goal']*g['goal_prices']-1e-8))
    record('Explicit gap stress 100->76 breaches 80',np.isclose(g['gap_wealth'][-1,0],76))
    stat=g['terminal_statistics'](np.array([70,90,100,140]),100)
    record('Shortfall denominator all paths vs conditional subset',stat['Breach probability']==.5 and stat['Mean deficit, all paths']==10 and stat['Mean deficit, breached paths']==20)
    none=g['terminal_statistics'](np.array([100,120]),100)
    record('No breached paths means probability zero and conditional mean undefined',none['Breach probability']==0 and np.isnan(none['Mean deficit, breached paths']))
    record('Glide endpoints and matching time dimensions',g['glide_weights'].shape==(60,2000) and np.isclose(g['glide_weights'][0,0],.8) and np.isclose(g['glide_weights'][-1,0],.2))
    record('Drawdown includes initial wealth and floors ratchet',np.all(g['running_peaks'][0]==g['initial_wealth']) and np.all(np.diff(g['drawdown_floors'],axis=0)>=0))
    eq=g['equity_metrics']
    record('Liability-friendly example isolates correlation',np.allclose(eq['Mean asset return'],.03) and np.isclose(*eq['Asset volatility'].to_numpy()) and eq['Funding-return volatility'].iloc[0]<eq['Funding-return volatility'].iloc[1])
    # Future price/return changes must not affect the first allocation.
    state=np.array([[.85],[.89],[1.]])
    psp=np.array([[.10],[-.10]])
    ghp=state[1:]/state[:-1]-1
    w1=g['wealth_with_goal_floor'](psp,ghp,state,100,100,3)[1]
    state2=state.copy();state2[1,0]=.95
    ghp2=state2[1:]/state2[:-1]-1
    w2=g['wealth_with_goal_floor'](psp,ghp2,state2,100,100,3)[1]
    record('First floor weight unaffected by future ZCB price',np.allclose(w1[0],w2[0]))
    return passed
