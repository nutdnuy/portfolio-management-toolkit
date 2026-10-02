---
title: เมื่อผลตอบแทนไม่เป็น Normal — เข้าใจความเสี่ยงปลายหาง
description: บทต่อจาก Returns อธิบาย Skewness, Kurtosis, การทดสอบ Normality, Python modules, Semi-deviation, VaR และ CVaR ตั้งแต่พื้นฐาน
---

# เมื่อผลตอบแทนไม่เป็น Normal

<p class="lead">ถ้าพอร์ตสองชุดมีผลตอบแทนเฉลี่ยและความผันผวนเท่ากัน เราจะมั่นใจได้หรือไม่ว่าความเสี่ยงขาดทุนรุนแรงเท่ากัน?</p>

ในบท [How to Calculate return](returns.html) เราเริ่มจากเปอร์เซ็นต์ การทบต้น และภาพรวมของตัววัดความเสี่ยง บทนี้ขยาย **Section 2 — Beyond the Gaussian case: Extreme risk estimates** ของ Module 1 ให้ลงมือทำทีละขั้น เราจะดูรูปร่างข้อมูลก่อนเลือกตัววัด แล้วค่อยเก็บสูตรที่เข้าใจแล้วไว้ในไฟล์ Python ที่เรียกใช้ซ้ำได้

คำว่า **Gaussian** ในชื่อ Section หมายถึง Normal distribution ส่วน **ปลายหาง (tail)** หมายถึงบริเวณที่ผลตอบแทนอยู่ไกลจากกลุ่มส่วนใหญ่ เมื่อเรียงผลตอบแทนจากน้อยไปมาก หางซ้ายคือด้านที่ผลตอบแทนต่ำ ส่วนความรุนแรงและโอกาสเกิดต้องดูจากข้อมูลหรือแบบจำลองที่ใช้ ไม่ได้รู้จากชื่อสินทรัพย์

ตัวเลขและกราฟในบทนี้เป็น **ตัวอย่างสมมติหรือการจำลองเพื่อเรียนรู้ทั้งหมด** ไม่ใช่ผลการลงทุนจริง เราจะใช้ข้อมูล 10 เดือนเพื่อดูรูปทรง ข้อมูล 4 งวดเพื่อฝึก downside และข้อมูล 20 วันเพื่อฝึก VaR โดยระบุทุกครั้งที่เปลี่ยนชุดข้อมูล การจำลอง Normality เป็นอีกตัวอย่างหนึ่ง ไม่ใช่การเพิ่มจำนวนข้อมูลให้ตัวอย่างเล็กเหล่านี้

## เส้นทางการอ่านและการเตรียมตัว

| ช่วงเรียน | คำถามที่เราจะตอบ |
|---|---|
| [รูปร่างของผลตอบแทน](#distribution-basics) | ค่าเฉลี่ยกับ SD มองข้ามอะไรไป? |
| [Skewness และ Kurtosis](#shape-moments) | ผลตอบแทนที่อยู่ไกลจาก mean ส่งผลต่อสูตรอย่างไร? |
| [ทดสอบ Normality](#normality-test) | p-value ช่วยตัดสินอะไร และไม่ได้บอกอะไร? |
| [สร้าง Python module](#python-module) | ย้ายสูตรที่รันได้แล้วไปใช้ซ้ำอย่างไร? |
| [ความเสี่ยงด้านล่างและปลายหาง](#downside-measures) | เราจะตั้งเกณฑ์ขาดทุนและเลือกวิธีวัดอย่างไร? |

ถ้ายังไม่คุ้นกับตัวแปร `import` หรือ `DataFrame` ให้เริ่มที่ [Python จากบทก่อน](returns.html#python-basics) ก่อน บทนี้เริ่มด้วย Notebook ใหม่และสร้างข้อมูลเอง รันช่องตามลำดับจากบนลงล่างด้วย **Shift + Enter** จึงไม่ต้องมี CSV ของคอร์ส โค้ดใช้ NumPy, pandas และ SciPy; หาก Notebook แจ้งว่าไม่มีแพ็กเกจ ให้ติดตั้งในสภาพแวดล้อมนั้นด้วย `%pip install numpy pandas scipy` แล้ว restart kernel ก่อนเริ่มใหม่

รอบแรกอ่านคำอธิบายและตารางให้เห็นความหมายก่อน แล้วค่อยรันโค้ด อย่าเพิ่งพยายามจำทุกสูตร โดยเฉพาะ Cornish–Fisher ที่อยู่ช่วงท้ายและอ่านเป็นหัวข้อเพิ่มเติมได้

<span id="distribution-basics"></span>

## ผลตอบแทนเฉลี่ยเท่ากัน ความเสี่ยงด้านหางอาจต่างกัน

ใน [บทผลตอบแทน](returns.html) เราเรียนว่า mean บอกผลตอบแทนเฉลี่ย และ standard deviation หรือ SD บอกว่าผลตอบแทนกระจายห่างจากค่าเฉลี่ยเพียงใด แต่สองตัวเลขนี้ยังไม่ได้บอกว่าผลตอบแทนส่วนใหญ่กระจุกอยู่ตรงไหน หรือจุดที่อยู่ไกลมากเป็นกำไรหรือขาดทุน

เราจะเปรียบเทียบชุดที่กำไรขาดทุนขนาดปานกลางกับชุดที่กำไรเล็กหลายครั้งแต่ขาดทุนมากครั้งหนึ่ง แล้วค่อยใช้ skewness และ kurtosis อธิบายว่าทำไม mean และ SD จึงยังเล่าเรื่องไม่ครบ

**Distribution หรือการแจกแจง** บอกการกระจายของผลลัพธ์และน้ำหนักของแต่ละส่วน การนับจากข้อมูลที่เกิดขึ้นแล้วคือการแจกแจงเชิงประจักษ์ ส่วนเส้นโค้ง Normal เป็นแบบจำลองความน่าจะเป็น สัดส่วนที่พบในสิบเดือนจึงยังไม่ใช่ความน่าจะเป็นที่รู้แน่นอนของเดือนถัดไป

### สร้างตัวอย่างเล็กที่ตรวจด้วยมือได้

เราจะใช้ผลตอบแทนสมมติสิบเดือนสองชุดชื่อ `Regular` และ `LeftTail` โดยตั้งใจให้ทั้งคู่มี mean 1% ต่อเดือนและ SD แบบหารด้วยจำนวนข้อมูลเท่ากับ 2% ต่อเดือน ชื่อ Regular แค่ใช้เรียกชุดข้อมูลที่กระจายสองด้านค่อนข้างสม่ำเสมอ **ไม่ได้หมายความว่ามันเป็น Normal** ข้อมูลทั้งสองชุดเป็นตัวอย่างที่ผู้เขียนสร้างขึ้น ไม่มีชุดใดเป็นประวัติผลการลงทุนจริง

โค้ดเริ่มใหม่จากช่องนี้ได้ โดยใช้ Python ที่ติดตั้ง NumPy, pandas และ SciPy แล้ว `import` เปิดใช้เครื่องมือ ส่วน `as np`, `as pd` และ `as stats` ตั้งชื่อย่อให้เรียกง่าย NumPy ช่วยคำนวณกับตัวเลขทั้งชุด pandas จัดเป็นตาราง และ SciPy มีฟังก์ชันทางสถิติ

```python
import numpy as np
import pandas as pd
import scipy.stats as stats
```

เราเริ่มจากตัวเลขที่มี mean เป็น 0 และ SD เป็น 1 ก่อน แล้วคูณด้วย `0.02` เพื่อกำหนดขนาดความกระจายเป็น 2% และบวก `0.01` เพื่อย้ายค่าเฉลี่ยเป็น 1% `np.array(...)` สร้างชุดตัวเลขที่คำนวณทุกสมาชิกพร้อมกันได้ ส่วน `np.sqrt(3)` คือรากที่สองของ 3 ซึ่งเมื่อคูณตัวเองจะได้ 3

ในบรรทัด `[-3] + [1/3] * 9` เครื่องหมายยังทำงานกับ **list** ของ Python: `[1/3] * 9` ทำซ้ำสมาชิกหนึ่งในสามเก้าครั้ง แล้ว `+` นำมาต่อท้าย `[-3]` จึงได้ตัวเลขสิบตัว เมื่อส่งเข้า `np.array` แล้ว การคูณบวกในบรรทัดสร้างตารางจึงเป็นการคำนวณกับตัวเลขทุกตัว

```python
z_regular = np.array([-3, -2, -1, -1, 0, 0, 1, 1, 2, 3]) / np.sqrt(3)
z_left = np.array([-3] + [1 / 3] * 9)
shape_data = pd.DataFrame({
    "Regular": 0.01 + 0.02 * z_regular,
    "LeftTail": 0.01 + 0.02 * z_left
})
print((shape_data * 100).round(4))
```

| ลำดับข้อมูล | Regular (% ต่อเดือน) | LeftTail (% ต่อเดือน) |
|---:|---:|---:|
| 1 | −2.4641 | −5.0000 |
| 2 | −1.3094 | 1.6667 |
| 3 | −0.1547 | 1.6667 |
| 4 | −0.1547 | 1.6667 |
| 5 | 1.0000 | 1.6667 |
| 6 | 1.0000 | 1.6667 |
| 7 | 2.1547 | 1.6667 |
| 8 | 2.1547 | 1.6667 |
| 9 | 3.3094 | 1.6667 |
| 10 | 4.4641 | 1.6667 |

ตารางปัดทศนิยมเพื่อให้อ่านง่าย แต่ให้ใช้ค่าต้นฉบับในตัวแปร `shape_data` คำนวณต่อ แถวใน Python เริ่มนับจาก 0 จึงจะแสดง 0 ถึง 9 ส่วนตารางอธิบายด้านบนเรียงลำดับ 1 ถึง 10

ลองตรวจสองสถิติที่เราเคยใช้ก่อน `.mean()` หาค่าเฉลี่ยลงไปในแต่ละคอลัมน์ และ `.std(ddof=0)` ใช้จำนวนข้อมูล $n$ เป็นตัวหารของ variance ก่อนถอดรากที่สอง

```python
shape_mean = shape_data.mean()
shape_sd = shape_data.std(ddof=0)
shape_summary = pd.DataFrame({
    "Mean (%)": shape_mean * 100,
    "SD with n (%)": shape_sd * 100
})
print(shape_summary.round(4))
```

ผลคือ Regular และ LeftTail มี **mean 1.0000% และ SD 2.0000% เหมือนกัน** แต่ Regular มีเดือนแย่ที่สุดประมาณ −2.4641% ส่วน LeftTail มีเดือน −5% ซึ่งแย่กว่าชัดเจน การรู้เพียง mean กับ SD จึงยังแยกสองรูปแบบนี้ไม่ได้

ที่ใช้ `ddof=0` ในส่วนนี้ เพราะเราจะอธิบาย standardized moments ที่คำนวณด้วยตัวหาร $n$ ให้สอดคล้องกันทั้งสูตร ไม่ได้หมายความว่าเรารู้ประชากรผลตอบแทนทั้งหมดแล้ว หากเปลี่ยนเป็น `ddof=1` ซึ่งเป็น sample SD แบบที่ใช้ในบทก่อน ทั้งสองชุดจะยังเท่ากัน แต่เป็นประมาณ **2.1082%** อย่านำ SD คนละ convention มาใส่ในสูตรเดียวกันโดยไม่ตรวจ

<span id="histogram-basics"></span>

## Histogram: นับว่าผลตอบแทนไปอยู่ตรงไหน

**Histogram** แบ่งแกนนอนเป็นช่วงผลตอบแทน แล้วนับว่ามีกี่ observations ตกในแต่ละช่วง แถบหนึ่งไม่ได้แทนเดือนหนึ่ง แต่แทน **กลุ่มเดือนที่มีผลตอบแทนอยู่ในช่วงเดียวกัน** ถ้าแกนนอนเป็นเวลาและแท่งหนึ่งแทนหนึ่งเดือน นั่นคือกราฟผลตอบแทนตามเวลา ซึ่งตอบอีกคำถามหนึ่ง [NIST: Histogram](https://www.itl.nist.gov/div898/handbook/eda/section3/histogra.htm)

สำหรับตัวอย่างนี้ แบ่งผลตอบแทนเป็นหกช่องที่กว้างเท่ากัน ช่องละ 2 จุดเปอร์เซ็นต์ ตั้งแต่ −6% ถึง +6% จะเห็นว่า LeftTail มีเก้าเดือนอยู่ระหว่าง 0% ถึง +2% และหนึ่งเดือนอยู่ระหว่าง −6% ถึง −4% การอ่านเฉพาะกลุ่มเดือนที่กำไรจึงทำให้มองข้ามจุดที่ห่างไปทางซ้ายมาก

<figure class="extreme-figure">
<picture><source media="(max-width: 650px)" srcset="assets/charts/extreme-risk-shapes-mobile.svg"><img src="assets/charts/extreme-risk-shapes.svg" width="720" height="670" loading="lazy" alt="Histogram ข้อมูลสมมติสิบเดือนสองชุดที่ mean 1% และ population SD 2% เท่ากัน: Regular กระจายหลายช่วง ส่วน LeftTail มีเก้าเดือนระหว่าง 0 ถึง 2% และหนึ่งเดือนระหว่าง −6 ถึง −4%"></picture>
<figcaption>ภาพที่ 1 — แกนและความกว้างช่องเท่ากันทั้งสองชุด ตัวเลขเหนือแท่งเป็นจำนวน observations ที่นับได้จริงจากข้อมูลสมมติ ไม่ใช่ความน่าจะเป็นที่ทราบแน่นอนของอนาคต ทั้งสองชุดไม่ได้กำหนดให้เป็น Normal</figcaption>
</figure>

ถ้าอยากให้ Python ช่วยนับ ใช้ `np.histogram` โดย `bins` ระบุ **ขอบช่อง** จำนวนขอบต้องมากกว่าจำนวนช่องหนึ่งจุด ฟังก์ชันคืนสองสิ่งคือจำนวนในแต่ละช่องและขอบที่ใช้ การเขียนชื่อตัวแปรสองชื่อคั่นด้วยจุลภาคทางซ้ายของ `=` คือรับสองผลลัพธ์นั้นตามลำดับ

```python
hist_bins = np.array([-0.06, -0.04, -0.02, 0.00, 0.02, 0.04, 0.06])
regular_counts, used_edges = np.histogram(shape_data["Regular"], bins=hist_bins)
left_counts, used_edges = np.histogram(shape_data["LeftTail"], bins=hist_bins)
print(regular_counts)
print(left_counts)
```

ได้ `[0 1 3 2 3 1]` และ `[1 0 0 9 0 0]` แต่ละชุดนับรวมกันได้สิบจุด NumPy รวมขอบซ้ายแต่ไม่รวมขอบขวา ยกเว้นช่องสุดท้ายที่รวมขอบขวาด้วย ตัวอย่างนี้เลือกช่วงครอบคลุมทุกค่า หากเลือกขอบแคบจนตัดข้อมูลทิ้ง ต้องตรวจว่าผลรวมจำนวนยังเท่ากับจำนวนข้อมูลที่ต้องการแสดงหรือไม่ [NumPy: histogram](https://numpy.org/doc/stable/reference/generated/numpy.histogram.html)

ความกว้างของช่องเปลี่ยนรูปร่างที่เห็น โดยเฉพาะตัวอย่างเล็ก จึงไม่ควรตัดสินจาก histogram อย่างเดียว ถ้าแกนตั้งเป็น **density** ให้ดูพื้นที่ของแท่งแทนความสูงเพื่ออ่านสัดส่วนของข้อมูล

Histogram ไม่เก็บลำดับเวลา สลับเดือนที่ขาดทุนไปไว้ท้ายชุดแล้วรูปจะเหมือนเดิม แต่เส้นทางเงินและ drawdown อาจเปลี่ยน เราจึงต้องดูผลตอบแทนเรียงตามเวลาด้วย

<span id="normal-distribution"></span>

## Normal คือแบบจำลองหนึ่ง ไม่ใช่รูปที่ข้อมูลต้องเป็น

**Normal distribution** หรือ Gaussian distribution เป็นแบบจำลองต่อเนื่องที่มีรูปกระดิ่งสมมาตรรอบค่าเฉลี่ย พารามิเตอร์สองตัวคือ $\mu$ อ่านว่า “มิว” ใช้กำหนดศูนย์กลาง และ $\sigma$ อ่านว่า “ซิกมา” ใช้กำหนดความกว้าง โดย $\sigma>0$ ถ้าสมมติว่าเป็น Normal แล้ว รู้สองค่านี้ก็ระบุการแจกแจงทั้งเส้นได้ แต่ถ้ายังไม่ได้ตั้งสมมติฐาน Normal การรู้สองค่านี้ยังทำไม่ได้ [SciPy: Normal distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html)

ให้แบบจำลองสมมติมี $\mu=1\%$ และ $\sigma=2\%$ ต่อเดือน ตำแหน่งที่ต่ำกว่าค่าเฉลี่ยหนึ่ง SD คือ $1\%-2\%=-1\%$ ตำแหน่งที่สูงกว่าค่าเฉลี่ยหนึ่ง SD คือ $1\%+2\%=3\%$ การใช้ SD ตรงนี้เป็นระยะห่างที่บวกหรือลบในหน่วย **จุดเปอร์เซ็นต์**

| ช่วงรอบค่าเฉลี่ย | ช่วงผลตอบแทนของแบบจำลอง | ความน่าจะเป็นภายใต้ Normal |
|---|---|---:|
| $\mu\pm1\sigma$ | −1% ถึง +3% | ประมาณ 68.27% |
| $\mu\pm2\sigma$ | −3% ถึง +5% | ประมาณ 95.45% |
| $\mu\pm3\sigma$ | −5% ถึง +7% | ประมาณ 99.73% |

**Standard Normal** มี mean 0 และ SD 1 เราแปลงผลตอบแทนเป็นระยะห่างจากค่าเฉลี่ยในหน่วย SD ได้ด้วย

$$
z=\frac{R-\mu}{\sigma}.
$$

ผลตอบแทน −5% จึงอยู่ที่ $(-0.05-0.01)/0.02=-3$ หรือสาม SD ต่ำกว่า mean ค่านี้ไม่มีหน่วย ไม่ใช่ผลตอบแทน −3%

ฟังก์ชัน `stats.norm.cdf(x)` ให้พื้นที่ด้านซ้ายตั้งแต่ $-\infty$ ถึง `x` ของ Standard Normal คำว่า **CDF** ย่อจาก cumulative distribution function เช่น `cdf(-3)` ตอบว่า ภายใต้แบบจำลองนี้มีโอกาสอยู่ต่ำกว่าค่าเฉลี่ยอย่างน้อยสาม SD เท่าไร

```python
normal_left_tail = stats.norm.cdf(-3)
normal_middle = stats.norm.cdf(1) - stats.norm.cdf(-1)
print(f"Below minus 3 SD: {normal_left_tail:.4%}")
print(f"Within plus/minus 1 SD: {normal_middle:.2%}")
```

ได้ **0.1350%** สำหรับด้านซ้ายของ −3 SD และ **68.27%** สำหรับช่วง −1 ถึง +1 SD สังเกตว่าตาราง 99.73% เป็นพื้นที่ตรงกลางซึ่งเหลือสองหางรวมกันประมาณ 0.27% หางซ้ายเพียงด้านเดียวจึงเหลือประมาณครึ่งหนึ่ง

ส่วนข้อมูล LeftTail ของเรามีหนึ่งในสิบเดือนอยู่ที่ −5% หรือคิดเป็น 10% ของชุดข้อมูล นี่เป็นตัวอย่างให้เห็นว่าการเอา mean และ SD ไปแทนใน Normal โดยอัตโนมัติอาจซ่อนรูปทรงที่ต่างออกไป **ไม่ได้ใช้สิบจุดนี้ประมาณว่าทุกเดือนในอนาคตมีโอกาสขาดทุน −5% เท่ากับ 10%**

Normal ไม่มีขอบล่าง แต่ simple return ของสินทรัพย์ที่ซื้อด้วยเงินตัวเองโดยไม่มีภาระเพิ่มต่ำสุด −100% จึงเป็นการประมาณที่ต้องตรวจบริบท การใช้ log return ก็ไม่ได้บังคับให้ข้อมูลเป็น Normal; ดู [บท Log return](returns.html#log-returns)

<span id="shape-moments"></span>

## เตรียมวัดรูปทรง: เอาค่าเฉลี่ยออก แล้ววัดระยะเป็นหน่วย SD

ก่อนเขียนสูตร skewness หรือ kurtosis ลองทำตามสามขั้นตอนนี้กับข้อมูลแต่ละเดือน: หักค่าเฉลี่ยออก หารด้วย SD แล้วพิจารณาว่าค่าที่ได้เป็นบวกหรือลบและมีขนาดเท่าไร ค่าที่เหลือเรียกว่า **standardized deviation** หรือในที่นี้เรียกสั้น ๆ ว่า z-score ของข้อมูล

ในสูตรต่อไป เรามีข้อมูล $n$ ค่า เขียนเป็น $R_1,\ldots,R_n$ ให้ $\bar R$ เป็นค่าเฉลี่ยของข้อมูล และให้ $s_0$ เป็น SD ที่ใช้ตัวหาร $n$:

$$
\bar R=\frac1n\sum_{i=1}^nR_i,
\qquad
s_0=\sqrt{\frac1n\sum_{i=1}^n(R_i-\bar R)^2},
\qquad
z_i=\frac{R_i-\bar R}{s_0}.
$$

$\sum$ หมายถึงบวกทุก observation, $i$ บอกลำดับข้อมูล และ $\sqrt{\cdot}$ คือรากที่สอง สำหรับทั้งสองชุดนี้ $\bar R=0.01$ และ $s_0=0.02$

ผลตอบแทน −5% ของ LeftTail มีระยะจาก mean เท่ากับ −6 จุดเปอร์เซ็นต์ จึงมี z-score −3 ส่วนผลตอบแทน $1\frac23\%$ ของอีกเก้าเดือนสูงกว่า mean อยู่ $\frac23$ จุดเปอร์เซ็นต์ จึงมี z-score $\frac13$ ทั้งสองชุดถูกทำให้เปรียบเทียบบนหน่วย SD เดียวกันแล้ว

```python
centered_returns = shape_data - shape_mean
standardized_returns = centered_returns / shape_sd
print(standardized_returns.round(4))
```

คำว่า **moment** หมายถึงค่าเฉลี่ยของค่าที่ยกกำลัง ถ้าหัก mean ก่อนจะเรียกว่า central moment การหารด้วยกำลังของ SD ทำให้ไม่มีหน่วย แต่ใช้ไม่ได้เมื่อ SD เป็นศูนย์ หากมี NaN ต้องตกลงวิธีจัดการก่อนคำนวณด้วย

<span id="skewness"></span>

## Skewness: ฝั่งไหนมีค่าที่ห่างจากค่าเฉลี่ยมากกว่า

ถ้าใช้กำลังสอง เครื่องหมายลบจะหายไป ระยะ −3 และ +3 ให้คำตอบ 9 เหมือนกัน เราจึงแยกขาลงจากขาขึ้นไม่ได้จาก variance อย่างเดียว แต่เมื่อใช้ **กำลังสาม** เครื่องหมายยังอยู่: $(-3)^3=-27$ และ $3^3=27$ ค่าที่อยู่ไกลจาก mean จึงมีน้ำหนักมาก พร้อมบอกทิศทางของมันด้วย

ในบทนี้ใช้ skewness แบบ standardized third central moment:

$$
S=\frac{\frac1n\sum_{i=1}^n(R_i-\bar R)^3}{s_0^3}
=\frac1n\sum_{i=1}^nz_i^3.
$$

Skewness ติดลบหมายถึงผลรวมถ่วงด้วยกำลังสามเอนไปทางค่าต่ำกว่าค่าเฉลี่ย ค่าบวกหมายถึงเอนไปทางด้านสูงกว่า mean สำหรับรูปทรงทั่วไปที่มียอดเดียว เรามักอธิบายว่าเบ้ซ้ายหรือเบ้ขวา แต่เครื่องหมายนี้ **ไม่ได้เกิดจากการนับว่ามีกี่เดือนบวกหรือกี่เดือนลบ** [NIST: Measures of Skewness and Kurtosis](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35b.htm)

### คำนวณ LeftTail ด้วยมือก่อน

LeftTail มี z-score −3 หนึ่งค่า และ $1/3$ เก้าค่า ดังนั้น

$$
S_{\text{LeftTail}}
=\frac{(-3)^3+9(1/3)^3}{10}
=\frac{-27+1/3}{10}
=-\frac83\approx-2.666667.
$$

เดือนที่ห่างไปทางซ้ายเพียงเดือนเดียวให้ส่วนร่วม −27 ขณะที่เก้าเดือนฝั่งขวารวมกันได้เพียง $1/3$ จึงเกิด skewness ติดลบมาก ทั้งที่ **เก้าในสิบเดือนมีกำไร** และเก้าเดือนนั้นยังสูงกว่าค่าเฉลี่ยด้วย นี่คือจุดที่ทำให้คำอธิบายว่า “negative skew แปลว่ามีเดือนขาดทุนมากกว่าเดือนกำไร” ผิด

Regular มีค่าที่จับคู่สมมาตรรอบ mean เช่น z-score $-3/\sqrt3$ กับ $+3/\sqrt3$ เมื่อนำกำลังสามมาบวกกันแต่ละคู่จะหักล้าง จึงได้ $S=0$ แต่การมี skewness เป็นศูนย์เพียงค่าเดียวก็ยังไม่ยืนยันว่าเป็น Normal และโดยทั่วไปไม่เพียงพอจะยืนยันสมมาตรทุกรูปแบบ

`** 3` ใน Python หมายถึงยกกำลังสาม แล้ว `.mean()` เฉลี่ยค่าที่ได้ลงไปในแต่ละคอลัมน์

```python
shape_skewness = (standardized_returns ** 3).mean()
print(shape_skewness.round(6))
print((shape_data["LeftTail"] > 0).sum())
print((shape_data["LeftTail"] < 0).sum())
```

ได้ Regular **0.000000**, LeftTail **−2.666667**, เดือนบวก **9** และเดือนลบ **1** การเปรียบเทียบ `> 0` หรือ `< 0` สร้างค่า `True`/`False` ของแต่ละเดือน เมื่อนำ `.sum()` มาบวก จะนับ True เป็นหนึ่งและ False เป็นศูนย์

### Mean กับ median ช่วยดูรูป แต่ไม่ใช่กฎตัดสินเครื่องหมาย

**Median** คือค่ากลางหลังเรียงข้อมูลจากน้อยไปมาก ไม่ใช่ค่าที่พบบ่อยที่สุด ซึ่งเรียกว่า **mode** กรณีสิบค่าให้เฉลี่ยลำดับที่ห้าและหก LeftTail จึงมี median ประมาณ 1.6667% สูงกว่า mean 1% เพราะจุดขาดทุน −5% ดึง mean ลงมากกว่าที่เปลี่ยนค่ากลางของข้อมูล

ความสัมพันธ์นี้อธิบายตัวอย่างของเราได้ แต่ไม่ควรจำว่า `mean < median` ต้องแปลว่า moment skewness ติดลบในทุก distribution โดยเฉพาะข้อมูลไม่ต่อเนื่องหรือมีหลายยอด การทดสอบเครื่องหมายของ mean ลบ median กำลังวัดคนละนิยามกับการเฉลี่ยกำลังสาม คอร์สมี [หน้าแก้ไขคำอธิบายในวิดีโอ Deviation from Normality](https://www.coursera.org/learn/introduction-portfolio-construction-python/supplement/yrJGY/incorrect-statement-in-deviation-from-normality-video) ซึ่งควรอ่านประกอบกับช่วงนี้

<span id="kurtosis"></span>

## Kurtosis: ให้ความสำคัญกับจุดที่อยู่ไกลมาก

ลองเปลี่ยนจากกำลังสามเป็น **กำลังสี่** เครื่องหมายลบหายไปอีกครั้ง แต่ระยะไกลถูกเพิ่มน้ำหนักแรงขึ้น: $1^4=1$, $2^4=16$ และ $3^4=81$ ดังนั้นจุดที่ห่างสาม SD ให้ส่วนร่วมต่อกำลังสี่มากกว่าจุดที่ห่างหนึ่ง SD ถึง 81 เท่า โดยยังต้องรวมกับความถี่ของแต่ละจุดด้วย

**Pearson kurtosis** ในบทนี้เขียนว่า $K$:

$$
K=\frac{\frac1n\sum_{i=1}^n(R_i-\bar R)^4}{s_0^4}
=\frac1n\sum_{i=1}^nz_i^4.
$$

สำหรับ LeftTail เรารู้ z-score ทุกค่าแล้ว จึงแทนได้ตรง ๆ ว่า

$$
K_{\text{LeftTail}}
=\frac{(-3)^4+9(1/3)^4}{10}
=\frac{81+1/9}{10}
=\frac{73}{9}\approx8.111111.
$$

ส่วน Regular ได้ $K=2.2$ ทั้งที่สองชุดมี mean และ SD เท่ากัน แสดงว่ารูปแบบของค่าที่อยู่ไกลจาก mean ยังต่างกันมาก

### ต้องดูว่าใช้ Pearson หรือ excess

Normal มี **Pearson kurtosis เท่ากับ 3** ในระดับการแจกแจง หลายโปรแกรมจึงลบ 3 ออก เพื่อให้ Normal เป็นจุดอ้างอิงที่ศูนย์ ค่านั้นเรียกว่า **excess kurtosis** และมีความสัมพันธ์ $K_{\text{excess}}=K-3$ คำว่า kurtosis ที่ไม่มีคำขยายจึงยังบอกไม่ได้ว่าควรเทียบกับ 3 หรือ 0

```python
shape_kurtosis = (standardized_returns ** 4).mean()
shape_excess = shape_kurtosis - 3
moment_table = pd.DataFrame({
    "Skewness": shape_skewness,
    "Pearson kurtosis": shape_kurtosis,
    "Excess kurtosis": shape_excess
})
print(moment_table.round(6))
```

| ชุดข้อมูล | Skewness | Pearson kurtosis | Excess kurtosis |
|---|---:|---:|---:|
| Regular | 0.000000 | 2.200000 | −0.800000 |
| LeftTail | −2.666667 | 8.111111 | 5.111111 |
| Normal ระดับทฤษฎี | 0 | 3 | 0 |

ค่าทฤษฎีของ Normal เป็นคุณสมบัติของแบบจำลอง ไม่ได้หมายความว่า sample ที่สุ่มจาก Normal ต้องได้ 0, 3 และ 0 พอดีทุกครั้ง เราจะเห็นความคลาดเคลื่อนจากการสุ่มในตัวอย่าง Jarque–Bera ต่อไป

Kurtosis สูงมักใช้เตือนว่าค่าที่อยู่ไกลมากมีอิทธิพลสูงเมื่อเทียบกับ scale ของชุดข้อมูล แต่ **ไม่ได้บอกโอกาสขาดทุนที่ระดับใดระดับหนึ่งโดยตรง** และไม่ได้บอกว่าจุดไกลนั้นเป็นฝั่งกำไรหรือขาดทุน เพราะกำลังสี่ทำให้เครื่องหมายหายไป หากสะท้อน LeftTail รอบ mean ให้จุด −5% กลายเป็น +7% แล้วจุดกำไรเล็ก ๆ กลายเป็น +0.3333% จะได้ skewness เปลี่ยนเป็น +2.666667 แต่ kurtosis ยังเท่าเดิม

จึงไม่ควรใช้คำว่า kurtosis เป็นเพียง “ความแหลมของยอดกราฟ” หรือสรุปจากเลขสูงเลขเดียวว่าอนาคตจะขาดทุนแน่ ๆ ต้องดูข้อมูลดิบและด้านของหางประกอบ ชุด LeftTail มีเพียงสองค่าที่ผู้เขียนกำหนด จึงไม่ได้เป็นหลักฐานทางสถิติว่าตลาดมีหางแบบใด หรือเป็น heavy-tailed distribution ในความหมายทางคณิตศาสตร์

<span id="scipy-moments"></span>

## ตรวจสูตรของเรากับ SciPy โดยตั้ง convention ให้ตรงกัน

ใน `lab_105.ipynb` คอร์สเริ่มจากสร้างฟังก์ชัน skewness และ kurtosis แล้วเปรียบเทียบกับ SciPy ประเด็นที่ควรนำมาใช้คือ **ตรวจนิยามก่อนตรวจว่าตัวเลขตรงกันหรือไม่** เราจะคงสูตร moment แบบหารด้วย $n$ ที่เพิ่งคำนวณไว้ แล้วระบุพารามิเตอร์ให้ชัด

`stats.skew(..., bias=True)` ใช้ standardized third moment ตามสูตรนี้ ส่วน `stats.kurtosis(..., fisher=False, bias=True)` คืน Pearson kurtosis หากเปลี่ยน `fisher=True` จะคืน excess kurtosis คำว่า `bias=True` ตรงนี้หมายถึงใช้ moment estimator แบบไม่แก้ finite-sample bias ไม่ได้หมายความว่าให้เลือกผลที่เอนเอียงตามความต้องการ ถ้าใช้ `bias=False` จะเป็นสูตรปรับแก้และอาจได้เลขต่างจากตารางของเรา [SciPy: skew](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skew.html), [SciPy: kurtosis](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kurtosis.html)

```python
scipy_moments = pd.DataFrame({
    "Skewness": stats.skew(shape_data, axis=0, bias=True),
    "Pearson kurtosis": stats.kurtosis(shape_data, axis=0, fisher=False, bias=True),
    "Excess kurtosis": stats.kurtosis(shape_data, axis=0, fisher=True, bias=True)
}, index=shape_data.columns)
print(scipy_moments.round(6))
print(np.allclose(moment_table, scipy_moments))
```

`axis=0` ให้คำนวณลงไปตามแถวแยกแต่ละคอลัมน์ ส่วน `index=shape_data.columns` นำชื่อ Regular และ LeftTail กลับมาติดผลลัพธ์ และ `np.allclose(...)` ตรวจว่าสองตารางใกล้กันภายในความคลาดเคลื่อนทศนิยมของคอมพิวเตอร์ ผลควรได้ตารางเดียวกับด้านบนและ **True**

<span id="normality-test"></span>

## Jarque–Bera: ข้อมูลขัดกับ Normal มากเพียงใด

การดู skewness และ kurtosis ทำให้เห็นรูปร่างได้ แต่ค่าเล็กน้อยที่ต่างจาก 0 และ 3 อาจเกิดขึ้นได้จากการสุ่ม แม้ต้นทางเป็น Normal เราจึงอยากถามว่า **ความต่างที่เห็นมากเกินกว่าจะอธิบายด้วยความผันแปรจากการสุ่มภายใต้สมมติฐาน Normal หรือไม่**

**Jarque–Bera หรือ JB** เป็นการทดสอบที่ใช้สองความต่างนี้ร่วมกัน ให้ $S$ เป็น skewness, $K$ เป็น Pearson kurtosis และ $n$ เป็นจำนวน observations:

$$
JB=\frac n6\left[S^2+\frac{(K-3)^2}{4}\right].
$$

ถ้าคำนวณ excess kurtosis ไว้แล้ว ให้ใส่ค่านั้นแทน $(K-3)$ โดยไม่ลบ 3 ซ้ำ กำลังสองทำให้ skewness ทั้งลบและบวกเพิ่มค่า JB ได้ และ kurtosis ที่ต่ำกว่า 3 ก็เพิ่มสถิติได้เช่นกัน **JB จึงไม่ได้ตรวจเฉพาะหางหนาหรือเฉพาะด้านขาดทุน**

### ตั้งสมมติฐานและเกณฑ์ตัดสินก่อนดูผล

**สมมติฐานศูนย์** เขียนว่า $H_0$ ในที่นี้คือ observations มาจาก Normal เดียวกัน ภายใต้เงื่อนไขการสุ่มที่รองรับการทดสอบมาตรฐาน เช่น ความเป็นอิสระและการแจกแจงไม่เปลี่ยนไปในช่วงที่นำมารวม ส่วน **สมมติฐานทางเลือก** คือข้อมูลไม่สอดคล้องกับ Normal นั้น โดย JB ตรวจผ่าน skewness และ kurtosis

ผลการทดสอบมีสองค่าที่ต้องอ่านให้แยกกัน: **test statistic** คือค่า JB ที่คำนวณจากข้อมูล ส่วน **p-value** คือความน่าจะเป็น ภายใต้ $H_0$ และเงื่อนไขของการทดสอบ ที่จะได้ค่า JB สูงเท่าหรือสูงกว่าที่สังเกต ถ้า p-value ต่ำ ความต่างที่พบจึงเกิดได้ยากภายใต้กรอบสมมติฐานที่กำลังทดสอบ

เราเลือก **ระดับนัยสำคัญ 1% หรือ $\alpha=0.01$ ก่อนดูผล** แล้วใช้เกณฑ์นี้:

| ผล | ถ้อยคำที่ใช้รายงาน |
|---|---|
| p-value < 0.01 | มีหลักฐานให้ปฏิเสธสมมติฐาน Normal ที่ระดับนัยสำคัญ 1% ภายใต้เงื่อนไขการทดสอบ |
| p-value ≥ 0.01 | ข้อมูลนี้ยังไม่ให้หลักฐานเพียงพอที่จะปฏิเสธสมมติฐาน Normal ด้วยการทดสอบนี้ |

**p-value 0.20 ไม่ได้แปลว่าโอกาสที่ข้อมูลเป็น Normal เท่ากับ 20%** และผลที่ “ยังไม่ปฏิเสธ” ไม่ควรถูกเขียนว่า “พิสูจน์ว่า Normal” นอกจากนี้การผ่านการทดสอบรูปร่างการแจกแจงไม่ได้พิสูจน์ว่า observations เป็นอิสระกัน [SciPy: คำอธิบายการทดสอบ Jarque–Bera](https://docs.scipy.org/doc/scipy/tutorial/stats/hypothesis_jarque_bera.html)

### ทำไมเราไม่ใช้สิบเดือนตัดสิน Normal

p-value มาตรฐานของ `stats.jarque_bera` อาศัยการประมาณสำหรับตัวอย่างขนาดใหญ่ เอกสาร SciPy ระบุว่าต้องมีตัวอย่างมากพอ และยกจำนวน **มากกว่า 2,000 observations** ไว้ จึงไม่ใช้ข้อมูลสิบจุดที่เราตั้งใจสร้างเพื่อแทนสมมติฐานการสุ่มแล้วสรุปผลทดสอบอย่างจริงจัง [SciPy: jarque_bera](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.jarque_bera.html)

จำนวนมากกว่า 2,000 ก็ไม่ได้แก้ทุกปัญหา หากข้อมูลรายวันมีช่วงผันผวนสูงติดต่อกัน หรือเอาหลายระบอบตลาดที่มีพารามิเตอร์ต่างกันมารวม เงื่อนไขของการสอบเทียบ p-value อาจไม่ตรง การมีแถวจำนวนมากอย่างเดียวไม่ยืนยันว่าข้อมูลเป็นตัวอย่างอิสระจากการแจกแจงเดียวกัน

<span id="reproducible-normality-example"></span>

## ทดลอง JB กับข้อมูลจำลองที่รู้วิธีสร้าง

คราวนี้สร้างข้อมูลจำลองสองชุด ชุดละ 5,000 observations เพื่อสาธิตการทดสอบ ชุดแรกสุ่มจาก Normal ชุดที่สองสุ่มจาก **Student-t ที่มี degrees of freedom เท่ากับ 5** ซึ่งยังสมมาตร แต่มีหางที่ลดลงช้ากว่า Normal พารามิเตอร์ degrees of freedom หรือ `df` เป็นตัวควบคุมรูปของ Student-t ไม่ใช่ตัวเดียวกับ `ddof` ที่เลือกตัวหารในการคำนวณ SD

เราปรับทั้งสอง **แบบจำลองต้นทาง** ให้มี mean 1% และ SD 2% โดย Student-t ที่ `df=5` ก่อนปรับมี variance $5/(5-2)=5/3$ จึงคูณด้วย $\sqrt{3/5}$ ให้ variance กลับเป็นหนึ่งก่อนใช้ scale 0.02 การเทียบครั้งนี้จึงต่างกันที่รูปทรง ไม่ใช่ตั้งใจให้ตัวหนึ่งผันผวนกว่าตั้งแต่ต้น [SciPy: Student-t distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html)

`np.random.default_rng(20261002)` สร้างตัวสุ่มโดยกำหนด **seed** เป็น 20261002 เพื่อทำตัวอย่างเดิมซ้ำได้เมื่อใช้สภาพแวดล้อมและลำดับคำสั่งเดียวกัน `size=5000` ระบุจำนวนที่ต้องการ และคำสั่งสองบรรทัดถัดไปใช้ตัวสุ่มตัวเดิมต่อเนื่องกัน ถ้ารันเฉพาะบรรทัดสุ่มซ้ำโดยไม่รันบรรทัดกำหนด seed ใหม่ ค่าจะเดินต่อจากสถานะเดิมและเปลี่ยนไป [NumPy: Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)

```python
rng = np.random.default_rng(20261002)
normal_sample = 0.01 + 0.02 * rng.normal(size=5000)
student_sample = 0.01 + 0.02 * rng.standard_t(df=5, size=5000) * np.sqrt(3 / 5)
jb_samples = pd.DataFrame({
    "Normal model": normal_sample,
    "Student-t model": student_sample
})
```

นี่เป็นข้อมูลจำลองที่ไม่มีสินทรัพย์หรือประวัติตลาดอ้างอิง และเราไม่ได้เลือก seed เพื่อให้ได้ผลที่ต้องการ ตรวจ sample moments ก่อน เพราะแม้ mean และ SD **เชิงทฤษฎี** เท่ากัน ค่าใน sample ที่สุ่มออกมาจะไม่ตรงเป๊ะ

```python
jb_sample_summary = pd.DataFrame({
    "Mean (%)": jb_samples.mean() * 100,
    "SD with n (%)": jb_samples.std(ddof=0) * 100,
    "Skewness": stats.skew(jb_samples, axis=0, bias=True),
    "Pearson kurtosis": stats.kurtosis(jb_samples, axis=0, fisher=False, bias=True)
}, index=jb_samples.columns)
print(jb_sample_summary.round(6))
```

| แหล่งที่ใช้จำลอง | Mean (%) | SD แบบหาร n (%) | Skewness | Pearson kurtosis |
|---|---:|---:|---:|---:|
| Normal model | 0.979830 | 1.994908 | −0.011844 | 2.998210 |
| Student-t model | 1.023542 | 1.952293 | −0.081629 | 6.052348 |

Normal ที่สุ่มมาจึงมี skewness ใกล้ 0 และ kurtosis ใกล้ 3 ส่วน Student-t ยังมี skewness ใกล้ 0 เพราะรูปต้นทางสมมาตร แต่ kurtosis สูงกว่าอย่างเห็นได้ชัด **หางหนาจึงเกิดได้แม้ไม่มีความเบ้ไปด้านใดด้านหนึ่ง**

Student-t ที่ `df=5` มี Pearson kurtosis เชิงทฤษฎีเท่ากับ 9 แต่ sample ครั้งนี้ได้ประมาณ 6.05 นี่ไม่ได้แปลว่าโค้ดผิด เพราะสถิติที่ให้น้ำหนักเหตุการณ์ไกลมากอาจยังต่างจากค่าทฤษฎีได้มากใน sample จำกัด หากเปลี่ยน seed คำตอบย่อมเปลี่ยนได้ และไม่ควรลบจุดรุนแรงออกเพียงเพื่อให้ค่าดูใกล้แบบจำลองที่ชอบ

### อ่านผลลัพธ์จริงโดยไม่แปลเกินสิ่งที่ทดสอบ

`stats.jarque_bera` คืนวัตถุผลลัพธ์ที่อ่านค่าได้ด้วย `.statistic` และ `.pvalue` เราส่งแต่ละชุดเข้าไปแยกกัน เพื่อให้แน่ใจว่าค่าที่รายงานหมายถึงชุดไหน

```python
jb_normal = stats.jarque_bera(normal_sample)
jb_student = stats.jarque_bera(student_sample)
print(f"Normal model: JB={jb_normal.statistic:.6f}, p={jb_normal.pvalue:.6g}")
print(f"Student-t model: JB={jb_student.statistic:.6f}, p={jb_student.pvalue:.6g}")
```

ผลจากตัวอย่างที่กำหนดคือ

```text
Normal model: JB=0.117558, p=0.942915
Student-t model: JB=1946.559114, p=0
```

สำหรับ Normal model ค่า p ประมาณ 0.942915 สูงกว่า 0.01 เราจึง **ยังไม่ปฏิเสธ $H_0$** สำหรับ sample ครั้งนี้ ส่วน Student-t ให้ค่า p ต่ำกว่า 0.01 มาก จึง **ปฏิเสธ $H_0$** ตามเกณฑ์ที่ตั้งไว้ก่อนดูผล การทราบว่าชุดแรกสร้างจาก Normal มาจากคำสั่งที่เราใช้สร้าง ไม่ใช่เพราะ p-value สูงพิสูจน์ให้เราแล้ว

ค่า `p=0` เกิดจากจำนวนเล็กเกินกว่าจะเก็บใน floating point ไม่ใช่ความน่าจะเป็นศูนย์ทางคณิตศาสตร์ ภายใต้การอ้างอิง chi-square สอง degrees of freedom ของ JB ตัวอย่างนี้รายงาน **p < $10^{-300}$** ก็เพียงพอสำหรับเทียบกับระดับ 1%

<span id="normality-test-limits"></span>

## ก่อนสรุปจากผลทดสอบ ให้กลับไปดูคำถามที่ต้องการตอบ

ถ้า JB ปฏิเสธ Normal ยังไม่ได้ระบุว่า distribution ที่ควรใช้แทนต้องเป็น Student-t หรือบอกว่า VaR ของพอร์ตเท่าไร หากยังไม่ปฏิเสธ ก็ไม่ได้หมายความว่าปลอดภัย: sample อาจมีพลังในการทดสอบไม่พอ และ distribution ที่ไม่ใช่ Normal บางแบบก็มี skewness และ kurtosis ตรงกับ Normal ได้

เมื่อข้อมูลมาก การทดสอบอาจพบความต่างเพียงเล็กน้อย จึงควรอ่านขนาดของ moments, histogram และจุดสุดโต่งร่วมกับผลกระทบต่อความเสี่ยงที่ต้องการวัด ส่วนข้อมูลตามเวลาอาจมีช่วง volatility สูงติดกัน ต้องตรวจความสัมพันธ์และการเปลี่ยนระบอบแยกต่างหาก **การสลับลำดับไม่เปลี่ยนค่า JB จึงใช้ JB พิสูจน์ความเป็นอิสระข้ามเวลาไม่ได้**

ตอนนี้เรารู้แล้วว่าผลตอบแทนอาจมีรูปร่างต่างกัน แม้ mean และ SD เท่ากัน ก่อนต่อเรื่องด้านขาดทุน เราจะจัดสูตรที่เข้าใจแล้วเป็นไฟล์เรียกใช้ซ้ำ จากนั้นค่อยถามว่า ถ้าสนใจเฉพาะด้านที่ต่ำกว่าเป้าหมายหรือแย่ที่สุดบางส่วน เราจะวัดขนาดความเสี่ยงนั้นอย่างไร

<span id="python-module"></span>

## เก็บสูตรที่เข้าใจแล้วไว้ใน Python module

ตอนนี้เราคำนวณ moments ด้วยมือและตรวจด้วย SciPy ได้แล้ว หากต้องคำนวณซ้ำหลาย Notebook การคัดลอกสูตรไปทุกไฟล์ทำให้แก้ครั้งหนึ่งแล้วลืมแก้อีกที่ได้ **ฟังก์ชัน (function)** คือชุดคำสั่งที่รับข้อมูลแล้วส่งคำตอบกลับ ส่วน **module** แบบที่เราจะสร้าง คือไฟล์ `.py` ที่เก็บฟังก์ชันเหล่านั้น

ใน [Lab Session-Building your own modules](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/VDaOA/lab-session-building-your-own-modules) คอร์สเริ่มจัดระเบียบเครื่องมือไว้ในไฟล์ร่วมกัน ที่นี่เราฝึกด้วยไฟล์เล็กชื่อ `finance_tools.py` ซึ่งคำนวณ skewness และ Pearson kurtosis ด้วยนิยามที่เพิ่งเรียน ตัวโค้ดด้านล่างเป็นตัวอย่างใหม่ของบทนี้

### สร้างไฟล์ไว้ข้าง Notebook

1. สร้างโฟลเดอร์สำหรับแบบฝึกหัดนี้ และเก็บ Notebook ของเราไว้ในนั้น
2. เปิดไฟล์ข้อความใหม่ ตั้งชื่อ **`finance_tools.py`** แล้วใส่โค้ดด้านล่าง หรือ <a href="downloads/finance_tools.py" download>ดาวน์โหลดไฟล์ตัวอย่างที่ตรงกับบทนี้</a> ไปไว้ในโฟลเดอร์เดียวกัน ตรวจว่าชื่อไม่ได้ลงท้าย `.py.txt`
3. บันทึกไฟล์ก่อนกลับไปรันช่อง `import` ใน Notebook

ไฟล์ finance_tools.py

```python
"""Population-moment helpers for the hypothetical Extreme Risk lesson."""
import numpy as np


def standardized_values(data):
    """Center one finite, nonconstant series and use population SD."""
    values = np.asarray(data, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("Use one series with at least two observations.")
    if not np.isfinite(values).all():
        raise ValueError("Missing or infinite observations need review first.")
    scale = values.std(ddof=0)
    if scale == 0:
        raise ValueError("Skewness and kurtosis need nonzero dispersion.")
    return (values - values.mean()) / scale


def skewness(data):
    """Return the third standardized moment (no bias correction)."""
    z = standardized_values(data)
    return float((z ** 3).mean())


def kurtosis(data):
    """Return Pearson kurtosis; a Normal population has value 3."""
    z = standardized_values(data)
    return float((z ** 4).mean())
```

`def` กำหนดชื่อฟังก์ชันและข้อมูลขาเข้า บรรทัดในฟังก์ชันเยื้องสี่ช่อง ส่วน `return` ส่งผลกลับให้ผู้เรียก `standardized_values` แปลงข้อมูลเป็น NumPy array ชนิดตัวเลข (`dtype=float`) แล้วสร้างค่า $z$ ด้วยการลบ mean และหาร population SD ฟังก์ชันสองตัวถัดไปจึงรับ $z$ มายกกำลังสามหรือสี่ได้เลย

ส่วน `if` ตรวจเงื่อนไขก่อนคำนวณ: `.ndim` คือจำนวนมิติ, `.size` คือจำนวนข้อมูล และ `np.isfinite(...).all()` ตรวจว่าทุกค่ามีค่าตัวเลขจำกัด ถ้าข้อมูลขาดหายหรือเป็นค่าคงที่ `raise ValueError(...)` จะหยุดพร้อมข้อความ แทนการคืนตัวเลขที่เราอาจนำไปตีความผิด ฟังก์ชันนี้รับ **หนึ่งคอลัมน์ต่อครั้ง** และไม่ทิ้งข้อมูลหายให้อัตโนมัติ

### เรียกใช้ด้วยชื่อไฟล์ ไม่ต้องใส่ .py

กลับมาที่ Notebook ซึ่งยังมี `shape_data` จากส่วนก่อน แล้วรัน

```python
import finance_tools as ft

module_skew = ft.skewness(shape_data["LeftTail"])
module_kurt = ft.kurtosis(shape_data["LeftTail"])
print(f"Skewness: {module_skew:.6f}")
print(f"Pearson kurtosis: {module_kurt:.6f}")
```

ได้ **−2.666667** และ **8.111111** เหมือนเดิม `as ft` เป็นชื่อย่อ; `ft.skewness` หมายถึงฟังก์ชัน skewness ที่อยู่ใน module นี้ `import` ไม่ได้ติดตั้งแพ็กเกจใหม่ แต่ค้นหาและโหลดโค้ดจากเส้นทางที่ Python มองเห็น

หากพบ `ModuleNotFoundError: No module named 'finance_tools'` ให้ตรวจชื่อไฟล์และโฟลเดอร์ทำงานก่อน ใช้ `Path.cwd()` เพื่อดูตำแหน่งที่ Notebook กำลังทำงาน และตรวจว่ามีไฟล์ตัวอย่างอยู่จริง

```python
from pathlib import Path

print(Path.cwd())
print(Path("finance_tools.py").is_file())
```

บรรทัดแรกจะแตกต่างกันตามเครื่อง ส่วนบรรทัดที่สองควรเป็น `True` เมื่อทำตามการจัดโฟลเดอร์ข้างต้น ไม่ควรแก้ด้วยการคัดลอกไฟล์หลายเวอร์ชันกระจายไปทั่วเครื่อง เพราะจะไม่รู้ว่า Notebook กำลังใช้เวอร์ชันใด

### แก้ไฟล์แล้วทำไมคำตอบยังเหมือนเดิม?

Python เก็บ module ที่โหลดแล้วไว้ในหน่วยความจำ การสั่ง `import` ซ้ำจึงไม่ได้อ่านไฟล์ใหม่ทุกครั้ง วิธีเริ่มต้นที่ชัดที่สุดคือ **บันทึกไฟล์ → restart kernel → รันช่องใหม่ตามลำดับ** อีกวิธีสำหรับการทดลองแก้ฟังก์ชันแบบง่ายคือใช้ `importlib.reload` กับชื่อ module แล้วเรียกฟังก์ชันผ่าน `ft` อีกครั้ง

```python
import importlib

ft = importlib.reload(ft)
print(f"Reloaded skewness: {ft.skewness(shape_data['LeftTail']):.6f}")
```

ใน Jupyter/IPython คอร์สยังใช้ `%load_ext autoreload` แล้วตามด้วย `%autoreload 2` เพื่อช่วยโหลด module ที่แก้ใหม่ก่อนรันช่องถัดไป คำสั่งที่ขึ้นต้นด้วย `%` นี้เป็น **IPython magic** จึงไม่ควรย้ายไปไว้ในไฟล์ `.py` และมีข้อจำกัดบางกรณี เมื่อจะตรวจคำตอบสุดท้ายให้ restart kernel แล้วรันใหม่ทั้งหมดเสมอ ดู [Python: Modules](https://docs.python.org/3/tutorial/modules.html) และ [IPython: autoreload](https://ipython.readthedocs.io/en/stable/config/extensions/autoreload.html)

<span id="downside-measures"></span>

## ก่อนวัดด้านขาดทุน: ต่ำกว่าเกณฑ์ไหน และหารด้วยกี่งวด

เมื่อรู้แล้วว่าข้อมูลอาจไม่สมมาตรและมีหางต่างจาก Normal เราจะเปลี่ยนคำถามจาก “ผลตอบแทนแกว่งมากแค่ไหน” เป็น “ผลตอบแทนส่วนที่ไม่ต้องการมีขนาดเท่าไร” ตัววัดกลุ่มนี้เรียกว่า **downside risk measures** แต่คำว่า downside ยังไม่ใช่สูตร ต้องระบุเกณฑ์ที่ใช้เทียบก่อน

กลับไปใช้ข้อมูลสมมติ 4 งวดจาก [บทผลตอบแทน](returns.html#risk-downside): −2%, 0%, +2%, +4% โดยแต่ละงวดยาวเท่ากัน ค่าเฉลี่ยเท่ากับ 1% ตัวอย่างนี้ใช้จำนวนเล็กเพื่อให้คำนวณด้วยมือได้ ไม่ใช่ข้อมูลสินทรัพย์จริง

```python
risk_r = pd.Series([-0.02, 0.00, 0.02, 0.04])
risk_target = 0.0
risk_shortfall = (risk_target - risk_r).clip(lower=0)
print(risk_shortfall.to_list())
```

ได้ `[0.02, 0.0, 0.0, 0.0]` เพราะเราตั้ง target ไว้ที่ 0% งวดที่ได้ −2% จึงขาดจากเป้าหมาย 2 percentage points ส่วนงวดอื่นไม่ได้ต่ำกว่าเป้าหมาย `.clip(lower=0)` เปลี่ยนค่าลบให้เป็นศูนย์ จึงเหลือเฉพาะขนาดส่วนที่ขาด

### Lower partial moment: เลือกให้น้ำหนักส่วนที่ขาด

**Lower partial moment หรือ LPM** คือค่าเฉลี่ยของส่วนที่ผลตอบแทนต่ำกว่า target หลังยกกำลังที่เลือก ให้ $\tau$ เป็น target, $R_i$ เป็น simple return งวดที่ $i$, $n$ เป็นจำนวนงวด และ $p>0$ เป็นกำลัง

$$
\widehat{\mathrm{LPM}}_p(\tau)
=\frac{1}{n}\sum_{i=1}^{n}\left[\max(\tau-R_i,0)\right]^p.
$$

อ่านสูตรจากข้างในออกมา: หา target ลบ return → เก็บเฉพาะค่าบวก → ยกกำลัง → เฉลี่ยโดยนับ **ทุกงวด** หากเลือก $p=1$ จะได้ขนาดส่วนที่ขาดเฉลี่ยต่อหนึ่งงวด หากเลือก $p=2$ การขาดจากเป้าหมายมากจะมีน้ำหนักเพิ่มขึ้น จากนั้นถอดรากเพื่อให้หน่วยกลับมาเป็นหน่วยเดียวกับ return

```python
risk_lpm1 = risk_shortfall.mean()
risk_lpm2 = risk_shortfall.pow(2).mean()
risk_downside = risk_lpm2 ** 0.5
print(f"Average shortfall across all periods: {risk_lpm1:.3%}")
print(f"Target-zero downside deviation: {risk_downside:.3%}")
```

ได้ **0.500%** และ **1.000%** ตามลำดับ ตัวแรกหารขนาดที่ขาด 2% ด้วย 4 งวด ส่วนตัวหลังคือ $\sqrt{0.02^2/4}=0.01$ ทั้งคู่บอกเรื่องการขาดจาก target ไม่ใช่ค่าเฉลี่ยของหาง 5% ที่จะใช้กับ Expected Shortfall ในหัวข้อถัดไป

### ชื่อคล้ายกัน แต่สาม convention นี้ไม่ใช่ค่าเดียวกัน

| สูตร | เลือกข้อมูลอะไร | วัดห่างจากอะไร และหารด้วยอะไร | ผลในตัวอย่าง |
|---|---|---|---:|
| Semideviation ตามหน้าแก้ไขของคอร์ส | งวดที่ต่ำกว่า mean ของข้อมูลทั้งหมด | ยกกำลังสองความห่างจาก mean ทั้งชุด หารจำนวนงวดในกลุ่มนั้น แล้วถอดราก | **2.236%** |
| `semideviation` ใน Lab 106 | งวดที่ return ติดลบ | std รอบ mean ของกลุ่มติดลบ โดย `ddof=0` | **0%** |
| Downside deviation แบบ target ที่ใช้ในเว็บไซต์ | ทุกงวด โดยงวดที่ไม่ต่ำกว่า target มี shortfall เป็นศูนย์ | ยกกำลังสองส่วนที่ขาดจาก target หารจำนวนทุกงวด แล้วถอดราก | **1.000%** เมื่อ target = 0 |

สูตรตามหน้าแก้ไขเลือก −2% กับ 0% เพราะต่ำกว่า mean 1% ทั้งคู่ ความห่างจึงเป็น −3 และ −1 percentage points ได้ $\sqrt{(0.03^2+0.01^2)/2}\approx2.236\%$ ส่วน Lab เลือกเพียง −2% จึงได้ std ของข้อมูลค่าเดียวเท่ากับ 0 เมื่อ `ddof=0` นี่หมายถึงไม่มีการกระจายภายในกลุ่มที่เลือก ไม่ได้หมายถึงไม่มีการขาดทุน

```python
risk_centered = risk_r - risk_r.mean()
risk_below_mean = risk_centered[risk_centered < 0]
risk_course_semi = np.sqrt(risk_below_mean.pow(2).mean())
risk_lab_semi = risk_r[risk_r < 0].std(ddof=0)
print(f"Course correction convention: {risk_course_semi:.3%}")
print(f"Lab 106 convention: {risk_lab_semi:.3%}")
```

เวลาเทียบผลต้องระบุสูตร ไม่แก้ชื่อให้เหมือนกันแล้วคาดหวังว่าคำตอบจะตรงกัน อ่าน [คำแก้ไข Semi Deviation ของคอร์ส](https://www.coursera.org/learn/introduction-portfolio-construction-python/supplement/SzIC4/semi-deviation) ควบคู่กับ Lab 106 ได้ หากไม่มีข้อมูลใต้ mean หรือติดลบเลย การเฉลี่ยหรือ std ของกลุ่มว่างจะไม่สามารถประมาณได้ ขณะที่ LPM รอบ target อาจเป็นศูนย์ได้หากทุกงวดทำได้ถึง target นี่เป็นอีกเหตุผลที่ไม่ควรแทน missing result ทุกตัวด้วยศูนย์

<span id="historical-loss-quantiles"></span>

## Historical VaR: วางขอบบนแกนการขาดทุน

ใช้ข้อมูลสมมติ 20 วันชุดเดียวกับ [Returns](returns.html#risk-var) ต่อ เพื่อแยกผลของ “วิธีคำนวณ” ออกจากผลของ “เปลี่ยนข้อมูล” ข้อมูลถูกเรียงจาก return ต่ำไปสูงแล้วเพื่อให้อ่านสะดวก การเรียงนี้ใช้หา quantile ไม่ใช้แทนลำดับเวลาจริงในการคำนวณ drawdown

```python
tail_r = pd.Series([
    -0.120, -0.060, -0.040, -0.030, -0.025,
    -0.020, -0.015, -0.010, -0.005,  0.000,
     0.002,  0.004,  0.006,  0.008,  0.010,
     0.012,  0.015,  0.020,  0.030,  0.040,
])
tail_loss = -tail_r
```

นิยาม $L=-R$ ทำให้ return −12% กลายเป็น loss +12% และ return +4% กลายเป็น loss −4% ดังนั้น loss อาจติดลบได้ ซึ่งหมายถึงกำไร เราไม่ใช้ absolute value เพราะจะทำให้กำไรกลายเป็นขาดทุนไปด้วย

ให้ $c$ เป็น confidence เช่น $c=0.95$ และ $\alpha=1-c=0.05$ เป็นสัดส่วนหางที่สนใจ **VaR ที่ confidence 95%** ในบทนี้คือ quantile 95% ของ loss โดยเลือกค่าที่ทำให้สัดส่วนสะสมถึง 95% เป็นครั้งแรก วิธีนี้เรียกว่า empirical inverse CDF และตรงกับ convention ของเครื่องมือเว็บไซต์

เมื่อเรียง loss จากน้อยไปมาก ข้อมูลแต่ละตัวมีน้ำหนัก $1/20=5\%$ อันดับที่ 18, 19 และ 20 คือ loss 4%, 6% และ 12% ตามลำดับ

| Confidence | ต้องสะสมถึงกี่ observations จาก 20 | Loss อันดับที่เลือก | Historical VaR หนึ่งวัน |
|---:|---:|---:|---:|
| 90% | 18 | 18 | **4%** |
| 95% | 19 | 19 | **6%** |
| 97.5% | 19.5 จึงขยับไปค่าที่สะสมถึงเป็นครั้งแรก | 20 | **12%** |

```python
for tail_confidence in [0.90, 0.95, 0.975]:
    tail_v = np.quantile(
        tail_loss, tail_confidence, method="inverted_cdf"
    )
    print(f"Confidence {tail_confidence:.1%}: VaR {tail_v:.2%}")
```

`method="inverted_cdf"` ระบุวิธีเลือกขอบอย่างชัดเจน ส่วน `for` ให้ Python ทำขั้นตอนเดิมกับแต่ละค่า confidence โดยบรรทัดที่เยื้องอยู่ด้านในจะทำซ้ำ การเพิ่ม confidence อาจทำให้ VaR กระโดดเป็นขั้น เพราะข้อมูลมีเพียง 20 ค่า

คำว่า VaR หนึ่งวัน 6% ไม่ใช่คำรับรองว่าขาดทุนได้มากที่สุด 6% ข้อมูลตัวอย่างมีวันที่ขาดทุน 12% อยู่แล้ว และไม่รับรองว่าโอกาสเกินขอบในอนาคตจะเท่ากับ 5% เรากำลังใช้ตัวอย่างประมาณการแจกแจงที่ยังไม่รู้

<span id="expected-shortfall-weights"></span>

## Expected Shortfall: เฉลี่ยให้ครบสัดส่วนหาง แม้จำนวนวันไม่ลงตัว

VaR สนใจขอบ ส่วน **Expected Shortfall (ES)** สนใจค่าเฉลี่ยของ loss ในหางที่แย่ที่สุดตามสัดส่วนที่เลือก บทนี้ใช้ชื่อ **CVaR** ในความหมายเดียวกับ ES แบบถ่วงน้ำหนักหางพอดี มิใช่การเลือกทุกค่าที่ผ่าน cutoff แล้วเฉลี่ยโดยไม่ดูจำนวน

สำหรับ 20 observations แต่ละตัวหนัก 5% ถ้าต้องการหาง 10% เราใช้สองค่าที่แย่ที่สุด ถ้าต้องการหาง 5% ใช้หนึ่งค่า และถ้าต้องการหาง 2.5% ใช้ **ครึ่งหนึ่งของน้ำหนัก** ของ observation ที่แย่ที่สุด การแบ่งน้ำหนักไม่ได้แบ่งเงินที่ขาดทุนครึ่งหนึ่ง แต่แบ่งส่วนที่ observation นั้นมีอยู่ในการแจกแจงตัวอย่าง

| Confidence | สัดส่วนหาง | จำนวน observations แบบเทียบเท่า | น้ำหนักจากแย่สุดลงมา | ES หนึ่งวัน |
|---:|---:|---:|---|---:|
| 90% | 10% | 2 | 1 ของ loss 12% และ 1 ของ loss 6% | **9%** |
| 92.5% | 7.5% | 1.5 | 1 ของ loss 12% และ 0.5 ของ loss 6% | **10%** |
| 95% | 5% | 1 | 1 ของ loss 12% | **12%** |
| 97.5% | 2.5% | 0.5 | 0.5 ของ loss 12% | **12%** |

ที่ 92.5% คำตอบคือ $(1\times12\%+0.5\times6\%)/1.5=10\%$ ส่วนที่ 97.5% คือ $(0.5\times12\%)/0.5=12\%$ การหารด้วยน้ำหนักรวมทำให้เห็นว่าทำไมค่า ES ไม่เหลือ 6% เมื่อใช้ครึ่ง observation

### สร้างฟังก์ชันที่รับ confidence โดยตรง

ฟังก์ชันด้านล่างรับผลตอบแทนหนึ่งชุดแบบหนึ่งมิติ และถือว่าแต่ละ observation มีน้ำหนักเท่ากัน ชื่อ `confidence=0.95` หมายถึง 95% จึงต่างจาก `level=5` ใน toolkit ของคอร์สที่หมายถึง **หาง 5%** อย่าส่ง 95 ไปแทน 0.95

```python
def _tail_sample(returns, confidence):
    values = np.asarray(returns, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("Use a non-empty one-dimensional return series.")
    if not np.isfinite(values).all():
        raise ValueError("Resolve missing or infinite returns first.")
    if not np.isscalar(confidence):
        raise ValueError("Confidence must be one number between 0 and 1.")
    confidence = float(confidence)
    if not np.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("Confidence must be strictly between 0 and 1.")
    return -values, confidence


def var_historic(returns, confidence=0.95):
    losses, confidence = _tail_sample(returns, confidence)
    return float(np.quantile(losses, confidence, method="inverted_cdf"))


def expected_shortfall(returns, confidence=0.95):
    losses, confidence = _tail_sample(returns, confidence)
    worst_first = np.sort(losses)[::-1]
    tail_size = (1 - confidence) * len(worst_first)
    weights = np.clip(tail_size - np.arange(len(worst_first)), 0, 1)
    return float(np.dot(weights, worst_first) / weights.sum())


for tail_confidence in [0.90, 0.925, 0.95, 0.975]:
    print(
        f"{tail_confidence:.1%}: "
        f"VaR {var_historic(tail_r, tail_confidence):.2%}, "
        f"ES {expected_shortfall(tail_r, tail_confidence):.2%}"
    )
```

ผลตามลำดับคือ **4%/9%, 6%/10%, 6%/12%, 12%/12%** เมื่ออ่านแต่ละคู่เป็น VaR/ES

ไม่ต้องจำ code ทั้งก้อน ให้ตามขั้นตอนของ `expected_shortfall`: `np.sort` เรียง loss → `[::-1]` กลับลำดับให้แย่ที่สุดอยู่ก่อน → `tail_size` คำนวณว่าหางหนักเท่ากับกี่ observations → สร้างน้ำหนัก → คูณ loss กับน้ำหนักแล้วหารน้ำหนักรวม

`np.arange(n)` สร้างเลข 0 ถึง $n-1$ ถ้า `tail_size=1.5` การคำนวณ `np.clip(1.5 - ..., 0, 1)` จะได้ `[1, 0.5, 0, ...]` ส่วน `np.dot` คูณสมาชิกตำแหน่งเดียวกันแล้วนำมาบวก คล้ายการหาผลตอบแทนพอร์ตแบบถ่วงน้ำหนัก `_tail_sample` เป็น helper ตรวจ input ที่สองฟังก์ชันใช้ร่วมกัน; เครื่องหมาย `_` ด้านหน้าเป็นธรรมเนียมบอกว่าออกแบบไว้ใช้ภายใน

### ถ้าค่าบริเวณขอบซ้ำกันล่ะ

สมมติข้อมูลอีกชุดมี returns −12%, −6%, −6% และ +1% อีก 17 งวด ถ้าต้องการ ES ที่ 92.5% ใช้ loss 12% เต็มหนึ่งส่วนและ loss 6% อีกครึ่งส่วน จึงได้ 10% เท่าเดิม เราไม่จำเป็นต้องเลือกว่า loss 6% มาจากวันไหน เพราะค่าที่นำไปคูณน้ำหนักเท่ากัน

```python
tail_ties = pd.Series([-0.12, -0.06, -0.06] + [0.01] * 17)
print(f"ES with ties at 92.5%: {expected_shortfall(tail_ties, 0.925):.2%}")
```

ได้ **10.00%** ขณะที่การเฉลี่ย loss ทุกค่าที่มากกว่าหรือเท่ากับ VaR 6% จะดึง 3 observations หรือ 15% เข้ามาและได้ 8% ส่วนการเลือกเฉพาะ loss มากกว่า 6% จะเหลือหนึ่ง observation และได้ 12% ทั้งสองวิธีไม่ได้ใช้หาง 7.5% ตามโจทย์

หลักการถ่วงน้ำหนักขอบมีความสำคัญเมื่อข้อมูลมีมวลเป็นจุดหรือมีค่าซ้ำ ไม่จำเป็นต้องใช้เพียงนิยาม conditional mean แบบต่อเนื่อง ดูประเด็นนี้เพิ่มเติมในงานต้นทางของ [Acerbi และ Tasche](https://arxiv.org/abs/cond-mat/0104295)

<span id="lab-site-tail-conventions"></span>

## ทำไมคำตอบจาก Lab อาจไม่เท่ากับเว็บไซต์

`edhec_risk_kit_106.py` หา Historical VaR ด้วย `-np.percentile(returns, level)` ซึ่งใช้ linear interpolation ตามค่าเริ่มต้น แล้วหา CVaR โดยเฉลี่ย returns ทุกตัวที่ต่ำกว่าหรือเท่ากับขอบ return ที่คำนวณได้ วิธีนี้ต่างจาก loss inverse CDF และ ES แบบเติมน้ำหนักหางให้ครบที่เราเพิ่งเขียน

ลองคำนวณจากข้อมูล 20 วันชุดเดียวกัน โดยระบุ `method="linear"` ให้เห็น convention โดยไม่ต้องนำไฟล์ toolkit ของคอร์สเข้ามา

```python
tail_lab_rows = []
for tail_confidence in [0.90, 0.925, 0.95, 0.975]:
    tail_alpha = 1 - tail_confidence
    tail_lab_var = -np.percentile(tail_r, 100 * tail_alpha, method="linear")
    tail_lab_cvar = -tail_r[tail_r <= -tail_lab_var].mean()
    tail_lab_rows.append({
        "Confidence": tail_confidence,
        "Site VaR": var_historic(tail_r, tail_confidence),
        "Lab VaR": tail_lab_var,
        "Exact-tail ES": expected_shortfall(tail_r, tail_confidence),
        "Lab tail mean": tail_lab_cvar,
    })
print(pd.DataFrame(tail_lab_rows).round(4))
```

| Confidence | VaR บน loss แบบเว็บไซต์ | VaR แบบ linear ของ Lab | ES ถ่วงหางพอดี | Tail mean ตาม Lab |
|---:|---:|---:|---:|---:|
| 90% | 4.00% | 4.20% | 9.00% | 9.00% |
| 92.5% | 6.00% | 5.15% | **10.00%** | **9.00%** |
| 95% | 6.00% | 6.30% | 12.00% | 12.00% |
| 97.5% | 12.00% | 9.15% | 12.00% | 12.00% |

ที่ confidence 95% การหา quantile บน return แบบ linear แทรกค่าระหว่าง −12% กับ −6% จึงได้ขอบ −6.3% ไม่ใช่ loss 6% ของ inverse CDF ส่วนที่ 92.5% ขอบ Lab คือ return −5.15% ทำให้เลือก −12% และ −6% ทั้งสองค่า จึงเฉลี่ยหาง 10% แทนหาง 7.5% ที่ต้องการ

ดังนั้นสิ่งแรกที่ตรวจเมื่อคำตอบไม่ตรงกันคือ input, หน่วย, confidence, quantile method และนิยาม tail mean ไม่ใช่เปลี่ยนสูตรไปเรื่อย ๆ จนตัวเลขเหมือนกัน เอกสาร [NumPy quantile](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html) อธิบายความต่างระหว่างวิธีเลือกขอบ; `quantile` รับ probability 0–1 ส่วน `percentile` รับระดับ 0–100

<span id="gaussian-var-calculation"></span>

## Gaussian VaR: จาก mean และ std ไปหาขอบในกระดิ่ง

Historical VaR ใช้ค่าที่สังเกต ส่วน **Gaussian VaR** ตั้งสมมติฐานว่า returns มีการแจกแจง Normal จากนั้นใช้ mean และ std ที่ประมาณจากข้อมูลกำหนดกระดิ่ง คำว่า **parametric** หมายถึงเริ่มจากรูปแบบแจกแจงที่เลือกแล้วประมาณพารามิเตอร์ของมัน

ใน Standard Normal ค่าเฉลี่ยเป็น 0 และ std เป็น 1 ถ้าต้องการขอบด้านล่างที่มี probability 5% จะได้ $z_{0.05}\approx-1.644854$ เครื่องหมายลบหมายถึงอยู่ด้านซ้ายของ mean ฟังก์ชัน `stats.norm.ppf(0.05)` ทำหน้าที่หาเลขนี้ โดย `ppf` เป็น inverse ของ cumulative distribution function

$$
\widehat{\mathrm{VaR}}^{\mathrm{Gaussian}}_c
=-\left(\hat\mu+z_{1-c}\hat\sigma\right).
$$

$\hat\mu$ และ $\hat\sigma$ คือ mean และ std ที่ประมาณจาก sample; หมวกบนตัวอักษรเตือนว่าไม่ใช่ค่าที่เรารู้จริงจากประชากรทั้งหมด ในตัวอย่างนี้เลือก `ddof=0` ให้ตรงกับสูตร moment ที่ใช้ใน Lab และ Cornish–Fisher ถัดไป

```python
tail_mu = tail_r.mean()
tail_sigma = tail_r.std(ddof=0)
tail_confidence = 0.95
tail_z = stats.norm.ppf(1 - tail_confidence)
tail_gaussian_var = -(tail_mu + tail_z * tail_sigma)

print(f"Mean per day: {tail_mu:.3%}")
print(f"Population-convention std per day: {tail_sigma:.3%}")
print(f"Lower-tail z: {tail_z:.6f}")
print(f"Gaussian one-day VaR (95%): {tail_gaussian_var:.3%}")
```

ได้ mean **−0.890% ต่อวัน**, std **3.448% ต่อวัน**, $z=-1.644854$ และ Gaussian VaR **6.562% ต่อวัน** การคำนวณไม่จำเป็นต้องสุ่ม Normal เพิ่มเพื่อหา quantile เพราะใช้ `ppf` ได้โดยตรง ดูนิยามพารามิเตอร์และ `ppf` ใน [SciPy Normal distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html)

Gaussian VaR ที่มากกว่าหรือน้อยกว่า Historical VaR ยังไม่บอกว่าวิธีใดถูกต้องสำหรับอนาคต: วิธีหนึ่งอาศัยกระดิ่งที่เลือก อีกวิธีอาศัยตัวอย่างที่ผ่านมา ซึ่งทั้งสองอาจพลาดเหตุการณ์ที่ยังไม่เห็น การเลือกรูปแจกแจงอื่น เช่น Student-t ก็ยังต้องตรวจสมมติฐานและความแม่นของพารามิเตอร์ ไม่ได้แก้ model error โดยอัตโนมัติ

<span id="cornish-fisher-steps"></span>

## Cornish–Fisher: ปรับตำแหน่ง quantile ด้วยรูปทรงข้อมูล

Cornish–Fisher ใช้ skewness และ kurtosis ปรับ $z$ ของ Normal โดยยังคงแปลงกลับด้วย $\hat\mu+z\hat\sigma$ เช่นเดิม วิธีนี้เป็น **ค่าประมาณของ quantile** ไม่ใช่การพิสูจน์ว่ารูปแจกแจงที่ได้ตรงกับตลาด

ให้ $S$ เป็น moment skewness และ $K$ เป็น **Pearson kurtosis** ซึ่งใช้ Normal = 3 สูตรที่ Lab ใช้คือ

$$
z_{\mathrm{CF}}
=z+\frac{z^2-1}{6}S
+\frac{z^3-3z}{24}(K-3)
-\frac{2z^3-5z}{36}S^2.
$$

เมื่อ $S=0$ และ $K=3$ ทุกพจน์ปรับแก้เป็นศูนย์ จึงกลับไปใช้ $z$ เดิม ระวังว่าถ้าคำนวณ **excess kurtosis** มาแล้ว ค่านั้นเท่ากับ $K-3$ อยู่แล้ว ไม่ต้องลบ 3 ซ้ำ

เริ่มจากลบ mean เพื่อหา deviations แล้วใช้ population moments ที่หารด้วย $n$ ทั้งชุด ไม่ผสมกับ sample standard deviation ที่หารด้วย $n-1$

```python
tail_centered = tail_r - tail_mu
if tail_sigma == 0:
    raise ValueError("Skewness and kurtosis need non-zero dispersion.")
tail_skew = tail_centered.pow(3).mean() / tail_sigma ** 3
tail_kurtosis = tail_centered.pow(4).mean() / tail_sigma ** 4

tail_z_cf = (
    tail_z
    + (tail_z ** 2 - 1) * tail_skew / 6
    + (tail_z ** 3 - 3 * tail_z) * (tail_kurtosis - 3) / 24
    - (2 * tail_z ** 3 - 5 * tail_z) * tail_skew ** 2 / 36
)
tail_cf_var = -(tail_mu + tail_z_cf * tail_sigma)

print(f"Moment skewness: {tail_skew:.6f}")
print(f"Pearson kurtosis: {tail_kurtosis:.6f}")
print(f"Adjusted z: {tail_z_cf:.6f}")
print(f"Cornish-Fisher one-day VaR (95%): {tail_cf_var:.3%}")
```

ได้ $S\approx-1.595429$, $K\approx6.009768$, $z_{\mathrm{CF}}\approx-1.989817$ และ VaR **7.751% ต่อวัน** เทียบกับ Gaussian **6.562%** และ Historical แบบเว็บไซต์ **6.000%** ที่ confidence 95% เท่ากัน

**ในตัวอย่างนี้** การปรับทำให้ VaR สูงขึ้น แต่ไม่ใช่กฎว่า Cornish–Fisher ต้องสูงกว่า Gaussian เสมอ ทิศทางขึ้นกับ $z$, skewness และ kurtosis ที่ใช้ โดยเฉพาะเมื่อ moments มีขนาดมากหรือประมาณจากข้อมูลน้อย สูตรประมาณอาจให้รูป quantile ที่ไม่น่าเชื่อถือ จึงต้องตรวจว่าผลตามหลายระดับ confidence เรียงตามลำดับสมเหตุสมผลด้วย การผ่านการตรวจนี้เพียงอย่างเดียวก็ยังไม่ยืนยันโมเดล

ตัวอย่าง 20 วันทำให้เห็นกลไกของสูตร แต่ไม่เพียงพอให้เชื่อถือประมาณการหางละเอียด หากเปลี่ยนวัน −12% เพียงวันเดียว mean, std, skewness และ kurtosis จะเปลี่ยนตามทั้งหมด การแสดงทศนิยมหลายหลักมีไว้ตรวจ code ไม่ใช่แสดงความแม่นของการพยากรณ์

<span id="extreme-risk-input-checks"></span>

## ก่อนอ่านผล ต้องรู้ว่าตัวเลขกำลังตอบคำถามเดียวกัน

เลือกตัววัดตามคำถาม แล้วบันทึกเงื่อนไขที่ใช้ให้คนอื่นคำนวณซ้ำได้ แค่บอกว่า “VaR เท่ากับ 6%” ยังขาดทั้งช่วงเวลา ความเชื่อมั่น และวิธีประมาณ

| สิ่งที่ต้องระบุ | ตัวอย่างที่ชัดเจน | ทำไมจึงมีผล |
|---|---|---|
| หน่วยและนิยาม | Simple total return รายวันในรูปทศนิยม | ใส่ −2 แทน −0.02 จะทำให้ขนาดคลาดเคลื่อน 100 เท่า |
| ช่วงข้อมูล | 20 observations สมมติที่เปิดให้ดูครบ | ช่วงตลาดที่ต่างกันและจำนวนข้อมูลต่างกันทำให้หางต่างกัน |
| Confidence และช่วงเวลาของ loss | One-day 95% VaR | 95% ต่อวันกับ 95% ต่อเดือนเป็นคนละคำถาม |
| วิธีเลือกขอบและหาง | Loss inverse CDF; ES ถ่วงหางให้ครบ 5% | แก้ความกำกวมเมื่อขอบมีค่าซ้ำหรือจำนวน observations ไม่ลงตัว |
| วิธีจัดการข้อมูลหาย | ตรวจเหตุผลก่อนเลือกตัดหรือแก้ข้อมูล | การลบวันที่ผิดปกติหรือเติมเป็น 0 อาจทำให้ความเสี่ยงดูต่ำลง |
| สมมติฐานแบบจำลอง | Historical, Gaussian หรือ Cornish–Fisher | ตัวเลขใกล้กันไม่ได้แปลว่าสมมติฐานตรงกับอนาคต |

ฟังก์ชันด้านบนจึงปฏิเสธ input ว่าง, ข้อมูลมากกว่าหนึ่งมิติ, `NaN`, infinity และ confidence นอกช่วงเปิด $(0,1)$ เพื่อให้ตรวจต้นเหตุก่อนคำนวณ แต่ยังไม่ได้รู้แทนเราว่าราคาเรียงวันถูกต้องหรือปรับปันผลแล้วหรือยัง หากมีหลายสินทรัพย์ต้องจัดวันให้ตรงกันและสร้าง portfolio returns ก่อนใช้กับพอร์ตทั้งก้อน ไม่ใช่นำ VaR ของแต่ละสินทรัพย์มาบวกโดยไม่พิจารณาว่าขาดทุนพร้อมกันหรือไม่

สำหรับการเปรียบเทียบข้ามเวลา อย่านำ one-day VaR หรือ ES คูณ $\sqrt{252}$ โดยอัตโนมัติ การขยายช่วงเวลาต้องคิดเรื่องการทบต้น ความสัมพันธ์ข้ามวัน และสมมติฐานการแจกแจงด้วย นอกจากนี้ข้อมูลรายวันอาจไม่เห็นความเสียหายระหว่างวันเช่นเดียวกับ drawdown ที่ขึ้นกับความถี่การสังเกต

ควรแยก **estimation error** จากการมีตัวอย่างจำกัด กับ **model error** จากรูปแบบจำลองไม่เหมาะสม การเพิ่มข้อมูลอาจช่วยส่วนแรกภายใต้เงื่อนไขที่เหมาะสม แต่ไม่ทำให้สมมติฐาน Normal ที่ไม่เหมาะกับโจทย์กลายเป็นจริง และการเพิ่ม confidence บน sample เล็กไม่ได้สร้างข้อมูลหางใหม่ขึ้นมา

<span id="extreme-tail-practice"></span>

## ฝึกอธิบายผล ก่อนเชื่อผลจากฟังก์ชัน

แบบฝึกหัดต่อไปนี้สร้างขึ้นสำหรับบทนี้เอง ใช้ข้อมูลสมมติที่เปิดไว้ทั้งหมด และไม่ใช่คำถามประเมินคะแนนของคอร์ส

1. ใน `risk_r` ถ้าใช้ target 1% แทน 0% ค่า downside deviation แบบหารทุกงวดจะเป็นเท่าไร? เหตุใดไม่เท่ากับ semideviation 2.236% ตามหน้าแก้ไข?
2. ใน `tail_r` ที่ confidence 97.5% เราควรพูดว่าใช้ข้อมูล “ครึ่งวัน” หรือ “ครึ่งหนึ่งของน้ำหนัก observation” เพราะอะไร?
3. ถ้าต้องการ confidence 92.5% ทำไม ES จึงเท่ากับ 10% แต่ threshold tail mean ของ Lab ได้ 9%?
4. ในชุด `tail_ties` ลองทาย ES 90% ก่อนรัน แล้วอธิบายว่าทำไมไม่เฉลี่ย loss 12%, 6%, 6% ทั้งสามตัว?
5. ถ้า skewness เป็น 0 และ Pearson kurtosis เป็น 3 สูตร Cornish–Fisher จะเหลืออะไร? ถ้าฟังก์ชันคืน excess kurtosis มาแล้ว ต้องใส่ลงตรงไหน?
6. เพราะเหตุใดผล Gaussian VaR 6.562% และ Cornish–Fisher 7.751% จึงยังไม่ใช่หลักฐานว่าวิธีหลังพยากรณ์ได้ดีกว่า?

<details>
<summary>เปิดแนวคำตอบและเหตุผล</summary>

1. Shortfalls คือ 3%, 1%, 0%, 0% จึงได้ $\sqrt{(0.03^2+0.01^2)/4}\approx1.581\%$; หน้าแก้ไขหารเฉพาะ 2 observations ที่ต่ำกว่า mean จึงได้ค่ามากกว่า
2. เป็นครึ่งหนึ่งของน้ำหนัก observation ในการแจกแจงตัวอย่าง ผลตอบแทน −12% ยังเป็นผลตอบแทนเต็มหนึ่งวัน ไม่ได้เปลี่ยนเป็นผลตอบแทนครึ่งวัน −6%
3. หาง 7.5% ของ 20 ตัวมีน้ำหนัก 1.5 observations จึงได้ $(12\%+0.5\times6\%)/1.5=10\%$; threshold ของ Lab ดึงสอง observations เต็มเข้ามาและได้ 9%
4. ES 90% เท่ากับ $(12\%+6\%)/2=9\%$ การรวมทั้งสามตัวจะมีน้ำหนักหาง 15% แทน 10% ค่าที่ขอบซ้ำกันไม่เปลี่ยนเป้าหมายสัดส่วนหาง
5. เหลือ $z$ เดิม; ใส่ excess kurtosis ลงแทนพจน์ $(K-3)$ โดยไม่ลบ 3 อีกครั้ง
6. เราคำนวณด้วย sample เดียวที่มีเพียง 20 วัน แล้วเปลี่ยนสมมติฐานและสูตร ยังไม่มีหลักฐานทดสอบกับข้อมูลใหม่ว่าขอบที่ประมาณสอบเทียบดีเพียงใด ตัวเลขสูงกว่าเพียงอย่างเดียวไม่ได้แปลว่าแม่นกว่า

</details>

แหล่งเรียนส่วนนี้คือ [Downside Risk Measures](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/Xeixz/downside-risk-measures), [Estimating VaR](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/Tlpi8/estimating-var), หน้าแก้ไข Semi Deviation และ Lab 106/`edhec_risk_kit_106.py` ของ EDHEC/Coursera ตัวอย่างข้อมูลและฟังก์ชัน ES ที่ถ่วงน้ำหนักขอบในบทนี้เขียนขึ้นใหม่ เพื่อให้ convention ชัดและตรวจผลด้วยมือได้

<span id="references"></span>

## แหล่งเรียนและวิธีตรวจตัวอย่าง

บทนี้เรียบเรียงใหม่จากหัวข้อ **Section 2 ของ Module 1** ในคอร์ส EDHEC/Coursera และตรวจโค้ดใน `lab_104.ipynb`–`lab_106.ipynb` ประกอบ ตัวอย่างและฟังก์ชันในหน้านี้สร้างสำหรับบทเรียนนี้เอง จึงไม่ใช่การถอด Transcript หรือสำเนา toolkit ของคอร์ส

- [Deviations from Normality](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/fpkEu/deviations-from-normality)
- [Correction to Deviations from Normality](https://www.coursera.org/learn/introduction-portfolio-construction-python/supplement/yrJGY/incorrect-statement-in-deviation-from-normality-video)
- [Lab Session-Building your own modules](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/VDaOA/lab-session-building-your-own-modules)
- [Downside risk measures](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/Xeixz/downside-risk-measures)
- [Lab Session-Deviations from Normality](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/c8aLc/lab-session-deviations-from-normality)
- [Estimating VaR](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/Tlpi8/estimating-var)
- [Lab Session-Semi Deviation, VaR and CVaR](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/BmEcs/lab-session-semi-deviation-var-and-cvar)
- [Semi Deviation](https://www.coursera.org/learn/introduction-portfolio-construction-python/supplement/SzIC4/semi-deviation)

แหล่งเอกสารฟังก์ชันเชื่อมไว้ใกล้โค้ดแต่ละส่วน ตรวจตัวอย่างด้วย NumPy 2.0.2, pandas 2.3.3 และ SciPy 1.13.1; จำนวนตำแหน่งทศนิยมและรูปแบบการพิมพ์อาจต่างกันในเวอร์ชันอื่น แต่ควรตรวจว่านิยามและวิธีคำนวณยังตรงกัน ข้อมูลสมมติไม่ใช่หลักฐานเชิงประจักษ์ว่าตลาดใดเป็นหรือไม่เป็น Normal

หากจะทำแบบฝึกหัด **Evidence of non-normality in asset returns** ให้เลือกข้อมูลที่มีสิทธิ์ใช้งานและระบุแหล่ง ช่วงวันที่ ความถี่ การนับปันผล หน่วย จำนวนข้อมูล และการจัดการค่าหาย แล้วเปรียบเทียบ histogram, moments และผลทดสอบโดยรายงานข้อจำกัดร่วมกัน อย่าใช้ข้อมูลจำลองข้างต้นเป็นข้อสรุปเกี่ยวกับสินทรัพย์จริง

<nav class="chapter-navigation" aria-label="บทเรียนก่อนหน้าและถัดไป">
<a href="returns.html" rel="prev">บทก่อนหน้า: How to Calculate return</a>
<a href="risk.html" rel="next">อ่านต่อ: ความเสี่ยงในการลงทุน</a>
</nav>
