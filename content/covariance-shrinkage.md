---
title: ลดความคลาดเคลื่อนของ Covariance ด้วย Shrinkage
description: สร้าง Constant-correlation target ทีละขั้น แยกค่า shrinkage ที่เลือกไว้จาก Ledoit–Wolf แล้วเปรียบเทียบ Rolling GMV ด้วยข้อมูลที่มีอยู่ก่อนลงทุน
---

# ลดความคลาดเคลื่อนของ Covariance ด้วย Shrinkage

<p class="lead">ถ้า correlation ของหุ้นสองตัวเปลี่ยนมากเมื่อเพิ่มข้อมูลเพียงหนึ่งเดือน เราควรให้น้ำหนักกับตัวเลขที่ประมาณได้มากแค่ไหน?</p>

เมทริกซ์ [covariance](glossary.html#covariance) เป็นข้อมูลเข้าของพอร์ตความแปรปรวนต่ำสุด หาก covariance บางคู่ต่ำเพราะความบังเอิญของช่วงข้อมูล โปรแกรมอาจให้น้ำหนักมากกับการกระจายความเสี่ยงที่ดูดีเฉพาะช่วงนั้น วิธี [shrinkage](glossary.html#covariance-shrinkage) นำ sample covariance มาผสมกับเมทริกซ์ที่กำหนดโครงสร้างให้ง่ายขึ้น ก่อนนำไปหาน้ำหนักพอร์ต

บทนี้เริ่มจากสินทรัพย์สมมติสามตัว เพื่อคำนวณทีละช่องในเมทริกซ์ แล้วทดลองกับสินทรัพย์สมมติแปดตัว โดยใช้ข้อมูลย้อนหลัง 36 เดือนเพื่อเลือกน้ำหนักสำหรับเดือนถัดไป เนื้อหาประกอบ [Honey I Shrunk the Covariance Matrix!](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/szNVo/honey-i-shrunk-the-covariance-matrix) และ [Lab Session — Covariance Estimation](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/DLb5f/module-2-lab-session-covariance-estimation)

ข้อมูลและโค้ดต่อไปนี้เขียนขึ้นใหม่ ใช้ผลตอบแทนรวมรายเดือนในหน่วยทศนิยม สกุลเงินเดียวกัน ไม่มีต้นทุนซื้อขายหรือภาษี เปิด Notebook ใหม่และรันจากต้นหน้าได้ด้วย NumPy, pandas และ SciPy [ดาวน์โหลด Notebook](notebooks/covariance-shrinkage.ipynb)

<span id="sample-covariance-start"></span>

## เริ่มจากสิ่งที่ sample covariance บอกเรา

ให้ $R_{t,i}$ เป็นผลตอบแทนสินทรัพย์ $i$ ในเดือน $t$ และมีข้อมูลครบ $T$ เดือน เราใช้ sample covariance แบบหารด้วย $T-1$:

$$
S_{ij}=\frac{1}{T-1}\sum_{t=1}^{T}
(R_{t,i}-\bar R_i)(R_{t,j}-\bar R_j).
$$

ขีดบนหมายถึงค่าเฉลี่ยตามเวลา ถ้า $i=j$ เรากำลังคูณความเบี่ยงเบนของสินทรัพย์ตัวเดียวกัน จึงได้ variance บนแนวทแยง ส่วนช่องนอกแนวทแยงวัดว่าผลตอบแทนสองตัวเบี่ยงจากค่าเฉลี่ยไปด้วยกันเพียงใด เมทริกซ์นี้สมมาตร เพราะ $S_{ij}=S_{ji}$

ตัวอย่างมีแปดเดือนและสินทรัพย์ A/B/C ค่า `0.02` คือผลตอบแทน 2% และ `-0.02` คือ −2% ไม่ใช่ราคาสินทรัพย์

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize

shrink_toy = pd.DataFrame({
    "A": [-0.02, 0.01, 0.03, -0.01, 0.02, 0.00, 0.01, -0.02],
    "B": [-0.01, 0.02, 0.01, -0.02, 0.04, -0.01, 0.00, 0.01],
    "C": [0.01, -0.02, 0.02, 0.00, 0.01, 0.03, -0.01, 0.00]
}, index=pd.period_range("2025-01", periods=8, freq="M"))
shrink_S = shrink_toy.cov(ddof=1)
print("Sample covariance, monthly decimal returns squared:")
print(shrink_S.round(6).to_string())
print("Monthly SD (%):", (shrink_toy.std(ddof=1) * 100).round(4).to_dict())
```

`cov(ddof=1)` คำนวณ covariance ของคอลัมน์โดยใช้ตัวหาร $8-1=7$ ส่วน `std(ddof=1)` ถอดรากของ variance เพื่อกลับมาอ่านเป็น SD รายเดือน ได้ A ประมาณ 1.8323%, B 1.9272% และ C 1.6036%

ลองตรวจช่อง A/B ด้วยมือ ค่าเฉลี่ย A เท่ากับ 0.0025 และ B เท่ากับ 0.005 ผลรวมของ $(R_A-0.0025)(R_B-0.005)$ ทั้งแปดเดือนเท่ากับ 0.0014 เมื่อหารด้วย 7 จึงได้ $S_{AB}=0.0002$ หน่วยของ covariance คือผลตอบแทนทศนิยมรายเดือนยกกำลังสอง เราไม่นำตัวเลขนี้ไปอ่านว่าเป็นผลตอบแทน 0.02% ของพอร์ต

ตัวเลขในตารางยังเป็นค่าประมาณจากแปดเดือน เราไม่รู้ covariance ของกระบวนการที่อาจสร้างผลตอบแทนในอนาคต แม้เพิ่มจำนวนเดือนก็ยังต้องพิจารณาว่าสภาวะในอดีตเหมาะจะใช้แทนช่วงที่จะลงทุนหรือไม่

<span id="constant-correlation-target"></span>

## ยืมโครงสร้างจาก Constant Correlation

เราจะสร้างเมทริกซ์เป้าหมาย $F$ โดยเก็บ variance ของแต่ละสินทรัพย์ตาม sample แต่ให้ทุกคู่มี correlation เท่ากับค่าเฉลี่ยเดียวกัน วิธีนี้เรียกว่า [constant-correlation target](glossary.html#constant-correlation) คำว่า constant ในที่นี้หมายถึงทุกคู่ในเมทริกซ์เดียวกันใช้ค่าเดียวกัน เมื่อเลื่อนช่วงข้อมูลแล้วประมาณใหม่ ค่านั้นเปลี่ยนตามเวลาได้

### เฉลี่ย correlation โดยไม่รวมแนวทแยง

จากความสัมพันธ์ $S_{ij}=\rho_{ij}s_i s_j$ เราคำนวณ correlation ได้โดยหาร covariance ด้วย SD ของทั้งสองตัว สำหรับสินทรัพย์ $N$ ตัว ค่าเฉลี่ยของคู่ที่ไม่ซ้ำคือ

$$
\bar\rho=\frac{2}{N(N-1)}\sum_{i<j}\hat\rho_{ij}.
$$

กรณีสามสินทรัพย์มีคู่ A/B, A/C และ B/C รวมสามคู่ เราไม่รวม correlation ของสินทรัพย์กับตัวเอง ซึ่งเท่ากับหนึ่ง และไม่จำเป็นต้องนับ B/A ซ้ำกับ A/B

```python
shrink_corr = shrink_toy.corr()
shrink_n = shrink_toy.shape[1]
shrink_pairs = np.triu_indices(shrink_n, k=1)
shrink_rho = shrink_corr.to_numpy()[shrink_pairs].mean()
print(shrink_corr.round(6).to_string())
print(f"Mean of the three distinct correlations: {shrink_rho:.6f}")
print("Equivalent all-off-diagonal formula:",
      np.isclose(shrink_rho, (shrink_corr.to_numpy().sum() - shrink_n)
                 / (shrink_n * (shrink_n - 1))))
```

`np.triu_indices(3, k=1)` สร้างตำแหน่งที่อยู่เหนือแนวทแยงหนึ่งชั้นขึ้นไป เมื่อนำมาเลือกค่าจาก array จะเหลือสามคู่ที่ต้องการ ได้ประมาณ 0.566379, 0.097243 และ −0.184900 ดังนั้น

$$
\bar\rho=\frac{0.566379+0.097243-0.184900}{3}
\approx0.159574.
$$

อีกสูตรในโค้ดรวมทุกช่องของ correlation matrix แล้วลบ $N$ เพื่อตัดเลขหนึ่งบนแนวทแยงออก จากนั้นหารด้วย $N(N-1)$ สูตรนี้นับแต่ละคู่สองครั้งทั้งในตัวเศษและตัวหาร จึงได้ค่าเฉลี่ยเดียวกัน `np.isclose` ตรวจความเท่ากันโดยยอมให้มีความต่างเล็กน้อยจากเลขทศนิยม

### เปลี่ยนกลับเป็น covariance ของแต่ละคู่

นิยาม target เป็น

$$
F_{ii}=S_{ii},\qquad
F_{ij}=\bar\rho\,s_i s_j\quad(i\ne j).
$$

แม้ correlation เท่ากันทุกคู่ แต่ covariance ยังต่างกันตาม SD ของสินทรัพย์ทั้งสองตัว เราจึงต้องสร้าง correlation matrix ก่อน แล้วคูณ $s_i s_j$ ให้ถูกช่อง

```python
shrink_sd = shrink_toy.std(ddof=1).to_numpy()
shrink_target_corr = np.full((shrink_n, shrink_n), shrink_rho)
np.fill_diagonal(shrink_target_corr, 1.0)
shrink_F = pd.DataFrame(
    shrink_target_corr * np.outer(shrink_sd, shrink_sd),
    index=shrink_toy.columns, columns=shrink_toy.columns
)
print("Constant-correlation target:")
print(shrink_F.round(6).to_string())
print(f"F[A,B] = {shrink_rho:.6f} × {shrink_sd[0]:.6f} × {shrink_sd[1]:.6f}")
print(f"F[A,B] = {shrink_F.loc['A', 'B']:.8f}")
assert np.allclose(np.diag(shrink_F), np.diag(shrink_S))
```

`np.full((N, N), value)` สร้าง array ขนาด $N\times N$ ที่ใส่ค่าเดียวกันทุกช่อง และ `np.fill_diagonal(..., 1.0)` เปลี่ยนแนวทแยงเป็นหนึ่ง ส่วน `np.outer(shrink_sd, shrink_sd)` สร้างตารางผลคูณ SD ทุกคู่ เครื่องหมาย `*` คูณสอง array ตามตำแหน่งเดียวกัน

ในช่อง A/B เราได้ $0.159574\times0.018323\times0.019272\approx0.00005635$ ลดจาก sample ที่ 0.00020000 ส่วนช่อง B/C เปลี่ยนจากประมาณ −0.00005714 เป็น +0.00004932 เพราะ target ใช้ correlation เฉลี่ยที่เป็นบวก โครงสร้างนี้จึงอาจลดหรือเพิ่ม covariance และอาจเปลี่ยนเครื่องหมายด้วย

การบังคับ correlation ให้เท่ากันเป็นข้อสมมติ ถ้าหุ้นในอุตสาหกรรมเดียวกันเคลื่อนไหวร่วมกันแรงกว่าหุ้นข้ามอุตสาหกรรมจริง ๆ target นี้จะลบความต่างบางส่วนทิ้ง อีกทั้ง $F$ ยังใช้ SD และ correlation เฉลี่ยที่ประมาณจากข้อมูล จึงยังมีความคลาดเคลื่อนจาก sample อยู่

<span id="shrinkage-weight"></span>

## ผสมสองเมทริกซ์ด้วยค่า δ

เรากำหนดตัวประมาณ shrinkage เป็น

$$
\widehat\Sigma_\delta=\delta F+(1-\delta)S,
\qquad 0\leq\delta\leq1.
$$

$\delta$ อ่านว่า delta เป็นน้ำหนักของ target ในเมทริกซ์ที่ผสมแล้ว ส่วน $1-\delta$ เป็นน้ำหนักของ sample covariance เมื่อได้เมทริกซ์นี้ เราจึงค่อยหาน้ำหนักลงทุน $w$ อีกขั้น

| ค่า δ | เมทริกซ์ที่ใช้ |
|---|---|
| 0 | Sample covariance $S$ ทั้งหมด |
| 0.5 | ค่าเฉลี่ยระหว่าง $S$ และ $F$ ทีละช่อง |
| 1 | Constant-correlation target $F$ ทั้งหมด |

เลือก $\delta=0.5$ สำหรับตัวอย่างนี้ ช่อง A/B จึงเท่ากับ $0.5(0.00005635)+0.5(0.00020000)\approx0.00012817$ แนวทแยงยังคงเดิม เพราะ $S$ กับ $F$ ใช้ variance เดียวกันอยู่แล้ว

```python
shrink_delta = 0.5
shrink_mix = shrink_delta * shrink_F + (1 - shrink_delta) * shrink_S
shrink_diagnostics = []
for delta in [0.0, 0.5, 1.0]:
    matrix = delta * shrink_F + (1 - delta) * shrink_S
    shrink_diagnostics.append({
        "Delta": delta,
        "Cov(A,B)": matrix.loc["A", "B"],
        "Cov(B,C)": matrix.loc["B", "C"],
        "Smallest eigenvalue": np.linalg.eigvalsh(matrix).min()
    })
print(pd.DataFrame(shrink_diagnostics).set_index("Delta").to_string(
    float_format=lambda value: f"{value:.8f}"
))
assert np.allclose(0 * shrink_F + shrink_S, shrink_S)
assert np.allclose(shrink_F + 0 * shrink_S, shrink_F)
```

ค่าของช่อง B/C หลังผสมอยู่ประมาณ −0.00000391 ระหว่าง sample ที่ติดลบกับ target ที่เป็นบวก คำว่า shrink ในกรณีนี้หมายถึงดึง correlation แต่ละคู่เข้าหาค่าเฉลี่ยที่กำหนด ไม่ได้หมายความว่าทุกช่องต้องเล็กลงในเชิงค่าสัมบูรณ์หรือถูกดึงเข้าหาศูนย์

### ความคลาดเคลื่อนจากการสุ่มกับความคลาดเคลื่อนจากโครงสร้าง

ถ้าเก็บข้อมูลใหม่จากกระบวนการเดียวกันหลายครั้ง ค่า covariance ที่ประมาณได้จะเปลี่ยนไป ความแกว่งของตัวประมาณนี้เป็นด้านหนึ่งของ [estimation error](glossary.html#estimation-error) เมทริกซ์ที่ยอมให้แต่ละคู่เปลี่ยนอย่างอิสระอาจตามความบังเอิญในข้อมูลมาก โดยเฉพาะเมื่อจำนวนสินทรัพย์มากเมื่อเทียบกับจำนวนเดือน

การใช้โครงสร้างร่วมกันอาจทำให้ค่าประมาณแกว่งน้อยลง แต่ถ้าโครงสร้างต่างจากความสัมพันธ์จริง ค่าเฉลี่ยของตัวประมาณเมื่อทำซ้ำอาจห่างจากค่าจริง เราเรียกส่วนนี้ว่า bias การเลือก $\delta$ จึงเกี่ยวข้องกับทั้ง variance ของตัวประมาณและ bias จาก target ไม่ใช่การเลือกว่าเมทริกซ์ใดดูเรียบกว่าบนหน้าจอ

เราไม่ทราบ covariance จริงเมื่อทำงานกับข้อมูลตลาด การลดความแตกต่างระหว่างช่องในเมทริกซ์ไม่ได้ยืนยันว่าความเสี่ยงพอร์ตในอนาคตจะลดลง ต้องประเมินผลกับข้อมูลที่ยังไม่ใช้เลือกวิธี รวมถึงตรวจข้อสมมติของ target ด้วย

### ค่า 0.5 ในบทนี้ต่างจาก Ledoit–Wolf อย่างไร

Lab ของคอร์สกำหนด $\delta=0.5$ เพื่อสาธิตการผสมตัวประมาณ บทนี้ใช้วิธีเดียวกันในส่วนการเลือกค่า delta โดยกำหนดไว้ก่อนดูผลทดลอง เราไม่ได้คำนวณ shrinkage intensity ด้วยสูตร Ledoit–Wolf และไม่ได้ค้นหาค่า delta ที่ทำให้ผลย้อนหลังดีที่สุด

งานของ [Olivier Ledoit และ Michael Wolf](https://ledoit.net/honey_abstract.htm) เสนอการประมาณ shrinkage intensity จากข้อมูล ภายใต้ target และเกณฑ์ความคลาดเคลื่อนที่กำหนด ค่าที่คำนวณจึงขึ้นกับข้อมูลและวิธีประมาณ แทนการตั้งเป็น 0.5 เสมอ

ชื่อไลบรารีก็ต้องอ่านให้ครบ [เอกสาร `sklearn.covariance.LedoitWolf`](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html) ระบุ target เป็น $\mu I$ โดย $\mu=\operatorname{tr}(S)/N$ หรือ variance เฉลี่ยบนแนวทแยง เมทริกซ์นี้มี covariance นอกแนวทแยงเป็นศูนย์และ variance ทุกตัวเท่ากัน จึงต่างจาก constant-correlation target ที่เราสร้าง ซึ่งเก็บ variance ของแต่ละสินทรัพย์ไว้ การเทียบผลต้องระบุทั้ง target, วิธีเลือก delta และตัวหารของ covariance

<span id="shrinkage-psd"></span>

## ตรวจว่าเมทริกซ์ให้ variance ที่มีความหมาย

สำหรับน้ำหนักพอร์ต $w$ ความแปรปรวนที่คำนวณจากเมทริกซ์คือ $w^\mathsf{T}\Sigma w$ ค่า variance ต้องไม่ติดลบ เมทริกซ์สมมาตรที่ให้เงื่อนไขนี้กับเวกเตอร์ $w$ ทุกตัวเรียกว่า [positive semidefinite หรือ PSD](glossary.html#positive-semidefinite) หากได้ค่าบวกเสมอสำหรับ $w\ne0$ จะเรียกว่า positive definite หรือ PD

คอลัมน์ `Smallest eigenvalue` ในตารางก่อนหน้าใช้ `np.linalg.eigvalsh` ซึ่งคำนวณ eigenvalues ของเมทริกซ์สมมาตร สำหรับการตรวจนี้ให้ดูเครื่องหมาย: ทุกค่าต้องไม่ติดลบจึงเป็น PSD และต้องบวกทุกค่าจึงเป็น PD ค่าเล็กระดับใกล้ศูนย์อาจเกิดจากความละเอียดของคอมพิวเตอร์ได้ ส่วนค่าลบที่มีขนาดชัดเจนต้องตรวจข้อมูลหรือวิธีสร้างเมทริกซ์

ทั้ง $S$, $F$ และเมทริกซ์ผสมในตัวอย่างเล็กเป็น PD ถ้า $S$ กับ $F$ เป็น PSD และ $0\leq\delta\leq1$ เมทริกซ์ผสมก็เป็น PSD เพราะสำหรับทุก $w$:

$$
w^\mathsf{T}\widehat\Sigma_\delta w
=\delta\,w^\mathsf{T}Fw+(1-\delta)\,w^\mathsf{T}Sw\geq0.
$$

หาก $F$ เป็น PD และ $\delta>0$ ความแปรปรวนข้างต้นจะเป็นบวกสำหรับ $w\ne0$ จึงได้ PD ด้วย แต่ shrinkage ไม่ได้แก้เมทริกซ์ singular ได้ทุกกรณี เช่น ถ้าทุกสินทรัพย์มีผลตอบแทนเหมือนกันทุกเดือน correlation ทุกคู่เป็นหนึ่ง ทั้ง sample และ target นี้จะยังมีความซ้ำซ้อนอยู่

<details>
<summary>อ่านเพิ่ม: ทำไมค่าเฉลี่ย correlation จึงสร้าง target ที่เป็น PSD ได้</summary>

ให้ $D$ เป็นเมทริกซ์แนวทแยงของ SD และ $\mathbf1$ เป็นเวกเตอร์เลขหนึ่ง target เขียนได้ว่า

$$
F=D\left[(1-\bar\rho)I+\bar\rho\mathbf1\mathbf1^\mathsf{T}\right]D.
$$

เมทริกซ์ correlation ในวงเล็บมี eigenvalues $1-\bar\rho$ จำนวน $N-1$ ค่า และ $1+(N-1)\bar\rho$ อีกหนึ่งค่า จึงเป็น PSD เมื่อ $-1/(N-1)\leq\bar\rho\leq1$ ค่าเฉลี่ยนอกแนวทแยงจาก correlation matrix ที่เป็น PSD จะอยู่ในช่วงนี้ ถ้าอสมการทั้งสองเป็นแบบเข้มงวดและ SD ทุกตัวเป็นบวก target จะเป็น PD

ข้อสรุปนี้ใช้กับ correlation ที่คำนวณจากชุด observations เดียวกันครบทุกสินทรัพย์ การคำนวณแต่ละคู่จากเดือนคนละชุดเพราะข้อมูลขาดหายอาจทำให้เมทริกซ์ที่ได้ไม่เป็น PSD

</details>

ตาม[เอกสาร pandas](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.cov.html) การคำนวณแบบ pairwise ซึ่งตัดค่าขาดหายแยกแต่ละคู่อาจไม่ให้เมทริกซ์ PSD เราจึงกำหนดให้ตัวอย่างต่อไปใช้ข้อมูลครบชุดเดียวกัน และหยุดเมื่อพบค่าขาดหาย การเติมศูนย์เองจะเปลี่ยนความหมายเป็นเดือนที่สินทรัพย์มีผลตอบแทนศูนย์

<span id="shrinkage-estimator-functions"></span>

## รวมขั้นตอนเป็นฟังก์ชัน แล้วหาพอร์ต GMV

ฟังก์ชัน `estimate_covariance` รับตารางผลตอบแทนหนึ่งช่วงและชื่อวิธี เราจะเรียกฟังก์ชันเดียวกันซ้ำกับหน้าต่างข้อมูลต่าง ๆ โดยไม่ต้องคัดลอกสูตรทุกครั้ง

```python
def estimate_covariance(history, method="sample", delta=0.5):
    values = history.to_numpy(dtype=float)
    if values.shape[0] < 2 or values.shape[1] < 2:
        raise ValueError("Need at least two observations and two assets")
    if not np.isfinite(values).all():
        raise ValueError("Use one complete, finite observation set")
    sample = history.cov(ddof=1).to_numpy()
    sd = np.sqrt(np.diag(sample))
    if (sd <= 0).any():
        raise ValueError("Each asset must have positive sample variance")
    if method == "sample":
        return sample
    correlations = sample / np.outer(sd, sd)
    n_assets = len(sd)
    mean_correlation = correlations[np.triu_indices(n_assets, k=1)].mean()
    target_correlation = np.full_like(sample, mean_correlation)
    np.fill_diagonal(target_correlation, 1.0)
    target = target_correlation * np.outer(sd, sd)
    if method == "constant-correlation":
        return target
    if method == "shrink" and np.isfinite(delta) and 0 <= delta <= 1:
        return delta * target + (1 - delta) * sample
    raise ValueError("Unknown method or shrinkage delta outside [0, 1]")

assert np.allclose(estimate_covariance(shrink_toy, "shrink"), shrink_mix)
print("Step-by-step and reusable estimator agree")
```

`method` เลือกว่าจะคืน sample, constant correlation หรือเมทริกซ์ผสม ส่วน `delta` ใช้เมื่อเลือก `"shrink"` ค่าเริ่มต้น 0.5 เขียนไว้ในวงเล็บหลังชื่อฟังก์ชัน ผู้เรียกสามารถส่งค่าอื่นระหว่าง 0 กับ 1 ได้

`np.isfinite` ตรวจว่าทุกช่องเป็นตัวเลขที่มีขอบเขต ไม่เป็น NaN หรือ infinity ส่วน `.all()` กำหนดให้ทุกช่องผ่านเงื่อนไข หากสินทรัพย์มี variance เป็นศูนย์ correlation จะคำนวณโดยหารศูนย์ ฟังก์ชันจึงให้แก้การจัดการสินทรัพย์นั้นก่อน บทนี้ยังไม่รวมสินทรัพย์ปลอดความเสี่ยงไว้ในเมทริกซ์ของสินทรัพย์เสี่ยง

### คงโจทย์หาน้ำหนัก แล้วเปลี่ยนเฉพาะ covariance

Global Minimum Variance หรือ GMV ในบทนี้เลือกน้ำหนักให้ variance ต่ำที่สุดภายใต้ข้อจำกัด

$$
\min_w\;w^\mathsf{T}\widehat\Sigma w,
\qquad \sum_iw_i=1,\qquad 0\leq w_i\leq1.
$$

ข้อจำกัดหมายถึงลงทุนเต็มจำนวน ไม่มีการขายชอร์ตหรือกู้เพิ่มเพื่อซื้อสินทรัพย์ การหา GMV ไม่ต้องใส่ expected return เราจึงแยกการเปรียบเทียบ covariance estimator ออกจากปัญหาประมาณค่าเฉลี่ยผลตอบแทนได้ หากต้องการพื้นฐานการใช้ optimizer อ่าน[การสร้าง Efficient Frontier](efficient-frontier.html)ประกอบ

```python
def gmv_weights(covariance):
    covariance = np.asarray(covariance, dtype=float)
    if covariance.ndim != 2 or covariance.shape[0] == 0:
        raise ValueError("Need a nonempty covariance matrix")
    n_assets = covariance.shape[0]
    if covariance.shape != (n_assets, n_assets) or not np.isfinite(covariance).all():
        raise ValueError("Need a finite square covariance matrix")
    if not np.allclose(covariance, covariance.T, atol=1e-12):
        raise ValueError("Covariance must be symmetric")
    if np.linalg.eigvalsh(covariance).min() < -1e-12:
        raise ValueError("Covariance must be positive semidefinite")
    scale = np.trace(covariance) / n_assets
    if scale <= 0:
        raise ValueError("Need positive average variance")
    scaled_cov = covariance / scale
    result = minimize(
        lambda w: w @ scaled_cov @ w,
        np.full(n_assets, 1 / n_assets),
        jac=lambda w: 2 * scaled_cov @ w,
        method="SLSQP", bounds=[(0, 1)] * n_assets,
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1,
                     "jac": lambda w: np.ones_like(w)},
        options={"ftol": 1e-12, "maxiter": 500}
    )
    if not result.success:
        raise RuntimeError(result.message)
    weights = result.x
    if (abs(weights.sum() - 1) > 1e-8
            or weights.min() < -1e-8 or weights.max() > 1 + 1e-8):
        raise RuntimeError("Solver returned infeasible weights")
    return weights

shrink_toy_weights = pd.DataFrame({
    "Sample": gmv_weights(shrink_S),
    "CC": gmv_weights(shrink_F),
    "Shrink 0.5": gmv_weights(shrink_mix),
    "EW": np.full(3, 1 / 3)
}, index=shrink_toy.columns)
print((shrink_toy_weights * 100).round(4).to_string())
```

`lambda w: ...` สร้างฟังก์ชันสั้น ๆ สำหรับ objective และ gradient ส่วน `jac` ส่งความชันให้ SLSQP เราหาร covariance ด้วย variance เฉลี่ยบนแนวทแยงเพื่อให้ขนาดตัวเลขเหมาะกับตัวหาคำตอบ การหารด้วยค่าบวกเดียวกันทั้งเมทริกซ์ไม่เปลี่ยนน้ำหนักที่ทำให้ variance ต่ำสุด

`bounds` บังคับน้ำหนักแต่ละตัวอยู่ระหว่าง 0 กับ 1 และ `constraints` บังคับผลรวมเป็นหนึ่ง หลังคำนวณต้องตรวจทั้ง `result.success` และความเป็นไปได้ของน้ำหนัก คำว่า success หมายถึงโปรแกรมจบตามเงื่อนไขการคำนวณ ไม่ได้รับรองว่า covariance ที่ป้อนเข้าไปเป็นค่าความเสี่ยงจริง ดูพารามิเตอร์ใน[เอกสาร SciPy SLSQP](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)

ผลของตัวอย่างเล็กเป็นเปอร์เซ็นต์เงินลงทุน:

| สินทรัพย์ | Sample GMV | CC GMV | Shrink δ = 0.5 | Equal Weight |
|---|---:|---:|---:|---:|
| A | 10.5793 | 30.4988 | 23.2711 | 33.3333 |
| B | 35.3904 | 26.7117 | 28.1675 | 33.3333 |
| C | 54.0302 | 42.7895 | 48.5613 | 33.3333 |

Sample ให้น้ำหนัก C มากกว่าอีกสองวิธี เพราะใช้ทั้ง SD ที่ต่ำกว่าและรูปแบบ covariance รายคู่จากแปดเดือน เมื่อนำ correlation ไปใกล้ค่าเฉลี่ย น้ำหนักที่คำนวณก็เปลี่ยนตาม แต่เราเพิ่งเลือกพอร์ตจากข้อมูลที่ใช้ประมาณ จึงยังไม่ทราบว่าพอร์ตใดจะผันผวนน้อยที่สุดในเดือนถัดไป

น้ำหนักจาก shrinkage ไม่จำเป็นต้องเท่ากับค่าเฉลี่ยของน้ำหนัก Sample GMV กับ CC GMV แม้ใช้ $\delta=0.5$ เพราะการหาน้ำหนักที่ทำให้ variance ต่ำสุดเป็นอีกปัญหาหนึ่งที่มีข้อจำกัด

<span id="rolling-gmv-experiment"></span>

## ทดลองเลือกน้ำหนักก่อนเห็นผลตอบแทนเดือนถัดไป

เราสร้างข้อมูล 96 เดือนของสินทรัพย์ A–H สินทรัพย์ทุกตัวได้รับ shock ร่วมจากตลาด แต่ตอบสนองต่างกัน จากนั้นเพิ่ม shock ของกลุ่ม A–D กับ E–H แยกกัน และ shock เฉพาะสินทรัพย์ เป้าหมายคือให้มีทั้งความสัมพันธ์ร่วมและโครงสร้างกลุ่มที่ constant correlation อาจอธิบายได้ไม่ครบ

ตัวเลขสุ่มถูกสร้างเป็น log returns ก่อนใช้ `np.expm1(x)` แปลงเป็น simple return $e^x-1$ ดังนั้นผลตอบแทนที่ส่งให้ backtest จึงมากกว่า −100% ข้อมูลนี้ไม่มีบริษัทหรือช่วงตลาดจริงอยู่เบื้องหลัง ป้ายปี 2010–2017 ใช้แสดงลำดับเดือนเท่านั้น

```python
shrink_rng = np.random.default_rng(20261003)
shrink_months = pd.period_range("2010-01", periods=96, freq="M")
shrink_assets = list("ABCDEFGH")
shrink_market = shrink_rng.normal(0, 0.025, size=(96, 1))
shrink_sectors = shrink_rng.normal(0, 0.020, size=(96, 2))
shrink_groups = np.repeat([0, 1], 4)
shrink_loadings = np.array([0.8, 1.0, 1.2, 0.9, 0.7, 1.1, 0.95, 1.3])
shrink_specific_sd = np.array([0.020, 0.025, 0.035, 0.030, 0.018, 0.022, 0.028, 0.040])
shrink_specific = shrink_rng.normal(0, shrink_specific_sd, size=(96, 8))
shrink_logs = (0.003 + shrink_market * shrink_loadings
               + shrink_sectors[:, shrink_groups] + shrink_specific)
shrink_returns = pd.DataFrame(np.expm1(shrink_logs), index=shrink_months, columns=shrink_assets)
print("Return rows and assets:", shrink_returns.shape)
print("Minimum simple return:", round(shrink_returns.to_numpy().min(), 6))
```

`default_rng(20261003)` กำหนด seed ให้สร้างชุดเดิมซ้ำได้ `size=(96, 1)` หมายถึง 96 เดือนของ shock ตลาดหนึ่งชุด และ `size=(96, 8)` หมายถึง 96 เดือนของแปดสินทรัพย์ ค่า SD ของ log shock ทั้งหมดเป็นหน่วยต่อเดือน ตัวอย่างเช่น `0.025` คือ 2.5% ต่อเดือนของ shock ตลาดก่อนคูณ loading

`shrink_groups` มีค่า `[0, 0, 0, 0, 1, 1, 1, 1]` จึงเลือก shock กลุ่มเดียวกันให้สี่สินทรัพย์แรก และอีกกลุ่มให้สี่สินทรัพย์หลัง ส่วน `shrink_specific_sd` กำหนดขนาด shock เฉพาะตัวต่างกัน การบวกและคูณ array ที่มีขนาดเข้ากันทำให้ NumPy คำนวณทุกเดือนและทุกสินทรัพย์พร้อมกัน

ได้ตารางขนาด 96 × 8 ผลตอบแทนต่ำสุดของชุดที่สุ่มได้ประมาณ −13.5792% รูปแบบความสัมพันธ์และพารามิเตอร์ของการสร้างข้อมูลคงที่ตลอดการทดลอง จึงไม่ได้ครอบคลุมการเปลี่ยนสภาวะตลาดหรือวิกฤตทุกแบบ

### ใช้ 36 เดือนย้อนหลัง แล้วถือหนึ่งเดือน

กำหนดขั้นตอนล่วงหน้าให้ทุกวิธีใช้ช่วงเวลาเดียวกัน:

1. ก่อนเดือน $t$ เริ่ม ใช้ผลตอบแทนตั้งแต่ $t-36$ ถึง $t-1$ ประมาณ covariance
2. หาน้ำหนัก GMV จาก Sample, Constant Correlation และ Shrink δ = 0.5 ส่วน EW ใช้น้ำหนัก $1/8$ ทุกตัว
3. ลงทุนตามสัดส่วนต้นงวด แล้วถือสินทรัพย์โดยไม่ปรับระหว่างเดือน $t$ ผลตอบแทนพอร์ตจึงเท่ากับ $w_t^\mathsf{T}R_t$
4. หลังเดือนจบ น้ำหนักไหลตามผลตอบแทน จากนั้นประมาณและปรับใหม่ก่อนเดือนถัดไป

ไม่มีการขายซื้อระหว่างเดือน และไม่มีต้นทุนในการทดลองนี้ เราจะวัด one-way turnover เพิ่ม เพื่อเห็นปริมาณการเปลี่ยนพอร์ต หากจะคิดค่าธรรมเนียมต้องระบุฐานค่าธรรมเนียมและหักเงินจริงตามขั้นตอน เช่นใน[ตัวอย่าง Smart Beta](smart-beta.html)

```python
def rolling_gmv(returns, window=36, shrink_delta=0.5):
    if (not returns.index.is_unique or not returns.index.is_monotonic_increasing
            or not returns.columns.is_unique or not isinstance(window, (int, np.integer))
            or window < 2 or len(returns) <= window):
        raise ValueError("Need ordered unique dates and enough history")
    expected_dates = pd.period_range(returns.index[0], periods=len(returns), freq="M")
    if not returns.index.equals(expected_dates):
        raise ValueError("Need a complete monthly PeriodIndex")
    if not np.isfinite(returns.to_numpy()).all() or (returns <= -1).any().any():
        raise ValueError("Need complete simple returns greater than -100%")
    if not np.isfinite(shrink_delta) or not 0 <= shrink_delta <= 1:
        raise ValueError("Shrinkage delta must be finite and in [0, 1]")
    methods = {"Sample GMV": "sample", "CC GMV": "constant-correlation",
               f"Shrink {shrink_delta:g}": "shrink"}
    names = list(methods) + ["EW"]
    weight_rows = {name: [] for name in names}
    previous_drift = {name: None for name in names}
    return_rows, turnover_rows = [], []
    for t in range(window, len(returns)):
        history = returns.iloc[t - window:t]
        held_returns = returns.iloc[t].to_numpy()
        weights = {name: gmv_weights(estimate_covariance(history, method, shrink_delta))
                   for name, method in methods.items()}
        weights["EW"] = np.full(returns.shape[1], 1 / returns.shape[1])
        one_return, one_turnover = {}, {}
        for name, w in weights.items():
            one_return[name] = float(w @ held_returns)
            one_turnover[name] = (0.0 if previous_drift[name] is None
                                  else float(np.abs(w - previous_drift[name]).sum() / 2))
            previous_drift[name] = w * (1 + held_returns) / (1 + one_return[name])
            weight_rows[name].append(w)
        return_rows.append(one_return)
        turnover_rows.append(one_turnover)
    dates = returns.index[window:]
    return (pd.DataFrame(return_rows, index=dates),
            {name: pd.DataFrame(rows, index=dates, columns=returns.columns)
             for name, rows in weight_rows.items()},
            pd.DataFrame(turnover_rows, index=dates))
```

บรรทัด `returns.iloc[t - window:t]` เลือก 36 แถวก่อนตำแหน่ง `t` โดยไม่รวมแถว `t` ส่วน `returns.iloc[t]` คือผลตอบแทนเดือนที่เพิ่งนำเงินไปถือ ฟังก์ชันรับ `PeriodIndex` รายเดือนที่ต่อเนื่อง และตรวจข้อมูลที่ขาดหายก่อนเริ่ม เพื่อไม่ให้คำว่า 36 แถวหมายถึงจำนวนเดือนที่ต่างกันโดยไม่รู้ตัว

`methods` เป็น dictionary ที่จับคู่ชื่อกลยุทธ์กับชื่อ estimator และ `.items()` ส่งแต่ละคู่ให้ loop ส่วน `weight_rows` เก็บน้ำหนักต้นงวดของทุกเดือน เพื่อเปิดตรวจภายหลังได้ ฟังก์ชันคืนผลสามชิ้นตามลำดับ: ตารางผลตอบแทน, dictionary ของตารางน้ำหนัก และตาราง turnover

สำหรับการวัด turnover เราเก็บน้ำหนักปลายงวดที่ไหลตามราคาไว้ใน `previous_drift`:

$$
\widetilde w_{i,t}=\frac{w_{i,t}(1+R_{i,t})}{1+R_{p,t}},\qquad
\mathrm{Turnover}_{t+1}=\frac12\sum_i|w_{i,t+1}-\widetilde w_{i,t}|.
$$

การนำเป้าหมายเดือนนี้ลบเป้าหมายเดือนก่อนตรง ๆ จะข้ามการเปลี่ยนน้ำหนักจากราคา แม้ EW ตั้งเป้าหมาย 12.5% เหมือนเดิมทุกเดือน ก็ยังต้องซื้อขายเพื่อกลับจากน้ำหนักที่ไหลไปแล้ว ตัวอย่างบันทึก turnover วันเริ่มลงทุนเป็นศูนย์ และรายงานค่าเฉลี่ยเฉพาะการปรับครั้งถัด ๆ ไป

```python
shrink_window = 36
shrink_backtest, shrink_weights, shrink_turnover = rolling_gmv(shrink_returns, window=shrink_window)
print("First training interval:", shrink_returns.index[0], "to", shrink_returns.index[35])
print("First held month:", shrink_backtest.index[0], "Held months:", len(shrink_backtest))
print("First held-month weights (%):")
print(pd.DataFrame({name: weights.iloc[0] * 100 for name, weights in shrink_weights.items()}).round(4).to_string())
print("First two held-month returns (%):")
print((shrink_backtest.head(2) * 100).round(4).to_string())
```

ช่วงประมาณครั้งแรกคือมกราคม 2010 ถึงธันวาคม 2012 และเดือนที่ถือครั้งแรกคือมกราคม 2013 จึงเหลือผลตอบแทนทดสอบ 60 เดือน ตารางน้ำหนักแถวแรกเป็นคำตอบที่เลือกก่อนใช้ผลตอบแทนเดือนมกราคม 2013

Sample GMV ให้น้ำหนัก A ประมาณ 20.7748% ขณะที่ CC GMV ให้ 16.3596% และ Shrink 0.5 ให้ 20.1873% น้ำหนักบางตัวเป็นศูนย์เพราะข้อจำกัด long-only ทำงานอยู่ ส่วน EW เริ่มที่ 12.5% ทุกตัว ตารางผลตอบแทนสองเดือนแรกเป็นผลที่เกิดขึ้นหลังนำน้ำหนักของแต่ละเดือนไปคูณกับผลตอบแทนสินทรัพย์

<span id="shrinkage-backtest-results"></span>

## อ่านผลนอกช่วงประมาณ โดยเก็บเงินเริ่มต้นไว้ด้วย

ให้แต่ละวิธีเริ่มด้วยมูลค่า 1 ก่อนเดือนมกราคม 2013 แล้วทบผลตอบแทนรายเดือน เราเพิ่มแถวเงินเริ่มต้นก่อนคำนวณ drawdown เพื่อให้การขาดทุนตั้งแต่เดือนแรกถูกนับด้วย

```python
shrink_wealth = pd.concat([
    pd.DataFrame(1.0, index=[shrink_backtest.index[0] - 1], columns=shrink_backtest.columns),
    (1 + shrink_backtest).cumprod()
])
shrink_drawdown = shrink_wealth / shrink_wealth.cummax() - 1
shrink_summary = pd.DataFrame({
    "Total return (%)": (shrink_wealth.iloc[-1] - 1) * 100,
    "Monthly SD (%)": shrink_backtest.std(ddof=1) * 100,
    "Max drawdown (%)": shrink_drawdown.min() * 100,
    "Mean turnover after entry (%)": shrink_turnover.iloc[1:].mean() * 100
})
print(shrink_summary.round(4).to_string())
```

`cumprod()` คูณตัวคูณ $1+R$ สะสม ส่วน `cummax()` เก็บมูลค่าสูงสุดที่เคยเกิดขึ้นถึงแต่ละเดือน เมื่อนำมูลค่าปัจจุบันหารด้วยค่าสูงสุดแล้วลบหนึ่งจะได้ drawdown แบบติดลบ คอลัมน์ `Max drawdown (%)` จึงใช้ค่าต่ำสุดของแต่ละเส้นทาง

| วิธี | ผลตอบแทนรวม 60 เดือน (%) | SD รายเดือน (%) | Max drawdown (%) | Turnover เฉลี่ยหลังเข้าลงทุน (%) |
|---|---:|---:|---:|---:|
| Sample GMV | 3.0602 | 2.4516 | −11.9916 | 6.5493 |
| CC GMV | 1.6418 | 2.4022 | −11.7908 | 4.5625 |
| Shrink 0.5 | 2.1453 | 2.4364 | −11.6563 | 5.5098 |
| EW | −3.7060 | 2.7777 | −17.3486 | 1.1764 |

ในชุดสมมตินี้ CC GMV มี SD รายเดือนต่ำที่สุด ส่วน Sample GMV มีผลตอบแทนสะสมสูงที่สุดในช่วงเดียวกัน และ Shrink 0.5 มี drawdown ลึกน้อยที่สุดในสามพอร์ต GMV ผลแต่ละคอลัมน์ตอบคนละคำถาม การเลือกเมทริกซ์ด้วยเป้าหมาย variance ต่ำไม่ได้สั่งให้โปรแกรมหาผลตอบแทนหรือ drawdown ที่ดีที่สุดด้วย

ค่า SD ใช้ตัวหาร $60-1=59$ และยังเป็นรายเดือน ผลตอบแทนรวมคือการทบทั้ง 60 เดือน จึงนำไปเทียบกับ SD โดยถือว่าทั้งสองเป็นหน่วยรายปีไม่ได้ ส่วน turnover เฉลี่ยใช้ 59 การปรับหลังเข้าลงทุน ค่าธรรมเนียมที่ไม่ได้รวมอาจเปลี่ยนอันดับผลตอบแทน โดยเฉพาะเมื่อความต่างของผลตอบแทนแต่ละวิธีมีขนาดเล็ก

เราใช้ seed, หน้าต่าง 36 เดือน และ delta 0.5 ชุดเดียวที่กำหนดไว้สำหรับบทเรียน ตัวอย่างนี้แสดงวิธีเปรียบเทียบตัวประมาณ และไม่รองรับข้อสรุปว่าลำดับดังกล่าวจะเกิดซ้ำกับข้อมูลชุดใหม่ หากลองหลายค่าแล้วเลือกค่าที่ดีที่สุดจาก 60 เดือนนี้ ช่วงเดิมจะกลายเป็นข้อมูลสำหรับเลือกวิธี ต้องกันช่วงใหม่ไว้ประเมินอีกครั้ง

<span id="shrinkage-past-only-check"></span>

## เปลี่ยนข้อมูลอนาคตเพื่อทดสอบเวลาเลือกน้ำหนัก

เราจะเพิ่มผลตอบแทนของทุกสินทรัพย์ตั้งแต่มกราคม 2016 เป็นต้นไปอีก 10 จุดเปอร์เซ็นต์ แล้วรันขั้นตอนเดิม น้ำหนักที่ใช้ถือเดือนมกราคม 2016 ต้องยังเท่าเดิม เพราะเลือกจากข้อมูลที่จบในธันวาคม 2015 ส่วนผลตอบแทนที่ได้รับในเดือนมกราคมย่อมเปลี่ยนได้

```python
shrink_changed = shrink_returns.copy()
shrink_cut = 72
shrink_changed.iloc[shrink_cut:] += 0.10
changed_backtest, changed_weights, _ = rolling_gmv(shrink_changed, window=shrink_window)
shrink_first_changed_month = shrink_returns.index[shrink_cut]
for name in shrink_weights:
    assert np.allclose(shrink_weights[name].loc[:shrink_first_changed_month],
                       changed_weights[name].loc[:shrink_first_changed_month])
assert np.allclose(changed_backtest.loc[shrink_first_changed_month]
                   - shrink_backtest.loc[shrink_first_changed_month], 0.10)
print("Weights through", shrink_first_changed_month, "use unchanged earlier history")
print("That month's realized return changes by 10 percentage points")
```

`iloc[72:]` เปลี่ยนตั้งแต่แถวตำแหน่ง 72 จนจบ แต่ `.loc[:shrink_first_changed_month]` ในการตรวจรวมเดือนมกราคม 2016 ด้วย `assert` จะหยุดหากเงื่อนไขไม่เป็นจริง ในกรณีนี้น้ำหนักทุกวิธียังเท่าเดิมถึงเดือนที่กำลังตรวจ และผลตอบแทนเดือนนั้นเพิ่ม 10 จุดเปอร์เซ็นต์ เพราะน้ำหนักรวมหนึ่ง

ตั้งแต่กุมภาพันธ์ 2016 ข้อมูลมกราคมที่แก้ไว้จะเข้าหน้าต่างประมาณ จึงอนุญาตให้น้ำหนัก GMV ต่างจากเดิมได้ การตรวจนี้ช่วยจับการนำผลตอบแทนเดือนที่จะถือเข้าไปใช้เลือกน้ำหนักก่อนเวลา หรือ [look-ahead bias](glossary.html#look-ahead-bias) แต่ยังต้องตรวจวันที่ข้อมูลเผยแพร่จริง การเปลี่ยนจักรวาลสินทรัพย์ สินทรัพย์ที่ออกจากตลาด และวิธีคิดต้นทุนเมื่อนำขั้นตอนไปใช้กับข้อมูลจริง

<span id="shrinkage-exercises"></span>

## ฝึกเปลี่ยนเมทริกซ์และอ่านผล

1. ถ้า $S_{AB}=0.0002$, $F_{AB}=0.00005635$ และ $\delta=0.25$ ช่อง A/B หลังผสมเป็นเท่าไร?
2. เหตุใด variance บนแนวทแยงจึงไม่เปลี่ยนเมื่อปรับ delta ในตัวอย่างนี้ และจะยังจริงหรือไม่ถ้าใช้ target เป็น variance เฉลี่ยคูณ identity matrix?
3. ถ้าหุ้นทุกตัวมีผลตอบแทนเหมือนกันทุกเดือน การตั้ง delta เป็น 0.5 ทำให้เมทริกซ์ผสมเป็น PD โดยอัตโนมัติหรือไม่?
4. เรียก `rolling_gmv(shrink_returns, shrink_delta=0)` แล้วเทียบคอลัมน์ `Shrink 0` กับ `Sample GMV` ควรได้ผลอย่างไร? ถ้าใช้ delta เป็น 1 ควรเทียบกับคอลัมน์ใด?
5. ถ้าต้องการพอร์ตสำหรับมกราคม 2013 โดยใช้หน้าต่าง 36 เดือน ใส่ผลตอบแทนมกราคม 2013 ลงใน covariance ได้หรือไม่?
6. EW มีน้ำหนักเป้าหมายคงที่ทุกเดือน เหตุใด turnover ที่รายงานจึงไม่เป็นศูนย์?

<details>
<summary>แนวคำตอบ</summary>

1. ได้ $0.25(0.00005635)+0.75(0.0002)=0.0001640875$ ใช้ตัวเลขที่ยังไม่ปัดเศษจากโค้ดจะได้คำตอบต่างเล็กน้อย
2. เพราะ $F_{ii}=S_{ii}$ ทุกตัว เมื่อผสมจึงยังเป็นค่าเดิม ส่วน target $\mu I$ เปลี่ยน variance แต่ละตัวไปหา $\mu$ จึงเปลี่ยนแนวทแยงได้ด้วย
3. ไม่ได้ ทั้ง $S$ และ constant-correlation target จะสะท้อนความซ้ำกันของสินทรัพย์ เมทริกซ์ผสมยัง singular ได้ เงื่อนไขที่เพียงพอข้อหนึ่งคือ target เป็น PD, sample เป็น PSD และ delta เป็นบวก
4. Delta 0 คืนเมทริกซ์ sample จึงควรได้น้ำหนักและผลตอบแทนเดียวกับ Sample GMV ภายในค่าคลาดเคลื่อนเชิงตัวเลข Delta 1 ควรตรงกับ CC GMV ชื่อคอลัมน์ของฟังก์ชันเปลี่ยนตามค่าที่ส่งเข้าไป
5. ใช้ได้ถึงธันวาคม 2012 เท่านั้น ผลตอบแทนมกราคม 2013 รู้เมื่อเดือนนั้นจบ การใส่เข้าไปจะใช้ข้อมูลของเดือนที่กำลังจะลงทุน
6. ระหว่างเดือน สินทรัพย์ให้ผลตอบแทนต่างกันจนน้ำหนักไหลออกจาก 12.5% การกลับมาเท่ากันเดือนถัดไปจึงต้องซื้อขาย Turnover ต้องเทียบเป้าหมายใหม่กับน้ำหนักที่ไหลแล้ว

</details>

<span id="shrinkage-sources"></span>

## แหล่งที่มาและขอบเขตของตัวอย่าง

อ่าน Transcript ภาษาอังกฤษเต็มของ [Honey I Shrunk the Covariance Matrix!](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/szNVo/honey-i-shrunk-the-covariance-matrix) และ [Covariance Estimation Lab](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/DLb5f/module-2-lab-session-covariance-estimation) เมื่อ 3 ตุลาคม 2026 ใช้เป็นโครงเรื่องการผสมตัวประมาณ การสร้าง constant correlation และการเปลี่ยน covariance ภายใต้กฎ GMV เดียวกัน คำอธิบายไทย โค้ด ข้อมูลสมมติ และแบบฝึกหัดในหน้านี้เขียนขึ้นใหม่

ชื่อบทเรียนอ้างถึง *Honey, I Shrunk the Sample Covariance Matrix* ของ Olivier Ledoit และ Michael Wolf, Journal of Portfolio Management 30(4), 2004, หน้า 110–119; [หน้าบทคัดย่อของผู้เขียน](https://ledoit.net/honey_abstract.htm)มีรายละเอียดบรรณานุกรม การเรียก estimator ว่า Ledoit–Wolf ต้องดู target และวิธีประมาณ intensity ของ implementation ด้วย จึงแยกจากตัวอย่าง fixed delta ในหน้านี้อย่างชัดเจน

ก่อนเปลี่ยนตัวอย่างเป็นข้อมูลจริง ให้ตรวจผลตอบแทนรวมและหน่วย วันที่ครบตรงกัน วิธีจัดการข้อมูลที่หายไป ข้อจำกัดน้ำหนัก และจังหวะคิดต้นทุน แล้วค่อยใช้ข้อมูลช่วงใหม่ตรวจว่าความเสี่ยงและการซื้อขายต่างจากที่ประมาณไว้เพียงใด
