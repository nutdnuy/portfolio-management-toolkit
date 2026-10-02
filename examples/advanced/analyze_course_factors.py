"""Analyze a locally supplied course data ZIP; no downloads or raw-data exports.

Usage: python analyze_course_factors.py /path/to/data.zip
Requires NumPy and pandas. All results are in-sample monthly OLS estimates.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd


def analyze(path):
    with ZipFile(path) as archive:
        daily_bytes = archive.read('data/brka_d_ret.csv')
        factor_bytes = archive.read('data/F-F_Research_Data_Factors_m.csv')
    daily = pd.read_csv(io.BytesIO(daily_bytes), index_col=0)
    daily.index = pd.to_datetime(daily.index, format='%Y-%m-%d')
    factors = pd.read_csv(io.BytesIO(factor_bytes), index_col=0)
    factors.columns = factors.columns.str.strip()
    factors.index = pd.to_datetime(factors.index.astype(str), format='%Y%m').to_period('M')
    factors = factors.replace([-99.99, -999], np.nan) / 100
    for frame in (daily, factors):
        if not frame.index.is_unique or not frame.index.is_monotonic_increasing:
            raise ValueError('Dates must be unique and increasing')
    if list(daily.columns) != ['BRKA'] or not np.isfinite(daily.to_numpy()).all():
        raise ValueError('Expected finite BRKA decimal daily returns')
    if (daily['BRKA'] < -1).any():
        raise ValueError('Simple asset returns cannot be below -100%')
    monthly = (1 + daily['BRKA']).groupby(daily.index.to_period('M')).prod() - 1
    expected = pd.period_range('1990-01', '2018-12', freq='M')
    sample = pd.concat([monthly.rename('BRKA'), factors], axis=1).reindex(expected)
    required = ['BRKA', 'Mkt-RF', 'SMB', 'HML', 'RF']
    if not np.isfinite(sample[required].to_numpy()).all():
        raise ValueError('The complete January 1990–December 2018 sample is required')
    y = (sample['BRKA'] - sample['RF']).to_numpy()
    report = {
        'archive_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        'files_sha256': {name: hashlib.sha256(raw).hexdigest() for name, raw in
                         [('brka_d_ret.csv', daily_bytes),
                          ('F-F_Research_Data_Factors_m.csv', factor_bytes)]},
        'sample': {'start': str(expected[0]), 'end': str(expected[-1]), 'months': len(sample)},
        'units': 'Monthly simple returns in decimals; alpha per month; beta dimensionless',
        'method': 'In-sample OLS with intercept; asset minus RF; factors already in excess/spread form',
        'models': {}
    }
    for name, columns in [('CAPM', ['Mkt-RF']), ('FF3', ['Mkt-RF', 'SMB', 'HML'])]:
        X = np.column_stack([np.ones(len(sample)), sample[columns].to_numpy()])
        coefficients, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
        if rank != X.shape[1]:
            raise ValueError('Regressors are rank deficient')
        residual = y - X @ coefficients
        np.testing.assert_allclose(X.T @ residual, 0, atol=1e-10)
        report['models'][name] = {
            'coefficients': dict(zip(['alpha'] + columns, coefficients.tolist())),
            'r_squared': float(1 - (residual @ residual) / np.sum((y - y.mean()) ** 2))
        }
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.archive), ensure_ascii=False, indent=2))
