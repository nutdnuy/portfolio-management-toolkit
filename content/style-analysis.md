---
title: Style Analysis: อ่านลักษณะพอร์ตจากผลตอบแทน
description: สร้าง Benchmark ที่น้ำหนักรวมหนึ่ง แยก Tracking Error ออกจาก RMSE และตรวจ Style Drift ด้วยข้อมูลนอกตัวอย่าง
---

# Style Analysis: อ่านลักษณะพอร์ตจากผลตอบแทน

<p class="lead">ถ้ารู้เพียงผลตอบแทนรายเดือนของกองทุน เราจะหาพอร์ตดัชนีที่เคลื่อนไหวคล้ายกันได้อย่างไร?</p>

ใน[บทหลาย Factor](multifactor-models.html) เราประมาณความไวของกองทุนต่อผลตอบแทนตลาด SMB และ HML บทนี้เปลี่ยนตัวแปรอธิบายเป็นผลตอบแทนของดัชนีสินทรัพย์ แล้วกำหนดให้น้ำหนักไม่ติดลบและรวมกันเป็นหนึ่ง คำตอบจึงอ่านเป็นส่วนผสมของพอร์ตอ้างอิงได้ เช่น หุ้น Value 50% หุ้น Growth 30% และพันธบัตร 20%

การประมาณแบบนี้เรียกว่า [returns-based style analysis หรือ RBSA](glossary.html#style-analysis) ใช้ตรวจลักษณะการรับความเสี่ยงจากผลตอบแทนย้อนหลัง การจะทราบว่ากองทุนถือหลักทรัพย์ใดจริงยังต้องตรวจข้อมูล holdings เพิ่มเติม เนื้อหาส่วนนี้ประกอบ [Factor benchmarks and Style analysis](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/nPLWC/factor-benchmarks-and-style-analysis) และ [Foundations Lab](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/ZdgGw/module-1-lab-session-foundations) ของ Advanced Module 1

ตัวอย่างทั้งหมดในหน้านี้สร้างขึ้นเพื่อฝึกคำนวณ ใช้ผลตอบแทนรวมรายเดือนในหน่วยทศนิยมและสกุลเงินเดียวกัน ไม่มีค่าธรรมเนียมหรือภาษี โค้ดรันจากต้นหน้าใน Notebook ใหม่ได้ด้วย NumPy, pandas และ SciPy [ดาวน์โหลด Notebook](notebooks/style-analysis.ipynb)

<span id="style-benchmark"></span>

## เริ่มจากพอร์ตอ้างอิงสองสินทรัพย์

สมมติเดือนหนึ่งดัชนีหุ้นให้ผลตอบแทน 4% และดัชนีพันธบัตรให้ 1% ถ้าต้นเดือนแบ่งเงิน 60% ในหุ้นและ 40% ในพันธบัตร ผลตอบแทนรวมคือ

$$
R_B=0.6(0.04)+0.4(0.01)=0.028=2.8\%.
$$

ตัวห้อย $B$ หมายถึง benchmark หรือพอร์ตอ้างอิง ถ้ากองทุนได้ 3.1% ในเดือนเดียวกัน ผลตอบแทนส่วนที่เกิน benchmark คือ $3.1\%-2.8\%=0.3$ จุดเปอร์เซ็นต์ หรือ 30 basis points

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize

one_month = np.array([0.04, 0.01])
benchmark_weights = np.array([0.6, 0.4])
benchmark_return = benchmark_weights @ one_month
fund_return = 0.031
active_return = fund_return - benchmark_return
print(f"Benchmark: {benchmark_return:.2%}")
print(f"Active return: {active_return * 10000:.0f} bp")
```

เครื่องหมาย `@` คูณน้ำหนักกับผลตอบแทนตำแหน่งเดียวกันแล้วบวกผล ในเดือนเดียว เรายังบอกไม่ได้ว่ากองทุนให้ผลตอบแทนส่วนเพิ่มอย่างสม่ำเสมอหรือเพียงเกิดความต่างครั้งหนึ่ง จึงต้องใช้หลายเดือนประมาณส่วนผสมที่อธิบายการเคลื่อนไหวได้

น้ำหนักคงที่ในสมการหมายถึงพอร์ตอ้างอิงที่กลับไปใช้น้ำหนักเดิมทุกต้นงวด หากซื้อแล้วถือ น้ำหนักจะเปลี่ยนตามราคาและไม่เท่ากับส่วนผสมเดิมทุกเดือน กลับไปดู[ตัวอย่าง weight drift](portfolio-basics.html) ได้ก่อนอ่านต่อ

<span id="style-objective"></span>

## เขียนสิ่งที่ต้องการหาให้เป็นสมการ

ให้ $X_{t,j}$ เป็นผลตอบแทนรวมของดัชนีที่ $j$ ในเดือน $t$ และ $y_t$ เป็นผลตอบแทนกองทุน เราต้องการหา $w_1,\ldots,w_K$ ในสมการ

$$
y_t=a+\sum_{j=1}^{K}w_jX_{t,j}+\varepsilon_t,
\qquad w_j\geq0,\qquad\sum_{j=1}^{K}w_j=1.
$$

$w_j$ เป็นสัดส่วนใน benchmark; $a$ เป็นค่าเฉลี่ยส่วนที่แบบจำลองอธิบายไม่ได้; $\varepsilon_t$ เป็นส่วนต่างที่เหลือในแต่ละเดือนหลังหักค่าเฉลี่ยแล้ว ในขั้นประมาณ $a$ เป็นค่าคงที่ตัวหนึ่งที่ต้องหา ไม่ได้เป็นสินทรัพย์ที่สร้างผลตอบแทนแน่นอนให้ผู้ลงทุน

วิธีหนึ่งคือเลือก $a,w$ ให้ผลรวม residual ยกกำลังสองต่ำที่สุด ภายใต้ข้อจำกัดน้ำหนัก สำหรับน้ำหนักชุดหนึ่ง ค่า $a$ ที่เหมาะสมคำนวณได้จาก $\bar y-\bar X^\mathsf{T}w$ จึงลดโจทย์เหลือหาน้ำหนักจากข้อมูลที่หักค่าเฉลี่ยแล้ว:

$$
\underset{w}{\operatorname{minimize}}\;
\frac{1}{T}\sum_{t=1}^{T}
\left[(y_t-\bar y)-\sum_jw_j(X_{t,j}-\bar X_j)\right]^2.
$$

ขีดบนหมายถึงค่าเฉลี่ยของช่วงที่ใช้ประมาณ วิธีนี้ตรงกับการลด variance ของส่วนต่าง $y-Xw$ ซึ่งเป็น objective ใน [Sharpe (1992), Asset Allocation: Management Style and Performance Measurement](https://web.stanford.edu/~wfsharpe/art/sa/sa.htm) ข้อจำกัดทำให้ผลต่างไม่จำเป็นต้องตั้งฉากกับดัชนีทุกตัวเหมือน OLS ที่ไม่มีข้อจำกัด

แบบจำลองใช้ผลตอบแทนรวมของดัชนีที่ลงทุนได้ เช่น ดัชนีหุ้น Value และ Growth แยกกัน ส่วน SMB/HML ในบทก่อนเป็นผลตอบแทน long–short การบังคับ loading ของสอง factor นั้นให้ไม่ติดลบและรวมหนึ่งจะเปลี่ยนความหมายของโจทย์ ไม่ได้สร้างพอร์ต long-only ของสินทรัพย์สามชนิดตามสมการนี้

## สร้างกองทุนจำลองที่เรารู้ส่วนผสม

เพื่อให้ตรวจคำตอบได้ เราจะสร้างดัชนีสามชุดและกองทุนเอง ข้อมูลมี 32 เดือน ช่วง 16 เดือนแรกใช้ส่วนผสม 50/30/20 ส่วน 16 เดือนหลังเปลี่ยนเป็น 20/60/20 มีส่วนเพิ่มคงที่เดือนละ 0.1 จุดเปอร์เซ็นต์ และส่วนที่เหลือสลับ −0.2/+0.2 จุดเปอร์เซ็นต์

รูปแบบบวก/ลบด้านล่างออกแบบให้แยกผลของดัชนีแต่ละตัวได้ง่าย จึงไม่ใช่แบบจำลองพยากรณ์ตลาด เดือนที่เขียนกำกับเป็นเพียงป้ายเวลาของข้อมูลสมมติ

```python
s1 = np.tile([-1, 1], 8)
s2 = np.tile([-1, -1, 1, 1], 4)
s3 = np.tile([-1] * 4 + [1] * 4, 2)
s4 = np.r_[[-1] * 8, [1] * 8]

style_base = np.column_stack([
    0.006 + 0.025 * s1,
    0.007 + 0.030 * s2,
    0.002 + 0.008 * s3
])
style_X = pd.DataFrame(
    np.tile(style_base, (2, 1)),
    index=pd.period_range("2020-01", periods=32, freq="M"),
    columns=["Value", "Growth", "Bonds"]
)
style_y = pd.Series(
    np.r_[style_base @ np.array([0.5, 0.3, 0.2]),
          style_base @ np.array([0.2, 0.6, 0.2])]
    + 0.001 + np.tile(0.002 * s4, 2),
    index=style_X.index, name="Fund"
)
print(style_X.head().to_string())
print(style_y.head().to_string())
```

`np.tile` ทำซ้ำข้อมูล; `column_stack` นำสามชุดมาตั้งเป็นสามคอลัมน์; `np.r_` ต่อข้อมูลช่วงแรกกับช่วงหลัง `style_X` จึงมี 32 แถว × 3 คอลัมน์ และ `style_y` มีผลตอบแทนกองทุน 32 ค่าในเดือนตรงกัน

สมมติว่าเพิ่งผ่านเดือนที่ 16 เราจะประมาณจากข้อมูลที่มีถึงเวลานั้น แล้วเก็บเดือนที่ 17–32 ไว้ตรวจภายหลัง คำว่า train หมายถึงช่วงประมาณ และ test หมายถึงช่วงตรวจที่ยังไม่ใช้เลือกน้ำหนัก

```python
style_train = style_X.iloc[:16]
style_train_y = style_y.iloc[:16]
style_test = style_X.iloc[16:]
style_test_y = style_y.iloc[16:]
assert style_train.index[-1] < style_test.index[0]
print("Train:", style_train.index[0], "to", style_train.index[-1])
print("Test:", style_test.index[0], "to", style_test.index[-1])
```

`iloc[:16]` เลือกตำแหน่ง 0 ถึง 15 ไม่รวมตำแหน่ง 16 การตัดตรงนี้ทำให้ข้อมูลอนาคตไม่ไหลเข้าไปในการประมาณครั้งแรก

## หาน้ำหนักด้วย SciPy และตรวจว่าหาคำตอบสำเร็จ

ฟังก์ชันต่อไปนี้รับตารางดัชนี `X` และผลตอบแทนกองทุน `y` ตรวจเดือนและค่าที่ขาดหายก่อนคำนวณ หากข้อมูลไม่ผ่านจะหยุดพร้อมข้อความ เพื่อให้แก้ข้อมูลก่อนตีความผล

```python
def style_fit(X, y, center=True):
    if not X.index.equals(y.index):
        raise ValueError("Dates must match in the same order")
    if not X.index.is_unique or not X.index.is_monotonic_increasing:
        raise ValueError("Dates must be unique and increasing")
    a = X.to_numpy(dtype=float)
    b = y.to_numpy(dtype=float)
    if (len(b) <= a.shape[1] + 1 or
            not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise ValueError("Need enough finite observations")
    ac = a - a.mean(axis=0) if center else a
    bc = b - b.mean() if center else b

    objective = lambda w: 1e6 * np.mean((ac @ w - bc) ** 2)
    gradient = lambda w: 2e6 * ac.T @ (ac @ w - bc) / len(b)
    result = minimize(
        objective, np.full(a.shape[1], 1 / a.shape[1]),
        jac=gradient, method="SLSQP", bounds=[(0, 1)] * a.shape[1],
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1,
                      "jac": lambda w: np.ones_like(w)}],
        options={"ftol": 1e-12, "maxiter": 1000}
    )
    if not result.success:
        raise RuntimeError(result.message)
    w = result.x
    assert np.isclose(w.sum(), 1, atol=1e-8)
    assert (w >= -1e-8).all() and (w <= 1 + 1e-8).all()
    alpha = float((b - a @ w).mean()) if center else 0.0
    return pd.Series(w, index=X.columns), alpha
```

`center=True` หักค่าเฉลี่ยจากแต่ละคอลัมน์ก่อน fit; `a.T` สลับแถวกับคอลัมน์เพื่อคำนวณ gradient หรือความชันของ objective; `jac` ส่งความชันนี้ให้ตัวหาคำตอบ เราคูณ objective และ gradient ด้วย $10^6$ เท่ากันเพื่อไม่ให้ตัวเลขที่โปรแกรมต้องลดมีขนาดเล็กเกินไป การคูณด้วยค่าบวกคงที่ไม่เปลี่ยนน้ำหนักที่ทำให้ objective ต่ำสุด

`bounds` กำหนดทุกน้ำหนักระหว่างศูนย์กับหนึ่ง และ `constraints` บังคับผลรวมให้เท่าหนึ่ง `ftol` เป็นเกณฑ์ความละเอียดในการหยุด ไม่ใช่ระดับความเชื่อมั่นทางสถิติ ดูรูปแบบพารามิเตอร์ได้จาก [SciPy: minimize with SLSQP](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)

```python
style_w, style_alpha = style_fit(style_train, style_train_y)
print(style_w.round(6).to_string())
print(f"Residual mean: {style_alpha:.3%} per month")
print(f"Weight sum: {style_w.sum():.6f}")
```

ได้ Value 0.5, Growth 0.3, Bonds 0.2 และค่าเฉลี่ยส่วนต่าง 0.100% ต่อเดือน ตรงกับวิธีสร้างข้อมูลในช่วงแรก ความตรงนี้เกิดจากชุดฝึกที่แยกตัวแปรได้ชัดและ residual ที่ออกแบบไว้ หากใช้ข้อมูลตลาด คำตอบจะขึ้นกับดัชนี ช่วงเวลา และความคล้ายกันของแต่ละคอลัมน์ด้วย

<span id="tracking-error-conventions"></span>

## Tracking Error, RMSE และค่าเฉลี่ยส่วนต่างวัดคนละอย่าง

กำหนด active return $d_t=y_t-X_t^\mathsf{T}w$ ก่อนหัก `style_alpha` เราอาจรายงานตัวเลขสามชนิด:

| ตัววัดรายเดือน | สูตรที่ใช้ในบทนี้ | สิ่งที่อ่านได้ |
|---|---|---|
| Mean active return | $\bar d$ | กองทุนสูงหรือต่ำกว่า benchmark โดยเฉลี่ยเท่าไร |
| Tracking Error (TE) | $\sqrt{\sum_t(d_t-\bar d)^2/(T-1)}$ | ส่วนต่างแกว่งรอบค่าเฉลี่ยมากเพียงใด |
| Root Mean Squared Error (RMSE) | $\sqrt{\sum_td_t^2/T}$ | ระยะจากส่วนต่างศูนย์ รวมทั้งค่าเฉลี่ยและความแกว่ง |

```python
style_benchmark = style_train @ style_w
style_active = style_train_y - style_benchmark
style_te = style_active.std(ddof=1)
style_rmse = np.sqrt(np.mean(style_active ** 2))
print(f"Mean active: {style_active.mean():.4%}")
print(f"Monthly TE: {style_te:.4%}")
print(f"Monthly RMSE: {style_rmse:.4%}")
print("MSE identity:", np.isclose(
    style_rmse ** 2,
    style_active.var(ddof=0) + style_active.mean() ** 2
))
```

ค่าเฉลี่ยส่วนต่างคือ 0.1000%, TE คือ 0.2066% และ RMSE คือ 0.2236% ต่อเดือน ถ้ากองทุนสูงกว่า benchmark อยู่ 1% ทุกเดือน TE จะเป็นศูนย์ แต่ RMSE ยังเป็น 1% เพราะการหักค่าเฉลี่ยของ TE ลบส่วนต่างคงที่ออกแล้ว

เอกลักษณ์ $\mathrm{MSE}=\operatorname{Var}(d)+\bar d^2$ ใช้ variance แบบหารด้วย $T$ จึงระบุ `ddof=0` ในบรรทัดตรวจ ส่วน TE ที่รายงานใช้ sample SD ซึ่งหารด้วย $T-1$ ตัวอย่างนี้ยังไม่แปลง TE เป็นรายปี การคูณด้วย $\sqrt{12}$ ต้องตรวจสมมติฐานเรื่องความสัมพันธ์ของ active return ข้ามเดือนด้วย

ในไฟล์ `edhec_risk_kit_202.py` ของ [Coursera Lab](https://www.coursera.org/learn/advanced-portfolio-construction-python/ungradedLab/RqxtJ/labs-and-code) ฟังก์ชัน `tracking_error` คำนวณ $\sqrt{\sum d_t^2}$ และ `style_analysis` ลดค่านี้โดยไม่มี intercept รากของผลรวมกำลังสองกับ RMSE ให้ตัวหาค่าน้ำหนักเดียวกันเมื่อจำนวนเดือนคงที่ แต่ต่างจาก objective ที่หักค่าเฉลี่ยในตัวอย่างหลักของหน้านี้ เราจึงแสดงทั้งสองแบบให้ตรวจเทียบได้ และรายงาน TE เป็น sample SD อย่างชัดเจน

ลองปิด `center` เพื่อประมาณน้ำหนักโดยบังคับ intercept เป็นศูนย์:

```python
style_raw_w, style_raw_alpha = style_fit(
    style_train, style_train_y, center=False
)
print(pd.DataFrame({
    "Variance objective": style_w,
    "Raw MSE objective": style_raw_w
}).round(6).to_string())
print("Raw-fit intercept:", style_raw_alpha)
```

น้ำหนักแบบ raw MSE ได้ประมาณ 50.5123%, 30.4620%, 19.0256% โปรแกรมพยายามใช้ส่วนผสมของดัชนีช่วยอธิบายค่าเฉลี่ยส่วนต่างด้วย จึงเปลี่ยนน้ำหนัก แม้ข้อมูลชุดเดียวกัน การเปรียบเทียบผลจากสองโปรแกรมต้องระบุทั้ง objective และการใส่ intercept

## อ่านความสามารถในการอธิบายข้อมูลจากตัวเลขที่นิยามชัด

สำหรับ objective ที่ลด variance เรารายงาน

$$
R^2_{\mathrm{var}}=1-\frac{\operatorname{Var}(y-Xw)}{\operatorname{Var}(y)}.
$$

อีก convention หนึ่งคำนวณ $1-\mathrm{SSE}/\mathrm{SST}$ โดยใช้ residual จาก benchmark ที่ยังไม่เพิ่ม intercept ตัวเลขนี้จะลงโทษค่าเฉลี่ยส่วนต่างด้วย ในข้อมูลเดียวกันจึงได้ค่าต่างกัน

```python
style_r2_var = 1 - style_active.var(ddof=0) / style_train_y.var(ddof=0)
style_r2_zero = 1 - np.sum(style_active ** 2) / np.sum(
    (style_train_y - style_train_y.mean()) ** 2
)
print(f"Variance fit: {style_r2_var:.4f}")
print(f"SSE fit without intercept: {style_r2_zero:.4f}")
```

ได้ประมาณ 0.9836 กับ 0.9795 ตามลำดับ ทั้งสองเป็นตัวเลขของช่วงฝึก ไม่ได้บอกว่าความคลาดเคลื่อนในอนาคตจะต่ำเท่าเดิม ภายใต้ข้อจำกัดหรือในช่วงนอกตัวอย่าง ตัววัดลักษณะนี้อาจติดลบได้ และจะนิยามไม่ได้เมื่อ variance ของกองทุนเป็นศูนย์ ไม่ควรบังคับตัดค่าให้อยู่ระหว่างศูนย์กับหนึ่งเพื่อให้ดูเหมือนสัดส่วนเสมอ

<span id="style-holdout"></span>

## ใช้น้ำหนักเดิมกับเดือนที่ยังไม่เคยเห็น

น้ำหนัก `style_w` และ `style_alpha` ประมาณจาก 16 เดือนแรกทั้งหมด เราจะตรึงสองค่านี้แล้วคำนวณผลตอบแทนที่แบบจำลองอธิบายในเดือนที่ 17–32 โดยยังไม่ fit ใหม่

```python
style_train_prediction = style_train @ style_w + style_alpha
style_test_prediction = style_test @ style_w + style_alpha
style_train_error = style_train_y - style_train_prediction
style_test_error = style_test_y - style_test_prediction
print(f"Train RMSE: {np.sqrt(np.mean(style_train_error ** 2)):.4%}")
print(f"Test RMSE: {np.sqrt(np.mean(style_test_error ** 2)):.4%}")
```

RMSE เพิ่มจาก 0.2000% เป็น 1.1889% ต่อเดือน ในตัวอย่างนี้เรารู้เหตุผลจากการสร้างข้อมูล: กองทุนเปลี่ยนจาก Value 50% เป็น 20% และเพิ่ม Growth จาก 30% เป็น 60% แต่ผู้วิเคราะห์ข้อมูลจริงไม่รู้กลไกนี้ล่วงหน้า ความคลาดเคลื่อนที่เพิ่มขึ้นยังอาจเกิดจากดัชนีไม่ครอบคลุมความเสี่ยง ช่วงตลาดเปลี่ยน หรือข้อมูลผิดหน่วยได้

ค่าที่คำนวณเป็นการอธิบายกองทุนด้วยผลตอบแทนดัชนีของเดือนเดียวกัน เราต้องรอเห็นผลตอบแทนดัชนีเดือนนั้นก่อน จึงยังไม่ใช่การพยากรณ์ผลตอบแทนกองทุน ณ ต้นเดือน

<span id="style-drift"></span>

## เลื่อนหน้าต่างเพื่อดู Style Drift

Style drift หมายถึงลักษณะการลงทุนที่เปลี่ยนไป เราประมาณน้ำหนักใหม่จาก 16 เดือนล่าสุดหลังจบแต่ละเดือน แล้วเปรียบเทียบผลตามเวลา ในการใช้ benchmark กับเดือนถัดไป ต้องใช้น้ำหนักที่ fit เสร็จก่อนเดือนถัดไปเริ่ม

```python
style_rolling_rows = []
style_next_predictions = []
for end in range(16, len(style_X) + 1):
    window_X = style_X.iloc[end - 16:end]
    window_y = style_y.iloc[end - 16:end]
    w, alpha = style_fit(window_X, window_y)
    row = w.to_dict()
    row["Estimated through"] = window_X.index[-1]
    style_rolling_rows.append(row)
    if end < len(style_X):
        assert window_X.index[-1] < style_X.index[end]
        style_next_predictions.append({
            "Month": style_X.index[end],
            "Estimated through": window_X.index[-1],
            "Explained return": float(style_X.iloc[end] @ w + alpha)
        })
style_rolling = pd.DataFrame(style_rolling_rows).set_index("Estimated through")
style_next = pd.DataFrame(style_next_predictions).set_index("Month")
print(style_rolling.iloc[[0, 8, 16]].round(4).to_string())
print(style_next.head(2).to_string())
```

หน้าต่างแรกได้ 50/30/20 และหน้าต่างสุดท้ายได้ 20/60/20 หน้าต่างตรงกลางผสมข้อมูลก่อนและหลังการเปลี่ยนพฤติกรรม คำตอบจึงค่อย ๆ เคลื่อนตามจำนวนเดือนใหม่ที่เข้ามา น้ำหนักที่เปลี่ยนระหว่างหน้าต่างอาจเกิดจาก sampling error ด้วย โดยเฉพาะเมื่อจำนวนข้อมูลน้อยหรือดัชนีเคลื่อนไหวคล้ายกันมาก

<figure class="lesson-figure">
<picture>
<source media="(max-width: 600px)" srcset="assets/charts/advanced-style-drift-mobile.svg">
<img src="assets/charts/advanced-style-drift.svg" alt="น้ำหนัก Value ลดจาก 50% เป็น 20% และ Growth เพิ่มจาก 30% เป็น 60% เมื่อหน้าต่างเลื่อนผ่านจุดเปลี่ยนสไตล์ในข้อมูลสมมติ" loading="lazy" width="720" height="560">
</picture>
<figcaption>ทุกจุดประมาณจาก 16 เดือนที่จบ ณ เดือนบนแกนนอน ข้อมูลสมมติเปลี่ยนส่วนผสมหลังเดือน 16 เส้นเชื่อมค่าที่คำนวณแต่ละเดือน ไม่ใช่เส้นทางการถือครองจริงของกองทุน</figcaption>
</figure>

หน้าต่าง 16 เดือนใช้เพื่อให้เห็นการคำนวณสั้น ๆ ในข้อมูลที่สร้างไว้ ไม่ใช่คำแนะนำว่าทุกกองทุนควรใช้ 16 เดือน การเลือกหน้าต่างจากช่วงที่ทำให้ผลดูดีที่สุดแล้วรายงานช่วงเดิมเป็นผลทดสอบจะทำให้การประเมินเอนเอียง

## เมื่อดัชนีสองตัวให้ข้อมูลเหมือนกัน

สมมติเพิ่มดัชนี `Value copy` ที่ให้ผลตอบแทนเหมือน Value ทุกเดือน น้ำหนัก 50% ใน Value จะให้ benchmark เดียวกับ Value 20% และ Value copy 30% จึงไม่มีข้อมูลพอแยกว่าสองชื่อควรได้รับน้ำหนักเท่าไร

```python
style_duplicate = style_train.assign(**{"Value copy": style_train["Value"]})
style_mix_a = pd.Series([0.5, 0.3, 0.2, 0.0], index=style_duplicate.columns)
style_mix_b = pd.Series([0.2, 0.3, 0.2, 0.3], index=style_duplicate.columns)
print("Same benchmark:", np.allclose(
    style_duplicate @ style_mix_a,
    style_duplicate @ style_mix_b
))
```

ได้ `True` แม้น้ำหนักคนละชุด เมื่อดัชนีเพียงใกล้เคียงกันมากแทนที่จะเหมือนกันพอดี ปัญหาจะปรากฏเป็นน้ำหนักที่ไวต่อการขยับข้อมูลเล็กน้อย การเลือก benchmark จึงต้องดูนิยามและความซ้ำซ้อนด้วย ควรตรวจผล fit, residual และความคงที่ของน้ำหนักร่วมกัน รวมถึงเปรียบเทียบกับ mandate หรือ holdings ที่เปิดเผย

## ฝึกอ่านผลก่อนนำไปใช้

1. กองทุนมี loading ตลาด 1.3 จาก OLS นำมาใช้เป็นน้ำหนักหุ้น 130% ในแบบจำลอง long-only ของหน้านี้ได้ทันทีหรือไม่?
2. กองทุนสูงกว่า benchmark เดือนละ 0.5% เท่ากันทุกเดือน TE และ RMSE ของ active return เป็นเท่าไร?
3. ถ้าเห็นน้ำหนัก Growth เพิ่มขึ้นในการประมาณ rolling เพียงครั้งเดียว จะสรุปว่าผู้จัดการเปลี่ยน holdings แล้วได้หรือไม่?
4. ลองเปลี่ยนส่วนผสมช่วงหลังในโค้ดสร้างข้อมูลกลับเป็น 50/30/20 แล้ว Restart Kernel และ Run All คาดว่า test RMSE จะเป็นเท่าไร?

<details>
<summary>แนวคำตอบ</summary>

1. แบบจำลองหน้านี้กำหนดน้ำหนักไม่เกินหนึ่งและไม่มีเงินกู้ ค่า 1.3 ในสมการ factor เป็นความไว การสร้างพอร์ตหุ้น 130% และเงินสด −30% ต้องเพิ่มสมมติฐานเรื่องการกู้และใช้แบบจำลองที่อนุญาตก่อน
2. TE เป็นศูนย์ เพราะส่วนต่างไม่แกว่ง แต่ RMSE เป็น 0.5% ต่อเดือน
3. ยังสรุปไม่ได้ การเปลี่ยนค่าประมาณอาจเกิดจาก residual หรือความซ้ำกันของดัชนี ต้องตรวจหลายหน้าต่าง คุณภาพ fit และหลักฐาน holdings/นโยบายประกอบ
4. Test RMSE จะกลับเป็น 0.2% เพราะทั้งน้ำหนักและส่วนเพิ่มเฉลี่ยตรงกับช่วงฝึก เหลือ residual ที่สร้างให้มีขนาด ±0.2% การได้คำตอบตรงเกิดจากโครงสร้างข้อมูลสาธิต

</details>

ต่อไปอ่าน[จาก Cap Weight สู่ Smart Beta](smart-beta.html) เพื่อแยกการเลือกกลุ่มหุ้นออกจากกฎกำหนดน้ำหนัก และเริ่มทดสอบกฎเหล่านั้นโดยใช้ข้อมูลที่มีจริงก่อนแต่ละงวด
