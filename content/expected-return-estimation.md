---
title: "Expected Return: ค่าเฉลี่ยที่เรายังไม่รู้"
description: แยกค่าเฉลี่ยย้อนหลังจากผลตอบแทนคาดหวัง คำนวณ standard error แล้วทดลอง mean shrinkage, agnostic priors และ factor forecasts ด้วยข้อมูลสมมติ
---

# Expected Return: ค่าเฉลี่ยที่เรายังไม่รู้

<p class="lead">ถ้าผลตอบแทนย้อนหลังเฉลี่ย 1% ต่อเดือน เรามีเหตุผลมากแค่ไหนที่จะใส่ 1% เป็นผลตอบแทนคาดหวังของเดือนหน้า?</p>

ใน[บทประมาณ Covariance](covariance-estimation.html) เราดูความคลาดเคลื่อนของข้อมูลด้านความเสี่ยงมาแล้ว อีกข้อมูลหนึ่งที่ optimizer ต้องใช้คือ [expected return](glossary.html#expected-return) หรือค่าเฉลี่ยของผลตอบแทนในแบบจำลองของอนาคต การคำนวณค่าเฉลี่ยย้อนหลังทำได้ด้วยการบวกและหาร แต่การนำค่าที่ได้ไปพยากรณ์ต้องเพิ่มสมมติฐานว่าประวัติช่วงนั้นบอกอะไรเกี่ยวกับอนาคตได้

บทนี้เริ่มจากผลตอบแทนหกเดือน คำนวณความไม่แน่นอนของค่าเฉลี่ย แล้วทดลองให้ความไม่แน่นอนนั้นส่งผ่านไปสู่น้ำหนักพอร์ต จากนั้นจึงใช้ shrinkage และ factor model เพื่อตั้งสมมติฐานที่มีโครงสร้างมากขึ้น เราจะระบุด้วยว่าสิ่งใดได้จากข้อมูล และสิ่งใดเป็นความเชื่อที่ใส่เพิ่ม

เนื้อหาประกอบ Module 3 ของ Advanced Portfolio Construction and Analysis with Python ตัวเลขทั้งหมดเป็นข้อมูลสมมติหรือการจำลองที่กำหนด seed ไม่มีผลทดสอบหุ้นจริง โค้ด 12 ชุดใช้ NumPy, pandas และ SciPy รันตามลำดับใน Notebook ใหม่ได้ ตัวอย่างต้นบทเป็นรายเดือน ช่วงจัดพอร์ตใช้ค่ารายปี แล้วกลับมาใช้รายเดือนในตัวอย่าง factor โดยประกาศหน่วยใหม่ทุกครั้ง

<span id="expected-return-basics"></span>

## ค่าเฉลี่ยย้อนหลังเป็นค่าที่คำนวณได้ ส่วนค่าเฉลี่ยอนาคตต้องประมาณ

ให้ $r_t$ เป็นผลตอบแทนของเดือนที่ $t$ หน่วยทศนิยม เช่น $0.02$ หมายถึง 2% ถ้ามีข้อมูล $T$ เดือน ค่าเฉลี่ยเลขคณิตของชุดข้อมูลคือ

$$
\bar r=\frac{r_1+r_2+\cdots+r_T}{T}.
$$

เครื่องหมายขีดด้านบนบอกว่าเรากำลังเฉลี่ยข้อมูลที่มีอยู่ ส่วน $\mu=E[r_{\text{next}}]$ ใช้แทนผลตอบแทนคาดหวังของช่วงถัดไปในแบบจำลอง เมื่อแบบจำลองมีหลายผลลัพธ์ ค่า $E[\cdot]$ คือค่าเฉลี่ยถ่วงน้ำหนักด้วยความน่าจะเป็นของผลลัพธ์เหล่านั้น เดือนหน้าที่เกิดขึ้นจริงอาจอยู่ไกลจาก $\mu$ ได้

สมมติเราบันทึกผลตอบแทนรวมของสินทรัพย์หนึ่งเป็น −4%, 2%, 5%, −1%, 3% และ 1% ผลบวกเท่ากับ 6% แล้วหารหกจึงได้ค่าเฉลี่ย 1% ต่อเดือน คำว่า “รวม” หมายถึงผลตอบแทนที่นับกระแสเงินสดจากสินทรัพย์ตาม convention เดียวกัน ไม่ปนราคากับผลตอบแทน

`import ... as ...` โหลดไลบรารีและตั้งชื่อย่อ `np` สำหรับ NumPy และ `pd` สำหรับ pandas `np.array` เก็บตัวเลขเป็นชุด `len` นับจำนวนสมาชิก `.sum()` บวกสมาชิกทั้งหมด และ `np.prod` คูณสมาชิกทั้งหมด `**` เป็นการยกกำลัง ส่วน `:.4%` แสดงทศนิยมเป็นเปอร์เซ็นต์สี่ตำแหน่งโดยไม่เปลี่ยนค่าที่เก็บไว้

```python
import numpy as np
import pandas as pd

mean_sample = np.array([-0.04, 0.02, 0.05, -0.01, 0.03, 0.01])
sample_size = len(mean_sample)
sample_mean = mean_sample.sum() / sample_size
sample_total = np.prod(1 + mean_sample) - 1
sample_geometric = (1 + sample_total) ** (1 / sample_size) - 1
print(f"Arithmetic mean per month: {sample_mean:.4%}")
print(f"Six-month total return: {sample_total:.4%}")
print(f"Geometric mean per month: {sample_geometric:.4%}")
```

ได้ค่าเฉลี่ยเลขคณิต 1.0000% ต่อเดือน ผลตอบแทนสะสมหกเดือน 5.8899% และค่าเฉลี่ยเรขาคณิต 0.9584% ต่อเดือน ตัวเลขสุดท้ายคืออัตราคงที่ที่ทบต้นหกครั้งแล้วได้มูลค่าปลายงวดเท่ากัน ดูวิธีทบต้นเพิ่มเติมใน[บท Returns](returns.html)

ทั้งสามค่าตอบคนละคำถาม ผลตอบแทนสะสมบอกการเปลี่ยนมูลค่าตลอดช่วง ค่าเฉลี่ยเรขาคณิตสรุปอัตราทบต้น ส่วนค่าเฉลี่ยเลขคณิตเป็นตัวประมาณที่ใช้บ่อยสำหรับค่าเฉลี่ยหนึ่งช่วงเวลา การใช้ $\bar r$ ประมาณ $\mu$ ต้องอาศัยสมมติฐานเกี่ยวกับการสุ่มและความคงที่ของกระบวนการผลตอบแทน

ตัวอย่างข้อมูลหกเดือนนี้มีไว้ตรวจเลข จึงยังไม่มีหลักฐานว่ามาจากกระบวนการใด แม้คำนวณค่าเฉลี่ยได้ถูกต้อง เราก็ยังไม่รู้จากตัวเลขหกตัวเพียงอย่างเดียวว่า expected return ของเดือนหน้าคือ 1%

<span id="mean-standard-error"></span>

## Standard error วัดความไม่แน่นอนของค่าเฉลี่ย

Standard deviation หรือ SD ของผลตอบแทนบอกการกระจายของผลตอบแทนแต่ละช่วง ส่วน [standard error](glossary.html#standard-error) หรือ SE ของค่าเฉลี่ยบอกว่า หากสุ่มประวัติใหม่หลายชุด ค่าเฉลี่ยของแต่ละชุดจะกระจายกันเท่าไร

เริ่มจากสมมติฐาน IID: ผลตอบแทนแต่ละช่วงเป็นอิสระจากกันและมาจากการแจกแจงเดียวกัน มีค่าเฉลี่ย $\mu$ และ variance $\sigma^2$ คงที่ เราจึงบวก variance ของแต่ละช่วงได้:

$$
\operatorname{Var}(\bar r)
=\frac{1}{T^2}\sum_{t=1}^{T}\operatorname{Var}(r_t)
=\frac{\sigma^2}{T},
\qquad
\operatorname{SE}(\bar r)=\frac{\sigma}{\sqrt T}.
$$

การหารด้วย $T$ ในค่าเฉลี่ยกลายเป็นการหารด้วย $T^2$ เมื่อคิด variance แล้วผลบวกมี $T$ พจน์ จึงเหลือตัวหาร $T$ ก่อนถอดราก เรามักไม่รู้ $\sigma$ จึงแทนด้วย sample SD:

$$
s=\sqrt{\frac{\sum_{t=1}^{T}(r_t-\bar r)^2}{T-1}},
\qquad \widehat{\operatorname{SE}}(\bar r)=\frac{s}{\sqrt T}.
$$

สำหรับข้อมูลหกเดือน ผลรวม squared deviations เท่ากับ 0.005 หารด้วย $6-1=5$ ได้ sample variance 0.001 จึงได้ $s\approx0.031623$ หรือ 3.1623% ต่อเดือน และ SE ของค่าเฉลี่ยเท่ากับ $0.031623/\sqrt6\approx0.012910$ หรือ 1.2910 จุดเปอร์เซ็นต์ต่อเดือน

### ช่วงความเชื่อมั่นของค่าเฉลี่ย

ถ้าเพิ่มสมมติฐานว่า observations เป็น IID Normal ช่วงความเชื่อมั่น 95% ของ $\mu$ เมื่อไม่รู้ variance คือ

$$
\bar r\pm t_{0.975,T-1}\frac{s}{\sqrt T}.
$$

$t_{0.975,T-1}$ เป็นค่าขอบของการแจกแจง Student's t ที่มีพื้นที่ด้านซ้าย 97.5% เหลือด้านขวา 2.5% และใช้ขอบล่างอีก 2.5% รวมเป็นพื้นที่หาง 5% `stats.t.ppf` คืนค่าขอบนี้ ส่วน `df` คือ degrees of freedom ซึ่งในสูตรนี้เท่ากับ $T-1$ เอกสาร [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) อธิบายสูตรและความหมายของช่วงความเชื่อมั่นนี้

```python
from scipy import stats

sample_sd = np.sqrt(np.sum((mean_sample - sample_mean) ** 2) / (sample_size - 1))
mean_se = sample_sd / np.sqrt(sample_size)
t_critical = stats.t.ppf(0.975, df=sample_size - 1)
mean_ci = sample_mean + np.array([-1, 1]) * t_critical * mean_se
print(f"Monthly return SD: {sample_sd:.4%}")
print(f"SE of monthly mean: {mean_se:.4%}")
print(f"t critical value: {t_critical:.4f}")
print("95% mean CI (% per month):", np.round(100 * mean_ci, 4))
```

`t_critical` ประมาณ 2.5706 ช่วงที่คำนวณได้คือ −2.3186% ถึง 4.3186% ต่อเดือน ภายใต้สมมติฐานที่กำหนด ข้อมูลชุดนี้ยังแยกค่าเฉลี่ยบวกเล็กน้อยออกจากศูนย์หรือค่าเฉลี่ยติดลบบางค่าได้ไม่ชัด ค่า SE ที่ใหญ่กว่าค่าเฉลี่ย 1% ช่วยให้เห็นขนาดความไม่แน่นอนนั้น

ความเชื่อมั่น 95% เป็นคุณสมบัติของวิธีสร้างช่วงเมื่อสุ่มข้อมูลซ้ำ หากเงื่อนไขของวิธีเป็นจริง ช่วงประมาณ 95% จะครอบคลุม $\mu$ ที่คงที่ ช่วงที่คำนวณจากข้อมูลชุดหนึ่งแล้วไม่ได้แปลว่าเดือนหน้าจะอยู่ในช่วงนั้นด้วยโอกาส 95% การทำนายผลตอบแทนหนึ่งเดือนยังต้องรับความผันผวนของเดือนใหม่เพิ่มเติม

ในข้อมูลตลาด การมี serial correlation หรือพารามิเตอร์เปลี่ยนตามเวลาอาจทำให้สูตร $s/\sqrt T$ บอกความไม่แน่นอนผิดขนาด ผลตอบแทนหางหนาและข้อมูลน้อยยังทำให้การใช้ t interval ตามตัวอย่างไม่แม่น ต้องเลือกวิธีอนุมานที่รองรับสมมติฐานของข้อมูลก่อนตีความช่วงที่โปรแกรมคืนมา

<span id="sampling-frequency-and-horizon"></span>

## เพิ่มความถี่ข้อมูลกับเพิ่มจำนวนปีให้ข้อมูลคนละแบบ

ลองสมมติแบบจำลองผลตอบแทนแบบบวกที่มี mean และ variance คงที่ มีช่วงย่อย $q$ ช่วงต่อปี และใช้ข้อมูลย้อนหลัง $H$ ปี จึงมี $T=qH$ observations ภายใต้ IID ให้ $\sigma_{\text{annual}}$ เป็น SD ของผลรวมผลตอบแทนหนึ่งปี จะได้

$$
\sigma_{\text{period}}=\frac{\sigma_{\text{annual}}}{\sqrt q},
\qquad
\hat\mu_{\text{annual}}=q\bar r_{\text{period}}.
$$

เมื่อคูณค่าเฉลี่ยด้วย $q$ ค่า SE ต้องคูณ $q$ เช่นกัน:

$$
\operatorname{SE}(\hat\mu_{\text{annual}})
=q\frac{\sigma_{\text{period}}}{\sqrt{qH}}
=\frac{\sigma_{\text{annual}}}{\sqrt H}.
$$

`pd.DataFrame` จัดผลลัพธ์เป็นตาราง โดยชื่อใน dictionary เป็นชื่อคอลัมน์และ `index` เป็นป้ายแถว เราเก็บการคำนวณเป็นทศนิยม แล้วคูณ 100 เฉพาะคอลัมน์ที่ต้องการแสดงเป็นเปอร์เซ็นต์

ดังนั้น ถ้า annual SD เท่ากับ 20% และมีประวัติห้าปี ค่า SE ของ annual mean เท่ากับ $20\%/\sqrt5\approx8.9443$ จุดเปอร์เซ็นต์ ทั้งกรณีข้อมูลเดือนละหนึ่งแถวและกรณีปีละ 252 วัน ภายใต้แบบจำลองเดียวกัน การเปลี่ยนความถี่ทำให้ SD ต่อแถวและจำนวนแถวเปลี่ยนชดเชยกัน

```python
annual_sigma = 0.20
history_years = 5
periods_per_year = np.array([12, 252])
observations = history_years * periods_per_year
period_sd = annual_sigma / np.sqrt(periods_per_year)
annual_mean_se = periods_per_year * period_sd / np.sqrt(observations)
frequency_table = pd.DataFrame({
    "observations": observations,
    "period_SD_pct": 100 * period_sd,
    "annual_mean_SE_pct": 100 * annual_mean_se,
}, index=["monthly", "daily"])
print(frequency_table.round(4))
years_grid = np.array([1, 4, 16, 64])
annual_se_by_year = annual_sigma / np.sqrt(years_grid)
print("Annual mean SE for 1, 4, 16, 64 years (%):", np.round(100 * annual_se_by_year, 4))
```

ตารางมี 60 เดือนหรือ 1,260 วัน SD ต่อเดือนประมาณ 5.7735% และ SD ต่อวันประมาณ 1.2599% แต่ SE ของ annual mean เท่ากัน ประวัติ 1, 4, 16 และ 64 ปีให้ SE เท่ากับ 20, 10, 5 และ 2.5 จุดเปอร์เซ็นต์ตามลำดับ การลด SE ลงครึ่งหนึ่งจึงต้องเพิ่มความยาวประวัติสี่เท่าในแบบจำลองนี้

หน่วยรายปีตอนนี้เป็น annualized arithmetic mean และ variance ของผลรวมแบบบวก ไม่ใช่ค่าเฉลี่ยหรือ variance ของผลตอบแทนที่ทบต้นจริงตลอดปี สมการนี้ใช้สอนว่าการประมาณ drift ขึ้นกับช่วงเวลาที่สังเกตอย่างไร ไม่ใช่สูตรที่แทนการทบต้นได้ทุกกรณี

ในทางปฏิบัติ ข้อมูลถี่อาจช่วยประมาณรายละเอียดความผันผวน แต่มีเรื่องราคาที่ไม่พร้อมกันและความสัมพันธ์ข้ามเวลาเพิ่มมา ส่วนข้อมูลหลายสิบปีอาจครอบคลุมธุรกิจ โครงสร้างตลาด หรือนโยบายที่เปลี่ยนไป การเพิ่ม $H$ จึงไม่ได้รับประกันว่าทุกปีมาจากการแจกแจงเดียวกัน

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/advanced-mean-uncertainty-mobile.svg">
<img src="assets/charts/advanced-mean-uncertainty.svg" alt="ภายใต้แบบจำลอง IID ที่มี annual SD 20% ค่า standard error ของ annual mean ลดตาม 20% หารรากที่สองของจำนวนปี" loading="lazy" width="720" height="560">
</picture>
<figcaption>กราฟคำนวณจากแบบจำลองผลตอบแทนแบบบวกและพารามิเตอร์คงที่เดียวกับตัวอย่าง แกนตั้งวัดความไม่แน่นอนของค่าเฉลี่ย ไม่ใช่ความผันผวนของผลตอบแทนปีหน้า การเพิ่มประวัติจาก 1 เป็น 4 ปีลด SE จาก 20 เป็น 10 จุดเปอร์เซ็นต์</figcaption>
</figure>

<span id="mean-uncertainty-simulation"></span>

## สุ่มประวัติหลายชุดเพื่อเห็นค่าเฉลี่ยที่แกว่งไปมา

ในการจำลอง เราตั้งค่าจริงของแบบจำลองเองได้ กำหนด mean รายเดือน 0.5%, SD รายเดือน 4% และผลตอบแทน IID Normal แต่ละประวัติมี 60 เดือน แล้วสุ่มประวัติ 10,000 ชุด ทุกชุดมาจาก mean เดียวกัน เราจะดูว่าค่าเฉลี่ยย้อนหลังต่างกันได้เท่าไร

`default_rng` สร้างตัวสุ่มและ seed ทำให้รันซ้ำได้ `size=(10000, 60)` สร้างตารางหนึ่งแถวต่อหนึ่งประวัติ `.mean(axis=1)` เฉลี่ยตามแนวคอลัมน์ภายในแต่ละแถว `ddof=1` ใช้ตัวหาร 59 สำหรับ sample SD ส่วนการเฉลี่ยค่าจริง/เท็จจะให้สัดส่วนของแถวที่เป็นจริง

```python
mean_rng = np.random.default_rng(20261003)
sim_true_mean, sim_true_sd = 0.005, 0.04
sim_months, sim_repeats = 60, 10000
sim_samples = mean_rng.normal(sim_true_mean, sim_true_sd, size=(sim_repeats, sim_months))
sim_means = sim_samples.mean(axis=1)
sim_ses = sim_samples.std(axis=1, ddof=1) / np.sqrt(sim_months)
sim_halfwidths = stats.t.ppf(0.975, sim_months - 1) * sim_ses
sim_coverage = np.mean(np.abs(sim_means - sim_true_mean) <= sim_halfwidths)
print(f"Theoretical SE: {sim_true_sd / np.sqrt(sim_months):.4%}")
print(f"SD of simulated sample means: {sim_means.std(ddof=1):.4%}")
print(f"Share of negative sample means: {np.mean(sim_means < 0):.2%}")
print(f"Share of intervals covering true mean: {sim_coverage:.2%}")
```

ตามทฤษฎี SE เท่ากับ $4\%/\sqrt{60}\approx0.5164$ จุดเปอร์เซ็นต์ ค่า SD ของ sample means ที่สุ่มได้ประมาณ 0.5057 จุดเปอร์เซ็นต์ มีค่าเฉลี่ยย้อนหลังติดลบประมาณ 16.62% ของประวัติ ทั้งที่กำหนด mean จริงเป็นบวก 0.5% ต่อเดือน

ช่วงความเชื่อมั่นจากรอบนี้ครอบคลุม mean จริงประมาณ 95.71% ค่านี้แกว่งตาม seed และจำนวนรอบ จึงไม่ต้องตรง 95.00% ทุกการจำลอง และยังเป็นผลภายใต้โลก IID Normal ที่เราสร้างเท่านั้น การจำลองจำนวนมากช่วยตรวจพฤติกรรมของวิธีภายใต้สมมติฐาน ไม่ได้ตรวจว่าตลาดทำตามสมมติฐานนั้น

Normal ในที่นี้เป็นแบบจำลองเพื่อศึกษา sample mean ไม่ได้นำไปสร้างราคาสินทรัพย์ สมมติฐาน Normal ของ simple return มีหางต่ำกว่า −100% ทางคณิตศาสตร์ จึงควรเลือกแบบจำลองที่เหมาะกับราคาหากเปลี่ยนโจทย์ไปจำลองความมั่งคั่ง

<span id="mean-sensitive-optimization"></span>

## ค่าเฉลี่ยต่างกันเล็กน้อยอาจทำให้น้ำหนักต่างกันมาก

ต่อไปเปลี่ยนเป็นข้อมูลรายปีของสินทรัพย์สองตัว A และ B กำหนด SD เท่ากันที่ 20% และ correlation 0.995 เมื่อผลตอบแทนสองตัวเกือบเคลื่อนไหวด้วยกัน การเพิ่ม A พร้อมลด B อาจเปลี่ยนความเสี่ยงรวมไม่มากนัก optimizer จึงตอบสนองแรงต่อความต่างของ expected returns

ใช้โจทย์ mean–variance ที่ให้คะแนนพอร์ตเป็น

$$
U(w)=w^\mathsf{T}\mu-\frac{\gamma}{2}w^\mathsf{T}\Sigma w,
\qquad w_A+w_B=1.
$$

พจน์แรกเป็น expected return พจน์หลังหักคะแนนตาม variance และ $\gamma>0$ กำหนดน้ำหนักที่ให้กับการลด variance ตัวอย่างเลือก $\gamma=3$ โดยใช้ returns หน่วยทศนิยมและ covariance หน่วยทศนิยมยกกำลังสองรายปี ไม่มีต้นทุน ภาษี หรือข้อจำกัดขนาดสถานะในกรณีแรก

สำหรับสองสินทรัพย์ แทน $w_B=1-w_A$ แล้วหาจุดสูงสุดของฟังก์ชันกำลังสอง ได้

$$
w_A^*=\frac{\mu_A-\mu_B+\gamma(\Sigma_{BB}-\Sigma_{AB})}
{\gamma(\Sigma_{AA}+\Sigma_{BB}-2\Sigma_{AB})}.
$$

ส่วน $\Sigma_{AA}+\Sigma_{BB}-2\Sigma_{AB}$ คือ variance ของผลต่าง $r_A-r_B$ สูตรต้องมีตัวหารเป็นบวก ถ้าสองสินทรัพย์มี SD เดียวกัน $s$ สูตรย่อเหลือ $w_A^*=1/2+(\mu_A-\mu_B)/[2\gamma s^2(1-\rho)]$ เมื่อ $\rho$ ใกล้หนึ่ง ตัวหารเล็กลง

`def` ประกาศฟังก์ชันที่เรียกซ้ำได้ `return` ส่งน้ำหนักกลับมา `long_only=False` เป็นค่าเริ่มต้นที่อนุญาตน้ำหนักติดลบ หากตั้งเป็น `True` ฟังก์ชันใช้ `np.clip` จำกัดน้ำหนัก A ให้อยู่ในช่วง 0 ถึง 1 วิธี clip นี้แก้ปัญหา long-only ได้ตรงสำหรับโจทย์สองสินทรัพย์ฟังก์ชันเว้าแบบนี้ ไม่ใช่วิธีทั่วไปสำหรับพอร์ตหลายสินทรัพย์

```python
def two_asset_mvo_weights(mu, covariance, gamma=3.0, long_only=False):
    difference_variance = covariance[0, 0] + covariance[1, 1] - 2 * covariance[0, 1]
    weight_a = (mu[0] - mu[1] + gamma * (covariance[1, 1] - covariance[0, 1]))
    weight_a = weight_a / (gamma * difference_variance)
    if long_only:
        weight_a = np.clip(weight_a, 0, 1)
    return np.array([weight_a, 1 - weight_a])

sensitivity_cov = 0.20 ** 2 * np.array([[1, 0.995], [0.995, 1]])
sensitivity_means = np.array([[0.07, 0.07], [0.0706, 0.0694], [0.0694, 0.0706]])
sensitivity_weights = np.array([two_asset_mvo_weights(mu, sensitivity_cov) for mu in sensitivity_means])
sensitivity_long_only = np.array([two_asset_mvo_weights(mu, sensitivity_cov, long_only=True) for mu in sensitivity_means])
print("Unconstrained A/B weights (%):\n", np.round(100 * sensitivity_weights, 2))
print("Long-only A/B weights (%):\n", np.round(100 * sensitivity_long_only, 2))
```

เมื่อ expected returns เป็น 7% ทั้งคู่ น้ำหนักเท่ากับ 50/50 เปลี่ยน A เป็น 7.06% และ B เป็น 6.94% จึงเปลี่ยนค่าที่ใส่ให้แต่ละตัวเพียง 0.06 จุดเปอร์เซ็นต์ แต่คำตอบที่อนุญาต short กลายเป็น 150/−50 เมื่อสลับค่าคาดหวังคำตอบก็กลายเป็น −50/150

น้ำหนัก 150/−50 หมายถึงถือ A มูลค่า 150% ของเงินพอร์ตและ short B มูลค่า 50% เมื่อตั้ง long-only ได้ 100/0 หรือ 0/100 แทน ข้อจำกัดตัดสถานะ short ออก แต่น้ำหนักยังเปลี่ยนจากมุมหนึ่งไปอีกมุมหนึ่งได้

ตัวอย่างนี้ตรึง covariance ไว้เพื่อแยกผลของ mean error ค่า $\mu$ ที่ต่างกันเกิดจากสมมติฐานของเรา ไม่ใช่หลักฐานว่า A หรือ B ให้ผลตอบแทนดีกว่าจริง การที่โปรแกรมหาคำตอบถูกต้องสำหรับข้อมูลเข้าจึงเป็นคนละเรื่องกับการประมาณข้อมูลเข้าได้แม่น

<span id="expected-mean-shrinkage"></span>

## ลดความต่างของค่าประมาณด้วย Mean shrinkage

[Mean shrinkage](glossary.html#mean-shrinkage) ผสมค่าประมาณจากข้อมูลกับ target ที่กำหนดไว้ ให้ $m_i$ เป็น target ของสินทรัพย์ $i$ และ $\delta$ เป็นสัดส่วนที่ให้น้ำหนัก target:

$$
\hat\mu_i^{\text{shrunk}}
=(1-\delta)\hat\mu_i+\delta m_i,
\qquad 0\leq\delta\leq1.
$$

เมื่อ $\delta=0$ ใช้ค่าประมาณเดิมทั้งหมด เมื่อ $\delta=1$ ใช้ target ทั้งหมด สมมติค่าประมาณเดิมเป็น 7.06% และ 6.94% แล้วเลือก target ร่วมเป็นค่าเฉลี่ยข้ามสินทรัพย์สองตัว คือ 7% ค่า $\delta=0.5$ จึงให้ A เท่ากับ $0.5(7.06\%)+0.5(7\%)=7.03\%$ และ B เท่ากับ 6.97%

ในโค้ด `[:, None]` เพิ่มแนวคอลัมน์ให้ตัวเลข $\delta$ แต่ละค่าคูณ expected returns ทั้งสองตัวได้ เราใช้ฟังก์ชันจัดพอร์ตเดิมโดยตรึง covariance และ $\gamma$ แล้วเปลี่ยนเฉพาะ expected returns

```python
shrinkage_deltas = np.array([0.0, 0.5, 0.9, 1.0])
mean_target = sensitivity_means[1].mean()
shrunken_means = ((1 - shrinkage_deltas[:, None]) * sensitivity_means[1]
                  + shrinkage_deltas[:, None] * mean_target)
shrunken_weights = np.array([two_asset_mvo_weights(mu, sensitivity_cov) for mu in shrunken_means])
shrinkage_results = pd.DataFrame({
    "delta": shrinkage_deltas,
    "mean_A_pct": 100 * shrunken_means[:, 0],
    "mean_B_pct": 100 * shrunken_means[:, 1],
    "weight_A_pct": 100 * shrunken_weights[:, 0],
    "weight_B_pct": 100 * shrunken_weights[:, 1],
})
print(shrinkage_results.round(4).to_string(index=False))
```

| น้ำหนัก target $\delta$ | Expected A ต่อปี | Expected B ต่อปี | น้ำหนัก A | น้ำหนัก B |
|---|---:|---:|---:|---:|
| 0 | 7.060% | 6.940% | 150% | −50% |
| 0.5 | 7.030% | 6.970% | 100% | 0% |
| 0.9 | 7.006% | 6.994% | 60% | 40% |
| 1 | 7.000% | 7.000% | 50% | 50% |

การหด mean เข้าหากันลดความสุดโต่งของน้ำหนักในตัวอย่าง แต่ถ้า A มี expected return สูงกว่า B จริงมาก การหดแรงอาจลบข้อมูลที่มีประโยชน์ด้วย เราแลกความแตกต่างของค่าประมาณที่ลดลงกับความเสี่ยงที่จะดึงไปหา target ผิด ค่า $\delta$ ในตารางเป็นค่าทดลองเพื่อเห็นผลของสูตร ยังไม่ได้เลือกจากการทดสอบนอกช่วงประมาณ

Target ที่เป็นค่าเฉลี่ยข้ามสินทรัพย์มาจากข้อมูลชุดเดียวกัน จึงต้องนับความไม่แน่นอนของ target ด้วย การเรียก target ว่า “prior” ไม่ได้ทำให้มันเป็นข้อมูลจากภายนอก และการเฉลี่ยเข้าหา target เพียงอย่างเดียวยังไม่ได้ระบุ Bayesian model ครบ

<span id="prior-posterior-basics"></span>

### Prior และ posterior เริ่มจากความไม่แน่นอนของพารามิเตอร์

[Prior](glossary.html#prior) ใน Bayesian model คือการแจกแจงที่กำหนดให้พารามิเตอร์ก่อนนำข้อมูลชุดที่กำลังวิเคราะห์มาปรับความเชื่อ ส่วน likelihood บอกว่าข้อมูลที่เห็นสอดคล้องกับพารามิเตอร์แต่ละค่าเพียงใดภายใต้แบบจำลองการเกิดข้อมูล เมื่อนำทั้งสองส่วนมารวมตามกฎของ Bayes ได้ [posterior](glossary.html#posterior) ซึ่งเป็นการแจกแจงของพารามิเตอร์หลังรับข้อมูล

ลองใช้เหรียญเพื่อแยกขั้นตอนนี้ออกจากเรื่องพอร์ต ให้ $p$ เป็นโอกาสออกหัวที่ยังไม่รู้ กำหนด prior $p\sim\operatorname{Beta}(2,2)$ การแจกแจง Beta อยู่ระหว่างศูนย์กับหนึ่ง จึงใช้กับความน่าจะเป็นได้ ค่าเฉลี่ย prior นี้คือ $2/(2+2)=50\%$ และยังยอมให้ $p$ ต่างจาก 50% ได้

ภายใต้การโยนอิสระที่ใช้ $p$ เดียวกัน หากเห็นหัว $h$ ครั้งและก้อย $l$ ครั้ง posterior เป็น $\operatorname{Beta}(2+h,2+l)$ และค่าเฉลี่ย posterior เป็น

$$
E[p\mid\text{ข้อมูล}]=\frac{2+h}{4+h+l}.
$$

เมื่อเห็นหัวหก ก้อยสี่ ค่าเฉลี่ย posterior เป็น $8/14\approx57.14\%$ อยู่ระหว่าง prior mean 50% กับสัดส่วนหัวในข้อมูล 60% ถ้าเริ่มจาก prior เดิมแล้วมีข้อมูลหัว 600 ก้อย 400 แทน จะได้ $602/1004\approx59.96\%$ ข้อมูลที่มากขึ้นให้น้ำหนักต่อ posterior มากขึ้นในแบบจำลองนี้ ไม่ต้องรอให้ข้ามเกณฑ์ใดก่อนจึงเริ่มอัปเดต สูตรและการอ่าน posterior mean เป็นค่าเฉลี่ยถ่วงน้ำหนักดูได้ใน [Stanford STATS 200: Prior distributions](https://web.stanford.edu/class/archive/stats/stats200/stats200.1172/Lecture21.pdf)

การประมาณ mean ของผลตอบแทนต้องเลือก likelihood และ prior ที่เหมาะกับข้อมูลต่อเนื่องต่างออกไป ตัวอย่างเหรียญใช้สอนกระบวนการอัปเดตเท่านั้น ส่วนวิธี frequentist ที่ใช้ SE ก่อนหน้าก็มีสมมติฐาน เช่น IID และการแจกแจงข้อมูล ทั้งสองแนวทางต้องประกาศสมมติฐานของตนให้ครบ

<span id="equal-means-and-gmv"></span>

## ถ้าไม่แยก Expected returns ระหว่างสินทรัพย์ จะได้พอร์ตอะไร?

พอร์ต maximum Sharpe ratio หรือ MSR คือพอร์ตที่ให้ Sharpe สูงสุดในชุดทางเลือกที่กำหนด คำว่า agnostic prior ในหัวข้อนี้หมายถึงการกำหนดโครงสร้างโดยไม่พยายามจัดอันดับ expected returns รายสินทรัพย์จากค่าเฉลี่ยระยะสั้น ยังต้องบอกให้ได้ว่าเราเลือกสมมติฐานแบบใด เพราะ equal means, equal Sharpe และ equal weights เป็นคนละข้อกำหนด

ให้สินทรัพย์ทุกตัวมี expected return เท่ากับ $m$ ใช้อัตราปลอดความเสี่ยง $r_f$ เดียวกัน และพอร์ตลงทุนเต็มจำนวน $\sum_iw_i=1$ จะได้

$$
\mu_p=\sum_iw_im=m,
\qquad
\operatorname{SR}_p=\frac{m-r_f}{\sqrt{w^\mathsf{T}\Sigma w}}.
$$

ถ้า $m-r_f>0$ ตัวเศษเป็นค่าบวกเดียวกันทุกพอร์ต การเพิ่ม Sharpe ratio จึงเท่ากับลด volatility ภายใต้ชุดข้อจำกัดเดียวกัน คำตอบคือ global minimum variance หรือ GMV ในชุดพอร์ตนั้น หาก $m-r_f=0$ ทุกพอร์ตที่ volatility บวกมี Sharpe ศูนย์เท่ากัน และถ้า $m-r_f<0$ การหารด้วย volatility ที่มากขึ้นกลับทำให้ Sharpe ติดลบน้อยลง

ตัวอย่างใหม่มีสินทรัพย์สามตัว ใช้ covariance รายปีที่ให้ SD เท่ากับ 10%, 15% และ 20% เมทริกซ์ตัวอย่างนี้เป็น positive definite จึงหา GMV ที่ไม่มีข้อจำกัดเพิ่มเติมได้ด้วย $\Sigma^{-1}\mathbf1/(\mathbf1^\mathsf{T}\Sigma^{-1}\mathbf1)$ ในโค้ด `np.linalg.solve` แก้สมการ $\Sigma x=\mathbf1$ แล้วหารทุกน้ำหนักด้วยผลรวม คำตอบของเมทริกซ์นี้เป็นบวกทั้งหมด จึงเป็น GMV ภายใต้ long-only ด้วย

```python
expected_cov = np.array([[0.0100, 0.0020, 0.0010],
                         [0.0020, 0.0225, 0.0030],
                         [0.0010, 0.0030, 0.0400]])
ones = np.ones(3)
gmv_direction = np.linalg.solve(expected_cov, ones)
gmv_weights = gmv_direction / gmv_direction.sum()
comparison_weights = np.array([gmv_weights, ones / 3, [0.0, 0.0, 1.0]])
comparison_vols = np.array([np.sqrt(w @ expected_cov @ w) for w in comparison_weights])
common_premiums = np.array([0.04, 0.0, -0.04])
premium_edge_sharpes = common_premiums[None, :] / comparison_vols[:, None]
print("GMV weights (%):", np.round(100 * gmv_weights, 4))
print("Annual SD of GMV, EW, C (%):", np.round(100 * comparison_vols, 4))
print(pd.DataFrame(premium_edge_sharpes, index=["GMV", "EW", "C"],
                   columns=["premium +4%", "premium 0%", "premium -4%"]).round(4))
```

ได้ GMV ประมาณ 62.8943%, 23.1861%, 13.9196% และ annual volatility 8.3020% ส่วน equal-weight มี volatility 9.6896% และถือ C ตัวเดียวมี volatility 20% จะเห็นว่า equal expected returns ให้ GMV ที่น้ำหนักไม่เท่ากันในกรณีนี้

เมื่อ common excess return เป็น +4% ต่อปี Sharpe ของ GMV ประมาณ 0.4818 สูงกว่า equal-weight 0.4128 และ C 0.2 เมื่อเปลี่ยน common premium เป็น −4% ค่า Sharpe เป็น −0.4818, −0.4128 และ −0.2 ตามลำดับ ลำดับของพอร์ตกลับด้าน จึงต้องระบุเงื่อนไข premium เป็นบวกเมื่อนำ equal means ไปอธิบาย MSR

นี่เป็นการเปรียบเทียบพอร์ตสินทรัพย์เสี่ยงที่ลงทุนเต็มจำนวน การเพิ่มเงินสดหรือข้อจำกัดอื่นเปลี่ยนชุดทางเลือกด้วย และพอร์ตเงินสดที่ variance ศูนย์ไม่สามารถแทนในสูตร Sharpe นี้โดยหารด้วยศูนย์

<span id="equal-sharpe-diversification"></span>

## Equal Sharpe นำไปสู่ Diversification ratio

อีกสมมติฐานคือให้ทุกสินทรัพย์มี Sharpe ratio รายตัวเท่ากับ $c>0$ จึงตั้ง expected excess return ให้แปรตาม SD:

$$
\mu_i-r_f=c\sigma_i.
$$

สำหรับพอร์ต long-only ที่น้ำหนักรวมหนึ่ง จะได้

$$
\operatorname{SR}_p
=c\frac{\sum_iw_i\sigma_i}{\sqrt{w^\mathsf{T}\Sigma w}}
=c\,\operatorname{DR}(w).
$$

$\operatorname{DR}$ หรือ diversification ratio เปรียบเทียบค่าเฉลี่ยถ่วงน้ำหนักของ SD รายสินทรัพย์กับ SD ของพอร์ตรวม ตัวเศษไม่ใช่ volatility ของพอร์ต เพราะยังไม่รวมความสัมพันธ์ระหว่างสินทรัพย์ ถ้าการรวมสินทรัพย์ลด volatility ลงเมื่อเทียบกับตัวเศษ อัตราส่วนนี้จะสูงขึ้น

ใช้ covariance สามสินทรัพย์เดิมและตั้ง common Sharpe รายปีเท่ากับ 0.4 Expected excess returns จึงเป็น 4%, 6% และ 8% ต่อปี การคูณ DR ด้วยค่าบวกคงที่ 0.4 ไม่เปลี่ยนพอร์ตที่ให้ค่าสูงสุด เราจึงหา maximum-DR portfolio ผ่านการ maximize Sharpe ภายใต้สมมติฐานนี้ได้

`minimize` ของ SciPy หาค่าต่ำสุด เราจึงใส่เครื่องหมายลบหน้าอัตราส่วน `lambda w:` เป็นวิธีเขียนฟังก์ชันสั้นที่รับน้ำหนัก `w` เครื่องหมาย `@` คูณเวกเตอร์หรือเมทริกซ์ ส่วน bounds กำหนดทุกน้ำหนักให้อยู่ระหว่าง 0 กับ 1 และ constraint ชนิด `eq` บังคับให้ `w.sum() - 1` เท่ากับศูนย์

```python
from scipy.optimize import minimize

def maximize_premium_ratio(premium, covariance):
    count = len(premium)
    result = minimize(
        lambda w: -(w @ premium) / np.sqrt(w @ covariance @ w),
        np.full(count, 1 / count), method="SLSQP",
        bounds=[(0.0, 1.0)] * count,
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1},
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not result.success:
        raise RuntimeError(result.message)
    return result.x

individual_vols = np.sqrt(np.diag(expected_cov))
common_sharpe = 0.4
diversification_weights = maximize_premium_ratio(common_sharpe * individual_vols, expected_cov)
diversification_vol = np.sqrt(diversification_weights @ expected_cov @ diversification_weights)
diversification_ratio = (diversification_weights @ individual_vols) / diversification_vol
print("Maximum-DR weights (%):", np.round(100 * diversification_weights, 4))
print(f"Diversification ratio: {diversification_ratio:.6f}")
print(f"Portfolio Sharpe: {common_sharpe * diversification_ratio:.6f}")
```

ได้ maximum-DR weights ประมาณ 46.6541%, 29.2491%, 24.0968% ค่า DR เท่ากับ 1.589394 และ Sharpe ของพอร์ตประมาณ $0.4\times1.589394=0.635758$ น้ำหนักนี้ต่างจากทั้ง GMV และ equal-weight เพราะสมมติฐาน expected returns ต่างกัน

`result.success` ตรวจว่า solver รายงานการจบสำเร็จ ถ้าไม่สำเร็จฟังก์ชันหยุดด้วย error เพื่อไม่ส่งน้ำหนักที่ยังไม่ผ่านการแก้โจทย์กลับไปใช้ การสำเร็จของ solver ไม่ได้ตรวจว่าทุกสินทรัพย์มี Sharpe 0.4 จริง รายละเอียด argument อยู่ใน[เอกสาร SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)

สมมติฐาน equal Sharpe ให้ผลตอบแทนคาดหวังชดเชย total volatility ทั้งหมด หาก volatility ส่วนหนึ่งเป็นความเสี่ยงเฉพาะตัวที่กระจายออกได้ การเพิ่มส่วนนี้อาจไม่ทำให้ผลตอบแทนคาดหวังสูงขึ้นตามสัดส่วน ทฤษฎี pricing อย่าง CAPM จึงเสนอให้ผูกผลตอบแทนกับ systematic exposure ภายใต้สมมติฐานของทฤษฎีแทน การเลือก equal Sharpe ยังเป็นทางเลือกเชิงแบบจำลอง และเงื่อนไข $c>0$ จำเป็นต่อการรักษาทิศทางการ maximize เช่นเดียวกับกรณี equal means

<span id="capm-expected-returns"></span>

## ใช้ CAPM เพื่อกำหนด Expected returns จาก Beta

ทบทวน [CAPM และ beta](factor-investing.html): beta วัดความไวต่อ market excess return ส่วน CAPM เพิ่มข้อกำหนดด้าน pricing ว่า

$$
\mu_i-r_f=\beta_i\lambda_M,
\qquad \lambda_M=E[r_M]-r_f.
$$

การประมาณ beta จาก regression ยังไม่ทำให้สมการ pricing เป็นจริงโดยอัตโนมัติ หากใช้ CAPM forecast เรากำลังตั้งสมมติฐานว่า expected alpha เป็นศูนย์ และ market premium ที่ใส่เหมาะกับช่วงอนาคตที่ต้องการประเมิน

ตัวอย่างใหม่เป็นรายปี ให้ beta ของ A/B/C เท่ากับ 0.7, 1.0, 1.3 ตั้ง $r_f=2\%$ และ market premium 5% จะได้ expected returns เท่ากับ $2\%+0.7(5\%)=5.5\%$, 7% และ 8.5% ค่า $\lambda_M$ มีหน่วยผลตอบแทนต่อปี ส่วน beta ไม่มีหน่วยเมื่อทั้ง market และสินทรัพย์ใช้ return หน่วยเดียวกัน

เราสร้าง covariance ให้สอดคล้องกับ factor model นี้ โดยใช้ market SD 18% และ residual SD ของสินทรัพย์ 12%, 10%, 15% สมมติ residual ไม่สัมพันธ์กับตลาดและไม่สัมพันธ์ข้ามสินทรัพย์ จึงได้ $\Sigma=\sigma_M^2\beta\beta^\mathsf{T}+D$ ตาม[บท covariance จาก factor](covariance-estimation.html)

```python
market_betas = np.array([0.7, 1.0, 1.3])
market_vol, market_premium, capm_rf = 0.18, 0.05, 0.02
idiosyncratic_vols = np.array([0.12, 0.10, 0.15])
capm_cov = market_vol ** 2 * np.outer(market_betas, market_betas) + np.diag(idiosyncratic_vols ** 2)
capm_expected_returns = capm_rf + market_betas * market_premium
capm_weights = maximize_premium_ratio(market_betas * market_premium, capm_cov)
capm_weights_double = maximize_premium_ratio(market_betas * (2 * market_premium), capm_cov)
capm_portfolio_beta = capm_weights @ market_betas
capm_portfolio_vol = np.sqrt(capm_weights @ capm_cov @ capm_weights)
print("CAPM annual expected returns (%):", np.round(100 * capm_expected_returns, 4))
print("CAPM weights (%):", np.round(100 * capm_weights, 4))
print("Positive premium rescaling preserves weights:", np.allclose(capm_weights, capm_weights_double, atol=1e-5))
print(f"Portfolio beta: {capm_portfolio_beta:.6f}; annual SD: {capm_portfolio_vol:.4%}")
print(f"CAPM portfolio Sharpe: {market_premium * capm_portfolio_beta / capm_portfolio_vol:.6f}")
```

ได้พอร์ต long-only ประมาณ 23.5532%, 48.4522%, 27.9946% มี portfolio beta 1.013324, annual volatility 19.5394% และ expected Sharpe 0.259302 ภายใต้ข้อมูลเข้าชุดนี้

เพราะ $\beta_p=\sum_iw_i\beta_i$ เราจึงเขียน

$$
\operatorname{SR}_p=\lambda_M\frac{\beta_p}{\sigma_p}.
$$

เมื่อ $\lambda_M>0$ ค่าเดียวกันทุกสินทรัพย์ การเปลี่ยนจาก premium 5% เป็น 10% ไม่เปลี่ยนน้ำหนัก MSR ในตัวอย่าง จึงได้ `True` เมื่อตรวจเทียบด้วย tolerance ของการคำนวณ แต่ expected return และ Sharpe ของพอร์ตยังเพิ่มตาม premium หาก premium ศูนย์จะไม่เหลือการจัดอันดับด้วย Sharpe แบบนี้ และหาก premium ติดลบการตัดตัวคูณออกต้องกลับทิศการหาค่าสูงสุด

ภายใต้ CAPM อัตราส่วน $(\mu_i-r_f)/\beta_i$ เรียกว่า Treynor ratio และเท่ากับ $\lambda_M$ เมื่อ $\beta_i\ne0$ ไม่ควรหารด้วย beta ศูนย์ และ Treynor ที่มี beta ติดลบต้องอ่านพร้อมทิศทาง exposure ไม่ใช้จัดอันดับแบบ reward-to-total-risk โดยตรง

พอร์ตที่หาในโค้ดเลือกได้เฉพาะสินทรัพย์สมมติสามตัว ความเสี่ยง residual ยังเหลืออยู่แม้ใช้ CAPM forecast การตั้ง expected alpha เป็นศูนย์ไม่ได้ทำให้ residual variance เป็นศูนย์

<span id="factor-mean-identity"></span>

## Regression ที่ดีในอดีตยังต้องมีสมมติฐานเพื่อพยากรณ์

จาก[บทหลายปัจจัย](multifactor-models.html#matrix-ols) เขียน model ของ excess return เป็น

$$
r_{t,i}-r_{f,t}=a_i+\sum_{k=1}^{K}b_{ik}f_{t,k}+\epsilon_{t,i}.
$$

$a_i$ เป็น intercept, $b_{ik}$ เป็น loading, $f_{t,k}$ เป็น factor return และ $\epsilon_{t,i}$ เป็น residual ถ้า loading คงที่และ residual มี expected value ศูนย์ แบบจำลองให้

$$
\mu_i=r_f+a_i+\sum_{k=1}^{K}b_{ik}\lambda_k,
\qquad \lambda_k=E[f_k].
$$

ในตัวอย่างต่อไป factor เป็นผลตอบแทนที่ซื้อขายได้: Market เป็น market excess return ส่วน Value เป็นผลต่างผลตอบแทนของสองขา จึงไม่มีการหัก risk-free rate ซ้ำจาก Value คำว่า Value เป็นชื่อปัจจัยสมมติ ไม่ใช่ชุดข้อมูล Fama–French จริง สำหรับปัจจัยมหภาคที่มีหน่วยอย่างการเติบโตของผลผลิต ราคาของความเสี่ยง $\lambda_k$ ไม่ใช่ค่าเฉลี่ยดิบของตัวแปรมหภาคโดยอัตโนมัติ ต้องระบุ pricing model เพิ่ม

เปลี่ยนกลับเป็นข้อมูลรายเดือน สร้างสอง factor แปดเดือนและสินทรัพย์สามตัวโดยกำหนด intercept/loadings ล่วงหน้า เราใช้แพตเทิร์น `u`, `v`, `q` ที่มีค่าเฉลี่ยศูนย์และตั้งฉากกันใน sample เพื่อให้ตรวจผล regression ได้ ไม่ได้อ้างว่าลำดับสมมติเหล่านี้เป็น IID หรือทำซ้ำตลาด

`factor_design` มีหนึ่งคอลัมน์ของเลข 1 สำหรับ intercept แล้วตามด้วย factor สองคอลัมน์ จึงมีขนาด 8×3 `lstsq` หาค่าสัมประสิทธิ์ที่ทำให้ผลรวม residual กำลังสองต่ำสุดพร้อมกันสามสินทรัพย์ เมทริกซ์สัมประสิทธิ์มีขนาด 3×3: แถวแรกเป็น intercept ส่วนสองแถวถัดไปเป็น loadings การ transpose สองแถวหลังทำให้ `fitted_loadings` มีหนึ่งแถวต่อสินทรัพย์และหนึ่งคอลัมน์ต่อ factor

```python
u = np.array([-1, -1, -1, -1, 1, 1, 1, 1])
v = np.array([-1, -1, 1, 1, -1, -1, 1, 1])
q = np.array([-1, 1, -1, 1, -1, 1, -1, 1])
factor_returns = pd.DataFrame({"Market": 0.005 + 0.03 * u, "Value": 0.002 + 0.015 * v},
                              index=pd.period_range("2024-01", periods=8, freq="M"))
planted_alpha = np.array([0.001, -0.0005, 0.0008])
planted_loadings = np.array([[0.7, 0.3], [1.0, -0.2], [1.3, 0.5]])
factor_rf = 0.001
asset_excess = planted_alpha + factor_returns.to_numpy() @ planted_loadings.T + q[:, None] * np.array([0.006, 0.008, 0.004])
asset_returns = pd.DataFrame(factor_rf + asset_excess, index=factor_returns.index, columns=["A", "B", "C"])
factor_design = np.column_stack([np.ones(len(factor_returns)), factor_returns])
fitted_coefficients = np.linalg.lstsq(factor_design, asset_excess, rcond=None)[0]
fitted_alpha, fitted_loadings = fitted_coefficients[0], fitted_coefficients[1:].T
reconstructed_means = factor_rf + fitted_alpha + fitted_loadings @ factor_returns.mean().to_numpy()
print("Fitted monthly alpha (%):", np.round(100 * fitted_alpha, 4))
print("Fitted factor loadings:\n", np.round(fitted_loadings, 4))
print("Monthly asset sample means (%):", np.round(100 * asset_returns.mean().to_numpy(), 4))
print("Full OLS mean identity:", np.allclose(reconstructed_means, asset_returns.mean().to_numpy()))
```

ได้ fitted alpha เท่ากับ 0.10%, −0.05%, 0.08% ต่อเดือน และ loading ตรงกับค่าที่ใช้สร้างข้อมูล ค่าเฉลี่ยผลตอบแทนรวมของ A/B/C เท่ากับ 0.61%, 0.51%, 0.93% ต่อเดือน เราทำให้ residual ของสินทรัพย์ใช้ `q` ร่วมกัน จึงไม่ตั้งสมมติฐานว่า residual ทั้งสามเป็นอิสระจากกัน

ผล `Full OLS mean identity: True` มาจากคุณสมบัติของ OLS ที่มี intercept: residual ในช่วง fit มีผลรวมศูนย์ ดังนั้น

$$
\bar r_i=\bar r_f+\hat a_i+\sum_k\hat b_{ik}\bar f_k.
$$

ถ้าใช้ fitted intercept และ sample factor means จากช่วงเดียวกันทั้งหมด การคำนวณผ่าน factor model จะคืนค่าเฉลี่ยสินทรัพย์เดิม จึงยังไม่มีการหดค่าเฉลี่ยหรือเพิ่มข้อมูลอนาคต การตั้ง $a_i^{\text{forecast}}=0$ การหด alpha หรือการใช้ premium จากแหล่งอื่นล้วนเป็นสมมติฐานเพิ่มเติมที่ต้องระบุให้ชัดเจน

การแยก expected returns เป็นผลจาก factor และ expected residual อธิบายไว้ใน [Sharpe: Factor-based Expected Returns](https://web.stanford.edu/~wfsharpe/mia/fac/mia_fac3.htm) หากต้องประมาณ intercept อนาคตแยกทุกสินทรัพย์ เราก็ยังเหลือปัญหาการประมาณ mean รายสินทรัพย์ แม้จะเขียนสมการในรูป factor แล้วก็ตาม

<span id="factor-premium-scenarios"></span>

## Factor premium หลายตัวทำให้ต้องเลือกความเชื่อเพิ่มเติม

เมื่อมีเพียง market premium บวกตัวเดียว เราตัดตัวคูณร่วมออกจากโจทย์ MSR ได้ แต่ในหลาย factor อัตราส่วนระหว่าง $\lambda_1,\lambda_2,\ldots$ เปลี่ยน expected returns ข้ามสินทรัพย์และอาจเปลี่ยนพอร์ตด้วย การรู้ loading จึงยังไม่พอ

ใช้ loading จากตัวอย่างเดิม กำหนด risk-free rate สำหรับเดือนอนาคตเป็น 0.15% ต่อเดือน และกำหนด forecast alpha เป็นศูนย์ เราจะเปรียบเทียบ premium สี่ชุดซึ่งล้วนเป็นสมมติฐานในตัวอย่าง:

| ชื่อในโค้ด | Market premium ต่อเดือน | Value premium ต่อเดือน | ที่มา |
|---|---:|---:|---|
| `historical_premia` | 0.50% | 0.20% | ค่าเฉลี่ย factor แปดเดือนที่สร้างไว้ |
| `cautious` | 0.30% | 0.00% | ค่าที่เลือกสมมติก่อนดูช่วงประเมิน |
| `negative_value` | 0.30% | −0.20% | ทดลองผลของ Value premium ติดลบ |
| `equal_factor_Sharpe` | คำนวณจาก $0.2s_M$ | คำนวณจาก $0.2s_V$ | สมมติ Sharpe รายเดือนของ factor เท่ากับ 0.2 |

ชื่อ `cautious` เป็นป้ายของสถานการณ์ ไม่ได้รับรองว่าเป็น forecast ที่ปลอดภัยกว่า ตัวอย่างนี้ใช้ future $r_f$ ใหม่ ไม่ได้เอา risk-free rate ในอดีตมาแทนอนาคตโดยอัตโนมัติ ส่วน zero expected alpha หมายถึงเราไม่พยากรณ์ผลตอบแทนส่วนเพิ่มที่แยกจาก factor ยังมี residual risk ตามเดิม

```python
future_rf = 0.0015
factor_premium_scenarios = pd.DataFrame({
    "historical_premia": factor_returns.mean(),
    "cautious": [0.003, 0.0],
    "negative_value": [0.003, -0.002],
    "equal_factor_Sharpe": 0.2 * factor_returns.std(ddof=1),
}, index=factor_returns.columns)
forecast_alpha = np.zeros(3)
factor_forecasts = pd.DataFrame(
    future_rf + forecast_alpha[:, None] + fitted_loadings @ factor_premium_scenarios.to_numpy(),
    index=asset_returns.columns, columns=factor_premium_scenarios.columns,
)
print("Factor premium assumptions (% per month):\n", (100 * factor_premium_scenarios).round(4))
print("Asset expected returns (% per month):\n", (100 * factor_forecasts).round(4))
```

สถานการณ์ `historical_premia` ให้ expected returns ของ A/B/C เท่ากับ 0.56%, 0.61%, 0.90% ต่อเดือน เช่น A เท่ากับ $0.15\%+0.7(0.50\%)+0.3(0.20\%)=0.56\%$ ตัวเลขต่างจาก sample means ก่อนหน้าเพราะเปลี่ยน $r_f$ และตั้ง forecast alpha ศูนย์

สถานการณ์ `cautious` ให้ 0.36%, 0.45%, 0.54% ต่อเดือน เมื่อเปลี่ยน Value premium เป็น −0.20% ผลของ B เพิ่มเป็น 0.49% เพราะ loading ของ B ต่อ Value เท่ากับ −0.2 ผลคูณ loading ลบกับ premium ลบจึงบวก 0.04 จุดเปอร์เซ็นต์ ส่วนสินทรัพย์ที่ loading บวกถูกลด expected return

กรณี equal factor Sharpe ใช้ sample SD รายเดือนประมาณ 3.2071% และ 1.6036% จึงตั้ง premia ประมาณ 0.6414% และ 0.3207% ต่อเดือน สมมติฐานว่า factor มี reward ต่อความเสี่ยงเท่ากันนี้ต่างจากสมมติฐาน equal Sharpe ของสินทรัพย์ทุกตัว เพราะสินทรัพย์มี loading และ residual risk ต่างกัน

การใช้ premium ย้อนหลังช่วงยาวช่วยเพิ่มข้อมูลภายใต้ความคงที่ แต่ไม่กำจัดความไม่แน่นอนของค่าเฉลี่ย factor ผลตอบแทนหลังค้นพบปัจจัยอาจต่างจากช่วงที่ใช้ค้นพบ วิธีนิยามปัจจัย ต้นทุน และ universe อาจเปลี่ยนได้ จึงควรดูหลายสมมติฐานและช่วงข้อมูลที่กำหนดไว้ล่วงหน้า แทนการเลือกย้อนหลังเฉพาะช่วงที่ให้พอร์ตดูดีที่สุด

<span id="expected-return-holdout"></span>

## ตรึง Forecast ก่อนเปิดข้อมูลช่วงประเมิน

สมมติเราตัดสินใจเมื่อสิ้นเดือนสิงหาคม 2024 ใช้ข้อมูลมกราคมถึงสิงหาคมที่สร้างไว้ และกำหนด forecast คงที่สำหรับการเปรียบเทียบสามเดือนถัดไปไว้สองแบบ แบบแรกใช้ sample mean ของสินทรัพย์ แบบที่สองใช้ factor forecast สถานการณ์ `cautious` ทุกสมมติฐานต้องถูกกำหนดก่อนเปิดผลตอบแทนกันยายนถึงพฤศจิกายน

เราจะคำนวณ root mean squared error หรือ RMSE โดยหาผลต่างระหว่างผลตอบแทนแต่ละเดือนกับ forecast ยกกำลังสอง เฉลี่ยทุกเดือนและทุกสินทรัพย์ แล้วถอดราก ให้ $H$ เป็นจำนวนเดือนประเมินและ $N$ เป็นจำนวนสินทรัพย์:

$$
\operatorname{RMSE}=\sqrt{\frac{1}{HN}\sum_{t=1}^{H}\sum_{i=1}^{N}
(r_{t,i}-\hat\mu_i)^2}.
$$

การยกกำลังสองทำให้ข้อผิดพลาดบวกและลบไม่หักล้างกัน การถอดรากทำให้หน่วยกลับมาเหมือนผลตอบแทน RMSE จึงรวมทั้งข้อผิดพลาดของ mean forecast และความผันผวนของผลตอบแทนที่เกิดจริง ไม่ใช่ค่าที่สังเกต estimation error ของ $\mu$ จริงได้โดยตรง

```python
frozen_forecasts = pd.DataFrame({
    "sample_mean": asset_returns.mean(),
    "factor_prior": factor_forecasts["cautious"],
})
heldout_returns = pd.DataFrame([[0.006, -0.002, 0.012],
                              [-0.010, 0.005, -0.015],
                              [0.020, 0.008, 0.010]],
                             index=pd.period_range("2024-09", periods=3, freq="M"),
                             columns=asset_returns.columns)
assert factor_returns.index.max() < heldout_returns.index.min()
forecast_rmse = pd.Series({
    name: np.sqrt(np.mean((heldout_returns.to_numpy() - frozen_forecasts[name].to_numpy()) ** 2))
    for name in frozen_forecasts.columns
})
print("Frozen forecasts (% per month):\n", (100 * frozen_forecasts).round(4))
print("Held-out realized means (% per month):", np.round(100 * heldout_returns.mean().to_numpy(), 4))
print("RMSE across months and assets (percentage points):\n", (100 * forecast_rmse).round(4))
```

`assert` ตรวจว่าวันท้ายของช่วงฝึกมาก่อนวันแรกของช่วงประเมิน `frozen_forecasts` เก็บ forecast ก่อนสร้างตัวอย่างช่วงประเมิน ส่วนลูป `for name in frozen_forecasts.columns` คำนวณ RMSE แยกแต่ละวิธีโดยใช้เดือนและสินทรัพย์ชุดเดียวกัน

ผลรวมทั้งเก้าช่องได้ RMSE ประมาณ 1.1103 จุดเปอร์เซ็นต์สำหรับ sample mean และ 1.0516 จุดเปอร์เซ็นต์สำหรับ factor prior ความต่างในข้อมูลสมมติสามเดือนไม่ได้พิสูจน์ว่า factor prior ดีกว่าโดยทั่วไป หากดูผลนี้ก่อนแล้วกลับไปปรับ premium ให้ RMSE ต่ำลง ข้อมูลกันยายนถึงพฤศจิกายนจะกลายเป็นข้อมูลที่ใช้เลือกแบบจำลอง และต้องกันข้อมูลช่วงใหม่ไว้ประเมินอีกครั้ง

ในการทดสอบพอร์ต ยังต้องตรึง covariance estimator, constraints, วิธีปรับพอร์ต และต้นทุนให้เปรียบเทียบกันได้ การใช้ realized factor returns ของเดือนที่ยังไม่มาถึงไปคำนวณ “forecast” ของเดือนนั้นเป็นการใช้ข้อมูลอนาคต แม้สมการ factor จะคำนวณถูกทุกพจน์ก็ตาม

บทถัดไป [Implied Returns และ Views](implied-returns-views.html) จะเริ่มจากน้ำหนักพอร์ตอ้างอิงแล้วถามกลับว่าค่าคาดหวังแบบใดรองรับน้ำหนักนั้น จากนั้น[บท Black–Litterman](black-litterman.html)จะรวม prior กับมุมมองและระดับความไม่แน่นอนของมุมมองอย่างเป็นระบบ

<span id="expected-return-exercises"></span>

## แบบฝึกหัดพร้อมแนวคำตอบ

### 1. ค่าเฉลี่ยเลขคณิตกับการทบต้น

พอร์ตหนึ่งเริ่มที่ 100 และจบที่ 144 หลังสองปี เส้นทางแรกได้ 20% ทั้งสองปี เส้นทางที่สองได้ −20% แล้ว 80% ค่าเฉลี่ยเลขคณิตและ CAGR ของสองเส้นทางเท่ากันหรือไม่?

เฉลย: ผลคูณของทั้งสองเส้นทางเป็น 1.44 จึงมี CAGR $\sqrt{1.44}-1=20\%$ เท่ากัน แต่ค่าเฉลี่ยเลขคณิตเป็น 20% กับ $(-20\%+80\%)/2=30\%$ ตามลำดับ การรู้มูลค่าต้นและปลายอย่างเดียวจึงไม่กำหนดค่าเฉลี่ยเลขคณิตของผลตอบแทนรายช่วง

### 2. SD สูงไม่ได้แปลว่า SE เท่ากับ SD

สมมติผลตอบแทน IID Normal มี SD ที่รู้แน่นอน 4% ต่อเดือน เก็บ 100 เดือน และได้ sample mean 0.5% ต่อเดือน SE และช่วง mean แบบ Normal 95% โดยใช้ค่าขอบ 1.96 เป็นเท่าไร?

เฉลย: SE เท่ากับ $4\%/\sqrt{100}=0.4$ จุดเปอร์เซ็นต์ ช่วง mean เป็น $0.5\%\pm1.96(0.4\%)$ หรือ −0.284% ถึง 1.284% ต่อเดือน โจทย์ให้ population SD จึงใช้ Normal critical value หากประมาณ SD จากข้อมูลจะใช้ t critical value ตามเงื่อนไขของสูตรก่อนหน้า ช่วงนี้ยังไม่ใช่ prediction interval ของเดือนหน้า

### 3. ต้องเพิ่มประวัติเท่าไรจึงลด SE ครึ่งหนึ่ง?

ใน additive IID model annual SD 20% ประวัติสี่ปีให้ SE ของ annual mean เท่าไร และต้องมีประวัติกี่ปีจึงลด SE ครึ่งหนึ่ง?

เฉลย: ได้ $20\%/\sqrt4=10$ จุดเปอร์เซ็นต์ ต้องเพิ่มเป็น 16 ปีจึงได้ $20\%/\sqrt{16}=5$ จุดเปอร์เซ็นต์ การเปลี่ยนสี่ปีเดิมจากข้อมูลรายเดือนเป็นรายวันไม่ให้ผลเท่ากับเพิ่มเป็น 16 ปี

### 4. Bayesian update ต้องรอข้อมูลมากก่อนหรือไม่?

เริ่มจาก prior $\operatorname{Beta}(2,2)$ แล้วเห็นหัวหก ก้อยสี่ หากครั้งถัดไปออกหัว ค่าเฉลี่ย posterior เปลี่ยนอย่างไร?

เฉลย: หลังสิบครั้ง posterior เป็น $\operatorname{Beta}(8,6)$ มี mean $8/14\approx57.14\%$ เมื่อเพิ่มหัวอีกหนึ่งเป็น $\operatorname{Beta}(9,6)$ มี mean $9/15=60\%$ ข้อมูลใหม่อัปเดต posterior ได้ทันทีภายใต้แบบจำลองนี้

### 5. Shrinkage target ไม่ใช่น้ำหนักพอร์ต

ค่าประมาณ expected returns รายปีเป็น 10% และ 2% เลือก target ร่วม 6% และ $\delta=0.75$ ได้ expected returns ใหม่เท่าไร และบอกได้หรือยังว่าต้องถือ 50/50?

เฉลย: ได้ $0.25(10\%)+0.75(6\%)=7\%$ และ $0.25(2\%)+0.75(6\%)=5\%$ ยังสรุปน้ำหนักไม่ได้ ต้องรู้ covariance, objective และ constraints ด้วย แม้หดจน expected returns เท่ากัน GMV ก็ไม่จำเป็นต้องเป็น equal-weight

### 6. เมื่อ common excess return ติดลบ

ทุกสินทรัพย์มี expected return 1% ต่อปี แต่ $r_f=3\%$ พอร์ตหนึ่งมี volatility 8% อีกพอร์ต 20% พอร์ตใดมี Sharpe มากกว่า?

เฉลย: Sharpe เป็น $-2\%/8\%=-0.25$ และ $-2\%/20\%=-0.10$ พอร์ต volatility สูงกว่ามี Sharpe มากกว่าในโจทย์นี้ จึงใช้ข้อสรุป equal means → MSR คือ GMV โดยไม่ระบุ positive common premium ไม่ได้

### 7. คูณ Loading กับ Premium โดยดูเครื่องหมายและหน่วย

สินทรัพย์มี loadings ต่อ Market/Value เท่ากับ 1.1/−0.4 คาด premia รายเดือน 0.4%/0.2% และ $r_f=0.1\%$ ต่อเดือน ถ้าตั้ง expected alpha ศูนย์ ได้ expected return เท่าไร?

เฉลย: $0.1\%+1.1(0.4\%)-0.4(0.2\%)=0.46\%$ ต่อเดือน หากเพิ่ม expected alpha 0.05% ต่อเดือนจะเป็น 0.51% การเพิ่ม alpha เป็นสมมติฐาน forecast เพิ่มเติม ไม่ใช่สิ่งที่ต้องใส่ตาม fitted historical alpha เสมอ

### 8. OLS fit ตรงค่าเฉลี่ยแล้วพิสูจน์อะไรได้?

ใช้ intercept และ factor means จากช่วงฝึกเดียวกันแล้วสร้างค่าเฉลี่ยสินทรัพย์กลับมาได้ตรง จากนั้นลอง premium 50 ชุดและเลือกชุดที่ RMSE ต่ำสุดในสามเดือนประเมิน เรามีหลักฐานพยากรณ์ที่น่าเชื่อถือพอหรือยัง?

เฉลย: การคืน sample mean เป็นเอกลักษณ์ของ OLS ที่มี intercept ส่วนการเลือกจาก 50 ชุดใช้ช่วงประเมินมาช่วยปรับแบบจำลองแล้ว ต้องแยกช่วงเลือกวิธีออกจากช่วงทดสอบถัดไป พร้อมพิจารณาความยาวข้อมูลและความไม่แน่นอนของคะแนน ไม่มีขั้นใดพิสูจน์ว่า expected returns ในอนาคตตรงกับ forecast ที่เลือก

<span id="expected-return-sources"></span>

## แหล่งเรียนและขอบเขตของบท

อ่าน Transcript เต็มเมื่อ 3 ตุลาคม 2026 ของ [Lack of Robustness of Expected Return Estimates](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/1U7Zh/lack-of-robustness-of-expected-return-estimates), [Agnostic Priors on Expected Return Estimates](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/TbidX/agnostic-priors-on-expected-return-estimates) และ [Using Factor Models to Estimate Expected Returns](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/c6E51/using-factor-models-to-estimate-expected-returns) ใช้เป็นโครงเรื่อง estimation error, mean shrinkage, agnostic assumptions และ factor premia ตัวอย่าง โค้ด คำอธิบายไทย และแบบฝึกหัดเขียนขึ้นใหม่ ไม่ใช่การทำซ้ำตาราง sector portfolios หรือผลทดสอบของวิดีโอ

สูตร SE และ confidence interval ตรวจจาก [NIST: Confidence Limits for the Mean](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) และ [What are confidence intervals?](https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm) การอัปเดต Beta–Bernoulli ตรวจจาก [Stanford STATS 200, Lecture 21](https://web.stanford.edu/class/archive/stats/stats200/stats200.1172/Lecture21.pdf) สมการ factor expected returns ตรวจจาก [Sharpe: Factor-based Expected Returns, Risks and Correlations](https://web.stanford.edu/~wfsharpe/mia/fac/mia_fac3.htm) ส่วน API ที่ใช้ดู [SciPy: Student's t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html) และ [SciPy: minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)

ในการอ่านประกอบคอร์ส ให้แยกผลตอบแทนสะสม อัตราทบต้น และค่าเฉลี่ยเลขคณิตออกจากกัน การใช้ช่วงข้อมูลต่างกันให้ sample means ต่างกันได้ แต่ค่าเฉลี่ยติดลบไม่ได้เป็นสิ่งที่เป็นไปไม่ได้โดยนิยาม บทนี้จึงตรวจสมมติฐานและความไม่แน่นอนของค่าประมาณก่อนแปลความหมายด้านพอร์ต พร้อมระบุเงื่อนไข premium บวกในเอกลักษณ์ GMV/DR/CAPM และให้ Bayesian update รับข้อมูลทุกครั้งตามแบบจำลองที่เลือก
