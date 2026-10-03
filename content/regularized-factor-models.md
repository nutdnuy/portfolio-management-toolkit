---
title: "Ridge, Lasso และ Elastic Net: ลดความแกว่งของ Factor Loadings"
description: "คำนวณ penalty จากตัวอย่างเล็ก อ่าน objective ของ scikit-learn และปรับสเกลปัจจัยโดยรักษาหน่วยของ loading"
---

# Ridge, Lasso และ Elastic Net: ลดความแกว่งของ Factor Loadings

<p class="lead">ในตัวอย่าง <a href="factor-model-estimation.html#unstable-factor-loadings">Factor Model Estimation</a> การเปลี่ยนผลตอบแทนกองทุนเพียง 0.001 จุดเปอร์เซ็นต์ทำให้ loading ของปัจจัยที่เกือบซ้ำกันเปลี่ยนจาก <code>[0.8, 0]</code> เป็น <code>[-0.2, 1]</code> การใช้สมการที่มี residual ต่ำที่สุดเพียงอย่างเดียวจึงอาจให้ loading ที่ไวต่อข้อมูล</p>

[Regularization](glossary.html#regularization) เพิ่มต้นทุนให้กับขนาด coefficient ระหว่างฝึกโมเดล เราต้องยอมให้ fit ข้อมูลฝึกคลาดเคลื่อนมากขึ้นได้ เพื่อแลกกับค่าประมาณที่อาจเปลี่ยนน้อยลงเมื่อข้อมูลเปลี่ยน ผลกับข้อมูลใหม่ต้องทดสอบแยก ไม่ได้ดีขึ้นเสมอจากการเพิ่ม penalty

บทนี้ใช้ข้อมูลสมมติที่คำนวณคำตอบด้วยมือได้ก่อน แล้วจึงลองข้อมูลปัจจัยที่สัมพันธ์กัน ส่วนการเลือกความแรงของ penalty ด้วยข้อมูลตามลำดับเวลาจะอยู่ใน [Factor Model Validation](factor-model-validation.html)

<span id="penalty-small-example"></span>

## สร้างตัวอย่างที่ตรวจคำตอบได้

สมการของเราคือ $y=a+Z\theta+e$ โดยแต่ละคอลัมน์ของ $Z$ ถูกปรับสเกลแล้วให้ค่าเฉลี่ยศูนย์และ SD เท่ากับหนึ่ง ส่วน $y$ ยังเป็นผลตอบแทนทศนิยมต่อเดือน ดังนั้น coefficient $\theta_j=0.02$ หมายถึง y สัมพันธ์กับการเพิ่ม 2 จุดเปอร์เซ็นต์เมื่อปัจจัยที่ปรับสเกลแล้วเพิ่มหนึ่งหน่วย หรือหนึ่ง SD ของปัจจัยเดิม

ตัวอย่างทั้งหน้ารันต่อกันได้ด้วย NumPy, pandas และ scikit-learn 1.6.1 ส่วน `combinations` เป็นเครื่องมือใน Python มาตรฐานสำหรับแจกแจงชุดย่อย

```python
import numpy as np
import pandas as pd
from itertools import combinations
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

np.set_printoptions(precision=6, suppress=True)
```

`Ridge`, `Lasso` และ `ElasticNet` เป็นคลาสของตัวประมาณ ซึ่งใช้ `.fit` และ `.predict` ในรูปแบบเดียวกับ `LinearRegression` ส่วน `StandardScaler` ใช้ปรับสเกล และ `make_pipeline` ใช้เชื่อมขั้นตอนปรับสเกลกับขั้นตอนประมาณสมการ

```python
penalty_Z = np.array([
    [-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1],
    [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1],
], dtype=float)
penalty_noise = 0.001 * penalty_Z[:, 0] * penalty_Z[:, 1]
penalty_y = 0.002 + penalty_Z @ np.array([0.020, 0.007, 0.0]) + penalty_noise
penalty_n = len(penalty_y)
penalty_ols = LinearRegression().fit(penalty_Z, penalty_y)
print("Column means:", penalty_Z.mean(axis=0))
print("Column SDs:", penalty_Z.std(axis=0, ddof=0))
print("Z.T @ Z / n:")
print(penalty_Z.T @ penalty_Z / penalty_n)
print("OLS coefficients:", penalty_ols.coef_)
```

เราสร้างข้อมูลแปดแถว สามปัจจัย แต่ละค่าใน Z เป็น −1 หรือ +1 โดยจัดให้คอลัมน์ตั้งฉากกัน ผล `Z.T @ Z / n` จึงเป็น identity matrix ซึ่งมีหนึ่งบนแนวทแยงและศูนย์ตำแหน่งอื่น `[:, 0]` เลือกทุกแถวของคอลัมน์แรก และ `len` นับจำนวนแถวของ y

OLS ได้ coefficient ประมาณ `[0.020, 0.007, 0]` และ intercept 0.002 ตัวเลขศูนย์อาจพิมพ์เป็น `-0.0` จากการคำนวณทศนิยมในเครื่อง เรารู้คำตอบเพราะสร้าง residual ให้ตั้งฉากกับ Z ไว้แล้ว เงื่อนไขพิเศษนี้จะช่วยให้ตรวจสูตรของแต่ละวิธีได้

<span id="l1-l2-objectives"></span>

## Penalty ลงโทษอะไร

เริ่มจาก coefficient `[0.020, 0.007, 0]` และแยกปริมาณสามอย่างที่มักสับสนกัน

```python
penalty_theta = np.array([0.020, 0.007, 0.0])
print(f"L1: {np.abs(penalty_theta).sum():.6f}")
print(f"Squared L2: {(penalty_theta ** 2).sum():.6f}")
print("Nonzero count:", np.count_nonzero(penalty_theta))
```

| ปริมาณ | วิธีคำนวณ | ค่าของตัวอย่าง |
|---|---|---:|
| L1 | บวกค่าสัมบูรณ์ของทุก coefficient | 0.027 |
| Squared L2 | บวกกำลังสองของทุก coefficient | 0.000449 |
| จำนวน nonzero | นับ coefficient ที่ไม่เท่ากับศูนย์ | 2 |

Lasso ใช้ L1 ไม่ได้ลงโทษจำนวน nonzero โดยตรง แม้ผลลัพธ์มักมี coefficient บางตัวเป็นศูนย์ ส่วน Ridge ใช้ squared L2 ไม่ใช่รากที่สองของผลรวมกำลังสอง การเปลี่ยน penalty ทำให้ได้ปัญหาคนละแบบ

เราจะเขียน Ridge ใน convention ต่อไปนี้ โดยไม่ลงโทษ intercept:

$$
\min_{a,\theta}\frac{1}{2n}\sum_t(y_t-a-Z_t^\mathsf T\theta)^2
+\frac{\lambda}{2}\sum_j\theta_j^2.
$$

สำหรับ Lasso ใช้

$$
\min_{a,\theta}\frac{1}{2n}\sum_t(y_t-a-Z_t^\mathsf T\theta)^2
+\lambda\sum_j|\theta_j|.
$$

$\lambda\geq0$ ควบคุมความแรงของ penalty หากเป็นศูนย์ ปัญหาจะกลับไปเป็น OLS หากเพิ่มขึ้น โมเดลยอมเสียความแม่นในการ fit เพื่อจำกัด coefficient มากขึ้น ค่า $\lambda$ เป็น [hyperparameter](glossary.html#hyperparameter) ที่เราเลือกวิธีตั้งค่าก่อนฝึกแต่ละครั้ง ต่างจาก coefficient ที่โปรแกรมประมาณจากข้อมูลภายใต้ค่าที่เลือกนั้น

ชื่อ `alpha` ใน scikit-learn หมายถึงความแรงของ penalty ของคลาสเหล่านี้ ไม่ใช่ alpha ของผลตอบแทนกองทุน การอ่านโค้ดจึงต้องดูว่าตัวเลขอยู่ใน `model.alpha` หรือ `model.intercept_`

<span id="ridge-hand-calculation"></span>

## Ridge และการหาร Coefficient ลง

ในข้อมูลพิเศษของเราที่ $Z^\mathsf TZ/n=I$ และคอลัมน์มีค่าเฉลี่ยศูนย์ คำตอบของ Ridge คือ

$$
\hat\theta_j^{\text{Ridge}}=\frac{\hat\theta_j^{\text{OLS}}}{1+\lambda}.
$$

เมื่อ $\lambda=0.5$ coefficient ตัวแรกจึงเป็น $0.020/1.5=0.013333$ และตัวที่สองเป็น $0.007/1.5=0.004667$

```python
ridge_lambda = 0.5
penalty_ridge = Ridge(alpha=penalty_n * ridge_lambda).fit(penalty_Z, penalty_y)
ridge_by_hand = penalty_ols.coef_ / (1 + ridge_lambda)
print("Ridge coefficients:", penalty_ridge.coef_)
print("Orthogonal formula:", ridge_by_hand)
print(f"Intercept: {penalty_ridge.intercept_:.6f}")
```

ต้องส่ง `alpha=n * lambda` ให้ `Ridge` เพราะไลบรารีเขียน objective เป็น SSE + `alpha` × squared L2 โดยไม่มีตัวหาร $2n$ การคูณ objective ในสูตรของเราด้วย $2n$ ทำให้ penalty กลายเป็น $n\lambda\sum_j\theta_j^2$ จึงเห็นตัวคูณ n ในโค้ด

การเปรียบเทียบ penalty ระหว่างโปรแกรมหรือบทความควรตรวจตัวหารหน้าค่า loss ด้วย ไม่ควรเปรียบเทียบตัวเลข `alpha` ตรง ๆ เพียงเพราะใช้ชื่อเหมือนกัน

สูตรหารทีละ coefficient นี้ใช้ได้เพราะเราเลือกคอลัมน์ตั้งฉากกัน สำหรับปัจจัยที่สัมพันธ์กัน Ridge ทำงานร่วมกันทั้งเวกเตอร์ coefficient และไม่รับประกันว่า coefficient ทุกตัวจะลดค่าสัมบูรณ์อย่างเป็นลำดับ เมื่อเพิ่ม penalty อย่างไรก็ดี Ridge ไม่มีกลไกตั้ง coefficient เป็นศูนย์แบบ Lasso โดยทั่วไป

<span id="lasso-soft-threshold"></span>

## Lasso และการตัด Coefficient เล็กให้เป็นศูนย์

ภายใต้เงื่อนไขตั้งฉากเดียวกัน คำตอบของ Lasso ใช้ **soft threshold**:

$$
\hat\theta_j^{\text{Lasso}}
=\operatorname{sign}(\hat\theta_j^{\text{OLS}})
\max(|\hat\theta_j^{\text{OLS}}|-\lambda,0).
$$

เริ่มจากขนาด coefficient แล้วลบ $\lambda$ ถ้าเหลือติดลบให้เปลี่ยนเป็นศูนย์ ถ้ายังเหลือบวกให้นำเครื่องหมายเดิมกลับมา สำหรับ $\lambda=0.005$ ได้ `[0.015, 0.002, 0]`

```python
lasso_lambda = 0.005
penalty_lasso = Lasso(alpha=lasso_lambda, tol=1e-12, max_iter=100000).fit(penalty_Z, penalty_y)
lasso_by_hand = np.sign(penalty_ols.coef_) * np.maximum(np.abs(penalty_ols.coef_) - lasso_lambda, 0)
print("Lasso coefficients:", penalty_lasso.coef_)
print("Soft-threshold formula:", lasso_by_hand)
```

`np.abs` หาค่าสัมบูรณ์, `np.maximum(..., 0)` เลือกค่าที่มากกว่าระหว่างแต่ละสมาชิกกับศูนย์ และ `np.sign` คืนเครื่องหมายบวก ลบ หรือศูนย์ เราใช้สูตรนี้ตรวจ `.fit` ได้เพราะ Z ของตัวอย่างตั้งฉากกัน ไม่ใช่สูตรสำเร็จที่นำไปใช้ทีละคอลัมน์กับข้อมูลสัมพันธ์กันทั่วไป

`Lasso(alpha=...)` ใช้ objective ที่หารด้วย $2n$ เหมือนสูตรที่เราเขียน จึงส่งค่า $\lambda$ ได้ตรง ๆ `max_iter` จำกัดจำนวนรอบที่โปรแกรมแก้ปัญหา ส่วน `tol` กำหนดเกณฑ์ความแม่นทางตัวเลข การเพิ่มจำนวนรอบไม่ได้เพิ่มข้อมูลหรือทำให้โมเดลเหมาะกับตลาดมากขึ้น หากโปรแกรมเตือนว่าไม่ลู่เข้า ควรตรวจสเกล ค่าตั้ง และการลู่เข้าก่อนอ่าน coefficient

ปัจจัยที่ถูกตั้งเป็นศูนย์หมายถึงถูกตัดออกภายใต้ชุดข้อมูล penalty และปัจจัยอื่นที่ให้มา ไม่ได้พิสูจน์ว่าปัจจัยนั้นไม่มีบทบาททางเศรษฐศาสตร์ ถ้ามีตัวแทนที่เกือบซ้ำกัน Lasso อาจเลือกตัวหนึ่งและตัดอีกตัว ทั้งที่ข้อมูลยังแยกบทบาทสองตัวไม่ได้ชัด

<span id="elastic-net-mixture"></span>

## Elastic Net รวม Penalty สองแบบ

Elastic Net ใน scikit-learn ใช้

$$
\frac{1}{2n}\|y-a-Z\theta\|_2^2
+\lambda\rho\|\theta\|_1
+\frac{\lambda(1-\rho)}{2}\|\theta\|_2^2.
$$

$\lambda$ ควบคุมระดับ penalty โดยรวม ส่วน $\rho$ หรือ `l1_ratio` ควบคุมส่วนผสม ถ้า $\rho=1$ จะเหลือ Lasso ถ้าอยู่ระหว่างศูนย์กับหนึ่ง จะมีทั้ง L1 และ squared L2 หากต้องการ Ridge ล้วน ใช้คลาส `Ridge` โดยแปลง convention ของ penalty ให้ตรงจะชัดเจนกว่า

สำหรับ Z ที่ตั้งฉาก คำตอบคือ soft threshold ด้วย $\lambda\rho$ แล้วหารด้วย $1+\lambda(1-\rho)$

```python
elastic_lambda = 0.005
elastic_ratio = 0.5
penalty_elastic = ElasticNet(alpha=elastic_lambda, l1_ratio=elastic_ratio, tol=1e-12, max_iter=100000).fit(penalty_Z, penalty_y)
elastic_by_hand = (
    np.sign(penalty_ols.coef_)
    * np.maximum(np.abs(penalty_ols.coef_) - elastic_lambda * elastic_ratio, 0)
    / (1 + elastic_lambda * (1 - elastic_ratio))
)
print("Elastic Net coefficients:", penalty_elastic.coef_)
print("Orthogonal formula:", elastic_by_hand)
```

เมื่อใช้ $\lambda=0.005$ และ $\rho=0.5$ ได้ coefficient ประมาณ `[0.017456, 0.004489, 0]` ส่วน L2 ช่วยให้การแบ่ง coefficient ระหว่างตัวแปรที่สัมพันธ์กันมีต้นทุน และส่วน L1 ยังทำให้บาง coefficient เป็นศูนย์ได้ ผลไม่ได้รับประกันว่าจะค้นพบปัจจัยจริงครบหรือเลือกตัวเดียวกันทุกช่วงเวลา

ลองเปลี่ยนความแรงหลายค่าเพื่อดู coefficient path ในตัวอย่างที่รู้คำตอบ

```python
ridge_path = []
for strength in [0, 0.1, 0.5, 1, 3, 9]:
    model = LinearRegression() if strength == 0 else Ridge(alpha=penalty_n * strength)
    model.fit(penalty_Z, penalty_y)
    ridge_path.append([strength, *model.coef_])
lasso_path = []
for strength in [0, 0.003, 0.005, 0.01, 0.02, 0.03]:
    model = LinearRegression() if strength == 0 else Lasso(alpha=strength, tol=1e-12, max_iter=100000)
    model.fit(penalty_Z, penalty_y)
    lasso_path.append([strength, *model.coef_])
ridge_path = pd.DataFrame(ridge_path, columns=["lambda", "F1", "F2", "F3"])
lasso_path = pd.DataFrame(lasso_path, columns=["lambda", "F1", "F2", "F3"])
print("Ridge path:")
print(ridge_path.round(6).to_string(index=False))
print("Lasso path:")
print(lasso_path.round(6).to_string(index=False))
```

`for` ทำงานซ้ำทีละค่าจากรายการ `append` เพิ่มหนึ่งแถวเข้า list และ `*model.coef_` กระจาย coefficient สามตัวเป็นสามช่องของแถว ตอน $\lambda=0$ เราใช้ `LinearRegression` โดยตรงตามคำแนะนำของไลบรารี

Ridge ที่ $\lambda=1$ ลด coefficient สองตัวเหลือครึ่งหนึ่ง ส่วน Lasso ที่ $\lambda=0.01$ ให้ coefficient ตัวที่สองเป็นศูนย์แล้ว แกน $\lambda$ ของสองวิธีมีคนละความหมายและสเกลตาม objective จึงไม่ควรตีความว่าเลขเดียวกันคือความแรงที่เท่าเทียมกัน

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/ml-factor-ridge-mobile.svg">
<img src="assets/charts/ml-factor-ridge.svg" alt="Ridge ลดขนาด coefficient ของ F1 และ F2 ในตัวอย่างตั้งฉากกัน เมื่อเพิ่ม penalty" loading="lazy" width="720" height="560">
</picture>
<figcaption>ค่าจากโค้ดด้านบน แกนตั้งคูณ coefficient ด้วย 100 เพื่ออ่านเป็นจุดเปอร์เซ็นต์ต่อเดือน ต่อ feature มาตรฐานหนึ่งหน่วย เส้นเชื่อมค่าที่ทดลอง ไม่ใช่ข้อมูลตลาด</figcaption>
</figure>

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/ml-factor-lasso-mobile.svg">
<img src="assets/charts/ml-factor-lasso.svg" alt="Lasso ทำให้ coefficient ของ F2 เป็นศูนย์ก่อน F1 ในตัวอย่างตั้งฉากกัน" loading="lazy" width="720" height="560">
</picture>
<figcaption>Lasso ใช้สเกลของ penalty ต่างจาก Ridge ในภาพก่อนหน้า F2 เป็นศูนย์เมื่อ λ ถึง 0.007 และ F1 เป็นศูนย์เมื่อ λ ถึง 0.020 ตามสูตร soft threshold; จุดบนกราฟแสดงค่าที่โค้ดเลือกทดลอง</figcaption>
</figure>

<span id="standardize-factor-penalties"></span>

## ปรับสเกลก่อน แล้วแปลง Loading กลับ

หากปัจจัยหนึ่งเก็บเป็นเปอร์เซ็นต์ อีกตัวเก็บเป็นทศนิยม ขนาด coefficient ที่ต้องใช้จะต่างกันถึง 100 เท่า แม้สมการอธิบายผลตอบแทนเท่าเดิม การลงโทษขนาดดิบจึงไวต่อหน่วยที่เลือก

StandardScaler เปลี่ยนปัจจัย $F_j$ เป็น

$$
Z_j=\frac{F_j-\bar F_j}{s_j}.
$$

มันคำนวณค่าเฉลี่ยและ SD จากข้อมูลที่ส่งเข้า `.fit` แล้วเก็บไว้สำหรับแปลงแถวใหม่ โดยใช้ SD แบบ `ddof=0` ค่า $s_j$ ไม่ใช่ค่าประมาณที่ควรคำนวณใหม่จากชุดทดสอบ ในบทถัดไปขั้นตอนนี้จะอยู่ภายในแต่ละ training fold

เราสร้างปัจจัยสมมติหกตัวจำนวน 60 แถว โดย Equity proxy เกือบเหมือน Equity และ Rates mirror เกือบตรงข้ามกับ Rates ปัจจัยเหล่านี้มีความหมายเพียงตามสูตรจำลอง ไม่ใช่ดัชนีตลาดจริง การสร้างเลข Normal ในที่นี้ใช้ทดลองการประมาณสมการ ไม่ได้สร้างเส้นทางราคาหรือยืนยันว่าผลตอบแทนตลาดแจกแจงเช่นนั้น

```python
scale_rng = np.random.default_rng(20261003)
scale_latent = scale_rng.normal(size=(60, 6))
scale_X = pd.DataFrame({
    "Equity": 0.004 + 0.04 * scale_latent[:, 0],
    "Equity proxy": 0.004 + 0.04 * (scale_latent[:, 0] + 0.08 * scale_latent[:, 1]),
    "Rates": 0.001 + 0.02 * scale_latent[:, 2],
    "Rates mirror": -0.001 + 0.02 * (-scale_latent[:, 2] + 0.08 * scale_latent[:, 3]),
    "FX": 0.02 * scale_latent[:, 4],
    "Noise proxy": 0.03 * scale_latent[:, 5],
})
scale_y = 0.001 + scale_X.to_numpy() @ np.array([0.7, 0, -0.25, 0, 0.1, 0]) + scale_rng.normal(0, 0.012, 60)
scale_model = make_pipeline(StandardScaler(), Lasso(alpha=0.001, tol=1e-10, max_iter=100000))
scale_model.fit(scale_X, scale_y)
scale_scaler = scale_model.named_steps["standardscaler"]
scale_fit = scale_model.named_steps["lasso"]
scale_beta = scale_fit.coef_ / scale_scaler.scale_
scale_alpha = scale_fit.intercept_ - scale_scaler.mean_ @ scale_beta
print(pd.DataFrame({"Standardized coefficient": scale_fit.coef_, "Original-unit loading": scale_beta}, index=scale_X.columns).round(6))
print(f"Original-unit monthly intercept: {scale_alpha:.6f}")
```

`default_rng(20261003)` กำหนด seed ให้สร้างข้อมูลซ้ำได้ `.normal(size=(60, 6))` สร้างอาร์เรย์ 60 แถวหกคอลัมน์ ส่วน `@` รวมปัจจัยตาม loading ที่ใช้สร้างกองทุน จากนั้น Pipeline ทำ `StandardScaler` ก่อน `Lasso` โดยอัตโนมัติ

coefficient ในคอลัมน์ `Standardized coefficient` อ้างอิงการเพิ่มหนึ่ง SD ของปัจจัย การแปลงกลับใช้

$$
\beta_j=\frac{\theta_j}{s_j},\qquad
a=a_Z-\sum_j\beta_j\bar F_j.
$$

จึงต้องปรับ intercept ด้วย ไม่ใช่หาร coefficient อย่างเดียว ในข้อมูลชุดนี้ Lasso แบ่ง loading ระหว่าง Equity และ Equity proxy และใช้ Rates mirror แทน Rates บางส่วน ผลยังต่างจาก loading ที่ใช้สร้างข้อมูล จึงไม่ควรอ่านรายชื่อ nonzero เป็นการค้นพบเหตุและผล

ลองเปลี่ยนหน่วย Equity เป็นเปอร์เซ็นต์ โดยคง y และปัจจัยอื่นไว้ แล้ว fit ซ้ำ

```python
scale_changed = scale_X.copy()
scale_changed["Equity"] *= 100
scale_changed_model = make_pipeline(StandardScaler(), Lasso(alpha=0.001, tol=1e-10, max_iter=100000))
scale_changed_model.fit(scale_changed, scale_y)
scale_prediction_error = np.max(np.abs(scale_changed_model.predict(scale_changed) - scale_model.predict(scale_X)))
raw_model = Lasso(alpha=0.00002, tol=1e-10, max_iter=100000).fit(scale_X, scale_y)
raw_changed_model = Lasso(alpha=0.00002, tol=1e-10, max_iter=100000).fit(scale_changed, scale_y)
raw_prediction_error = np.max(np.abs(raw_model.predict(scale_X) - raw_changed_model.predict(scale_changed)))
print("Scaled-model predictions unchanged:", scale_prediction_error < 1e-10)
print(f"Largest unscaled-model change: {100 * raw_prediction_error:.6f} percentage points")
```

โมเดลที่ปรับสเกลให้ fitted returns ตรงกับเดิมภายในความคลาดเคลื่อนของคอมพิวเตอร์ ส่วนโมเดล Lasso ที่ไม่ปรับสเกลและใช้ `alpha` เท่าเดิมให้ fitted returns ต่างได้ประมาณ 0.387580 จุดเปอร์เซ็นต์ในแถวที่ต่างที่สุด ตัวเลขนี้เป็นผลจากข้อมูลจำลองชุดนี้ แสดงผลของการเปลี่ยนหน่วย ไม่ใช่การวัด performance นอกชุดฝึก

การปรับสเกลช่วยจัดการหน่วย แต่ไม่ได้กำจัด multicollinearity และไม่ได้ทำให้ข้อมูลที่มี outlier กลายเป็นข้อมูลปกติ

<span id="shrinkage-bias-variance"></span>

## ลด Variance ได้ แต่เพิ่ม Bias

สมมติเรามีตัวประมาณ $\hat\theta$ ที่ไม่มี bias และมี standard error $s$ แล้วเลือกย่อค่าประมาณลงด้วยตัวคูณ $c$ ซึ่งอยู่ระหว่างศูนย์กับหนึ่ง:

$$
\tilde\theta=c\hat\theta.
$$

หากค่าจริงคือ $\theta$ จะได้ bias เท่ากับ $(c-1)\theta$ และ variance เท่ากับ $c^2s^2$ ดังนั้น

$$
\operatorname{MSE}(\tilde\theta)
=(1-c)^2\theta^2+c^2s^2.
$$

ลองให้ standard error เท่ากับ 0.01 และย่อค่าประมาณเหลือครึ่งหนึ่ง คำนวณ expected MSE ได้โดยไม่ต้องสุ่มจำลอง

```python
shrink_truth = np.array([0.0, 0.003, 0.03])
shrink_se = 0.01
shrink_amount = 0.5
shrink_risk = pd.DataFrame({
    "True parameter": shrink_truth,
    "Unshrunk MSE": np.full(3, shrink_se ** 2),
    "Half-shrunk MSE": (1 - shrink_amount) ** 2 * shrink_truth ** 2 + shrink_amount ** 2 * shrink_se ** 2,
})
print(shrink_risk.to_string(index=False, float_format=lambda value: f"{value:.8f}"))
```

เมื่อค่าจริงเท่ากับศูนย์ MSE ลดจาก 0.0001 เหลือ 0.000025 แต่เมื่อค่าจริงเป็น 0.03 กลับเพิ่มเป็น 0.00025 เพราะ bias ที่เพิ่มมีขนาดใหญ่กว่าประโยชน์จาก variance ที่ลด นี่จึงเป็นเหตุให้ต้องเลือก penalty จากข้อมูลฝึกและ validation แทนการตั้งให้แรงที่สุด

ผล James–Stein ที่กล่าวถึงในคอร์สให้เหตุผลว่าการยอมมี bias อาจลดความคลาดเคลื่อนรวมได้ สำหรับกรณีพื้นฐานที่ข้อมูลแต่ละมิติเป็น Normal อิสระกัน มี variance เท่ากันที่ทราบค่า และ shrink เวกเตอร์ค่าประมาณเข้าหาจุดตั้งต้นคงที่ ผลดังกล่าวเกี่ยวกับอย่างน้อยสามมิติและ expected squared-error รวมทั้งเวกเตอร์ ไม่ใช่ข้อพิสูจน์ว่า Lasso หรือ Ridge จะชนะ OLS กับผลตอบแทนทุกชุด หรือว่าทุก coefficient ต้องแม่นขึ้นแยกกัน

<span id="small-best-subset"></span>

## เลือกไม่เกินสองปัจจัยด้วย Best Subset

อีกวิธีคือกำหนดจำนวนปัจจัยที่ยอมให้ใช้ แล้วลองทุกชุดที่เป็นไปได้ ตัวอย่างสามปัจจัยของเรามีชุดที่เลือกได้ไม่เกินสองตัวรวมเจ็ดชุด: ชุดว่างหนึ่งชุด, ชุดตัวเดียวสามชุด และชุดสองตัวสามชุด

```python
subset_rows = []
for size in range(3):
    for columns in combinations(range(3), size):
        if size == 0:
            fitted = np.full(penalty_n, penalty_y.mean())
        else:
            model = LinearRegression().fit(penalty_Z[:, columns], penalty_y)
            fitted = model.predict(penalty_Z[:, columns])
        subset_rows.append({"Columns": columns, "Training MSE": np.mean((penalty_y - fitted) ** 2)})
subset_table = pd.DataFrame(subset_rows).sort_values("Training MSE")
print("Candidate subsets:", len(subset_table))
print("Best subset:", subset_table.iloc[0]["Columns"])
print(f"Best training MSE: {subset_table.iloc[0]['Training MSE']:.8f}")
```

`combinations(range(3), size)` แจกแจงตำแหน่งคอลัมน์ที่ไม่ซ้ำกัน เช่น `(0, 1)` หมายถึงปัจจัยที่หนึ่งกับสอง ถ้าเลือกชุดว่าง โมเดลมีเพียงค่าเฉลี่ย y เป็น intercept หากมีคอลัมน์ เราทำ OLS ของชุดนั้นแล้ววัด training MSE

ได้ชุด `(0, 1)` และ training MSE 0.000001 การคัดด้วย training loss ภายใต้เพดานสองตัวนี้ยังไม่ได้เลือกเพดานที่เหมาะกับข้อมูลใหม่ หากต้องเลือกระหว่างหนึ่ง สอง หรือสามตัว ต้องประเมินการเลือกชุดภายใน training folds และใช้ validation เลือกเพดาน เช่นเดียวกับการเลือก penalty

วิธีไล่ทุกชุดใช้ได้กับตัวอย่างเล็ก แต่จำนวนชุดโตเร็วตามจำนวนปัจจัย ปัญหา best subset ที่ใส่ตัวแปรเลือกแบบศูนย์หรือหนึ่งเป็นปัญหาเชิงจัดหมู่ การเขียนด้วยไลบรารี optimization ไม่ได้ทำให้ทั้งปัญหากลายเป็น convex โดยอัตโนมัติ ตัวอย่างนี้จึงใช้ Python มาตรฐานไล่ชุดเล็ก ๆ และไม่ต้องติดตั้ง mixed-integer solver

<span id="regularization-practice"></span>

## แบบฝึกหัด

<details><summary>1. สำหรับ coefficient [−0.02, 0.01] ค่า L1 และ squared L2 เท่าไร</summary>

L1 เท่ากับ $0.02+0.01=0.03$ และ squared L2 เท่ากับ $0.02^2+0.01^2=0.0005$ ทั้งสองต่างจากจำนวน nonzero ซึ่งเท่ากับ 2

</details>

<details><summary>2. ถ้า n = 40 และใช้สูตร Ridge ที่มี λ = 0.2 ตามบทนี้ ต้องส่ง alpha ให้ scikit-learn เท่าไร</summary>

ส่ง $40(0.2)=8$ เพราะ `Ridge` ใช้ SSE ที่ไม่ได้หารด้วย $2n$

</details>

<details><summary>3. ในกรณีคอลัมน์ตั้งฉาก coefficient OLS = −0.008 และ Lasso λ = 0.003 คำตอบเท่าไร</summary>

ขนาดเหลือ $0.008-0.003=0.005$ แล้วคืนเครื่องหมายลบ จึงได้ −0.005

</details>

<details><summary>4. ถ้า coefficient OLS = 0.004 และ Lasso λ = 0.005 ในกรณีเดียวกันจะเหลือเท่าไร</summary>

เหลือศูนย์ เพราะ $\max(0.004-0.005,0)=0$

</details>

<details><summary>5. Standardized coefficient = 0.012 และ SD ของปัจจัยเดิม = 0.03 loading เดิมเท่าไร</summary>

$0.012/0.03=0.4$ ถ้าต้องแปลงทั้งสมการ ยังต้องปรับ intercept ด้วยค่าเฉลี่ยของทุกปัจจัย

</details>

<details><summary>6. Lasso ให้ loading ปัจจัยหนึ่งเป็นศูนย์ สรุปได้หรือไม่ว่าปัจจัยนั้นไม่มีผลทางเศรษฐศาสตร์</summary>

สรุปไม่ได้ ผลขึ้นกับชุดข้อมูล สเกล penalty และปัจจัยอื่นที่ใช้ หากปัจจัยอื่นทำหน้าที่เป็นตัวแทนที่ใกล้กัน Lasso อาจเลือกแทนกันได้

</details>

<details><summary>7. การเพิ่ม penalty ทำให้ training error ต่ำลงเสมอหรือไม่</summary>

ไม่ใช่ เป้าหมายที่ลดคือ training loss บวก penalty และ OLS ให้ SSE ต่ำที่สุดอยู่แล้วในกลุ่มสมการเชิงเส้นเดียวกัน การยอมให้ training loss เพิ่มเป็นส่วนหนึ่งของวิธีนี้ ส่วนผลต่อ validation error ต้องวัดจริง

</details>

<details><summary>8. ถ้าเลือกชุดปัจจัยหลังดู final test แล้ว คะแนน test ยังเป็นการประเมินที่กันไว้หรือไม่</summary>

ไม่เป็นแล้ว เพราะ test มีส่วนในการเลือกโมเดล ต้องใช้ validation ภายใน development data เลือกตัวแปรหรือ hyperparameter และกันข้อมูลอีกช่วงไว้ประเมินขั้นสุดท้าย

</details>

<span id="regularization-sources"></span>

## แหล่งอ่านและ Convention ของโค้ด

อ่าน Transcript ฉบับเต็มของ [Penalty Methods](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/xvqVH/penalty-methods), [Setting Factor Loadings](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/0Qh5m/setting-factor-loadings-and-examples), [Shrinkage Concepts](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/uLWa0/shrinkage-concepts) และ [Factor Models Lab](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/zxZH1/lab-session-jupiter-notebook-on-factor-models) พร้อม [รายการอ้างอิงของคอร์ส](https://www.coursera.org/learn/python-machine-learning-for-investment-management/supplement/MjrVV/references-for-module-2-machine-learning-techniques-for-robust-estimation-of) ตรวจเมื่อ 3 ตุลาคม 2026

สูตรที่ใช้ตรวจ implementation อ้างอิงเอกสาร [Ridge](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.Ridge.html), [Lasso](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.Lasso.html), [ElasticNet](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.ElasticNet.html) และ [StandardScaler](https://scikit-learn.org/1.6/modules/generated/sklearn.preprocessing.StandardScaler.html) จึงระบุ squared L2 และตัวหารของ loss แยกกันชัดเจน สำหรับขอบเขตการ shrink เวกเตอร์ค่าเฉลี่ย ดูงานของ Morris และ Lysy เรื่อง [Shrinkage Estimation in Multilevel Normal Models](https://arxiv.org/abs/1203.5610)

โค้ดและข้อมูลทั้งหมดเขียนใหม่ ไม่ใช้ฟังก์ชันของผู้สอน ไม่มีการอ้างว่าชุดปัจจัยจำลองเป็น factor portfolio ที่ซื้อขายได้จริง
