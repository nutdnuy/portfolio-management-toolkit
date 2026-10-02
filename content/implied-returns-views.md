---
title: "Implied Returns: เริ่มจากพอร์ตแล้วระบุ Views"
description: ถอดผลตอบแทนส่วนเกินที่รองรับน้ำหนักพอร์ต อธิบาย risk aversion เงินสดและข้อจำกัดงบประมาณ แล้วเขียนมุมมองแบบ absolute และ relative ด้วย P Q และ Omega
---

# Implied Returns: เริ่มจากพอร์ตแล้วระบุ Views

<p class="lead">ถ้าเรารู้แล้วว่าพอร์ตตั้งต้นถือสินทรัพย์ A 50%, B 30% และ C 20% ผลตอบแทนคาดหมายแบบใดจึงทำให้การถือน้ำหนักนี้สมเหตุผลภายใต้แบบจำลองที่เลือก?</p>

ใน [บทประมาณ expected return](expected-return-estimation.html) เราเริ่มจากข้อมูลเพื่อหาค่าผลตอบแทนคาดหมาย แล้วจึงนำค่านั้นไปจัดพอร์ต บทนี้เริ่มจากน้ำหนักพอร์ตที่กำหนดไว้ ย้อนกลับไปหาชุดผลตอบแทนที่รองรับพอร์ตนั้น จากนั้นเขียนความเห็นที่ต่างจากชุดตั้งต้นให้เป็นตัวเลขที่ตรวจสอบได้

ตัวอย่าง A/B/C ทั้งหมดเป็นข้อมูลสมมติ มีช่วงเวลาหนึ่งปีและเก็บผลตอบแทนเป็นทศนิยม เรากำหนด covariance, น้ำหนักพอร์ต และพารามิเตอร์ความชอบเสี่ยงเพื่อศึกษาสูตร ตัวเลขผลตอบแทนที่ได้ไม่ได้มาจากราคาตลาดหรือคำพยากรณ์ของผู้วิเคราะห์ โค้ดใช้ NumPy กับ pandas และรันตามลำดับใน Notebook ใหม่ได้โดยไม่ต้องนำตัวแปรจากบทก่อนเข้ามา

| ช่วงเรียน | คำถามที่ใช้ตรวจความเข้าใจ |
|---|---|
| [ย้อนจากน้ำหนักไปหาผลตอบแทน](#reverse-optimization) | ต้องรู้อะไรเพิ่มจากน้ำหนักพอร์ตบ้าง |
| [สร้างตัวอย่าง A/B/C](#fixture-and-covariance) | Covariance ชุดนี้ใช้คำนวณความเสี่ยงได้หรือไม่ |
| [ผลตอบแทนโดยนัย](#implied-excess-returns) | ทำไมจึงได้ $\Pi=\delta\Sigma w_0$ |
| [เกณฑ์ตัดสินและเงินสด](#mean-variance-utility) | นักลงทุนเลือกน้ำหนักภายใต้ข้อจำกัดใด |
| [ข้อจำกัดงบประมาณ](#budget-constraint) | ทำไมน้ำหนักเดียวกันรองรับ mean ได้หลายชุด |
| [สร้าง P และ Q](#constructing-views) | มุมมองต่อ C ต่างจากมุมมอง A เทียบกับ B อย่างไร |
| [ความไม่แน่นอนของมุมมอง](#view-uncertainty) | ค่าใน $\Omega$ เป็น SD, variance หรือความน่าจะเป็น |
| [ตรวจ inputs](#validating-views) | รูปร่าง หน่วย และข้อมูลซ้ำทำให้การคำนวณผิดอย่างไร |

<span id="reverse-optimization"></span>

## ย้อนโจทย์จากน้ำหนักพอร์ตไปหาผลตอบแทน

การจัดพอร์ตตามปกติเริ่มจากผลตอบแทนคาดหมาย $\mu$ กับ covariance $\Sigma$ แล้วแก้โจทย์หาน้ำหนัก $w$ ส่วน reverse optimization กำหนดน้ำหนัก $w_0$ ไว้ก่อน แล้วหาผลตอบแทนที่ทำให้พอร์ตนี้เป็นคำตอบของโจทย์ที่ระบุ

[Implied returns](glossary.html#implied-returns) หมายถึงผลตอบแทนที่ถอดกลับจากสมมติฐานเหล่านี้ หากเปลี่ยน covariance หรือเกณฑ์ตัดสินของนักลงทุน ผลตอบแทนโดยนัยก็เปลี่ยนได้แม้ใช้น้ำหนักเดิม จึงต้องเก็บทั้งน้ำหนักและสมมติฐานที่ใช้ถอดกลับไว้ด้วย

พอร์ตตั้งต้นอาจเป็นดัชนีตามมูลค่าตลาด หรือ benchmark ที่ผู้ลงทุนกำหนด ถ้าเลือกพอร์ตอื่น เราอธิบายผลลัพธ์ว่าเป็นผลตอบแทนที่รองรับ benchmark นั้น การเรียกว่าเป็นผลตอบแทนดุลยภาพของตลาดต้องมีสมมติฐานตลาดเพิ่มเติม ไม่ได้เกิดจากการใส่น้ำหนักลงในสูตรเพียงอย่างเดียว

ใน Coursera ตอน [Extracting Implied Expected Returns](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/nyHIO/extracting-implied-expected-returns) ใช้พอร์ต benchmark เป็นจุดเริ่มก่อนเพิ่มมุมมองของผู้ลงทุน บทนี้จะระบุเกณฑ์ mean–variance และเรื่องเงินสดให้ครบ เพราะถ้ารู้เฉพาะน้ำหนักของพอร์ต เราจะยังระบุระดับ expected return ได้ไม่เอกลักษณ์

<span id="fixture-and-covariance"></span>

## กำหนดสินทรัพย์ น้ำหนัก และช่วงเวลาของตัวอย่าง

ให้ $N=3$ เป็นจำนวนสินทรัพย์ เรียงลำดับ A, B, C เหมือนกันในทุกเวกเตอร์และทุกแถวคอลัมน์ของเมทริกซ์ พอร์ตตั้งต้นคือ

$$
w_0=\begin{bmatrix}0.50\\0.30\\0.20\end{bmatrix},\qquad
\Sigma=\begin{bmatrix}
0.0400&0.0120&0.0080\\
0.0120&0.0225&0.0045\\
0.0080&0.0045&0.0100
\end{bmatrix}.
$$

$\Sigma$ เป็น [covariance](glossary.html#covariance) ของผลตอบแทนหนึ่งปี แถว A คอลัมน์ B เท่ากับ 0.012 จึงต้องเท่ากับแถว B คอลัมน์ A ตัวเลขบนแนวทแยงเป็น variance ของแต่ละสินทรัพย์ ถอดรากที่สองได้ SD 20%, 15% และ 10% ตามลำดับ ค่า 0.04 จึงเป็น $0.20^2$ ไม่ใช่ SD 4%

กำหนดอัตราปลอดความเสี่ยงของงวดนี้ $r_f=0.02$ หรือ 2% และ [risk aversion](glossary.html#risk-aversion) $\delta=2.5$ พารามิเตอร์ตัวหลังจะคูณต้นทุนความเสี่ยงในเกณฑ์ตัดสินที่เราจะเขียนต่อไป ทั้งสองค่าเป็นสมมติฐานของตัวอย่าง

เมทริกซ์ covariance ต้องสมมาตรและเป็น [positive semidefinite หรือ PSD](glossary.html#positive-semidefinite) เพื่อให้ $x^\top\Sigma x\geq0$ สำหรับน้ำหนัก $x$ ทุกชุด ถ้าเป็น positive definite หรือ PD จะได้ค่ามากกว่าศูนย์สำหรับ $x\ne0$ และแก้ระบบสมการย้อนกลับได้เอกลักษณ์ ตัวอย่างนี้ใช้ PD

```python
import numpy as np
import pandas as pd

assets = pd.Index(["A", "B", "C"], name="Asset")
covariance = np.array([
    [0.0400, 0.0120, 0.0080],
    [0.0120, 0.0225, 0.0045],
    [0.0080, 0.0045, 0.0100],
])
benchmark_weights = np.array([0.50, 0.30, 0.20])
risk_aversion = 2.5
risk_free_rate = 0.02

def validate_covariance(matrix, require_pd=False):
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or matrix.size == 0:
        raise ValueError("Covariance must be a nonempty square matrix")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("Covariance entries must be finite")
    if not np.allclose(matrix, matrix.T, rtol=1e-10, atol=1e-12):
        raise ValueError("Covariance must be symmetric")
    eigenvalues = np.linalg.eigvalsh(matrix)
    if eigenvalues.min() < -1e-12:
        raise ValueError("Covariance must be positive semidefinite")
    if require_pd and eigenvalues.min() <= 1e-12:
        raise ValueError("This calculation requires positive definite covariance")
    return matrix

covariance = validate_covariance(covariance, require_pd=True)
print("Annual SD (%):", np.sqrt(np.diag(covariance)) * 100)
print("Eigenvalues:", np.round(np.linalg.eigvalsh(covariance), 8))
print("Benchmark weight sum:", benchmark_weights.sum())
```

ผลลัพธ์ให้ SD `[20. 15. 10.]` เปอร์เซ็นต์ eigenvalues ประมาณ `[0.00778767, 0.01641472, 0.04829761]` และผลรวมน้ำหนัก 1 ทุก eigenvalue เป็นบวก จึงผ่านเงื่อนไข PD ในตัวอย่างนี้

`np.diag(covariance)` อ่านแนวทแยง `np.linalg.eigvalsh` คำนวณ eigenvalues ของเมทริกซ์สมมาตร ส่วน `np.allclose` ยอมให้ต่างกันเล็กน้อยจากการแทนเลขทศนิยมในคอมพิวเตอร์ ตัวเลข `1e-12` คือ $10^{-12}$ เป็น tolerance สำหรับตัวอย่างหน่วยทศนิยมนี้ ไม่ใช่เกณฑ์สากลของข้อมูลทุกขนาด ฟังก์ชันเพียงตรวจเมทริกซ์และแจ้งข้อผิดพลาด ไม่ได้ซ่อม covariance หรือยืนยันว่ามันประมาณตลาดได้ดี

<span id="implied-excess-returns"></span>

## คำนวณผลตอบแทนส่วนเกินที่รองรับพอร์ตตั้งต้น

เราจะใช้ $\Pi$ อ่านว่า “พายตัวใหญ่” แทนเวกเตอร์ implied expected excess returns สูตรที่ใช้คือ

$$
\Pi=\delta\Sigma w_0.
$$

เครื่องหมาย excess หมายถึงผลตอบแทนคาดหมายหลังลบ $r_f$ แล้ว ถ้า $\Pi_A=0.063$ ผลตอบแทนรวมที่คาดหมายสำหรับ A ภายใต้สมมติฐานนี้คือ $0.02+0.063=0.083$ หรือ 8.3% ต่อปี ส่วน 6.3% เป็นผลตอบแทนส่วนเกินเหนืออัตราปลอดความเสี่ยง

คูณเมทริกซ์ทีละแถวได้

$$
\Sigma w_0=
\begin{bmatrix}
0.04(0.5)+0.012(0.3)+0.008(0.2)\\
0.012(0.5)+0.0225(0.3)+0.0045(0.2)\\
0.008(0.5)+0.0045(0.3)+0.01(0.2)
\end{bmatrix}
=\begin{bmatrix}0.0252\\0.01365\\0.00735\end{bmatrix}.
$$

แต่ละรายการคือ $\operatorname{Cov}(r_i,r_{w_0})$ หรือ covariance ระหว่างผลตอบแทนของสินทรัพย์ $i$ กับผลตอบแทนพอร์ตตั้งต้น แล้วคูณ 2.5 อีกครั้งจึงได้

$$
\Pi=\begin{bmatrix}0.063\\0.034125\\0.018375\end{bmatrix}.
$$

```python
covariance_with_benchmark = covariance @ benchmark_weights
pi = risk_aversion * covariance_with_benchmark
benchmark_variance = float(benchmark_weights @ covariance @ benchmark_weights)
benchmark_excess_mean = float(benchmark_weights @ pi)
calibrated_delta = benchmark_excess_mean / benchmark_variance
implied_table = pd.DataFrame({
    "Benchmark weight": benchmark_weights,
    "Cov(asset, benchmark)": covariance_with_benchmark,
    "Implied excess (%)": pi * 100,
    "Implied raw (%)": (risk_free_rate + pi) * 100,
}, index=assets)
print(implied_table.round(6).to_string())
print("Benchmark variance:", round(benchmark_variance, 8))
print("Benchmark implied excess (%):", round(benchmark_excess_mean * 100, 6))
print("Recovered delta:", round(calibrated_delta, 6))
```

| สินทรัพย์ | น้ำหนัก | Covariance กับพอร์ต | Implied excess | Implied raw |
|---|---:|---:|---:|---:|
| A | 50% | 0.0252 | 6.3000% | 8.3000% |
| B | 30% | 0.01365 | 3.4125% | 5.4125% |
| C | 20% | 0.00735 | 1.8375% | 3.8375% |

`@` คูณเมทริกซ์หรือเวกเตอร์ตามกฎผลรวมแถวคูณคอลัมน์ ส่วน `float(...)` เปลี่ยนผลลัพธ์ scalar ของ NumPy ให้เป็นตัวเลขตัวเดียว `to_string()` ทำให้ pandas แสดงครบทุกคอลัมน์ และการ `round` ใช้เฉพาะตอนพิมพ์ ตัวแปรที่คำนวณต่อยังเก็บค่าก่อนปัด

พอร์ตมี variance $w_0^\top\Sigma w_0=0.018165$ และ implied excess mean $w_0^\top\Pi=0.0454125$ หรือ 4.54125% เมื่อนำสูตร $\Pi=\delta\Sigma w_0$ คูณซ้ายด้วย $w_0^\top$ จะได้

$$
\delta=\frac{w_0^\top\Pi}{w_0^\top\Sigma w_0}
=\frac{0.0454125}{0.018165}=2.5.
$$

ถ้ามีค่าผลตอบแทนส่วนเกินของ benchmark ที่เลือกไว้จากแหล่งอื่น เราอาจใช้ความสัมพันธ์นี้ปรับระดับ $\delta$ ได้ แต่ตัวอย่างข้างบนเป็นการตรวจย้อนกลับจาก $\Pi$ ที่สร้างด้วย 2.5 จึงยังไม่ได้ประมาณ risk aversion จากข้อมูลจริง และการนำผลตอบแทนย้อนหลังช่วงที่ติดลบมาหาร variance จะให้ $\delta$ ติดลบ ซึ่งใช้แทนนักลงทุนที่หลีกเลี่ยงความเสี่ยงในเกณฑ์นี้ไม่ได้

ความสัมพันธ์เดียวกันเขียนเป็น $\Pi_i=\beta_{i,0}\Pi_0$ ได้ โดย $\beta_{i,0}=\operatorname{Cov}(r_i,r_{w_0})/\operatorname{Var}(r_{w_0})$ และ $\Pi_0=w_0^\top\Pi$ หากจะตีความเป็น CAPM ของตลาด ต้องอธิบายเพิ่มว่าเหตุใด benchmark จึงเป็นพอร์ตตลาดและสมมติฐาน CAPM ใช้ได้ การจัดรูปสมการอย่างเดียวให้เพียงความสัมพันธ์ภายใต้ inputs ที่กำหนด

<span id="mean-variance-utility"></span>

## ที่มาของสูตรจากเกณฑ์ผลตอบแทนกับความเสี่ยง

ให้ $x$ เป็นน้ำหนักสินทรัพย์เสี่ยงเทียบกับเงินทุนเริ่มต้น และให้เงินที่เหลือ $1-\mathbf1^\top x$ อยู่ในสินทรัพย์ปลอดความเสี่ยง สัญลักษณ์ $\mathbf1$ เป็นเวกเตอร์ที่มีเลขหนึ่งทุกช่อง ดังนั้น $\mathbf1^\top x$ คือผลรวมน้ำหนักสินทรัพย์เสี่ยง

ถ้า $R$ เป็นเวกเตอร์ผลตอบแทนจริงในงวด ผลตอบแทนพอร์ตรวมเงินสดคือ

$$
R_p=x^\top R+(1-\mathbf1^\top x)r_f
=r_f+x^\top(R-r_f\mathbf1).
$$

ให้ $\mu_e=E[R]-r_f\mathbf1$ เป็น expected excess return ของสินทรัพย์ เราเลือกน้ำหนักเพื่อให้คะแนน mean–variance สูงที่สุด:

$$
U(x)=x^\top\mu_e-\frac{\delta}{2}x^\top\Sigma x.
$$

พจน์แรกเป็นผลตอบแทนส่วนเกินที่คาดหมาย พจน์หลังหักคะแนนตาม variance ยิ่ง $\delta$ สูง ยิ่งหักคะแนนความเสี่ยงมาก อัตรา $r_f$ ที่คงที่เท่ากันทุกพอร์ตถูกตัดออกจากคะแนนได้โดยไม่เปลี่ยนคำตอบ ค่า $U$ เป็นคะแนนสำหรับเปรียบเทียบพอร์ตภายใต้แบบจำลอง ไม่ใช่ผลตอบแทนที่รับประกันหรือเงินกำไรที่ต้องเกิดจริง

ในทฤษฎี expected utility เราเปรียบเทียบ $E[u(W)]$ จากฟังก์ชันความพึงพอใจต่อความมั่งคั่ง $u$ เกณฑ์ mean–variance ข้างบนเป็นรูปแบบที่เราเลือกใช้ในบทนี้ การใช้ mean กับ variance แทนการแจกแจงทั้งหมดต้องมีเหตุผลรองรับจากฟังก์ชัน utility และสมมติฐานของแบบจำลอง จึงไม่ควรอ้างว่าสูตรนี้แทน expected utility ทุกชนิดหรือครอบคลุมความเสี่ยงหางได้ครบ

เมื่อยังไม่บังคับให้ผลรวมน้ำหนักสินทรัพย์เสี่ยงเท่ากับหนึ่ง และอนุญาตการถือ short หรือกู้ยืมตามคำตอบของแบบจำลอง อนุพันธ์ของคะแนนตาม $x$ คือ

$$
\nabla U(x)=\mu_e-\delta\Sigma x.
$$

สำหรับสินทรัพย์แต่ละตัว ส่วนเพิ่มของ expected return ต้องเท่ากับส่วนเพิ่มของค่าปรับความเสี่ยงที่จุดเหมาะสม จึงตั้งอนุพันธ์เป็นศูนย์และได้

$$
\mu_e=\delta\Sigma x^*.
$$

เมื่อเลือก $x^*=w_0$ จะได้ $\Pi=\delta\Sigma w_0$ ถ้า $\delta>0$ และ $\Sigma$ เป็น PD คะแนนเป็นฟังก์ชันเว้าอย่างเคร่งครัด จึงมีจุดสูงสุดเพียงจุดเดียว เราตรวจได้โดยขยับน้ำหนักออกจาก $w_0$ เป็น $w_0+d$:

$$
U(w_0+d)-U(w_0)=-\frac{\delta}{2}d^\top\Sigma d<0
\quad\text{เมื่อ }d\ne0.
$$

```python
def portfolio_utility(weights, means, sigma, delta):
    return float(weights @ means - 0.5 * delta * weights @ sigma @ weights)

recovered_weights = np.linalg.solve(risk_aversion * covariance, pi)
direction = np.array([0.10, -0.05, 0.02])
perturbed_weights = benchmark_weights + direction
utility_at_anchor = portfolio_utility(benchmark_weights, pi, covariance, risk_aversion)
utility_at_perturbation = portfolio_utility(perturbed_weights, pi, covariance, risk_aversion)
utility_loss_formula = 0.5 * risk_aversion * direction @ covariance @ direction
print("Recovered risky weights:", np.round(recovered_weights, 8))
print("Cash at anchor:", round(1 - recovered_weights.sum(), 8))
print("Cash after perturbation:", round(1 - perturbed_weights.sum(), 8))
print("Utility at anchor:", round(utility_at_anchor, 10))
print("Utility after perturbation:", round(utility_at_perturbation, 10))
print("Utility loss, quadratic formula:", round(float(utility_loss_formula), 10))
```

โค้ดแก้กลับมาได้ `[0.5, 0.3, 0.2]` เงินสดที่จุดตั้งต้นเป็นศูนย์ คะแนน 0.02270625 เมื่อลองเพิ่ม A 10 จุดเปอร์เซ็นต์ ลด B 5 จุดเปอร์เซ็นต์ และเพิ่ม C 2 จุดเปอร์เซ็นต์ น้ำหนักเสี่ยงรวมเป็น 1.07 จึงมีเงินสด −0.07 หมายถึงกู้เงินเท่ากับ 7% ของทุนเริ่มต้นภายใต้สมมติฐานยืมได้ที่อัตราเดียวกับ $r_f$

คะแนนหลังขยับลดเหลือ 0.0222521875 ต่างกัน 0.0004540625 ซึ่งตรงกับสูตรกำลังสองข้างบน `np.linalg.solve(A, b)` หาคำตอบ $x$ ของ $Ax=b$ โดยไม่ต้องสร้าง inverse ของ $A$ โดยตรง ฟังก์ชัน `portfolio_utility` ในบทนี้ใช้กับ inputs ที่เราจัดรูปและตรวจไว้แล้ว

ที่มาของเกณฑ์และสูตร unconstrained นี้ตรวจได้ใน [He และ Litterman (December 1999), Appendix B–C หน้า 17–18](https://people.duke.edu/~charvey/Teaching/BA453_2004/GS_The_intuition_behind.pdf) ผลลัพธ์เรื่องน้ำหนักที่ตามมาจะขึ้นกับข้อจำกัดของโจทย์ จึงต้องรักษาข้อสมมติเรื่องเงินสด การ short และการกู้ยืมให้ตรงกับการคำนวณ

<span id="risk-aversion-and-cash"></span>

## เปลี่ยน risk aversion โดยคง expected return เดิม

แยก $\delta$ ที่ใช้สร้างผลตอบแทนตั้งต้นออกจาก $\delta_{\mathrm{investor}}$ ของคนที่นำผลตอบแทนชุดนั้นไปจัดพอร์ต เมื่อคง $\Pi$ และ $\Sigma$ ไว้ น้ำหนักเหมาะสมของนักลงทุนคือ

$$
x^*=\frac{1}{\delta_{\mathrm{investor}}}\Sigma^{-1}\Pi.
$$

ถ้านักลงทุนใช้ 5 แทน 2.5 น้ำหนักสินทรัพย์เสี่ยงทุกตัวจะเหลือครึ่งหนึ่ง เงินที่เหลืออยู่ใน cash ถ้าใช้ 1.25 น้ำหนักเสี่ยงจะเพิ่มเป็นสองเท่า และต้องกู้เงินภายใต้โจทย์ที่ไม่มีข้อจำกัดการกู้ยืมนี้

```python
delta_rows = []
for investor_delta in [1.25, 2.5, 5.0]:
    risky_weights = np.linalg.solve(investor_delta * covariance, pi)
    delta_rows.append({
        "Investor delta": investor_delta,
        "A": risky_weights[0], "B": risky_weights[1], "C": risky_weights[2],
        "Cash": 1 - risky_weights.sum(),
        "Expected excess (%)": 100 * risky_weights @ pi,
        "SD (%)": 100 * np.sqrt(risky_weights @ covariance @ risky_weights),
    })
delta_table = pd.DataFrame(delta_rows).set_index("Investor delta")
print(delta_table.round(6).to_string())
```

| Investor $\delta$ | A | B | C | Cash | Expected excess | SD |
|---:|---:|---:|---:|---:|---:|---:|
| 1.25 | 100% | 60% | 40% | −100% | 9.0825% | 26.9555% |
| 2.50 | 50% | 30% | 20% | 0% | 4.54125% | 13.4778% |
| 5.00 | 25% | 15% | 10% | 50% | 2.270625% | 6.7389% |

Cash −100% หมายถึงกู้เพิ่มเท่ากับทุนเริ่มต้น เพื่อให้มูลค่าถือสินทรัพย์เสี่ยงรวม 200% ตัวอย่างไม่ได้ตรวจวงเงินกู้ margin อัตรากู้จริง หรือต้นทุนซื้อขาย ถ้านักลงทุนห้ามกู้ ห้าม short หรือกำหนดน้ำหนักสูงสุดรายสินทรัพย์ ต้องนำข้อจำกัดเหล่านั้นเข้า optimization

เมื่อแบ่งน้ำหนักเสี่ยงด้วยผลรวมของมัน ทุกแถวจะมีสัดส่วน A/B/C เท่ากับ 50/30/20 เหมือนกัน แต่ขั้นตอนนี้ลบความต่างด้านเงินสดและ leverage ออกไป การรายงานเฉพาะสัดส่วนภายในพอร์ตเสี่ยงจึงบอกการถือครองเทียบกับทุนทั้งหมดไม่ครบ

สำหรับพอร์ตสัมผัสเส้นจากสินทรัพย์ปลอดความเสี่ยงใน [บท Efficient Frontier](efficient-frontier.html) การคูณเวกเตอร์ excess means ด้วยค่าบวกยังคงทิศทางของ $\Sigma^{-1}\mu_e$ ไว้ น้ำหนักพอร์ตเสี่ยงที่ normalize แล้วจึงไม่บอกระดับของ means ได้เอง จำเป็นต้องเลือกสเกล เช่น $\delta$ และผลตอบแทนส่วนเกินของ benchmark เพิ่มเติม

<span id="budget-constraint"></span>

## ถ้าบังคับลงทุนในสินทรัพย์เสี่ยงรวม 100% สูตรย้อนกลับมีค่าคงที่เพิ่ม

เปลี่ยนโจทย์เป็นลงทุนในสินทรัพย์ A/B/C ให้รวมหนึ่งเสมอ และไม่มี cash ให้เลือกเพิ่มหรือลด ขณะนี้ข้อจำกัดคือ $\mathbf1^\top w=1$ กำหนด Lagrangian เป็น

$$
\mathcal L(w,\eta)
=w^\top\mu_e-\frac{\delta}{2}w^\top\Sigma w
-\eta(\mathbf1^\top w-1).
$$

$\eta$ เป็นตัวคูณที่ช่วยบังคับข้อจำกัดงบประมาณ อนุพันธ์ให้

$$
\mu_e=\delta\Sigma w+\eta\mathbf1.
$$

ดังนั้นทั้ง $\Pi$ และ $\Pi+c\mathbf1$ รองรับน้ำหนักเหมาะสมชุดเดิมภายใต้ข้อจำกัดนี้ได้ การเพิ่ม expected return เท่ากันทุกสินทรัพย์ทำให้ทุกพอร์ตที่มีน้ำหนักรวมหนึ่งได้คะแนนเพิ่มเท่ากับ $c$ ลำดับความชอบจึงไม่เปลี่ยน

การใช้ $\Pi=\delta\Sigma w_0$ ในโจทย์นี้เลือกสมาชิกหนึ่งจากครอบครัวคำตอบ โดยตั้ง $\eta=0$ ถ้าอาศัยน้ำหนักอย่างเดียว เราจะยังไม่รู้ค่าคงที่ที่เพิ่มให้ทุกสินทรัพย์ และถ้ายังไม่กำหนด $\delta$ ก็ยังไม่รู้สเกลของผลตอบแทนด้วย

ฟังก์ชันถัดไปแก้โจทย์ที่มีเฉพาะข้อจำกัดผลรวมน้ำหนัก ยังอนุญาตน้ำหนักติดลบ คำนวณ $\eta$ จากเงื่อนไขผลรวมก่อน แล้วแทนกลับไปหาน้ำหนัก:

$$
\eta=\frac{\mathbf1^\top\Sigma^{-1}\mu_e-\delta}
{\mathbf1^\top\Sigma^{-1}\mathbf1},\qquad
w^*=\frac1\delta\Sigma^{-1}(\mu_e-\eta\mathbf1).
$$

```python
def budget_constrained_weights(means, sigma, delta):
    sigma = validate_covariance(sigma, require_pd=True)
    means = np.asarray(means, dtype=float)
    if means.shape != (len(sigma),) or not np.all(np.isfinite(means)):
        raise ValueError("Mean vector must be finite and match covariance")
    if not np.isfinite(delta) or delta <= 0:
        raise ValueError("Risk aversion must be finite and positive")
    ones = np.ones(len(means))
    inverse_mean = np.linalg.solve(sigma, means)
    inverse_one = np.linalg.solve(sigma, ones)
    budget_multiplier = (ones @ inverse_mean - delta) / (ones @ inverse_one)
    weights = (inverse_mean - budget_multiplier * inverse_one) / delta
    return weights, float(budget_multiplier)

shifted_means = pi + 0.01
budget_base, eta_base = budget_constrained_weights(pi, covariance, risk_aversion)
budget_shifted, eta_shifted = budget_constrained_weights(shifted_means, covariance, risk_aversion)
unconstrained_shifted = np.linalg.solve(risk_aversion * covariance, shifted_means)
normalized_shifted = unconstrained_shifted / unconstrained_shifted.sum()
print("Budget solution with pi:", np.round(budget_base, 8))
print("Budget solution with pi + 1 pp:", np.round(budget_shifted, 8))
print("Budget multipliers:", np.round([eta_base, eta_shifted], 8))
print("Unconstrained shifted solution:", np.round(unconstrained_shifted, 6))
print("Shifted solution divided by its sum:", np.round(normalized_shifted, 6))
```

เมื่อใช้ $\Pi$ ได้ $\eta=0$ และน้ำหนัก `[0.5, 0.3, 0.2]` เมื่อเพิ่ม mean ให้ทุกสินทรัพย์อีกหนึ่งจุดเปอร์เซ็นต์ ได้ $\eta=0.01$ และน้ำหนักเดิม

แต่ถ้าแก้แบบไม่มีข้อจำกัดก่อน จะได้น้ำหนักประมาณ `[0.496599, 0.408844, 0.553741]` แล้วนำผลลัพธ์หารด้วยผลรวมน้ำหนัก จะกลายเป็น `[0.340326, 0.280186, 0.379487]` ซึ่งต่างจากคำตอบของโจทย์งบประมาณ การ normalize คำตอบ unconstrained จึงใช้แทนการแก้โจทย์ mean–variance ที่กำหนด $\delta$ และบังคับผลรวมน้ำหนักไม่ได้ทั่วไป

ถ้าเพิ่มเงื่อนไขห้าม short หรือเพดานน้ำหนัก และคำตอบชนขอบเขต อนุพันธ์ยังมีตัวคูณของข้อจำกัดเหล่านั้นเพิ่มอีก การใช้ reverse formula แบบไม่มีข้อจำกัดมาอ้างว่าเป็นผลตอบแทนชุดเดียวที่รองรับพอร์ตจริงจึงเกินกว่าสิ่งที่สูตรบอก

<span id="model-sensitivity"></span>

## เปลี่ยน covariance แล้วผลตอบแทนโดยนัยก็เปลี่ยน

ลองคง SD 20%, 15%, 10% ไว้ แต่ตั้ง correlation ทุกคู่เป็นศูนย์ covariance นอกแนวทแยงจะเป็นศูนย์ทั้งหมด นี่เป็นอีกสมมติฐานหนึ่ง ไม่ใช่การแก้ข้อมูลเดิมให้ถูกต้องกว่าเดิม

```python
covariance_diagonal = np.diag(np.diag(covariance))
pi_diagonal = risk_aversion * covariance_diagonal @ benchmark_weights
sensitivity_table = pd.DataFrame({
    "Pi with original covariance (%)": pi * 100,
    "Pi with zero correlations (%)": pi_diagonal * 100,
    "Pi with delta = 5 (%)": (5.0 * covariance @ benchmark_weights) * 100,
}, index=assets)
print(sensitivity_table.round(6).to_string())
print("Weights recovered under diagonal model:",
      np.round(np.linalg.solve(risk_aversion * covariance_diagonal, pi_diagonal), 8))
```

| สินทรัพย์ | Covariance เดิม, $\delta=2.5$ | Correlation ศูนย์, $\delta=2.5$ | Covariance เดิม, $\delta=5$ |
|---|---:|---:|---:|
| A | 6.3000% | 5.0000% | 12.6000% |
| B | 3.4125% | 1.6875% | 6.8250% |
| C | 1.8375% | 0.5000% | 3.6750% |

ทุกคอลัมน์ถอดกลับจากน้ำหนัก 50/30/20 แต่ระดับและสัดส่วนผลตอบแทนต่างกัน คอลัมน์ที่เปลี่ยน $\delta$ คูณผลตอบแทนทุกตัวเป็นสองเท่า ส่วนคอลัมน์ที่เปลี่ยน covariance ปรับแต่ละสินทรัพย์ไม่เท่ากันตาม covariance กับพอร์ต

หากนำ $\Pi$ จาก covariance แบบหนึ่งไปแก้จัดพอร์ตด้วย covariance อีกแบบหนึ่ง ก็ไม่ควรคาดว่าจะได้น้ำหนักตั้งต้นกลับมา การรายงานผลจึงควรเก็บวันที่ข้อมูล ช่วงเวลา วิธีประมาณ covariance น้ำหนัก benchmark และ $\delta$ ไว้คู่กับ $\Pi$ เสมอ

<span id="constructing-views"></span>

## เขียนมุมมองแบบ absolute และ relative ด้วย P กับ Q

[Active views](glossary.html#active-views) เป็นความเห็นเกี่ยวกับ expected return ของสินทรัพย์หรือผลต่างระหว่างพอร์ต เราจะใช้มุมมองสมมติสองข้อในช่วงเวลาหนึ่งปีเดียวกับ $\Pi$:

1. C มี expected excess return 2.5% เป็น absolute view เพราะระบุระดับของ C โดยตรง
2. A มี expected return สูงกว่า B อยู่ 2 จุดเปอร์เซ็นต์ เป็น relative view เพราะระบุผลต่าง A ลบ B

ให้ $K=2$ เป็นจำนวน views แล้วเขียน

$$
P=\begin{bmatrix}0&0&1\\1&-1&0\end{bmatrix},\qquad
Q=\begin{bmatrix}0.025\\0.020\end{bmatrix}.
$$

$P$ เป็น pick matrix ขนาด $K\times N$ แต่ละแถวเลือกสินทรัพย์หรือผสมผลตอบแทนที่มุมมองพูดถึง $Q$ เป็นเวกเตอร์ค่าผลตอบแทนเป้าหมายของมุมมอง มี $K$ รายการ สัญลักษณ์ $Q$ ในบทนี้เป็น view returns ไม่มีความหมายเป็นความน่าจะเป็นแบบ risk-neutral

แถว `[0, 0, 1]` เลือก C แถว `[1, -1, 0]` คำนวณ A ลบ B เครื่องหมาย −1 เป็นสัมประสิทธิ์ในผลต่าง ไม่ได้สั่งให้พอร์ตสุดท้าย short B 100% น้ำหนักที่ลงทุนจริงยังต้องคำนวณหลังรวมมุมมองกับข้อมูลตั้งต้นและข้อจำกัดของผู้ลงทุน

หากมุมมองเป็น “A สูงกว่าพอร์ตที่ถือ B 60% และ C 40%” แถวนั้นเขียน `[1, -0.6, -0.4]` โดย $Q$ ของแถวจะเป็น expected return ของ A ลบ expected return ของพอร์ตดังกล่าว แถวของ $P$ จึงไม่จำเป็นต้องรวมหนึ่ง

### ตรวจว่ามุมมองต่างจาก prior ไปทางใด

การประเมินก่อนรับมุมมองหรือ [prior](glossary.html#prior) มีค่าเฉลี่ยตั้งต้น $\Pi$ จึงคาดค่าของแต่ละพอร์ตในมุมมองไว้ที่ $P\Pi$ เราอ่านความต่างจาก $Q-P\Pi$:

$$
P\Pi=\begin{bmatrix}0.018375\\0.063-0.034125\end{bmatrix}
=\begin{bmatrix}0.018375\\0.028875\end{bmatrix},
\qquad
Q-P\Pi=\begin{bmatrix}0.006625\\-0.008875\end{bmatrix}.
$$

มุมมอง C สูงกว่า prior 0.6625 จุดเปอร์เซ็นต์ ส่วนมุมมอง A ลบ B ต่ำกว่า prior 0.8875 จุดเปอร์เซ็นต์ แม้ยังคาดว่า A จะสูงกว่า B อยู่ 2 จุดเปอร์เซ็นต์ก็ตาม การระบุว่ามุมมองเป็นบวกต่อสินทรัพย์เพียงจากเครื่องหมายของ $Q$ จึงทำให้ตีความผิดได้

### แปลง raw กับ excess ให้ตรงกัน

เขียนเวกเตอร์ raw means เป็น $\mu_{\mathrm{raw}}=\mu_e+r_f\mathbf1$ แล้วค่ามุมมองในหน่วย raw คือ

$$
Q_{\mathrm{raw}}=Q_e+r_fP\mathbf1.
$$

สำหรับ absolute C ผลรวมแถวเป็นหนึ่ง จึงต้องบวก $r_f$ อีก 2%: excess view 2.5% เท่ากับ raw view 4.5% สำหรับ A ลบ B ผลรวมแถวเป็นศูนย์ $r_f$ จึงหักล้างกัน ผลต่างยังเป็น 2 จุดเปอร์เซ็นต์ทั้งสอง convention

```python
P = np.array([[0.0, 0.0, 1.0], [1.0, -1.0, 0.0]])
Q = np.array([0.025, 0.020])
view_names = pd.Index(["C absolute", "A minus B"], name="View")
prior_view_mean = P @ pi
view_surprise = Q - prior_view_mean
Q_raw = Q + risk_free_rate * P.sum(axis=1)
basket_p = np.array([1.0, -0.6, -0.4])
view_table = pd.DataFrame({
    "Prior excess (%)": prior_view_mean * 100,
    "View excess (%)": Q * 100,
    "View raw (%)": Q_raw * 100,
    "Difference (pp)": view_surprise * 100,
}, index=view_names)
print(view_table.round(6).to_string())
print("P shape:", P.shape, "Q shape:", Q.shape)
print("A minus a 60/40 B/C basket, prior (%):", round(float(basket_p @ pi) * 100, 6))
```

ตารางให้ C prior excess 1.8375%, view excess 2.5%, view raw 4.5% ส่วน A ลบ B ให้ 2.8875%, 2%, 2% ตามลำดับ พอร์ต A ลบตะกร้า B/C มี prior 3.5175%

`P.sum(axis=1)` รวมสัมประสิทธิ์ทีละแถว ค่า `.shape` ของ $P$ เป็น `(2, 3)` และของ $Q$ เป็น `(2,)` ซึ่งเป็นเวกเตอร์หนึ่งมิติของ NumPy ไม่ใช่เมทริกซ์สองคอลัมน์ เราใช้ `P @ pi` แล้วได้หนึ่งค่าต่อหนึ่ง view โดยยังรักษาลำดับสินทรัพย์ A/B/C เหมือนใน covariance

Coursera ตอน [Introducing Active Views](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/oCQ00/introducing-active-views) ใช้การเขียน views ต่อสินทรัพย์หรือส่วนผสมของสินทรัพย์เป็นขั้นต่อจาก reverse optimization บทนี้จะเก็บมิติเหล่านี้ไว้ชัดเจน: $P$ ขนาด $K\times N$, $Q$ ยาว $K$ และ covariance ของข้อผิดพลาดในมุมมองขนาด $K\times K$

<span id="view-uncertainty"></span>

## Omega วัดความไม่แน่นอนของ expected return ในมุมมอง

การเขียน view ว่า C มี expected excess return 2.5% ยังไม่บอกว่าเราเชื่อตัวเลขนี้แน่นเพียงใด แบบจำลองจะเพิ่มข้อผิดพลาดของมุมมอง:

$$
Q=P\mu_e+\varepsilon_v,\qquad
E[\varepsilon_v]=0,\qquad
\operatorname{Cov}(\varepsilon_v)=\Omega.
$$

ในการตีความแบบ Bayesian $\mu_e$ เป็นค่าเฉลี่ยผลตอบแทนที่ยังไม่รู้ และ $Q$ เป็นการประเมินมันผ่าน $P$ แบบจำลองในบท Black–Litterman ถัดไปใช้ข้อผิดพลาดร่วมแบบ Normal และสมมติให้ view errors เป็นอิสระจากความไม่แน่นอนของ prior mean $\Omega$ เป็น [view uncertainty](glossary.html#view-uncertainty) ขนาด $K\times K$ แนวทแยงเป็น variance ของข้อผิดพลาดแต่ละ view ส่วนนอกแนวทแยงเป็น covariance ระหว่างข้อผิดพลาด

ความผันผวนของผลตอบแทนจริงกับความไม่แน่นอนของค่าเฉลี่ยเป็นคนละปริมาณ $\Sigma_{CC}=0.01$ หมายถึง variance ของผลตอบแทน C หนึ่งปี ส่วน $\Omega_{11}$ หมายถึงความคลาดเคลื่อนของมุมมองเรื่อง expected excess return ของ C ตัวเลขทั้งสองมีหน่วยกำลังสองเหมือนกัน แต่ไม่ได้แทนสิ่งเดียวกัน

หากกำหนด SD ของข้อผิดพลาดในมุมมองเป็น 1 จุดเปอร์เซ็นต์ ต้องใส่ variance $0.01^2=0.0001$ ใน $\Omega$ ไม่ใช่ 0.01 ถ้าใส่ 0.01 จะกลายเป็น SD 10 จุดเปอร์เซ็นต์

### กำหนดความไม่แน่นอนเพื่อเตรียมบทถัดไป

ให้ความไม่แน่นอนของ prior mean เป็น $\tau\Sigma$ โดยเลือก $\tau=0.05$ แล้วเลือก variance ของข้อผิดพลาดแต่ละ view เท่ากับ variance ของ prior mean เมื่อฉายไปยัง view เดียวกัน:

$$
\Omega=\operatorname{diag}\!\left(\operatorname{diag}(P\tau\Sigma P^\top)\right).
$$

สูตรนี้เลือกเฉพาะค่าบนแนวทแยง และตั้ง covariance ของข้อผิดพลาดระหว่าง views เป็นศูนย์ เป็น convention สำหรับตัวอย่างร่วมกับบทถัดไป ไม่ใช่ค่าความเชื่อมั่นที่ประมาณจากความแม่นยำย้อนหลัง ในแบบจำลอง Normal การกำหนด covariance ศูนย์ระหว่างข้อผิดพลาดทำให้ถือว่าข้อผิดพลาดเหล่านั้นเป็นอิสระต่อกันด้วย หากไม่มีสมมติฐาน Normal covariance ศูนย์เพียงอย่างเดียวยังไม่พอจะสรุป independence

```python
tau = 0.05
prior_mean_covariance = tau * covariance
prior_view_covariance = P @ prior_mean_covariance @ P.T
omega = np.diag(np.diag(prior_view_covariance))
print("Prior covariance of view means:")
print(np.round(prior_view_covariance, 8))
print("Chosen independent view-error covariance Omega:")
print(np.round(omega, 8))
print("View-error SDs (pp):", np.round(np.sqrt(np.diag(omega)) * 100, 6))
print("Change Omega variance to one quarter, SDs (pp):",
      np.round(np.sqrt(np.diag(omega / 4)) * 100, 6))
```

ได้เมทริกซ์สองชุดที่ต่างกัน:

$$
P\tau\Sigma P^\top=
\begin{bmatrix}0.0005&0.000175\\0.000175&0.001925\end{bmatrix},
\qquad
\Omega=\begin{bmatrix}0.0005&0\\0&0.001925\end{bmatrix}.
$$

มุมมองเรื่อง C กับ A ลบ B มี prior covariance เท่ากับ $0.05(0.008-0.0045)=0.000175$ แต่เราเลือก view-error covariance ระหว่างสองข้อให้เป็นศูนย์ สองเมทริกซ์นี้วัดคนละชั้นของความไม่แน่นอน จึงไม่จำเป็นต้องมีค่า off-diagonal เหมือนกัน การสร้าง $\Omega$ แบบ diagonal เป็นการเพิ่มสมมติฐานเรื่องข้อผิดพลาดของข้อมูลมุมมอง

SD ของ view errors เท่ากับ 2.236068 และ 4.387482 จุดเปอร์เซ็นต์ หากลด variance ของทั้งสอง view เหลือหนึ่งในสี่ SD จะเหลือครึ่งหนึ่งเป็น 1.118034 และ 2.193741 จุดเปอร์เซ็นต์ `np.diag` ชั้นในดึงแนวทแยงเป็นเวกเตอร์ ชั้นนอกสร้างเมทริกซ์ใหม่ที่มีค่านั้นบนแนวทแยงและใส่ศูนย์นอกแนวทแยง

$\tau=0.05$ ไม่ได้แปลว่า prior ถูก 5% หรือเรามั่นใจ 95% และ $\Omega$ ก็ไม่ใช่โอกาสที่มุมมองจะเกิดขึ้นจริง มันระบุสเกลความไม่แน่นอนในแบบจำลอง เมื่อจะนำความเชื่อมั่นที่ผู้วิเคราะห์ตอบเป็นเปอร์เซ็นต์มาใช้ ต้องมีกฎแปลงเพิ่มเติมและอธิบายกฎนั้น ส่วนตัวอย่างนี้กำหนด variance โดยตรง

ความเชื่อมั่นในมุมมองต้องอ่านเทียบกับความไม่แน่นอนของ prior ด้วย หากเปลี่ยนทั้ง $\tau$ และ $\Omega$ ผลของการผสมข้อมูลอาจต่างจากการเปลี่ยน $\Omega$ เพียงตัวเดียว เราจะคำนวณน้ำหนักข้อมูลทั้งสองฝั่งในบทถัดไป

<span id="correlated-views"></span>

## ถ้า views ใช้ข้อมูลร่วมกัน ข้อผิดพลาดอาจสัมพันธ์กัน

ผู้วิเคราะห์สองมุมมองอาจใช้รายงานเศรษฐกิจ ชุดกำไรบริษัท หรือโมเดลเดียวกัน การถือว่าข้อผิดพลาดเป็นอิสระจึงต้องมีเหตุผลรองรับ หากข้อผิดพลาดสัมพันธ์กัน ให้ใส่ covariance นอกแนวทแยง:

$$
\Omega_{ij}=\rho_{ij}s_i s_j,
$$

โดย $s_i$ เป็น SD ของข้อผิดพลาด view $i$ และ $\rho_{ij}$ เป็น correlation ระหว่างข้อผิดพลาด สูตรนี้ใช้ correlation ของข้อผิดพลาดในการประเมิน mean ไม่ใช่ดึง correlation ของผลตอบแทนสินทรัพย์มาใส่โดยอัตโนมัติ

ลองคง SD ทั้งสองค่าไว้ แต่สมมติว่า view-error correlation เป็น 0.5 เราตั้งค่าไว้เพื่อศึกษาความสัมพันธ์ ไม่ได้ประมาณจากข้อมูลของผู้วิเคราะห์จริง

```python
view_error_sd = np.sqrt(np.diag(omega))
view_error_correlation = np.array([[1.0, 0.5], [0.5, 1.0]])
omega_correlated = np.outer(view_error_sd, view_error_sd) * view_error_correlation
validate_covariance(omega_correlated, require_pd=True)
print("Correlated view-error covariance:")
print(np.round(omega_correlated, 8))
print("Eigenvalues:", np.round(np.linalg.eigvalsh(omega_correlated), 8))
print("Recovered error correlation:", round(
    omega_correlated[0, 1] / (view_error_sd[0] * view_error_sd[1]), 6))
```

ได้ $\Omega_{12}\approx0.00049054$ และ eigenvalues ประมาณ 0.00034747 กับ 0.00207753 ซึ่งเป็นบวกทั้งคู่ `np.outer(view_error_sd, view_error_sd)` สร้างตารางผลคูณ $s_i s_j$ แล้ว `*` คูณกับ correlation ทีละช่อง รูปแบบนี้ต่างจาก `@` ที่คูณเมทริกซ์ตามผลรวมแถวคูณคอลัมน์

การเลือก correlation ทุกคู่ให้อยู่ในช่วง −1 ถึง 1 ยังไม่พอรับประกันว่าเมทริกซ์ที่ใหญ่กว่าสองมิติจะเป็น PSD ต้องตรวจทั้งเมทริกซ์ด้วย หาก $\Omega$ ไม่เป็น PSD จะมีส่วนผสมของข้อผิดพลาดที่แบบจำลองให้ variance ติดลบ จึงใช้เป็น covariance ไม่ได้

<span id="validating-views"></span>

## ตรวจมิติและเมทริกซ์ก่อนรวมมุมมอง

สำหรับ $N$ สินทรัพย์และ $K$ views รูปร่างข้อมูลต้องเป็นดังนี้

| ตัวแปร | รูปร่าง | สิ่งที่แต่ละรายการหมายถึง |
|---|---|---|
| $\Pi$ | $N$ | Expected excess return รายสินทรัพย์ |
| $\Sigma$ | $N\times N$ | Covariance ของผลตอบแทนสินทรัพย์ |
| $P$ | $K\times N$ | สัมประสิทธิ์ของสินทรัพย์ในแต่ละ view |
| $Q$ | $K$ | Expected return ของแต่ละ view ตาม convention ที่เลือก |
| $\Omega$ | $K\times K$ | Covariance ของข้อผิดพลาดใน views |

จำนวน views มากกว่าจำนวนสินทรัพย์ได้ เช่น มีผู้ประเมินหลายคนต่อสินทรัพย์ชุดเดิม แต่ข้อมูลมุมมองที่ซ้ำหรือสัมพันธ์กันต้องถูกสะท้อนในโครงสร้างข้อผิดพลาด จำนวนแถวที่มากขึ้นเพียงอย่างเดียวไม่ได้ยืนยันว่ามีข้อมูลใหม่เพิ่มตามนั้น

ฟังก์ชันต่อไปตรวจ $P,Q,\Omega$ ก่อนนำไปใช้ เมทริกซ์ $\Omega$ ที่เป็น PSD แต่ singular ยังเป็น covariance ได้ ฟังก์ชันจึงไม่ปฏิเสธมันเพียงเพราะไม่มี inverse การแก้ posterior ในขั้นต่อไปต้องตรวจเมทริกซ์ของระบบที่จะ solve อีกครั้งตามสูตรที่ใช้

```python
def validate_views(pick_matrix, view_means, view_covariance, n_assets):
    pick_matrix = np.asarray(pick_matrix, dtype=float)
    view_means = np.asarray(view_means, dtype=float)
    if (pick_matrix.ndim != 2 or pick_matrix.shape[1] != n_assets
            or pick_matrix.shape[0] == 0 or not np.all(np.isfinite(pick_matrix))):
        raise ValueError("P must be finite with shape (number of views, number of assets)")
    k = pick_matrix.shape[0]
    if view_means.shape != (k,) or not np.all(np.isfinite(view_means)):
        raise ValueError("Q must be a finite vector with one entry per view")
    view_covariance = validate_covariance(view_covariance)
    if view_covariance.shape != (k, k):
        raise ValueError("Omega shape must match the number of views")
    return pick_matrix, view_means, view_covariance

P, Q, omega = validate_views(P, Q, omega, len(assets))
invalid_view_cases = {
    "Wrong P width": (P[:, :2], Q, omega),
    "Wrong Q length": (P, Q[:1], omega),
    "Negative variance": (P, Q, np.diag([-0.0005, 0.001925])),
    "Correlation larger than one": (P, Q, np.array([[0.0005, 0.01], [0.01, 0.001925]])),
}
for label, inputs in invalid_view_cases.items():
    try:
        validate_views(*inputs, n_assets=len(assets))
    except ValueError as error:
        print(label + ": rejected - " + str(error))
```

โค้ดปฏิเสธตัวอย่างผิดทั้งสี่ชุด: $P$ มีคอลัมน์ขาดหนึ่งสินทรัพย์, $Q$ มีค่าขาดหนึ่ง view, variance ติดลบ และ covariance นอกแนวทแยงใหญ่จนเมทริกซ์ไม่เป็น PSD ข้อความ `ValueError` บอกเงื่อนไขที่ผิด แทนการปล่อยให้ตัวเลขที่ได้จากขั้นหลังดูเหมือนคำตอบที่เชื่อถือได้

คำสั่ง `try` ลองเรียกฟังก์ชัน ถ้าเกิด `ValueError` จะไปทำส่วน `except` เพื่อพิมพ์ข้อผิดพลาด แล้วทดสอบกรณีถัดไปได้ เครื่องหมาย `*inputs` แยก tuple เป็นสาม arguments ส่วน `n_assets` เป็นจำนวนสินทรัพย์ที่ต้องตรงกับ covariance

การตรวจนี้ยังไม่รู้ว่าคอลัมน์ชื่อ A ถูกนำไปใส่แทน C หรือไม่ เพราะ NumPy เก็บตำแหน่งเป็นหลัก ก่อนสร้าง array จากข้อมูลจริงควรจัดลำดับด้วยชื่อสินทรัพย์ให้ตรงกัน ตรวจวันอ้างอิง และตรวจว่าข้อมูลในมุมมองมีให้ใช้แล้ว ณ วันตัดสินใจ การผ่าน shape check ไม่ได้ตรวจ look-ahead bias หรือความน่าเชื่อถือของแหล่งข้อมูล

<span id="redundant-views"></span>

## มุมมองซ้ำและการขยายสเกลหนึ่งแถว

สมมติคัดลอก view A ลบ B เดิมสองครั้ง ทั้งคู่มี $P$ แถวเดียวกันและ $Q=0.02$ เท่ากัน ถ้าเป็นข้อมูลชิ้นเดียวที่ถูกคัดลอก ข้อผิดพลาดก็เป็นตัวเดียวกัน จึงมี correlation 1 และ

$$
P_{\mathrm{duplicate}}=
\begin{bmatrix}1&-1&0\\1&-1&0\end{bmatrix},\qquad
\Omega_{\mathrm{duplicate}}=
\begin{bmatrix}s^2&s^2\\s^2&s^2\end{bmatrix}.
$$

เมทริกซ์นี้เป็น PSD แต่ rank หนึ่ง การใช้ diagonal $\Omega$ ให้ข้อมูลที่คัดลอกเหมือนเป็นการประเมินที่มีข้อผิดพลาดอิสระสองครั้ง จะเพิ่มความเชื่อมั่นโดยไม่มีหลักฐานใหม่ ถ้าผู้ประเมินสองคนทำงานอิสระจริง แม้ $P$ เหมือนกันก็อาจมีข้อมูลใหม่ได้ จึงต้องพิจารณาที่มาของ views แทนการลบทุกแถวที่เหมือนกันโดยอัตโนมัติ

อีกกรณีคือเปลี่ยนสเกลการเขียน view จาก A ลบ B เท่ากับ 2% เป็น 10A ลบ 10B เท่ากับ 20% ทั้งคู่แสดงความสัมพันธ์เดียวกัน แต่ต้องขยาย variance ของข้อผิดพลาดแถวนั้นเป็น 100 เท่าด้วย โดยถ้า $S$ เป็นเมทริกซ์แนวทแยงของตัวคูณแต่ละแถว:

$$
P'=SP,\qquad Q'=SQ,\qquad\Omega'=S\Omega S^\top.
$$

```python
P_duplicate = np.vstack([P[1], P[1]])
Q_duplicate = np.repeat(Q[1], 2)
omega_duplicate = np.full((2, 2), omega[1, 1])
validate_views(P_duplicate, Q_duplicate, omega_duplicate, len(assets))
row_scale = np.diag([1.0, 10.0])
P_scaled = row_scale @ P
Q_scaled = row_scale @ Q
omega_scaled = row_scale @ omega @ row_scale.T
original_standardized_gap = (Q - P @ pi) / np.sqrt(np.diag(omega))
scaled_standardized_gap = (Q_scaled - P_scaled @ pi) / np.sqrt(np.diag(omega_scaled))
print("Repeated P rank:", np.linalg.matrix_rank(P_duplicate))
print("Repeated-error covariance eigenvalues:", np.linalg.eigvalsh(omega_duplicate))
print("Original standardized gaps:", np.round(original_standardized_gap, 6))
print("Scaled-row standardized gaps:", np.round(scaled_standardized_gap, 6))
```

กรณีคัดลอกมี rank ของ $P$ เท่ากับ 1 และ eigenvalues ของ $\Omega$ เป็น `[0, 0.00385]` ส่วนการขยายแถวที่สองสิบเท่า ให้ standardized gaps ก่อนและหลังเท่ากันประมาณ `[0.296279, -0.202280]`

Standardized gap ในโค้ดนำ $Q-P\Pi$ หารด้วย SD ของ view error ทีละแถว จึงช่วยตรวจว่าเมื่อขยายทั้ง mean และ SD ตามสเกลเดียวกัน อัตราส่วนยังคงเดิม ค่านี้ยังไม่ใช่ความน่าจะเป็นที่สินทรัพย์จะชนะอีกตัว และไม่ได้เป็นการทดสอบนัยสำคัญที่รวมความไม่แน่นอนของ prior ครบแล้ว

ถ้าตั้ง $\Omega=0$ จะระบุว่าไม่มีข้อผิดพลาดของ views และต้องใช้เป็น hard views หรือพิจารณาลิมิตอย่างระมัดระวัง views ที่ขัดกัน เช่น A ลบ B ต้องเท่ากับทั้ง 2% และ 4% แบบแน่นอนพร้อมกัน ไม่สามารถเป็นจริงร่วมกันได้ การนำเมทริกซ์ singular ไปหา inverse หรือเปลี่ยนเป็น pseudoinverse โดยไม่ตรวจความหมายของข้อจำกัดจะซ่อนปัญหานี้

<span id="units-and-horizon"></span>

## เปลี่ยนหน่วยทศนิยมเป็นเปอร์เซ็นต์ต้องเปลี่ยน covariance ด้วย

เมื่อเก็บ 6.3% เป็น 0.063 ทุกค่าผลตอบแทนอยู่ในหน่วยทศนิยม แต่ถ้าเปลี่ยนไปเก็บเป็น 6.3 ซึ่งเป็นจำนวนจุดเปอร์เซ็นต์ จะต้องเปลี่ยน

$$
\Pi'=100\Pi,\quad Q'=100Q,\quad
\Sigma'=100^2\Sigma,\quad\Omega'=100^2\Omega.
$$

$P$ เป็นสัมประสิทธิ์เลือกสินทรัพย์จึงไม่เปลี่ยน $\tau$ เป็นสเกลแบบไม่มีหน่วยจึงไม่เปลี่ยนในการแปลงหน่วยนี้ ส่วน risk aversion ที่ใช้กับคะแนน mean–variance ต้องเป็น $\delta'=\delta/100$ เพื่อให้สูตรย้อนกลับยังมีน้ำหนักเดิม:

$$
\delta'\Sigma'w_0
=\frac{\delta}{100}(100^2\Sigma)w_0
=100\Pi.
$$

ค่า $\delta=2.5$ ต้องอ่านร่วมกับหน่วยที่เราใช้ ก่อนเปรียบเทียบ risk aversion ข้ามโปรแกรมต้องตรวจว่าโปรแกรมเหล่านั้นเก็บผลตอบแทนด้วยหน่วยเดียวกัน

```python
unit_scale = 100.0
covariance_percent = covariance * unit_scale**2
pi_percent = pi * unit_scale
Q_percent = Q * unit_scale
omega_percent = omega * unit_scale**2
risk_aversion_percent = risk_aversion / unit_scale
recomputed_pi_percent = risk_aversion_percent * covariance_percent @ benchmark_weights
recovered_percent_weights = np.linalg.solve(
    risk_aversion_percent * covariance_percent, pi_percent
)
print("Pi in percentage points:", pi_percent)
print("Pi recomputed with consistent units:", np.round(recomputed_pi_percent, 6))
print("Omega in squared percentage points:")
print(omega_percent)
print("Recovered weights:", np.round(recovered_percent_weights, 8))
print("View gap in percentage points:", np.round(Q_percent - P @ pi_percent, 6))
```

ได้ $\Pi'=[6.3,3.4125,1.8375]$ และ $\Omega'$ มีแนวทแยง 5 กับ 19.25 หน่วยจุดเปอร์เซ็นต์ยกกำลังสอง เมื่อใช้ $\delta'=0.025$ แล้วแก้ย้อนกลับ น้ำหนักยังเป็น `[0.5, 0.3, 0.2]` การเปลี่ยนหน่วยตัวเลขอย่างสอดคล้องไม่ควรเปลี่ยนคำตอบการลงทุน

### ช่วงเวลาเป็นอีกเงื่อนไขที่ต้องตรงกัน

ตัวอย่างทั้งหมดใช้ expected return และ covariance ของงวดหนึ่งปีเดียวกัน หากจะเปลี่ยนเป็นรายเดือน ต้องระบุแบบจำลองของการรวมงวดก่อน การนำ $Q$ รายปีมารวมกับ $\Pi$ รายเดือนจะเปรียบเทียบคนละปริมาณ แม้ Python จะคูณเมทริกซ์ได้ตามปกติ

Variance ของผลตอบแทนที่เกิดจริงหลายงวดและ variance ของค่าเฉลี่ยที่ยังไม่รู้ยังแปลงต่างกันได้ ตัวอย่างเช่น ถ้ากำหนดค่าเฉลี่ยของผลตอบแทนรายเดือนที่คงที่เป็น $m$ และใช้ผลตอบแทนแบบบวกสะสมทั้ง 12 เดือน ค่าเฉลี่ยรายปีจะเป็น $12m$ ความไม่แน่นอนของค่าเฉลี่ยรายปีจึงเป็น $144\operatorname{Var}(m)$ เพราะคูณตัวแปรเดียวด้วย 12 ขณะที่ variance ของผลตอบแทนรายเดือนที่บวกกันอาจเป็น $12\sigma^2$ ภายใต้เงื่อนไขว่ารายเดือนไม่มี autocovariance

สมการหลังไม่ได้ใช้แทนการทบต้น simple returns โดยตรง และไม่ได้ให้กฎว่า $\Omega$ ต้องคูณ 12 ทุกครั้งที่ annualize ต้องเริ่มจากนิยามว่าความไม่แน่นอนของมุมมองกำลังวัดอะไรและตัวแปรแต่ละงวดสัมพันธ์กันอย่างไร

<span id="exercises"></span>

## แบบฝึกหัด

ลองคำนวณด้วยตัวเองก่อนเปิดเฉลย ทุกข้อใช้ตัวอย่าง A/B/C ในบท เว้นแต่โจทย์กำหนดค่าใหม่

### 1. คำนวณ implied return ของ B ด้วยมือ

ใช้แถว B ของ $\Sigma$, น้ำหนัก 50/30/20 และ $\delta=2.5$ หา implied excess return ของ B แล้วแปลงเป็น raw mean เมื่อ $r_f=2\%$

<details>
<summary>ดูเฉลย</summary>

Covariance กับ benchmark เท่ากับ $0.012(0.5)+0.0225(0.3)+0.0045(0.2)=0.01365$ คูณ 2.5 ได้ 0.034125 หรือ excess 3.4125% บวก $r_f$ อีก 2% ได้ raw mean 5.4125% ตัวเลขนี้รองรับพอร์ตภายใต้ inputs ของตัวอย่าง ไม่ได้เกิดจากการเฉลี่ยผลตอบแทนย้อนหลังของ B

</details>

### 2. นักลงทุนระวังความเสี่ยงมากขึ้นถือเงินสดเท่าไร

คง $\Pi$ และ $\Sigma$ เดิม แต่เพิ่ม investor $\delta$ จาก 2.5 เป็น 10 ใช้โจทย์ unconstrained ที่มี cash residual หาน้ำหนัก A/B/C และ cash

<details>
<summary>ดูเฉลย</summary>

น้ำหนักสินทรัพย์เสี่ยงเหลือหนึ่งในสี่ของเดิม คือ `[0.125, 0.075, 0.05]` รวม 0.25 จึงถือ cash 0.75 หรือ 75% Expected excess เหลือหนึ่งในสี่คือ 1.1353125% และ SD เหลือหนึ่งในสี่ประมาณ 3.36944% เพราะสเกลน้ำหนักทุกตัวเท่ากัน โดย cash ในตัวอย่างมีผลตอบแทนแน่นอนในงวดนี้

</details>

### 3. Fully invested แยก mean ที่เพิ่มเท่ากันทุกสินทรัพย์ออกได้หรือไม่

สมมติรู้ว่า benchmark 50/30/20 เป็นคำตอบของ mean–variance ที่บังคับน้ำหนักรวมหนึ่ง และใช้ $\delta=2.5$ การรู้เพียงเท่านี้เลือกได้หรือไม่ว่าควรใช้ $\Pi$ หรือ $\Pi+0.02\mathbf1$?

<details>
<summary>ดูเฉลย</summary>

เลือกไม่ได้จากข้อมูลเท่านี้ ทั้งสองชุดให้น้ำหนักเหมาะสมเดิม เพราะพอร์ตที่มีผลรวมน้ำหนักหนึ่งทุกชุดได้ expected return เพิ่ม 2 จุดเปอร์เซ็นต์เท่ากัน ตัวคูณงบประมาณ $\eta$ เปลี่ยนจาก 0 เป็น 0.02 หากเปิดให้เลือก cash การเพิ่ม mean ของ risky assets โดยคง $r_f$ เดิมจะเปลี่ยนการจัดสรรได้ จึงต้องระบุว่าโจทย์มี cash ให้เลือกหรือไม่

</details>

### 4. เขียน view ของ A เทียบกับพอร์ต B/C

คาดว่า A มี expected return มากกว่าพอร์ต B 60% และ C 40% อยู่ 3 จุดเปอร์เซ็นต์ เขียน $P$ แถวเดียวและ $Q$ แล้วบอกว่ามุมมองนี้สูงหรือต่ำกว่า prior

<details>
<summary>ดูเฉลย</summary>

ใช้ $P=[1,-0.6,-0.4]$ และ $Q=0.03$ Prior ของผลต่างเท่ากับ $0.063-0.6(0.034125)-0.4(0.018375)=0.035175$ ดังนั้น view ต่ำกว่า prior 0.005175 หรือ 0.5175 จุดเปอร์เซ็นต์ แม้ยังคาดว่า A ชนะตะกร้าก็ตาม ผลรวมแถวเป็นศูนย์จึงได้ผลต่างเดียวกันทั้ง raw และ excess convention

</details>

### 5. แปลง SD ของ view error เป็น Omega

มีสอง views ที่สมมติว่า errors เป็นอิสระแบบ Normal โดย SD ของ error เท่ากับ 1 และ 2 จุดเปอร์เซ็นต์ จงเขียน $\Omega$ หากต่อมาสมมติให้ error correlation เป็น −0.25 ค่า off-diagonal ควรเป็นเท่าไร?

<details>
<summary>ดูเฉลย</summary>

กรณีอิสระใช้ $\Omega=\operatorname{diag}(0.01^2,0.02^2)=\operatorname{diag}(0.0001,0.0004)$ เมื่อ correlation เป็น −0.25 ค่า off-diagonal ทั้งสองช่องเป็น $-0.25(0.01)(0.02)=-0.00005$ ต้องตรวจ PSD ทั้งเมทริกซ์ด้วย ในกรณีสองมิตินี้ determinant เท่ากับ $0.0001(0.0004)-(-0.00005)^2=0.0000000375>0$ และ variance เป็นบวก จึงเป็น PD

</details>

### 6. ตรวจ view ที่เขียน 7% แบบ raw

ผู้วิเคราะห์บอกว่า C มี expected raw return 7% ต่อปี โดยใช้ risk-free rate 2% ค่า $Q$ ที่ใส่ในตัวอย่างนี้ควรเป็นเท่าไร? ถ้าผู้อ่านอีกคนเปลี่ยน view เดิมจาก C เป็น 10C จะต้องเปลี่ยน $Q$ และ variance ของ error อย่างไร?

<details>
<summary>ดูเฉลย</summary>

ต้องแปลงเป็น excess ก่อน จึงได้ $Q=0.07-0.02=0.05$ เมื่อแถว $P$ เปลี่ยนจาก `[0, 0, 1]` เป็น `[0, 0, 10]` ต้องคูณ $Q$ สิบเท่าเป็น 0.5 และคูณ variance ของ error หนึ่งร้อยเท่า หากมี view อื่นร่วมด้วย covariance ระหว่าง error ของแถวที่เปลี่ยนกับแถวที่ไม่เปลี่ยนจะคูณสิบเท่า ตามสูตร $S\Omega S^\top$

</details>

นำ $\Pi$, $P$, $Q$, $\tau$ และ $\Omega$ ของตัวอย่างไปต่อใน [บท Black–Litterman](black-litterman.html) เพื่อคำนวณ posterior mean แล้วดูว่าการเลือก covariance และข้อจำกัดในขั้นจัดพอร์ตเปลี่ยนน้ำหนักอย่างไร

<span id="sources"></span>

## แหล่งอ้างอิงและขอบเขตที่อ่าน

ตรวจแหล่งข้อมูลวันที่ 3 ตุลาคม 2569 อ่าน transcript เต็มของ Coursera สองตอนผ่านบัญชีที่เข้าถึงคอร์สได้ และอ่านข้อความ supplemental ที่คอร์สแนะนำ บทภาษาไทยนี้เรียบเรียงใหม่ ใช้ตัวเลขสมมติและโค้ดเขียนขึ้นสำหรับบท ไม่เผยแพร่ transcript หรือคัดลอกตัวอย่างข้อมูลประเทศจากบทความต้นทาง

- Coursera, EDHEC, *Advanced Portfolio Construction and Analysis with Python*: [Extracting Implied Expected Returns](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/nyHIO/extracting-implied-expected-returns) และ [Introducing Active Views](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/oCQ00/introducing-active-views) ใช้ตรวจลำดับแนวคิด benchmark, reverse optimization และการระบุ views
- Coursera supplemental: [The Intuition Behind Black-Litterman Model Portfolios](https://www.coursera.org/learn/advanced-portfolio-construction-python/supplement/cVBb3/the-intuition-behind-black-litterman-model-portfolios) แนะนำเอกสาร He–Litterman ผ่าน SSRN โดยระบุปี 2002 ส่วนฉบับ primary PDF ที่อ่านสำหรับบทนี้เป็นฉบับ December 1999 ตามรายการถัดไป
- Guangliang He และ Robert Litterman, [*The Intuition Behind Black-Litterman Model Portfolios*, Goldman Sachs Investment Management, December 1999](https://people.duke.edu/~charvey/Teaching/BA453_2004/GS_The_intuition_behind.pdf): อ่านส่วนเนื้อหาและข้อจำกัดที่เกี่ยวข้อง หน้า 2, 4, 7–14 และ Appendix B–C หน้า 17–18 ตามเลขหน้าที่พิมพ์ในเอกสาร ใช้ตรวจ convention ของ excess returns และสูตร mean–variance, implied returns, views กับ covariance ของข้อผิดพลาด
- Fischer Black และ Robert Litterman, [*Global Portfolio Optimization*, Financial Analysts Journal 48(5), 1992](https://rpc.cfainstitute.org/research/financial-analysts-journal/1992/faj-v48-n5-28): อ่านบทคัดย่อบนเว็บไซต์ผู้เผยแพร่เพื่อตรวจแนวคิด equilibrium anchor และ absolute/relative views ไม่ได้อ้างว่าเข้าถึงเนื้อหาเต็มผ่านเว็บไซต์นั้น
