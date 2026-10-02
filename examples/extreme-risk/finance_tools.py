"""Population-moment helpers for the hypothetical Extreme Risk lesson."""
import numpy as np


def standardized_values(data):
    """Center one finite, nonconstant series and use population SD."""
    values = np.asarray(data, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("Use one series with at least two observations.")
    if not np.isfinite(values).all():
        raise ValueError("Missing or infinite observations need review first.")
    scale = values.std(ddof=0)
    if scale == 0:
        raise ValueError("Skewness and kurtosis need nonzero dispersion.")
    return (values - values.mean()) / scale


def skewness(data):
    """Return the third standardized moment (no bias correction)."""
    z = standardized_values(data)
    return float((z ** 3).mean())


def kurtosis(data):
    """Return Pearson kurtosis; a Normal population has value 3."""
    z = standardized_values(data)
    return float((z ** 4).mean())
