---
title: "Risk Parity: แบ่งงบความเสี่ยงก่อนแบ่งเงิน"
description: หา weights จากเป้าหมาย risk contributions แยก Inverse Volatility ออกจาก ERC ทดลองงบความเสี่ยงไม่เท่ากัน เพดานน้ำหนัก และการกู้เงินเพื่อกำหนด volatility
---

# Risk Parity: แบ่งงบความเสี่ยงก่อนแบ่งเงิน

<p class="lead">หากต้องการให้สินทรัพย์สี่ตัวมีส่วนต่อความเสี่ยงตัวละ 25% เราต้องหาน้ำหนักเงินลงทุนที่ทำให้ได้ส่วนแบ่งนั้น น้ำหนักที่ได้มักไม่ใช่ตัวละ 25%</p>

บท [Risk Contribution](risk-contributions.html) คำนวณส่วนแบ่งความเสี่ยงจากน้ำหนักที่มีอยู่แล้ว บทนี้กลับทิศทาง โดยกำหนด [risk budget](glossary.html#risk-budget) ของแต่ละสินทรัพย์ก่อน แล้วหาน้ำหนักที่ทำให้ส่วนแบ่งตรงเป้าหมาย หากทุกตัวมี budget เท่ากัน เรียกว่า Equal Risk Contribution หรือ ERC ซึ่งเป็นรูปแบบของ [risk parity](glossary.html#risk-parity) ที่เราจะใช้ในหน้านี้

คำว่า risk parity มีการใช้กว้างกว่านี้ในงานลงทุน บางวิธีใช้น้ำหนักส่วนกลับของ SD เป็นตัวแทน บางวิธีแบ่งความเสี่ยงตาม asset classes หรือ factors เราจึงระบุทั้งวิธีวัดความเสี่ยงและส่วนประกอบที่นำมาแบ่ง บทนี้ใช้ volatility และแบ่งตามสินทรัพย์ที่กำหนดไว้

ตัวอย่างทั้งหมดเขียนขึ้นใหม่ ใช้ covariance สมมติชุดเดียวกับบทก่อนในหน่วยปี ไม่มี expected return ที่ใช้แนะนำการลงทุน ไม่มีต้นทุนซื้อขาย ยกเว้นต้นทุนเงินกู้ที่ระบุในตัวอย่างท้ายบท โค้ดรันจาก Notebook ใหม่ตามลำดับได้ด้วย NumPy, pandas และ SciPy โดยไม่ต้องรันบทก่อน

<span id="risk-parity-target"></span>

## กำหนดเป้าหมายเป็นส่วนแบ่งความเสี่ยง

สำหรับ $N$ สินทรัพย์ ให้ $b_i$ เป็นส่วนแบ่งความเสี่ยงเป้าหมายของตัวที่ $i$ ใช้ $b_i>0$ และ $\sum_ib_i=1$ ในวิธีที่กำลังจะสร้าง เป้าหมายคือ

$$
p_i(w)=\frac{w_i(\Sigma w)_i}{w^\top\Sigma w}=b_i.
$$

ERC สี่สินทรัพย์ใช้ $b_i=1/4$ ทุกตัว ส่วนการกำหนด $b=(0.40,0.30,0.20,0.10)$ หมายถึงต้องการให้ A/B/C/D รับส่วนความเสี่ยง 40/30/20/10 ตามลำดับ นี่เป็นเป้าหมายของ contribution ภายใต้ covariance ที่เลือก ยังไม่ใช่น้ำหนักเงินลงทุน

สร้างข้อมูลเข้า A/B/C/D ที่มี SD 20%, 15%, 10%, 25% ต่อปี และ correlation ต่างกันตามคู่:

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize

assets = ["A", "B", "C", "D"]
asset_vol = np.array([0.20, 0.15, 0.10, 0.25])
correlation = np.array([
    [1.00, 0.50, 0.20, 0.65],
    [0.50, 1.00, 0.10, 0.40],
    [0.20, 0.10, 1.00, 0.15],
    [0.65, 0.40, 0.15, 1.00]
])
covariance = np.outer(asset_vol, asset_vol) * correlation
print(pd.DataFrame(covariance, index=assets, columns=assets).round(5))
print("Smallest covariance eigenvalue:", round(np.linalg.eigvalsh(covariance).min(), 8))
```

`np.outer` คูณ SD ทุกคู่เพื่อแปลง correlation เป็น covariance เมทริกซ์นี้มี eigenvalue ต่ำสุดประมาณ 0.00942128 ซึ่งเป็นบวก จึงเป็น positive definite พอร์ตที่มี exposure ไม่เป็นศูนย์จะมี variance บวก และเราสามารถใช้สูตร risk shares ที่หารด้วย variance ได้

ชื่อและลำดับของสินทรัพย์ต้องเหมือนกันใน covariance, weights และ budget เมื่อแปลง DataFrame เป็น NumPy array ป้ายแถวและคอลัมน์จะไม่ช่วยจับการเรียงผิดให้อีกต่อไป

<span id="inverse-volatility-weights"></span>

## ลองถ่วงน้ำหนักด้วยส่วนกลับของ SD

[Inverse-volatility weighting](glossary.html#inverse-volatility) ให้สินทรัพย์ที่มี SD ต่ำได้น้ำหนักสูงตามสูตร

$$
w_i^{\mathrm{IV}}=\frac{1/\sigma_i}{\sum_j1/\sigma_j}.
$$

เช่น A มี SD 20% ให้คะแนน $1/0.20=5$ ส่วน C มี SD 10% ให้คะแนน 10 เมื่อหารด้วยผลรวมคะแนนทั้งสี่ตัว จึงได้ C หนักเป็นสองเท่าของ A วิธีนี้ทำให้ $w_i\sigma_i$ เท่ากันทุกตัว แต่ยังไม่ได้ใช้ correlation ระหว่างตัว

```python
def risk_shares(cov, weights):
    weights = np.asarray(weights, dtype=float)
    marginal_variance = np.asarray(cov, dtype=float) @ weights
    variance = weights @ marginal_variance
    if variance <= 0:
        raise ValueError("Portfolio variance must be positive")
    return weights * marginal_variance / variance

w_equal = np.repeat(1 / len(assets), len(assets))
w_inverse_vol = (1 / asset_vol) / (1 / asset_vol).sum()
initial_comparison = pd.DataFrame({
    "EW weight (%)": 100 * w_equal,
    "EW risk (%)": 100 * risk_shares(covariance, w_equal),
    "IV weight (%)": 100 * w_inverse_vol,
    "IV risk (%)": 100 * risk_shares(covariance, w_inverse_vol)
}, index=assets)
print(initial_comparison.round(4).to_string())
print("Correlation row sums:", correlation.sum(axis=1))
```

`np.repeat(0.25, 4)` สร้างน้ำหนักเท่ากันสี่ตัว ฟังก์ชัน `risk_shares` คำนวณ $\Sigma w$ ก่อน แล้วคูณกับ weights ทีละตำแหน่งและหารด้วย variance พอร์ต ใช้กับเมทริกซ์ที่เราสร้างและตรวจแล้วในตัวอย่างนี้

น้ำหนัก IV เป็นประมาณ 19.4805%, 25.9740%, 38.9610%, 15.5844% แต่ risk shares เป็น 29.375%, 25%, 18.125%, 27.5% C ยังรับความเสี่ยงต่ำกว่าเป้าหมาย 25% แม้จะลงเงินมากที่สุด เพราะ C มี correlation กับตัวอื่นต่ำกว่า

สำหรับ IV ให้ $k=w_i\sigma_i$ ซึ่งเท่ากันทุกตัว จะได้

$$
w_i(\Sigma w)_i=k^2\sum_j\rho_{ij}.
$$

ส่วนของแต่ละตัวจึงขึ้นกับผลรวม correlation ในแถวนั้น ในข้อมูลนี้ row sums เป็น 2.35, 2.00, 1.45, 2.20 เมื่อหารด้วยผลรวมทั้งหมด 8 จึงได้ risk shares ของ IV ตามที่โค้ดแสดง

<span id="inverse-volatility-exact-cases"></span>

## เงื่อนไขที่ Inverse Volatility ให้ ERC พอดี

### สองสินทรัพย์

สำหรับสินทรัพย์สองตัว การตั้ง contribution ให้เท่ากันเขียนได้เป็น

$$
w_1^2\sigma_1^2+w_1w_2\rho\sigma_1\sigma_2
=w_2^2\sigma_2^2+w_1w_2\rho\sigma_1\sigma_2.
$$

พจน์ covariance ทั้งสองฝั่งเหมือนกันจึงตัดออก เหลือ $w_1\sigma_1=w_2\sigma_2$ เมื่อ weights และ SD เป็นบวก รวมกับ $w_1+w_2=1$ จึงได้สูตร inverse volatility ไม่ว่าค่า correlation จะเป็นเท่าใด ตราบที่ portfolio variance ยังบวก

หาก SD เป็น 20%/10% จะได้ weights 1/3 และ 2/3 ส่วน correlation เปลี่ยนระดับ volatility รวม แต่ไม่เปลี่ยนน้ำหนัก ERC ของกรณีสองสินทรัพย์นี้

### หลายสินทรัพย์ที่มี correlation ทุกคู่เท่ากัน

ถ้าทุกคู่ใช้ correlation $\rho$ เดียวกัน ผลรวมแต่ละแถวคือ $1+(N-1)\rho$ เท่ากัน IV จึงให้ contribution เท่ากันด้วย สมมติฐานนี้เป็นเงื่อนไขที่เพียงพอ ไม่ได้บอกว่า correlation ในตลาดต้องเท่ากัน

```python
special_cases = []
for rho in [-0.7, 0.0, 0.8]:
    two_vol = np.array([0.20, 0.10])
    two_cov = np.outer(two_vol, two_vol) * np.array([[1, rho], [rho, 1]])
    two_w = (1 / two_vol) / (1 / two_vol).sum()
    special_cases.append([rho, *two_w, *risk_shares(two_cov, two_w)])
print(pd.DataFrame(special_cases, columns=["rho", "w1", "w2", "p1", "p2"]).round(6).to_string(index=False))
equal_corr = np.full((4, 4), 0.3)
np.fill_diagonal(equal_corr, 1.0)
equal_corr_cov = np.outer(asset_vol, asset_vol) * equal_corr
print("Four-asset IV shares under equal correlation:", risk_shares(equal_corr_cov, w_inverse_vol))
```

ตารางสองสินทรัพย์ให้ risk shares 0.5/0.5 เมื่อ correlation เป็น −0.7, 0 และ 0.8 ส่วนเมทริกซ์สี่ตัวที่ทุกคู่ใช้ 0.3 ให้ shares ตัวละ 0.25 `np.full((4,4),0.3)` ใส่ค่าเดียวกันทุกช่อง แล้ว `np.fill_diagonal` เปลี่ยนแนวทแยงกลับเป็นหนึ่ง

กรณีสองตัวที่ correlation −1 และน้ำหนัก inverse volatility จะหักล้างกันจน variance ศูนย์ ทำให้ $p_i$ กลายเป็น $0/0$ เช่นเดียวกัน เมทริกซ์ equicorrelation ที่ขอบ $\rho=-1/(N-1)$ อาจให้ variance ศูนย์ในทิศทางนี้ เราจึงไม่ใช้กรณีเหล่านี้เป็นตัวอย่าง risk shares 50/50 หรือ $1/N$

ในกรณีทั่วไป หาก correlation row sums เท่ากันและ variance บวก IV ก็ให้ ERC ได้ แม้ correlation แต่ละคู่ไม่เท่ากัน แต่ถ้า row sums ต่างกันตามตัวอย่างตั้งต้น เราต้องคำนวณน้ำหนักด้วยวิธีอื่น

<span id="unequal-risk-budgets"></span>

## งบความเสี่ยงไม่เท่ากันเริ่มตรวจได้จากกรณีไม่มี Correlation

ถ้า covariance เป็นแนวทแยง เรามี

$$
c_i=w_i^2\sigma_i^2.
$$

ต้องการ $c_i/V=b_i$ จึงเลือก $w_i\sigma_i$ ให้เป็นสัดส่วนกับ $\sqrt{b_i}$ แล้ว normalize:

$$
w_i=\frac{\sqrt{b_i}/\sigma_i}{\sum_j\sqrt{b_j}/\sigma_j}.
$$

เช่น budget 40% เทียบกับ 10% ต่างกันสี่เท่า แต่ exposure หลังคูณ SD ต่างกันสองเท่า เพราะ contribution ใช้กำลังสอง เราไม่ได้ใช้สูตร $b_i/\sigma_i$ สำหรับกรณีนี้

```python
budget = np.array([0.40, 0.30, 0.20, 0.10])
diagonal_cov = np.diag(asset_vol ** 2)
w_diagonal_budget = np.sqrt(budget) / asset_vol
w_diagonal_budget /= w_diagonal_budget.sum()
print(pd.DataFrame({"Budget (%)": 100 * budget,
                    "Weight (%)": 100 * w_diagonal_budget,
                    "Risk share (%)": 100 * risk_shares(diagonal_cov, w_diagonal_budget)},
                   index=assets).round(4).to_string())
```

น้ำหนักจาก covariance แนวทแยงเป็นประมาณ 25.1958%, 29.0936%, 35.6323%, 10.0783% และ risk shares กลับมาเป็น 40/30/20/10 ตามเป้าหมาย ใช้ผลนี้เป็นคำตอบแบบปิดสำหรับตรวจตัวแก้สมการในหัวข้อถัดไปได้ แต่จะนำ weights ชุดนี้ไปใช้กับ covariance ที่มี correlation แล้วคาดหวัง shares เดิมทันทีไม่ได้

<span id="risk-budget-solver"></span>

## หาน้ำหนักจาก Covariance ทั่วไป

ให้ $x_i>0$ เป็นตัวแปรช่วยที่ยังไม่บังคับให้รวมเป็นหนึ่ง เราเลือก $x$ ให้ค่าต่อไปนี้ต่ำสุด:

$$
f(x)=\frac12x^\top\Sigma x-\sum_i b_i\log x_i.
$$

พจน์แรกเพิ่มเมื่อรับความเสี่ยงมาก ส่วน $-b_i\log x_i$ เพิ่มสูงมากเมื่อ $x_i$ เข้าใกล้ศูนย์ จึงกันไม่ให้ตัวที่มี budget บวกถูกทิ้งเป็นน้ำหนักศูนย์ เมื่อ $\Sigma$ positive definite และทุก $b_i>0$ ปัญหานี้มีคำตอบบวกที่เป็นเอกลักษณ์

อนุพันธ์ที่คำตอบเท่ากับศูนย์:

$$
(\Sigma x)_i-\frac{b_i}{x_i}=0
\quad\Longrightarrow\quad
x_i(\Sigma x)_i=b_i.
$$

เมื่อรวมทุกตัวจะได้ $x^\top\Sigma x=\sum_i b_i=1$ จากนั้นตั้ง $w=x/\sum_jx_j$ ทั้ง contribution และ variance จะถูกหารด้วย $(\sum_jx_j)^2$ เหมือนกัน ทำให้

$$
\frac{w_i(\Sigma w)_i}{w^\top\Sigma w}=b_i.
$$

การ normalize ขั้นนี้อาศัยคุณสมบัติว่าการเพิ่มขนาดทั้งพอร์ตไม่เปลี่ยน risk shares ไม่ใช่กฎทั่วไปว่าคำตอบ optimization ทุกชนิด normalize แล้วจะยังตอบโจทย์เดิม เช่น weights จาก utility optimization ในบท Black–Litterman ต้องแยกงบเงินสดตามเงื่อนไขของปัญหานั้น

<details>
<summary>อ่านต่อ: เหตุใดปัญหานี้เป็น convex และเปลี่ยนตัวแปรได้</summary>

Hessian ของ $f$ คือ $\Sigma+\operatorname{diag}(b_i/x_i^2)$ ซึ่ง positive definite บน $x_i>0$ ภายใต้เงื่อนไขที่กำหนด จึงเป็น strictly convex พจน์ quadratic คุมเมื่อขนาด $x$ สูงมาก และ log term คุมเมื่อสมาชิกเข้าใกล้ศูนย์

เพื่อให้สเกลตัวเลขเหมาะกับ optimizer ใช้ $z_i=\sigma_i x_i$ และให้ $C$ เป็น correlation matrix จะได้ objective ที่ต่างจากเดิมเพียงค่าคงที่เป็น $\tfrac12z^\top Cz-\sum_i b_i\log z_i$ gradient คือ $Cz-b/z$ เมื่อได้ $z$ จึงหารด้วย SD เพื่อกลับเป็น $x$ ก่อน normalize

</details>

โค้ดใช้ `minimize` ของ SciPy พร้อม gradient ที่คำนวณเอง ฟังก์ชันรับ covariance และ budget แล้วคืน array ของ weights ตามลำดับข้อมูลเข้า:

```python
def risk_budget_weights(cov, budget):
    cov = np.asarray(cov, dtype=float)
    budget = np.asarray(budget, dtype=float)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1] or cov.shape[0] == 0:
        raise ValueError("Covariance must be a nonempty square matrix")
    n = cov.shape[0]
    if budget.shape != (n,):
        raise ValueError("Budget must have one entry per asset")
    if not np.isfinite(cov).all() or not np.isfinite(budget).all():
        raise ValueError("Inputs must be finite")
    if not np.allclose(cov, cov.T, rtol=1e-10, atol=1e-12):
        raise ValueError("Covariance must be symmetric")
    if np.any(budget <= 0) or not np.isclose(budget.sum(), 1.0, rtol=0, atol=1e-10):
        raise ValueError("Budgets must be positive and sum to one")
    cov = (cov + cov.T) / 2
    np.linalg.cholesky(cov)
    vol = np.sqrt(np.diag(cov))
    corr = cov / np.outer(vol, vol)

    def objective(z):
        return 0.5 * z @ corr @ z - budget @ np.log(z)

    def gradient(z):
        return corr @ z - budget / z

    fit = minimize(objective, np.sqrt(budget), jac=gradient,
                   method="L-BFGS-B", bounds=[(1e-12, None)] * n,
                   options={"ftol": 1e-15, "gtol": 1e-8, "maxiter": 2000})
    if not fit.success or not np.isfinite(fit.x).all():
        raise RuntimeError("Risk-budget optimization did not converge")
    x = fit.x / vol
    weights = x / x.sum()
    variance = weights @ cov @ weights
    shares = weights * (cov @ weights) / variance
    if np.any(weights <= 0) or np.max(np.abs(shares - budget)) > 1e-7:
        raise RuntimeError("Risk shares do not match the requested budgets")
    return weights

print("Risk-budget solver is ready")
```

ส่วนแรกตรวจ input: covariance ต้องเป็น square matrix ที่สมมาตรและ positive definite, budget ต้องมีหนึ่งค่าต่อสินทรัพย์ เป็นบวกทุกตัวและรวมหนึ่ง `np.linalg.cholesky` จะหยุดด้วย `LinAlgError` หากเมทริกซ์ไม่ผ่านเงื่อนไข PD ส่วน missing values เช่น `NaN` ถูกปฏิเสธตั้งแต่ต้น ฟังก์ชันนี้ตั้งใจไม่รองรับ zero budgets หรือเมทริกซ์ singular; ถ้าจะตัดสินทรัพย์ออกต้องกำหนด universe ใหม่และอธิบายการเปลี่ยน budget

ใน `minimize` ตัวแปร `objective` คืนค่าเดียวที่ต้องการลด และ `jac=gradient` ส่งสูตรอนุพันธ์ให้โปรแกรม `bounds` กำหนด $z_i$ ไม่น้อยกว่า $10^{-12}$ เพื่อกันการคำนวณ log ที่ศูนย์ เริ่มค้นหาจาก `np.sqrt(budget)` ส่วน `ftol`, `gtol` และ `maxiter` คุมเกณฑ์หยุดและจำนวนรอบ ตาม [เอกสาร SciPy L-BFGS-B](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html)

หลัง optimizer แจ้ง success เราคำนวณ risk shares ซ้ำจาก weights และ covariance จริง ต้องคลาดจาก budget ไม่เกิน $10^{-7}$ ในหน่วยสัดส่วน จึงคืนผล การตรวจนี้ช่วยจับคำตอบที่หยุดค้นหาแล้วแต่ยังไม่ตรงสมการ โดยไม่ได้พิสูจน์ว่า covariance ประมาณอนาคตได้ดี

<span id="erc-and-budget-results"></span>

## คำตอบของ ERC และ Budget 40/30/20/10

กลับมาใช้ covariance เต็มที่มี correlation ต่างกันตามคู่:

```python
equal_budget = np.repeat(0.25, 4)
w_erc = risk_budget_weights(covariance, equal_budget)
w_budget = risk_budget_weights(covariance, budget)
allocation_table = pd.DataFrame({
    "ERC weight (%)": 100 * w_erc,
    "ERC risk (%)": 100 * risk_shares(covariance, w_erc),
    "Budget weight (%)": 100 * w_budget,
    "Budget risk (%)": 100 * risk_shares(covariance, w_budget)
}, index=assets)
print(allocation_table.round(4).to_string())
print("ERC annual volatility (%):", round(100 * np.sqrt(w_erc @ covariance @ w_erc), 4))
```

ERC ให้ weights ประมาณ 16.2989%, 24.9698%, 44.8160%, 13.9153% แต่ละตัวมี risk share 25% และ volatility รวมประมาณ 10.3969% ต่อปี C ต้องรับเงินมากกว่า IV ซึ่งให้ 38.9610% เพราะ IV เดิมให้ risk share C ต่ำกว่าเป้าหมาย

เมื่อตั้ง budget เป็น 40/30/20/10 weights เปลี่ยนเป็นประมาณ 25.0830%, 28.7429%, 39.8718%, 6.3024% A ได้เงิน 25.0830% เพื่อรับความเสี่ยง 40% ส่วน C ได้เงินมากกว่า A แต่รับความเสี่ยงเพียง 20% เพราะ SD และ covariance ของทั้งสองตัวต่างกัน

การเลือก budget เป็นการตัดสินใจของผู้กำหนดพอร์ต สมการหา weights ที่ทำตามเป้าหมายได้ภายใต้ covariance นี้ แต่ไม่ได้บอกว่า budget ชุดใดเหมาะกับผลตอบแทน เป้าหมายการใช้เงิน หรือข้อจำกัดของผู้ลงทุน

### ตรวจคำตอบกับสูตรที่รู้และการเปลี่ยนหน่วย

หากคูณ covariance ทั้งเมทริกซ์ด้วยค่าบวกเดียวกัน risk shares สำหรับ weights เดิมไม่เปลี่ยน คำตอบ risk-budget weights จึงควรเหมือนกันด้วย เช่นใช้ annualized covariance หรือหารด้วย 12 เป็น monthly covariance ตาม convention ที่กำหนด

```python
w_monthly = risk_budget_weights(covariance / 12, equal_budget)
w_diagonal_solved = risk_budget_weights(diagonal_cov, budget)
print("Annual/monthly allocation agrees:", np.allclose(w_erc, w_monthly, atol=1e-9))
print("Diagonal closed form agrees:", np.allclose(w_diagonal_budget, w_diagonal_solved, atol=1e-8))
print("Maximum ERC risk-share error:", f"{np.max(np.abs(risk_shares(covariance, w_erc) - equal_budget)):.2e}")
print("Total invested weight:", round(w_erc.sum(), 12))
```

ผลเปรียบเทียบทั้งสองบรรทัดเป็น `True` และ total invested weight เท่ากับหนึ่ง การตรวจกรณีแนวทแยงใช้สูตร $\sqrt b/\sigma$ ที่หาได้ด้วยมือ จึงช่วยตรวจวิธี solve ด้วยคำตอบอีกวิธีหนึ่ง กฎหาร 12 เป็น convention ภายใต้สมมติฐานการรวมผลตอบแทนตามเวลา ไม่ได้ทำให้ variance ของผลตอบแทนทบต้นคำนวณได้ exact โดยอัตโนมัติ

<span id="risk-budget-negative-correlation"></span>

## Correlation ติดลบยังใช้ได้ เมื่อ Covariance ยัง PD

การมี correlation ติดลบไม่ได้ทำให้ covariance ใช้ไม่ได้ ลองตัวอย่างใหม่สามสินทรัพย์ที่ตัวแรกกับตัวที่สองมี correlation −0.65 อีกสองคู่เป็น 0.10 และ −0.10 แล้วตั้ง budgets เป็น 20/50/30

```python
negative_corr = np.array([[1.0, -0.65, 0.1], [-0.65, 1.0, -0.1], [0.1, -0.1, 1.0]])
negative_vol = np.array([0.20, 0.15, 0.10])
negative_cov = np.outer(negative_vol, negative_vol) * negative_corr
negative_budget = np.array([0.2, 0.5, 0.3])
w_negative = risk_budget_weights(negative_cov, negative_budget)
print("Smallest correlation eigenvalue:", round(np.linalg.eigvalsh(negative_corr).min(), 6))
print("Weights:", np.round(w_negative, 6))
print("Risk shares:", np.round(risk_shares(negative_cov, w_negative), 6))
```

Correlation matrix นี้มี eigenvalue ต่ำสุด 0.35 ซึ่งเป็นบวก ได้ weights ประมาณ 25.5035%, 42.0766%, 32.4199% และ risk shares 20/50/30 ทุกตัวเป็นบวกตามเป้าหมาย แม้มีพจน์ covariance ติดลบ

ในบทก่อน weights ที่กำหนดมาเองอาจให้ negative risk contribution ได้ แต่ตรงนี้ optimizer เปลี่ยน weights เพื่อให้ contributions ตรงกับ budgets บวก หากใช้เมทริกซ์ที่เกือบ singular หรือ budgets เล็กมาก อาจต้องตรวจความแม่นเชิงตัวเลขเพิ่มเติมแทนการลดเกณฑ์ตรวจจนผ่าน

<span id="risk-budget-weight-caps"></span>

## ตั้งเพดานเงินลงทุนแล้ว อาจทำ Budget เดิมไม่ได้

ERC ตั้งต้นให้ C ประมาณ 44.8160% หากข้อจำกัดกำหนดว่า C ลงได้ไม่เกิน 30% คำตอบ ERC เดิมจะใช้ไม่ได้ และเมื่อ covariance เป็น PD กับ budgets บวก คำตอบ long-only ERC เป็นเอกลักษณ์ จึงไม่มี weights ชุดอื่นที่ยังให้ shares ตัวละ 25% พร้อมผ่านเพดานนี้ได้

เราลองปัญหาอีกแบบ: หาพอร์ตที่ risk shares อยู่ใกล้ 25% ที่สุดตามผลรวมกำลังสองของความคลาดเคลื่อน ภายใต้ weights ไม่ติดลบ รวมหนึ่ง และ C ไม่เกิน 30%

```python
cap = 0.30
capped_fit = minimize(
    lambda w: np.sum((risk_shares(covariance, w) - equal_budget) ** 2),
    w_equal, method="SLSQP",
    bounds=[(0.0, 1.0), (0.0, 1.0), (0.0, cap), (0.0, 1.0)],
    constraints={"type": "eq", "fun": lambda w: w.sum() - 1.0},
    options={"ftol": 1e-13, "maxiter": 1000}
)
if not capped_fit.success:
    raise RuntimeError(capped_fit.message)
w_capped = capped_fit.x
assert np.isclose(w_capped.sum(), 1) and w_capped[2] <= cap + 1e-9
print(pd.DataFrame({"ERC weight (%)": 100 * w_erc,
                    "Capped weight (%)": 100 * w_capped,
                    "Capped risk (%)": 100 * risk_shares(covariance, w_capped)},
                   index=assets).round(4).to_string())
print("Largest deviation from 25% risk (percentage points):",
      round(100 * np.max(np.abs(risk_shares(covariance, w_capped) - equal_budget)), 4))
```

`bounds` เรียงตาม A/B/C/D จึงวางเพดาน C ที่ตำแหน่งสาม `constraints` กำหนดให้น้ำหนักรวมหนึ่ง ส่วน `lambda w: ...` เป็นฟังก์ชันสั้นที่รับ weights แล้วคืนค่าความคลาดเคลื่อนรวม

ได้ weights ประมาณ 20.8267%, 31.8297%, 30%, 17.3436% และ risk shares ประมาณ 29.7427%, 30.4014%, 10.6581%, 29.1978% ส่วนของ C ห่างเป้า 25% ประมาณ 14.3419 จุดเปอร์เซ็นต์ เรารายงานผลเป็นพอร์ตที่ fit ใกล้ risk budgets ภายใต้ cap และวัด residual ให้เห็น

Objective ที่ใช้ fit risk shares โดยตรงอาจไม่เป็น convex การที่ SLSQP แจ้ง success จึงไม่รับรองว่าเจอ global optimum ทุกกรณี ตัวอย่างนี้มีไว้แสดงผลของข้อจำกัด ไม่ได้แทนตัวแก้สมการ convex ของหัวข้อก่อน หากบังคับทั้ง sector limits, turnover และ liquidity ต้องนิยามว่าเมื่อทำ budgets ตรงไม่ได้ จะยอมเปลี่ยนเป้าหมายส่วนใดและวัดความคลาดเคลื่อนอย่างไร

<span id="risk-parity-volatility-target"></span>

## เปลี่ยนระดับ Volatility ด้วยเงินสดหรือเงินกู้

พอร์ต ERC ตั้งต้นมี volatility ประมาณ 10.3969% ถ้ากำหนด volatility เป้าหมาย $\sigma^*=20\%$ และสมมติผลตอบแทนเงินสดหรือต้นทุนกู้แน่นอนตลอดช่วง ให้เพิ่ม risky exposures ทุกตัวด้วยตัวคูณ

$$
k=\frac{\sigma^*}{\sigma_{\mathrm{ERC}}},
\qquad w_{\mathrm{risky}}=kw_{\mathrm{ERC}},
\qquad w_{\mathrm{cash}}=1-k.
$$

เมื่อ $k<1$ เหลือเงินสดเป็นบวก เมื่อ $k>1$ เงินสดติดลบหมายถึงกู้มาซื้อสินทรัพย์เพิ่ม ตัวอย่างนี้ได้ $k\approx1.9237$ จึงมี risky exposure ประมาณ 192.37% และเงินสด −92.37% ของเงินทุนเริ่มต้น

ทดลองหนึ่งปีสมมติให้ A/B/C/D ได้ผลตอบแทน −12%, −8%, +1%, −18% อัตราฝากเงิน 2% และอัตรากู้ 4% ต่อปี เป็นอัตราที่แน่นอนแยกกัน ไม่มีค่าธรรมเนียมหรือการเรียกหลักประกันระหว่างปี

```python
base_vol = np.sqrt(w_erc @ covariance @ w_erc)
target_vol = 0.20
risky_scale = target_vol / base_vol
cash_weight = 1.0 - risky_scale
scaled_weights = risky_scale * w_erc
scenario_returns = np.array([-0.12, -0.08, 0.01, -0.18])
lending_rate, borrowing_rate = 0.02, 0.04
funding_rate = lending_rate if cash_weight >= 0 else borrowing_rate
scenario_return = scaled_weights @ scenario_returns + cash_weight * funding_rate
print("Risky allocation (%):", round(100 * risky_scale, 4))
print("Cash allocation (%):", round(100 * cash_weight, 4))
print("Model volatility (%):", round(100 * np.sqrt(scaled_weights @ covariance @ scaled_weights), 4))
print("Risk shares:", np.round(risk_shares(covariance, scaled_weights), 6))
print("One-year scenario return after funding (%):", round(100 * scenario_return, 4))
print("End wealth from 100,000:", round(100000 * (1 + scenario_return), 2))
```

ถ้ามีเงินต้น 100,000 บาท พอร์ตนี้กู้ประมาณ 92,365.5 บาท และลงทุนในสินทรัพย์เสี่ยงรวมประมาณ 192,365.5 บาท ผลตอบแทนบนเงินต้นคือ

$$
R_{\mathrm{equity}}=(kw)^\top R+(1-k)r_{\mathrm{funding}}.
$$

เพราะ $(1-k)$ ติดลบ พจน์อัตรากู้จึงเป็นต้นทุน ผลตอบแทนสมมติหลังหักเงินกู้ประมาณ −15.2559% เหลือเงินทุนปลายปี 84,744.15 บาท ส่วน risk shares ยังเป็นตัวละ 25% และ volatility ตาม covariance ที่กำหนดเพิ่มเป็น 20%

20% เป็นเป้าหมาย SD ภายใต้แบบจำลอง ไม่ใช่เพดานขาดทุน ในการถือจริงอัตรากู้เปลี่ยนได้ มีข้อจำกัดหลักประกัน ต้นทุนซื้อขาย และความเสี่ยงถูกบังคับลดสถานะ หากต้นทุนเงินกู้มีความผันผวนหรือสัมพันธ์กับสินทรัพย์ ต้องรวมความเสี่ยงส่วนนั้นด้วย สูตร scale เฉพาะ risky covariance จะไม่ครบ

<span id="risk-parity-model-change"></span>

## Risk shares ที่ตั้งไว้เปลี่ยนเมื่อแบบจำลองเปลี่ยน

ตรึง weights ERC เดิม แล้วเปลี่ยน correlation ทุกคู่เป็น 0.80 โดยคง SD รายตัวไว้ จากนั้นเปรียบเทียบกับ ERC ที่คำนวณใหม่จากเมทริกซ์นั้น กรณีนี้เป็นการทดลองสมมติฐาน ไม่ใช่การพยากรณ์ตลาด

```python
stress_corr = np.full((4, 4), 0.8)
np.fill_diagonal(stress_corr, 1.0)
stress_cov = np.outer(asset_vol, asset_vol) * stress_corr
w_stress_erc = risk_budget_weights(stress_cov, equal_budget)
stress_table = pd.DataFrame({
    "Old model risk (%)": 100 * risk_shares(covariance, w_erc),
    "New model, old weights (%)": 100 * risk_shares(stress_cov, w_erc),
    "New ERC weight (%)": 100 * w_stress_erc
}, index=assets)
print(stress_table.round(4).to_string())
print("Old portfolio volatility under new model (%):",
      round(100 * np.sqrt(w_erc @ stress_cov @ w_erc), 4))
```

weights เดิมให้ shares ประมาณ 21.5975%, 25.0064%, 30.2674%, 23.1287% ภายใต้ covariance ใหม่ และ volatility เพิ่มเป็น 13.8038% จึงไม่ได้รักษา shares ตัวละ 25% ไว้เมื่อข้อมูลความเสี่ยงเปลี่ยน

weights ERC ที่คำนวณใหม่เท่ากับ IV เพราะเมทริกซ์ใหม่นี้มี correlation ทุกคู่เท่ากัน แต่การปรับ weights จริงต้องซื้อขายและอาจมีต้นทุน ระหว่างวันที่ปรับพอร์ต weights ยังเคลื่อนตามราคาสินทรัพย์ด้วย การไม่ใช้ expected returns เป็น input ไม่ได้ลบความคลาดเคลื่อนของ covariance การเลือก universe หรือความเสี่ยงจากช่วงข้อมูลที่ใช้ประมาณ

<span id="risk-parity-practice"></span>

## แบบฝึกหัด

โจทย์เป็นตัวอย่างใหม่ของบทนี้ ใช้ covariance และเงื่อนไขตามที่ระบุ

**1. สองสินทรัพย์ SD 30% และ 10% จะมี ERC weights เท่าไร ถ้า correlation เท่ากับ 0.40?**

<details><summary>ดูเฉลย</summary>

ใช้ inverse volatility ให้คะแนน $1/0.30$ และ $1/0.10$ จึงได้ weights 25%/75% ทั้งสองมี $w_i\sigma_i=0.075$ เท่ากันและ risk shares ตัวละ 50% correlation นี้ไม่ทำให้ variance เป็นศูนย์

</details>

**2. IV ของตัวอย่างสี่สินทรัพย์ให้ C รับ risk share 18.125% ได้อย่างไร?**

<details><summary>ดูเฉลย</summary>

เมื่อ $w_i\sigma_i$ เท่ากัน contributions เป็นสัดส่วนกับ correlation row sums แถว C รวม 1.45 ส่วนผลรวมทุกแถวเป็น 8 จึงได้ $1.45/8=0.18125$ หรือ 18.125%

</details>

**3. สองสินทรัพย์ที่ไม่สัมพันธ์กันมี SD เท่ากัน ตั้ง risk budgets 80%/20% ต้องใช้ weights 80%/20% หรือไม่?**

<details><summary>ดูเฉลย</summary>

ใช้ $w_i\propto\sqrt{b_i}/\sigma_i$ เมื่อ SD เท่ากันจะได้อัตราส่วน weights $\sqrt{0.8}:\sqrt{0.2}=2:1$ จึงลงเงิน 2/3 และ 1/3 การลง 80/20 จะให้ contributions เป็นสัดส่วน 0.64:0.04 หรือ shares ประมาณ 94.1176%/5.8824%

</details>

**4. เหตุใดการ normalize ตัวแปรช่วย $x$ จึงไม่ทำให้ risk budgets เปลี่ยน?**

<details><summary>ดูเฉลย</summary>

ให้ $s=\sum_jx_j$ เมื่อแทน $w=x/s$ contribution แต่ละตัวและ variance รวมจะถูกหารด้วย $s^2$ จึงตัดกันใน $p_i$ คุณสมบัตินี้ใช้กับ relative risk shares ไม่ใช่กับ objective ของ optimization ทุกประเภท

</details>

**5. ถ้า optimizer แจ้ง success แต่ risk shares ต่างจากเป้าหมาย 0.03 ควรรับคำตอบว่าเป็น ERC หรือไม่?**

<details><summary>ดูเฉลย</summary>

ต้องตรวจว่าความต่าง 0.03 คือ 3 จุดเปอร์เซ็นต์ ซึ่งเกิน tolerance $10^{-7}$ ของฟังก์ชันนี้มาก ควรตรวจ objective, input, constraints และการลู่เข้า โค้ดจะหยุดด้วย RuntimeError แทนการรายงานว่าทำ budgets ได้ตรง

</details>

**6. จำกัด C ไม่เกิน 30% แล้วได้ risk share C 10.6581% แปลว่าโปรแกรมผิดแน่หรือไม่?**

<details><summary>ดูเฉลย</summary>

เป้าหมายเดิมทำไม่ได้ภายใต้ cap เพราะคำตอบ ERC ของเมทริกซ์นี้ต้องลง C ประมาณ 44.8160% ต้องระบุว่ากำลังแก้ปัญหา fit ใกล้ budgets ภายใต้ข้อจำกัด และรายงาน residual ไม่เปลี่ยนชื่อผลเป็น exact ERC

</details>

**7. พอร์ต SD 10% ถูกขยาย risky exposure เป็น 1.5 เท่า จะมีเงินสดและ volatility เท่าไร?**

<details><summary>ดูเฉลย</summary>

เงินสด $1-1.5=-0.5$ คือกู้ 50% ของเงินทุนเดิม volatility เป็น 15% เมื่อ covariance คงเดิมและต้นทุนกู้แน่นอน risk shares ของ risky assets ไม่เปลี่ยน แต่ผลตอบแทนบนเงินทุนต้องหักต้นทุนเงินกู้ และไม่มีเพดานว่าขาดทุนต้องไม่เกิน 15%

</details>

**8. มี correlation ติดลบในข้อมูล แล้ว risk budgeting ใช้ไม่ได้เสมอไปหรือไม่?**

<details><summary>ดูเฉลย</summary>

ใช้ได้ในฟังก์ชันนี้เมื่อ covariance ยัง symmetric positive definite และ budgets เป็นบวกตามข้อกำหนด ตัวอย่างสามสินทรัพย์มี correlation −0.65 แต่คำนวณ weights ที่ให้ shares 20/50/30 ได้ กรณี perfect hedge ที่ variance ศูนย์หรือเมทริกซ์ singular ต้องจัดการต่างหาก

</details>

<span id="risk-parity-sources"></span>

## แหล่งที่มาและการทดลองต่อ

อ่าน Transcript ของ [Simplified risk parity portfolios](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/QHzyJ/simplified-risk-parity-portfolios) และ [Risk Parity Portfolios](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/OnWYS/risk-parity-portfolios) ครบจากหน้าคอร์สเมื่อ 3 ตุลาคม 2026 ใช้หัวข้อ inverse volatility, ERC และ risk diversification มาอธิบายด้วยข้อมูลสมมติใหม่ ไม่มีการทำซ้ำผลตอบแทนย้อนหลังที่แสดงในวิดีโอ

Jean-Charles Richard และ Thierry Roncalli, [Constrained Risk Budgeting Portfolios](https://arxiv.org/pdf/1902.05710), §2–3 อธิบายการสร้าง risk-budget portfolios ด้วย log barrier และปัญหาเมื่อเพิ่ม constraints บทนี้ใช้พจน์ความเสี่ยงแบบ quadratic ร่วมกับ log barrier โดยแสดงอนุพันธ์และตรวจ risk-share identity ได้โดยตรง หลัก Euler ที่ใช้คำนวณ contributions อ้างอิง [Tasche](https://arxiv.org/pdf/0708.2542), §3.1 การตรวจ PD ใช้ [NumPy Cholesky](https://numpy.org/doc/stable/reference/generated/numpy.linalg.cholesky.html) และตัวแก้ปัญหาใช้ [SciPy L-BFGS-B](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html)

โค้ดทั้งหมดเขียนขึ้นใหม่ ฟังก์ชัน solver ใช้ positive budgets กับ PD covariance ตามขอบเขตที่ระบุ บท [ทดลองวิธีจัดพอร์ตด้วยข้อมูลที่มีอยู่ก่อนลงทุน](diversification-backtest.html) จะใช้หน้าต่างข้อมูลย้อนหลัง กำหนดเวลาหาน้ำหนัก และหักต้นทุนซื้อขายก่อนเปรียบเทียบวิธีต่าง ๆ
