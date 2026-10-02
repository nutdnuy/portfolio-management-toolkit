"""Execute the chapter and independently verify its moments and tail conventions."""
import contextlib
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
from statistics import NormalDist
import sys
import tempfile

import numpy as np
import pandas as pd
import scipy
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content/extreme-risk.md"
MODULE = ROOT / "examples/extreme-risk/finance_tools.py"
sys.dont_write_bytecode = True
source = SOURCE.read_text(encoding="utf-8")
module_source = MODULE.read_text(encoding="utf-8")
blocks = re.findall(r"```python\r?\n(.*?)```", source, flags=re.S)
assert blocks, "The chapter has executable Python examples."
assert sum(block.strip() == module_source.strip() for block in blocks) == 1, (
    "Exactly one full module example must match downloadable finance_tools.py."
)

namespace = {}
execution = []
original_cwd = Path.cwd()
with tempfile.TemporaryDirectory(prefix="pmt-extreme-risk-") as directory:
    temporary = Path(directory)
    (temporary / "finance_tools.py").write_text(module_source, encoding="utf-8")
    sys.path.insert(0, directory)
    os.chdir(directory)
    try:
        for number, block in enumerate(blocks, 1):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exec(compile(block, f"extreme-risk-example-{number}", "exec"), namespace)
            execution.append({"block": number, "status": "passed", "stdout": stdout.getvalue()})
        imported = sys.modules.get("finance_tools")
        assert imported is not None, "The lesson exercises importing the separate module."
        assert Path(imported.__file__).resolve() == (temporary / "finance_tools.py").resolve()
        assert namespace["ft"] is imported, "Module examples use the imported file."
    finally:
        os.chdir(original_cwd)
        sys.path.remove(directory)


checks = []


def close(label, actual, expected):
    actual, expected = float(actual), float(expected)
    assert math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12), (label, actual, expected)
    checks.append({"name": label, "actual": actual, "expected": expected, "status": "passed"})


def rejects(label, function, *args):
    try:
        function(*args)
    except ValueError:
        checks.append({"name": label, "status": "passed", "result": "ValueError"})
    else:
        raise AssertionError(f"Expected ValueError: {label}")


def population_moments(values):
    values = list(map(float, values))
    mean = math.fsum(values) / len(values)
    centered = [value - mean for value in values]
    variance = math.fsum(value ** 2 for value in centered) / len(values)
    skew = (math.fsum(value ** 3 for value in centered) / len(values)) / variance ** 1.5
    kurt = (math.fsum(value ** 4 for value in centered) / len(values)) / variance ** 2
    return mean, math.sqrt(variance), skew, kurt


module = namespace["ft"]
for name, expected_skew, expected_kurt in [("Regular", 0, 2.2), ("LeftTail", -8 / 3, 73 / 9)]:
    values = namespace["shape_data"][name]
    mean, sd, skew, kurt = population_moments(values)
    close(f"{name}: mean", mean, 0.01)
    close(f"{name}: population SD", sd, 0.02)
    close(f"{name}: analytic skewness", skew, expected_skew)
    close(f"{name}: analytic Pearson kurtosis", kurt, expected_kurt)
    close(f"{name}: lesson mean", namespace["shape_mean"][name], mean)
    close(f"{name}: lesson population SD", namespace["shape_sd"][name], sd)
    close(f"{name}: lesson skewness", namespace["shape_skewness"][name], skew)
    close(f"{name}: lesson Pearson kurtosis", namespace["shape_kurtosis"][name], kurt)
    close(f"{name}: lesson excess kurtosis", namespace["shape_excess"][name], kurt - 3)
    close(f"{name}: module skewness", module.skewness(values), expected_skew)
    close(f"{name}: module kurtosis", module.kurtosis(values), expected_kurt)
    close(f"{name}: standardization mean", module.standardized_values(values).mean(), 0)
    close(f"{name}: standardization SD", module.standardized_values(values).std(ddof=0), 1)
    # Jarque-Bera's asymptotic reference is chi-squared with two degrees of freedom.
    jb = len(values) / 6 * (skew ** 2 + (kurt - 3) ** 2 / 4)
    result = stats.jarque_bera(values)
    close(f"{name}: Jarque-Bera statistic", result.statistic, jb)
    close(f"{name}: asymptotic JB p-value", result.pvalue, math.exp(-jb / 2))
    for shift, scale in [(0.5, 2.5), (-0.2, 0.3)]:
        transformed = np.asarray(values) * scale + shift
        close(f"{name}: affine skew {shift}", module.skewness(transformed), expected_skew)
        close(f"{name}: affine kurtosis {shift}", module.kurtosis(transformed), expected_kurt)

assert list(namespace["regular_counts"]) == [0, 1, 3, 2, 3, 1]
assert list(namespace["left_counts"]) == [1, 0, 0, 9, 0, 0]
close("Normal model: probability below minus three SD", namespace["normal_left_tail"], NormalDist().cdf(-3))
close("Normal model: probability within one SD", namespace["normal_middle"], NormalDist().cdf(1) - NormalDist().cdf(-1))
for name, sample_name, result_name in [("Normal", "normal_sample", "jb_normal"), ("Student-t", "student_sample", "jb_student")]:
    sample = namespace[sample_name]
    assert len(sample) == 5000
    _, _, sample_skew, sample_kurt = population_moments(sample)
    statistic = len(sample) / 6 * (sample_skew ** 2 + (sample_kurt - 3) ** 2 / 4)
    close(f"{name}: simulated-sample JB", namespace[result_name].statistic, statistic)
    close(f"{name}: simulated-sample p-value", namespace[result_name].pvalue, math.exp(-statistic / 2))

for number, values in enumerate([[], [1], [1, 1], [1, np.nan], [1, np.inf], [[1, 2], [3, 4]]], 1):
    rejects(f"module invalid input {number}", module.standardized_values, values)

close("LPM1 over all periods", namespace["risk_lpm1"], 0.02 / 4)
close("LPM2 over all periods", namespace["risk_lpm2"], 0.02 ** 2 / 4)
close("Target-zero downside deviation", namespace["risk_downside"], 0.01)
close("Course semideviation convention", namespace["risk_course_semi"], math.sqrt((0.03 ** 2 + 0.01 ** 2) / 2))
close("Lab negative-group SD convention", namespace["risk_lab_semi"], 0)


def reference_tail(values, confidence):
    """Integrate exact rational probability mass, independently of NumPy quantiles."""
    losses = sorted([-float(value) for value in values])
    probability = Fraction(str(confidence))
    rank = math.ceil(probability * len(losses))
    var = losses[rank - 1]
    remaining = (1 - probability) * len(losses)
    total_mass = remaining
    weighted = 0.0
    for loss in reversed(losses):
        weight = min(Fraction(1), remaining)
        if weight <= 0:
            break
        weighted += float(weight) * loss
        remaining -= weight
    return var, weighted / float(total_mass)


var_historic = namespace["var_historic"]
expected_shortfall = namespace["expected_shortfall"]
fixtures = {
    "lesson": namespace["tail_r"],
    "ties": namespace["tail_ties"],
    "all gains": [0.01, 0.02, 0.03, 0.04],
    "constant loss": [-0.03] * 20,
    "zero returns": [0] * 20,
}
for name, values in fixtures.items():
    for confidence in [0.5, 0.9, 0.925, 0.95, 0.975]:
        var, es = reference_tail(values, confidence)
        close(f"{name}: VaR {confidence}", var_historic(values, confidence), var)
        close(f"{name}: ES {confidence}", expected_shortfall(values, confidence), es)
        close(f"{name}: ES permutation {confidence}", expected_shortfall(list(reversed(values)), confidence), es)
        assert es >= var - 1e-12, f"ES includes the worst tail: {name}"
close("95% historical VaR", var_historic(namespace["tail_r"], 0.95), 0.06)
close("95% historical ES", expected_shortfall(namespace["tail_r"], 0.95), 0.12)
close("92.5% exact fractional-tail ES", expected_shortfall(namespace["tail_r"], 0.925), 0.10)
close("92.5% tied-boundary ES", expected_shortfall(namespace["tail_ties"], 0.925), 0.10)
for function in [var_historic, expected_shortfall]:
    for values in [[], [0.01, np.nan], [0.01, np.inf], [[0.01, 0.02]]]:
        rejects(f"{function.__name__}: reject invalid sample {values}", function, values)
    for confidence in [0, 1, -0.1, 95, np.nan, np.inf, [0.95]]:
        rejects(f"{function.__name__}: reject confidence {confidence}", function, [0.01, -0.02], confidence)

mu, sigma, skew, kurtosis = population_moments(namespace["tail_r"])
z = NormalDist().inv_cdf(0.05)
adjusted = z + (z * z - 1) * skew / 6 + (z ** 3 - 3 * z) * (kurtosis - 3) / 24 - (2 * z ** 3 - 5 * z) * skew ** 2 / 36
close("Gaussian mean", namespace["tail_mu"], mu)
close("Gaussian population SD", namespace["tail_sigma"], sigma)
close("Gaussian lower quantile", namespace["tail_z"], z)
close("Gaussian VaR", namespace["tail_gaussian_var"], -(mu + z * sigma))
close("Cornish-Fisher skewness", namespace["tail_skew"], skew)
close("Cornish-Fisher Pearson kurtosis", namespace["tail_kurtosis"], kurtosis)
close("Cornish-Fisher adjusted quantile", namespace["tail_z_cf"], adjusted)
close("Cornish-Fisher VaR", namespace["tail_cf_var"], -(mu + adjusted * sigma))

report = {
    "status": "passed",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "source": str(SOURCE.relative_to(ROOT)),
    "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
    "module_sha256": hashlib.sha256(module_source.encode()).hexdigest(),
    "python": sys.version,
    "libraries": {"numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__},
    "execution_mode": "Fresh namespace, source-order execution, isolated temporary module import and reload.",
    "block_count": len(blocks),
    "module_exact_sync": True,
    "checks": checks,
    "blocks": execution,
    "limitations": [
        "Package installation and the Jupyter application UI are not exercised.",
        "Jarque-Bera numeric equality verifies its formula, not asymptotic adequacy for ten observations.",
        "Hypothetical examples and formulas do not validate forecasts or a market model.",
    ],
}
report_path = ROOT / "qa/output/extreme-risk-python-report.json"
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Extreme Risk Python checks passed: {len(blocks)} executed blocks, exact module sync/import/reload, and {len(checks)} independent numerical/input checks.")
