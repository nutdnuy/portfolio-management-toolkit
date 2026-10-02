---
title: "Black–Litterman: รวมค่าตั้งต้นกับ Views"
description: เริ่มจากการผสมค่าประมาณตัวเดียว สร้าง posterior mean และความไม่แน่นอน แล้วแยกโจทย์เลือกน้ำหนักที่มีเงินสดออกจากพอร์ต long-only ที่ลงทุนเต็มจำนวน
---

# Black–Litterman: รวมค่าตั้งต้นกับ Views

<p class="lead">ถ้าค่าตั้งต้นบอกว่าผลตอบแทนคาดหวังอยู่ที่ 4% แต่งานวิเคราะห์ของเราประเมินได้ 6% เราควรใช้ตัวเลขใด และควรเชื่อตัวเลขนั้นแค่ไหน?</p>

บทก่อนหน้า [Implied Returns และ Active Views](implied-returns-views.html) เตรียมค่าตั้งต้น $\Pi$ จากน้ำหนักอ้างอิง และเขียนมุมมองเพิ่มเติมเป็น $P,Q,\Omega$ แล้ว ขั้นตอนของ [Black–Litterman](glossary.html#black-litterman) ในบทนี้คือรวมข้อมูลสองส่วน โดยให้ความไม่แน่นอนของแต่ละส่วนกำหนดขนาดการปรับค่าเฉลี่ย จากนั้นจึงนำผลไปเลือกน้ำหนักพอร์ตภายใต้ข้อจำกัดที่ต้องการ

ตัวอย่างทั้งหมดเป็นข้อมูลสมมติที่เขียนขึ้นใหม่ ใช้ผลตอบแทนคาดหวังส่วนเกินจากอัตราปลอดความเสี่ยงในช่วงหนึ่งปีเดียวกัน หน่วยทศนิยม เช่น `0.04` หมายถึง 4% ต่อปี ไม่มีต้นทุน ภาษี หรือข้อมูลราคาตลาดจริง โค้ดรันตามลำดับใน Notebook ใหม่ได้ด้วย NumPy, pandas และ SciPy โดยไม่ต้องรันบทก่อนหน้า [ดาวน์โหลด Notebook](notebooks/black-litterman.ipynb)

<span id="bayesian-one-number"></span>

## ลองรวมค่าประมาณเพียงตัวเดียวก่อน

สมมติว่าเราต้องการประมาณค่าเฉลี่ยผลตอบแทนส่วนเกินที่ยังไม่รู้ เรียกค่านี้ว่า $\mu$ ข้อมูลก่อนเพิ่ม View หรือ [prior](glossary.html#prior) ของเราระบุว่า $\mu$ มีค่าเฉลี่ย 4% และ SD ของความไม่แน่นอนเท่ากับ 2 จุดเปอร์เซ็นต์ เขียนด้วยการแจกแจง Normal ได้ว่า

$$
\mu\sim N(0.04,\;0.02^2).
$$

เลขตัวที่สองใน $N(\text{mean},\text{variance})$ เป็น variance จึงต้องยกกำลังสอง ส่วน 2 จุดเปอร์เซ็นต์นี้วัดความไม่แน่นอนเกี่ยวกับ $\mu$ ไม่ใช่ SD ของผลตอบแทนที่สินทรัพย์จะให้ในปีหน้า

งานวิเคราะห์อีกส่วนให้ View ว่า $\mu$ อยู่ที่ 6% โดยมีความคลาดเคลื่อนแบบ Normal ที่ SD เท่ากับ 1 จุดเปอร์เซ็นต์ เราสมมติว่าความคลาดเคลื่อนของ View เป็นอิสระจากค่า $\mu$ ที่มี prior ข้างต้น การรวมข้อมูลภายใต้สมมติฐานนี้ใช้น้ำหนักแปรผกผันกับ variance เรียก $1/\text{variance}$ ว่า precision

$$
v_{\text{post}}=\frac{1}{1/0.02^2+1/0.01^2},\qquad
\mu_{\text{post}}=v_{\text{post}}
\left(\frac{0.04}{0.02^2}+\frac{0.06}{0.01^2}\right).
$$

Prior มี precision 2,500 ส่วน View มี precision 10,000 จึงให้น้ำหนัก 20% กับ prior และ 80% กับ View ค่าเฉลี่ยหลังรวม หรือ [posterior](glossary.html#posterior) เท่ากับ $0.2(4\%)+0.8(6\%)=5.6\%$

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize

scalar_prior_mean, scalar_prior_se = 0.04, 0.02
scalar_view_mean, scalar_view_se = 0.06, 0.01
scalar_prior_precision = 1 / scalar_prior_se**2
scalar_view_precision = 1 / scalar_view_se**2
scalar_posterior_var = 1 / (scalar_prior_precision + scalar_view_precision)
scalar_posterior_mean = scalar_posterior_var * (
    scalar_prior_precision * scalar_prior_mean
    + scalar_view_precision * scalar_view_mean
)
print(f"Posterior expected return: {scalar_posterior_mean:.4%}")
print(f"Posterior uncertainty SD: {np.sqrt(scalar_posterior_var):.4%}")
print("Weights on prior and view:",
      scalar_posterior_var * np.array([scalar_prior_precision, scalar_view_precision]))
```

SD ของความไม่แน่นอนหลังรวมเท่ากับประมาณ 0.8944 จุดเปอร์เซ็นต์ ต่ำกว่าก่อนรวม เพราะแบบจำลองถือว่าเราได้รับข้อมูลเพิ่มที่มีประโยชน์ นี่เป็นผลภายใต้สมมติฐานเรื่องความเป็นอิสระและความคลาดเคลื่อนที่ระบุไว้ หาก View เพียงนำตัวเลขเดิมมาพูดซ้ำ เราจะให้น้ำหนักเหมือนเป็นข้อมูลใหม่ไม่ได้

ในโค้ด `**2` คือยกกำลังสอง และ `np.sqrt` คือรากที่สอง ส่วนรูปแบบ `:.4%` คูณตัวเลขทศนิยมด้วย 100 เพื่อแสดงเป็นเปอร์เซ็นต์สี่ตำแหน่ง ตัวแปรยังเก็บค่าที่ไม่ปัดเศษไว้สำหรับคำนวณต่อ

<span id="black-litterman-inputs"></span>

## กลับมาที่สามสินทรัพย์และสอง Views

ใช้สินทรัพย์สมมติ A/B/C ชุดเดียวกับบทก่อนหน้า น้ำหนักอ้างอิงคือ $w_0=(0.5,0.3,0.2)^\mathsf{T}$ และ covariance ของผลตอบแทนส่วนเกินหนึ่งปีคือ

$$
\Sigma=\begin{bmatrix}
0.04&0.012&0.008\\
0.012&0.0225&0.0045\\
0.008&0.0045&0.01
\end{bmatrix}.
$$

รากที่สองของแนวทแยงให้ SD ผลตอบแทน 20%, 15% และ 10% ต่อปีตามลำดับ เรากำหนดค่าความเกลียดความเสี่ยงสำหรับสร้าง prior เป็น $\delta=2.5$ จึงได้ [implied excess returns](glossary.html#implied-returns)

$$
\Pi=\delta\Sigma w_0
=\begin{bmatrix}0.063\\0.034125\\0.018375\end{bmatrix}.
$$

นี่เป็นผลตอบแทนที่สอดคล้องกับน้ำหนักอ้างอิงภายใต้ covariance และแบบจำลองที่เลือก ไม่ใช่ผลตอบแทนอนาคตที่อ่านออกมาจากราคาตลาดได้โดยปราศจากสมมติฐาน

สอง [Views](glossary.html#active-views) ของเราคือ C มีผลตอบแทนส่วนเกินคาดหวัง 2.5% และ A มีผลตอบแทนคาดหวังสูงกว่า B อยู่ 2 จุดเปอร์เซ็นต์:

$$
P=\begin{bmatrix}0&0&1\\1&-1&0\end{bmatrix},\qquad
Q=\begin{bmatrix}0.025\\0.020\end{bmatrix}.
$$

แถวแรกเลือกค่าเฉลี่ยของ C ส่วนแถวที่สองนำค่าเฉลี่ย A ลบ B ดังนั้น $P\mu$ มีสองค่า ตรงกับจำนวน Views ไม่ใช่จำนวนสินทรัพย์ หาก View แรกเป็นผลตอบแทนรวมแทนผลตอบแทนส่วนเกิน ต้องหักอัตราปลอดความเสี่ยงของช่วงเดียวกันก่อน ส่วน View แบบ A ลบ B หักอัตราปลอดความเสี่ยงเดียวกันออกจากทั้งสองฝั่งแล้วหายไป

กำหนดความไม่แน่นอนของ prior เป็น $\tau\Sigma$ โดย $\tau=0.05$ และใช้กฎสาธิตของ Lab สำหรับ [ความไม่แน่นอนของ Views](glossary.html#view-uncertainty): เก็บเฉพาะแนวทแยงของ $P\tau\Sigma P^\mathsf{T}$ เป็น $\Omega$ ค่า 0.05 และกฎนี้เป็นข้อกำหนดของตัวอย่าง ไม่ได้ประมาณมาจากความแม่นยำของผู้วิเคราะห์

```python
assets = ["A", "B", "C"]
covariance = np.array([[0.0400, 0.0120, 0.0080],
                       [0.0120, 0.0225, 0.0045],
                       [0.0080, 0.0045, 0.0100]])
benchmark_weights = np.array([0.5, 0.3, 0.2])
risk_aversion = 2.5
pi = risk_aversion * covariance @ benchmark_weights
P = np.array([[0.0, 0.0, 1.0], [1.0, -1.0, 0.0]])
Q = np.array([0.025, 0.020])
tau = 0.05
prior_mean_cov = tau * covariance
projected_prior_cov = P @ prior_mean_cov @ P.T
omega = np.diag(np.diag(projected_prior_cov))
print("Prior excess returns (%):", np.round(pi * 100, 4))
print("View surprises (percentage points):", np.round((Q - P @ pi) * 100, 4))
print("Projected prior covariance:\n", projected_prior_cov)
print("View-error covariance:\n", omega)
```

`@` คูณเมทริกซ์ ส่วน `.T` สลับแถวกับคอลัมน์ `np.diag` ครั้งแรกดึงแนวทแยงออกมาเป็นเวกเตอร์ และครั้งที่สองนำเวกเตอร์นั้นไปสร้างเมทริกซ์แนวทแยง จึงได้

$$
P\tau\Sigma P^\mathsf{T}
=\begin{bmatrix}0.0005&0.000175\\0.000175&0.001925\end{bmatrix},\qquad
\Omega=\begin{bmatrix}0.0005&0\\0&0.001925\end{bmatrix}.
$$

เมทริกซ์แรกวัดความไม่แน่นอนของค่าที่ prior คาดสำหรับสอง Views ส่วนเมทริกซ์หลังวัดความคลาดเคลื่อนของแหล่งข้อมูล Views ที่เราใส่เพิ่ม การตั้งช่องนอกแนวทแยงของ $\Omega$ เป็นศูนย์จึงเป็นสมมติฐานว่าความคลาดเคลื่อนของ Views เป็นอิสระ ไม่ได้หมายความว่าพอร์ตที่ Views กล่าวถึงไม่มีความสัมพันธ์กัน

ความต่าง $Q-P\Pi$ หรือ view surprise เท่ากับ $(0.006625,-0.008875)^\mathsf{T}$ View ของ C สูงกว่า prior 0.6625 จุดเปอร์เซ็นต์ แต่ View A ชนะ B อยู่ 2 จุดเปอร์เซ็นต์ต่ำกว่า prior spread ที่ 2.8875 จุดเปอร์เซ็นต์ จึงเป็นการปรับความคาดหวังส่วนต่าง A/B ลง แม้ประโยคของ View จะยังใช้คำว่า A ชนะ B

<span id="black-litterman-posterior"></span>

## ปรับค่าเฉลี่ยด้วยขนาดความไม่แน่นอน

แบบจำลองกำหนดให้ $\mu\sim N(\Pi,\tau\Sigma)$ และ $Q=P\mu+\varepsilon$ โดย $\varepsilon\sim N(0,\Omega)$ และ $\varepsilon$ เป็นอิสระจาก $\mu$ เราจะใช้สัญลักษณ์ $\mu_{BL}$ สำหรับค่าเฉลี่ย posterior ของ $\mu$

เริ่มจากเมทริกซ์ขนาดสอง Views คูณสอง Views:

$$
A_v=P\tau\Sigma P^\mathsf{T}+\Omega.
$$

จากนั้นสร้างเมทริกซ์ตัวคูณการปรับ หรือ gain:

$$
G=\tau\Sigma P^\mathsf{T}A_v^{-1},\qquad
\mu_{BL}=\Pi+G(Q-P\Pi).
$$

สูตรมีความหมายว่าเริ่มจาก prior แล้วบวกการปรับตามความต่างของ Views ส่วน $G$ กำหนดว่าความต่างแต่ละ View ส่งต่อไปยังค่าเฉลี่ยแต่ละสินทรัพย์เท่าใด โดยใช้ทั้ง covariance และความไม่แน่นอนที่ระบุไว้

| ตัวแปร | ขนาดในตัวอย่าง | ความหมาย |
|---|---|---|
| $\Pi,\mu_{BL}$ | 3 ค่า | ค่าเฉลี่ยผลตอบแทนส่วนเกินของ A/B/C |
| $P$ | 2 × 3 | แปลงค่าเฉลี่ยสินทรัพย์เป็นค่าของสอง Views |
| $Q-P\Pi$ | 2 ค่า | ความต่างของ Views จาก prior |
| $A_v$ | 2 × 2 | ความไม่แน่นอนรวมในพื้นที่ของ Views |
| $G$ | 3 × 2 | ส่งความต่างสองค่าไปปรับค่าเฉลี่ยสามสินทรัพย์ |

ในโปรแกรมเราไม่จำเป็นต้องสร้าง inverse ทั้งเมทริกซ์ [`np.linalg.solve(A, B)`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html) หา $X$ ที่ทำให้ $AX=B$ โค้ดต่อไปแก้ $A_v X=P\tau\Sigma$ แล้ว transpose คำตอบเพื่อให้ได้ $G$ โดยใช้ความสมมาตรของเมทริกซ์ covariance

```python
view_system = P @ prior_mean_cov @ P.T + omega
gain = np.linalg.solve(view_system, P @ prior_mean_cov).T
posterior_mean = pi + gain @ (Q - P @ pi)
posterior_mean_cov = prior_mean_cov - gain @ P @ prior_mean_cov
predictive_cov = covariance + posterior_mean_cov
print("Gain matrix:\n", np.round(gain, 6))
print(pd.DataFrame({"Prior excess (%)": pi * 100,
                    "Posterior excess (%)": posterior_mean * 100}, index=assets).round(4).to_string())
print("Posterior view means (%):", np.round(P @ posterior_mean * 100, 4))
print("Posterior uncertainty of the mean:\n", np.round(posterior_mean_cov, 8))
```

ได้ค่าเฉลี่ย posterior ของ A/B/C ประมาณ 6.2156%, 3.7098% และ 2.1458% ต่อปี ช่อง A ของ gain บอกว่าต้องคูณ surprise ของ View C ด้วย 0.339061 และ surprise ของ View A/B ด้วย 0.348225 จึงคำนวณการปรับ A ได้ประมาณ

$$
0.339061(0.006625)+0.348225(-0.008875)
\approx-0.0008442.
$$

ดังนั้นค่าเฉลี่ย A ลดจาก 6.3% เป็นประมาณ 6.2156% การคำนวณพร้อมกันนี้คำนึงถึงความสัมพันธ์ระหว่างสินทรัพย์ ค่าเฉลี่ยของสินทรัพย์ที่ไม่ได้ถูกเลือกโดย View ใดโดยตรงก็อาจเปลี่ยนได้ การผสมจึงไม่ใช่ค่าเฉลี่ยถ่วงน้ำหนักทีละสินทรัพย์แบบตัวอย่างหนึ่งมิติเสมอไป

เมื่ออ่านผลผ่าน $P\mu_{BL}$ เราได้ C ประมาณ 2.1458% และ A ลบ B ประมาณ 2.5057 จุดเปอร์เซ็นต์ Views ยังไม่ถูกบังคับให้เกิดขึ้นตรงตัว เพราะ $\Omega$ ระบุว่าข้อมูล Views มีความคลาดเคลื่อน

<span id="mean-uncertainty-predictive-risk"></span>

## ความไม่แน่นอนของค่าเฉลี่ยยังไม่ใช่ความเสี่ยงของผลตอบแทน

นอกจากค่าเฉลี่ย posterior แล้ว เราคำนวณ covariance ของความไม่แน่นอนที่เหลือเกี่ยวกับ $\mu$ ได้ด้วย:

$$
M=\tau\Sigma-GP\tau\Sigma.
$$

ภายใต้โมเดลนี้ $\mu$ หลังรับ Views มีการแจกแจง $N(\mu_{BL},M)$ ถ้าต้องการความเสี่ยงของผลตอบแทนในปีหน้าต้องพิจารณาอีกชั้นหนึ่ง สมมติให้ผลตอบแทนส่วนเกิน $R$ เมื่อทราบ $\mu$ มีค่าเฉลี่ย $\mu$ และ covariance $\Sigma$ ที่ถือว่าทราบแล้ว ความผันผวนรอบค่าเฉลี่ยนี้ยังคงมีอยู่ แม้เราจะรู้ค่าเฉลี่ยอย่างแม่นยำ

การรวมความไม่แน่นอนสองชั้นให้

$$
\operatorname{Cov}(R\mid\text{Views})
=\underbrace{\Sigma}_{\text{ความผันผวนรอบค่าเฉลี่ย}}
+\underbrace{M}_{\text{ความไม่แน่นอนของค่าเฉลี่ย}}
=\Sigma_{\text{predictive}}.
$$

เราจึงเก็บทั้งสามผลแยกกัน: `mean` คือ $\mu_{BL}$, `mean_cov` คือ $M$ และ `covariance + mean_cov` คือ predictive covariance อย่านำ $M$ เพียงอย่างเดียวไปใช้เป็น covariance ของผลตอบแทนสินทรัพย์

<details>
<summary>อ่านเพิ่ม: สูตรที่เขียนด้วย precision matrix</summary>

หาก $\tau\Sigma$ และ $\Omega$ กลับเมทริกซ์ได้ สูตรเดียวกันเขียนเป็น

$$
M=\left[(\tau\Sigma)^{-1}+P^\mathsf{T}\Omega^{-1}P\right]^{-1},
$$

$$
\mu_{BL}=M\left[(\tau\Sigma)^{-1}\Pi
+P^\mathsf{T}\Omega^{-1}Q\right].
$$

นี่เป็นรูปหลายมิติของการบวก precision ในตัวอย่างแรก รูป gain ที่เราใช้ไม่ต้องกลับ $\Omega$ โดยตรง จึงใช้กับบางกรณีที่ $\Omega$ เป็น singular ได้ ตราบใดที่ $A_v$ ยังแก้ระบบสมการได้ อย่างไรก็ตามการเปลี่ยนรูปสูตรไม่ได้ทำให้ข้อมูลซ้ำหรือระบบ singular ทุกชนิดหายไป

</details>

รวมขั้นตอนเป็นฟังก์ชันเพื่อทดลองเปลี่ยนข้อมูลเข้าได้สะดวก ฟังก์ชันนี้ใช้ array หนึ่งมิติสำหรับ $\Pi,Q$ และเมทริกซ์สองมิติสำหรับตัวอื่น โดยให้ลำดับสินทรัพย์ตรงกันทุกจุด

```python
def bl_posterior(covariance, pi, P, Q, omega, tau=0.05):
    covariance, pi, P, Q, omega = [np.asarray(x, dtype=float)
                                  for x in (covariance, pi, P, Q, omega)]
    if (covariance.ndim != 2 or covariance.shape[0] == 0
            or covariance.shape[0] != covariance.shape[1] or pi.ndim != 1
            or P.ndim != 2 or Q.ndim != 1):
        raise ValueError("Need a square covariance, vectors pi/Q and a matrix P")
    n, k = len(pi), len(Q)
    if covariance.shape != (n, n) or P.shape != (k, n) or omega.shape != (k, k):
        raise ValueError("Asset and view dimensions do not match")
    if not all(np.isfinite(x).all() for x in (covariance, pi, P, Q, omega)):
        raise ValueError("Inputs must be finite")
    if not np.isfinite(tau) or tau <= 0:
        raise ValueError("Tau must be finite and positive")
    if (not np.allclose(covariance, covariance.T, atol=1e-12)
            or not np.allclose(omega, omega.T, atol=1e-12)):
        raise ValueError("Covariance matrices must be symmetric")
    np.linalg.cholesky(covariance)  # requires positive definite asset covariance
    prior_cov = tau * covariance
    if k == 0:
        return pi.copy(), prior_cov, covariance + prior_cov
    if np.linalg.eigvalsh(omega).min() < -1e-12:
        raise ValueError("View-error covariance must be positive semidefinite")
    system = P @ prior_cov @ P.T + omega
    system_eigenvalues = np.linalg.eigvalsh(system)
    if system_eigenvalues.min() <= 1e-12 * system_eigenvalues.max():
        raise np.linalg.LinAlgError("View system is singular or too close to singular")
    np.linalg.cholesky(system)  # redundant exact views may make this singular
    update = np.linalg.solve(system, P @ prior_cov).T
    mean = pi + update @ (Q - P @ pi)
    mean_cov = prior_cov - update @ P @ prior_cov
    mean_cov = (mean_cov + mean_cov.T) / 2  # remove roundoff asymmetry
    return mean, mean_cov, covariance + mean_cov

bl_mean, bl_M, bl_predictive = bl_posterior(covariance, pi, P, Q, omega, tau)
assert np.allclose(bl_mean, posterior_mean)
assert np.allclose(bl_M, posterior_mean_cov)
print(pd.DataFrame({
    "Prior mean uncertainty SD (%)": np.sqrt(np.diag(prior_mean_cov)) * 100,
    "Posterior mean uncertainty SD (%)": np.sqrt(np.diag(bl_M)) * 100,
    "Conditional return SD (%)": np.sqrt(np.diag(covariance)) * 100,
    "Predictive return SD (%)": np.sqrt(np.diag(bl_predictive)) * 100
}, index=assets).round(4).to_string())
```

สำหรับ C, SD ของความไม่แน่นอนเกี่ยวกับค่าเฉลี่ยลดจากประมาณ 2.2361 เป็น 1.5748 จุดเปอร์เซ็นต์ แต่ SD ของผลตอบแทนที่คาดการณ์ยังอยู่ประมาณ 10.1232% ต่อปี เพราะรวมความผันผวนพื้นฐาน 10% ด้วย การลดความไม่แน่นอนของค่าเฉลี่ยไม่ได้ทำให้การลงทุนไม่มีความเสี่ยง

หาก Views ตรงกับ prior พอดีจน $Q-P\Pi=0$, ค่าเฉลี่ย posterior จะไม่เปลี่ยน แต่ข้อมูล Views ที่กำหนดว่ามีความแม่นยำอาจยังลด $M$ ได้ การมีข้อมูลมายืนยันค่าเดิมจึงต่างจากการไม่มี Views เลย

`np.asarray(..., dtype=float)` ทำให้ข้อมูลเข้าอยู่ในรูป array ตัวเลข `np.isfinite` ปฏิเสธทั้งค่าที่หายไปและ infinity ส่วน `np.linalg.cholesky` ตรวจว่าระบบที่ต้องใช้เป็น positive definite โค้ดยังหยุดถ้าเมทริกซ์ของ Views singular หรือใกล้ singular มาก เราควรตรวจว่ามี Views ซ้ำหรือข้อมูลเข้าผิดก่อนเปลี่ยนตัวแก้สมการ ผลต่างเล็กน้อยระหว่าง `mean_cov` กับ transpose จาก roundoff ถูกเฉลี่ยกลับให้สมมาตร

การทำงานได้ของสมการไม่ยืนยันว่า $\Sigma$ เป็นค่าความเสี่ยงจริง เราถือว่า covariance นี้ทราบแล้วเพื่อแยกบทเรียนเรื่องค่าเฉลี่ยออกมา แต่ในการใช้งาน covariance เองก็ต้องประมาณ และมีความคลาดเคลื่อนตาม [บท Covariance Estimation](covariance-estimation.html)

<span id="black-litterman-confidence"></span>

## ถ้าเชื่อ Views มากขึ้นหรือน้อยลง

ขนาดของ $\Omega$ วัดความคลาดเคลื่อน ไม่ใช่เปอร์เซ็นต์โอกาสที่ View จะถูกต้อง ถ้าเพิ่ม $\Omega$ โดยคงข้อมูลอื่นไว้ เรากำลังบอกว่า Views มีข้อมูลแม่นยำน้อยลง หากลด $\Omega$ เรากำลังเพิ่มความมั่นใจในข้อมูล Views

ทดลองคูณ $\Omega$ ทั้งเมทริกซ์ด้วย 0, 0.1, 1, 10 และหนึ่งล้าน ค่า 0 หมายถึงถือว่าทั้งสองสมการของ Views แน่นอนในแบบจำลอง ตัวอย่างนี้ใช้ได้เพราะสองแถวของ $P$ ไม่ซ้ำกันและเมทริกซ์ $A_v$ ยังเป็น PD

```python
confidence_rows = []
for multiplier in [0.0, 0.1, 1.0, 10.0, 1_000_000.0]:
    mean, mean_cov, _ = bl_posterior(covariance, pi, P, Q, multiplier * omega, tau)
    confidence_rows.append({"Omega multiplier": multiplier,
                            "C expected excess (%)": mean[2] * 100,
                            "A-B expected spread (%)": (P @ mean)[1] * 100,
                            "C mean uncertainty SD (%)": np.sqrt(max(mean_cov[2, 2], 0)) * 100})
confidence_table = pd.DataFrame(confidence_rows).set_index("Omega multiplier")
print(confidence_table.round(6).to_string())
exact_mean, exact_M, _ = bl_posterior(covariance, pi, P, Q, np.zeros((2, 2)), tau)
assert np.allclose(P @ exact_mean, Q)
assert np.allclose(P @ exact_M @ P.T, 0, atol=1e-12)
print("Uncertainty left outside the two exact views:", round(np.trace(exact_M), 8))
```

| ตัวคูณ Ω | ค่าเฉลี่ย C (%) | ส่วนต่างค่าเฉลี่ย A − B (จุดเปอร์เซ็นต์) |
|---:|---:|---:|
| 0 | 2.500000 | 2.000000 |
| 0.1 | 2.431298 | 2.102541 |
| 1 | 2.145762 | 2.505742 |
| 10 | 1.890899 | 2.826199 |
| 1,000,000 | 1.837501 | 2.887499 |

เมื่อเพิ่มความคลาดเคลื่อนมาก ๆ ผลเข้าใกล้ prior ของ C ที่ 1.8375% และ prior spread ที่ 2.8875 จุดเปอร์เซ็นต์ ส่วนกรณีไม่ให้มีความคลาดเคลื่อน เราได้ $P\mu_{BL}=Q$ และความไม่แน่นอนของสองค่าที่ Views ระบุเป็นศูนย์

แต่ $M$ ทั้งเมทริกซ์ยังไม่เป็นศูนย์: รู้ค่าเฉลี่ย C และส่วนต่าง A/B ไม่ได้ทำให้รู้ระดับค่าเฉลี่ย A กับ B แยกจากกันทั้งหมด ยังเหลือความไม่แน่นอนในทิศทางที่ Views ไม่ได้ระบุไว้ อีกทั้ง $\Sigma$ ยังมีอยู่ แม้สมมติว่า Views ของค่าเฉลี่ยแน่นอน ผลตอบแทนที่เกิดขึ้นจริงก็ไม่ได้ถูกบังคับให้ตรงกับค่าเฉลี่ยนั้น

ตารางนี้เป็นการเปลี่ยนความคลาดเคลื่อนของสอง Views พร้อมกันตามข้อมูลชุดเดียว ไม่ใช่ข้อพิสูจน์ว่าการปรับความมั่นใจของ View หนึ่งจะทำให้ทุกน้ำหนักเคลื่อนทางเดียวเสมอเมื่อมี Views หลายข้อสัมพันธ์กัน

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/advanced-view-confidence-mobile.svg">
<img src="assets/charts/advanced-view-confidence.svg" alt="เมื่อใช้เฉพาะ View ของ C ค่าเฉลี่ย posterior เริ่มที่ 2.5% เมื่อ view error เป็นศูนย์ และเข้าใกล้ prior 1.8375% เมื่อความไม่แน่นอนเพิ่ม" loading="lazy" width="720" height="560">
</picture>
<figcaption>เพื่อแยกผลของความเชื่อมั่น กราฟนี้ใช้เฉพาะ absolute View ของ C และตัด View A ลบ B ออก คง prior และ tau เดิม แกนนอนเป็น SD ของข้อผิดพลาดใน View; ที่ SD ≈ 2.2361 จุดเปอร์เซ็นต์ ค่าเฉลี่ย C เท่ากับ 2.16875% จึงต่างจากกรณีสอง Views ในตารางด้านบน</figcaption>
</figure>

<span id="black-litterman-tau"></span>

## ทำไมเปลี่ยน τ แล้วค่าเฉลี่ยอาจไม่เปลี่ยน

ถ้าคง $\Omega$ ไว้ แต่เพิ่ม $\tau$ เรากำลังเพิ่มความไม่แน่นอนของ prior เมื่อเทียบกับ Views อย่างไรก็ตามกฎสาธิตที่ใช้สร้าง $\Omega$ ข้างต้นก็คูณด้วย $\tau$ ด้วย หากสร้าง $\Omega$ ใหม่ตามกฎนี้ทุกครั้ง ความไม่แน่นอนทั้งสองส่วนจะเพิ่มด้วยตัวคูณเดียวกัน

เขียน $\Omega=\tau\Omega_0$ แล้วแทนลงใน gain จะได้

$$
G=\Sigma P^\mathsf{T}
\left(P\Sigma P^\mathsf{T}+\Omega_0\right)^{-1}.
$$

$\tau$ ตัดกันในสูตรค่าเฉลี่ย posterior แต่ $M$ ยังมีขนาดแปรตาม $\tau$ จึงไม่ตัดกันจาก predictive covariance ทดลองทั้งกรณีสร้าง $\Omega$ ใหม่และคง $\Omega$ เดิมไว้:

```python
tau_rows = []
for tau_value in [0.01, 0.05, 0.20]:
    scaled_omega = np.diag(np.diag(P @ (tau_value * covariance) @ P.T))
    scaled_mean, scaled_M, scaled_predictive = bl_posterior(
        covariance, pi, P, Q, scaled_omega, tau_value)
    fixed_mean, _, _ = bl_posterior(covariance, pi, P, Q, omega, tau_value)
    assert np.allclose(scaled_mean, bl_mean)
    tau_rows.append({"Tau": tau_value,
                     "C mean, scaled Omega (%)": scaled_mean[2] * 100,
                     "C mean, fixed Omega (%)": fixed_mean[2] * 100,
                     "C mean uncertainty SD (%)": np.sqrt(scaled_M[2, 2]) * 100,
                     "C predictive return SD (%)": np.sqrt(scaled_predictive[2, 2]) * 100})
print(pd.DataFrame(tau_rows).set_index("Tau").round(4).to_string())
```

เมื่อสร้าง $\Omega$ ใหม่ตาม $\tau$, ค่าเฉลี่ย C อยู่ที่ประมาณ 2.1458% เท่าเดิมทั้งสามกรณี แต่ SD ของความไม่แน่นอนเกี่ยวกับค่าเฉลี่ย C เปลี่ยนจากประมาณ 0.7043 เป็น 1.5748 และ 3.1496 จุดเปอร์เซ็นต์ตามลำดับ ส่วนกรณีคง $\Omega$ เดิม ค่าเฉลี่ย C เปลี่ยนจากประมาณ 1.9362% ไปเป็น 2.1458% และ 2.3516%

ดังนั้นประโยคว่า “ค่า tau ไม่มีผล” ต้องระบุว่าไม่มีผลต่อค่าเฉลี่ยภายใต้กฎการปรับ $\Omega$ ที่ใช้อยู่เท่านั้น หากนำ predictive covariance ไปหาน้ำหนักพอร์ต ผลของ tau อาจยังปรากฏผ่านความเสี่ยง

<span id="correlated-and-duplicate-views"></span>

## Views สองข้ออาจมาจากข้อมูลชุดเดียวกัน

ผู้วิเคราะห์สองคนอาจใช้ประมาณการเศรษฐกิจชุดเดียวกันจนความผิดพลาดสัมพันธ์กัน หรือ Views คนละข้ออาจมาจากโมเดลตัวเดียวกัน การตั้ง $\Omega$ เป็นแนวทแยงในทุกกรณีจะข้ามเรื่องนี้ไป

ตัวอย่างต่อไปคง variance ของความคลาดเคลื่อนแต่ละ View ไว้ แต่สมมติ correlation ของความคลาดเคลื่อนเท่ากับ 0.6 เราสร้างช่องนอกแนวทแยงด้วยสูตรเดียวกับ covariance ทั่วไป คือ correlation คูณ SD ทั้งสองตัว

```python
view_error_correlation = 0.6
view_error_sd = np.sqrt(np.diag(omega))
omega_correlated = np.outer(view_error_sd, view_error_sd) * np.array(
    [[1.0, view_error_correlation], [view_error_correlation, 1.0]])
correlated_mean, correlated_M, correlated_predictive = bl_posterior(
    covariance, pi, P, Q, omega_correlated, tau)
print("Correlated view-error covariance:\n", np.round(omega_correlated, 8))
print(pd.DataFrame({"Independent errors (%)": bl_mean * 100,
                    "Correlated errors (%)": correlated_mean * 100}, index=assets).round(4).to_string())
```

ได้ covariance ของ view errors นอกแนวทแยงประมาณ 0.00058864 ซึ่งเป็นคนละค่ากับ 0.000175 ใน $P\tau\Sigma P^\mathsf{T}$ ผลค่าเฉลี่ย A/B/C เปลี่ยนเป็นประมาณ 6.0981%, 3.8588% และ 2.2570% ตามลำดับ

ผลนี้ไม่ควรถูกแปลว่า errors สัมพันธ์กันแล้วต้องเชื่อ Views น้อยลงทุกทิศทางเสมอไป ในตัวอย่าง surprise ของ C เป็นบวก แต่ surprise ของ A/B เป็นลบ เมื่อ errors มักเคลื่อนไปทางเดียวกันตามสมมติฐาน ส่วนต่างของสัญญาณจึงมีความไม่แน่นอนต่างจากกรณี errors อิสระ การรวมต้องใช้เมทริกซ์ทั้งหมด

### การคัดลอก View เดิมไม่ได้สร้างหลักฐานใหม่

แยกออกมาเฉพาะ View ของ C เพื่อเห็นปัญหานี้ชัดขึ้น หากเพิ่มแถว C=2.5% เดิมอีกหนึ่งแถวแล้วตั้ง errors ให้เป็นอิสระ โปรแกรมจะเข้าใจว่าเราได้ข้อมูลใหม่อีกชิ้น ถ้าเป็นการคัดลอกข้อมูลเดิมจริง ต้องรวมเป็น View เดียว หรือระบุการพึ่งพากันให้ตรงความจริง

```python
one_P, one_Q, one_omega = P[:1], Q[:1], omega[:1, :1]
one_mean, one_M, _ = bl_posterior(covariance, pi, one_P, one_Q, one_omega, tau)
duplicate_P = np.repeat(one_P, 2, axis=0)
duplicate_Q = np.repeat(one_Q, 2)
duplicate_rows = [{"Treatment": "One observation", "C mean (%)": one_mean[2] * 100,
                   "C mean uncertainty SD (%)": np.sqrt(one_M[2, 2]) * 100}]
for label, error_corr in [("Two independent observations", 0.0),
                          ("Nearly identical errors", 0.999)]:
    duplicate_omega = one_omega[0, 0] * np.array([[1.0, error_corr], [error_corr, 1.0]])
    mean, mean_cov, _ = bl_posterior(covariance, pi, duplicate_P, duplicate_Q, duplicate_omega, tau)
    duplicate_rows.append({"Treatment": label, "C mean (%)": mean[2] * 100,
                           "C mean uncertainty SD (%)": np.sqrt(mean_cov[2, 2]) * 100})
print(pd.DataFrame(duplicate_rows).set_index("Treatment").round(6).to_string())
try:
    bl_posterior(covariance, pi, duplicate_P, duplicate_Q,
                 np.full((2, 2), one_omega[0, 0]), tau)
except np.linalg.LinAlgError:
    print("Exactly duplicated information: keep one row instead of solving a singular system")
```

View ของ C เพียงข้อเดียวให้ค่าเฉลี่ย posterior C เท่ากับ 2.168750% และ SD ความไม่แน่นอนประมาณ 1.581139 จุดเปอร์เซ็นต์ หากป้อนซ้ำแต่บอกว่าเป็นข้อมูลอิสระ ค่าเฉลี่ยจะขยับไปหา 2.5% มากขึ้นเป็น 2.279167% และ SD ลดเหลือ 1.290994 จุดเปอร์เซ็นต์ การเปลี่ยนนี้สมเหตุผลเมื่อเป็นหลักฐานอิสระจริง แต่เป็นการนับข้อมูลซ้ำถ้าใช้รายงานเดิมสองครั้ง

เมื่อ errors มี correlation 0.999 ผลเกือบกลับมาตรงกับ View เดียว ส่วนกรณีสำเนาเหมือนกันทุกประการที่ correlation เป็น 1 ระบบในรูปนี้เป็น singular โค้ดจึงหยุดและแจ้งให้เก็บแถวเดียว `try` กับ `except` ในตัวอย่างใช้รับข้อผิดพลาดที่ตั้งใจสาธิต ไม่ได้ทำให้ระบบที่ไม่มีคำตอบเฉพาะตัวกลายเป็นระบบที่ใช้ได้

<span id="black-litterman-portfolio-choices"></span>

## ค่าเฉลี่ยชุดเดียวกันยังเลือกพอร์ตได้หลายโจทย์

Black–Litterman ให้ค่าประมาณและความไม่แน่นอน ขั้นเลือกพอร์ตต้องระบุอีกว่าถือเงินสดได้หรือไม่ กู้ยืมได้หรือไม่ ขายชอร์ตได้หรือไม่ และใช้ covariance ใดวัดความเสี่ยง เราจะเทียบสองโจทย์โดยคงข้อมูล Views ชุดเดียวกัน

### โจทย์แรก: ให้น้ำหนักสินทรัพย์เสี่ยงเปลี่ยนได้ และถือเงินสดส่วนที่เหลือ

ให้ $\gamma>0$ เป็นความเกลียดความเสี่ยงของผู้เลือกพอร์ต และ $C_R$ เป็น covariance ที่เลือกใช้ ประโยชน์เชิงค่าเฉลี่ย–variance ของพอร์ตเขียนเป็น

$$
U(w)=w^\mathsf{T}\mu_{BL}-\frac{\gamma}{2}w^\mathsf{T}C_Rw.
$$

เมื่อไม่มีข้อจำกัดน้ำหนักและ $C_R$ เป็น PD คำตอบได้จาก $\gamma C_Rw=\mu_{BL}$ จึงใช้ `solve` อีกครั้ง น้ำหนักเงินสดคือ $1-\sum_iw_i$ ค่าติดลบหมายถึงกู้ยืมที่อัตราปลอดความเสี่ยงเพื่อลงทุนเพิ่ม ส่วนสินทรัพย์ที่มีน้ำหนักติดลบหมายถึงขายชอร์ต สมมติฐานนี้ยังไม่รวมส่วนต่างอัตรากู้ยืม ต้นทุน หรือข้อจำกัดหลักประกัน

ในช่วงแรกกำหนด $\gamma=\delta=2.5$ เพื่อเทียบกับ prior เดิม เราจะแยกสัญลักษณ์ $\gamma$ และ $\delta$ เพราะการเปลี่ยนความเสี่ยงที่ผู้ลงทุนยอมรับกับการเปลี่ยนค่าที่ใช้สร้าง prior เป็นคนละการตัดสินใจ

#### ตรวจกรณีไม่มี Views ก่อน

เมื่อไม่มี Views, $\mu_{BL}=\Pi$ และ $M=\tau\Sigma$ ถ้าใช้ $C_R=\Sigma$ จะได้น้ำหนัก $w_0$ กลับมา แต่ถ้าใช้ predictive covariance $C_R=(1+\tau)\Sigma$ จะได้

$$
w_{\text{no views,predictive}}=\frac{w_0}{1+\tau}.
$$

```python
no_view_mean, no_view_M, no_view_predictive = bl_posterior(
    covariance, pi, np.empty((0, 3)), np.empty(0), np.empty((0, 0)), tau)
no_view_fixed_weights = np.linalg.solve(risk_aversion * covariance, no_view_mean)
no_view_predictive_weights = np.linalg.solve(risk_aversion * no_view_predictive, no_view_mean)
assert np.allclose(no_view_mean, pi)
assert np.allclose(no_view_M, tau * covariance)
assert np.allclose(no_view_fixed_weights, benchmark_weights)
assert np.allclose(no_view_predictive_weights, benchmark_weights / (1 + tau))
print("No views, fixed Sigma risky weights:", np.round(no_view_fixed_weights, 6))
print("No views, predictive risky weights:", np.round(no_view_predictive_weights, 6))
print(f"Predictive cash weight: {1 - no_view_predictive_weights.sum():.4%}")
```

`np.empty((0, 3))` สร้างเมทริกซ์ที่ไม่มีแถว Views แต่ยังมีสามคอลัมน์สินทรัพย์ ไม่ใช่การใส่ View ว่าผลตอบแทนเป็นศูนย์ ฟังก์ชันจัดการกรณีนี้โดยคืน prior และความไม่แน่นอนเดิม

กรณี fixed $\Sigma$ ได้ A/B/C เป็น 50%/30%/20% ส่วน predictive covariance ได้ประมาณ 47.6190%/28.5714%/19.0476% รวมสินทรัพย์เสี่ยง 95.2381% และเงินสด 4.7619% อัตราส่วนระหว่างสินทรัพย์เสี่ยงยังเท่าเดิม แต่จำนวนเงินที่ลงทุนในสินทรัพย์เสี่ยงลดลง เพราะโจทย์นี้คำนึงถึงความไม่แน่นอนของค่าเฉลี่ยด้วย

#### ใส่ Views แล้วแก้โจทย์เดิม

```python
fixed_sigma_weights = np.linalg.solve(risk_aversion * covariance, bl_mean)
predictive_weights = np.linalg.solve(risk_aversion * bl_predictive, bl_mean)
allocation_table = pd.DataFrame({
    "Fixed Sigma (%)": np.r_[fixed_sigma_weights, 1 - fixed_sigma_weights.sum()] * 100,
    "Predictive Sigma+M (%)": np.r_[predictive_weights, 1 - predictive_weights.sum()] * 100
}, index=assets + ["Cash"])
print(allocation_table.round(4).to_string())
```

| รายการ | ใช้ Σ คงเดิม (%) | ใช้ predictive Σ + M (%) |
|---|---:|---:|
| A | 44.7455 | 43.1351 |
| B | 35.2545 | 33.0554 |
| C | 34.1695 | 34.4473 |
| เงินสด | −14.1695 | −10.6378 |

ตัวอย่างนี้ทั้งสองกรณีต้องกู้ยืม หากผู้ลงทุนห้ามกู้ยืม คำตอบนี้ยังไม่ใช่พอร์ตที่ทำได้ตามข้อกำหนดของเขา และไม่ควรนำเฉพาะน้ำหนักสินทรัพย์เสี่ยงไปหารให้รวมหนึ่งแล้วเรียกว่าเป็นคำตอบของโจทย์ utility เดิม การเปลี่ยนขนาดพอร์ตเปลี่ยนทั้งผลตอบแทนและความเสี่ยงที่ฟังก์ชันประโยชน์กำลังชั่งน้ำหนัก

ในโค้ด `np.r_[risky_weights, cash_weight]` ต่อรายการน้ำหนักเงินสดไว้ท้ายเวกเตอร์เพื่อแสดงตารางเท่านั้น ไม่ได้ทำการปรับน้ำหนักที่แก้ได้

### โจทย์ที่สอง: Long-only และลงทุนในสามสินทรัพย์เต็มจำนวน

เพิ่มข้อจำกัด $w_i\geq0$ และ $\sum_iw_i=1$ โดยไม่มีเงินสดเป็นสินทรัพย์ในชุดนี้ เราต้องแก้โจทย์ใหม่:

$$
\max_w\;w^\mathsf{T}\mu_{BL}
-\frac{\gamma}{2}w^\mathsf{T}\Sigma_{\text{predictive}}w,
\qquad w_i\geq0,\quad\sum_iw_i=1.
$$

```python
def long_only_utility(mean, risk_cov, investor_aversion=2.5):
    mean, risk_cov = np.asarray(mean, dtype=float), np.asarray(risk_cov, dtype=float)
    if (mean.ndim != 1 or len(mean) == 0 or risk_cov.shape != (len(mean), len(mean))
            or not np.isfinite(mean).all() or not np.isfinite(risk_cov).all()
            or not np.isfinite(investor_aversion) or investor_aversion <= 0
            or not np.allclose(risk_cov, risk_cov.T, atol=1e-12)):
        raise ValueError("Need finite means, a symmetric covariance and positive risk aversion")
    np.linalg.cholesky(risk_cov)
    n = len(mean)
    result = minimize(
        lambda w: investor_aversion / 2 * (w @ risk_cov @ w) - w @ mean,
        np.full(n, 1 / n), jac=lambda w: investor_aversion * risk_cov @ w - mean,
        method="SLSQP", bounds=[(0, 1)] * n,
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1,
                     "jac": lambda w: np.ones(n)},
        options={"ftol": 1e-12, "maxiter": 500})
    if (not result.success or abs(result.x.sum() - 1) > 1e-8
            or result.x.min() < -1e-8 or result.x.max() > 1 + 1e-8):
        raise RuntimeError("Optimizer did not return a feasible solution")
    return result.x

long_only_weights = long_only_utility(bl_mean, bl_predictive, risk_aversion)
print("Fully invested, long-only weights (%):", np.round(long_only_weights * 100, 4))
print(f"Cash weight: {1 - long_only_weights.sum():.4%}")
print(f"Model expected excess return: {long_only_weights @ bl_mean:.4%}")
print(f"Predictive SD: {np.sqrt(long_only_weights @ bl_predictive @ long_only_weights):.4%}")
```

SciPy [`minimize` แบบ SLSQP](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html) หาค่าต่ำสุด เราจึงเปลี่ยนเครื่องหมายของ utility แล้วใส่เป็น objective ส่วน `jac` ให้ความชัน, `bounds` กำหนดช่วงน้ำหนัก และ `constraints` บังคับผลรวมหนึ่ง หลังจบยังตรวจสถานะโปรแกรมและความเป็นไปได้ของน้ำหนัก

ได้น้ำหนัก A/B/C ประมาณ 43.2221%/30.5768%/26.2011% ไม่มีเงินสดและไม่มีการกู้ยืม ผลตอบแทนส่วนเกินคาดหวังตามโมเดลประมาณ 4.3831% และ predictive SD ประมาณ 12.8762% ต่อปี ทั้งสองตัวเลขเป็นผลคำนวณจากสมมติฐาน ไม่ใช่ผลตอบแทนหรือความผันผวนที่ยืนยันจากข้อมูลทดสอบ

คำกล่าวว่าสินทรัพย์ที่ไม่มี Views จะมีน้ำหนักเท่า benchmark เสมอ จึงต้องระวัง ในสูตร unconstrained บางรูปสามารถแยกพอร์ตเป็นฐานอ้างอิงกับส่วนปรับตาม Views ได้ แต่เมื่อเปลี่ยนฐานความเสี่ยง ปรับขนาดให้ผลรวมหนึ่ง หรือเพิ่มข้อจำกัด น้ำหนักอื่นอาจเปลี่ยนด้วย ต้องระบุโจทย์ที่ใช้ก่อนอธิบายผล

<span id="black-litterman-risk-aversion"></span>

## เปลี่ยนความเกลียดความเสี่ยงของใคร

ถ้าเราเชื่อค่าเฉลี่ย posterior และ predictive covariance ชุดเดิม แต่เพิ่ม $\gamma$ ของผู้ลงทุนในโจทย์ที่มีเงินสด เขาจะลงทุนในสินทรัพย์เสี่ยงน้อยลง สูตร $w=(\gamma C_R)^{-1}\mu_{BL}$ ทำให้น้ำหนักสินทรัพย์เสี่ยงลดครึ่งหนึ่งเมื่อเพิ่ม $\gamma$ เป็นสองเท่า โดยยังไม่เปลี่ยน $\Pi$ หรือ Views

```python
aversion_rows = []
for investor_aversion in [1.25, 2.5, 5.0]:
    risky_weights = np.linalg.solve(investor_aversion * bl_predictive, bl_mean)
    aversion_rows.append({"Investor risk aversion": investor_aversion,
                         "Risky allocation (%)": risky_weights.sum() * 100,
                         "Cash (%)": (1 - risky_weights.sum()) * 100,
                         "Model expected excess (%)": risky_weights @ bl_mean * 100})
print(pd.DataFrame(aversion_rows).set_index("Investor risk aversion").round(4).to_string())
new_prior_pi = 5.0 * covariance @ benchmark_weights
new_prior_mean, _, _ = bl_posterior(covariance, new_prior_pi, P, Q, omega, tau)
print("Different prior calibration, posterior excess (%):", np.round(new_prior_mean * 100, 4))
```

เมื่อ $\gamma$ เท่ากับ 1.25, 2.5 และ 5 สัดส่วนสินทรัพย์เสี่ยงรวมประมาณ 221.2756%, 110.6378% และ 55.3189% ตามลำดับ ค่าแรกจึงต้องกู้ยืมมาก และอาจใช้ไม่ได้ภายใต้ข้อจำกัดจริง ความสัมพันธ์แบบหารตาม $\gamma$ นี้เป็นของโจทย์ unconstrained ที่มีเงินสด ไม่ใช่คำตอบของโจทย์ fully invested ในส่วนก่อนหน้า

ท้ายโค้ดลองอีกการเปลี่ยนหนึ่ง: สร้าง prior ใหม่ด้วย $\delta=5$ แล้วคง Views ไว้ ค่าเฉลี่ย posterior กลายเป็นประมาณ 10.8871%, 7.0881% และ 3.0057% นี่คือการเปลี่ยนข้อมูลความเชื่อตั้งต้นเอง จึงไม่เหมือนการให้ผู้ลงทุนคนใหม่ถือพอร์ตจากค่าประมาณเดิม การทดลองความไวของแบบจำลองควรบอกให้ชัดว่าคงตัวแปรใดและเปลี่ยนตัวแปรใด

<span id="black-litterman-exercises"></span>

## ลองตรวจความเข้าใจ

1. ในตัวอย่างหนึ่งมิติ ถ้าเปลี่ยน SD ของความคลาดเคลื่อน View จาก 1 เป็น 2 จุดเปอร์เซ็นต์ โดย prior ยังเหมือนเดิม ค่าเฉลี่ย posterior และ SD ของความไม่แน่นอนเป็นเท่าไร?
2. View A ชนะ B อยู่ 2 จุดเปอร์เซ็นต์เป็นการเพิ่มหรือลดส่วนต่างเมื่อเทียบกับ prior ของตัวอย่าง และทราบได้จากตัวเลขใด?
3. หากความไม่แน่นอนของค่าเฉลี่ยสินทรัพย์หนึ่งมี variance เท่ากับ 0.0004 และ conditional return variance เท่ากับ 0.01, predictive SD เท่ากับ 2% หรือไม่?
4. เพราะเหตุใดการเพิ่ม tau จึงอาจไม่เปลี่ยนค่าเฉลี่ย posterior แต่เปลี่ยนน้ำหนักที่ใช้ predictive covariance ได้?
5. ถ้าคัดลอกรายงานประมาณการฉบับเดียวกันมาเป็นสอง Views จะใช้ $\Omega$ แบบแนวทแยงและนับทั้งสองเป็นข้อมูลอิสระได้หรือไม่?
6. กรณีไม่มี Views, $\tau=0.10$, $\gamma=\delta$ และใช้ predictive covariance โดยถือเงินสดได้ สัดส่วนสินทรัพย์เสี่ยงรวมกับเงินสดเป็นเท่าไร? ถ้าข้อกำหนดเปลี่ยนเป็นลงทุนเต็มจำนวนในสินทรัพย์เสี่ยง ต้องแก้โจทย์เดิมหรือโจทย์ใหม่?

<details>
<summary>แนวคำตอบ</summary>

1. Prior และ View มี variance เท่ากัน จึงให้น้ำหนักครึ่งต่อครึ่ง ค่าเฉลี่ยเป็น 5% และ variance posterior เท่ากับ $0.02^2/2=0.0002$ จึงมี SD ประมาณ 1.4142 จุดเปอร์เซ็นต์
2. ลดส่วนต่าง เพราะ prior ให้ $\Pi_A-\Pi_B=6.3\%-3.4125\%=2.8875$ จุดเปอร์เซ็นต์ จึงมี surprise เท่ากับ −0.8875 จุดเปอร์เซ็นต์ คำว่า “ชนะ” เพียงอย่างเดียวไม่ได้บอกทิศทางการปรับจาก prior
3. ไม่ใช่ 2% ตัวเลขนั้นเป็น SD ของความไม่แน่นอนเกี่ยวกับค่าเฉลี่ย predictive SD เท่ากับ $\sqrt{0.01+0.0004}\approx10.1980\%$
4. หาก $\Omega$ เพิ่มตาม tau ด้วย ตัวคูณจะตัดกันใน gain และค่าเฉลี่ย แต่ $M$ ยังเปลี่ยน จึงเปลี่ยน covariance $\Sigma+M$ ในโจทย์เลือกพอร์ตได้ ถ้าคง $\Omega$ ไว้ ค่าเฉลี่ยก็อาจเปลี่ยนด้วย
5. ไม่ได้ถ้าเป็นข้อมูลชิ้นเดียวกันจริง การนับเป็นอิสระทำให้ความมั่นใจเพิ่มโดยไม่มีหลักฐานใหม่ ควรเก็บ View เดียว หรือสร้างโครงสร้างความคลาดเคลื่อนที่สะท้อนข้อมูลร่วมกัน โดยตรวจระบบ singular ด้วย
6. สินทรัพย์เสี่ยงรวม $1/1.10\approx90.9091\%$ และเงินสดประมาณ 9.0909% การบังคับให้ลงทุนในสินทรัพย์เสี่ยงเต็มจำนวนเพิ่มข้อจำกัดใหม่ จึงต้องแก้โจทย์ตามข้อจำกัดนั้น ไม่ควรเรียกน้ำหนักที่ normalize แล้วว่าคำตอบ utility unconstrained เดิม

</details>

<span id="black-litterman-sources"></span>

## แหล่งที่มาและขอบเขต

อ่าน Transcript ภาษาอังกฤษเต็มของ [Black-Litterman Analysis](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/Vgyoc/black-litterman-analysis) และ [Module 3 Lab Session — Black Litterman](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/RWEZL/module-3-lab-session-black-litterman) เมื่อ 3 ตุลาคม 2026 และตรวจ `lab_23.ipynb` ผ่าน [Coursera Labs and code](https://www.coursera.org/learn/advanced-portfolio-construction-python/ungradedLab/RqxtJ/labs-and-code) แบบอ่านอย่างเดียว โดยเฉพาะเซลล์ In[4]–In[6] สำหรับ implied returns, default Omega และ posterior; In[8] กับ In[22]–In[23] สำหรับการปรับสเกลน้ำหนักและฐาน $w_0/(1+\tau)$ ไม่ได้รันหรือแจกจ่าย Notebook ของคอร์ส

สูตร prior และ posterior ตรวจประกอบกับ [He และ Litterman, *The Intuition Behind Black-Litterman Model Portfolios*, December 1999, Appendix B](https://people.duke.edu/~charvey/Teaching/BA453_2002/GS_The_intuition_behind.pdf) และ [Idzorek, *A Step-by-Step Guide to the Black-Litterman Model*, ฉบับ July 2004, Section 2](https://www.cis.upenn.edu/~mkearns/finread/idzorek.pdf) ซึ่งเป็นสำเนางานผู้เขียนที่โฮสต์ในเว็บไซต์มหาวิทยาลัย [เอกสาร PyPortfolioOpt](https://pyportfolioopt.readthedocs.io/en/stable/BlackLitterman.html) แสดงสูตร predictive covariance $\Sigma+M$ เช่นกัน บทนี้เขียนสูตรและฟังก์ชันด้วย NumPy เอง ไม่ต้องติดตั้ง PyPortfolioOpt

โค้ด Lab เรียกเมทริกซ์ที่คืนว่า `sigma_bl` และคำนวณเป็น $\Sigma+M$ บทนี้จึงแยกชื่อความไม่แน่นอนของค่าเฉลี่ยออกจากความเสี่ยง predictive อย่างชัดเจน ส่วนค่า tau, covariance, Views และความคลาดเคลื่อนทั้งหมดเป็นข้อกำหนดสำหรับสอน ไม่ใช่ค่าที่สอบเทียบกับตลาดหรือความสามารถพยากรณ์จริง การใช้ข้อมูลจริงต้องตรวจหน่วย ช่วงเวลา ลำดับสินทรัพย์ แหล่งข้อมูลร่วมกันของ Views และผลนอกช่วงที่ใช้เลือกพารามิเตอร์
