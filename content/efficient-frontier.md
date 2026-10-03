---
title: หลายสินทรัพย์และ Efficient Frontier
description: เรียน matrix จากน้ำหนักพอร์ต แยกพอร์ตที่สร้างได้จากพอร์ตที่มีประสิทธิภาพ และใช้ SciPy หาน้ำหนักภายใต้ข้อจำกัดพร้อมตรวจคำตอบ
---

# หลายสินทรัพย์และ Efficient Frontier

<p class="lead">เมื่อมีสินทรัพย์สามตัว เราจะค้นหาสัดส่วนที่ให้ผลตอบแทนคาดหมาย 10% ด้วยความผันผวนต่ำที่สุดได้อย่างไร?</p>

ใน[บทพอร์ตสองสินทรัพย์](portfolio-basics.html) เราลองน้ำหนัก A แล้วให้น้ำหนัก B เท่ากับส่วนที่เหลือได้ทันที เมื่อเพิ่มสินทรัพย์ตัวที่สาม น้ำหนักที่เหลือยังแบ่งได้หลายแบบ และความเสี่ยงต้องนับ covariance ของทุกคู่ เราจึงเขียนข้อมูลเป็นเวกเตอร์และ matrix ก่อนให้ตัวแก้ปัญหา optimization ค้นหาน้ำหนัก

บทนี้ใช้ข้อมูลสมมติต่อปีชุดเดียวตลอดหน้า ไม่มีการดาวน์โหลดตลาดหรือประมาณค่าจากราคาจริง เรากำหนด expected arithmetic return, SD และ correlation ไว้เพื่อฝึกกลไก Mean–variance optimization การใช้ค่าประมาณเหล่านี้ตัดสินใจลงทุนจริงเป็นอีกโจทย์หนึ่งซึ่งอยู่ใน[บทความไม่แน่นอนของค่าประมาณ](portfolio-estimation.html)

เนื้อหาเรียบเรียงประกอบหัวข้อ Efficient Frontier และ Lab 108–109 โค้ดเริ่มจาก Notebook ใหม่ได้โดยมี NumPy, pandas และ SciPy แล้วรันทุกช่องตามลำดับ ผลตอบแทนใช้ทศนิยม เช่น 6% คือ 0.06; variance และ covariance ใช้หน่วยผลตอบแทนยกกำลังสองของช่วงหนึ่งปี

[ดาวน์โหลด Notebook ของบทนี้](notebooks/efficient-frontier.ipynb) เพื่อรันตัวอย่างตามลำดับและเทียบผลลัพธ์ที่บันทึกไว้

<span id="matrix-inputs"></span>

## เขียนข้อมูลสามสินทรัพย์ให้เรียงลำดับเดียวกัน

ให้ A, B และ C มีพารามิเตอร์ดังนี้ เราใช้ชื่ออักษรแทนสินทรัพย์เพื่อไม่ทำให้ค่าที่สมมติขึ้นดูเหมือนเป็น forecast ของตลาดใด

| สินทรัพย์ | Expected return ต่อปี | SD ต่อปี |
|---|---:|---:|
| A | 6% | 10% |
| B | 10% | 15% |
| C | 14% | 20% |

Correlation ของ A/B เท่ากับ 0.2, A/C เท่ากับ 0.1 และ B/C เท่ากับ 0.3 ทุกคู่มีความสัมพันธ์ทางบวก แต่ไม่ได้เคลื่อนไหวเหมือนกันทั้งหมด Covariance คำนวณจาก $\rho_{ij}\sigma_i\sigma_j$ เช่น A/B เท่ากับ $0.2(0.10)(0.15)=0.003$ เมื่อเรียงทั้งตารางจะได้

$$
\mu=\begin{bmatrix}0.06\\0.10\\0.14\end{bmatrix},
\qquad
\Sigma=\begin{bmatrix}
0.0100&0.0030&0.0020\\
0.0030&0.0225&0.0090\\
0.0020&0.0090&0.0400
\end{bmatrix}.
$$

ตัว $\mu$ อ่านว่า “มิว” เก็บ expected return ทุกตัวเป็น **เวกเตอร์** หรือลำดับตัวเลขหนึ่งชุด ส่วน $\Sigma$ อ่านว่า “ซิกมาใหญ่” เป็น **matrix** หรือตารางตัวเลขหลายแถวหลายคอลัมน์ แนวทแยงเป็น variance ของ A, B, C และช่องนอกแนวทแยงเป็น covariance

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize

asset_names = ["A", "B", "C"]
annual_mu = np.array([0.06, 0.10, 0.14])
annual_cov = np.array([
    [0.0100, 0.0030, 0.0020],
    [0.0030, 0.0225, 0.0090],
    [0.0020, 0.0090, 0.0400]
])
print(pd.DataFrame(annual_cov, index=asset_names, columns=asset_names))
```

วงเล็บเหลี่ยมชั้นนอกเก็บตาราง ส่วนแต่ละวงเล็บชั้นในเป็นหนึ่งแถว `np.array` เปลี่ยนรายการตัวเลขให้คำนวณแบบ NumPy ได้ และ `pd.DataFrame` ใส่ชื่อแถวกับคอลัมน์เพื่อให้อ่านตรวจง่าย

NumPy จับคู่ด้วยตำแหน่งของตัวเลข เมื่อ `annual_mu` เรียง A/B/C แถวและคอลัมน์ของ covariance รวมทั้งน้ำหนักก็ต้องเรียง A/B/C หากมาจาก pandas ควรจัด `.loc[asset_names]` และ `.loc[asset_names, asset_names]` ก่อนแปลงเป็น array การสลับชื่อสินทรัพย์ผิดลำดับอาจให้ตัวเลขที่คำนวณสำเร็จแต่เป็นของพอร์ตคนละชุด

<span id="matrix-portfolio-math"></span>

## เครื่องหมาย @ ย่อการคูณถ่วงน้ำหนักที่เรารู้จัก

สมมติลงทุน A 50%, B 30%, C 20% เขียนน้ำหนักเป็น $w=(0.5,0.3,0.2)$ Expected return ของพอร์ตยังเป็นสูตรเดิม:

$$
\mu_p=0.5(0.06)+0.3(0.10)+0.2(0.14)=0.088.
$$

ในสัญลักษณ์ matrix เขียนเป็น $w^\mathsf{T}\mu$ ตัว $\mathsf{T}$ หมายถึง transpose หรือสลับเวกเตอร์คอลัมน์เป็นแถวเพื่อคูณกัน ใน NumPy เมื่อทั้งสองเป็น array หนึ่งมิติ ใช้ `w @ annual_mu` ได้ตรง ๆ `@` คือ matrix multiplication ส่วน `*` ยังเป็นการคูณสมาชิกตามตำแหน่ง [NumPy: matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html)

```python
example_weights = np.array([0.50, 0.30, 0.20])
expected_by_parts = (example_weights * annual_mu).sum()
expected_by_matrix = example_weights @ annual_mu
print(f"Weighted sum: {expected_by_parts:.2%}")
print(f"Matrix calculation: {expected_by_matrix:.2%}")
```

ทั้งสองวิธีได้ 8.80% ต่อปี `example_weights * annual_mu` คืนส่วนร่วมของแต่ละตัวเป็น `[0.03, 0.03, 0.028]` แล้วจึงบวก ส่วน `@` รวมขั้นตอนคูณและบวกเป็นคำสั่งเดียว

สำหรับ variance ต้องรวมทุกคู่:

$$
\begin{aligned}
\sigma_p^2={}&w_A^2\sigma_A^2+w_B^2\sigma_B^2+w_C^2\sigma_C^2\\
&+2w_Aw_B\Sigma_{AB}+2w_Aw_C\Sigma_{AC}+2w_Bw_C\Sigma_{BC}.
\end{aligned}
$$

สูตรย่อคือ $\sigma_p^2=w^\mathsf{T}\Sigma w$ ส่วน SD เท่ากับรากที่สองของ variance ลองมองการคูณจากขวาไปซ้าย: `annual_cov @ example_weights` จะรวม covariance ของแต่ละสินทรัพย์กับส่วนผสมที่ถือ จากนั้นคูณน้ำหนักด้านซ้ายและรวมอีกครั้ง จึงครบทั้งพจน์แนวทแยงและคู่ไขว้

```python
covariance_with_mix = annual_cov @ example_weights
example_variance = example_weights @ covariance_with_mix
example_sd = np.sqrt(example_variance)
print(covariance_with_mix.round(6))
print(f"Variance: {example_variance:.6f}")
print(f"SD: {example_sd:.4%}")
```

ได้ variance 0.008505 และ SD ประมาณ 9.2223% ต่อปี ตัวอย่างนี้มี expected return 8.8% แต่ SD 9.2223% เป็นคนละตัววัด ห้ามรายงาน variance 0.008505 เป็น SD 0.8505%

เมื่อมี $N$ สินทรัพย์ น้ำหนักมี $N$ ค่า covariance มี $N\times N$ ช่อง ตัวเลขแนวทแยงมี $N$ ค่า และคู่สินทรัพย์ที่ไม่ซ้ำมี $N(N-1)/2$ คู่ เช่น 30 สินทรัพย์มี 435 คู่ แม้สูตร matrix จะสั้น แต่ข้อมูลเข้าที่ต้องประมาณมีจำนวนมากขึ้น

### Covariance ที่ใช้ต้องทำให้ variance ไม่ติดลบ

Variance ของพอร์ตทุกน้ำหนักต้องไม่ติดลบ คุณสมบัตินี้เรียกว่า **positive semidefinite** หาก matrix ทำให้บางน้ำหนักมี variance ติดลบ แปลว่าตารางนั้นไม่ใช่ covariance ที่สอดคล้องกัน ไม่ควรแก้ด้วยการตัด variance ติดลบเป็นศูนย์เงียบ ๆ

ตัวอย่างนี้ตรวจทั้งความสมมาตรและ eigenvalues ซึ่งเป็นตัวเลขที่ช่วยตรวจคุณสมบัติดังกล่าว `np.linalg.eigvalsh` ใช้กับ matrix สมมาตร ผลทุกตัวที่เป็นบวกยืนยันว่าตารางนี้เป็น positive definite ซึ่งเข้มกว่า positive semidefinite

```python
print(np.allclose(annual_cov, annual_cov.T))
cov_eigenvalues = np.linalg.eigvalsh(annual_cov)
print(cov_eigenvalues.round(6))
print((cov_eigenvalues > 0).all())
```

ได้ `True`, eigenvalues ประมาณ `[0.009317, 0.019113, 0.044070]` และ `True` `.T` สลับแถวกับคอลัมน์ ส่วน `.all()` ตรวจว่าทุกสมาชิกผ่านเงื่อนไขหรือไม่ ถ้าใช้ค่าประมาณจริง ยังต้องตรวจข้อมูลซ้ำ ข้อมูลหาย และการเรียงสินทรัพย์ก่อนอาศัยการทดสอบเชิงตัวเลขนี้

<span id="feasible-portfolios"></span>

## พอร์ตที่สร้างได้ยังไม่ใช่พอร์ตที่มีประสิทธิภาพทุกจุด

กำหนดกติกาว่าไม่มี short ใช้เงินครบทั้งหมด และยังไม่มีเงินสดแยก:

$$
w_A+w_B+w_C=1,
\qquad 0\leq w_i\leq1.
$$

น้ำหนัก `[1, 0, 0]`, `[0.5, 0.3, 0.2]` และ `[1/3, 1/3, 1/3]` ผ่านกติกา จึงเป็น **feasible portfolios** ส่วน `[0.8, 0.5, -0.3]` รวมเป็นหนึ่งแต่ไม่ผ่านเงื่อนไขไม่มี short

หากวาดพอร์ตที่ผ่านกติกาทั้งหมดเป็นจุดในระนาบ SD กับ expected return จะเกิด **feasible set** หรือพื้นที่ของพอร์ตที่สร้างได้ จุดบางจุดมีอีกพอร์ตหนึ่งที่ให้ expected return สูงกว่าโดยมี SD เท่ากันหรือต่ำกว่า เราเรียกว่าถูกพอร์ตนั้นครอบงำ ในกรอบ mean–variance จึงไม่มีเหตุผลให้เลือกจุดที่ถูกครอบงำเมื่อข้อจำกัดอื่นเหมือนกัน

**Efficient frontier** เป็นส่วนของขอบที่เพิ่ม expected return ต่อไปไม่ได้โดยไม่เพิ่ม variance การมีหลายชื่อในพอร์ตหรือการอยู่บนขอบด้านใดด้านหนึ่งของภาพไม่ได้ทำให้ efficient โดยอัตโนมัติ และ efficient ในบทนี้ประเมินจาก mean กับ variance ซึ่งยังไม่ครอบคลุม[ความเสี่ยงปลายหาง](extreme-risk.html)

เก็บสูตรที่ใช้บ่อยเป็นฟังก์ชันก่อน `def` สร้างฟังก์ชันและ `return` ส่งตัวเลขกลับ ฟังก์ชัน variance จงใจยังไม่ถอดราก เพราะการหาจุดต่ำสุดของ variance ให้ตำแหน่งเดียวกับการหาจุดต่ำสุดของ SD

```python
def model_return(w):
    return float(w @ annual_mu)

def model_variance(w):
    return float(w @ annual_cov @ w)

def model_sd(w):
    return np.sqrt(model_variance(w))

print(f"Example portfolio: {model_return(example_weights):.2%}, {model_sd(example_weights):.4%}")
```

`float(...)` เปลี่ยน scalar ของ NumPy ให้เป็นตัวเลข Python ทั่วไป ไม่ได้เปลี่ยนสูตรหรือปัดทศนิยม

<span id="optimization-problem"></span>

## เปลี่ยนคำถามเป็นโจทย์ที่มีเป้าหมายและข้อจำกัด

สมมติว่าต้องการ expected return $r_\star=10\%$ ต่อปี โจทย์คือ

$$
\begin{aligned}
\underset{w}{\operatorname{minimize}}\quad &w^\mathsf{T}\Sigma w\\
\text{subject to}\quad &\sum_iw_i=1,\\
&w^\mathsf{T}\mu=r_\star,\\
&0\leq w_i\leq1.
\end{aligned}
$$

อ่านทีละบรรทัด: เลือกน้ำหนักให้ variance ต่ำที่สุด ใช้เงินครบ ต้องได้ expected return ตามเป้า และไม่ขาย short ค่า $r_\star$ เป็นเป้าหมายของแบบจำลอง ไม่ใช่ผลตอบแทนที่รับประกันว่าจะเกิดขึ้น

โจทย์นี้เป็น **quadratic programming** เพราะฟังก์ชันที่ต้องการลดเป็นกำลังสองของน้ำหนัก ขณะที่ข้อจำกัดเป็นเชิงเส้น เมื่อ covariance เป็น positive semidefinite พื้นที่ feasible เป็นแบบ convex และ objective เป็น convex ปัญหานี้จึงมีโครงสร้างที่ช่วยค้นหาจุดต่ำสุดทั่วทั้งพื้นที่ได้ [CVX Group: Portfolio optimization](https://www.cvxgrp.org/cvx_short_course/docs/applications/notebooks/portfolio_optimization.html)

ใน Python เราจะใช้ `minimize` ของ SciPy กับวิธี **SLSQP** ซึ่งรองรับ constraints และ bounds SLSQP เป็นตัวแก้ปัญหาเชิงตัวเลขทั่วไป การที่โจทย์ของเราเป็น quadratic programming ไม่ได้หมายความว่ากำลังเรียกแพ็กเกจชื่อ `quadprog` และสถานะสำเร็จของตัวแก้ยังควรตรวจเทียบกับเงื่อนไขและคำตอบจากอีกวิธี [SciPy: SLSQP](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)

### เขียน residual ที่ควรเป็นศูนย์

สำหรับข้อจำกัดแบบเท่ากัน ให้เขียนค่าผลต่างที่ต้องเป็นศูนย์ เช่น น้ำหนักรวมหนึ่งเขียนเป็น `w.sum() - 1` ส่วนผลตอบแทนตามเป้าคือ `model_return(w) - target` ค่า `type: "eq"` บอก SciPy ว่าเป็นข้อจำกัด equality

เราจะใช้ฟังก์ชันเดียวกันหาทั้งพอร์ตตามเป้าและพอร์ต variance ต่ำสุดโดยไม่ตั้งเป้า หาก `target=None` แปลว่ายังไม่มีข้อจำกัดผลตอบแทน `None` เป็นค่าพิเศษของ Python ที่ใช้แทน “ไม่ได้ระบุ”

```python
def budget_residual(w):
    return w.sum() - 1

def solve_variance(target=None):
    constraints = [{"type": "eq", "fun": budget_residual}]
    if target is not None:
        if not annual_mu.min() <= target <= annual_mu.max():
            raise ValueError("Target is outside the long-only return range")
        def target_residual(w):
            return model_return(w) - target
        constraints.append({"type": "eq", "fun": target_residual})
    result = minimize(
        model_variance, np.full(3, 1 / 3),
        jac=lambda w: 2 * annual_cov @ w,
        method="SLSQP", bounds=[(0, 1)] * 3,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000}
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result
```

`np.full(3, 1/3)` สร้างน้ำหนักตั้งต้นเท่ากันสามตัว ส่วน `bounds=[(0, 1)] * 3` ตั้งขอบ 0 ถึง 1 ให้ทั้งสามน้ำหนัก `lambda w: ...` เป็นฟังก์ชันสั้นที่รับ `w` แล้วคืนค่าถัดจากเครื่องหมาย colon ในที่นี้ `jac` ส่ง gradient ของ variance คือ $2\Sigma w$ ช่วยให้ตัวแก้ทราบทิศทางที่ฟังก์ชันเปลี่ยน

`ftol` กำหนดความละเอียดเกณฑ์หยุดและ `maxiter` จำกัดจำนวนรอบ ค่าละเอียดช่วยตรวจตัวอย่างนี้แต่ไม่ทำให้พารามิเตอร์ตลาดแม่นขึ้น หากการแก้ไม่สำเร็จ เราให้หยุดพร้อมข้อความ แทนการนำ `result.x` ไปใช้อย่างไม่ตรวจสถานะ

### รันเป้า 10% แล้วตรวจน้ำหนักจริง

ผลลัพธ์ `.x` คือน้ำหนักที่ตัวแก้พบ `.success` เป็นสถานะ และ `.message` เป็นคำอธิบายจากตัวแก้ เราตรวจทั้งงบประมาณ ผลตอบแทน และขอบน้ำหนักด้วย `assert` หากเงื่อนไขใดไม่ผ่าน Notebook จะหยุดเพื่อให้ตรวจ

```python
target_result = solve_variance(target=0.10)
target_weights = target_result.x
assert np.isclose(target_weights.sum(), 1, atol=1e-8)
assert np.isclose(model_return(target_weights), 0.10, atol=1e-8)
assert (target_weights >= -1e-8).all() and (target_weights <= 1 + 1e-8).all()
print(pd.Series(target_weights, index=asset_names).round(6))
print(f"Expected return: {model_return(target_weights):.4%}")
print(f"SD: {model_sd(target_weights):.4%}")
```

ได้ A 34.375%, B 31.25%, C 34.375%, expected return 10% และ SD ประมาณ 10.5623% ต่อปี ค่าผ่อนปรน $10^{-8}$ ใช้รองรับความคลาดเคลื่อนตัวเลข เช่นศูนย์ที่คอมพิวเตอร์เก็บเป็นลบเล็กมาก ไม่ใช่การอนุญาตให้มี short ที่มีนัยสำคัญ

หากถือ A และ C อย่างละครึ่งจะได้ expected return 10% เช่นกัน แต่ SD ประมาณ 11.6190% ภายใต้ covariance ชุดเดียวกัน การเพิ่ม B แล้วลด A/C ตามผลข้างต้นจึงลด variance โดยยังได้ expected return ตามเป้า

<span id="optimizer-validation"></span>

## ใช้อีกวิธีตรวจคำตอบก่อนวาดเส้น

สำหรับตัวอย่างสามสินทรัพย์นี้ expected return 10% บังคับให้ $w_A=w_C$ และ $w_B=1-2w_A$ เราจึงลองน้ำหนัก A ตั้งแต่ 0 ถึง 0.5 แล้วคำนวณ variance ของทุกจุดได้โดยไม่เรียก optimizer อีกครั้ง

```python
candidate_a = np.linspace(0, 0.5, 10001)
manual_weights = np.column_stack([candidate_a, 1 - 2 * candidate_a, candidate_a])
manual_variances = np.sum((manual_weights @ annual_cov) * manual_weights, axis=1)
manual_best = manual_weights[np.argmin(manual_variances)]
print(pd.Series(manual_best, index=asset_names).round(6))
print(f"Fine-grid SD: {model_sd(manual_best):.6%}")
assert np.allclose(manual_best, target_weights, atol=0.00006)
```

`np.column_stack` วางน้ำหนัก A/B/C เป็นสามคอลัมน์ แต่ละแถวเป็นพอร์ตหนึ่งแบบ `np.argmin` คืนตำแหน่งที่ variance ต่ำสุด จึงเลือกแถวนั้นกลับมาได้ การค้นหาแบบ grid นี้ละเอียดทุก 0.005 จุดเปอร์เซ็นต์ของน้ำหนักและได้คำตอบตรงกับ optimizer ภายในหนึ่งช่วง grid

Grid ยังมีขอบเขตความละเอียดและจำนวนสินทรัพย์ที่ทำได้สะดวก จึงเหมาะกับการตรวจตัวอย่างเล็ก ในปัญหาจริงต้องตรวจ feasibility, สถานะตัวแก้ และความไวต่อข้อมูลเข้า ไม่ควรใช้คำว่า “คอมพิวเตอร์คำนวณแล้ว” แทนการตรวจเหล่านี้

<span id="gmv-efficient-branch"></span>

## แยกพอร์ต variance ต่ำสุดออกจากทั้งเส้นขอบ

เรียก `solve_variance()` โดยไม่ระบุ target จะได้ **Global Minimum Variance portfolio หรือ GMV** ซึ่งมี variance ต่ำที่สุดในพอร์ตที่ผ่านข้อจำกัดทั้งหมด คำว่า global ในที่นี้หมายถึงทั่วทั้งพื้นที่ long-only ที่เรากำหนด ไม่ได้หมายถึงสินทรัพย์ทุกชนิดบนโลก

```python
gmv_result = solve_variance()
gmv_weights = gmv_result.x
gmv_return = model_return(gmv_weights)
gmv_sd = model_sd(gmv_weights)
print(pd.Series(gmv_weights, index=asset_names).round(6))
print(f"GMV mean: {gmv_return:.4%}; SD: {gmv_sd:.4%}")
```

ได้ A ประมาณ 68.3285%, B 20.5279%, C 11.1437%, expected return 7.7126% และ SD 8.7587% ต่อปี พอร์ต GMV นี้ยังเสี่ยง เพราะ covariance ให้ variance เป็นบวก ไม่ใช่สินทรัพย์ปลอดความเสี่ยง

เราสามารถสั่งหาพอร์ต variance ต่ำสุดสำหรับทุกเป้าหมายตั้งแต่ 6% ถึง 14% ได้ แต่เป้าหมายที่ต่ำกว่า expected return ของ GMV จะได้พอร์ตที่เสี่ยงมากกว่า GMV พร้อมกับมี mean ต่ำกว่า ดังนั้น เส้นของพอร์ต variance ต่ำสุดตามทุก target ไม่ใช่ efficient frontier ทั้งเส้น ต้องเลือกเฉพาะส่วนตั้งแต่ GMV ขึ้นไปในตัวอย่างนี้

```python
frontier_rows = []
for target in [0.06, 0.075, 0.08, 0.10, 0.12, 0.14]:
    w = solve_variance(target).x
    frontier_rows.append({
        "Target": target, "SD": model_sd(w),
        "Efficient branch": target >= gmv_return - 1e-8
    })
frontier_table = pd.DataFrame(frontier_rows)
print(frontier_table.round(6))
```

| เป้าหมาย expected return ต่อปี | SD ต่ำสุดที่เป้านั้น | อยู่บน efficient branch? |
|---:|---:|---|
| 6.0% | 10.0000% | ไม่อยู่ |
| 7.5% | 8.7759% | ไม่อยู่ |
| 8.0% | 8.7901% | อยู่ |
| 10.0% | 10.5623% | อยู่ |
| 12.0% | 14.1117% | อยู่ |
| 14.0% | 20.0000% | อยู่ |

คำว่า efficient ไม่ได้รับรองว่าผลตอบแทนจริงจะสูง หรือพอร์ตเหมาะกับผู้ลงทุนทุกคน มันบอกการเปรียบเทียบ mean กับ variance ภายใต้ข้อมูลเข้าและข้อจำกัดชุดนี้ หากเปลี่ยน forecast, correlation หรือกติกาการลงทุน เส้น frontier ก็เปลี่ยนได้

<figure class="course-figure">
<picture>
<source media="(max-width: 600px)" srcset="assets/charts/course-frontier-mobile.svg">
<img src="assets/charts/course-frontier.svg" alt="ขอบพอร์ตที่มีประสิทธิภาพของ A B C และจุด GMV" width="720" height="560" loading="lazy">
</picture>
<figcaption>จุดสีเทาเป็นตัวอย่างน้ำหนักบนกริดครั้งละ 5 percentage points จึงแสดงเพียงบางพอร์ตในชุดที่ทำได้ เส้นสีม่วงคำนวณจากการลด variance ณ ผลตอบแทนเป้าหมายตั้งแต่ GMV ขึ้นไป ส่วนเส้นประด้านล่างมีพอร์ตที่ให้ผลตอบแทนคาดหมายสูงกว่าที่ SD เท่ากัน ใช้พารามิเตอร์ A, B, C สมมติชุดเดียวกับโค้ดในบท</figcaption>
</figure>

<span id="portfolio-constraints"></span>

## ข้อจำกัดเปลี่ยนคำตอบและเป้าหมายที่ทำได้

ในแบบ long-only ผลตอบแทนคาดหมายของพอร์ตเป็นค่าเฉลี่ยถ่วงน้ำหนัก จึงต้องอยู่ระหว่าง 6% กับ 14% การตั้งเป้า 16% ภายใต้กติกานี้ไม่มีคำตอบ ต่อให้เพิ่มจำนวนรอบของ optimizer ก็ไม่ทำให้ข้อจำกัดที่ขัดกันกลายเป็นจริง

หากจำกัดน้ำหนักสินทรัพย์แต่ละตัวไม่เกิน 60% การให้ C 60% และ B 40% เป็นพอร์ต mean สูงสุด ได้ $0.6(14\%)+0.4(10\%)=12.4\%$ เป้า 14% จึงหลุดจากพื้นที่ feasible ใหม่ ข้อจำกัดเหล่านี้อาจสะท้อนวงเงินรายชื่อ ความเสี่ยงกระจุกตัว หรือขนาดการซื้อขายที่ทำได้

ข้อจำกัดน้ำหนักสูงสุดมักช่วยลดการพึ่งพาสินทรัพย์เดียว แต่ก็อาจทำให้ variance ต่ำสุด ณ เป้าหมายหนึ่งสูงขึ้น เพราะเราตัดทางเลือกบางส่วนออก ไม่มีเหตุผลที่จะคาดว่าการเพิ่มข้อจำกัดจะทำให้ optimum ดีกว่าเดิมภายใต้ objective และข้อมูลเข้าชุดเดิม

ส่วนการเปิด short หรือกู้ยืมขยายพื้นที่น้ำหนักและเพิ่มความเสี่ยงที่ต้องดูนอกเหนือจาก volatility เช่นภาระหลักประกันและต้นทุนเงินทุน ก่อนปลด bounds ต้องเปลี่ยนสมมติฐานในบทอธิบายและการตรวจผลให้ตรงกันด้วย

<span id="frontier-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

**1. ถ้าใช้ `annual_cov * example_weights` แทน `annual_cov @ example_weights` จะได้ผลเหมือนกันหรือไม่?**

<details>
<summary>ดูเฉลย: ตรวจขนาดผลลัพธ์</summary>

ไม่เหมือน `*` คูณสมาชิกตามตำแหน่งโดยกระจายน้ำหนักไปตามคอลัมน์ จึงยังได้ตาราง 3 × 3 ส่วน `@` คูณและรวมตามกติกา matrix จึงได้เวกเตอร์สามค่า ขั้นคูณน้ำหนักทางซ้ายอีกครั้งจึงจะรวมเป็น variance ตัวเดียว ควรตรวจ `.shape` เมื่อเริ่มเขียนสูตรหลายมิติ

</details>

**2. พอร์ตที่ target 7.5% มี variance ต่ำที่สุดในพอร์ตทุกชุดที่ mean 7.5% แล้ว ทำไมยังไม่ efficient?**

<details>
<summary>ดูเฉลย: เปรียบเทียบกับ GMV</summary>

GMV มี expected return ประมาณ 7.7126% สูงกว่าและ SD 8.7587% ต่ำกว่า 8.7759% ของ target 7.5% จึงครอบงำพอร์ตนั้น การดีที่สุดในกลุ่มที่ตรึง mean หนึ่งค่าไม่เพียงพอจะดีที่สุดเมื่อเปรียบเทียบข้าม target

</details>

**3. ถ้า optimizer แจ้งไม่สำเร็จแต่ส่งน้ำหนักออกมาแล้ว ควรนำไปวาด frontier ต่อหรือไม่?**

<details>
<summary>ดูเฉลย: เก็บสถานะและตรวจเงื่อนไข</summary>

ควรหยุดตรวจข้อความ สัดส่วนน้ำหนัก ผลรวม เป้าหมาย และความถูกต้องของ covariance ก่อน ค่าที่คืนมาอาจเป็นเพียงจุดสุดท้ายก่อนหยุด ซึ่งยังละเมิดข้อจำกัดหรือยังไม่เข้าใกล้ optimum ไม่ควรซ่อนจุดล้มเหลวแล้วเชื่อมเส้นผ่านราวกับคำนวณสำเร็จทุก target

</details>

## แหล่งอ้างอิงและอ่านต่อ

- EDHEC Business School, [Markowitz Optimization and the Efficient Frontier](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/197i9/markowitz-optimization-and-the-efficient-frontier), [Applying Quadprog to Draw the Efficient Frontier](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/tnbqp/applying-quadprog-to-draw-the-efficient-frontier) และ [Lab Session](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/9cjxj/lab-session-applying-quadprog-to-draw-the-efficient-frontier). อ่านประกอบ Lab 108–109; ตัวอย่างและโค้ดบนหน้านี้เขียนใหม่
- [NumPy: Matrix multiplication](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html) และ [SciPy: SLSQP](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html) สำหรับความหมายของคำสั่งที่ใช้
- [CVX Group: Portfolio optimization](https://www.cvxgrp.org/cvx_short_course/docs/applications/notebooks/portfolio_optimization.html) สำหรับรูปปัญหา mean–variance และข้อจำกัดแบบ convex

ไปต่อที่ [สินทรัพย์ปลอดความเสี่ยงและความไม่แน่นอนของค่าประมาณ](portfolio-estimation.html) เพื่อเลือกจุดบน frontier และตรวจว่าคำตอบเปลี่ยนเพียงใดเมื่อ forecast คลาดเคลื่อน
