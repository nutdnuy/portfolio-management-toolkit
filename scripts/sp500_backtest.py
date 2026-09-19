"""Daily-close educational S&P 500 comparison. Python standard library only.

Usage: python3 sp500_backtest.py INPUT.csv OUTPUT.json
Input columns: date,close (ISO date and positive S&P 500 price-index close).
Raw index observations are not redistributed with the public toolkit.
"""
import csv
import datetime as dt
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

METHODS = ('Buy & Hold', 'SLPI', 'CPPI', 'TIPP', 'Variable m', 'OBPI (model)')


def load_prices(filename):
    rows = []
    with open(filename, encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            date = dt.date.fromisoformat(row['date'])
            close = float(row['close'])
            if not math.isfinite(close) or close <= 0:
                raise ValueError('Prices must be finite and positive')
            if rows and date <= rows[-1][0]:
                raise ValueError('Dates must be strictly increasing, without duplicates')
            rows.append((date, close))
    if len(rows) < 260:
        raise ValueError('Need a price history including at least 252 warm-up returns')
    return rows


def volatility(rows, index, window):
    """Use returns ending strictly BEFORE this execution close; never future data."""
    if index - window < 1:
        raise ValueError('Insufficient pre-trade history')
    values = [math.log(rows[k][1] / rows[k-1][1]) for k in range(index-window, index)]
    return statistics.stdev(values) * math.sqrt(252)


def variable_multiplier(sigma):
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError('A positive finite volatility estimate is required')
    return min(6.0, max(1.0, 3.0 * 0.20 / sigma))


def call_price(spot, strike, sigma, years):
    """European Black-Scholes call, r=q=0; theoretical price, not a market quote."""
    if years <= 0:
        return max(spot - strike, 0.0)
    if sigma <= 0:
        return max(spot - strike, 0.0)
    scale = sigma * math.sqrt(years)
    d1 = (math.log(spot / strike) + .5 * sigma * sigma * years) / scale
    d2 = d1 - scale
    normal = lambda x: .5 * math.erfc(-x / math.sqrt(2))
    return spot * normal(d1) - strike * normal(d2)


def simulate_year(rows, year, floor_fraction=.90, m=3.0, vol_window=20,
                  option_sigma=None, keep_paths=False):
    in_year = [i for i, (date, _) in enumerate(rows) if date.year == year]
    if not in_year or in_year[0] == 0:
        raise ValueError('Full year and preceding year-end close required')
    start, end = in_year[0]-1, in_year[-1]
    if rows[start][0].year != year-1 or rows[end][0].month != 12:
        raise ValueError('Incomplete calendar year')
    if len(in_year) < 240:
        raise ValueError('Too few daily observations for a complete trading year')
    if not 0 < floor_fraction < 1 or m <= 0:
        raise ValueError('Invalid allocation parameters')
    floor0 = 100 * floor_fraction
    sigma0 = volatility(rows, start, 252) if option_sigma is None else option_sigma
    if not math.isfinite(sigma0) or sigma0 <= 0:
        raise ValueError('Invalid option volatility')
    horizon = (rows[end][0]-rows[start][0]).days / 365
    premium = call_price(100, 100, sigma0, horizon)
    units = (100-floor0) / premium
    states = {}
    for name in METHODS:
        mult = variable_multiplier(volatility(rows, start, vol_window)) if name == 'Variable m' else m
        exposure = 100 if name in ('Buy & Hold', 'SLPI') else min(100, mult*(100-floor0))
        states[name] = dict(value=100., peak=100., floor=floor0, exposure=exposure,
                            max_drawdown=0., min_value=100., max_shortfall=0.,
                            breached=False, stopped=False, trades=0, turnover=0.,
                            first_exit=None, path=[])
    for i in range(start+1, end+1):
        date, price = rows[i]
        daily_return = price/rows[i-1][1] - 1
        for name, state in states.items():
            risky_before = state['exposure'] * (1+daily_return)
            if name == 'OBPI (model)':
                normalized_spot = 100 * price/rows[start][1]
                years_left = (rows[end][0]-date).days/365
                state['value'] = floor0 + units*call_price(normalized_spot, 100, sigma0, years_left)
            else:
                state['value'] += state['exposure'] * daily_return
            state['peak'] = max(state['peak'], state['value'])
            if name == 'TIPP':
                state['floor'] = max(state['floor'], floor_fraction*state['peak'])
            shortfall = max(0., state['floor']-state['value'])
            state['max_shortfall'] = max(state['max_shortfall'], shortfall)
            state['breached'] |= shortfall > 1e-8
            state['min_value'] = min(state['min_value'], state['value'])
            state['max_drawdown'] = max(state['max_drawdown'], 100*(1-state['value']/state['peak']))
            target = risky_before
            if name == 'SLPI':
                state['stopped'] |= state['value'] <= floor0
                if state['stopped']:
                    target = 0.
            elif name in ('CPPI', 'TIPP', 'Variable m'):
                mult = variable_multiplier(volatility(rows, i, vol_window)) if name == 'Variable m' else m
                target = min(state['value'], max(0., mult*(state['value']-state['floor'])))
            # No unnecessary terminal trade. Metrics use wealth before a zero-cost exchange.
            if i < end and name != 'OBPI (model)':
                amount = abs(target-risky_before)
                if amount > 1e-8:
                    state['trades'] += 1
                    state['turnover'] += amount
                if target <= 1e-8 and state['first_exit'] is None:
                    state['first_exit'] = date.isoformat()
                state['exposure'] = target
            if keep_paths:
                state['path'].append((date.isoformat(), state['value'], state['floor'], target))
    results = []
    for name, state in states.items():
        result = dict(year=year, method=name, start=rows[start][0].isoformat(),
                      end=rows[end][0].isoformat(), days=len(in_year),
                      final=state['value'], return_pct=state['value']-100,
                      max_drawdown_pct=state['max_drawdown'], min_value=state['min_value'],
                      floor_breached=state['breached'], max_shortfall=state['max_shortfall'],
                      first_exit=state['first_exit'], rebalance_count=state['trades'],
                      risky_turnover=state['turnover'] if name != 'OBPI (model)' else None)
        if name == 'OBPI (model)':
            result.update(option_sigma=sigma0, call_premium=premium, call_units=units)
        if keep_paths:
            result['path'] = state['path']
        results.append(result)
    return results


def run(rows):
    annual = [result for year in range(2018, 2026) for result in simulate_year(rows, year)]
    summary = []
    for method in METHODS:
        group = [r for r in annual if r['method'] == method]
        summary.append(dict(method=method,
            mean_annual_return_pct=statistics.mean(r['return_pct'] for r in group),
            worst_within_year_drawdown_pct=max(r['max_drawdown_pct'] for r in group),
            floor_breach_years=sum(r['floor_breached'] for r in group),
            exit_years=sum(r['first_exit'] is not None for r in group),
            mean_rebalance_count=statistics.mean(r['rebalance_count'] for r in group)))
    sensitivity = []
    for year in (2020, 2022, 2023):
        for sigma in (.15, .20, .30):
            result = simulate_year(rows, year, option_sigma=sigma)[-1]
            sensitivity.append({k:result[k] for k in ('year','method','return_pct','option_sigma','call_premium','call_units')})
    return dict(annual=annual, summary=summary, obpi_sensitivity=sensitivity)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    source, destination = map(Path, sys.argv[1:])
    prices = load_prices(source)
    results = run(prices)
    results['engine_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    results['source'] = dict(provider='S&P Dow Jones Indices via FRED, SP500',
        url='https://fred.stlouisfed.org/series/SP500', retrieved='2026-09-19',
        sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        first=prices[0][0].isoformat(), last=prices[-1][0].isoformat(), observations=len(prices),
        measure='Daily close price index, no dividends; input kept local')
    results['assumptions'] = dict(years=list(range(2018,2026)), initial=100, floor=90,
        reset='Each calendar year independently; previous year final trading close to current year final close',
        safe_rate=0, costs=0, dividends=False, constant_m=3, variable_vol_window=20,
        signal_lag='All volatility estimates end one trading close before execution',
        variable_rule='clamp(3*0.20/annualized_sample_log_return_volatility,1,6)',
        execution='Idealized observed closing prices; no intraday stop fills; fractional holdings',
        obpi='Reserve 90 + European ATM calls, r=q=0; start trailing 252-return volatility fixed through expiry; theoretical premiums and marks, not traded option history')
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')
    for r in results['summary']:
        print(r)
