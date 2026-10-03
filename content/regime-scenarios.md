---
title: "Regime Scenarios: รวมความเสี่ยงจากหลายภาวะตลาด"
description: คำนวณ mixture mean และ covariance รวม ตรวจความแปรปรวนจากสถานการณ์โดยตรง อ่าน expected shortfall แบบถ่วง probability และแยก Monte Carlo error จาก model error
---

# Regime Scenarios: รวมความเสี่ยงจากหลายภาวะตลาด

<p class="lead">หากตลาดปกติให้ผลตอบแทนเฉลี่ยบวก แต่ตลาดตึงเครียดให้ผลตอบแทนเฉลี่ยลบ การเฉลี่ย covariance สองชุดยังนับความเสี่ยงไม่ครบ เราต้องรวมความต่างของค่าเฉลี่ยทั้งสองภาวะด้วย</p>

บท [Market Regimes](market-regimes.html) อธิบายโอกาสของแต่ละสถานะและเวลาที่รู้ข้อมูล บทนี้จะรับความน่าจะเป็นนั้นมาเป็นสมมติฐาน แล้วคำนวณผลตอบแทนและความเสี่ยงของพอร์ตในหนึ่งปีข้างหน้า เริ่มด้วย mean และ covariance ตามสถานะ ต่อด้วยรายการสถานการณ์แบบมีผลตอบแทนแน่นอนในแต่ละแถว และจบด้วยการสุ่ม Monte Carlo

ตัวอย่างทั้งสามส่วนเป็นข้อมูลสมมติ ส่วนรายการหกสถานการณ์เป็นชุดใหม่ที่มี moments ของตนเอง ไม่ใช่การ discretize ชุด Normal ให้ได้ moments เดิมโดยอัตโนมัติ โค้ดใช้ NumPy กับ pandas เท่านั้น ทุกผลตอบแทนเก็บเป็นทศนิยมต่อปี และทุกพอร์ตในตัวอย่างไม่มี leverage ไม่มีค่าซื้อขาย และถือน้ำหนักต้นงวดตามที่ระบุตลอดช่วงหนึ่งปีโดยไม่ปรับระหว่างปี

```python
import numpy as np
import pandas as pd

np.set_printoptions(precision=6, suppress=True)
```

<span id="conditional-scenario-inputs"></span>

## เริ่มจากสิ่งที่รู้ภายใต้แต่ละภาวะ

มีสินทรัพย์สมมติ A และ B เรากำหนดความน่าจะเป็นปีหน้า Calm 70% และ Stress 30% พร้อมค่าเฉลี่ยและ covariance แบบมีเงื่อนไขดังนี้

| สมมติฐานรายปี | Calm | Stress |
|---|---:|---:|
| ความน่าจะเป็น | 0.70 | 0.30 |
| ค่าเฉลี่ย A | 8% | −12% |
| ค่าเฉลี่ย B | 3% | 2% |
| SD ของ A | 10% | 20% |
| SD ของ B | 5% | 8% |
| Correlation A/B | 0.20 | −0.125 |

Covariance คู่ A/B ใน Calm จึงเท่ากับ $0.20(0.10)(0.05)=0.001$ ส่วนใน Stress เท่ากับ $-0.125(0.20)(0.08)=-0.002$ ค่าแนวทแยงคือ SD ยกกำลังสอง ตัวเลข correlation ของตัวอย่างนี้กำหนดเพื่อให้คำนวณตามได้ ไม่ใช่ข้ออ้างว่าพันธบัตรหรือสินทรัพย์ใดต้อง hedge หุ้นได้ในวิกฤต

```python
scenario_p = np.array([0.70, 0.30])
scenario_means = np.array([[0.08, 0.03], [-0.12, 0.02]])
scenario_covs = np.array([[[0.0100, 0.0010], [0.0010, 0.0025]],
                          [[0.0400, -0.0020], [-0.0020, 0.0064]]])
scenario_w = np.array([0.60, 0.40])
print("Conditional portfolio means:", scenario_means @ scenario_w)
print("State probabilities:", scenario_p)
```

`scenario_means` มี shape `(2, 2)` คือสองสถานะ สองสินทรัพย์ ส่วน `scenario_covs` มี shape `(2, 2, 2)` คือ covariance หนึ่งเมทริกซ์ต่อสถานะ น้ำหนัก `[0.60, 0.40]` รวมเป็นหนึ่ง

ค่าเฉลี่ยพอร์ตเมื่อ Calm คือ $0.6(0.08)+0.4(0.03)=0.06$ หรือ 6% เมื่อ Stress คือ $0.6(-0.12)+0.4(0.02)=-0.064$ หรือ −6.4% ในขั้นนี้เราไม่ได้บอกว่าทุกปีในสถานะเดียวกันให้ผลตอบแทนเท่ากัน ยังมีการกระจายรอบค่าเฉลี่ยตาม covariance ของสถานะนั้น

ความน่าจะเป็น 70/30 เป็น input สำหรับปีที่จะลงทุน หากเริ่มจาก filtered probabilities ของปีปัจจุบัน ต้องคูณ transition matrix เพื่อได้ predicted probabilities ของปีถัดไปก่อน ตามสูตร $p_{t+1\mid t}=p_{t\mid t}P$ ในบทก่อน ทั้ง probability และพารามิเตอร์ต้องใช้เฉพาะข้อมูลที่รู้ก่อนช่วงลงทุนเริ่ม สำหรับ 70/30 ที่เป็น stationary distribution ของตัวอย่าง การคูณ P ให้ค่าเดิม แต่กรณีทั่วไปอาจเปลี่ยน ต้องประเมินความคลาดเคลื่อนของค่าประมาณเหล่านี้ด้วย

<span id="total-mixture-covariance"></span>

## ความเสี่ยงรวมมีส่วนภายในและระหว่างภาวะ

ให้ $p_s$ เป็นโอกาสของสถานะ $s$, $\mu_s$ เป็นเวกเตอร์ค่าเฉลี่ย และ $\Sigma_s$ เป็น covariance ภายในสถานะ ค่าเฉลี่ยรวมได้จากการถ่วง probability:

$$\bar\mu=\sum_s p_s\mu_s.$$

แต่ covariance รวมต้องมีสองพจน์:

$$
\Sigma_{\rm mix}
=\underbrace{\sum_s p_s\Sigma_s}_{\text{within-state}}
+\underbrace{\sum_s p_s(\mu_s-\bar\mu)(\mu_s-\bar\mu)^\top}_{\text{between-state}}.
$$

พจน์แรกวัดความแกว่งที่ยังเหลือเมื่อรู้สถานะแล้ว พจน์ที่สองวัดความต่างของจุดศูนย์กลางแต่ละสถานะ ก่อนรู้ว่าสถานะใดจะเกิด เรายังไม่รู้ว่าผลตอบแทนจะกระจายรอบจุดศูนย์กลางใดด้วย สูตรนี้มาจาก law of total covariance และใช้ได้เมื่อมี second moments จำกัด ไม่ต้องสมมติ Normal เพื่อให้สูตรเป็นจริง

คำนวณ A ด้วยมือ: ค่าเฉลี่ยรวม $0.7(0.08)+0.3(-0.12)=0.02$ ส่วน within variance คือ $0.7(0.01)+0.3(0.04)=0.019$ และ between variance คือ

$$0.7(0.08-0.02)^2+0.3(-0.12-0.02)^2=0.0084.$$

ดังนั้น variance รวมของ A เท่ากับ $0.0274$ ไม่ใช่ $0.019$

```python
def mixture_moments(probabilities, means, covariances):
    p, mu, cov = (np.asarray(a, dtype=float) for a in [probabilities, means, covariances])
    if (p.ndim != 1 or mu.ndim != 2 or mu.shape[0] != len(p)
        or cov.shape != (len(p), mu.shape[1], mu.shape[1])
        or not all(np.isfinite(a).all() for a in [p, mu, cov])
        or np.any(p < 0) or not np.isclose(p.sum(), 1)):
        raise ValueError("Check probabilities, shapes and finite values")
    if not np.allclose(cov, cov.transpose(0, 2, 1)) or np.linalg.eigvalsh(cov).min() < -1e-12:
        raise ValueError("Each covariance must be symmetric positive semidefinite")
    mean = p @ mu
    centered = mu - mean
    within = np.einsum("k,kij->ij", p, cov)
    between = (centered * p[:, None]).T @ centered
    return mean, within + between, within, between

scenario_mean, scenario_cov, scenario_within, scenario_between = mixture_moments(
    scenario_p, scenario_means, scenario_covs)
print("Mixture mean:", scenario_mean)
print("Within-state covariance:\n", scenario_within)
print("Between-state covariance:\n", scenario_between)
print("Total covariance:\n", scenario_cov)
```

ฟังก์ชันตรวจว่า probabilities ไม่ติดลบ รวมเป็นหนึ่ง และ covariance แต่ละชุดสมมาตร positive semidefinite เมทริกซ์ชนิดนี้ให้ variance ที่ไม่ติดลบเมื่อคำนวณกับทุกเวกเตอร์น้ำหนัก ดู [นิยาม positive semidefinite](glossary.html#positive-semidefinite)

`centered = mu - mean` คือส่วนต่างของ mean แต่ละสถานะจาก mean รวม `p[:, None]` เปลี่ยน probability จากแถวเป็นคอลัมน์เพื่อคูณทุกสินทรัพย์ในสถานะเดียวกัน ส่วน `einsum("k,kij->ij", p, cov)` บอก NumPy ให้ถ่วงเมทริกซ์แต่ละสถานะด้วย probability แล้วรวมดัชนีสถานะ `k`

ผลที่ได้คือ

$$
\bar\mu=(0.020,0.027)^\top,\qquad
\Sigma_{\rm mix}=\begin{pmatrix}0.0274&0.00052\\0.00052&0.003691\end{pmatrix}.
$$

Covariance คู่ A/B มี within $0.0001$ และ between $0.00042$ รวม $0.00052$ แม้ภายใน Stress จะมี covariance ติดลบ แต่เมื่อเปลี่ยนจาก Calm ไป Stress ค่าเฉลี่ยของทั้ง A และ B ลดลงพร้อมกัน จึงเพิ่มพจน์ between ที่เป็นบวก

<span id="mixture-portfolio-risk"></span>

## คูณน้ำหนักแล้วอ่านหน่วยให้ตรง

เมื่อใช้พอร์ต $w=(0.6,0.4)^\top$:

$$E[R_p]=w^\top\bar\mu,\qquad
\operatorname{Var}(R_p)=w^\top\Sigma_{\rm mix}w,
\qquad \operatorname{SD}(R_p)=\sqrt{w^\top\Sigma_{\rm mix}w}.$$

```python
scenario_portfolio_mean = scenario_w @ scenario_mean
scenario_portfolio_variance = scenario_w @ scenario_cov @ scenario_w
scenario_portfolio_sd = np.sqrt(scenario_portfolio_variance)
scenario_sd_without_between = np.sqrt(scenario_w @ scenario_within @ scenario_w)
print(f"Annual expected return: {100 * scenario_portfolio_mean:.4f}%")
print(f"Annual variance: {scenario_portfolio_variance:.8f}")
print(f"Annual SD: {100 * scenario_portfolio_sd:.4f}%")
print(f"SD omitting between-state variation: {100 * scenario_sd_without_between:.4f}%")
```

ค่าเฉลี่ยพอร์ตคือ 2.28% ต่อปี variance เท่ากับ 0.01070416 ในหน่วยผลตอบแทนทศนิยมยกกำลังสอง และ SD ประมาณ 10.3461% ต่อปี ถ้าใช้เพียง covariance เฉลี่ยภายในสถานะ SD จะเหลือประมาณ 8.6459% ซึ่งขาดส่วนที่มาจากความต่างของค่าเฉลี่ยสถานะ

การคูณ variance ด้วย 100 ไม่ทำให้เป็น SD หน่วยเปอร์เซ็นต์ ต้องถอดรากก่อนแล้วค่อยคูณ 100 ขณะเดียวกัน ค่าเฉลี่ย 2.28% เป็น arithmetic expectation ของหนึ่งปี ไม่ใช่ CAGR ของพอร์ตที่ถือหลายปีภายใต้การสลับสถานะ

ถ้า mean ทุกสถานะเท่ากัน พจน์ between จะเป็นศูนย์ แต่ SD หรือ correlation ภายในแต่ละสถานะยังต่างกันได้ และการแจกแจงรวมอาจมีหางต่างจาก Normal ชุดเดียว การเก็บไว้เพียง mean/covariance จึงไม่เก็บรูปร่างการแจกแจงทั้งหมด

<span id="finite-weighted-scenarios"></span>

## สร้างรายการสถานการณ์ที่คำนวณตรงได้

อีกวิธีหนึ่งเขียนผลตอบแทนในอนาคตที่เป็นไปได้เป็นแถว แล้วกำหนด probability ของแต่ละแถว เช่น ปีที่ A ได้ −35% และ B ได้ −4% มีโอกาส 12% ภายใต้ชุดสมมติใหม่ต่อไปนี้ แต่ละแถวเป็นทางเลือกของปีเดียวกัน ไม่ใช่ปีที่ต้องเกิดเรียงต่อกัน

สามแถวแรกมี probability รวม 70% และสามแถวท้ายรวม 30% เพื่อแสดงการแตกสถานะใหญ่เป็นเหตุการณ์ย่อย หากเริ่มจากความน่าจะเป็นภายใน Calm `[0.5,0.3,0.2]` แล้วคูณ 0.7 จะได้ `[0.35,0.21,0.14]` ต้องถ่วงแบบเดียวกันให้ทุกสถานะก่อนรวมรายการ

```python
finite_returns = np.array([[0.15, 0.05], [0.07, 0.02], [-0.05, 0.03],
                           [-0.35, -0.04], [-0.15, 0.04], [0.08, 0.09]])
finite_p = np.array([0.35, 0.21, 0.14, 0.12, 0.105, 0.075])
finite_mean = finite_p @ finite_returns
finite_centered = finite_returns - finite_mean
finite_cov = (finite_centered * finite_p[:, None]).T @ finite_centered
print(pd.DataFrame({"Probability": finite_p, "Asset A (%)": 100 * finite_returns[:, 0],
                    "Asset B (%)": 100 * finite_returns[:, 1]}))
print("Finite-scenario mean:", finite_mean)
print("Finite-scenario covariance:\n", finite_cov)
```

`finite_p @ finite_returns` ถ่วงผลตอบแทนแต่ละแถวด้วย probability ได้ mean ของ A 0.845% และ B 3.205% ต่อปี จากนั้นหัก mean และคำนวณ weighted covariance สูตรเดียวกับค่าคาดหมายของการแจกแจงไม่ต่อเนื่อง

$$\mu_F=\sum_j p_jR_j,\qquad
\Sigma_F=\sum_jp_j(R_j-\mu_F)(R_j-\mu_F)^\top.$$

เราใช้ probabilities ที่นิยามการแจกแจงครบแล้ว ไม่ใช่การประมาณ sample covariance แบบตัวหาร $n-1$ จึงไม่มีการแก้ `ddof` เพิ่ม หากแถวเป็นตัวอย่างสุ่มจากประชากรเพื่อประมาณ covariance จะเป็นโจทย์อีกแบบหนึ่ง

ค่าเฉลี่ยและ covariance ของหกแถวนี้ไม่เท่ากับชุดก่อนหน้า การจับคู่ให้ moments ตรงต้องเป็นขั้นตอนออกแบบสถานการณ์เพิ่มเติม ไม่เกิดขึ้นเพียงเพราะจำนวนแถวมากหรือแบ่ง probability เป็น 70/30 เหมือนกัน

<span id="scenario-moment-identity"></span>

## ความแปรปรวนจากแถวตรงกับสูตรเมทริกซ์

ผลตอบแทนพอร์ตในแถว $j$ คือ $R_{p,j}=R_j^\top w$ คำนวณ mean และ variance โดยตรงจากหกแถวได้ แล้วเปรียบเทียบกับ $w^\top\Sigma_Fw$

```python
finite_portfolio = finite_returns @ scenario_w
finite_portfolio_mean = finite_p @ finite_portfolio
finite_direct_variance = finite_p @ (finite_portfolio - finite_portfolio_mean) ** 2
finite_matrix_variance = scenario_w @ finite_cov @ scenario_w
print(f"Direct expected return: {100 * finite_portfolio_mean:.4f}%")
print(f"Direct variance: {finite_direct_variance:.8f}")
print(f"Matrix variance: {finite_matrix_variance:.8f}")
print("Same quantity:", np.isclose(finite_direct_variance, finite_matrix_variance))
```

พอร์ต 60/40 ได้ mean 1.7890% และ variance 0.01171861 ทั้งสองวิธีตรงกัน เพราะใช้แถวและ probabilities ชุดเดียวกัน ความเท่ากันนี้เป็นเอกลักษณ์ทางพีชคณิต ไม่ต้องใช้ Normal และไม่ต้องรอให้จำนวนสถานการณ์มากจนเข้าใกล้อนันต์

หาก mean/covariance มาจากค่าที่ตั้งไว้ภายนอก แต่เราสุ่มข้อมูลจำนวนจำกัดมาคำนวณ sample moments ตัวเลขย่อมคลาดกันได้ สิ่งที่ตรงกันแน่นอนคือ variance โดยตรงกับ variance ผ่าน covariance ที่คำนวณจากสถานการณ์สุ่มชุดเดียวกันและ normalization เดียวกัน

<span id="weighted-scenario-shortfall"></span>

## อ่านหางขาดทุนเมื่อแต่ละสถานการณ์มีน้ำหนักต่างกัน

ให้ loss $L_j=-R_{p,j}$: ผลตอบแทน −22.6% คือ loss +22.6% ส่วนกำไรมี loss ติดลบ [Expected shortfall](extreme-risk.html) ที่ระดับ confidence 95% เฉลี่ย loss ของ probability mass 5% ที่แย่ที่สุด โดยต้องใช้เพียงบางส่วนของ probability แถวขอบเขตได้

ผลตอบแทนพอร์ต 60/40 ในหกแถวเรียงตามลำดับเดิมคือ 11%, 5%, −1.8%, −22.6%, −7.4% และ 8.4% เหตุการณ์ที่แย่ที่สุดมี loss 22.6% และ probability 12% ซึ่งมากกว่าหาง 5% อยู่แล้ว ดังนั้น ES95 เท่ากับ 22.6% โดยใช้เพียง 5% จาก 12% ของแถวนั้น

ถ้า confidence เป็น 80% หางต้องมี probability 20% ใช้แถว loss 22.6% ครบ 12% และใช้ 8% จากแถว loss 7.4% ที่มีทั้งหมด 10.5% จะได้

$$\operatorname{ES}_{80\%}=
\frac{0.12(0.226)+0.08(0.074)}{0.20}=0.1652.$$

```python
def scenario_es(losses, probabilities, confidence=0.95):
    losses, p = np.asarray(losses, float), np.asarray(probabilities, float)
    if (losses.ndim != 1 or len(losses) == 0 or p.shape != losses.shape
        or not np.isfinite(losses).all() or not np.isfinite(p).all()
        or np.any(p < 0) or not np.isclose(p.sum(), 1)
        or not np.isfinite(confidence) or not 0 < confidence < 1):
        raise ValueError("Need finite losses, probabilities summing to one, and 0 < confidence < 1")
    order = np.argsort(-losses, kind="stable")
    ordered_loss, ordered_p = losses[order], p[order]
    tail_mass = 1 - confidence
    mass_before = np.r_[0.0, np.cumsum(ordered_p[:-1])]
    used = np.minimum(ordered_p, np.maximum(tail_mass - mass_before, 0))
    return used @ ordered_loss / tail_mass

finite_es95 = scenario_es(-finite_portfolio, finite_p, 0.95)
finite_es80 = scenario_es(-finite_portfolio, finite_p, 0.80)
print(f"95% expected shortfall: {100 * finite_es95:.4f}%")
print(f"80% expected shortfall: {100 * finite_es80:.4f}%")
```

ฟังก์ชันเรียง loss จากมากไปน้อย `mass_before` เก็บ probability สะสมก่อนแต่ละแถว `maximum` ตรวจว่ายังขาดหางอีกเท่าไร และ `minimum` จำกัดไม่ให้ใช้เกิน probability ของแถวนั้น เมื่อนำ loss คูณ probability ที่ใช้แล้วหารขนาดหาง จะได้ ES95 22.6000% และ ES80 16.5200%

หากหลายแถวมี loss เท่ากัน การแบ่ง probability หางระหว่างแถวเหล่านั้นไม่เปลี่ยนค่า ES เพราะ loss ต่อหน่วยเท่ากัน วิธีเลือกทุกแถวที่ loss เกินหรือเท่ากับ VaR แล้วเฉลี่ยใหม่ทั้งแถวอาจใช้ probability มากเกินหางที่ต้องการ จึงไม่เท่ากับนิยามนี้เมื่อมีมวล probability ที่ขอบเขต

ES เป็นค่าเฉลี่ยภายในหาง ไม่ใช่ขาดทุนสูงสุด และ confidence 95% ไม่ได้หมายความว่าการขาดทุนจะไม่เกิน ES ด้วย probability 95% ดูความต่างของ VaR กับ ES ใน [บทความเสี่ยงหาง](extreme-risk.html)

<span id="compare-scenario-portfolios"></span>

## เปรียบเทียบพอร์ตด้วยสถานการณ์ชุดเดียวกัน

ลองเพิ่มน้ำหนัก A จาก 0% เป็น 100% ทีละ 25 จุดเปอร์เซ็นต์ และใส่ส่วนที่เหลือใน B ทุกพอร์ตใช้ probabilities และผลตอบแทนหกแถวเดิม เปลี่ยนเพียงน้ำหนัก

```python
finite_comparison = []
for equity_weight in [0, 0.25, 0.50, 0.75, 1]:
    w = np.array([equity_weight, 1 - equity_weight])
    portfolio = finite_returns @ w
    finite_comparison.append({"A weight": equity_weight,
        "Mean (%)": 100 * (finite_p @ portfolio),
        "SD (%)": 100 * np.sqrt(w @ finite_cov @ w),
        "ES 95% (%)": 100 * scenario_es(-portfolio, finite_p)})
finite_comparison = pd.DataFrame(finite_comparison)
print(finite_comparison.round(4))
```

ในชุดสมมตินี้ การเพิ่ม A ทำให้ mean ลดลง ขณะที่ SD และ ES95 สูงขึ้น ตัวอย่างพอร์ต A 25% ได้ mean 2.615%, SD 6.1299% และ ES95 11.75% ส่วนพอร์ต A 75% ได้ mean 1.435%, SD 12.8870% และ ES95 27.25%

ผลเช่นนี้มาจากสถานการณ์ที่เรากำหนด ไม่ใช่กฎว่า A ซึ่งมีความเสี่ยงสูงต้องให้ expected return ต่ำกว่า B เสมอ การประเมินพอร์ตจากแบบจำลองจึงต้องแสดง input ให้ผู้อ่านตรวจได้ รวมทั้งตรวจความไวต่อ probability และผลตอบแทนของแถวที่มีอิทธิพลสูง

ตารางนี้สำรวจห้าน้ำหนักที่กำหนด ไม่ใช่การแก้ optimization ต่อเนื่อง หากจะหาน้ำหนักจริงต้องกำหนด objective, ข้อจำกัดน้ำหนัก, ผลตอบแทนขั้นต่ำหรือ liability รวมถึงต้นทุน แล้วทดสอบด้วยข้อมูลที่ไม่ได้ใช้ตั้งโจทย์ พอร์ตที่ให้ objective ดีที่สุดภายในสถานการณ์ชุดหนึ่งยังขึ้นกับความถูกต้องของชุดนั้น

<span id="simulate-mixture-scenarios"></span>

## สุ่มจาก mixture แล้วเทียบกับ moments ที่ตั้งไว้

กลับไปยังพารามิเตอร์ Calm/Stress ในส่วนแรก คราวนี้สมมติผลตอบแทนร่วมของ A/B เป็น multivariate Normal ภายในแต่ละสถานะ ขั้นสุ่มหนึ่งปีคือเลือกสถานะตาม 70/30 ก่อน แล้วสุ่มผลตอบแทนตาม mean และ covariance ของสถานะที่เลือก จึงเป็น mixture ของสอง Normal ไม่ใช่ Normal ชุดเดียวที่ใช้ค่าเฉลี่ยพารามิเตอร์

```python
scenario_rng = np.random.default_rng(401)
scenario_count = 100000
scenario_states = (scenario_rng.random(scenario_count) >= scenario_p[0]).astype(int)
scenario_draws = np.empty((scenario_count, 2))
for state in [0, 1]:
    selected = scenario_states == state
    shock = scenario_rng.standard_normal((selected.sum(), 2))
    L = np.linalg.cholesky(scenario_covs[state])
    scenario_draws[selected] = scenario_means[state] + shock @ L.T
scenario_mc_mean = scenario_draws.mean(axis=0)
scenario_mc_cov = np.cov(scenario_draws, rowvar=False, ddof=0)
print("Monte Carlo mean:", scenario_mc_mean)
print("Theoretical mean:", scenario_mean)
print("Largest covariance error:", round(np.abs(scenario_mc_cov - scenario_cov).max(), 8))
```

`default_rng(401)` ตั้งตัวสร้างเลขสุ่มให้ทำซ้ำได้ `random` สร้างเลขในช่วง 0 ถึง 1 ค่าตั้งแต่ 0.70 ขึ้นไปถูกกำหนดเป็น Stress ส่วน mask `selected` เลือกแถวของสถานะนั้นมาสร้างผลตอบแทน

`cholesky` ให้เมทริกซ์ $L$ ที่ $LL^\top=\Sigma_s$ เมื่อ `shock` มีสมาชิก Normal อิสระ mean 0 และ variance 1 การคูณแถว `shock @ L.T` ทำให้ covariance ตรงกับสถานะตามแบบจำลอง จากนั้นบวก mean ของสถานะ วิธีนี้เทียบเท่าการสร้าง multivariate Normal ตาม mean/covariance ที่กำหนด ดูเงื่อนไขเมทริกซ์ใน [NumPy multivariate_normal](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.multivariate_normal.html)

100,000 ตัวอย่างให้ mean โดยประมาณ `[0.018898, 0.026982]` ต่างจาก `[0.02, 0.027]` และ covariance คลาดมากที่สุดประมาณ 0.00008945 แม้สร้างข้อมูลจากแบบจำลองที่รู้จริง sample moments ก็ไม่จำเป็นต้องตรงค่าประชากรพอดี

นี่เป็นการสุ่มปีข้างหน้าอย่างอิสระหลายครั้ง ไม่ใช่ 100,000 ปีที่เดินต่อกันด้วย Markov transition และ Normal ของ simple return ยังมีหางต่ำกว่า −100% ทางทฤษฎี การนำไปจำลองความมั่งคั่งหลายปีต้องเลือกแบบจำลองราคาหรือผลตอบแทนให้เหมาะกับการคำนวณนั้น

<span id="scenario-monte-carlo-error"></span>

## จำนวนตัวอย่างลด sampling error ไม่ได้ซ่อมสมมติฐาน

สำหรับค่าเฉลี่ยพอร์ตจากตัวอย่างที่สุ่มเป็นอิสระกัน MC standard error ประมาณได้ด้วย

$$\operatorname{SE}(\widehat\mu_p)=s_p/\sqrt N.$$

$s_p$ คือ sample SD ของผลตอบแทนพอร์ต และ $N$ คือจำนวนสถานการณ์สุ่ม จำนวน observations ที่มากขึ้นลดความแกว่งของค่าเฉลี่ยจำลองรอบค่าเฉลี่ยของโมเดล แต่ไม่ทำให้ probability 70/30 หรือ conditional means ใกล้ตลาดจริงขึ้นเอง

```python
scenario_mc_portfolio = scenario_draws @ scenario_w
scenario_mc_se = scenario_mc_portfolio.std(ddof=1) / np.sqrt(scenario_count)
scenario_mc_mean_error = scenario_mc_portfolio.mean() - scenario_portfolio_mean
print(f"Sample mean: {100 * scenario_mc_portfolio.mean():.4f}%")
print(f"Mean standard error: {100 * scenario_mc_se:.4f} percentage points")
print(f"Sample-minus-theory mean: {100 * scenario_mc_mean_error:.4f} percentage points")
```

Mean พอร์ตจำลองได้ประมาณ 2.2132% เทียบค่าทฤษฎี 2.28% ส่วน SE ประมาณ 0.0328 จุดเปอร์เซ็นต์ ความต่างครั้งนี้ −0.0668 จุดเปอร์เซ็นต์ หรือประมาณสอง SE เป็นความเป็นไปได้จากการสุ่ม ไม่ควรเลือก seed ใหม่เพียงเพื่อให้ตัวเลขดูใกล้ทฤษฎีขึ้น

SE นี้เป็นของ mean ไม่ใช่ของ variance, ES หรือความน่าจะเป็นหาง ซึ่งต้องใช้ตัวประมาณความคลาดเคลื่อนที่เหมาะกับแต่ละสถิติ และสูตร $1/\sqrt N$ ใช้กับสถานการณ์อิสระตามที่สร้าง ไม่ใช่จำนวนปีที่มี serial dependence แล้วนับทุกปีเป็นอิสระ

<span id="scenario-probability-sensitivity"></span>

## เปลี่ยนความน่าจะเป็นแล้วคำนวณใหม่ทั้งสอง moments

หากโอกาส Stress เปลี่ยน ค่าเฉลี่ยรวมเปลี่ยน และพจน์ between-state ก็เปลี่ยนตาม เราจะคง conditional means/covariances และน้ำหนักพอร์ตไว้ แล้วทดลอง Stress 10%, 30% และ 50%

```python
scenario_sensitivity = []
for stress_probability in [0.10, 0.30, 0.50]:
    p = np.array([1 - stress_probability, stress_probability])
    mean, cov, _, _ = mixture_moments(p, scenario_means, scenario_covs)
    scenario_sensitivity.append({"Stress probability": stress_probability,
        "Mean (%)": 100 * (scenario_w @ mean),
        "SD (%)": 100 * np.sqrt(scenario_w @ cov @ scenario_w)})
scenario_sensitivity = pd.DataFrame(scenario_sensitivity)
print(scenario_sensitivity.round(4))
```

Mean พอร์ตเปลี่ยนจาก 4.76% เป็น 2.28% และ −0.20% ส่วน SD เปลี่ยนจากประมาณ 8.2839% เป็น 10.3461% และ 11.5395% การเปลี่ยน probability จึงไม่ได้แค่เลื่อนค่าเฉลี่ยของการแจกแจงโดยรักษาความเสี่ยงเดิม

หากลงทุนหลายปี เราต้องกำหนดด้วยว่าสถานะของปีต่อไปสัมพันธ์กับปีนี้อย่างไร สองแบบจำลองอาจมี probability และ moments ของปีเดียวกันเท่ากัน แต่ให้ลำดับเหตุการณ์ต่างกัน เมื่อมีการถอนเงิน ลำดับเหล่านั้นส่งผลต่อจำนวนเงินที่เหลือ บท [Endowment Simulation](endowment-simulation.html) จะคำนวณประเด็นนี้ด้วยบัญชีเงินรายปี

<span id="regime-scenario-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

1. ถ้า probability ของ Calm/Stress เปลี่ยนเป็น 50/50 ค่าเฉลี่ย A เป็นเท่าไร

<details><summary>เฉลยข้อ 1</summary>

$0.5(0.08)+0.5(-0.12)=-0.02$ หรือ −2% ต่อปี ต้องเปลี่ยน between covariance ด้วย เพราะ mean รวมที่ใช้หักออกเปลี่ยนแล้ว

</details>

2. ถ้าทั้งสองสถานะมี mean เท่ากัน แต่ covariance ต่างกัน จะมี between-state covariance หรือไม่

<details><summary>เฉลยข้อ 2</summary>

ไม่มี เพราะ $\mu_s-\bar\mu=0$ ทุกสถานะ แต่ mixture อาจยังไม่เป็น Normal ชุดเดียว หากความแปรปรวนภายในต่างกันมาก รูปร่างและหางรวมจึงยังต่างได้

</details>

3. สำหรับ A ในตัวอย่างหลัก หากละพจน์ between จะขาด variance ไปเท่าไร

<details><summary>เฉลยข้อ 3</summary>

ขาด 0.0084 จาก variance รวม 0.0274 คิดเป็นประมาณ 30.66% ของ variance รวม ตัวเลขนี้เป็นสัดส่วน variance ไม่ใช่ส่วนต่าง SD 30.66 จุดเปอร์เซ็นต์

</details>

4. เหตุใด covariance ของรายการหกสถานการณ์จึงไม่หารด้วยจำนวนแถวลบหนึ่ง

<details><summary>เฉลยข้อ 4</summary>

เพราะ probabilities นิยามการแจกแจงที่กำลังคำนวณอยู่แล้ว จึงใช้ค่าคาดหมาย $\sum p_j(R_j-\mu)(R_j-\mu)^\top$ การประมาณ covariance ประชากรจากตัวอย่างสุ่มเป็นอีกปัญหาหนึ่งที่อาจใช้ตัวปรับ small-sample ต่างกัน

</details>

5. สำหรับพอร์ต 60/40 ถ้าคำนวณ ES90 จากหกสถานการณ์ ได้เท่าไร

<details><summary>เฉลยข้อ 5</summary>

หางแย่ที่สุด 10% ยังอยู่ภายในแถวที่ loss 22.6% ซึ่งมี probability 12% จึงได้ ES90 เท่ากับ 22.6% เช่นเดียวกับ ES95 ในตัวอย่างนี้

</details>

6. ถ้าใช้ทุกแถวที่ loss มากกว่า 7.4% เพื่อคำนวณ ES80 จะผิดตรงไหน

<details><summary>เฉลยข้อ 6</summary>

จะได้เพียงแถว loss 22.6% ที่มี probability 12% แต่ต้องการหาง 20% ต้องใช้เพิ่มอีก 8% จากแถว loss 7.4% การเปลี่ยนเป็นเงื่อนไขมากกว่าหรือเท่าก็จะรวม 22.5% ซึ่งเกินหาง จึงต้องแบ่งมวล probability ที่ขอบเขต

</details>

7. ต้องเพิ่มจำนวนตัวอย่างจาก 100,000 เป็นเท่าไรจึงคาดว่า SE ของ mean ลดครึ่งหนึ่ง โดยแบบจำลองและวิธีสุ่มเดิม

<details><summary>เฉลยข้อ 7</summary>

เพิ่มเป็น 400,000 เพราะ SE แปรผกผันกับ $\sqrt N$ การเพิ่มสองเท่าลด SE ได้เพียงตัวคูณ $1/\sqrt2$ และแม้เพิ่มเป็นสี่เท่าก็ไม่ได้ลด model error

</details>

8. เปรียบเทียบ variance โดยตรงจากชุดสุ่มกับสูตรเมทริกซ์แล้วไม่ตรง ควรตรวจอะไรเป็นลำดับแรก

<details><summary>เฉลยข้อ 8</summary>

ตรวจว่าใช้ returns แถวเดียวกัน probabilities เดียวกัน น้ำหนักเรียงสินทรัพย์ตรงกัน และตัวหาร covariance เดียวกันหรือไม่ หากด้านหนึ่งใช้ covariance ประชากรที่กำหนดไว้ แต่ด้านหนึ่งใช้ตัวอย่างสุ่ม จะมี sampling error เพิ่มเข้ามา ความไม่ตรงในกรณีนั้นไม่ได้หักล้างเอกลักษณ์ของ finite scenarios

</details>

<span id="regime-scenario-sources"></span>

## แหล่งที่มาและขอบเขตของตัวอย่าง

ทีมอ่าน transcript เต็มของ [A scenario based portfolio model](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/ZtY1n/a-scenario-based-portfolio-model) และ [A two regime portfolio example](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/xCMTv/a-two-regime-portfolio-example) รวมทั้งหน้า [ข้อมูลประกอบ scenario model](https://www.coursera.org/learn/python-machine-learning-for-investment-management/supplement/KlXGS/information-on-scenario-based-portfolio-model-video) และ [Regime-aware asset allocation](https://www.coursera.org/learn/python-machine-learning-for-investment-management/supplement/5sfFH/regime-aware-asset-allocation) เมื่อ 3 ตุลาคม 2026 ไม่ได้อ่านรายงาน PDF แนบครบ จึงไม่อ้างว่าตัวอย่างนี้ทำซ้ำผลวิจัยในรายงาน

สูตร ตัวเลข และโค้ดเป็นตัวอย่างใหม่ ตรวจ identity ของ covariance และ probability-weighted tail โดยตรง บทนี้ใช้ mean–variance ได้เพราะมี second moments ไม่ได้กำหนดว่า returns ต้องเป็น Normal และแยก variance $w^\top\Sigma w$ ออกจาก SD ที่ต้องถอดราก การสุ่มใช้ Normal เฉพาะส่วน Monte Carlo เพื่อแสดง sampling error ส่วนรายการหกสถานการณ์เป็นการแจกแจงไม่ต่อเนื่องที่กำหนดครบในหน้า
