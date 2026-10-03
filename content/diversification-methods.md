---
title: "Diversification: กระจายเงินด้วยวิธีใด"
description: "เปรียบเทียบ Cap Weight, Equal Weight, GMV, ข้อจำกัด ENC, Maximum Decorrelation และ Maximum Diversification ด้วยสินทรัพย์สมมติชุดเดียวกัน พร้อม Python และแบบฝึกหัด"
---

# Diversification: กระจายเงินด้วยวิธีใด

<p class="lead">เมื่อใช้สินทรัพย์และ covariance ชุดเดียวกัน GMV, Maximum Decorrelation และ Maximum Diversification จะให้น้ำหนักต่างกันอย่างไร บทนี้เปรียบเทียบทั้งสามวิธีกับ CW/EW และเพิ่มข้อจำกัด ENC เพื่อดูต้นทุนของการบังคับให้เงินกระจายมากขึ้น</p>

เราจะใช้หุ้นสมมติ A, B, C และ D ตั้งแต่วิธีที่ใช้เพียงมูลค่าตลาด ไปจนถึงวิธีที่ใช้ [covariance](glossary.html#covariance) เพื่อเลือกน้ำหนัก ตัวเลขราคา จำนวนหุ้น และความเสี่ยงทั้งหมดสร้างขึ้นเพื่ออธิบายวิธีคำนวณ ไม่ใช่ข้อมูลบริษัทหรือผลทดสอบกลยุทธ์ในตลาด

โค้ดใช้ NumPy และ SciPy รันเรียงจากบนลงล่างได้โดยไม่ต้องดาวน์โหลดข้อมูล หากยังไม่คุ้นกับน้ำหนักพอร์ตและเครื่องหมาย `@` ให้ทบทวน [เริ่มจัดพอร์ตจากสินทรัพย์สองตัว](portfolio-basics.html) ก่อน ส่วน [บท Expected Return](expected-return-estimation.html) อธิบายว่าทำไมค่าประมาณผลตอบแทนเฉลี่ยจึงทำให้พอร์ตเปลี่ยนมากได้ บทนี้จะเลือกเกณฑ์ที่ไม่ต้องป้อน expected return แต่ยังต้องตรวจข้อสมมติของข้อมูลความเสี่ยงที่ใช้

<span id="จากจำนวนเง-นส-น-ำหน-กพอร-ต"></span>

<span id="capital-weights"></span>

## เตรียม CW และ EW เป็นพอร์ตอ้างอิง

ใช้กฎ [Cap Weight และ Equal Weight จากบท Smart Beta](smart-beta.html#cap-and-equal-weights) กับข้อมูลสมมติชุดใหม่ A–D: CW แบ่งตามมูลค่าตลาด ส่วน EW ลงเงินตัวละ $1/4$ ราคามีหน่วยบาทต่อหุ้นและจำนวนหุ้นมีหน่วยล้านหุ้น ผลคูณจึงเป็นมูลค่าตลาดหน่วยล้านบาท

`np.array` เก็บตัวเลขตามลำดับ A–D, `*` คูณตามตำแหน่ง และ `.sum()` รวมมูลค่าทั้งหมด ส่วน `np.full` สร้างน้ำหนักเท่ากัน และ `np.round` ปัดเฉพาะตอนแสดงผล

```python
import numpy as np

asset_names = np.array(["A", "B", "C", "D"])
prices = np.array([70.0, 20.0, 10.0, 50.0])
shares_million = np.array([10.0, 5.0, 10.0, 2.0])
market_caps_million = prices * shares_million
cap_weights = market_caps_million / market_caps_million.sum()
equal_weights = np.full(len(asset_names), 1 / len(asset_names))
print("Market caps (million baht):", market_caps_million)
print("CW weights (%):", np.round(100 * cap_weights, 2))
print("EW weights (%):", np.round(100 * equal_weights, 2))
```

ได้มูลค่าตลาด `[700, 100, 100, 100]` ล้านบาท, CW `[70, 10, 10, 10]`% และ EW `[25, 25, 25, 25]`% มูลค่าตลาดรวม 1,000 ล้านบาทเป็นขนาดจักรวาลลงทุน แยกจากเงินผู้ลงทุน 1,000,000 บาทที่จะใช้ทดลองการซื้อขาย โดยสมมติให้ซื้อหุ้นเป็นเศษส่วนและไม่มีขนาดรายการขั้นต่ำ

การเปรียบเทียบหลักใช้ long-only $w_i\geq0$ และลงทุนเต็มงบ $\sum_iw_i=1$ ทุกวิธี ดัชนีจริงอาจปรับจำนวนหุ้นตาม free float และมีกฎจำกัดน้ำหนักเพิ่มเติม ตาม [S&P DJI: Methodology Matters](https://www.spglobal.com/spdji/en/research-insights/index-literacy/methodology-matters/)

<span id="enc-แปลงความกระจ-กต-วเป-นจำนวนส-นทร-พย-เท-ยบเท-า"></span>

<span id="effective-number"></span>

## เตรียม ENC สำหรับตรวจและจำกัดการกระจุกตัว

ใช้ [จำนวนสินทรัพย์เทียบเท่าจากน้ำหนัก](smart-beta.html#concentration-and-risk) หรือ ENC $=1/\sum_iw_i^2$ เพื่อเปรียบเทียบพอร์ต และจะนำไปเป็นข้อจำกัดของ GMV ในช่วงถัดไป ฟังก์ชันรับ array หนึ่งมิติ ตรวจค่าจำกัด น้ำหนักไม่ติดลบ และผลรวมหนึ่งด้วย `np.isclose` ส่วน `w @ w` ให้ผลรวมกำลังสองน้ำหนัก หากข้อมูลผิดเงื่อนไข `raise ValueError` จะหยุดโดยไม่ปรับน้ำหนักแทนให้

```python
def effective_number(weights):
    w = np.asarray(weights, dtype=float)
    if w.ndim != 1 or not np.all(np.isfinite(w)):
        raise ValueError("Weights must be a finite one-dimensional array.")
    if np.any(w < 0) or not np.isclose(w.sum(), 1):
        raise ValueError("Use nonnegative weights that sum to one.")
    return 1 / (w @ w)

print(f"CW ENC: {effective_number(cap_weights):.4f}")
print(f"EW ENC: {effective_number(equal_weights):.4f}")
print(f"One holding ENC: {effective_number([1.0]):.4f}")
print(f"Two equal labels ENC: {effective_number([0.5, 0.5]):.4f}")
```

ผลสี่บรรทัดคือ 1.9231, 4, 1 และ 2 ตามลำดับ สำหรับ long-only ที่ลงทุนเต็มงบ ENC อยู่ระหว่าง 1 กับ $N$ แต่การแยกกองทุนที่ถือสินทรัพย์เหมือนกันทุกอย่างเป็นสองชื่อทำให้ ENC เพิ่มจาก 1 เป็น 2 ได้โดยไม่เปลี่ยนผลตอบแทนพอร์ต จึงต้องกำหนดหน่วยของสินทรัพย์และตรวจการถือซ้ำด้วย

เงื่อนไข long-only เป็นส่วนหนึ่งของการตีความ หากแทนน้ำหนัก `[2, -1]` ในสูตรดิบจะได้ 0.2 ซึ่งอยู่นอกความหมายจำนวนสินทรัพย์เทียบเท่าที่ใช้ในบทนี้

<span id="money-and-risk"></span>

## น้ำหนักเท่ากัน แต่ความเสี่ยงเปลี่ยนตามความสัมพันธ์

กำหนด annual volatility ของ A–D เท่ากับ 20%, 15%, 10% และ 25% ตามลำดับ และให้ correlation เป็นตารางต่อไปนี้ ตัวเลขทั้งหมดเป็นพารามิเตอร์สมมติของผลตอบแทนหนึ่งปี จึงไม่ต้องนำไปคูณหรือหารด้วย 12 อีก

$$
\sigma=\begin{bmatrix}0.20&0.15&0.10&0.25\end{bmatrix}^{\mathsf T},
\qquad
\rho=\begin{bmatrix}
1&0.50&0.20&0.65\\
0.50&1&0.10&0.40\\
0.20&0.10&1&0.15\\
0.65&0.40&0.15&1
\end{bmatrix}.
$$

Correlation ไม่มีหน่วย เช่น A กับ D มีค่า 0.65 ส่วน covariance ของคู่นี้คือ $\Sigma_{AD}=\sigma_A\sigma_D\rho_{AD}=0.20(0.25)(0.65)=0.0325$ ถ้าใช้ผลตอบแทนทศนิยม covariance ก็อยู่ในหน่วยทศนิยมยกกำลังสองของผลตอบแทนหนึ่งปี

ความผันผวนพอร์ตคำนวณจาก

$$
\sigma_p=\sqrt{w^{\mathsf T}\Sigma w},
\qquad \Sigma_{ij}=\sigma_i\sigma_j\rho_{ij}.
$$

`np.outer(annual_vols, annual_vols)` สร้างตารางที่ช่อง $i,j$ เป็น $\sigma_i\sigma_j$ แล้ว `* correlation` คูณแต่ละช่องด้วย correlation คู่นั้น `np.diag` เมื่อรับ array หนึ่งมิติจะสร้างเมทริกซ์แนวทแยง ส่วน `np.linalg.eigvalsh` คืน eigenvalues ของเมทริกซ์สมมาตร เราใช้ตรวจว่า covariance ที่กำหนดเป็น positive definite ตามนิยามใน [บท covariance](covariance-estimation.html)

```python
annual_vols = np.array([0.20, 0.15, 0.10, 0.25])
correlation = np.array([
    [1.00, 0.50, 0.20, 0.65],
    [0.50, 1.00, 0.10, 0.40],
    [0.20, 0.10, 1.00, 0.15],
    [0.65, 0.40, 0.15, 1.00],
])
covariance = np.outer(annual_vols, annual_vols) * correlation

def portfolio_sd(weights, matrix):
    return np.sqrt(weights @ matrix @ weights)

print("Covariance eigenvalues:", np.round(np.linalg.eigvalsh(covariance), 6))
for label, matrix in [
    ("Zero correlations", np.diag(annual_vols ** 2)),
    ("Specified correlations", covariance),
    ("All correlations one", np.outer(annual_vols, annual_vols)),
]:
    print(label, f"EW annual SD = {portfolio_sd(equal_weights, matrix):.4%}")
```

Eigenvalues ของ covariance ชุดหลักประมาณ `[0.009421, 0.013293, 0.019948, 0.092338]` เป็นบวกทั้งหมด ส่วน EW มี SD ต่อปีต่างกันตามสามกรณี:

| Correlation ที่สมมติ | ENC | SD พอร์ตต่อปี |
|---|---:|---:|
| ทุกคู่นอกแนวทแยงเป็นศูนย์ | 4 | 9.1856% |
| ตารางที่กำหนด | 4 | 13.1933% |
| ทุกคู่เท่ากับหนึ่ง | 4 | 17.5000% |

ในกรณี correlation เท่ากับหนึ่ง ความผันผวนพอร์ตเท่ากับค่าเฉลี่ยถ่วงน้ำหนักของความผันผวนรายตัว คือ $0.25(20+15+10+25)=17.5$% เมื่อ correlation ต่ำลง สมาชิกบางตัวช่วยลดการแกว่งร่วมกันได้ แม้รายชื่อและน้ำหนักทุกตัวเหมือนเดิม ค่า correlation เป็นศูนย์เพียงอย่างเดียวยังไม่ยืนยันว่าผลตอบแทนเป็นอิสระต่อกัน

Covariance กรณีทุก correlation เท่ากับหนึ่งเป็นเมทริกซ์ singular เราคำนวณ $w^{\mathsf T}\Sigma w$ ได้ตามปกติเพราะไม่ได้หา inverse แต่จะนำเมทริกซ์นี้ไปใช้สูตรที่ต้องมี inverse โดยไม่ตรวจเงื่อนไขไม่ได้

<span id="เม-อราคาขย-บ-น-ำหน-กก-ขย-บ"></span>

<span id="weight-drift"></span>

## ตรวจน้ำหนักก่อนปรับพอร์ตและยอดซื้อขาย

ใช้ [สูตร weight drift](smart-beta.html#weight-drift) กับผลตอบแทนหนึ่งช่วงของ A–D ที่ 10%, −5%, 2% และ −8% กำหนดว่าไม่มีปันผลหรือเงินจ่ายออก จำนวนหุ้นบริษัทคงที่ สมาชิกจักรวาลเดิม ไม่มีเงินฝากถอนและไม่มีต้นทุน จึงใช้ total return อัปเดตทั้งมูลค่าที่ถือและ market cap ได้ตรงกัน

เราจะตรวจว่าพอร์ตที่เริ่มตรง CW ยังตรงกับ CW ใหม่หลังราคาเปลี่ยน แล้วคำนวณเงินซื้อขายเพื่อกลับไป EW สำหรับเงินต้น 1,000,000 บาท `equal_rebalance_trades` เป็นบวกเมื่อซื้อและลบเมื่อขาย ส่วน `np.abs` ใช้ขนาดโดยไม่สนเครื่องหมาย

```python
one_period_returns = np.array([0.10, -0.05, 0.02, -0.08])
cap_drift = cap_weights * (1 + one_period_returns) / (1 + cap_weights @ one_period_returns)
equal_drift = equal_weights * (1 + one_period_returns) / (1 + equal_weights @ one_period_returns)
new_market_caps = prices * (1 + one_period_returns) * shares_million
new_cap_weights = new_market_caps / new_market_caps.sum()
initial_wealth = 1_000_000.0
equal_end_positions = initial_wealth * equal_weights * (1 + one_period_returns)
equal_end_wealth = equal_end_positions.sum()
equal_rebalance_trades = equal_end_wealth * equal_weights - equal_end_positions
equal_one_way_turnover = np.abs(equal_weights - equal_drift).sum() / 2
print("CW drift matches new CW:", np.allclose(cap_drift, new_cap_weights))
print("EW drift weights (%):", np.round(100 * equal_drift, 4))
print("EW rebalance trades (baht):", equal_rebalance_trades)
print(f"One-way turnover: {equal_one_way_turnover:.4%}")
```

`np.allclose` ให้ผล `True` ว่า CW หลัง drift ตรงกับ CW ใหม่ ส่วน EW เปลี่ยนเป็น `[27.5689, 23.8095, 25.5639, 23.0576]`% และเหลือเงิน 997,500 บาท เป้าหมาย EW รอบใหม่จึงเป็นตัวละ 249,375 บาท:

| หุ้น | มูลค่าก่อนปรับ (บาท) | ซื้อเพิ่ม / ขายออก (บาท) |
|---|---:|---:|
| A | 275,000 | −25,625 |
| B | 237,500 | +11,875 |
| C | 255,000 | −5,625 |
| D | 230,000 | +19,375 |

ยอดซื้อและขายด้านละ 31,250 บาท ทำให้ one-way turnover เท่ากับ $31{,}250/997{,}500\approx3.1328$% หากคิดค่าธรรมเนียมทั้งซื้อและขาย ต้องใช้ฐานสองด้านตาม [นิยามต้นทุนใน Smart Beta](smart-beta.html#turnover-and-cost) ตัวอย่างนี้ยังไม่หักค่าธรรมเนียม และข้อสรุป CW ไม่ต้องซื้อขายอาศัยสมมติฐานราคาเปลี่ยนอย่างเดียวที่ระบุไว้

<span id="gmv-unconstrained"></span>

## GMV เลือกน้ำหนักให้ variance ต่ำที่สุด

Global minimum variance หรือ GMV เลือก $w$ ให้ $w^{\mathsf T}\Sigma w$ ต่ำที่สุดภายใต้ข้อจำกัดที่กำหนด เนื่องจากการถอดรากเพิ่มตามค่าที่ไม่ติดลบ การทำให้ variance ต่ำที่สุดจึงทำให้ SD ต่ำที่สุดด้วย

ในโจทย์นี้เราป้อน covariance โดยไม่มี expected return จึงไม่ได้กำหนดว่าทุกสินทรัพย์ต้องมีผลตอบแทนคาดหวังเท่ากัน การสมมติ equal positive expected excess returns เป็นเงื่อนไขหนึ่งที่ทำให้ MSR ตรงกับ GMV ดังที่อธิบายใน [บท Expected Return](expected-return-estimation.html) แต่การนิยามโจทย์ GMV เองไม่ต้องสมมติค่าเฉลี่ย

เริ่มจากปัญหาที่มีเพียงข้อจำกัดลงทุนเต็มงบและยังอนุญาตน้ำหนักติดลบ หาก $\Sigma$ เป็น positive definite จะได้คำตอบ

$$
w^{\mathrm{GMV}}=\frac{\Sigma^{-1}\mathbf1}{\mathbf1^{\mathsf T}\Sigma^{-1}\mathbf1},
$$

โดย $\mathbf1$ คือ vector ที่ทุกตำแหน่งเป็นหนึ่ง ตัวเศษให้น้ำหนักก่อนปรับสเกล และตัวหารทำให้ผลรวมน้ำหนักเท่ากับหนึ่ง เราไม่ต้องสร้าง inverse ขึ้นมาจริง ๆ: `np.linalg.solve(covariance, ones)` แก้สมการ $\Sigma x=\mathbf1$ แล้วนำ $x$ มาหารด้วยผลรวม

```python
ones = np.ones(len(asset_names))
gmv_raw = np.linalg.solve(covariance, ones)
gmv_unconstrained = gmv_raw / gmv_raw.sum()
print("GMV with budget constraint only (%):", np.round(100 * gmv_unconstrained, 4))
print(f"Annual SD: {portfolio_sd(gmv_unconstrained, covariance):.4%}")
print("All weights nonnegative:", np.all(gmv_unconstrained >= 0))
```

น้ำหนักที่ได้ประมาณ `[0.7343, 27.8110, 70.6822, 0.7726]`% และ SD 8.6855% ต่อปี ในข้อมูลชุดนี้คำตอบทุกตัวเป็นบวกอยู่แล้ว จึงยังทำตามเงื่อนไข long-only ได้ คำตอบจาก covariance ชุดอื่นอาจมีน้ำหนักติดลบ ซึ่งแปลว่าขายชอร์ตสินทรัพย์นั้น

เราไม่แก้ปัญหาขายชอร์ตด้วยการตัดน้ำหนักลบเป็นศูนย์แล้วหารใหม่ เพราะน้ำหนักที่เหลืออาจไม่ใช่คำตอบที่ดีที่สุดภายใต้ข้อจำกัดใหม่ ต้องแก้โจทย์ที่ใส่ข้อจำกัดนั้นตั้งแต่ต้น ส่วนสูตรข้างต้นต้องมี covariance ที่ invertible ตามเงื่อนไขของ [`np.linalg.solve`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html)

<span id="long-only-gmv"></span>

## ระบุข้อจำกัดก่อนเรียกตัวแก้โจทย์

สำหรับพอร์ต long-only เราแก้ปัญหา

$$
\min_w w^{\mathsf T}\Sigma w
\quad\text{ภายใต้}\quad
\sum_iw_i=1,\quad 0\leq w_i\leq1.
$$

ขอบบนหนึ่งเป็นผลตามมาของน้ำหนักไม่ติดลบและผลรวมหนึ่ง เราใส่ไว้ในโค้ดเพื่ออ่านขอบเขตแต่ละตัวได้ตรง ๆ ปัญหานี้เป็น convex quadratic optimization เมื่อ covariance เป็น positive semidefinite และ covariance ที่กำหนดในบทเป็น positive definite จึงมีคำตอบ GMV เดียวบนชุดข้อจำกัดนี้

เราจะเขียนฟังก์ชันเดียวให้รองรับข้อจำกัด ENC ที่จะใช้ในหัวข้อถัดไปด้วย `min_enc=None` หมายถึงยังไม่กำหนด ENC ขั้นต่ำ ถ้าให้ค่า $K$ เราเพิ่มเงื่อนไข $\sum_iw_i^2\leq1/K$ ซึ่งมาจากการจัดรูป $\operatorname{ENC}(w)\geq K$

ใน `minimize`, `fun` คือค่าที่ต้องการลด, `x0` คือน้ำหนักเริ่มต้น, `bounds` คือช่วงของน้ำหนักแต่ละตัว และ `constraints` คือเงื่อนไขส่วนรวม `lambda w: ...` สร้างฟังก์ชันสั้นที่รับน้ำหนักแล้วคืนค่าด้านขวา เงื่อนไข `eq` ต้องคืนศูนย์ ส่วน `ineq` ต้องคืนค่ามากกว่าหรือเท่ากับศูนย์ `jac` ให้ความชันแก่ตัวแก้โจทย์ โดยความชันของ $w^{\mathsf T}\Sigma w$ คือ $2\Sigma w$

```python
from scipy.optimize import minimize

def solve_min_variance(matrix, min_enc=None):
    n = len(matrix)
    if min_enc is not None and not 1 <= min_enc <= n:
        raise ValueError("The ENC target must lie between 1 and N.")
    if min_enc == n:
        return np.full(n, 1 / n)
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1,
                    "jac": lambda w: np.ones(n)}]
    if min_enc is not None:
        constraints.append({"type": "ineq", "fun": lambda w: 1 / min_enc - w @ w,
                            "jac": lambda w: -2 * w})
    result = minimize(
        lambda w: w @ matrix @ w, np.full(n, 1 / n),
        jac=lambda w: 2 * matrix @ w, method="SLSQP",
        bounds=[(0, 1)] * n, constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(result.message)
    w = result.x
    if abs(w.sum() - 1) > 1e-8 or np.any(w < 0):
        raise RuntimeError("The returned weights violate the portfolio constraints.")
    if min_enc is not None and w @ w > 1 / min_enc + 1e-8:
        raise RuntimeError("The returned weights violate the ENC constraint.")
    return w

gmv_weights = solve_min_variance(covariance)
print("Long-only GMV weights (%):", np.round(100 * gmv_weights, 4))
print(f"GMV ENC: {effective_number(gmv_weights):.4f}")
print("Agrees with formula:", np.allclose(gmv_weights, gmv_unconstrained, atol=2e-6))
```

ฟังก์ชันใช้ SLSQP ของ SciPy เป็นตัวแก้โจทย์เชิงตัวเลข `ftol` เป็นเกณฑ์ความละเอียดในการหยุด และ `maxiter` จำกัดจำนวนรอบ `result.success` บอกสถานะการจบ ส่วน `result.x` เก็บน้ำหนัก เราตรวจเงื่อนไขอีกครั้งก่อนคืนผล ไม่เปลี่ยน covariance หรือปรับน้ำหนักเมื่อพบปัญหา รายละเอียดสถานะและเกณฑ์หยุดอยู่ใน [เอกสาร SLSQP](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)

ตัวอย่างนี้เรียกฟังก์ชันด้วยเมทริกซ์ covariance หรือ correlation ที่ตรวจแล้ว ฟังก์ชันยังไม่ได้เป็นเครื่องมือตรวจความถูกต้องของข้อมูลทั่วไป เช่น สลับลำดับสินทรัพย์ผิดหรือป้อนเมทริกซ์ที่ไม่สมมาตร หากนำไปใช้กับข้อมูลใหม่ต้องตรวจข้อมูลเหล่านั้นก่อน

น้ำหนักตรงกับสูตร GMV ภายในความละเอียดที่ตรวจ และ ENC ประมาณ 1.7329 ต่ำกว่า CW ที่มี ENC 1.9231 แม้ SD ของ GMV ต่ำกว่ามาก C มี volatility ต่ำที่สุดและ correlation ค่อนข้างต่ำกับตัวอื่นจึงได้รับน้ำหนักสูงในตัวอย่างนี้ อย่างไรก็ตาม GMV อาจถือสินทรัพย์ที่ volatility สูงได้ ถ้าความสัมพันธ์กับส่วนอื่นช่วยลด variance รวม การพิจารณา volatility ทีละตัวจึงใช้แทน covariance ทั้งตารางไม่ได้

<span id="gmv-enc-constraint"></span>

## กำหนดให้ GMV กระจายเงินอย่างน้อยเท่าไร

ถ้าผู้ลงทุนไม่ต้องการให้น้ำหนักกระจุกเท่า GMV เดิม สามารถเพิ่มเงื่อนไข

$$
\operatorname{ENC}(w)\geq K
\quad\Longleftrightarrow\quad
\sum_i w_i^2\leq\frac{1}{K}.
$$

สำหรับสี่สินทรัพย์ $K$ อยู่ในช่วง 1 ถึง 4 ถ้า $K=1$ ทุกพอร์ต long-only ที่ลงทุนเต็มงบทำได้อยู่แล้ว ถ้า $K=4$ คำตอบที่ทำได้มีเพียง EW เราจึงคืน EW โดยตรงในบรรทัด `if min_enc == n` ของฟังก์ชัน ส่วน $K>4$ ทำไม่ได้ในจักรวาลนี้และฟังก์ชันจะหยุดพร้อมคำอธิบาย

ENC เป็นข้อจำกัดผลรวมกำลังสองน้ำหนัก ไม่ใช่จำนวนชื่อที่ถืออยู่ การถือสี่ตัวแต่ให้น้ำหนักสามตัวน้อยมากยังมี ENC ใกล้หนึ่งได้ ในทางกลับกัน เงื่อนไข ENC อย่างน้อย 3 บังคับให้มีอย่างน้อยสามน้ำหนักที่ไม่เป็นศูนย์ แต่ไม่ได้กำหนดว่าต้องถือเพียงสามตัวหรือทุกตัวเท่ากัน

รูปแบบ `[คำสั่ง for k in enc_targets]` เรียกคำสั่งหนึ่งครั้งต่อค่า `k` แล้วเก็บผลเป็นรายการ `np.vstack` นำ array น้ำหนักในรายการนั้นมาต่อเป็นแถว และ `zip` ช่วยวนอ่านค่าเป้าหมายกับแถวน้ำหนักที่ตรงกัน เราทดลองข้อจำกัดหลายระดับโดยใช้ covariance และขอบเขตน้ำหนักเดิมทั้งหมด

```python
enc_targets = np.array([1.0, 2.0, 3.0, 3.5, 4.0])
enc_constrained_weights = np.vstack([
    solve_min_variance(covariance, min_enc=k) for k in enc_targets
])
gmv_enc_weights = solve_min_variance(covariance, min_enc=3)
print("Target  Achieved ENC  Annual SD  Weights A/B/C/D (%)")
for target, w in zip(enc_targets, enc_constrained_weights):
    print(f"{target:4.1f}    {effective_number(w):8.4f}    "
          f"{portfolio_sd(w, covariance):.4%}   {np.round(100 * w, 4)}")
```

| ENC ขั้นต่ำ | ENC ที่ได้ | SD ต่อปี | น้ำหนัก C |
|---:|---:|---:|---:|
| 1 | 1.7329 | 8.6855% | 70.6822% |
| 2 | 2.0000 | 8.7649% | 64.2765% |
| 3 | 3.0000 | 9.9124% | 46.4790% |
| 3.5 | 3.5000 | 10.8682% | 38.7245% |
| 4 | 4.0000 | 13.1933% | 25.0000% |

เมื่อกำหนด $K=3$ น้ำหนัก A–D คือประมาณ `[14.7334, 29.4864, 46.4790, 9.3012]`% จึงลดเงินใน C และย้ายไปตัวอื่น ค่า SD สูงขึ้นจาก 8.6855% เป็น 9.9124% ต่อปีตาม covariance ที่ใช้

การเพิ่ม $K$ ทำให้ชุดพอร์ตที่อนุญาตเล็กลง พอร์ตบางชุดที่เคยเลือกได้ถูกตัดออก ค่าต่ำสุดของ variance จึงลดลงไม่ได้ภายใต้ covariance เดิม บางช่วงอาจคงที่หากข้อจำกัดยังไม่กระทบคำตอบ เช่น GMV เดิมมี ENC 1.7329 จึงผ่านข้อกำหนดขั้นต่ำ 1 อยู่แล้ว

ข้อจำกัดนี้ทำให้แลก variance ที่ต่ำที่สุดตามค่าประมาณกับการกระจายเงินมากขึ้น เมื่อ covariance ประมาณผิด ผลนอกตัวอย่างอาจต่างจากลำดับในตาราง การเพิ่ม ENC จึงไม่ได้รับประกันว่าจะลดความเสี่ยงจริงหรือเพิ่ม Sharpe ratio

<span id="maximum-decorrelation"></span>

## Maximum Decorrelation ใช้ความสัมพันธ์เป็นเกณฑ์

[Maximum decorrelation](glossary.html#maximum-decorrelation) ในบทนี้หมายถึงการเลือกน้ำหนักให้ $w^{\mathsf T}\rho w$ ต่ำที่สุด โดยใช้ correlation matrix $\rho$ แทน covariance พร้อมข้อจำกัด long-only และลงทุนเต็มงบเดิม:

$$
\min_w w^{\mathsf T}\rho w,
\qquad \mathbf1^{\mathsf T}w=1,\quad w_i\geq0.
$$

มองได้ว่าเราสร้างโลกสมมติซึ่งสินทรัพย์ทุกตัวมี volatility เท่ากับหนึ่ง แล้วหา GMV ในโลกนั้น เมื่อระดับ volatility เท่ากัน ความแตกต่างระหว่างสินทรัพย์ในโจทย์จึงมาจาก correlation น้ำหนักที่ลด $w^{\mathsf T}\rho w$ จะพิจารณาทั้งน้ำหนักและความสัมพันธ์ทุกคู่ รวมช่องแนวทแยงที่เท่ากับหนึ่งด้วย ไม่ใช่เพียงเลือกคู่ที่มี correlation ต่ำที่สุด

พอร์ต MDec ที่ถือจริงยังต้องประเมินความเสี่ยงด้วย covariance เดิม เพราะ A–D มี annual volatility 20%, 15%, 10% และ 25% ไม่ได้เปลี่ยนเป็นหนึ่งจริง ๆ การนำ $\sqrt{w^{\mathsf T}\rho w}$ มาแสดงเป็น annual volatility ของพอร์ตเงินจริงจึงใช้หน่วยผิด

```python
max_decorrelation_weights = solve_min_variance(correlation)
decorrelation_objective = max_decorrelation_weights @ correlation @ max_decorrelation_weights
print("MDec weights (%):", np.round(100 * max_decorrelation_weights, 4))
print(f"Correlation objective: {decorrelation_objective:.6f}")
print(f"ENC: {effective_number(max_decorrelation_weights):.4f}")
print(f"Actual-model annual SD: {portfolio_sd(max_decorrelation_weights, covariance):.4%}")
```

ได้สัดส่วนประมาณ `[9.5102, 28.8155, 38.4396, 23.2346]`% มี ENC 3.4034 และ SD ตาม covariance เดิม 11.2442% ต่อปี C ยังมีน้ำหนักสูงสุด แต่ต่ำกว่า 70.6822% ของ GMV เนื่องจากการลด volatility รายตัวไม่ใช่สิ่งที่ MDec ใช้แยกสินทรัพย์

หากทุกสินทรัพย์มี volatility เท่ากันที่ $s>0$ จะได้ $\Sigma=s^2\rho$ การคูณ objective ด้วยค่าบวกคงที่ไม่เปลี่ยนน้ำหนักที่ทำให้ค่าต่ำที่สุด GMV และ MDec จึงตรงกันในกรณีนั้น เมื่อ volatility ต่างกันอย่างในตัวอย่าง ทั้งสองวิธีตอบคนละโจทย์

<span id="maximum-diversification"></span>

## Maximum Diversification เปรียบเทียบความเสี่ยงก่อนและหลังรวมพอร์ต

[Diversification ratio](glossary.html#diversification-ratio) หรือ DR นิยามเป็น

$$
\operatorname{DR}(w)=\frac{\sum_iw_i\sigma_i}{\sqrt{w^{\mathsf T}\Sigma w}}
=\frac{w^{\mathsf T}\sigma}{\sigma_p}.
$$

ตัวเศษเป็นค่าเฉลี่ยถ่วงน้ำหนักของ volatility รายตัว ตัวส่วนเป็น volatility ของพอร์ตรวม ทั้งสองใช้หน่วยและช่วงเวลาเดียวกัน จึงหารกันแล้วไม่มีหน่วย สูตรนี้และการเลือกพอร์ตที่ทำให้ DR สูงที่สุดอธิบายใน Choueifaty และ Coignard, [Toward Maximum Diversification](https://www.tobam.fr/wp-content/uploads/2014/12/TOBAM-JoPM-Maximum-Div-2008.pdf) หน้า 40–43

สำหรับ EW ของเรา ตัวเศษคือ 17.5% ต่อปี และตัวส่วนคือ 13.1933% ต่อปี จึงได้ DR ประมาณ $17.5/13.1933=1.3264$ เราเปรียบเทียบความเสี่ยงของสินทรัพย์ที่เลือกถ่วงน้ำหนักกับความเสี่ยงหลังรวมเป็นพอร์ต ไม่ได้ใช้ expected return ในเศษ

สำหรับ covariance ที่ถูกต้องและน้ำหนัก long-only ความผันผวนรวมไม่เกินค่าเฉลี่ยถ่วงน้ำหนักของความผันผวนรายตัว จึงได้ DR อย่างน้อยหนึ่งเมื่อส่วนเป็นบวก การถือสินทรัพย์ตัวเดียวที่มี volatility บวกให้ DR เท่ากับหนึ่ง และกรณีทุกสินทรัพย์เคลื่อนไหวสัมพันธ์กันสมบูรณ์ในทิศเดียวกันก็ให้ค่าเดียวกัน หากมีพอร์ต variance ศูนย์แต่ตัวเศษบวก อัตราส่วนนี้จะไม่เป็นจำนวนจำกัด จึงต้องพิจารณากรณีขอบแยกต่างหาก Covariance ชุดหลักของเราเป็น positive definite ทำให้พอร์ตที่ลงทุนเต็มงบไม่มี variance ศูนย์

เราจะหา MaxDR สองทางเพื่อตรวจผลกัน ทางแรกให้ SLSQP ลดค่าลบของ DR เพราะการทำให้ $-\operatorname{DR}$ ต่ำที่สุดเท่ากับทำให้ DR สูงที่สุด ทางที่สองแปลงคำตอบจาก correlation ซึ่งจะอธิบายหลังโค้ด

`np.diag(matrix)` เมื่อรับเมทริกซ์จะดึง variance บนแนวทแยงออกมา แล้ว `np.sqrt` ให้ volatility รายตัว คำสั่งเดียวกันนี้จึงมีหน้าที่ต่างจาก `np.diag` ที่รับ array หนึ่งมิติในตัวอย่างก่อนหน้า

```python
def diversification_ratio(weights, matrix):
    individual_vols = np.sqrt(np.diag(matrix))
    return (weights @ individual_vols) / portfolio_sd(weights, matrix)

max_dr_result = minimize(
    lambda w: -diversification_ratio(w, covariance), equal_weights,
    method="SLSQP", bounds=[(0, 1)] * len(asset_names),
    constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
    options={"ftol": 1e-12, "maxiter": 1000},
)
if not max_dr_result.success:
    raise RuntimeError(max_dr_result.message)
max_dr_weights = max_dr_result.x
if np.any(max_dr_weights < 0) or abs(max_dr_weights.sum() - 1) > 1e-8:
    raise RuntimeError("The MaxDR weights violate the portfolio constraints.")
dr_from_correlation = max_decorrelation_weights / annual_vols
dr_from_correlation = dr_from_correlation / dr_from_correlation.sum()
print("MaxDR weights (%):", np.round(100 * max_dr_weights, 4))
print(f"Maximum DR: {diversification_ratio(max_dr_weights, covariance):.6f}")
print("Matches correlation route:", np.allclose(max_dr_weights, dr_from_correlation, atol=2e-6))
```

ได้ MaxDR ประมาณ `[6.6321, 26.7930, 53.6126, 12.9623]`% และ DR 1.463196 ผลทั้งสองวิธีตรงกันภายในความละเอียดที่ตรวจ น้ำหนักนี้ต่างจาก MDec `[9.5102, 28.8155, 38.4396, 23.2346]`% จึงต้องระบุให้ชัดว่ากำลังใช้ correlation หาคำตอบโดยตรง หรือใช้ correlation เป็นขั้นกลางเพื่อหา MaxDR

### เหตุผลที่หารน้ำหนัก MDec ด้วย volatility

กำหนดน้ำหนักใหม่

$$
q_i=\frac{w_i\sigma_i}{\sum_jw_j\sigma_j}.
$$

ถ้า $w_i\geq0$ และทุก $\sigma_i>0$ จะได้ $q_i\geq0$ และ $\sum_iq_i=1$ เช่นเดียวกับน้ำหนักพอร์ต โดย $q_i$ บอกสัดส่วนของพจน์ $w_i\sigma_i$ ในผลรวม ตัวนี้ยังไม่ใช่ [risk contribution](glossary.html#risk-contribution) เพราะการคำนวณสัดส่วนความเสี่ยงที่แต่ละสินทรัพย์มีต่อพอร์ตจริงต้องใช้ covariance กับสินทรัพย์อื่นด้วย

เมื่อเขียน $\Sigma=\operatorname{diag}(\sigma)\rho\operatorname{diag}(\sigma)$ จะจัดรูปได้ว่า

$$
\operatorname{DR}(w)=\frac{1}{\sqrt{q^{\mathsf T}\rho q}}.
$$

การทำให้ DR สูงที่สุดจึงเท่ากับการหา $q$ ที่ลด $q^{\mathsf T}\rho q$ ภายใต้ผลรวมหนึ่งและไม่ติดลบ ปัญหาหลังนี้ตรงกับโจทย์ที่ใช้หา MDec เราจึงใช้ `max_decorrelation_weights` เป็น $q$ ที่เหมาะสม แล้วกลับไปหาน้ำหนักเงินจริงด้วย

$$
w_i=\frac{q_i/\sigma_i}{\sum_jq_j/\sigma_j}.
$$

การแปลงนี้อธิบายว่าทำไมโค้ดต้องหารด้วย `annual_vols` ก่อนปรับผลรวมเป็นหนึ่ง และช่วยตรวจคำตอบจากตัวแก้ ratio โดยตรงผ่านปัญหา quadratic ที่เป็น convex ในข้อมูลชุดนี้ เงื่อนไขที่ใช้คือ long-only และลงทุนเต็มงบ หากเพิ่มเพดานน้ำหนักหรือ ENC ขั้นต่ำของ $w$ ข้อจำกัดนั้นต้องถูกแปลงไปยัง $q$ ด้วย จะนำ MDec ภายใต้ข้อจำกัดเดิมมาหาร volatility แล้วสรุปว่าเป็น MaxDR ที่ทำตามข้อจำกัดเพิ่มเติมไม่ได้

หากทุกสินทรัพย์มี expected excess return เท่ากับ $s\sigma_i$ ด้วยค่า Sharpe ร่วม $s>0$ จะได้ Sharpe พอร์ตเท่ากับ $s\operatorname{DR}(w)$ จึงทำให้ MaxDR เป็น MSR ภายใต้สมมติฐานนั้น รายละเอียดกรณี $s=0$ และ $s<0$ อยู่ใน [บท Expected Return](expected-return-estimation.html) ส่วนการเลือก DR เป็นเกณฑ์กระจายความเสี่ยงโดยตรงไม่ได้ยืนยันว่าตลาดมี Sharpe รายตัวเท่ากัน

<span id="compare-methods"></span>

## เปรียบเทียบหกวิธีบนข้อมูลชุดเดียวกัน

ตารางต่อไปใช้ A–D ชุดเดิม ทุกพอร์ตเป็น long-only และลงทุนเต็มงบ มีเพียง GMV+ENC3 ที่เพิ่มข้อจำกัด ENC อย่างน้อย 3 เราคำนวณ SD และ DR ของทุกพอร์ตด้วย covariance ชุดเดียวกัน แม้เกณฑ์ที่ใช้หาน้ำหนักจะแตกต่างกัน

`strategy_weights` เป็น dictionary ซึ่งจับคู่ชื่อวิธีกับ array น้ำหนัก `.items()` ใช้วนอ่านทั้งชื่อและน้ำหนัก ส่วน `strategy_metrics` เก็บสามค่าตามลำดับ ENC, annual SD และ DR การแสดง SD ด้วย `:.4%` คูณด้วย 100 และเติมเครื่องหมายเปอร์เซ็นต์ แต่ค่าที่เก็บยังเป็นทศนิยม

```python
strategy_weights = {
    "CW": cap_weights, "EW": equal_weights, "GMV": gmv_weights,
    "GMV+ENC3": gmv_enc_weights, "MDec": max_decorrelation_weights,
    "MaxDR": max_dr_weights,
}
strategy_metrics = {}
print("Method     ENC     Annual SD     DR      Weights A/B/C/D (%)")
for name, w in strategy_weights.items():
    enc = effective_number(w)
    sd = portfolio_sd(w, covariance)
    dr = diversification_ratio(w, covariance)
    strategy_metrics[name] = np.array([enc, sd, dr])
    print(f"{name:9s} {enc:.4f}  {sd:.4%}  {dr:.4f}  {np.round(100 * w, 2)}")
```

| วิธี | ENC | SD ต่อปี | DR | น้ำหนัก A / B / C / D (%) |
|---|---:|---:|---:|---|
| CW | 1.9231 | 16.7824% | 1.1321 | 70.00 / 10.00 / 10.00 / 10.00 |
| EW | 4.0000 | 13.1933% | 1.3264 | 25.00 / 25.00 / 25.00 / 25.00 |
| GMV | 1.7329 | 8.6855% | 1.3332 | 0.73 / 27.81 / 70.68 / 0.77 |
| GMV+ENC3 | 3.0000 | 9.9124% | 1.4470 | 14.73 / 29.49 / 46.48 / 9.30 |
| MDec | 3.4034 | 11.2442% | 1.4120 | 9.51 / 28.82 / 38.44 / 23.23 |
| MaxDR | 2.6287 | 9.5320% | 1.4632 | 6.63 / 26.79 / 53.61 / 12.96 |

GMV มี SD ต่ำที่สุดตาม covariance ที่ใช้ เพราะนั่นคือ objective ของมัน EW มี ENC สูงที่สุดเพราะแบ่งเงินเท่ากัน MaxDR มี DR สูงที่สุด แต่ SD สูงกว่า GMV และ ENC ต่ำกว่า EW ตัวเลขทั้งสามวัดคนละด้าน จึงไม่ควรนำค่าสูงสุดหรือต่ำสุดข้ามคอลัมน์มาตีความว่าเป็นวิธีที่ชนะทุกเกณฑ์

ข้อมูลที่ต้องใช้เพื่อกำหนดน้ำหนักต่างกันด้วย:

| วิธี | ข้อมูลที่กำหนดน้ำหนัก | สิ่งที่เลือกให้เหมาะที่สุดหรือทำตามกฎ |
|---|---|---|
| CW | ราคาและจำนวนหุ้นที่ใช้ถ่วงน้ำหนัก | ลงเงินตามสัดส่วนมูลค่าตลาดในจักรวาล |
| EW | รายชื่อสมาชิก | แบ่งเงิน $1/N$ ณ เวลาปรับสมดุล |
| GMV | Covariance | ลด variance ภายใต้ข้อจำกัด |
| GMV+ENC3 | Covariance และ ENC ขั้นต่ำ | ลด variance โดยต้องกระจายเงินถึงเกณฑ์ |
| MDec | Correlation | ลด $w^{\mathsf T}\rho w$ |
| MaxDR | Volatility และ correlation | เพิ่มอัตราส่วน $w^{\mathsf T}\sigma/\sigma_p$ |

CW และ EW ไม่ต้องประมาณ covariance เพื่อหาน้ำหนัก แต่ถ้าต้องการประเมินความเสี่ยงของพอร์ตทั้งสองก็ยังต้องมีข้อมูลหรือแบบจำลองความเสี่ยง ส่วน covariance ที่ใช้กับวิธีอื่นเป็นค่าที่กำหนดแน่นอนเฉพาะในตัวอย่างนี้ เมื่อทำงานจริง ค่าประมาณอาจคลาดเคลื่อนและเปลี่ยนตามเวลา

เรายังไม่ได้กำหนด expected return ของ A–D จึงคำนวณ expected portfolio return หรือจัดอันดับ Sharpe ของหกวิธีจากตารางนี้ไม่ได้ DR ใช้ volatility รายตัวในเศษ ไม่ได้ใช้ excess return

<span id="rank-and-estimation"></span>

## ตรวจจำนวนข้อมูลและความไวของน้ำหนัก

### ข้อมูลสั้นอาจทำให้ covariance ไม่มี inverse

ต่อไปเป็นตัวอย่างแยกของผลตอบแทนรายเดือนสมมติสี่เดือน สี่สินทรัพย์ ใช้เพื่อตรวจ rank เท่านั้น เราไม่นำ sample covariance ชุดนี้ไปแทน annual covariance ที่ใช้เปรียบเทียบหกวิธีข้างต้น

เมื่อมี $T$ observations และลบค่าเฉลี่ยแต่ละคอลัมน์แล้ว เมทริกซ์ข้อมูลที่ได้มี rank ไม่เกิน $T-1$ ดังนั้น sample covariance ของสินทรัพย์ $N$ ตัวมี rank ไม่เกิน $\min(N,T-1)$ ในกรณี $T=N=4$ จึงมี rank ได้ไม่เกิน 3 และไม่มี inverse แบบปกติ

`mean(axis=0)` หาค่าเฉลี่ยลงตามแต่ละคอลัมน์ การลบ array ค่าเฉลี่ยออกจากทุกแถวเรียกว่า broadcasting ส่วน `.T` สลับแถวกับคอลัมน์ [`np.linalg.matrix_rank`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_rank.html) ใช้ความละเอียดเชิงตัวเลขเพื่อตรวจจำนวนทิศทางที่เป็นอิสระต่อกัน

```python
small_returns = np.array([
    [-0.02,  0.01,  0.005, -0.04],
    [ 0.01, -0.01,  0.002,  0.03],
    [ 0.02,  0.02,  0.001,  0.05],
    [ 0.05,  0.03, -0.003,  0.06],
])
small_centered = small_returns - small_returns.mean(axis=0)
small_sample_cov = small_centered.T @ small_centered / (len(small_returns) - 1)
print("Return matrix shape:", small_returns.shape)
print("Sample covariance rank:", np.linalg.matrix_rank(small_sample_cov))
print("Sample covariance eigenvalues:", np.linalg.eigvalsh(small_sample_cov))
```

ผลคือ shape `(4, 4)` และ rank 3 โดย eigenvalue ที่เล็กที่สุดอยู่ใกล้ศูนย์มาก บางเครื่องอาจแสดงเป็นค่าติดลบขนาดประมาณ $10^{-20}$ จากความละเอียดทศนิยม ค่านี้ต่างจาก covariance ที่มี eigenvalue ติดลบอย่างมีนัยสำคัญจนให้ variance ติดลบได้

Covariance ที่ singular ยังนิยามโจทย์ long-only minimum variance ได้ แต่คำตอบอาจไม่เป็นเอกลักษณ์ และสูตรที่ใช้ $\Sigma^{-1}$ ใช้ไม่ได้ การเพิ่มจำนวนเดือนจนเกินจำนวนสินทรัพย์ช่วยแก้ข้อจำกัดด้าน rank นี้ได้ในบางข้อมูล แต่ยังไม่รับประกัน full rank หากมีสินทรัพย์ซ้ำหรือมีความสัมพันธ์เชิงเส้น และไม่ได้รับประกันความแม่นยำของค่าประมาณ วิธีประมาณด้วย factor model และ shrinkage อยู่ใน [บท Covariance Estimation](covariance-estimation.html) และ [บท Covariance Shrinkage](covariance-shrinkage.html)

### เมทริกซ์คำนวณได้ ก็ยังประมาณผิดได้

กลับสู่ covariance รายปีชุดเดิม คราวนี้ลองสมมติว่าผู้จัดพอร์ตประเมิน volatility ของ C เป็น 8% แทน 10% โดยยังประเมิน correlation ทุกคู่ตามเดิม เราจะหา GMV ใหม่จากค่าประมาณนี้ แล้วประเมินน้ำหนักที่ได้ด้วย covariance เดิมเพื่อดูความไวของการตัดสินใจ

การทดลองนี้กำหนด covariance เดิมเป็นเกณฑ์อ้างอิงที่เรารู้ไว้ล่วงหน้าในโลกสมมติ ทั้งสองตารางเป็นพารามิเตอร์ที่ผู้เขียนกำหนด ไม่ใช่การประมาณจากข้อมูลย้อนหลังหรือการพิสูจน์ว่า covariance เดิมคือความจริงของตลาด

`.copy()` สร้าง array แยกต่างหาก ทำให้แก้ค่า C ใน `stressed_vols` ได้โดยไม่เปลี่ยน `annual_vols` ส่วน `[2]` เลือกสมาชิกตัวที่สาม เพราะ Python เริ่มนับตำแหน่งจากศูนย์

```python
stressed_vols = annual_vols.copy()
stressed_vols[2] = 0.08
stressed_covariance = np.outer(stressed_vols, stressed_vols) * correlation
stressed_gmv_weights = solve_min_variance(stressed_covariance)
stressed_gmv_enc_weights = solve_min_variance(stressed_covariance, min_enc=3)
for name, w in [
    ("Original GMV", gmv_weights),
    ("Changed-estimate GMV", stressed_gmv_weights),
    ("Changed-estimate GMV+ENC3", stressed_gmv_enc_weights),
]:
    print(name, "weights (%):", np.round(100 * w, 4))
    print(f"  Changed-estimate SD: {portfolio_sd(w, stressed_covariance):.4%}; "
          f"reference SD: {portfolio_sd(w, covariance):.4%}; "
          f"ENC: {effective_number(w):.4f}")
```

GMV จากค่าประมาณใหม่เพิ่มน้ำหนัก C จาก 70.6822% เป็นประมาณ 80.3605% และลด ENC จาก 1.7329 เป็น 1.4616 พอร์ตใหม่นี้มี SD เพียง 7.3346% ตามค่าประมาณใหม่ แต่เมื่อประเมินด้วย covariance อ้างอิงเดิมจะได้ 8.8315% สูงกว่า 8.6855% ของ GMV เดิม

เมื่อเพิ่ม ENC ขั้นต่ำเป็น 3 พอร์ตจากค่าประมาณใหม่ถือ C ประมาณ 47.2364% และมี SD ตาม covariance อ้างอิง 9.9199% เทียบกับ 9.9124% ของ GMV+ENC3 ที่ใช้ค่าประมาณเดิม น้ำหนักเปลี่ยนน้อยลงในตัวอย่างนี้ แต่ความเสี่ยงอ้างอิงยังสูงกว่า GMV ที่ไม่ใส่ข้อจำกัด ENC เราจึงมองเห็นทั้งผลจำกัดการกระจุกตัวและต้นทุนใน objective ที่กำหนด ไม่ได้พบข้อรับรองว่าข้อจำกัดชนิดนี้ช่วยทุกสถานการณ์

ก่อนทดสอบด้วยข้อมูลตลาดต้องกำหนดวันที่คำนวณน้ำหนัก ช่วงข้อมูลที่ใช้ประมาณ covariance และช่วงผลตอบแทนที่นำมาประเมินให้แยกกัน น้ำหนักที่ใช้ในช่วงถัดไปต้องสร้างจากข้อมูลที่มีแล้ว ณ เวลาตัดสินใจ รวมทั้งใช้รายชื่อสินทรัพย์ที่ผู้ลงทุนรู้ในวันนั้น เมื่อเทียบวิธีที่ปรับสมดุลต่างกันต้องนับการซื้อขายและต้นทุนด้วย การใช้ข้อมูลอนาคตเลือก covariance หรือเลือก ENC ที่ให้ผลย้อนหลังดีที่สุดจะทำให้การประเมินได้เปรียบข้อมูลที่ผู้ลงทุนจริงไม่มี

<span id="diversification-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

### 1. ซื้อจำนวนหุ้นเท่ากันได้ EW หรือไม่

ใช้ราคา A–D เท่ากับ 70, 20, 10 และ 50 บาท ถ้าซื้ออย่างละหนึ่งหุ้น จะได้น้ำหนักเท่าไร และเป็น CW ตามจำนวนหุ้นบริษัทที่กำหนดในบทหรือไม่

เฉลย: มูลค่ารวม 150 บาท น้ำหนักจึงเป็น $[70,20,10,50]/150$ หรือประมาณ `[46.6667, 13.3333, 6.6667, 33.3333]`% ยังไม่ใช่ EW ซึ่งต้องแบ่งมูลค่าตัวละ 25% และไม่ใช่ CW ของตัวอย่าง เพราะการซื้อหนึ่งหุ้นต่อบริษัทไม่ได้ถ่วงด้วยจำนวนหุ้นบริษัท 10, 5, 10 และ 2 ล้านหุ้น

### 2. ถือสามตัวแปลว่า ENC เท่ากับสามหรือไม่

พอร์ตมีน้ำหนัก `[0.50, 0.25, 0.25, 0]` จงหา ENC แล้วเทียบกับจำนวนสินทรัพย์ที่มีน้ำหนักเป็นบวก

เฉลย: ผลรวมกำลังสองคือ $0.25+0.0625+0.0625=0.375$ จึงได้ ENC $=1/0.375\approx2.6667$ แม้ถือสามตัวจริง หากต้องการ ENC เท่ากับสามโดยถือเพียงสามตัว ต้องแบ่งเงินสามตัวนั้นเท่ากันตัวละหนึ่งในสาม

### 3. แยกกองทุนเป็นสองชื่อช่วยลด SD เท่าไร

กองทุนสองกองมีผลตอบแทนเหมือนกันทุกช่วง ทั้งคู่มี annual SD 20% ถ้าถือกองละ 50% จะได้ ENC และ SD เท่าไร

เฉลย: ENC เท่ากับ 2 เพราะน้ำหนักเท่ากัน แต่ correlation เท่ากับหนึ่ง จึงได้ SD $=0.5(20\%)+0.5(20\%)=20\%$ เหมือนถือกองเดียว การแยกชื่อไม่เพิ่มแหล่งความเสี่ยงที่แตกต่างกันในกรณีนี้

### 4. CW ต้องขายตัวที่ขึ้นราคาหรือไม่

เริ่มจาก CW `[70, 10, 10, 10]`% ให้เฉพาะ A ขึ้นราคา 10% ส่วนตัวอื่นราคาเดิม ไม่มีปันผลและจำนวนหุ้นบริษัทคงที่ น้ำหนักใหม่ของ A เท่าไร ต้องขาย A เพื่อรักษา CW หรือไม่

เฉลย: มูลค่าตามสัดส่วนเดิมเปลี่ยนจาก `[70, 10, 10, 10]` เป็น `[77, 10, 10, 10]` รวม 107 น้ำหนัก A จึงเป็น $77/107\approx71.9626$% พอร์ตที่ถือจำนวนหุ้นเดิมจะเลื่อนไปตรงกับ CW ใหม่อยู่แล้ว ถ้าขาย A ให้กลับมา 70% จะเป็นการคงน้ำหนักเป้าหมายเดิม ไม่ใช่ตาม CW ใหม่ในตัวอย่างนี้

### 5. ENC ขั้นต่ำเป็นสี่เหลือพอร์ตให้เลือกกี่ชุด

มีสี่สินทรัพย์ น้ำหนักไม่ติดลบและรวมหนึ่ง ถ้ากำหนด ENC อย่างน้อยสี่ จะยังหา GMV ที่ให้น้ำหนักต่างจาก EW ได้หรือไม่

เฉลย: ไม่ได้ เพราะ $\sum_i(w_i-1/4)^2\geq0$ เมื่อกระจายพจน์และใช้ $\sum_iw_i=1$ จะได้ $\sum_iw_i^2\geq1/4$ ดังนั้น ENC ไม่เกินสี่ และเกิดค่าเท่ากันได้เมื่อทุกพจน์ $w_i-1/4$ เป็นศูนย์เท่านั้น จึงเหลือน้ำหนัก `[0.25, 0.25, 0.25, 0.25]` ชุดเดียว

### 6. แยก MDec, MaxDR และ GMV ด้วยสองสินทรัพย์

ให้สินทรัพย์สองตัวมี annual SD 10% และ 20% และ correlation เท่ากับศูนย์ ภายใต้ long-only และลงทุนเต็มงบ จงหาน้ำหนักของสามวิธีโดยใช้สูตรในบท

เฉลย: Correlation matrix เป็น identity จึงได้ MDec `[0.5, 0.5]` สำหรับ MaxDR ให้นำ `[0.5, 0.5]` หารด้วย `[0.10, 0.20]` ได้ `[5, 2.5]` แล้วหารผลรวม 7.5 จึงเป็น `[2/3, 1/3]` ส่วน GMV เมื่อ covariance เป็นแนวทแยงจะถ่วงน้ำหนักตาม inverse variance คือ `[1/0.01, 1/0.04]=[100,25]` หาร 125 ได้ `[0.8,0.2]` ค่า SD ของ MDec, MaxDR และ GMV ประมาณ 11.1803%, 9.4281% และ 8.9443% ต่อปีตามลำดับ MaxDR มี DR $\sqrt2\approx1.4142$ แม้ SD ยังสูงกว่า GMV

### 7. ข้อมูลสิบเดือนพอหา inverse ของ covariance ยี่สิบสินทรัพย์หรือไม่

ข้อมูลครบทุกเดือน ไม่มี missing values และคำนวณ sample covariance โดยลบค่าเฉลี่ยตามปกติ เมทริกซ์มีขนาด $20\times20$ จะ invertible ได้หรือไม่

เฉลย: Rank ไม่เกิน $\min(20,10-1)=9$ จึงไม่เป็น full rank และไม่มี inverse แบบปกติ การมีตัวเลขครบ 400 ช่องไม่ได้แปลว่ามีข้อมูลอิสระพอประมาณทุกทิศทาง ควรทบทวนช่วงข้อมูลและวิธีประมาณ covariance พร้อมข้อสมมติ ไม่ใช้การเติมเลขเล็ก ๆ บนแนวทแยงโดยไม่อธิบายผลที่เปลี่ยนแบบจำลอง

### 8. จากตารางหกวิธี เลือกผู้ชนะด้าน Sharpe ได้หรือยัง

MaxDR มี DR สูงสุด ขณะที่ GMV มี SD ต่ำสุด ข้อมูลใดขาดอยู่หากต้องการเปรียบเทียบ expected Sharpe และต้องเพิ่มอะไรหากต้องการทดสอบผลหลังต้นทุน

เฉลย: ต้องมี expected excess return ที่สอดคล้องกับช่วงเวลาของ covariance จึงคำนวณ expected Sharpe ได้ ค่า DR ใช้ volatility รายตัวแทน expected excess return ในเศษ จะเทียบสองค่านี้โดยตรงได้ภายใต้สมมติฐานเพิ่มเติม เช่น ทุกสินทรัพย์มี Sharpe ร่วมที่เป็นบวก หากต้องการผลหลังต้นทุนต้องกำหนดช่วงทดสอบนอกตัวอย่าง จังหวะประมาณพารามิเตอร์และปรับสมดุล รายชื่อสินทรัพย์ที่รู้ ณ เวลานั้น ตลอดจนต้นทุนและข้อจำกัดการซื้อขาย ข้อมูลที่กำหนดในบทพอเปรียบเทียบเกณฑ์ทางคณิตศาสตร์ แต่ยังไม่มีเส้นทางตลาดสำหรับทดสอบผลลงทุนจริง

การแบ่งเงินตัวละ 25% ยังไม่ได้ระบุว่าแต่ละตัวรับผิดชอบความเสี่ยงพอร์ตเท่ากันหรือไม่ ขั้นต่อไปคือคำนวณ [risk contribution](glossary.html#risk-contribution) ซึ่งใช้ทั้งน้ำหนักและ covariance แล้วจึงตั้งโจทย์ [risk parity](glossary.html#risk-parity) ให้ส่วนความเสี่ยงเหล่านั้นเท่ากัน

<span id="diversification-sources"></span>

## แหล่งที่มาและขอบเขตของตัวอย่าง

บทเรียนเรียบเรียงใหม่จากหัวข้อในคอร์ส Advanced Portfolio Construction and Analysis with Python โดยอ่าน Transcript ของ [Naive Diversification](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/U3iJ0/naive-diversification) และ [Scientific Diversification](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/VJpdS/scientific-diversification) ครบทั้งสองบทเมื่อ 3 ตุลาคม 2026 ใช้เป็นลำดับแนวคิดเรื่องความกระจุกตัว ENC, GMV และการเลือกน้ำหนักด้วย correlation

คำอธิบาย CW และการดูแลดัชนีตรวจเทียบกับ [S&P DJI: Methodology Matters](https://www.spglobal.com/spdji/en/research-insights/index-literacy/methodology-matters/) ส่วน DR และความเชื่อมโยงกับ correlation อ้างอิงส่วนคำนิยามและทฤษฎีหน้า 40–43 ของ Choueifaty และ Coignard (2008), [Toward Maximum Diversification](https://www.tobam.fr/wp-content/uploads/2014/12/TOBAM-JoPM-Maximum-Div-2008.pdf) บทนี้ไม่ได้ทำซ้ำผลทดลองตลาดในงานนั้นและไม่ได้ใช้ผลในอดีตเป็นข้อรับรองผลตอบแทนของวิธีใด

เอกสารประกอบโค้ดที่ตรวจเมื่อ 3 ตุลาคม 2026 ได้แก่ [`scipy.optimize.minimize` แบบ SLSQP](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html), [`numpy.linalg.solve`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html) และ [`numpy.linalg.matrix_rank`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_rank.html) ทุก array ในบทเป็นตัวอย่างสมมติที่สร้างขึ้นใหม่ โค้ดใช้ NumPy และ SciPy โดยไม่มี CSV, toolkit หรือ Transcript ของคอร์สรวมอยู่ในไฟล์ดาวน์โหลด
