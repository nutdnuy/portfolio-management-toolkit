---
title: Monte Carlo — สร้างเส้นทางราคาและทดสอบ CPPI ด้วย Python
description: เรียน Brownian increments, Exact GBM, Seed และแกนของ Array ก่อนจำลอง CPPI หลายเส้นทาง แยกโอกาสทะลุ Floor, Shortfall และความผิดพลาดของแบบจำลอง
---

# Monte Carlo: สร้างหลายเส้นทางแล้ววัดผล

<p class="lead">CPPI ผ่านตัวอย่างหกเดือนแล้ว แต่ถ้าตลาดลงก่อนฟื้น หรือผันผวนกว่าที่คาด ผลจะเปลี่ยนไปเพียงใด?</p>

บท [CPPI จากศูนย์](cppi-dynamic-allocation.html) ใช้ผลตอบแทนที่กำหนดไว้ล่วงหน้าหนึ่งเส้นทาง บทนี้จะให้คอมพิวเตอร์สร้างเส้นทางจำนวนมากจากแบบจำลองเดียวกัน แล้วนับว่าพอร์ตจบต่ำกว่า floor กี่ครั้ง และขาดไปครั้งละเท่าไร วิธีสุ่มเพื่อประมาณผลลัพธ์ลักษณะนี้เรียกว่า **Monte Carlo simulation**

การจำลองช่วยตอบคำถามว่า “ถ้าโลกทำงานตามสมมติฐานเหล่านี้ กลยุทธ์จะมีผลอย่างไร” จำนวนเส้นทางที่มากขึ้นทำให้ประมาณผลภายในแบบจำลองได้แม่นขึ้น แต่ไม่ได้ทำให้สมมติฐานของตลาดถูกต้องขึ้นโดยอัตโนมัติ เราจะแยกสองประเด็นนี้ตลอดบท

ตัวเลขทั้งหมดเป็น **การทดลองสมมติ** โค้ดรันจาก Notebook ใหม่ได้ตามลำดับด้วย NumPy, pandas และ SciPy โดยไม่ต้องมี CSV หรือฟังก์ชันจากบทก่อน ตัวอย่างหลักไม่ต้องติดตั้งเครื่องมือวาดกราฟหรือ ipywidgets

| ช่วงเรียน | คำถาม |
|---|---|
| [จากผลตอบแทนหนึ่งงวดสู่ GBM](#gbm-model) | สุ่มส่วนใด และเวลาเข้าไปอยู่ในสูตรอย่างไร? |
| [สร้าง Array ของหลายเส้นทาง](#gbm-python) | แถวกับคอลัมน์หมายถึงอะไร? |
| [ตรวจผลกับสูตร](#monte-carlo-error) | ค่าเฉลี่ยจำลองห่างจากค่าทฤษฎีเท่าไรจึงยังสมเหตุสมผล? |
| [ใส่ CPPI ลงในเส้นทาง](#cppi-simulation) | กลยุทธ์แต่ละตัวได้รับตลาดชุดเดียวกันหรือไม่? |
| [นับ Shortfall](#shortfall-statistics) | ทะลุระหว่างทางกับจบต่ำกว่า floor ต่างกันอย่างไร? |
| [ทดสอบสมมติฐาน](#simulation-limits) | ปรับจำนวนตัวอย่าง ความถี่ หรือแบบจำลอง กำลังแก้ปัญหาชนิดใด? |

[ดาวน์โหลด Notebook ของบทนี้](notebooks/monte-carlo.ipynb) เพื่อรันตัวอย่างตามลำดับและเทียบผลลัพธ์ที่บันทึกไว้

<span id="gbm-model"></span>

## แบบจำลองราคา: การเติบโตกับแรงสุ่ม

ใน **Geometric Brownian Motion หรือ GBM** อัตราการเปลี่ยนแปลงของราคาแบ่งเป็นส่วนแนวโน้มเฉลี่ยกับส่วนสุ่ม เขียนแบบต่อเนื่องได้ว่า

$$
\frac{dS_t}{S_t}=\mu\,dt+\sigma\,dW_t
$$

$S_t$ คือราคา ณ เวลา $t$ ใช้หน่วยบาทในตัวอย่าง $\mu$ คือ drift ของราคาในแบบจำลอง หน่วยต่อปี ส่วน $\sigma$ คือ volatility ต่อรากของปี และ $W_t$ คือ Brownian motion เราจะใช้เวลาเป็นปีทั้งหมด จึงต้องแปลงหนึ่งเดือนเป็น $\Delta t=1/12$ ปี และหนึ่งไตรมาสเป็น $1/4$ ปี

สำหรับผู้เริ่มต้น ยังไม่ต้องคำนวณ stochastic calculus เพื่อจำลองสูตรนี้ ให้เริ่มจากคุณสมบัติของการเปลี่ยนแปลง Brownian ในหนึ่งช่วงเวลา

$$
\Delta W=\sqrt{\Delta t}\,Z,\qquad Z\sim N(0,1)
$$

$Z$ เป็นตัวเลขที่สุ่มจาก Standard Normal ซึ่งมี mean 0 และ SD 1 เราจึงได้ variance ของ $\Delta W$ เท่ากับ $\Delta t$ และ SD เท่ากับ $\sqrt{\Delta t}$ ภายใต้แบบจำลองนี้ increments ของช่วงเวลาที่ไม่ทับกันเป็นอิสระกัน

ถ้า annual volatility เป็น 20% ขนาด SD ของส่วนสุ่มในหนึ่งเดือนจะเป็น $0.20\sqrt{1/12}\approx5.7735\%$ ไม่ใช่ $20\%/12$ ส่วน drift ต้องคูณ $1/12$ เพราะส่วนเฉลี่ยสะสมตามเวลา ขณะที่ variance ของ increments อิสระสะสมตามเวลา จึงมีรากที่สองในสูตร SD

### สูตรจำลองแบบ Exact ที่จุดเวลา

เมื่อ $\mu$ และ $\sigma$ คงที่ และไม่มีเงินปันผลแยกออกจากราคา คำตอบของแบบจำลองในแต่ละช่วงคือ

$$
S_{t+\Delta t}
=S_t\exp\left[(\mu-\tfrac12\sigma^2)\Delta t
+\sigma\sqrt{\Delta t}\,Z\right]
$$

วงเล็บใน exponential คือ **log return** ของช่วงนั้น ส่วน simple return คือ exponential ของวงเล็บแล้วลบ 1 สูตรนี้รักษาราคาให้เป็นบวก ใน constant-parameter GBM log returns เป็น Normal ส่วนราคาในอนาคตเป็น Lognormal ดูที่มาได้ใน [เอกสาร GBM ของ Karl Sigman, Columbia University](https://www.columbia.edu/~ks20/FE-Notes/4700-07-Notes-GBM.pdf) โดยต้องตรวจนิยาม drift เมื่อเทียบแหล่งอื่น เพราะบางเอกสารใช้ $\mu$ เรียก drift ของ log price

คำว่า exact หมายถึงสุ่มการเปลี่ยนแปลงระหว่างจุดเวลาได้ตรงกับแบบจำลอง GBM นี้ ไม่ได้หมายความว่าจำลองตลาดจริงได้ตรง และไม่ได้บอกเส้นทางทุกขณะระหว่างจุดเวลาเหล่านั้น

ลองใช้ $\mu=6\%$, $\sigma=20\%$ และหนึ่งเดือน โดยกำหนดค่า $Z$ ไว้เป็น −1, 0 และ +1 เพื่อดูผลของสูตรก่อนเริ่มสุ่ม

```python
import numpy as np
import pandas as pd
from scipy import stats

example_z = np.array([-1.0, 0.0, 1.0])
example_dt = 1 / 12
example_log_returns = (0.06 - 0.5 * 0.20**2) * example_dt + 0.20 * np.sqrt(example_dt) * example_z
example_simple_returns = np.expm1(example_log_returns)
print(pd.DataFrame({"Z": example_z, "Monthly return (%)": example_simple_returns * 100}).round(4))
```

| $Z$ | Simple return หนึ่งเดือน |
|---:|---:|
| −1 | −5.2948% |
| 0 | +0.3339% |
| +1 | +6.2972% |

`np.expm1(x)` คำนวณ $e^x-1$ ได้โดยตรงและช่วยความแม่นยำเมื่อ $x$ ใกล้ศูนย์ ผลตอบแทนเมื่อ $Z=0$ ไม่ใช่ค่าเฉลี่ย simple return เพราะ exponential เป็นฟังก์ชันโค้ง ภายใต้แบบจำลองนี้ค่าเฉลี่ย gross return ของงวดคือ $e^{\mu\Delta t}$

### ระวังความหมายของ “ผลตอบแทน 6% ต่อปี”

ถ้าใส่ $\mu=0.06$ ในสูตรข้างต้น ค่าเฉลี่ยการเติบโตหนึ่งปีคือ $e^{0.06}-1\approx6.1837\%$ หากต้องการตั้ง **expected simple return หนึ่งปี** ให้เท่ากับ $g=6\%$ พอดี ต้องใช้

$$
\mu=\log(1+g)=\log(1.06)\approx0.058269
$$

ตัวอย่างหลักหลังจากนี้จะใช้ convention หลัง คือ $g=6\%$ และคำนวณ $\mu$ จาก `np.log1p(g)` ส่วนความผันผวนจะเพิ่มเป็น 30% ต่อรากของปีเพื่อทดลองตลาดที่กระจายกว้างขึ้น ทั้งสองค่าเป็นสมมติฐานที่ตั้งเพื่อเรียน ไม่ใช่ประมาณการตลาด

### สูตร Euler ที่พบใน Lab ต่างกันอย่างไร?

อีกวิธีหนึ่งประมาณ simple return เป็น $R\approx\mu\Delta t+\sigma\sqrt{\Delta t}Z$ แล้วนำ $1+R$ มาคูณต่อกัน นี่คือรูปแบบ **Euler** ของ SDE ซึ่งเป็นค่าประมาณและอาจสร้าง $R<-100\%$ ได้ เพราะ Normal ไม่มีขอบล่าง การจำลองแบบ exponential ด้านบนจะไม่เกิดปัญหาราคาติดลบจากสูตรนี้

เมื่อเทียบ `lab_121`, `lab_123` และเอกสาร [gbm function](https://www.coursera.org/learn/introduction-portfolio-construction-python/supplement/d3h3F/gbm-function) ให้ตรวจสูตรที่ใช้ในไฟล์ด้วย รุ่นที่ตั้ง mean ของ gross return เป็น $(1+g)^{\Delta t}$ แล้วบวกแรงสุ่มแบบ Normal ทำให้ค่าเฉลี่ย gross return มีการทบต้นตาม $g$ แต่ยังคงเป็นการสุ่ม **gross return แบบ Normal** จึงไม่ได้กลายเป็น exact lognormal GBM เพียงเพราะปรับ mean แล้ว

<span id="gbm-python"></span>

## สร้างตาราง 12 งวด × 20,000 เส้นทาง

เราจะทดลองสามปี ปรับพอร์ตรายไตรมาส ดังนั้นมี $3\times4=12$ ช่วงผลตอบแทน และมี 13 จุดราคาเมื่อรวมวันเริ่มต้น ทุกเส้นทางเริ่มที่ 100 บาท

| ตัวแปร | ค่า | ความหมาย |
|---|---:|---|
| `mc_years` | 3 | ระยะเวลาจำลองเป็นปี |
| `mc_steps_per_year` | 4 | จำนวนช่วงต่อปี |
| `mc_paths` | 20,000 | จำนวนเส้นทางสุ่ม |
| `mc_growth` | 0.06 | expected simple return หนึ่งปี |
| `mc_sigma` | 0.30 | volatility ต่อรากของปี |
| `mc_seed` | 202603 | เลขตั้งต้นเครื่องสุ่มสำหรับทำซ้ำ |

```python
mc_years = 3
mc_steps_per_year = 4
mc_paths = 20_000
mc_growth = 0.06
mc_mu = np.log1p(mc_growth)
mc_sigma = 0.30
mc_start = 100.0
mc_seed = 202603
mc_steps = mc_years * mc_steps_per_year
mc_dt = 1 / mc_steps_per_year

mc_rng = np.random.default_rng(mc_seed)
mc_z = mc_rng.standard_normal((mc_steps, mc_paths))
mc_log_returns = (mc_mu - 0.5 * mc_sigma**2) * mc_dt + mc_sigma * np.sqrt(mc_dt) * mc_z
mc_risky_returns = np.expm1(mc_log_returns)
mc_prices = mc_start * np.vstack([
    np.ones(mc_paths),
    np.exp(np.cumsum(mc_log_returns, axis=0))
])
print("Returns shape:", mc_risky_returns.shape)
print("Prices shape:", mc_prices.shape)
print(pd.DataFrame(mc_prices[:4, :3]).round(4))
```

`20_000` เป็นเลข 20000 ที่ใส่ขีดล่างเพื่ออ่านง่าย `standard_normal((12, 20000))` สุ่มตารางที่มี 12 แถวและ 20,000 คอลัมน์ แต่ละคอลัมน์เป็นโลกสมมติหนึ่งเส้นทาง และแต่ละแถวเป็นหนึ่งไตรมาส เอกสาร [NumPy standard_normal](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.standard_normal.html) อธิบาย mean, SD และรูปร่างของผลที่คืนมา

`np.cumsum(..., axis=0)` รวม log return สะสม **ลงตามแถวเวลาในแต่ละคอลัมน์** แล้ว `np.exp` เปลี่ยนกลับเป็นตัวคูณราคา `np.ones(mc_paths)` สร้างแถวเริ่มต้นที่ทุกเส้นทางมีตัวคูณ 1 ส่วน `np.vstack` ต่อแถวนี้ไว้ด้านบน จึงได้ shape ของผลตอบแทน `(12, 20000)` และ shape ของราคา `(13, 20000)`

ถ้าไม่ระบุแกนในคำสั่งสะสมบางชนิด เช่น `np.cumprod` ค่าเริ่มต้นอาจนำสมาชิกทั้งตารางมาต่อเป็นชุดเดียว ทำให้กำลังทบต้นข้ามคนละเส้นทาง ตรวจพฤติกรรม `axis` ได้จาก [เอกสาร NumPy](https://numpy.org/doc/stable/reference/generated/numpy.cumprod.html)

`mc_prices[:4, :3]` เลือกสี่แถวแรกและสามเส้นทางแรกเพื่อดูรูปทรงข้อมูล โดย `:4` ไม่รวมตำแหน่ง 4 เราไม่จำเป็นต้องพิมพ์ 20,000 คอลัมน์เพื่อพิสูจน์ว่า array ถูกต้อง

### Seed ทำให้ทบทวนผลได้ แต่ไม่เพิ่มความสมจริง

`default_rng(202603)` สร้างเครื่องสุ่มที่เริ่มจากสถานะที่กำหนด หากสร้างเครื่องสุ่มใหม่ด้วย seed เดิมและเรียกคำสั่งเหมือนเดิมในสภาพแวดล้อมเดียวกัน จะทำซ้ำผลได้ ถ้าเรียกสุ่มซ้ำบน `mc_rng` ตัวเดิม สถานะได้เดินหน้าไปแล้ว จึงได้ชุดใหม่ การทำซ้ำข้ามเวอร์ชันหรือเปลี่ยนวิธีเรียกอาจต่างกัน ควรเก็บทั้ง seed และเวอร์ชันแพ็กเกจตามคำอธิบายของ [NumPy Generator](https://numpy.org/doc/stable/reference/random/generator.html)

```python
print("NumPy version:", np.__version__)
mc_rng_check = np.random.default_rng(mc_seed)
assert np.array_equal(mc_z, mc_rng_check.standard_normal((mc_steps, mc_paths)))
assert np.allclose(mc_prices[0], mc_start)
assert np.all(mc_prices > 0)
assert np.allclose(mc_prices[1:] / mc_prices[:-1] - 1, mc_risky_returns)
```

`array_equal` ตรวจสมาชิกทุกตำแหน่งว่าเหมือนกัน `allclose` ยอมให้มีความคลาดเคลื่อนจากการคำนวณทศนิยมเล็กน้อย และ `assert` หยุดเมื่อสิ่งที่ตรวจไม่จริง การตรวจบรรทัดสุดท้ายเชื่อมราคาที่จำลองกับผลตอบแทนที่เราจะนำไปใช้ใน CPPI

<span id="monte-carlo-error"></span>

## ตรวจค่าเฉลี่ยกับสูตร ก่อนนำไปทดสอบกลยุทธ์

สำหรับ GBM ค่าคาดหมายและมัธยฐานของราคาปลายทางเป็น

$$
\mathbb{E}[S_T]=S_0e^{\mu T},\qquad
\operatorname{Median}(S_T)=S_0e^{(\mu-\sigma^2/2)T}
$$

ภายใต้พารามิเตอร์ที่กำหนด ค่าเฉลี่ยตามสูตรเท่ากับ $100(1.06)^3=119.1016$ บาท ส่วนมัธยฐานประมาณ 104.0610 บาท ค่าเฉลี่ยสูงกว่ามัธยฐานเพราะการแจกแจงราคามีหางขวา เส้นทางที่โตมากสามารถดึงค่าเฉลี่ยขึ้นได้ จึงควรรายงานมากกว่าตัวเลข mean เพียงค่าเดียว

การสุ่ม 20,000 เส้นทางไม่จำเป็นต้องให้ค่าเฉลี่ยตรงกับสูตรทุกหลัก **Monte Carlo standard error หรือ SE** ของค่าเฉลี่ยประมาณได้จาก SD ของราคาปลายทางหารด้วยรากที่สองของจำนวนเส้นทาง เมื่อเส้นทางเป็นอิสระและมี variance จำกัด

$$
SE(\overline S_T)\approx\frac{s(S_T)}{\sqrt N}
$$

```python
mc_terminal = mc_prices[-1]
mc_theory_mean = mc_start * np.exp(mc_mu * mc_years)
mc_theory_median = mc_start * np.exp((mc_mu - 0.5 * mc_sigma**2) * mc_years)
mc_mean = mc_terminal.mean()
mc_se = mc_terminal.std(ddof=1) / np.sqrt(mc_paths)
mc_mean_interval = mc_mean + np.array([-1.0, 1.0]) * 1.96 * mc_se
print("Theory mean:", round(mc_theory_mean, 4))
print("Simulation mean:", round(mc_mean, 4))
print("Theory median:", round(mc_theory_median, 4))
print("Simulation median:", round(np.median(mc_terminal), 4))
print("Mean standard error:", round(mc_se, 4))
print("Approximate 95% interval for model mean:", np.round(mc_mean_interval, 4))
```

ผลจาก seed นี้และ NumPy 2.0.2 ให้ mean ประมาณ 119.3784 บาท median 103.8237 บาท และ SE ของ mean 0.4769 บาท ช่วงประมาณ 95% สำหรับค่าเฉลี่ยของแบบจำลองเป็นราว 118.4437–120.3131 บาท ค่าทฤษฎี 119.1016 อยู่ในช่วงนี้

ช่วงดังกล่าวอาศัยการประมาณแบบ Normal ของค่าเฉลี่ยจากหลายเส้นทาง ไม่ใช่ช่วงที่ราคาปลายทาง 95% ของผู้ลงทุนจะอยู่ และไม่รวมความไม่แน่นอนว่าเราตั้ง $\mu$ หรือ $\sigma$ ถูกหรือไม่ ถ้าต้องการกระจายผลลัพธ์ของแต่ละเส้นทาง ให้ดู quantile ของ `mc_terminal` แยกต่างหาก

```python
mc_probabilities = np.array([0.05, 0.50, 0.95])
mc_terminal_quantiles = np.quantile(mc_terminal, mc_probabilities)
mc_theory_quantiles = mc_start * np.exp(
    (mc_mu - 0.5 * mc_sigma**2) * mc_years
    + mc_sigma * np.sqrt(mc_years) * stats.norm.ppf(mc_probabilities)
)
print(pd.DataFrame({"Simulation": mc_terminal_quantiles, "Theory": mc_theory_quantiles},
                   index=["5%", "50%", "95%"]).round(4))
```

`np.quantile` หาจุดแบ่งจากราคาปลายทางที่สุ่มได้ ส่วน `stats.norm.ppf` ให้ quantile ของ Standard Normal เพื่อนำไปแทนในสูตร lognormal และเปรียบเทียบกับค่าทฤษฎี ทั้งสองคอลัมน์เป็น quantile ของผลลัพธ์แต่ละเส้นทาง ไม่ใช่ช่วงความเชื่อมั่นของค่าเฉลี่ย

ถ้าต้องการลด SE ของ mean เหลือครึ่งหนึ่งโดยยังใช้วิธีสุ่มเดิมและแบบจำลองเดิม โดยทั่วไปต้องเพิ่มเส้นทางประมาณสี่เท่า เพราะ SE ลดตาม $1/\sqrt N$ จำนวนเส้นทางกับจำนวนช่วงเวลามีหน้าที่คนละอย่าง การเพิ่มจาก 12 เป็น 52 จุดต่อปีไม่ได้เพิ่มจำนวนโลกอิสระที่ใช้ประมาณ mean

<span id="cppi-simulation"></span>

## ให้ CPPI ทำงานพร้อมกันทุกเส้นทาง

เราจะเริ่มพอร์ตละ 100 บาท ตั้ง **floor คงที่ 80 บาท** และให้เงินสดมีผลตอบแทนทบต้น 2% ต่อปี จึงให้เงินสดหนึ่งไตรมาสเท่ากับ $(1.02)^{1/4}-1$ ประมาณ 0.4963% การคำนวณครั้งนี้ต่างจากตัวอย่างรายเดือนเงินสด 0% ในบทก่อน จึงระบุค่าใหม่ทั้งหมด

ยังคงไม่มีค่าธรรมเนียม ภาษี การกู้ หรือการขายชอร์ต และให้ซื้อขายเศษหน่วยได้ ค่าต่อไปนี้เป็นกติกาในการทดลอง ไม่ใช่การรับประกัน floor เราจะใช้ผลตอบแทน GBM ชุดเดียวกันกับทุกค่า multiplier เพื่อให้ความต่างที่เห็นมาจากกติกาการลงทุน ไม่ปนกับการเปลี่ยนชุดสุ่ม

```python
def cppi_many_paths(risky_returns, start=100.0, floor=80.0,
                    multiplier=3.0, cash_annual=0.02, steps_per_year=4):
    returns = np.asarray(risky_returns, dtype=float)
    if returns.ndim != 2 or not np.isfinite(returns).all() or (returns < -1).any():
        raise ValueError("Use a finite time-by-path matrix of simple returns >= -1.")
    if start <= 0 or not 0 <= floor <= start or multiplier < 0:
        raise ValueError("Check start, floor and multiplier.")
    if cash_annual <= -1 or steps_per_year <= 0:
        raise ValueError("Check cash rate and steps per year.")

    n_steps, n_paths = returns.shape
    wealth = np.full((n_steps + 1, n_paths), start, dtype=float)
    cash_return = (1 + cash_annual)**(1 / steps_per_year) - 1
    for step in range(n_steps):
        current = wealth[step]
        risky_amount = np.clip(multiplier * (current - floor), 0, current)
        safe_amount = current - risky_amount
        wealth[step + 1] = risky_amount * (1 + returns[step]) + safe_amount * (1 + cash_return)
    return wealth

mc_floor = 80.0
mc_cppi = cppi_many_paths(mc_risky_returns)
print("CPPI wealth shape:", mc_cppi.shape)
print(pd.DataFrame(mc_cppi[:4, :3]).round(4))
```

โค้ดยังต้องวนตามเวลา เพราะเงินงวดหน้าขึ้นกับงวดนี้ แต่ไม่ต้องเขียน loop อีกชั้นเพื่อวน 20,000 เส้นทาง `current` เป็นแถวที่มีมูลค่าพอร์ตครบทุกเส้นทาง การลบ floor คูณ multiplier และ `clip` จึงคำนวณให้แต่ละเส้นทางพร้อมกัน

`np.full((n_steps + 1, n_paths), start, dtype=float)` เตรียมตารางที่เริ่มด้วยค่าตั้งต้นทุกช่อง ต่อมา loop เขียนค่าผลลัพธ์ลงแถว 1 ถึงแถวสุดท้าย แถว 0 คงอยู่เป็นเงินเริ่มต้น ทุกเส้นทางได้รับผลตอบแทนของตัวเองจาก `returns[step]` จึงไม่มีการเฉลี่ยเส้นทางก่อนตัดสินใจวงเงินเสี่ยง

ถ้าเอาราคาเฉลี่ยของ 20,000 เส้นทางมาทำ CPPI เพียงครั้งเดียว ผลนั้นไม่เท่ากับการเฉลี่ยผล CPPI ของ 20,000 เส้นทาง เพราะกติกามีทั้ง floor และการจำกัดวงเงินซึ่งตอบสนองต่อสถานะของแต่ละเส้นทาง

<span id="shortfall-statistics"></span>

## ทะลุ floor ระหว่างทาง กับจบต่ำกว่า floor

กำหนด **terminal breach** ว่าเงินปลายปีที่สามต่ำกว่า 80 บาท ส่วน **grid breach** หมายถึงเคยต่ำกว่า 80 บาท ณ จุดตรวจรายไตรมาสอย่างน้อยหนึ่งครั้ง ทั้งสองตัวนับไม่จำเป็นต้องเท่ากัน เพราะพอร์ตที่ลงต่ำกว่า floor อาจถือเงินสดแล้วรับดอกเบี้ยจนกลับขึ้นมาได้

เราตรวจได้เฉพาะจุดที่จำลองไว้ใน array หากพอร์ตต่ำกว่า floor ระหว่างไตรมาสแล้วกลับขึ้นมาก่อนสิ้นไตรมาส ตัวนับ grid breach จะไม่เห็นเหตุการณ์นั้น การใช้คำว่า “เคยทะลุ” จึงต้องระบุความถี่ที่สังเกตด้วย

**Shortfall** ปลายทางในบทนี้เป็นจำนวนเงินบาทที่ขาดจาก floor และไม่นับค่าติดลบเมื่อพอร์ตสูงกว่า floor

$$
L_j=\max(F-V_{T,j},0)
$$

$j$ คือหมายเลขเส้นทาง เราจะแยกค่าเฉลี่ยสองแบบ: เฉลี่ย shortfall ทุกเส้นทาง โดยเส้นทางที่ไม่ขาดมีค่า 0 และเฉลี่ยเฉพาะเส้นทางที่ขาด หากไม่มีเส้นทางใดขาด ค่าแบบหลังยังคำนวณจากตัวอย่างไม่ได้ จึงแสดง `NaN` แทนการรายงานว่าเฉลี่ยขาดศูนย์บาท

```python
def shortfall_summary(wealth, floor=80.0):
    terminal = wealth[-1]
    shortfall = np.maximum(floor - terminal, 0.0)
    terminal_breach = terminal < floor
    grid_breach = (wealth[1:] < floor).any(axis=0)
    return pd.Series({
        "Terminal mean": terminal.mean(),
        "Terminal median": np.median(terminal),
        "Terminal breaches": int(terminal_breach.sum()),
        "Grid breaches": int(grid_breach.sum()),
        "Terminal breach probability": terminal_breach.mean(),
        "Grid breach probability": grid_breach.mean(),
        "Mean shortfall across all paths": shortfall.mean(),
        "Mean shortfall given breach": shortfall[terminal_breach].mean() if terminal_breach.any() else np.nan
    })

mc_summary = shortfall_summary(mc_cppi, mc_floor)
print(mc_summary.round(6))
```

`wealth[-1]` เลือกแถวสุดท้าย `terminal < floor` ได้ชุด True/False และ `.mean()` ของชุดนี้ให้สัดส่วน True เพราะ Python นับ True เป็น 1 และ False เป็น 0 ส่วน `.any(axis=0)` ตรวจลงตามเวลาในแต่ละเส้นทางว่ามีอย่างน้อยหนึ่งจุดเป็น True หรือไม่

ผลของตัวอย่าง $m=3$ จาก 20,000 เส้นทางมีดังนี้

| ตัววัด | ผลที่ได้ | หน่วยหรือความหมาย |
|---|---:|---|
| Mean ปลายทาง | 114.4867 | บาท |
| Median ปลายทาง | 93.2148 | บาท |
| จบต่ำกว่า floor | 156 | เส้นทาง |
| สัดส่วนจบต่ำกว่า floor | 0.78% | 156 / 20,000 |
| เคยต่ำกว่า floor ณ จุดตรวจ | 504 | เส้นทาง |
| สัดส่วนเคยต่ำกว่า floor ณ จุดตรวจ | 2.52% | 504 / 20,000 |
| Mean shortfall ทุกเส้นทาง | 0.0152 | บาทต่อเส้นทาง |
| Mean shortfall เฉพาะเมื่อขาด | 1.9484 | บาทต่อเส้นทางที่ขาด |

ค่า 0.0152 บาทดูเล็ก เพราะเฉลี่ยรวมเส้นทางที่ shortfall เป็นศูนย์จำนวนมาก ตรวจความสัมพันธ์ได้ว่า $0.0078\times1.9484\approx0.0152$ จึงควรรายงานทั้งความถี่กับขนาดเมื่อเกิดเหตุ ไม่ใช้ค่าเฉลี่ยทุกเส้นทางแทนความรุนแรงที่ผู้ประสบเหตุเจอ

### สัดส่วน 0.78% ยังมีความคลาดเคลื่อนจากการสุ่ม

เมื่อแต่ละเส้นทางเป็นอิสระ ตัวแปรว่าทะลุหรือไม่เป็น Bernoulli เราประมาณ SE ของสัดส่วนด้วย $\sqrt{\hat p(1-\hat p)/N}$ ได้ ตัวอย่างนี้มี terminal breach 156 ครั้ง จึงมี SE ประมาณ 0.0622 จุดเปอร์เซ็นต์

```python
mc_p = float(mc_summary["Terminal breach probability"])
mc_p_se = np.sqrt(mc_p * (1 - mc_p) / mc_paths)
print("Breach estimate (%):", 100 * mc_p)
print("Monte Carlo SE (percentage points):", 100 * mc_p_se)
print("Approximate interval (%):", 100 * (mc_p + np.array([-1, 1]) * 1.96 * mc_p_se))
```

ช่วงประมาณแบบ Normal เป็นราว 0.6581%–0.9019% ภายใต้แบบจำลองนี้ การประมาณดังกล่าวไม่เหมาะเมื่อจำนวนเหตุการณ์น้อยมากหรือเป็นศูนย์ เช่น ถ้าทดลอง $N$ เส้นทางแล้วไม่พบเหตุเลย ขอบบนด้านเดียว 95% จากสมการ $(1-p)^N=0.05$ คือ $p=1-0.05^{1/N}$ ภายใต้เส้นทางอิสระและโอกาสเกิดคงที่ สำหรับ 20,000 เส้นทางได้ประมาณ 0.0150% จึงยังไม่เท่ากับพิสูจน์ว่าโอกาสเป็นศูนย์

### เปรียบเทียบ multiplier บนตลาดชุดเดียวกัน

```python
mc_comparisons = {}
for m in [1.0, 2.0, 3.0, 4.0]:
    strategy_wealth = cppi_many_paths(mc_risky_returns, multiplier=m)
    mc_comparisons[f"m={m:g}"] = shortfall_summary(strategy_wealth, mc_floor)
mc_comparison_table = pd.DataFrame(mc_comparisons).T
print(mc_comparison_table[["Terminal mean", "Terminal median", "Terminal breaches", "Grid breaches"]].round(4))
```

| Multiplier | Mean ปลายทาง | Median ปลายทาง | จบต่ำกว่า floor | เคยต่ำกว่า floor ณ จุดตรวจ |
|---:|---:|---:|---:|---:|
| 1 | 109.0497 | 105.7109 | 0 | 0 |
| 2 | 112.4004 | 100.2959 | 0 | 0 |
| 3 | 114.4867 | 93.2148 | 156 | 504 |
| 4 | 115.3416 | 88.6271 | 1,248 | 3,246 |

ในตัวอย่างนี้เพิ่ม multiplier แล้ว mean สูงขึ้น แต่ median ต่ำลงและการทะลุ floor เพิ่มขึ้น การเลือกว่าใคร “ดีกว่า” จึงต้องระบุเป้าหมายและข้อจำกัดก่อน ตารางนี้ไม่ได้ให้ค่า multiplier ที่เหมาะกับทุกคน และการไม่พบเหตุใน $m=2$ ยังไม่ใช่หลักฐานว่าความเสี่ยงเป็นศูนย์

คอร์ส [Analyzing CPPI strategies](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/1rfqp/analyzing-cppi-strategies) และ [Designing and calibrating CPPI strategies](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/I3kmk/designing-and-calibrating-cppi-strategies) ใช้การทดลองเปลี่ยนพารามิเตอร์เพื่ออ่านผลลักษณะนี้ ตัวอย่างในหน้านี้ใช้ข้อมูลสุ่มและพารามิเตอร์ของเราเอง จึงไม่คาดหวังว่าตัวเลขจะตรงกับวิดีโอ

<span id="simulation-limits"></span>

## เปลี่ยนสมมติฐานให้ตรงคำถามที่อยากทดสอบ

การเพิ่มจำนวนเส้นทาง เปลี่ยนความถี่ซื้อขาย และเปลี่ยนแบบจำลองราคาแก้ความไม่แน่นอนคนละชนิด

| สิ่งที่เปลี่ยน | สิ่งที่กำลังศึกษา | สิ่งที่ยังไม่ถูกแก้ |
|---|---|---|
| เพิ่มจาก 20,000 เป็น 80,000 เส้นทาง | ลด sampling error ภายในแบบจำลองเดิม | แบบจำลองอาจยังไม่มี crash หรือ volatility clustering |
| เปลี่ยนการปรับพอร์ตรายไตรมาสเป็นรายเดือน | เปลี่ยนกติกาการซื้อขายและช่วงเวลาที่รับ gap risk | ยังมีต้นทุนและเหตุการณ์ระหว่างจุดปรับ |
| เพิ่ม volatility หรือเพิ่ม price jump | ทดสอบความไวต่อสมมติฐานตลาด | ต้องกำหนดขนาดและความถี่จากเหตุผลหรือข้อมูล |
| เพิ่มค่าธรรมเนียมและข้อจำกัดซื้อขาย | ทดสอบความเป็นไปได้ของการนำกติกาไปใช้ | ยังต้องตรวจสภาพคล่องและเวลาส่งคำสั่งจริง |
| ประมาณ drift หลายค่า | ดูผลของความไม่แน่นอนด้านผลตอบแทนคาดหวัง | ไม่ได้ทำให้ทราบค่า drift ในอนาคต |

การเปลี่ยนความถี่ควรเปรียบเทียบอย่างระมัดระวัง หากอยากแยกผลของการปรับพอร์ตอย่างเดียว สามารถจำลองราคาในกริดละเอียดชุดเดียว แล้วให้กลยุทธ์แต่ละตัวเลือกจุดซื้อขายของตน แทนการสุ่มคนละชุดทุกครั้ง ผลต่างจึงตีความได้ง่ายขึ้น

### พารามิเตอร์อาจเปลี่ยนตามเวลา

constant-parameter GBM ใช้ $\mu$ และ $\sigma$ เดิมทุกงวด จึงไม่สร้างช่วง volatility สูงต่อเนื่องจากกลไกของตัวมันเอง วิดีโอ [Monte Carlo Simulation](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/9Yj1e/monte-carlo-simulation) ขยายไปถึงดอกเบี้ย ความผันผวน และ risk premium ที่เปลี่ยนตามเวลา

เริ่มทดลองได้ด้วย scenario ง่าย ๆ: กำหนดเองให้ volatility ของครึ่งแรกกับครึ่งหลังต่างกัน ช่วงจำลองของเรามีสามปี จึงให้ครึ่งแรก 30% และครึ่งหลัง 45% โดยคงค่า $\mu$ เดิม นี่เป็น **สมมติฐานช่วงเครียดที่กำหนดไว้ล่วงหน้า** ไม่ใช่แบบจำลองที่เรียนรู้ว่าเมื่อไรตลาดจะเปลี่ยน regime

```python
mc_sigma_by_step = np.full(mc_steps, 0.30)
mc_sigma_by_step[mc_steps // 2:] = 0.45
mc_stress_log_returns = (
    (mc_mu - 0.5 * mc_sigma_by_step[:, None]**2) * mc_dt
    + mc_sigma_by_step[:, None] * np.sqrt(mc_dt) * mc_z
)
mc_stress_returns = np.expm1(mc_stress_log_returns)
mc_stress_wealth = cppi_many_paths(mc_stress_returns)
mc_stress_summary = shortfall_summary(mc_stress_wealth, mc_floor)
print(pd.DataFrame({"Constant volatility": mc_summary, "Higher volatility later": mc_stress_summary}).round(4))
```

`//` คือการหารเอาจำนวนเต็ม จึงเริ่มเปลี่ยนที่แถว 6 ของผลตอบแทน 12 แถว `[:, None]` เปลี่ยน array ที่มีค่า volatility 12 ตัวให้เป็น 12 แถวหนึ่งคอลัมน์ เพื่อให้ NumPy ขยายค่าแต่ละงวดไปใช้กับ 20,000 เส้นทางได้ เราใช้ `mc_z` เดิมเพื่อให้แรงสุ่มมาตรฐานตรงกันขณะเปลี่ยนขนาดความผันผวน

ถ้าต้องการให้ variance หรืออัตราดอกเบี้ยเป็นกระบวนการสุ่มด้วย ต้องกำหนดสมการ พารามิเตอร์ ความสัมพันธ์ของ shocks และวิธีจำลองเพิ่ม การใช้ Normal สุ่มทุกอย่างอาจสร้างอัตราหรือ variance ที่ไม่เข้ากับแบบจำลองที่ตั้งใจ ส่วนการตั้ง $\mu=r+\lambda\sigma$ ก็ต้องแยกว่า $r$ คืออัตราปลอดภัยใน convention ใด และ $\lambda$ เป็นพารามิเตอร์ risk premium ต่อความเสี่ยง ไม่ใช่ค่าที่รู้แน่นอนของตลาด

### ทดลองด้วย Slider ภายหลังได้

`lab_122` แนะนำ ipywidgets และ `lab_123` ใช้ตัวควบคุมปรับพารามิเตอร์ของการจำลอง การเลื่อน slider เป็นวิธีเปลี่ยน argument แล้วเรียกฟังก์ชันใหม่ เมื่อเข้าใจฟังก์ชันแล้วจึงเพิ่มส่วนติดต่อได้ตาม [คู่มือติดตั้ง ipywidgets](https://ipywidgets.readthedocs.io/en/stable/user_install.html) ในสภาพแวดล้อม Notebook ที่ใช้อยู่ หากเปลี่ยนพารามิเตอร์แล้วสุ่มใหม่ทุกครั้ง กราฟที่ต่างจะรวมทั้งผลของพารามิเตอร์และ noise จากตัวอย่างใหม่ จึงควรมีตัวเลือกคง seed สำหรับการเปรียบเทียบ

<span id="monte-carlo-practice"></span>

## แบบฝึกหัด: ตรวจโมเดลและหน่วยก่อนอ่านผล

โจทย์ต่อไปนี้สร้างขึ้นใหม่จากแนวคิดในบท

**1.** annual volatility 24% ถ้าจำลองรายเดือน SD ของส่วนสุ่มใน log return ต่อเดือนเป็นเท่าไร?

<details><summary>เปิดคำตอบข้อ 1</summary>

$0.24\sqrt{1/12}\approx0.069282$ หรือ 6.9282% ใช้รากที่สองของเวลา เพราะ variance ของ Brownian increment สะสมตามเวลา

</details>

**2.** หาก array ผลตอบแทนมี shape `(60, 5000)` และหนึ่งแถวแทนหนึ่งเดือน หมายถึงกี่ปีและกี่เส้นทาง? ราคาที่รวมจุดเริ่มต้นควรมี shape เท่าไร?

<details><summary>เปิดคำตอบข้อ 2</summary>

60 เดือนคือห้าปี มี 5,000 เส้นทาง ราคาต้องมี shape `(61, 5000)` การสะสมตามเวลาใช้ `axis=0`

</details>

**3.** พอร์ตจบต่ำกว่า floor 20 เส้นทางจาก 10,000 เส้นทาง และเฉลี่ยขาด 5 บาทเฉพาะกลุ่มที่ขาด mean shortfall ทุกเส้นทางเป็นเท่าไร?

<details><summary>เปิดคำตอบข้อ 3</summary>

สัดส่วนขาดคือ $20/10{,}000=0.002$ หรือ 0.2% เมื่ออีก 9,980 เส้นทางมี shortfall เป็นศูนย์ ค่าเฉลี่ยทุกเส้นทางจึงเป็น $0.002\times5=0.01$ บาท

</details>

**4.** ถ้าตั้ง $\mu=0$ ใน exact GBM ราคาปลายทางทุกเส้นทางต้องกลับมาเท่าราคาเริ่มต้นหรือไม่?

<details><summary>เปิดคำตอบข้อ 4</summary>

ไม่จำเป็น ค่าคาดหมายของราคาคือ $S_0$ แต่แต่ละเส้นทางยังขึ้นลง และมัธยฐานเป็น $S_0e^{-\sigma^2T/2}$ ซึ่งต่ำกว่า $S_0$ เมื่อ $\sigma>0$ และ $T>0$ ค่าเฉลี่ยไม่ใช่ข้อบังคับของแต่ละเส้นทาง

</details>

**5.** เพิ่มจำนวนเส้นทางสิบเท่าแล้ว shortfall probability ดูนิ่งมาก สามารถสรุปได้หรือไม่ว่าแบบจำลองมี crash risk ครบถ้วน?

<details><summary>เปิดคำตอบข้อ 5</summary>

ไม่ได้ ความนิ่งบอกว่าการประมาณภายในแบบจำลองมี sampling error ลดลง แต่หากกติกาสุ่มไม่มี jumps หรือเลือก volatility ต่ำเกินจริง เส้นทางเพิ่มก็ยังมาจากสมมติฐานเดิม ต้องทดสอบ model error ด้วยข้อมูลหรือแบบจำลองอื่นแยกต่างหาก

</details>

<span id="monte-carlo-sources"></span>

## แหล่งประกอบบท

อ่านแนวคิดของคอร์สได้ที่ [Simulating asset returns with random walks](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/7sy60/simulating-asset-returns-with-random-walks), [Monte Carlo Simulation](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/9Yj1e/monte-carlo-simulation) และ [Lab Random Walks and Monte Carlo](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/D4ZCu/lab-session-random-walks-and-monte-carlo) ประกอบกับ `lab_121`, `lab_122`, `lab_123` และ toolkit ที่มากับคอร์ส โค้ดและการทดลองในหน้านี้เขียนใหม่ โดยเลือก exact GBM เพื่อแยกแบบจำลองออกจาก Euler approximation ให้ชัดเจน

สำหรับคณิตศาสตร์ของ Brownian motion และ GBM ดู [เอกสารการสอนของ Karl Sigman](https://www.columbia.edu/~ks20/4703-Sigman/Monte-Carlo-Sigman.html) เมื่อต้องนำ simulation ไปศึกษาการลงทุนจริง ให้บันทึกหน่วยเวลา seed เวอร์ชันเครื่องมือ วิธีจัดการข้อมูล และสมมติฐานสินทรัพย์รองรับ floor พร้อมผลลัพธ์ เพื่อให้ผู้อื่นทำซ้ำและตรวจความหมายของตัวเลขได้
