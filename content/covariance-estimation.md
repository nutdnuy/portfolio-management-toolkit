---
title: ประมาณ Covariance เมื่อข้อมูลมีจำกัด
description: สร้าง sample covariance จากตารางผลตอบแทน เข้าใจ rank และความไม่เสถียรของ GMV แล้วใช้ factor model โดยระบุสมมติฐานของ residual ให้ครบ
---

# ประมาณ Covariance เมื่อข้อมูลมีจำกัด

<p class="lead">เมื่อเพิ่มหุ้นจาก 10 ตัวเป็น 100 ตัว เราต้องประมาณความเสี่ยงเพิ่มอีกกี่ค่า และข้อมูลย้อนหลังชุดเดิมยังเพียงพอหรือไม่?</p>

การหาพอร์ตที่ความผันผวนต่ำต้องรู้ทั้งความผันผวนของแต่ละสินทรัพย์และการเคลื่อนไหวร่วมกัน เราเคยใช้ covariance matrix เป็นข้อมูลเข้าใน[บท Efficient Frontier](efficient-frontier.html)แล้ว บทนี้ย้อนมาถามว่าตัวเลขในเมทริกซ์มาจากไหน และข้อผิดพลาดของการประมาณส่งต่อไปสู่น้ำหนักพอร์ตอย่างไร

ใช้ [นิยาม covariance และความเสี่ยงพอร์ต](portfolio-basics.html#covariance) เป็นพื้นฐาน ส่วนต้นเตรียมเมทริกซ์สมมติแปดเดือนและตรวจผลจาก NumPy กับ pandas ก่อนเข้าสู่จำนวนพารามิเตอร์ rank ความไวของ GMV และสมมติฐาน residual ของ factor model

เนื้อหาประกอบหัวข้อการประมาณความเสี่ยงของคอร์ส Advanced Portfolio Construction and Analysis with Python เรื่อง The curse of dimensionality และ Estimating the Covariance Matrix with a Factor Model ตัวเลขทั้งหมดในหน้านี้เป็นตัวอย่างที่สร้างขึ้น ไม่มีข้อมูลหุ้นจริง โค้ดใช้ NumPy และ pandas รันตามลำดับใน Notebook ใหม่ได้ หากยังไม่คุ้นกับ beta หรือ residual ให้อ่าน[บทหลายปัจจัย](multifactor-models.html#matrix-ols)ประกอบ

<span id="ตารางผลตอบแทนม-หน-งแถวต-อหน-งช-วงเวลา"></span>

<span id="returns-matrix"></span>

## เตรียมตารางสำหรับทดลองค่าประมาณ

สร้างผลตอบแทนรวมสมมติ $T=8$ เดือนของสินทรัพย์ $N=3$ ตัว หน่วยทศนิยม ตาราง $R$ ขนาด $T\times N$ ใช้เวลาเป็นแถวและสินทรัพย์เป็นคอลัมน์ ทุกคอลัมน์อ้างอิงเดือน สกุลเงิน และการนับกระแสเงินสดแบบเดียวกัน ตาม [การจัดข้อมูลผลตอบแทน](portfolio-basics.html#two-asset-data)

`pd.DataFrame` จัดตาราง `pd.period_range` สร้างป้ายเดือน และ `.shape` คืนจำนวนแถวกับคอลัมน์ตามลำดับ โค้ดรวม imports ไว้เพื่อให้รันบทนี้ใน Notebook ใหม่ได้

```python
import numpy as np
import pandas as pd

R = pd.DataFrame({
    "A": [-0.02, 0.00, 0.02, 0.04, -0.01, 0.01, 0.03, 0.05],
    "B": [-0.01, 0.01, 0.00, 0.02, 0.01, 0.03, 0.02, 0.04],
    "C": [0.005, 0.005, 0.015, 0.015, 0.015, 0.015, 0.005, 0.005],
}, index=pd.period_range("2025-01", periods=8, freq="M"))
T, N = R.shape
print("Months and assets:", R.shape)
print((R * 100).round(2))
```

ผลได้ `(8, 3)` ตารางที่พิมพ์คูณ 100 เพื่ออ่านเป็นเปอร์เซ็นต์ ส่วน `R` ยังคงเป็นผลตอบแทนทศนิยมที่จะใช้ประมาณ covariance ไม่ใช่ราคาสินทรัพย์

<span id="ห-กค-าเฉล-ยก-อนด-ว-าแต-ละค-เคล-อนไหวร-วมก-นเท-าไร"></span>

<span id="ต-วหาร-t-1-หมายถ-งอะไร"></span>

<span id="sample-covariance"></span>

## คำนวณ sample covariance ทุกคู่พร้อมกัน

ขยาย [การคำนวณ covariance สองสินทรัพย์](portfolio-basics.html#covariance) เป็นเมทริกซ์ โดยให้ $R_c=R-\bar R$ เป็นตารางที่หักค่าเฉลี่ยรายคอลัมน์แล้ว:

$$S=\frac{R_c^\mathsf{T}R_c}{T-1}.$$

$R_c^\mathsf{T}$ มีขนาด $N\times T$ คูณ $R_c$ ขนาด $T\times N$ จึงได้ผลรวมผลคูณของสินทรัพย์ทุกคู่ในเมทริกซ์ $N\times N$

```python
means = R.mean()
Rc = R - means
A_centered = Rc.to_numpy()
S_manual = A_centered.T @ A_centered / (T - 1)
ab_cross_products = Rc["A"] * Rc["B"]
print("Means (%):", (means * 100).round(2).to_dict())
print(f"First A/B product: {ab_cross_products.iloc[0]:.6f}")
print(f"Sum of A/B products: {ab_cross_products.sum():.6f}")
print(pd.DataFrame(S_manual, index=R.columns, columns=R.columns).round(8))
```

`R.mean()` หาค่าเฉลี่ยรายคอลัมน์ การลบ `means` จับคู่ตามชื่อคอลัมน์ `.to_numpy()` แปลงเป็น array, `.T` สลับแถวกับคอลัมน์ และ `@` คูณเมทริกซ์ ส่วน `.iloc[0]` เลือกเดือนแรก

ค่าเฉลี่ย A/B เท่ากับ 1.5% และ C เท่ากับ 1% ต่อเดือน ผลคูณส่วนต่าง A/B เดือนแรกคือ 0.000875 รวมแปดเดือนได้ 0.002 หาร 7 เป็น covariance 0.000285714 แนวทแยงให้ variance A/B/C เท่ากับ 0.00060000, 0.00025714 และ 0.00002857 ตามลำดับ ช่อง A/B กับ B/A เท่ากันจึงได้เมทริกซ์สมมาตร

หน่วย covariance คือผลตอบแทนทศนิยมรายเดือนยกกำลังสอง การคูณ returns ด้วย 100 จะเพิ่ม covariance $100^2$ เท่า รายละเอียดการรักษาหน่วยอยู่ใน [ความถี่และหน่วยของพอร์ต](portfolio-basics.html#frequency-consistency)

ใช้ `ddof=1` หรือตัวหาร $T-1$ เพื่อประมาณ covariance หลังประมาณค่าเฉลี่ยจากข้อมูลเดียวกัน ความไม่เอนเอียงเป็นคุณสมบัติเมื่อสุ่ม observations อิสระจากการแจกแจงเดียวกันที่มี second moments จำกัด ไม่ได้บอกว่าข้อมูลแปดเดือนนี้ตรงกับความเสี่ยงจริง หรือรับรองผลเดิมเมื่อมีความสัมพันธ์ข้ามเวลาและพารามิเตอร์เปลี่ยน ส่วน `ddof=0` หารด้วย $T$ เราจะตรวจผลต่างของ convention นี้กับไลบรารีต่อไป

<span id="covariance-python"></span>

## ตรวจคำตอบกับ NumPy และ pandas

`DataFrame.cov(ddof=1)` คำนวณ covariance ระหว่างคอลัมน์ ส่วน `np.cov` ตั้งค่าเริ่มต้นให้แต่ละแถวเป็นตัวแปร เราจึงต้องใส่ `rowvar=False` สำหรับตารางเวลาเป็นแถวของบทนี้

```python
S_pandas = R.cov(ddof=1)
S_numpy = np.cov(R.to_numpy(), rowvar=False, ddof=1)
S_ddof0 = np.cov(R.to_numpy(), rowvar=False, ddof=0)
print("Manual matches pandas:", np.allclose(S_manual, S_pandas.to_numpy()))
print("Manual matches NumPy:", np.allclose(S_manual, S_numpy))
print("T divisor equals (T-1)/T times sample:", np.allclose(S_ddof0, (T - 1) / T * S_manual))
```

ทั้งสามบรรทัดได้ `True` `np.allclose` ยอมให้ตัวเลขต่างกันเล็กน้อยจากการคำนวณทศนิยม ส่วน covariance ที่หารด้วย $T$ มีค่าเป็น $7/8$ ของแบบหารด้วย $T-1$ ในข้อมูลชุดนี้

รายละเอียดแนวข้อมูลและ `ddof` อยู่ใน[เอกสาร NumPy](https://numpy.org/doc/stable/reference/generated/numpy.cov.html) และ[เอกสาร pandas](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.cov.html) ตัวอย่างตอนนี้ไม่มีข้อมูลหาย เราจะดูผลของการข้ามแถวที่มีข้อมูลหายแยกต่างหากก่อนใช้เมทริกซ์กับพอร์ต

<span id="correlation-ทำให-เปร-ยบเท-ยบความส-มพ-นธ-ข-ามค-ได"></span>

<span id="covariance-correlation"></span>

## ตรวจการแปลง covariance เป็น correlation และกลับคืน

ใช้ $\rho_{ij}=S_{ij}/(s_i s_j)$ จาก [นิยาม correlation](portfolio-basics.html#correlation) โดยดึง SD จากรากของ variance บนแนวทแยง แล้วตรวจว่าคูณกลับได้เมทริกซ์เดิม

```python
asset_sds = np.sqrt(np.diag(S_manual))
sd_products = np.outer(asset_sds, asset_sds)
correlation = S_manual / sd_products
S_rebuilt = correlation * sd_products
print("Monthly SD (%):", np.round(asset_sds * 100, 4))
print(pd.DataFrame(correlation, index=R.columns, columns=R.columns).round(4))
print("Rebuilt covariance matches:", np.allclose(S_rebuilt, S_manual))
```

`np.diag` ดึงแนวทแยง `np.sqrt` ถอดราก และ `np.outer` สร้างผลคูณ SD ทุกคู่ ได้ correlation A/B ประมาณ 0.7274 ส่วนคู่ที่เกี่ยวกับ C ใกล้ศูนย์ และ `Rebuilt covariance matches` เป็น `True` สำหรับคอลัมน์คงที่ SD จะเป็นศูนย์และ correlation นิยามไม่ได้ จึงต้องแยกกรณีนี้จากค่าศูนย์ที่ตีความว่าไม่มีความสัมพันธ์เชิงเส้น

<span id="covariance-portfolio-risk"></span>

## ตรวจ wΣw ด้วยการสร้างผลตอบแทนพอร์ตจริงในตัวอย่าง

ใช้ [สูตร variance พอร์ต](portfolio-basics.html#portfolio-variance) $s_p^2=w^\mathsf{T}Sw$ ตรวจเทียบกับ variance ของ `R @ weights` โดยใช้แปดเดือนและตัวหาร $T-1$ เหมือนกัน กำหนดน้ำหนัก A/B/C เป็น 40/40/20 ปรับกลับทุกต้นเดือน ไม่มีต้นทุนหรือเงินฝากถอน

```python
weights = pd.Series({"A": 0.4, "B": 0.4, "C": 0.2})
w = weights.reindex(R.columns).to_numpy()
portfolio_returns = R @ weights
portfolio_variance = w @ S_manual @ w
portfolio_sd = np.sqrt(portfolio_variance)
print(f"Matrix variance: {portfolio_variance:.9f}")
print(f"Variance of portfolio returns: {portfolio_returns.var(ddof=1):.9f}")
print(f"Monthly portfolio SD: {portfolio_sd:.4%}")
```

ได้ variance 0.000229714 ทั้งสองวิธี และ SD ประมาณ 1.5156% ต่อเดือน `reindex` จัดลำดับน้ำหนักให้ตรงกับคอลัมน์ก่อนแปลงเป็น array ส่วน `R @ weights` ยังมีชื่อให้ pandas จับคู่

ในข้อมูลจริง หากน้ำหนักไหลตามราคา ไม่ได้ rebalancing กลับ และไม่ได้ใช้ชุดเดือนเดียวกัน ความเท่ากันนี้จะไม่ใช่การตรวจแบบเดียวกับที่เรากำหนดไว้ การเทียบความเสี่ยงคาดการณ์กับความเสี่ยงภายหลังต้องแยกด้วยว่า $S$ ใช้ข้อมูลถึงวันใด และน้ำหนักถูกตัดสินใจเมื่อใด

<span id="covariance-dimensionality"></span>

## จำนวนค่าที่ไม่ซ้ำกันเพิ่มเป็นกำลังสอง

เมทริกซ์ $N\times N$ มี $N^2$ ช่อง แต่ครึ่งบนกับครึ่งล่างซ้ำกัน เราจึงมี variance $N$ ค่าและ covariance นอกแนวทแยง $N(N-1)/2$ ค่า รวม

$$
\frac{N(N+1)}{2}
$$

ค่าที่ไม่ซ้ำกัน หากเขียนด้วย SD และ correlation ก็มี SD $N$ ค่าและ correlation ของคู่ที่ต่างกัน $N(N-1)/2$ ค่าเท่ากัน การประมาณ expected return อีก $N$ ค่าเป็นงานเพิ่มจากเมทริกซ์ความเสี่ยงนี้

| จำนวนสินทรัพย์ N | Variance | Covariance ของคู่ที่ต่างกัน | รวมค่าที่ไม่ซ้ำใน S |
|---:|---:|---:|---:|
| 3 | 3 | 3 | 6 |
| 10 | 10 | 45 | 55 |
| 30 | 30 | 435 | 465 |
| 100 | 100 | 4,950 | 5,050 |
| 500 | 500 | 124,750 | 125,250 |

เราไม่ได้มีการทดลองอิสระใหม่ 5,050 ครั้งเพียงเพราะคำนวณได้ 5,050 ช่อง ทุกช่องอาศัยเดือนชุดเดียวกัน การเพิ่มจำนวนหุ้นโดยไม่เพิ่มข้อมูลทำให้ต้องประเมินความสัมพันธ์จำนวนมากจากประวัติเดิม แต่การนำจำนวนช่องไปเทียบกับจำนวนเดือนอย่างเดียวไม่ใช่เกณฑ์ตัดสินว่าเมทริกซ์กลับด้านได้หรือไม่

ตัวอย่างเช่น หุ้น 100 ตัวกับข้อมูล 2,500 วันมี 5,050 ค่าที่ไม่ซ้ำ มากกว่าจำนวนวัน แต่ covariance ขนาด $100\times100$ ยังอาจมี rank ครบได้ ต้องแยกปัญหาความไม่แน่นอนของการประมาณออกจากข้อจำกัดทางพีชคณิตต่อไปนี้

<span id="covariance-rank"></span>

## Rank ถูกจำกัดด้วยจำนวนแถวหลังหักค่าเฉลี่ย

[Rank](glossary.html#matrix-rank) บอกจำนวนทิศทางของข้อมูลที่เป็นอิสระเชิงเส้น หลังหักค่าเฉลี่ย ผลรวมของแถวใน $R_c$ เป็นศูนย์ จึงมีความสัมพันธ์เชิงเส้นอย่างน้อยหนึ่งข้อระหว่างแถว และได้

$$
\operatorname{rank}(S)=\operatorname{rank}(R_c)
\leq\min(N,T-1).
$$

ถ้า $N\geq T$ covariance แบบนี้จึงมี rank ไม่ครบ $N$ แน่นอน เรียกว่า singular และไม่มีเมทริกซ์ผกผันปกติ แม้ $N<T$ ก็ยัง singular ได้ เช่น สินทรัพย์สองคอลัมน์ให้ผลตอบแทนเหมือนกันทุกเดือน

ลองข้อมูลใหม่ที่มี 4 เดือนแต่ 5 สินทรัพย์ เราใช้ชุดนี้เฉพาะสาธิต rank และไม่แทนชุด A/B/C เดิม

```python
wide_returns = np.array([
    [0.02, -0.01, 0.03, 0.00, 0.01],
    [-0.01, 0.02, 0.00, 0.03, 0.01],
    [0.03, 0.00, -0.02, 0.01, -0.01],
    [0.00, 0.01, 0.01, -0.01, 0.02],
])
wide_centered = wide_returns - wide_returns.mean(axis=0)
S_wide = wide_centered.T @ wide_centered / (len(wide_returns) - 1)
print("Covariance shape:", S_wide.shape)
print("Rank:", np.linalg.matrix_rank(S_wide))
print("Eigenvalues:", np.round(np.linalg.eigvalsh(S_wide), 9))
```

ได้เมทริกซ์ขนาด `(5, 5)` แต่ rank 3 ค่า eigenvalue สองค่าจึงใกล้ศูนย์ Eigenvalue วัดการกระจายตามทิศทางเฉพาะของเมทริกซ์ ค่าใกล้ศูนย์บอกว่ามีทิศทางที่ข้อมูลชุดนี้แทบไม่มีความแปรปรวน การคำนวณเลขทศนิยมอาจให้ค่าลบจิ๋วระดับ $10^{-20}$ แทนศูนย์พอดี

สำหรับข้อมูลครบทุกแถว sample covariance ต้องเป็น [positive semidefinite หรือ PSD](glossary.html#positive-semidefinite) เพราะสำหรับเวกเตอร์น้ำหนักใด ๆ $v$:

$$
v^\mathsf{T}Sv=\frac{\sum_t(R_cv)_t^2}{T-1}\geq0.
$$

Variance จึงติดลบไม่ได้ แต่ PSD ยอมให้มี eigenvalue ศูนย์ ส่วน positive definite ต้องเป็นบวกทุกทิศทาง การตรวจว่าเมทริกซ์สมมาตรเพียงอย่างเดียวจึงไม่พอ และการกลับด้านได้ก็ยังไม่รับประกันว่าค่าประมาณจะเสถียร

<span id="near-singular-gmv"></span>

## เมทริกซ์เกือบ singular ทำให้น้ำหนัก GMV ไวต่อค่าประมาณ

Global Minimum Variance หรือ GMV คือพอร์ตที่ variance ต่ำสุด ภายใต้เงื่อนไขน้ำหนักรวมหนึ่ง ถ้าอนุญาตขายชอร์ตโดยไม่จำกัดและ $S$ เป็น positive definite คำตอบคือ

$$
w_{\mathrm{GMV}}=\frac{S^{-1}\mathbf1}{\mathbf1^\mathsf{T}S^{-1}\mathbf1},
$$

โดย $\mathbf1$ เป็นเวกเตอร์ที่ทุกค่าเท่ากับหนึ่ง เราคำนวณ $S^{-1}\mathbf1$ ด้วย `np.linalg.solve(S, ones)` ซึ่งแก้สมการเชิงเส้นโดยไม่สร้าง inverse เอง แต่การเปลี่ยนวิธีคำนวณไม่ได้กำจัดความไม่แน่นอนที่อยู่ใน $S$

ตัวอย่างใหม่ต่อไปใช้พารามิเตอร์รายปีที่ตั้งขึ้นเอง สินทรัพย์สองตัวมี correlation 0.99999 และ SD ตัวแรก 20% เราลองเปลี่ยน SD ตัวที่สองจาก 20.01% เป็น 19.99% ซึ่งต่างกันเพียง 0.02 จุดเปอร์เซ็นต์ ดูว่าน้ำหนักเปลี่ยนเท่าไร

```python
near_results = []
for sd_b in [0.2001, 0.1999]:
    sds = np.array([0.20, sd_b])
    S_near = np.outer(sds, sds) * np.array([[1.0, 0.99999], [0.99999, 1.0]])
    raw_solution = np.linalg.solve(S_near, np.ones(2))
    gmv_weights = raw_solution / raw_solution.sum()
    near_results.append({
        "SD of B": sd_b, "Condition number": np.linalg.cond(S_near),
        "Weight A": gmv_weights[0], "Weight B": gmv_weights[1],
        "Long-only weight A": np.clip(gmv_weights[0], 0, 1),
    })
near_table = pd.DataFrame(near_results)
print(near_table.round(4).to_string(index=False))
```

กรณี SD ของ B 20.01% ให้น้ำหนัก A ประมาณ 25.1853 และ B −24.1853 หมายถึง long A ราว 2,518.53% และ short B ราว 2,418.53% ของเงินทุน ส่วนกรณี SD ของ B 19.99% กลับเป็น A −24.1974 และ B 25.1974 สูตรพยายามใช้สองสินทรัพย์ที่เกือบเคลื่อนไหวเหมือนกันหักล้างความเสี่ยง แต่ต้องใช้สถานะขนาดใหญ่มาก

Condition number ในตัวอย่างประมาณ 200,000 เป็นสัญญาณว่าการแก้สมการอาจไวต่อการเปลี่ยนข้อมูล ไม่ใช่โอกาสขาดทุนและไม่ใช่จำนวนครั้งที่การคำนวณผิด น้ำหนักที่แกว่งนี้เกิดแม้เราไม่ได้เปลี่ยน expected return เพราะ GMV ใช้ covariance เป็นหลัก

คอลัมน์สุดท้ายจำกัดน้ำหนัก A ให้อยู่ในช่วง 0 ถึง 1 ด้วย `np.clip` สำหรับโจทย์สองสินทรัพย์ที่น้ำหนักรวมหนึ่งและ variance เป็นฟังก์ชันกำลังสองนี้ การตัดคำตอบให้อยู่ในช่วงให้คำตอบ long-only ได้: กรณีแรกถือ A ทั้งหมด กรณีหลังถือ B ทั้งหมด จึงลดการใช้สถานะมหาศาล แต่ยังเห็นน้ำหนักกระโดดจากปลายหนึ่งไปอีกปลายหนึ่ง

วิธี clip นี้ใช้สาธิตโจทย์สองตัวโดยเฉพาะ พอร์ตหลายตัวต้องแก้ optimization ภายใต้ข้อจำกัดจริง การใช้ pseudoinverse กับเมทริกซ์ singular ก็เป็นการเลือกคำตอบตามเกณฑ์หนึ่ง ไม่ได้เพิ่มข้อมูลให้ค่าประมาณความเสี่ยงถูกต้องขึ้น

<span id="missing-covariance"></span>

## ข้อมูลหายอาจทำให้ covariance รายคู่ประกอบกันไม่ได้

pandas ข้ามค่าที่หายเมื่อคำนวณ covariance ของแต่ละคู่ จึงอาจใช้เดือนคนละชุดสำหรับ A/B กับ A/C แม้ทุกช่องมีตัวเลข เมื่อนำมารวมเป็นเมทริกซ์อาจไม่เป็น PSD ตามที่[เอกสาร pandas เตือนไว้](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.cov.html)

ตารางสมมติต่อไปสร้างให้ A/B เคลื่อนไหวทางเดียวกันในสองแถวแรก A/C ไปทางเดียวกันในสองแถวถัดมา และ B/C สวนทางกันในสองแถวท้าย `np.nan` หมายถึงไม่มีข้อมูล ไม่ใช่ผลตอบแทนศูนย์

```python
incomplete = pd.DataFrame({
    "A": [1, -1, 1, -1, np.nan, np.nan],
    "B": [1, -1, np.nan, np.nan, 1, -1],
    "C": [np.nan, np.nan, 1, -1, -1, 1],
}) * 0.01
S_pairwise = incomplete.cov()
print(S_pairwise.round(7))
print("Smallest eigenvalue:", np.linalg.eigvalsh(S_pairwise.to_numpy())[0])
print("Rows complete for all assets:", len(incomplete.dropna()))
```

เมทริกซ์มี variance บนแนวทแยงประมาณ 0.0001333 แต่ covariance รายคู่เป็น +0.0002, +0.0002 และ −0.0002 ค่า eigenvalue ต่ำสุดประมาณ −0.0002667 ซึ่งไม่ใช่ความคลาดเคลื่อนจิ๋วจากคอมพิวเตอร์ เมทริกซ์นี้ให้ variance ติดลบสำหรับน้ำหนักบางชุดได้ จึงใช้เป็น covariance ของพอร์ตอย่างสอดคล้องกันไม่ได้

การเลือกเฉพาะแถวที่ทุกสินทรัพย์มีข้อมูลช่วยให้คำนวณจากตัวอย่างเดียวกัน แต่ในโจทย์นี้ `dropna()` เหลือศูนย์แถว ต้องแก้โจทย์ข้อมูลก่อน เช่น หาแหล่งที่ครอบคลุมช่วงเดียวกันหรือเปลี่ยนจักรวาลสินทรัพย์ การเติมช่องว่างด้วยศูนย์คือสมมติว่าผลตอบแทนเดือนนั้นเป็นศูนย์ ซึ่งต้องมีเหตุผลรองรับ

ในงานจริงควรบันทึกจำนวน observations และช่วงเวลาที่ใช้ร่วมกันด้วย การใช้ข้อมูลราคาที่ปิดคนละเขตเวลาหรือสินทรัพย์ที่ไม่มีการซื้อขายทุกวันอาจทำให้ความสัมพันธ์ที่เห็นได้รับผลจากวิธีบันทึกข้อมูล แม้ไฟล์ไม่มีช่องว่างเลยก็ตาม

<span id="factor-covariance-model"></span>

## Factor model อธิบายความสัมพันธ์ผ่านปัจจัยร่วมจำนวนน้อย

ให้ $r_t$ เป็นเวกเตอร์ผลตอบแทนของสินทรัพย์ $N$ ตัว ณ เวลา $t$ และ $f_t$ เป็นเวกเตอร์ factor $K$ ตัว เขียนแบบจำลองเป็น

$$
r_t=a+Bf_t+\varepsilon_t.
$$

$a$ มีค่าคงที่หนึ่งค่าต่อสินทรัพย์ $B$ เป็นเมทริกซ์ loading ขนาด $N\times K$ และ $\varepsilon_t$ เป็นส่วนที่ factor อธิบายไม่ได้ของสินทรัพย์แต่ละตัว Loading ยังมีความหมายเป็นความไวตาม[บทก่อน](multifactor-models.html#loadings-not-weights) ไม่ใช่น้ำหนักเงินลงทุน

เมื่อ factor กับ residual ไม่มี covariance กัน และค่าคงที่ $a$ ไม่เปลี่ยนตามเวลา จะได้

$$
\Sigma=B\Sigma_fB^\mathsf{T}+\Psi,
\qquad\Psi=\operatorname{Cov}(\varepsilon_t).
$$

$\Sigma_f$ เป็น covariance ของ factor ขนาด $K\times K$ และ $\Psi$ เป็น covariance ของ residual ขนาด $N\times N$ หาก factor กับ residual มี covariance กัน สูตรเต็มยังต้องเพิ่ม $B\operatorname{Cov}(f,\varepsilon)+\operatorname{Cov}(\varepsilon,f)B^\mathsf{T}$ อีกสองพจน์

Factor แต่ละตัวสัมพันธ์กันได้ เราจึงเก็บช่องนอกแนวทแยงของ $\Sigma_f$ ไว้ การใช้ factor ที่ตั้งฉากกันเป็นทางเลือกหนึ่งของแบบจำลอง ไม่ใช่คุณสมบัติที่ Fama–French หรือ factor ทุกชุดต้องมี

### สร้างตัวอย่างที่ residual ของสองสินทรัพย์ยังเคลื่อนไหวร่วมกัน

ใช้ข้อมูลใหม่แปดเดือนและสินทรัพย์สี่ตัวเพื่อให้ตรวจตารางได้ง่าย Factor สองตัวใช้การแกว่งร่วมบางส่วน ส่วน residual ของสินทรัพย์ที่หนึ่งกับสองใช้ตัวแปร `q` ร่วมกัน จึงตั้งใจให้สมมติฐาน residual ไม่สัมพันธ์กันผิดในโจทย์นี้

```python
u = np.tile([-1, 1], 4)
v = np.tile([-1, -1, 1, 1], 2)
q = np.repeat([-1, 1], 4)
z = u * v
F = np.column_stack([0.005 + 0.020 * u, 0.002 + 0.010 * u + 0.015 * v])
B_true = np.array([[1.0, 0.3], [0.8, -0.2], [0.4, 0.7], [1.2, 0.1]])
E_true = np.column_stack([0.010 * q, 0.015 * q, 0.008 * z, 0.005 * q + 0.010 * z])
a_true = np.array([0.0, 0.001, -0.0005, 0.0007])
Y = a_true + F @ B_true.T + E_true
print("Returns:", Y.shape, "factors:", F.shape, "loadings:", B_true.shape)
print("Factor correlation:", np.round(np.corrcoef(F, rowvar=False), 4))
```

`np.tile` ทำรูปแบบซ้ำ ส่วน `np.repeat` ทำค่าแต่ละตัวซ้ำตามจำนวนที่กำหนด `np.column_stack` วางแต่ละชุดเป็นคอลัมน์ ได้ผลตอบแทน `Y` ขนาด 8×4, factor `F` ขนาด 8×2 และ loading ขนาด 4×2 ผลคูณ `F @ B_true.T` จึงเป็น 8×4 พร้อมบวกค่าคงที่รายสินทรัพย์และ residual ได้

ตัวอย่างนี้ใช้ผลตอบแทนในหน่วยทศนิยมรายเดือน และสมมติผลตอบแทนปลอดความเสี่ยงเป็นศูนย์ จึงไม่มีความต่างระหว่าง total กับ excess return ในการสาธิตนี้ หาก RF เปลี่ยนไปในแต่ละเดือนและ fit ด้วย excess return เมทริกซ์ที่ได้ก็เป็น covariance ของ excess return ต้องดูความเสี่ยงของ RF และ covariance ที่เกี่ยวข้องเมื่อต้องการกลับไปเป็น total-return covariance

<span id="full-residual-covariance"></span>

## เก็บ residual covariance ครบจะสร้าง sample covariance กลับมาได้

เรา fit สมการของสินทรัพย์ทั้งสี่พร้อมกันด้วย OLS ที่มี intercept โดยวางคอลัมน์หนึ่งไว้หน้าข้อมูล factor แต่ละคอลัมน์ของ `Y` เป็นกองทุนหรือสินทรัพย์ที่ต้องการอธิบาย `np.linalg.lstsq` จึงคืน coefficient หนึ่งคอลัมน์ต่อสินทรัพย์

```python
X_factor = np.column_stack([np.ones(len(F)), F])
fit_coef = np.linalg.lstsq(X_factor, Y, rcond=None)[0]
B_hat = fit_coef[1:].T
E_hat = Y - X_factor @ fit_coef
Sigma_f = np.cov(F, rowvar=False, ddof=1)
Psi = np.cov(E_hat, rowvar=False, ddof=1)
S_factor_full = B_hat @ Sigma_f @ B_hat.T + Psi
S_assets = np.cov(Y, rowvar=False, ddof=1)
print("Estimated loadings:\n", np.round(B_hat, 4))
print("Factors orthogonal to residuals:", np.allclose((F - F.mean(axis=0)).T @ E_hat, 0))
print("Full reconstruction:", np.allclose(S_factor_full, S_assets))
```

`fit_coef[1:]` เลือก coefficient ของ factor หลังแถว intercept แล้ว `.T` จัดกลับเป็นสินทรัพย์ตามแถวและ factor ตามคอลัมน์ ได้ loading ตรงกับ `B_true` ตามที่ออกแบบไว้ สองบรรทัดสุดท้ายได้ `True`

OLS พร้อม intercept ทำให้ residual ตั้งฉากกับ factor ใน sample ที่ใช้ fit จึงสร้าง covariance ของ sample กลับได้เมื่อใช้ $\Psi$ ครบและตัวหาร $T-1$ เหมือนกันทุกส่วน แต่ OLS ไม่ได้บังคับให้ residual ของสินทรัพย์คนละตัวตั้งฉากกัน สิ่งที่เราใส่ร่วมกันใน `q` จึงยังเหลืออยู่

การเขียน sample covariance ใหม่เป็นสองส่วนนี้ยังไม่ได้ลดจำนวน covariance ที่ต้องประมาณ เพราะ $\Psi$ ยังมีคู่สินทรัพย์ครบทุกคู่ การลดจำนวนเกิดขึ้นเมื่อเรากำหนดโครงสร้างให้ $\Psi$ เพิ่มเติม

<span id="diagonal-residual-assumption"></span>

## ใช้ D แนวทแยงคือการสมมติว่า residual ข้ามสินทรัพย์ไม่สัมพันธ์กัน

Factor covariance estimator แบบหนึ่งแทน $\Psi$ ด้วยเมทริกซ์แนวทแยง $D$ ที่เก็บ variance ของ residual แต่ละตัวและตั้ง covariance ข้ามสินทรัพย์เป็นศูนย์:

$$
\widehat\Sigma_{\mathrm{factor}}=\widehat B\widehat\Sigma_f\widehat B^\mathsf{T}+\widehat D.
$$

สมมติฐานนี้เหมาะหรือไม่ขึ้นกับ factor ที่เลือก หากมีความเสี่ยงร่วมจากอุตสาหกรรมหรือประเทศที่ยังไม่อยู่ใน factor ความสัมพันธ์นั้นอาจยังค้างใน residual การเรียกส่วนที่เหลือว่า specific return จึงไม่ทำให้มันเป็นอิสระข้ามสินทรัพย์ตามชื่อ

```python
D_sample = np.diag(np.diag(Psi))
S_factor_diagonal = B_hat @ Sigma_f @ B_hat.T + D_sample
factor_weights = np.full(Y.shape[1], 1 / Y.shape[1])
full_sd = np.sqrt(factor_weights @ S_factor_full @ factor_weights)
diagonal_sd = np.sqrt(factor_weights @ S_factor_diagonal @ factor_weights)
print(f"Residual covariance, asset 1/2: {Psi[0, 1]:.8f}")
print(f"Asset covariance with full residual: {S_factor_full[0, 1]:.8f}")
print(f"Asset covariance with diagonal residual: {S_factor_diagonal[0, 1]:.8f}")
print(f"Equal-weight monthly SD: full {full_sd:.4%}; diagonal {diagonal_sd:.4%}")
```

`np.diag` ชั้นในดึง variance ของ residual ส่วนชั้นนอกนำค่ากลับไปวางเฉพาะแนวทแยง `np.full` สร้างน้ำหนักเท่ากันสี่ตัว ตัวละ 0.25

Residual covariance ของสินทรัพย์ 1/2 เท่ากับประมาณ 0.00017143 เมื่อตัดพจน์นี้ covariance รวมของคู่นั้นลดจาก 0.00052400 เป็น 0.00035257 พอร์ตน้ำหนักเท่ากันมี SD 2.2890% ต่อเดือนเมื่อใช้ residual covariance ครบ และ 2.1754% เมื่อเหลือเฉพาะแนวทแยง

ในตัวอย่างนี้ diagonal approximation ประเมินความเสี่ยงต่ำกว่า covariance ของข้อมูลที่สร้าง เพราะเราจงใจทิ้งความสัมพันธ์บวกที่ยังเหลืออยู่ กรณีอื่นอาจให้ความต่างอีกทิศทางหนึ่ง จึงไม่มีข้อสรุปว่าการตั้ง residual covariance เป็นศูนย์ทำให้ค่าความเสี่ยงต่ำลงทุกพอร์ตเสมอ

หาก $\widehat\Sigma_f$ เป็น PSD และ diagonal residual variances ไม่ติดลบ เมทริกซ์ที่ประกอบได้จะเป็น PSD ด้วย และถ้า residual variance ทุกตัวเป็นบวกก็จะเป็น positive definite เงื่อนไขทางพีชคณิตนี้ทำให้ใช้คำนวณความเสี่ยงได้อย่างสอดคล้อง แต่ยังไม่ได้พิสูจน์ว่าใกล้ covariance ในอนาคต

<span id="factor-parameter-count"></span>

## ประหยัดจำนวนค่าที่ประมาณโดยแลกกับข้อสมมติ

เมื่อใช้ factor ที่สังเกตได้ $K$ ตัว และ residual covariance แนวทแยง รายการข้อมูลความเสี่ยงที่ต้องประมาณประกอบด้วย loading $NK$ ค่า, factor covariance ที่ไม่ซ้ำ $K(K+1)/2$ ค่า และ residual variance อีก $N$ ค่า รวม

$$
NK+\frac{K(K+1)}{2}+N.
$$

ตัวอย่าง $N=100,K=5$ ได้ $500+15+100=615$ ค่า เทียบกับ sample covariance ที่มี 5,050 ค่า หากกำหนด factor ให้ไม่มี covariance กัน เหลือ factor variances 5 ค่า รวมเป็น 605 ค่า แต่การละ covariance ของ factor ต้องมีเหตุผลตามแบบจำลองด้วย

การนับเฉพาะ 500 loadings ยังไม่ครบสิ่งที่ต้องใช้สร้าง covariance matrix ส่วน intercept และค่าเฉลี่ยเป็นพารามิเตอร์เพิ่มเติมของการ fit ผลตอบแทน ค่าคงที่เหล่านั้นไม่ปรากฏใน covariance โดยตรง

สำหรับตัวอย่างสี่สินทรัพย์สอง factor ข้างต้น รายการนี้มี $8+3+4=15$ ค่า ซึ่งมากกว่าสิบค่าที่ไม่ซ้ำใน sample covariance เราใช้ระบบเล็กเพื่อให้ตรวจตารางและสมมติฐานของ residual ได้ ประโยชน์ด้านจำนวนพารามิเตอร์จะเห็นเมื่อจำนวนสินทรัพย์มากเมื่อเทียบกับ factor และไม่ได้หมายความว่าต้องเลือก factor model กับทุกโจทย์

### ตัวหารของ residual variance ขึ้นกับสิ่งที่ต้องการประมาณ

ในตัวอย่าง reconstruction เราใช้ covariance ของ residual ด้วยตัวหาร $T-1$ เพื่อให้เอกลักษณ์ sample covariance ตรงกันทุกพจน์ หากต้องการประมาณ variance ของ error ใน regression ที่มี intercept และ factor $K$ ตัว ภายใต้เงื่อนไข OLS แบบมาตรฐาน ตัวหารปรับ degrees of freedom เป็น $T-K-1$

```python
factor_T, factor_K = F.shape
D_regression = np.diag(np.sum(E_hat ** 2, axis=0) / (factor_T - factor_K - 1))
print("Divisors: sample", factor_T - 1, "regression", factor_T - factor_K - 1)
print("Sample residual variances:", np.round(np.diag(D_sample), 7))
print("Regression error-variance formula:", np.round(np.diag(D_regression), 7))
print("Ratio:", np.round(np.diag(D_regression) / np.diag(D_sample), 4))
```

ได้ตัวหาร 7 กับ 5 ค่าจากสูตร regression จึงเป็น 1.4 เท่าของ sample residual variances ในชุดนี้ การสลับตัวหารทำให้ reconstruction ไม่ใช่เอกลักษณ์เดียวกับก่อนหน้า ต้องระบุ convention เมื่อเปรียบเทียบผลจากโปรแกรมต่างกัน

สูตรหารด้วย $T-K-1$ อาศัยสมมติฐานเช่น conditional mean ของ error เป็นศูนย์ ความแปรปรวนคงที่ และไม่มีความสัมพันธ์ข้าม observations สำหรับผลไม่เอนเอียงตามแบบจำลอง ข้อมูลตัวอย่างนี้เป็นแพตเทิร์นที่สร้างไว้ จึงใช้สอนการคำนวณตัวหาร ไม่ใช่หลักฐานว่าผ่านเงื่อนไขทางสถิติ

<span id="covariance-estimation-caveats"></span>

## เมทริกซ์ที่คำนวณได้ต้องผ่านการใช้งานนอกช่วงประมาณ

Factor model อาจใช้ตัวแปรมหภาค ลักษณะบริษัทหรืออุตสาหกรรม หรือปัจจัยที่สกัดจากข้อมูล เช่น principal components การเลือกจำนวน factor ช่วงข้อมูล และวิธีจัดการ residual ยังเป็นการตัดสินใจของแบบจำลอง แม้ factor จะถูกสกัดทางสถิติก็ไม่ได้แปลว่าไม่มีข้อสมมติหรือดีที่สุดสำหรับทุกพอร์ต

อีกวิธีที่ Transcript แนะนำคือ constant-correlation model: คง variance ของแต่ละสินทรัพย์ไว้ แต่แทน correlation ของคู่ที่ต่างกันด้วยค่าเฉลี่ยร่วมค่าเดียว วิธีนี้ลดความแตกต่างระหว่างค่าประมาณโดยยอมให้โครงสร้างห่างจากตลาดจริงบางส่วน แนวคิดเดียวกันนำไปสู่การผสม sample covariance กับเมทริกซ์ที่มีโครงสร้างในบท shrinkage ต่อไป

การเพิ่มความถี่ข้อมูลอาจเพิ่มจำนวนแถว แต่เปลี่ยนปัญหาเรื่องราคาที่ไม่พร้อมกัน เสียงรบกวนจากการซื้อขาย และความสัมพันธ์ข้ามเวลา การย้อนกลับไปไกลขึ้นอาจรวมช่วงที่ความเสี่ยงต่างจากปัจจุบัน จึงไม่ควรถือว่าทุกแถวที่เพิ่มให้ข้อมูลใหม่คุณภาพเท่าเดิม

ถ้าจะเปรียบเทียบ sample covariance กับ factor covariance ให้ประมาณทั้งคู่จากข้อมูลก่อนวันตัดสินใจ แล้วใช้ข้อจำกัดพอร์ตและต้นทุนแบบเดียวกันในช่วงภายหลัง ตรวจทั้งความเสี่ยงที่เกิดจริง ความเปลี่ยนแปลงน้ำหนัก และความเข้มข้นของพอร์ต การที่เมทริกซ์หนึ่งทำให้ optimizer สำเร็จหรือให้ variance ต่ำมากในช่วงฝึกยังตอบไม่ได้ว่าจะใช้พอร์ตได้ดีกว่าในอนาคต

<span id="covariance-exercises"></span>

## แบบฝึกหัดพร้อมแนวคำตอบ

### 1. มี 20 สินทรัพย์ ต้องประมาณกี่ค่า?

แยก variance และ covariance ของคู่ที่ต่างกันก่อนรวมคำตอบ

เฉลย: variance 20 ค่าและ covariance $20(19)/2=190$ ค่า รวม 210 ค่าที่ไม่ซ้ำกันในเมทริกซ์ ยังไม่รวม expected returns อีก 20 ค่า

### 2. มี 60 เดือนและ 80 สินทรัพย์

Sample covariance ขนาด 80×80 ที่หักค่าเฉลี่ยแล้วมี rank เต็ม 80 ได้หรือไม่?

เฉลย: rank ไม่เกิน $\min(80,59)=59$ จึง singular แน่นอน การคำนวณ inverse แล้วโปรแกรมไม่รายงาน error ไม่ใช่หลักฐานว่าเมทริกซ์มีข้อมูลครบทุกทิศทาง ต้องตรวจ rank และความไวเชิงตัวเลขด้วย

### 3. เปลี่ยนผลตอบแทนจากทศนิยมเป็นเปอร์เซ็นต์

ถ้า covariance เดิมเป็น 0.0004 แล้วคูณผลตอบแทนทุกค่าด้วย 100 covariance และ correlation เปลี่ยนอย่างไร?

เฉลย: covariance เป็น $0.0004\times100^2=4$ ส่วน correlation เหมือนเดิมเมื่อทั้งสองคอลัมน์คูณค่าบวก 100 เหมือนกัน ค่า SD เพิ่มเป็น 100 เท่าตามหน่วย

### 4. Factor ไม่สัมพันธ์กับ residual แล้ว residual ของหุ้นต้องไม่สัมพันธ์กันด้วยหรือไม่?

เฉลย: เป็นคนละเงื่อนไข OLS ที่มี intercept ทำให้ factor ตั้งฉากกับ residual ใน sample แต่ไม่ได้บังคับ covariance ระหว่าง residual ของหุ้น 1 กับหุ้น 2 เป็นศูนย์ ตัวแปร `q` ที่ร่วมกันในตัวอย่างทำให้คู่นี้ยังสัมพันธ์กันเต็มที่

### 5. เมทริกซ์ factor เป็น positive definite แล้วปลอดภัยพอให้ใช้พอร์ตหรือยัง?

เฉลย: เรารู้ว่า variance เป็นบวกในทุกทิศทางและเมทริกซ์กลับด้านได้ แต่ยังต้องประเมินว่าปัจจัยครอบคลุมความเสี่ยงหรือไม่ พารามิเตอร์คงที่เพียงใด และน้ำหนักที่ได้ทำงานอย่างไรในช่วงภายหลัง ข้อจำกัด long-only ช่วยจำกัดสถานะ แต่ตัวอย่างสองสินทรัพย์แสดงว่าน้ำหนักยังอาจกระโดดได้

<span id="covariance-sources"></span>

## แหล่งเรียนและขอบเขตของบท

อ่าน Transcript เต็มของ [The curse of dimensionality](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/ZMjFG/the-curse-of-dimensionality) และ [Estimating the Covariance Matrix with a Factor Model](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/CC9Qx/estimating-the-covariance-matrix-with-a-factor-model) เมื่อ 3 ตุลาคม 2026 ใช้เป็นโครงเรื่องจำนวนพารามิเตอร์ การเพิ่มโครงสร้าง และความเสี่ยงจากสมมติฐาน ตัวอย่าง คำอธิบายไทย สมการที่ขยายความ โค้ด และแบบฝึกหัดในหน้านี้เขียนขึ้นใหม่

ตรวจวิธีเรียกใช้และ convention กับ [NumPy: cov](https://numpy.org/doc/stable/reference/generated/numpy.cov.html) และ [pandas: DataFrame.cov](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.cov.html) การเปรียบเทียบจำนวนค่าที่ไม่ซ้ำในเมทริกซ์กับจำนวนวันที่มีข้อมูลเป็นแรงจูงใจให้ระวัง estimation error ส่วนข้อสรุปเรื่อง singularity ในบทนี้ใช้ขอบเขต rank โดยตรง
