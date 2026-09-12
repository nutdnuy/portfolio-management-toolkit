"""Verify notebook execution, complete chapter capture, and Python/JS agreement."""
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("make_notebook", ROOT / "scripts/make_notebook.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
notebook = json.loads((ROOT / "notebooks/portfolio-insurance.ipynb").read_text(encoding="utf-8"))
source = (ROOT / "content/portfolio-insurance.md").read_text(encoding="utf-8")
model = (ROOT / "src/math.mjs").read_text(encoding="utf-8")
assert notebook["metadata"]["source"]["sha256"] == hashlib.sha256(source.encode()).hexdigest(), "Stale chapter copy"
assert notebook["metadata"]["source"]["model_sha256"] == hashlib.sha256(model.encode()).hexdigest(), "Stale JS model reference"
assert notebook["nbformat"] == 4 and notebook["nbformat_minor"] == 5
assert len({cell["id"] for cell in notebook["cells"]}) == len(notebook["cells"])

chapter_cells = [cell["source"] for cell in notebook["cells"] if cell["metadata"].get("toolkit_role") == "chapter"]
body = re.sub(r"\A---\n.*?\n---\n", "", source, flags=re.S)
canonical = generator.clean_markdown(body)
normalize = lambda text: re.sub(r"\s+", "", text)
assert normalize("\n\n".join(chapter_cells)) == normalize(canonical), "Some canonical prose or equations were lost"
assert not re.search(r'<(?:section|div)\b', "\n".join(chapter_cells)), "HTML wrappers remain"

namespace, svg_count = {}, 0
for cell in notebook["cells"]:
    if cell["cell_type"] != "code":
        continue
    assert isinstance(cell["execution_count"], int)
    actual_stdout, actual_svgs = io.StringIO(), []
    namespace["_portfolio_svg_capture"] = actual_svgs.append
    with contextlib.redirect_stdout(actual_stdout):
        exec(compile(cell["source"], cell["id"], "exec"), namespace)
    saved_stdout = "".join(output["text"] for output in cell["outputs"] if output["output_type"] == "stream")
    saved_svgs = [output["data"]["image/svg+xml"] for output in cell["outputs"] if output["output_type"] == "display_data"]
    assert actual_stdout.getvalue() == saved_stdout, f"Output mismatch: {cell['id']}"
    assert actual_svgs == saved_svgs, f"Chart mismatch: {cell['id']}"
    for svg in saved_svgs:
        document = ET.fromstring(svg)
        assert document.tag.endswith("svg")
        assert "<title>" in svg and "<polyline" in svg
        assert "<image" not in svg and "<script" not in svg
        svg_count += 1
assert svg_count == 2, f"Expected CPPI and put charts, got {svg_count}"

# Read-only differential check against the JavaScript used by the actual site.
cases = [dict(scenario=scenario, floorPct=floor, multiplier=multiplier, rate=rate)
         for scenario in ("rally", "crash", "whipsaw", "recovery")
         for floor, multiplier, rate in [(90, 3, 0), (80, 1, 0.04), (100, 3, 0), (70, 6, -0.01)]]
js = """import {simulate, protectivePut} from './src/math.mjs';
const cases = JSON.parse(process.argv[1]);
console.log(JSON.stringify({paths:cases.map(c=>simulate(c)), put:protectivePut()}));"""
completed = subprocess.run(["node", "--input-type=module", "-e", js, json.dumps(cases)],
                           cwd=ROOT, text=True, capture_output=True, check=True)
website = json.loads(completed.stdout)

def compare(actual, expected, path="result"):
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        assert actual == expected, (path, actual, expected)
    elif isinstance(expected, (int, float)):
        assert math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), (path, actual, expected)
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, f"{path}[{index}]")
    elif isinstance(expected, dict):
        for key, value in expected.items():
            compare(actual[key], value, f"{path}.{key}")

for case, expected in zip(cases, website["paths"]):
    actual = namespace["simulate"](scenario=case["scenario"], floor_pct=case["floorPct"],
                                   multiplier=case["multiplier"], rate=case["rate"])
    for key in ("rows", "metrics", "benchmarkMetrics", "parameters"):
        compare(actual[key], expected[key], key)
compare(namespace["protective_put"](), website["put"], "protectivePut")
print(f"Notebook passed: complete chapter capture, all cells re-executed, {svg_count} SVG charts, and {len(cases)} Python/JS path comparisons.")
