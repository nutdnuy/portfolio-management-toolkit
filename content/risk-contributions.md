---
title: "Risk Contribution: ใครสร้างความเสี่ยงให้พอร์ต"
description: แยกความเสี่ยงพอร์ตเป็นส่วนของแต่ละสินทรัพย์ คำนวณ Variance และ Volatility contributions ตรวจ marginal risk และแยกชื่อสินทรัพย์ออกจากแหล่งความเสี่ยง
---

# Risk Contribution: ใครสร้างความเสี่ยงให้พอร์ต

<p class="lead">ลงเงินครึ่งหนึ่งใน A ไม่ได้แปลว่า A สร้างความเสี่ยงครึ่งหนึ่งของพอร์ต ในตัวอย่างนี้ A ใช้เงิน 50% แต่มีส่วนต่อความแปรปรวนของพอร์ตประมาณ 68.15%</p>

[Risk contribution](glossary.html#risk-contribution) วัดว่าสินทรัพย์แต่ละตัวมีส่วนต่อความเสี่ยงรวมเท่าไร การคำนวณต้องใช้ทั้งน้ำหนัก ความผันผวนของสินทรัพย์ และการเคลื่อนไหวร่วมกับสินทรัพย์อื่น หากหุ้นสองตัวขึ้นลงพร้อมกัน การแยกถือคนละครึ่งยังอาจรับความเสี่ยงชนิดเดียวกันอยู่มาก

เราจะเริ่มจาก covariance ที่กำหนดให้ คำนวณส่วนของ A ด้วยมือ แล้วสร้างตารางครบทุกสินทรัพย์ บทนี้ใช้ volatility เป็นมาตรวัดความเสี่ยง จึงวัดการกระจายของผลตอบแทนรอบค่าเฉลี่ย ไม่ได้ครอบคลุมสภาพคล่อง ความเสียหายปลายหาง หรือความเสี่ยงผิดนัดทั้งหมด

ตัวเลขและโค้ดเป็นตัวอย่างสมมติที่เขียนขึ้นใหม่ สินทรัพย์ A/B/C/D ใช้ผลตอบแทนหน่วยทศนิยมและ covariance ในหน่วยปี ไม่มีการประมาณจากราคาตลาด รันโค้ดตามลำดับใน Notebook ใหม่ได้ด้วย NumPy และ pandas เนื้อหาประกอบ [Measuring risk contributions](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/rZNZ8/measuring-risk-contributions) ในคอร์ส Advanced Portfolio Construction and Analysis with Python

<span id="risk-contribution-inputs"></span>

## เริ่มจากพอร์ตที่มีเงินอยู่จริง

สมมติมีเงิน 1,000,000 บาท ลงใน A/B/C/D เท่ากับ 500,000 / 200,000 / 200,000 / 100,000 บาท น้ำหนักจึงเป็น

$$
w=(0.50,\;0.20,\;0.20,\;0.10)^\top,
\qquad \sum_iw_i=1.
$$

SD ของผลตอบแทนรายปีแต่ละตัวเท่ากับ 20%, 15%, 10%, 25% ตามลำดับ เราจะใช้ $\Sigma$ แทน [covariance matrix](glossary.html#covariance) และสร้างแต่ละช่องจาก

$$
\Sigma_{ij}=\rho_{ij}\sigma_i\sigma_j.
$$

เช่น correlation ของ A/B เท่ากับ 0.50 ทำให้ covariance เป็น $0.50\times0.20\times0.15=0.015$ ส่วนแนวทแยง A/A คือ $0.20^2=0.04$ อย่านำ SD 20 มาใส่แทน 0.20 เพราะจะทำให้ covariance ใหญ่ขึ้น 10,000 เท่า

```python
import numpy as np
import pandas as pd

assets = ["A", "B", "C", "D"]
asset_vol = np.array([0.20, 0.15, 0.10, 0.25])
correlation = np.array([
    [1.00, 0.50, 0.20, 0.65],
    [0.50, 1.00, 0.10, 0.40],
    [0.20, 0.10, 1.00, 0.15],
    [0.65, 0.40, 0.15, 1.00]
])
covariance = np.outer(asset_vol, asset_vol) * correlation
weights = np.array([0.50, 0.20, 0.20, 0.10])
portfolio_variance = weights @ covariance @ weights
portfolio_vol = np.sqrt(portfolio_variance)
print(pd.DataFrame(covariance, index=assets, columns=assets).round(5))
print(f"Annual portfolio variance: {portfolio_variance:.8f}")
print(f"Annual portfolio volatility: {100 * portfolio_vol:.4f}%")
```

`np.array` เก็บชุดตัวเลขตามลำดับ A/B/C/D และ `np.outer(asset_vol, asset_vol)` สร้างผลคูณ SD ทุกคู่ เครื่องหมาย `*` คูณตามช่อง ส่วน `@` คูณแบบเมทริกซ์ `weights @ covariance @ weights` จึงคำนวณผลรวมของ $w_iw_j\Sigma_{ij}$ ทุกคู่ ได้ความแปรปรวนพอร์ต

$$
V=w^\top\Sigma w=0.019845,
\qquad \sigma_p=\sqrt V=0.14087228.
$$

Volatility ของพอร์ตจึงประมาณ 14.0872% ต่อปี มีหน่วยเดียวกับ SD ของผลตอบแทน ส่วน $V$ มีหน่วยผลตอบแทนทศนิยมยกกำลังสอง `round` และรูปแบบ `:.4f` ลดทศนิยมเฉพาะตอนแสดงผล การคำนวณถัดไปยังใช้ค่าที่ไม่ปัดเศษ

<span id="variance-contributions"></span>

## คำนวณส่วนของ A ก่อน แล้วจึงรวมทั้งพอร์ต

ผลตอบแทนพอร์ตคือ $R_p=\sum_jw_jR_j$ ดังนั้น covariance ระหว่าง A กับพอร์ตเท่ากับ

$$
\operatorname{Cov}(R_A,R_p)
=\sum_j\Sigma_{Aj}w_j
=(\Sigma w)_A.
$$

วงเล็บ $(\Sigma w)_A$ หมายถึงสมาชิกตำแหน่ง A ของเวกเตอร์ $\Sigma w$ ในตัวอย่างนี้

$$
(\Sigma w)_A
=0.04(0.50)+0.015(0.20)+0.004(0.20)+0.0325(0.10)
=0.02705.
$$

คูณด้วยน้ำหนักของ A อีกครั้ง จะได้ส่วนของ A ที่จัดสรรจากความแปรปรวนรวม:

$$
c_A=w_A(\Sigma w)_A=0.50(0.02705)=0.013525.
$$

```python
a_covariance_terms = covariance[0] * weights
a_variance_terms = weights[0] * a_covariance_terms
print("Covariance between A and portfolio:", round(a_covariance_terms.sum(), 8))
print("A variance-allocation terms:", a_variance_terms)
print("A variance contribution:", round(a_variance_terms.sum(), 8))
print("A share of variance (%):", round(100 * a_variance_terms.sum() / portfolio_variance, 4))
```

Python เริ่มนับตำแหน่งจากศูนย์ `covariance[0]` จึงเลือกแถว A และ `weights[0]` เลือกน้ำหนัก A ตัวเลขสี่ตัวใน `a_variance_terms` คือ 0.010000, 0.001500, 0.000400 และ 0.001625 รวมเป็น 0.013525 เมื่อหารด้วยความแปรปรวนพอร์ต 0.019845 จะได้สัดส่วน 68.1532%

### Covariance ของคู่เดียวกันไปอยู่ที่ใคร

ขยาย variance ของพอร์ตสองตัวจะพบพจน์ร่วม $2w_Aw_B\Sigma_{AB}$ วิธีนี้ให้ครึ่งหนึ่งคือ $w_Aw_B\Sigma_{AB}$ อยู่กับ A และอีกครึ่งอยู่กับ B สำหรับคู่ A/B ในพอร์ตสี่ตัวของเรา พจน์ร่วมทั้งหมดเท่ากับ $2(0.50)(0.20)(0.015)=0.003$ จัดให้แต่ละตัว 0.0015

เรามองการแบ่งนี้เป็นตารางได้ แต่ละช่องใส่ $w_iw_j\Sigma_{ij}$ แล้วรวมตามแถว:

```python
weighted_covariance = np.outer(weights, weights) * covariance
variance_by_asset = weighted_covariance.sum(axis=1)
print(pd.DataFrame(weighted_covariance, index=assets, columns=assets).round(6))
print("Row sums:", variance_by_asset)
print("Matrix total equals portfolio variance:", np.isclose(weighted_covariance.sum(), portfolio_variance))
print("A/B combined cross term:", round(weighted_covariance[0, 1] + weighted_covariance[1, 0], 8))
```

`sum(axis=1)` รวมคอลัมน์ภายในแต่ละแถว จึงได้ $c_i$ ครบสี่ตัวเป็น 0.013525, 0.002760, 0.000935 และ 0.002625 ผลรวมเท่ากับ $V$ ทุกช่องที่อยู่ใน variance ถูกจัดสรรหนึ่งครั้งพอดี

คำว่า contribution ในที่นี้เป็นการแยก covariance ตามแบบจำลอง ไม่ใช่ข้อสรุปว่าสินทรัพย์ตัวใดเป็นสาเหตุของราคาที่เปลี่ยน และไม่ใช่กำไรหรือขาดทุนที่เกิดขึ้นจริงในปีใดปีหนึ่ง

<span id="euler-volatility"></span>

## เปลี่ยนจาก Variance เป็น Volatility contributions

ถ้าต้องการรายงานส่วนประกอบที่บวกกันได้ volatility 14.0872% เราต้องหาร $c_i$ ด้วย $\sigma_p$:

$$
RC_i=\frac{w_i(\Sigma w)_i}{\sigma_p},
\qquad \sum_iRC_i=\sigma_p.
$$

$RC_i$ คือ [component risk](glossary.html#component-risk) ในหน่วย volatility ส่วนสัดส่วนต่อความเสี่ยงรวมคือ

$$
p_i=\frac{RC_i}{\sigma_p}
=\frac{c_i}{V},
\qquad \sum_i p_i=1.
$$

จึงได้สัดส่วนเดียวกัน ไม่ว่าจะเริ่มจาก variance allocation แล้วหารด้วย $V$ หรือเริ่มจาก volatility contribution แล้วหารด้วย $\sigma_p$ สำหรับ A นั้น $RC_A\approx0.096009$ หรือ 9.6009 จุดเปอร์เซ็นต์ของ volatility พอร์ต 14.0872% คิดเป็น 68.1532% ของความเสี่ยงรวม

| ปริมาณ | สูตร | เมื่อรวมทุกสินทรัพย์ |
|---|---|---|
| Variance allocation $c_i$ | $w_i(\Sigma w)_i$ | $V$ |
| Volatility contribution $RC_i$ | $c_i/\sigma_p$ | $\sigma_p$ |
| Relative risk contribution $p_i$ | $c_i/V$ | 1 |

### เหตุใดสูตรอนุพันธ์ของ Variance มีเลข 2

[Marginal risk](glossary.html#marginal-risk) วัดความเปลี่ยนแปลงของความเสี่ยงเมื่อเพิ่ม exposure หรือขนาดการถือสินทรัพย์ต่อเงินทุนเริ่มต้นเล็กน้อย สำหรับ volatility เราได้

$$
m_i=\frac{\partial\sigma_p}{\partial w_i}
=\frac{(\Sigma w)_i}{\sigma_p},
\qquad RC_i=w_im_i.
$$

แต่อนุพันธ์ของ variance คือ $\partial V/\partial w_i=2(\Sigma w)_i$ หากคูณด้วย $w_i$ แล้วรวม จะได้ $2V$ เราจึงใช้ครึ่งหนึ่งของผลคูณนี้สำหรับ variance allocation $c_i$ สูตรสองชุดสอดคล้องกันผ่านกฎลูกโซ่ของ $\sqrt V$

<details>
<summary>อ่านต่อ: Euler allocation และการเพิ่มขนาดพอร์ต</summary>

เมื่อเพิ่มทุก exposure เป็น $k$ เท่าโดย $k>0$ ความแปรปรวนเพิ่มเป็น $k^2V$ แต่ volatility เพิ่มเป็น $k\sigma_p$ เรียกว่าความเป็น homogeneous degree 2 และ degree 1 ตามลำดับ Euler's theorem ให้ $\sum_iw_i\partial V/\partial w_i=2V$ และ $\sum_iw_i\partial\sigma_p/\partial w_i=\sigma_p$ เมื่ออนุพันธ์นิยามได้ เงื่อนไข $\sigma_p>0$ จึงจำเป็นสำหรับสูตร volatility ที่มีตัวหารนี้

</details>

สร้างฟังก์ชันเพื่อให้เรียกตารางเดิมกับพอร์ตอื่นได้ ฟังก์ชันรับ covariance และ exposure ตามลำดับเดียวกัน ตรวจขนาด ตัวเลขที่ขาดหาย ความสมมาตร และ positive semidefinite ก่อนคำนวณ

```python
def risk_components(cov, weights):
    cov = np.asarray(cov, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if weights.ndim != 1 or cov.shape != (weights.size, weights.size) or weights.size == 0:
        raise ValueError("Covariance and weights must have matching dimensions")
    if not np.isfinite(cov).all() or not np.isfinite(weights).all():
        raise ValueError("Inputs must be finite")
    if not np.allclose(cov, cov.T, rtol=1e-10, atol=1e-12):
        raise ValueError("Covariance must be symmetric")
    cov = (cov + cov.T) / 2
    eigenvalues = np.linalg.eigvalsh(cov)
    scale = max(np.abs(eigenvalues).max(), np.finfo(float).tiny)
    if eigenvalues.min() < -1e-10 * scale:
        raise ValueError("Covariance must be positive semidefinite")
    covariance_with_portfolio = cov @ weights
    variance = float(weights @ covariance_with_portfolio)
    if variance <= 0:
        raise ValueError("Positive portfolio variance is needed for risk shares")
    vol = np.sqrt(variance)
    variance_parts = weights * covariance_with_portfolio
    return pd.DataFrame({
        "Weight": weights,
        "Variance part": variance_parts,
        "Marginal vol": covariance_with_portfolio / vol,
        "Component vol": variance_parts / vol,
        "Risk share": variance_parts / variance
    })

components = risk_components(covariance, weights)
components.index = assets
print(components.round(6).to_string())
print("Component-vol sum:", round(components["Component vol"].sum(), 8))
print("Weighted variance-gradient sum:", round(weights @ (2 * covariance @ weights), 8))
```

`def` นิยามฟังก์ชันโดยยังไม่คำนวณจนกว่าจะเรียกใช้ `np.asarray(..., dtype=float)` แปลงข้อมูลเข้าเป็น array ตัวเลข ส่วน `raise ValueError` หยุดพร้อมบอกว่าข้อมูลชนิดใดผิด `eigvalsh` คำนวณ eigenvalues ของเมทริกซ์สมมาตร เราอนุโลมค่าติดลบระดับเล็กมากจากการปัดเศษ แต่ไม่ได้ซ่อม covariance ที่ใช้ไม่ได้ให้กลายเป็น covariance ใหม่

คอลัมน์ `Component vol` รวมเป็น 0.14087228 ขณะที่ `Risk share` รวมเป็นหนึ่ง ผลรวมจาก variance gradient เป็น 0.03969 ซึ่งเท่ากับ $2\times0.019845$ ฟังก์ชันไม่ได้บังคับ exposure รวมเป็นหนึ่ง เพราะเราจะใช้ตรวจพอร์ตที่มีเงินสดหรือกู้เงินได้ด้วย ต้องระบุงบเงินสดแยกเมื่อใช้กรณีเหล่านั้น

<span id="capital-versus-risk-concentration"></span>

## ลงเงินเท่ากันแล้ว ความเสี่ยงยังต่างกันได้

เปลี่ยนเป็น equal weight ตัวละ 25% แล้วคำนวณด้วย covariance เดิม:

```python
equal_weights = np.repeat(0.25, 4)
equal_components = risk_components(covariance, equal_weights)
comparison = pd.DataFrame({
    "Original weight (%)": 100 * weights,
    "Original risk (%)": 100 * components["Risk share"].to_numpy(),
    "EW weight (%)": 100 * equal_weights,
    "EW risk (%)": 100 * equal_components["Risk share"].to_numpy()
}, index=assets)
print(comparison.round(4).to_string())
for name, w in [("Original", weights), ("EW", equal_weights)]:
    shares = risk_components(covariance, w)["Risk share"].to_numpy()
    print(name, "effective assets =", round(1 / np.sum(w ** 2), 4),
          "effective risk contributions =", round(1 / np.sum(shares ** 2), 4))
```

D มีเงินลงทุน 25% แต่สร้างความเสี่ยงประมาณ 40.8438% ส่วน C มีเงิน 25% เท่ากันแต่สร้างความเสี่ยงเพียง 6.9120% D มีทั้ง SD สูงและ correlation กับ A/B ที่สูงกว่า C ในตัวอย่างนี้

เราเปรียบเทียบความกระจุกตัวด้วยสองตัวเลขได้ เมื่อ weights และ risk shares ไม่ติดลบ:

$$
N_{\mathrm{capital}}=\frac{1}{\sum_iw_i^2},
\qquad
N_{\mathrm{risk}}=\frac{1}{\sum_ip_i^2}.
$$

ค่าแรกคือ [effective number of assets](glossary.html#effective-number-assets) ส่วนค่าหลังคอร์สเรียกว่า [effective number of correlated bets](glossary.html#effective-number-bets) พอร์ตเดิมได้ประมาณ 2.9412 และ 1.9859 ตามลำดับ ส่วน equal weight ได้ 4 และ 3.1532

ถ้า risk shares เป็นตัวละ 25% จะได้ $N_{\mathrm{risk}}=4$ ถ้าความเสี่ยงทั้งหมดอยู่ที่ตัวเดียวจะได้ 1 ตัวเลขนี้บอกความสม่ำเสมอของส่วนแบ่งที่นิยามไว้ สินทรัพย์ทั้งสี่ยังอาจรับความเสี่ยงจากปัจจัยเศรษฐกิจร่วมกัน จึงไม่ควรอ่านค่า 4 ว่าพอร์ตมีสี่ความเสี่ยงอิสระ

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/advanced-capital-risk-mobile.svg">
<img src="assets/charts/advanced-capital-risk.svg" alt="สินทรัพย์ A ใช้เงิน 50% แต่มีส่วนแบ่งความเสี่ยงประมาณ 68.15% ส่วน C ใช้เงิน 20% แต่มีส่วนแบ่งความเสี่ยงประมาณ 4.71%" loading="lazy" width="720" height="560">
</picture>
<figcaption>ตัวอย่างสมมติสี่สินทรัพย์เดิม แท่งแต่ละสีรวมกันเป็น 100%: สีม่วงเป็นน้ำหนักเงินลงทุน สีเขียวเป็น relative risk contribution ซึ่งใช้ทั้งน้ำหนักและ covariance การแบ่งเงินจึงไม่เท่ากับการแบ่งความเสี่ยง</figcaption>
</figure>

<span id="marginal-funded-change"></span>

## เพิ่ม A ด้วยเงินจากที่ใด ต้องระบุให้ครบ

ค่า $m_A\approx0.192018$ เป็นอนุพันธ์เมื่อเพิ่ม exposure A และตรึง B/C/D ไว้ เช่นเพิ่ม A 0.01 หน่วยต่อเงินทุนเดิม โดยลดเงินสดที่ไม่มีความเสี่ยงลง 0.01 หน่วย การเปลี่ยนแปลง volatility โดยประมาณคือ $0.01m_A$

ถ้าพอร์ตลงทุนเต็มจำนวนและขาย C มาซื้อ A แทน น้ำหนักจะเปลี่ยนพร้อมกันสองช่อง ผลโดยประมาณต่อ volatility จึงเป็น

$$
\Delta\sigma_p\approx(m_A-m_C)\Delta w_A.
$$

เราตรวจอนุพันธ์ด้วยการขยับเล็กน้อยทั้งด้านบวกและลบ เรียกวิธีนี้ว่า central finite difference:

```python
h = 1e-6
unit_a = np.array([1.0, 0.0, 0.0, 0.0])
move_c_to_a = np.array([1.0, 0.0, -1.0, 0.0])
def vol_at(w):
    return np.sqrt(w @ covariance @ w)

free_derivative = (vol_at(weights + h * unit_a) - vol_at(weights - h * unit_a)) / (2 * h)
funded_derivative = (vol_at(weights + h * move_c_to_a) - vol_at(weights - h * move_c_to_a)) / (2 * h)
marginal_vol = components["Marginal vol"].to_numpy()
print("A derivative, holding other exposures fixed:", round(free_derivative, 8))
print("Analytical marginal volatility of A:", round(marginal_vol[0], 8))
print("A funded by C, directional derivative:", round(funded_derivative, 8))
print("Marginal A minus marginal C:", round(marginal_vol[0] - marginal_vol[2], 8))
print("Approximate vol change for 1 percentage-point C-to-A shift:", round(0.01 * funded_derivative, 8))
```

`h=1e-6` คือระยะขยับ 0.000001 หน่วยน้ำหนัก `unit_a` เปลี่ยนเฉพาะ A ส่วน `move_c_to_a` เพิ่ม A และลด C เท่ากัน เราไม่ได้ normalize weights ระหว่างคำนวณ เพราะจะเปลี่ยนทิศทางที่ต้องการตรวจ

โค้ดให้ $m_A-m_C\approx0.15883181$ ถ้าย้ายเงินจาก C ไป A 1 จุดเปอร์เซ็นต์ของพอร์ต volatility จะเพิ่มประมาณ 0.00158832 หน่วยทศนิยม หรือ 0.158832 จุดเปอร์เซ็นต์ นี่เป็นค่าประมาณเฉพาะบริเวณน้ำหนักปัจจุบัน เมื่อเปลี่ยนน้ำหนักมากควรคำนวณ $\sqrt{w^\top\Sigma w}$ ของพอร์ตใหม่โดยตรง

<span id="risk-contribution-units"></span>

## หน่วยเวลา หน่วยเปอร์เซ็นต์ และหน่วยบาท

ถ้าคูณ covariance ทั้งเมทริกซ์ด้วยค่าบวก $a$ จะได้ variance parts เพิ่ม $a$ เท่า และ volatility contributions เพิ่ม $\sqrt a$ เท่า แต่ risk shares ไม่เปลี่ยน เพราะตัวเศษและตัวหารเพิ่มเท่ากัน

ตัวอย่างใช้การหาร covariance ด้วย 12 ตาม convention แปลง annualized covariance เป็นรายเดือน กฎนี้อาศัยสมมติฐานการรวมผลตอบแทนที่ไม่มี serial covariance และพารามิเตอร์คงที่ตามที่ใช้ annualize ไม่ใช่สูตร exact สำหรับ variance ของผลตอบแทน simple ที่ทบต้นหนึ่งปีในทุกแบบจำลอง ส่วนการเปลี่ยนข้อมูลทศนิยมเป็นหน่วยเปอร์เซ็นต์คูณผลตอบแทนด้วย 100 จึงคูณ covariance ด้วย $100^2$

```python
monthly_components = risk_components(covariance / 12, weights)
percent_components = risk_components(covariance * 10000, weights)
capital = 1000000
money_components = capital * components["Component vol"]
print("Monthly model volatility (%):", round(100 * np.sqrt(portfolio_variance / 12), 4))
print("Shares unchanged across time units:", np.allclose(monthly_components["Risk share"], components["Risk share"].to_numpy()))
print("Shares unchanged across decimal/percent units:", np.allclose(percent_components["Risk share"], components["Risk share"].to_numpy()))
print("Currency component standard deviations:", money_components.round(2).to_dict())
print("Total currency standard deviation:", round(capital * portfolio_vol, 2))
```

ใน convention นี้ SD รายเดือนเป็น 4.0666% ส่วน risk shares ยังเหมือนเดิม เมื่อเงินทุนต้นงวดคงที่ 1,000,000 บาท ความผันผวนของกำไรขาดทุนในหน่วยเงินเท่ากับ $1{,}000{,}000\sigma_p\approx140{,}872.28$ บาท และ contribution ของ A เท่ากับประมาณ 96,008.95 บาท

ตัวเลข 96,008.95 บาทเป็นส่วนจัดสรรของ SD เงินพอร์ต ไม่ใช่ SD ของเงินที่ลง A เพียงตัวเดียว ซึ่งเท่ากับ $500{,}000\times20\%=100{,}000$ บาท และไม่ใช่วงเงินขาดทุนสูงสุดของ A

<span id="negative-risk-contribution"></span>

## สินทรัพย์ที่ช่วยหักล้างพอร์ตอาจมี Contribution ติดลบ

ใช้ตัวอย่างใหม่ที่แยกจาก A/B/C/D: X มี SD 20%, Y มี SD 10%, correlation เท่ากับ −0.80 และน้ำหนัก X/Y เท่ากับ 10%/90% จึงมี covariance $-0.80\times0.20\times0.10=-0.016$

สำหรับ X คำนวณได้

$$
c_X=0.10\{0.04(0.10)-0.016(0.90)\}=-0.00104.
$$

แม้ทั้งสองน้ำหนักเป็นบวก พจน์ covariance ที่ติดลบก็มีขนาดมากกว่าพจน์ variance ของ X เอง ทำให้ X มีส่วนหักล้างความผันผวนของพอร์ตในแบบจำลองนี้

```python
hedge_cov = np.array([[0.04, -0.016], [-0.016, 0.01]])
hedge_weights = np.array([0.10, 0.90])
hedge_components = risk_components(hedge_cov, hedge_weights)
hedge_components.index = ["X", "Y"]
hedge_vol = np.sqrt(hedge_weights @ hedge_cov @ hedge_weights)
print(hedge_components.round(6).to_string())
print("Portfolio volatility (%):", round(100 * hedge_vol, 4))
print("Raw 1/sum(shares squared):", round(1 / np.sum(hedge_components["Risk share"] ** 2), 4))
print("Volatility after removing X and holding 90% Y, 10% cash (%):", 100 * 0.9 * 0.1)
```

SD พอร์ตเป็น 7.4967% และ risk shares ของ X/Y เป็น −18.5053%/118.5053% รวมกัน 100% ค่าเกิน 100% ของ Y เกิดจากมี contribution ติดลบมาหักไว้ SD ของ X เองยังเป็นบวก 20%

หากขาย X แล้วพักเงิน 10% ไว้ในเงินสดที่มีผลตอบแทนแน่นอน โดยยังถือ Y 90% จะได้ volatility $0.90\times10\%=9\%$ สูงกว่าพอร์ตก่อนขาย ส่วนต่างของ volatility จากการขายทั้งหมดไม่จำเป็นต้องเท่ากับ component risk เพราะ component มาจากอนุพันธ์ที่น้ำหนักเดิม การขายออกทั้งตำแหน่งเป็นการเปลี่ยนที่มีขนาดจำกัด

ถ้านำ risk shares ชุดนี้ไปใส่ $1/\sum p_i^2$ จะได้ประมาณ 0.6951 เราจึงหยุดตีความเป็นจำนวน bets ระหว่าง 1 ถึง $N$ เมื่อมีส่วนแบ่งติดลบ ไม่แก้โดยเอาค่าสัมบูรณ์โดยไม่บอก เพราะจะเปลี่ยนนิยามการวัด

### กรณีที่ความเสี่ยงรวมเป็นศูนย์

ถ้า X/Y มี SD เท่ากัน 20%, correlation −1 และน้ำหนักตัวละ 50% ผลตอบแทนที่เบี่ยงจากค่าเฉลี่ยหักล้างกันพอดีในแบบจำลอง ได้ variance ศูนย์:

```python
zero_risk_cov = np.array([[0.04, -0.04], [-0.04, 0.04]])
zero_risk_weights = np.array([0.5, 0.5])
print("Perfect-hedge variance:", zero_risk_weights @ zero_risk_cov @ zero_risk_weights)
try:
    risk_components(zero_risk_cov, zero_risk_weights)
except ValueError as error:
    print(type(error).__name__ + ": " + str(error))
```

`try` ทดลองเรียกฟังก์ชัน และ `except` จับข้อผิดพลาดที่เราคาดไว้ ตัวอย่างนี้หยุดด้วยข้อความว่าต้องมี variance บวก เพราะสูตร $c_i/V$ กลายเป็น $0/0$ การรายงาน risk shares เป็น 50%/50% จะใส่คำตอบให้สัดส่วนที่ยังนิยามไม่ได้ กรณี variance ใกล้ศูนย์มากก็ไวต่อการปัดเศษและค่าประมาณ covariance จึงควรตรวจขนาดตัวหารก่อนนำผลไปใช้

<span id="asset-factor-risk"></span>

## แยกตามสินทรัพย์กับแยกตามปัจจัยตอบคนละเรื่อง

ตารางเดิมถามว่าส่วนของ A/B/C/D เท่าไร ถ้าทั้งสี่ตัวรับผลจากปัจจัยตลาดร่วมกัน เราอาจต้องถามต่อว่าปัจจัยนั้นสร้างความเสี่ยงเท่าไร โดยใช้ [factor model](multifactor-models.html) รูปแบบ

$$
R=Bf+\varepsilon,\qquad
\Sigma=B\Sigma_fB^\top+\Sigma_\varepsilon.
$$

$B$ เก็บ factor loadings โดยแถวเป็นสินทรัพย์ คอลัมน์เป็นปัจจัย $\Sigma_f$ เป็น covariance ของปัจจัย และ $\Sigma_\varepsilon$ เป็น covariance ของส่วนที่เหลือ สมการนี้สมมติว่า $\operatorname{Cov}(f,\varepsilon)=0$ หากไม่เป็นศูนย์ต้องเพิ่ม cross terms

สำหรับน้ำหนัก $w$ ให้ $g=B^\top w$ เป็น exposure ต่อปัจจัย เราแยก variance เป็น

$$
V=g^\top\Sigma_fg+w^\top\Sigma_\varepsilon w.
$$

ใช้กฎเดิมจัดให้ปัจจัย $k$ เป็น $g_k(\Sigma_fg)_k$ และให้ residual ของสินทรัพย์ $i$ เป็น $w_i(\Sigma_\varepsilon w)_i$ ตัวอย่างต่อไปสร้าง covariance ชุดใหม่จาก factor model โดยยังใช้น้ำหนัก 50/20/20/10 ตัวเลขจะไม่ใช่ risk shares ของเมทริกซ์ตั้งต้น

```python
loadings = np.array([[1.0, 0.1], [0.8, 0.5], [0.2, 1.0], [1.2, -0.2]])
factor_cov = np.array([[0.0144, 0.0012], [0.0012, 0.0036]])
residual_cov = np.diag(np.array([0.04, 0.05, 0.03, 0.06]) ** 2)
factor_model_cov = loadings @ factor_cov @ loadings.T + residual_cov
factor_exposure = loadings.T @ weights
factor_parts = factor_exposure * (factor_cov @ factor_exposure)
residual_parts = weights * (residual_cov @ weights)
factor_model_variance = weights @ factor_model_cov @ weights
factor_breakdown = pd.Series(np.r_[factor_parts, residual_parts],
                             index=["Factor 1", "Factor 2", "Residual A", "Residual B", "Residual C", "Residual D"])
print("Factor exposures:", factor_exposure)
print("Variance by factor and residual:")
print(factor_breakdown.round(8).to_string())
print("Risk shares (%):", (100 * factor_breakdown / factor_model_variance).round(4).to_dict())
print("Decomposition adds up:", np.isclose(factor_breakdown.sum(), factor_model_variance))
print("Asset shares for the same factor model (%):",
      np.round(100 * risk_components(factor_model_cov, weights)["Risk share"].to_numpy(), 4))
```

`loadings.T @ weights` เปลี่ยน exposure ในสินทรัพย์สี่ตัวเป็น exposure ในปัจจัยสองตัว ได้ $g=(0.82,0.33)^\top$ ปัจจัยทั้งสองมี covariance 0.0012 จึงยังมีพจน์ร่วม ส่วน residual covariance ใช้แนวทแยง เป็นสมมติฐานว่าความเสี่ยง residual แต่ละสินทรัพย์ไม่สัมพันธ์กัน

Factor 1 มีส่วนประมาณ 88.5910% ของ variance ในแบบจำลองใหม่นี้ ขณะที่ถ้าแยกตามสินทรัพย์ A มีส่วน 58.5214% ทั้งสองตารางบวกกลับเป็น variance รวมเดียวกัน แต่จัดกลุ่มส่วนประกอบต่างกัน ไม่ควรนำ factor shares ไปบวกกับ asset shares ซ้ำอีกครั้ง

ปัจจัยที่เลือกและวิธีแทนปัจจัยมีผลต่อการแบ่งนี้ การเปลี่ยน basis ของ factor model อาจเปลี่ยนส่วนที่ติดป้ายให้แต่ละปัจจัยได้ แม้ covariance ที่อธิบายพอร์ตยังเหมือนเดิม

<span id="duplicate-assets"></span>

## เพิ่มชื่อสินทรัพย์โดยไม่เพิ่มแหล่งความเสี่ยง

สมมติมีสินทรัพย์สองตัวที่ไม่สัมพันธ์กัน SD 20%/10% ลงน้ำหนัก 1/3 และ 2/3 ทำให้ทั้งสองมี risk share ตัวละ 50% ต่อมาเราแบ่งรายการแรกเป็นสองชื่อ แต่แต่ละชื่อถือ exposure เดิมเหมือนกันทุกอย่าง ลงเงินชื่อใหม่ละ 1/6 แทนการลง 1/3 ในชื่อเดียว

```python
base_cov = np.diag([0.20 ** 2, 0.10 ** 2])
base_weights = np.array([1 / 3, 2 / 3])
label_map = np.array([[1, 0], [1, 0], [0, 1]])
duplicate_cov = label_map @ base_cov @ label_map.T
duplicate_weights = np.array([1 / 6, 1 / 6, 2 / 3])
base_shares = risk_components(base_cov, base_weights)["Risk share"].to_numpy()
duplicate_shares = risk_components(duplicate_cov, duplicate_weights)["Risk share"].to_numpy()
print("Underlying exposure unchanged:", np.allclose(label_map.T @ duplicate_weights, base_weights))
print("Variance unchanged:", np.isclose(base_weights @ base_cov @ base_weights,
                                        duplicate_weights @ duplicate_cov @ duplicate_weights))
print("Original shares:", base_shares)
print("Shares after splitting first label:", duplicate_shares)
print("Effective risk contributions before/after:", 1 / np.sum(base_shares ** 2),
      round(1 / np.sum(duplicate_shares ** 2), 6))
```

แถวแรกและแถวสองของ `label_map` ชี้ไปสินทรัพย์เดิมตัวเดียวกัน จึงมี correlation กันเท่ากับหนึ่ง `label_map.T @ duplicate_weights` รวม exposure กลับมาแล้วได้ 1/3 และ 2/3 เหมือนเดิม ความแปรปรวนพอร์ตจึงไม่เปลี่ยน

เมื่อแบ่งตามชื่อใหม่ risk shares กลายเป็น 25%, 25%, 50% ทำให้ $N_{\mathrm{risk}}$ เพิ่มจาก 2 เป็น 2.666667 ทั้งที่ยังมีผลตอบแทนต้นทางเพียงสองชุด การเปรียบเทียบจำนวน bets จึงต้องตรึงวิธีแบ่งสินทรัพย์หรือกลุ่มความเสี่ยงไว้ด้วย โดยเฉพาะเมื่อกองทุนหลายกองถือหลักทรัพย์ซ้ำกัน

<span id="risk-contribution-sensitivity"></span>

## Contribution เปลี่ยนเมื่อ Covariance เปลี่ยน

กลับมาที่พอร์ต A/B/C/D น้ำหนักเดิม เราทดลองให้ทุกคู่มี correlation เท่ากับ 0.80 โดยคง SD แต่ละตัวไว้ กรณีนี้เป็นการเปลี่ยนสมมติฐานพร้อมกันทั้งเมทริกซ์ ไม่ใช่การคาดว่าตลาดจะมี correlation 0.80

```python
higher_corr = np.full((4, 4), 0.8)
np.fill_diagonal(higher_corr, 1.0)
higher_cov = np.outer(asset_vol, asset_vol) * higher_corr
higher_components = risk_components(higher_cov, weights)
sensitivity = pd.DataFrame({
    "Original risk (%)": 100 * components["Risk share"].to_numpy(),
    "Higher-correlation risk (%)": 100 * higher_components["Risk share"].to_numpy()
}, index=assets)
print(sensitivity.round(4).to_string())
print("Volatility under the two models (%):", round(100 * portfolio_vol, 4),
      round(100 * np.sqrt(weights @ higher_cov @ weights), 4))
```

Volatility เพิ่มจาก 14.0872% เป็น 16.3966% แต่ risk share ของ A ลดจาก 68.1532% เป็น 59.5127% สัดส่วนที่ลดลงไม่ได้แปลว่าความเสี่ยงรวมลดลง ตัวหารและ contribution ของสินทรัพย์อื่นเปลี่ยนพร้อมกัน จึงควรดูทั้ง volatility รวมและส่วนแบ่ง

เมื่อนำไปใช้กับข้อมูลราคา covariance ต้องประมาณจากช่วงข้อมูลที่มีอยู่แล้ว มีวันที่ หน่วยเวลา และวิธีจัดการ missing values ชัดเจน หากใช้คนละช่วงเวลาคำนวณแต่ละคู่ อาจได้เมทริกซ์ที่ใช้เป็น covariance ไม่ได้ ทบทวน [การประมาณ covariance](covariance-estimation.html) ก่อนนำ risk contribution ไปใช้ตัดสินใจจัดพอร์ต

<span id="risk-contribution-practice"></span>

## แบบฝึกหัด

โจทย์เหล่านี้ใช้ข้อมูลสมมติในหน้า เป็นแบบฝึกที่เขียนขึ้นใหม่

**1. B ใช้เงิน 20% มีส่วนต่อ variance และ risk share เท่าไร?**

<details><summary>ดูเฉลย</summary>

$(\Sigma w)_B=0.015(0.5)+0.0225(0.2)+0.0015(0.2)+0.015(0.1)=0.0138$ จึงได้ $c_B=0.2(0.0138)=0.00276$ และ $p_B=0.00276/0.019845\approx13.9078\%$

</details>

**2. ถ้าคูณน้ำหนักทุกตัวด้วย 2 โดยกู้เงินเพิ่ม variance, volatility และ risk shares เปลี่ยนอย่างไร?**

<details><summary>ดูเฉลย</summary>

ภายใต้ covariance เดิมและต้นทุนเงินกู้ที่แน่นอน variance เพิ่ม 4 เท่าเป็น 0.07938, volatility เพิ่ม 2 เท่าเป็นประมาณ 28.1745% และ risk shares ของ risky assets ไม่เปลี่ยน น้ำหนักเสี่ยงรวมเป็น 2 จึงมีน้ำหนักเงินสด −1 หรือหนี้เท่ากับเงินทุนเริ่มต้น ต้องหักต้นทุนกู้ในผลตอบแทนด้วย

</details>

**3. ทำไมคูณ variance gradient ด้วย weights แล้วรวมจึงไม่ได้ variance เดิม?**

<details><summary>ดูเฉลย</summary>

Variance เป็น homogeneous degree 2 ผลรวมจึงเป็น $2V$ ใช้ $c_i=\tfrac12w_i\partial V/\partial w_i$ เพื่อให้รวมได้ $V$ ส่วน volatility เป็น degree 1 จึงใช้ $RC_i=w_i\partial\sigma_p/\partial w_i$ ได้โดยตรง

</details>

**4. การเพิ่ม A ด้วยเงินจาก C ใช้ marginal volatility ของ A เพียงตัวเดียวได้หรือไม่?**

<details><summary>ดูเฉลย</summary>

ต้องรวมผลจากการลด C ด้วย ใช้ $m_A-m_C$ คูณขนาดเงินที่ย้ายในหน่วยน้ำหนัก สำหรับ 1 จุดเปอร์เซ็นต์ได้ volatility เพิ่มโดยประมาณ 0.158832 จุดเปอร์เซ็นต์ เมื่อใช้การเพิ่มเล็กน้อยรอบพอร์ตเดิม

</details>

**5. ในตัวอย่าง X/Y ส่วนของ X ติดลบ แปลว่า X ไม่มีความเสี่ยงหรือไม่?**

<details><summary>ดูเฉลย</summary>

X ยังมี SD 20% แต่ covariance กับพอร์ตเป็นลบที่น้ำหนักปัจจุบัน จึงมีผลหักล้างความเสี่ยงที่วัดด้วย volatility การเปลี่ยน covariance หรือน้ำหนักอาจเปลี่ยนเครื่องหมาย contribution และไม่ได้รับประกันว่าจะป้องกันการขาดทุนในทุกสถานการณ์

</details>

**6. ถ้าแบ่งสินทรัพย์หนึ่งตัวออกเป็นสองชื่อเหมือนกันทุกอย่าง แล้ว ENCB เพิ่มขึ้น เรากระจายความเสี่ยงเพิ่มหรือยัง?**

<details><summary>ดูเฉลย</summary>

ตัวอย่างแสดงว่า exposure ต้นทางและ variance ไม่เปลี่ยน ENCB ที่เพิ่มมาจากการแบ่งส่วนประกอบเป็นคนละชื่อ ต้องตรวจ underlying holdings หรือ factor exposures ก่อนสรุปว่าพอร์ตมีแหล่งความเสี่ยงเพิ่ม

</details>

**7. พอร์ตสองตัว hedge กันจน variance ศูนย์ ควรรายงาน risk shares เท่าไร?**

<details><summary>ดูเฉลย</summary>

สูตร relative risk contribution ใช้ variance เป็นตัวหาร จึงยังนิยามไม่ได้ในกรณีนี้ ควรรายงาน variance ศูนย์ตามแบบจำลองและระบุว่า shares คำนวณไม่ได้ แทนการใส่ศูนย์หรือ 50%/50% เอง

</details>

<span id="risk-contribution-sources"></span>

## แหล่งที่มาและบทถัดไป

อ่าน Transcript ของ [Measuring risk contributions](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/rZNZ8/measuring-risk-contributions) ครบจากหน้าคอร์สเมื่อ 3 ตุลาคม 2026 แล้วเรียบเรียงใหม่ด้วยตัวอย่างคนละชุด บทเรียนใช้การจัดสรร variance และ relative shares ตามหัวข้อคอร์ส พร้อมแยกจาก volatility contributions ให้เห็นหน่วยชัดเจน

หลัก Euler allocation ตรวจจาก Dirk Tasche, [Capital Allocation to Business Units and Sub-Portfolios: The Euler Principle](https://arxiv.org/pdf/0708.2542), §2.2, §3.1 และ Appendix A สูตรการแยก factor covariance ในหน้านี้ขยายจากสมการ $R=Bf+\varepsilon$ ภายใต้สมมติฐานที่ระบุ ส่วนการตรวจ eigenvalues ใช้ [NumPy eigvalsh](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigvalsh.html) โค้ดและตารางทั้งหมดเขียนและคำนวณขึ้นใหม่ ไม่ต้องใช้ toolkit หรือข้อมูลตลาดของคอร์ส

บทถัดไปใช้ $p_i$ เป็นเป้าหมายในการหาน้ำหนัก: [Risk Parity: แบ่งงบความเสี่ยงก่อนแบ่งเงิน](risk-parity.html)
