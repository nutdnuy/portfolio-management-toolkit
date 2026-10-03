---
title: ความเสี่ยงที่เปลี่ยนตามเวลา: EWMA และ GARCH
description: เรียน conditional variance จากศูนย์ เปรียบเทียบ Rolling กับ EWMA คำนวณ GARCH ทีละวัน และแยกการอัปเดตเมื่อเห็นข้อมูลออกจากการพยากรณ์หลายวัน
---

# ความเสี่ยงที่เปลี่ยนตามเวลา: EWMA และ GARCH

<p class="lead">ถ้าเมื่อวานตลาดแกว่งแรงกว่าช่วงหลายเดือนที่ผ่านมา เราควรให้น้ำหนักกับเหตุการณ์นั้นเท่าไรในการประเมินความเสี่ยงวันพรุ่งนี้?</p>

เมื่อคงน้ำหนักพอร์ตไว้ การใช้ covariance ชุดเดิมทำให้ค่าความเสี่ยงที่คำนวณได้คงเดิมด้วย แต่ข้อมูลที่เรารู้เปลี่ยนไปหลังผลตอบแทนแต่ละงวด เราจะคำนวณค่าความเสี่ยงใหม่ตามข้อมูลที่เข้ามา โดยแยกเวลาที่เห็นผลตอบแทนออกจากเวลาที่ใช้ค่าพยากรณ์

เนื้อหาต่อจากการประมาณ covariance ในคอร์ส Advanced Portfolio Construction and Analysis with Python เราเริ่มจากสินทรัพย์เดียวเพื่ออ่านสูตรให้คล่อง แล้วขยายไปยัง covariance ของพอร์ต ตัวอย่างทั้งหมดเป็นข้อมูลสมมติและการจำลองที่ตั้งพารามิเตอร์ไว้ล่วงหน้า ไม่ได้ประมาณพารามิเตอร์จากตลาดจริง โค้ดใช้ NumPy และ pandas เปิด Notebook ใหม่แล้วรันทุกช่องตามลำดับได้

| ช่วงเรียน | สิ่งที่จะคำนวณ |
|---|---|
| [Conditional variance](#conditional-variance) | แยกความเสี่ยงเมื่อรู้ข้อมูลวันนี้ออกจากความเสี่ยงโดยเฉลี่ย |
| [Rolling และ Expanding](#rolling-and-expanding) | ติดตามผลของวันที่แกว่งแรงเมื่อเลื่อนหน้าต่างข้อมูล |
| [EWMA](#ewma-recursion) | อัปเดต variance และตรวจน้ำหนักของข้อมูลกับค่าเริ่มต้น |
| [Covariance ตามเวลา](#ewma-covariance) | อัปเดตเมทริกซ์ที่ยังใช้คำนวณความเสี่ยงพอร์ตได้ |
| [ARCH และ GARCH](#arch-and-garch) | เพิ่มระดับ variance ระยะยาวและติดตามผลของ shock |
| [พยากรณ์หลายวัน](#multi-step-forecast) | เฉลี่ยความไม่แน่นอนของ shock ที่ยังไม่เกิด |
| [Factor GARCH](#factor-garch) | ใช้ความเสี่ยงของปัจจัยร่วมสร้าง covariance ของหลายสินทรัพย์ |

<span id="conditional-variance"></span>

## Conditional variance คือความเสี่ยงเมื่อกำหนดชุดข้อมูลที่รู้แล้ว

ให้ $r_t$ เป็นผลตอบแทนในวันที่ $t$ และ $\mathcal F_{t-1}$ เป็นข้อมูลทั้งหมดที่เราใช้ได้ก่อนวันนั้น เช่น ผลตอบแทนจนถึงวันก่อนหน้า เราแยกผลตอบแทนเป็นค่าเฉลี่ยที่คาดไว้กับส่วนที่ผิดจากคาด:

$$
r_t=\mu_t+\varepsilon_t,\qquad
\mu_t=E[r_t\mid\mathcal F_{t-1}].
$$

เครื่องหมาย $E[\cdot\mid\mathcal F_{t-1}]$ หมายถึงค่าเฉลี่ยภายใต้ข้อมูลที่รู้แล้ว ส่วน $\varepsilon_t$ เรียกว่า innovation หรือ residual ในตัวอย่างแบบจำลองนี้ เมื่อจบวันจึงคำนวณมันได้จากผลตอบแทนที่เกิดขึ้นลบค่าเฉลี่ยที่กำหนดก่อนวันนั้น

Conditional variance เขียนเป็น

$$
h_t=\operatorname{Var}(r_t\mid\mathcal F_{t-1})
=E[\varepsilon_t^2\mid\mathcal F_{t-1}],
\qquad \sigma_t=\sqrt{h_t}.
$$

$h_t$ มีหน่วยเป็นผลตอบแทนยกกำลังสอง ส่วน $\sigma_t$ หรือ [conditional SD](glossary.html#conditional-volatility) กลับมาอยู่ในหน่วยผลตอบแทน ตัวอย่างเช่น SD รายวัน 1% เขียนเป็น 0.01 และมี variance $0.01^2=0.0001$ เราจะเก็บผลตอบแทนเป็นทศนิยมใน Python ทุกช่อง และคูณ 100 เฉพาะตอนแสดง SD เป็นเปอร์เซ็นต์

Unconditional variance มองการกระจายโดยไม่กำหนดข้อมูลเฉพาะของวันนี้ สมมติว่ามีสองสภาวะที่มีโอกาสอย่างละครึ่ง ทั้งสองสภาวะมี mean ผลตอบแทนศูนย์ แต่มี SD รายวัน 1% กับ 3% ถ้ารู้สภาวะจะใช้ SD ตามสภาวะนั้น หากไม่รู้สภาวะ variance รวมเท่ากับค่าเฉลี่ยของ variance ทั้งสอง คือ $0.5(0.01^2)+0.5(0.03^2)=0.0005$ จึงมี SD ประมาณ 2.2361% ไม่ใช่ค่าเฉลี่ยของ SD ที่เท่ากับ 2%

### เหตุที่ต้องระบุค่าเฉลี่ยก่อนยกกำลังสอง

เราใช้ $\varepsilon_t^2$ เพราะ variance วัดการเบี่ยงจากค่าเฉลี่ย การใช้ $r_t^2$ ตรง ๆ อาศัยสมมติฐานว่า mean ที่ใช้ในแบบจำลองเป็นศูนย์ ถ้า mean ไม่เป็นศูนย์ second moment จะรวมกำลังสองของ mean เข้าไปด้วย:

$$
E[r_t^2]=\operatorname{Var}(r_t)+(E[r_t])^2.
$$

```python
import numpy as np
import pandas as pd

state_sd = np.array([0.01, 0.03])
state_probabilities = np.array([0.5, 0.5])
unconditional_variance = float(state_probabilities @ (state_sd**2))
mean_example = np.array([0.01, 0.02, 0.03])
print("Conditional SDs (%):", state_sd * 100)
print("Unconditional variance:", unconditional_variance)
print("Unconditional SD (%):", round(100 * np.sqrt(unconditional_variance), 6))
print("Raw second moment:", round(np.mean(mean_example**2), 8))
print("Centered variance, divisor n:", round(np.var(mean_example, ddof=0), 8))
```

ผลลัพธ์ให้ unconditional variance 0.0005 และ SD 2.236068% ส่วนข้อมูลตัวอย่าง 1%, 2%, 3% มีค่าเฉลี่ย 2% ค่าเฉลี่ยของกำลังสองเท่ากับ 0.00046667 แต่ variance ที่ลบค่าเฉลี่ยและหารด้วย $n$ เท่ากับ 0.00006667 ส่วนต่าง 0.0004 คือ $0.02^2$

`np.array` เก็บตัวเลขหลายค่าเป็นเวกเตอร์ `@` ในตัวอย่างแรกคำนวณผลรวมของความน่าจะเป็นคูณ variance แต่ละสภาวะ ส่วน `np.var(..., ddof=0)` ใช้ตัวหาร $n$ เพื่อแสดงเอกลักษณ์ข้างต้นให้ตรงกัน หากประมาณ mean จาก sample แล้วใช้ sample variance แบบตัวหาร $n-1$ ต้องกำหนด `ddof=1` ซึ่งเป็นอีก convention หนึ่ง

ในตัวอย่างถัดไปเรากำหนด conditional mean เป็นศูนย์ไว้ก่อน แล้วใช้ผลตอบแทนเป็น residual โดยตรง นี่เป็นสมมติฐานของตัวอย่าง ไม่ใช่ข้อสรุปว่าผลตอบแทนจริงมีค่าเฉลี่ยศูนย์ทุกตลาดหรือทุกความถี่ และห้ามหักค่าเฉลี่ยของข้อมูลทั้งช่วงอนาคตเพื่อใช้สร้าง residual ย้อนหลังใน backtest

ความเสี่ยงที่เปลี่ยนตามข้อมูลยังอยู่ร่วมกับ unconditional variance ที่คงที่ได้ แบบจำลอง GARCH ช่วงหลังของบทจะเป็นตัวอย่าง จึงควรแยก conditional variance ที่ขึ้นลงออกจากการเปลี่ยนกฎหรือพารามิเตอร์ของกระบวนการเอง แนวคิดนี้อยู่ใน [Bollerslev (1986), หน้า 307–310](https://econ.duke.edu/~boller/Published_Papers/joe_86.pdf) หากพูดว่า volatility เปลี่ยนแล้วจึงต้องเป็นกระบวนการ nonstationary เสมอ จะรวมสองเรื่องนี้เข้าด้วยกัน

<span id="rolling-and-expanding"></span>

## Expanding เก็บข้อมูลเพิ่ม ส่วน Rolling ตัดข้อมูลเก่าออก

Expanding window ใช้ข้อมูลตั้งแต่จุดเริ่มต้นถึงวันนี้ จำนวนข้อมูลจึงเพิ่มตามเวลา ส่วน rolling window เก็บย้อนหลังจำนวนคงที่ เช่น 60 วัน ทุกครั้งที่เพิ่มวันใหม่ก็เอาวันเก่าสุดออก

เมื่อกำหนด mean ศูนย์ ค่าเฉลี่ยของ residual ยกกำลังสองสำหรับสองวิธีคือ

$$
\widehat h_{t+1}^{\mathrm{expanding}}
=\frac1t\sum_{s=1}^{t}\varepsilon_s^2,
\qquad
\widehat h_{t+1}^{\mathrm{rolling}}
=\frac1L\sum_{s=t-L+1}^{t}\varepsilon_s^2.
$$

$L$ คือจำนวนวันย้อนหลัง เราใช้ตัวห้อย $t+1$ เพื่อบอกว่าค่านี้คำนวณเมื่อจบวัน $t$ แล้วนำไปเป็นค่าประเมินของวันถัดไป ไม่ได้รู้ผลตอบแทนวัน $t+1$ มาแล้ว

สร้างข้อมูล 18 วัน ส่วนใหญ่มี residual ขนาด 1% สลับเครื่องหมาย แต่วันที่ 6 มี +5% ใช้ rolling เพียง 5 วันเพื่อให้เห็นจังหวะที่วันที่ 6 เข้าและออกจากหน้าต่าง ข้อมูลตั้งขึ้นนี้ใช้ตรวจสูตร ไม่ใช่รูปแบบที่อ้างว่าเกิดขึ้นในตลาด

```python
residuals = pd.Series(
    [0.01, -0.01, 0.01, -0.01, 0.01, 0.05,
     0.01, -0.01, 0.01, -0.01, 0.01, -0.01,
     0.01, -0.01, 0.01, -0.01, 0.01, -0.01],
    index=pd.RangeIndex(1, 19, name="Day"), name="Residual"
)
squared_residuals = residuals**2
expanding_after = squared_residuals.expanding(min_periods=1).mean()
rolling_after = squared_residuals.rolling(5, min_periods=5).mean()
window_table = pd.DataFrame({
    "Residual (%)": 100 * residuals,
    "Expanding next-day SD (%)": 100 * np.sqrt(expanding_after),
    "Rolling next-day SD (%)": 100 * np.sqrt(rolling_after)
})
print(window_table.loc[[5, 6, 10, 11]].round(6))
```

| หลังเห็นข้อมูลถึงวัน | Residual วันนี้ | Expanding SD สำหรับวันถัดไป | Rolling 5 วัน SD สำหรับวันถัดไป |
|---|---:|---:|---:|
| 5 | +1% | 1.000000% | 1.000000% |
| 6 | +5% | 2.236068% | 2.408319% |
| 10 | −1% | 1.843909% | 2.408319% |
| 11 | +1% | 1.783765% | 1.000000% |

`residuals**2` ยกกำลังสองทุกแถว `expanding().mean()` เฉลี่ยตั้งแต่แถวแรกจนถึงแถวปัจจุบัน ส่วน `rolling(5, min_periods=5)` รอจนมีครบห้าแถวแล้วจึงให้ผล ก่อนหน้านั้นเป็น `NaN` ซึ่งหมายถึงยังไม่พร้อมคำนวณตามเงื่อนไข ไม่ใช่ความเสี่ยงศูนย์

หลังวันที่ 6 ค่าเฉลี่ยกำลังสองใน rolling คือ $(4\times0.01^2+0.05^2)/5=0.00058$ ค่านี้คงอยู่จนถึงหลังวันที่ 10 เพราะวันที่แกว่งแรงยังมีน้ำหนัก $1/5$ เท่าเดิม พอเลื่อนไปหลังวันที่ 11 วันที่ 6 ถูกตัดออกทันที SD จึงกลับเป็น 1% แม้ข้อมูลใหม่ของวันที่ 11 ไม่ได้ผิดปกติจากวันก่อน

การใช้หน้าต่างสั้นตอบสนองข้อมูลใหม่เร็วขึ้นแต่เหลือ observations น้อยลง ส่วนข้อมูลยาวช่วยลดความแกว่งจากการสุ่มบางส่วน แต่ผสมช่วงที่อาจมีระดับความเสี่ยงต่างกัน [Portfolio Construction with Time-Varying Risk Parameters](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/D2MAC/portfolio-construction-with-time-varying-risk-parameters) อภิปรายการเลือกข้อมูลที่ใหม่พอสำหรับโจทย์นี้ ไม่มีกฎว่าหน้าต่างสั้นที่สุดหรือ expanding จะเหมาะกว่าทุกกรณี

การเพิ่มความถี่ข้อมูลก็ต้องรักษาความหมายของงวดให้ตรง ข้อมูลรายวัน 252 แถวกับรายเดือน 252 แถวครอบคลุมประวัติคนละระยะ และการเปลี่ยนไปใช้ข้อมูลระหว่างวันยังมีปัญหาราคาซื้อขายไม่พร้อมกันและ market microstructure เพิ่มขึ้น จำนวนแถวที่มากขึ้นไม่ได้รับรองว่าข้อมูลมีสัญญาณเพิ่มในสัดส่วนเดียวกัน

<span id="ewma-recursion"></span>

## EWMA ลดน้ำหนักอดีตลงทีละส่วน

[Exponentially Weighted Moving Average หรือ EWMA](glossary.html#ewma) ใช้ decay factor $\lambda$ ซึ่งในบทนี้อยู่ระหว่าง 0 กับ 1 สูตรอัปเดต variance คือ

$$
h_{t+1}=\lambda h_t+(1-\lambda)\varepsilon_t^2.
$$

ก่อนเริ่มวัน $t$ เรามี $h_t$ หลังจบวันจึงรู้ $\varepsilon_t$ แล้วผสมกำลังสองของมันกับ variance เดิมเพื่อได้ $h_{t+1}$ ค่า $\lambda$ มากทำให้รักษาค่าเดิมไว้มาก ส่วน $1-\lambda$ เป็นน้ำหนักของกำลังสอง residual ที่เพิ่งเห็น สูตรเดียวกันอยู่ใน [เอกสาร EWMAVariance ของ arch](https://arch.readthedocs.io/en/stable/univariate/generated/arch.univariate.EWMAVariance.html)

เริ่มต้นด้วย $h_1=0.0001$ หรือ SD 1% ต่อวัน และใช้ $\lambda=0.90$ เมื่อจบวันที่ 6 ซึ่งมี residual +5% จะได้

$$
h_7=0.90(0.0001)+0.10(0.05^2)=0.00034,
\qquad \sqrt{h_7}\approx1.843909\%.
$$

วันที่มี +5% และ −5% จะส่งผลเท่ากันในสูตรนี้ เพราะถูกยกกำลังสองทั้งคู่ EWMA รูปแบบนี้จึงไม่แยกผลของข่าวดีและข่าวร้ายที่มีขนาดเท่ากัน

```python
def ewma_variance(eps, lam, initial_variance):
    eps = np.asarray(eps, dtype=float)
    if eps.ndim != 1 or not np.isfinite(eps).all():
        raise ValueError("eps must be a finite one-dimensional array")
    if not np.isfinite([lam, initial_variance]).all():
        raise ValueError("Lambda and initial variance must be finite")
    if not 0 < lam < 1 or initial_variance <= 0:
        raise ValueError("Use 0 < lam < 1 and positive initial variance")
    h = np.empty(len(eps) + 1)
    h[0] = initial_variance
    for t, shock in enumerate(eps):
        h[t + 1] = lam * h[t] + (1 - lam) * shock**2
    return h

lam = 0.90
initial_variance = 0.01**2
ewma_h = ewma_variance(residuals, lam, initial_variance)
ewma_table = pd.DataFrame({
    "Before observing day SD (%)": 100 * np.sqrt(ewma_h[:-1]),
    "After observing day: next-day SD (%)": 100 * np.sqrt(ewma_h[1:])
}, index=residuals.index)
print(ewma_table.loc[[5, 6, 7, 10, 11]].round(6))
assert np.isclose(ewma_h[6], 0.00034)
```

| วัน $t$ | SD ก่อนเห็นผลตอบแทนวันนั้น | SD ที่อัปเดตให้วันถัดไป |
|---|---:|---:|
| 5 | 1.000000% | 1.000000% |
| 6 | 1.000000% | 1.843909% |
| 7 | 1.843909% | 1.777639% |
| 10 | 1.658192% | 1.604568% |
| 11 | 1.604568% | 1.554727% |

`ewma_variance` รับ residual ทั้งชุด ค่า $\lambda$ และ variance เริ่มต้น ฟังก์ชันตรวจว่าข้อมูลเป็นตัวเลขที่มีค่าจำกัดก่อนคำนวณ `np.empty(len(eps) + 1)` จองพื้นที่เพิ่มหนึ่งตำแหน่งสำหรับค่าเริ่มต้น ส่วน `enumerate(eps)` คืนทั้งตำแหน่งและ residual ทีละค่า

ในโค้ด `h[0]` คือ $h_1$ ก่อนเห็นข้อมูลวันแรก และ `h[6]` คือ $h_7$ หลังเห็นข้อมูลวันที่ 6 แล้ว ตารางใช้ `h[:-1]` สำหรับค่าก่อนเห็นวันนั้น และ `h[1:]` สำหรับค่าที่อัปเดตแล้ว การเก็บทั้งสองชุดช่วยตรวจว่าค่าพยากรณ์เข้ามาก่อนผลตอบแทนที่ต้องการประเมิน

หลัง shock วันที่ 6 ข้อมูลวันที่ 7 เป็นต้นไปยังมี residual ขนาด 1% ตามเส้นทางที่เรากำหนด EWMA จึงค่อย ๆ ลดลง แต่ไม่กระโดดเมื่อวันที่ 6 มีอายุเกินห้าวัน เหตุที่ลดในตารางคือเราได้รับข้อมูลใหม่ที่แกว่งน้อยลงจริงในตัวอย่างนี้ การยังไม่รู้ข้อมูลอนาคตเป็นอีกกรณีหนึ่งที่จะคำนวณแยกในหัวข้อพยากรณ์หลายวัน

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/advanced-risk-window-mobile.svg">
<img src="assets/charts/advanced-risk-window.svg" alt="ข้อมูลสมมติแสดง Rolling 5 วันลดลงทันทีหลังวันที่ 11 ส่วน EWMA ค่อย ๆ ลดตามข้อมูลใหม่หลัง shock วันที่ 6" loading="lazy" width="720" height="560">
</picture>
<figcaption>แต่ละจุดใช้ข้อมูลถึงวันที่บนแกนนอน เพื่อประเมิน SD ของวันถัดไป เส้นเชื่อมจุดรายวันจากตัวอย่างเดียวกับโค้ด วันที่ 11 ไม่มี shock ใหม่ แต่ข้อมูลวันที่ 6 หลุดจากหน้าต่าง Rolling แล้ว</figcaption>
</figure>

<span id="finite-ewma-weights"></span>

## น้ำหนักของข้อมูลจำนวนจำกัดกับค่าเริ่มต้น

เมื่อขยาย recursion หลังเห็นข้อมูล $n$ วัน เราได้

$$
h_{n+1}=\lambda^n h_1
+(1-\lambda)\sum_{j=0}^{n-1}\lambda^j\varepsilon_{n-j}^2.
$$

$j=0$ หมายถึงข้อมูลล่าสุด ข้อมูลย้อนหลังหนึ่งวันมีน้ำหนักลดลงด้วยตัวคูณ $\lambda$ และลดอีกหนึ่งครั้งทุกครั้งที่เก่าขึ้น น้ำหนักที่ให้ observations รวมกันเท่ากับ $1-\lambda^n$ ส่วนที่เหลือ $\lambda^n$ ยังอยู่ที่ค่าเริ่มต้น $h_1$ ทั้งสองส่วนรวมกันได้หนึ่ง

เมื่อขยายประวัติให้ยาวขึ้น น้ำหนักของค่าเริ่มต้นจะเข้าใกล้ศูนย์ สำหรับประวัติที่ยาวไม่สิ้นสุดและผลรวมที่ลู่เข้า จึงเขียนในรูป

$$
h_{t+1}=(1-\lambda)\sum_{j=0}^{\infty}\lambda^j\varepsilon_{t-j}^2,
\qquad (1-\lambda)\sum_{j=0}^{\infty}\lambda^j=1.
$$

ในข้อมูลจริงที่มีจำนวนจำกัด เราใช้ค่าเริ่มต้นหรือปรับน้ำหนักตามวิธีที่ระบุ แทนการสมมติว่าข้อมูลที่ยังไม่มีให้ variance เป็นศูนย์

อีกวิธีคือมีข้อมูลเพียง $n$ ค่า แล้วปรับน้ำหนักของข้อมูลเหล่านั้นให้รวมหนึ่งโดยไม่ใส่ค่าเริ่มต้น:

$$
a_j=\frac{\lambda^j}{\sum_{k=0}^{n-1}\lambda^k},
\qquad
\widehat h^{\mathrm{finite}}=\sum_{j=0}^{n-1}a_j\varepsilon_{n-j}^2.
$$

ทั้งสองสูตรใช้การลดน้ำหนักตามอายุ แต่ดูแลช่วงเริ่มต้นต่างกัน สำหรับข้อมูลสั้นจึงให้ตัวเลขต่างกันได้ หากเขียนโปรแกรมต้องระบุว่าใช้สูตรใด

```python
n_seen = 6
ages = np.arange(n_seen)
recent_first = residuals.iloc[:n_seen].to_numpy()[::-1]
raw_weights = (1 - lam) * lam**ages
initial_weight = lam**n_seen
recursive_expansion = initial_weight * initial_variance + raw_weights @ (recent_first**2)
finite_weights = lam**ages / np.sum(lam**ages)
finite_variance = float(finite_weights @ (recent_first**2))
assert np.isclose(raw_weights.sum() + initial_weight, 1)
assert np.isclose(recursive_expansion, ewma_h[n_seen])
print("Raw observation weight sum:", round(raw_weights.sum(), 6))
print("Initial-state weight:", round(initial_weight, 6))
print("Recursive variance:", round(recursive_expansion, 8))
print("Normalized finite-sample variance:", round(finite_variance, 8))
print("Equal weights when finite lambda=1:", np.ones(n_seen) / n_seen)
```

เมื่อมีข้อมูลหกวันและ $\lambda=0.90$ น้ำหนัก observations รวม 0.468559 และน้ำหนักค่าเริ่มต้นยังเหลือ 0.531441 สูตร recursive ให้ variance 0.00034000 ตามเดิม แต่สูตร finite ที่ปรับน้ำหนักข้อมูลให้รวมหนึ่งให้ประมาณ 0.00061221 เพราะกำลังสอง residual ของวันที่ 6 ได้สัดส่วนมากขึ้นในกลุ่มข้อมูลที่มีเพียงหกวัน

`np.arange(n_seen)` สร้างอายุ 0, 1, 2, 3, 4, 5 ส่วน `[::-1]` กลับลำดับ residual ให้ข้อมูลล่าสุดอยู่ก่อน จึงจับคู่กับอายุศูนย์ได้ตรงกัน `raw_weights` เก็บน้ำหนัก observations จาก recursion และ `finite_weights` เก็บน้ำหนักที่หารปรับให้รวมหนึ่งแล้ว

สำหรับสูตร finite เมื่อ $\lambda=1$ ทุกพจน์ $\lambda^j$ เท่ากับหนึ่ง จึงได้ equal weight ตัวละ $1/n$ แต่ถ้าแทน $\lambda=1$ ลงใน recursion จะได้ $h_{t+1}=h_t$ และหยุดรับข้อมูลใหม่ ข้อความว่า “lambda เท่ากับหนึ่งคือ equal weight” จึงต้องอ่านพร้อมสูตรที่ใช้ บท [Exponentially weighted average](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/c4t09/exponentially-weighted-average) เริ่มจากแนวคิด weighted average ของข้อมูล ส่วนตัวอย่างฟังก์ชันของเราเลือก recursion พร้อมค่าเริ่มต้นชัดเจน

<span id="ewma-half-life"></span>

## Half-life บอกอัตราที่น้ำหนักเก่าลดลง

ถ้าข้อมูลมีน้ำหนักวันนี้เท่ากับ $a$ หลังผ่านไป $k$ observations น้ำหนักเดิมจะเหลือ $a\lambda^k$ เวลาที่น้ำหนักลดครึ่งหนึ่งจึงแก้จาก $\lambda^k=0.5$:

$$
k_{1/2}=\frac{\ln(0.5)}{\ln(\lambda)}.
$$

หน่วยเป็นจำนวน observations หากข้อมูลรายวันจึงอ่านเป็นจำนวนวันซื้อขาย หากเปลี่ยนเป็นรายเดือนค่าเดียวกันจะหมายถึงจำนวนเดือน ไม่ใช่ระยะเวลาเดิม

```python
lambda_choices = np.array([0.70, 0.90, 0.94, 0.97])
half_lives = np.log(0.5) / np.log(lambda_choices)
print(pd.DataFrame({"Lambda": lambda_choices, "Half-life (observations)": half_lives}).round(6))
initial_high = 0.02**2
h_high_start = ewma_variance(residuals, lam, initial_high)
initialization_gap = h_high_start - ewma_h
expected_gap = (initial_high - initial_variance) * lam**np.arange(len(ewma_h))
assert np.allclose(initialization_gap, expected_gap)
print("Variance gap after 10 observations:", round(initialization_gap[10], 8))
```

| $\lambda$ | Half-life ของน้ำหนัก (observations) |
|---:|---:|
| 0.70 | 1.943358 |
| 0.90 | 6.578813 |
| 0.94 | 11.202306 |
| 0.97 | 22.756573 |

Half-life เป็นจำนวนทศนิยมได้ เป็นวิธีบอกความเร็วของการลดน้ำหนัก ไม่ใช่คำสั่งให้เลือกหน้าต่างที่มีจำนวนแถวเท่าค่านี้ ข้อมูลที่เก่ากว่า half-life ยังมีน้ำหนักเหลืออยู่

ส่วนท้ายโค้ดลองเริ่ม variance ที่ $0.02^2$ แทน $0.01^2$ แล้วป้อน residual ชุดเดียวกัน ผลต่างของค่าที่ได้หลัง $n$ วันเท่ากับ $(0.02^2-0.01^2)\lambda^n$ หลังสิบ observations จึงยังต่างกันประมาณ 0.00010460 การตั้งต้นจึงมีผลต่อช่วงแรก โดยเฉพาะเมื่อ $\lambda$ ใกล้หนึ่ง

ในการใช้งานจริงอาจตั้งต้นจากข้อมูลก่อนช่วงประเมินผล หรือใช้กฎ backcast ที่ระบุไว้ ต้องไม่ใช้ข้อมูลทดสอบในอนาคตมาช่วยตั้งค่าพยากรณ์ย้อนหลังโดยไม่เปิดเผย ส่วนการเลือก $\lambda$ ควรใช้ช่วงฝึกหรือ validation ตามโจทย์และหน่วยเวลาเดียวกัน ไม่ควรเลือกจากผลที่ดีที่สุดในช่วงทดสอบสุดท้ายแล้วรายงานเหมือนไม่เคยเห็นข้อมูลนั้น

[RiskMetrics Technical Document ฉบับ 1996, Table 5.9 หน้าเอกสาร 100](https://www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7e95a#page=112) บันทึกค่า 0.94 สำหรับการพยากรณ์หนึ่งวัน และ 0.97 สำหรับชุดพยากรณ์หนึ่งเดือน โดยทั้งคู่ใช้ observations รายวันในการผลิตข้อมูล ตัวเลขนี้เป็น convention ในบริบทนั้น ไม่ได้กำหนดค่าเหมาะสมตายตัวสำหรับทุกสินทรัพย์

<span id="ewma-covariance"></span>

## อัปเดตทั้ง Covariance โดยใช้ Outer Product

สำหรับหลายสินทรัพย์ ให้ $\varepsilon_t$ เป็นเวกเตอร์ residual และ $\Sigma_t$ เป็น covariance ที่ใช้ก่อนรับผลตอบแทนวัน $t$ สูตร EWMA ขยายเป็น

$$
\Sigma_{t+1}=\lambda\Sigma_t+(1-\lambda)\varepsilon_t\varepsilon_t^\mathsf{T}.
$$

$\varepsilon_t\varepsilon_t^\mathsf{T}$ เรียกว่า outer product สำหรับสองสินทรัพย์จะได้เมทริกซ์ที่มี residual ยกกำลังสองบนแนวทแยง และผลคูณ residual ของทั้งคู่ในตำแหน่ง covariance ถ้าทั้งคู่ติดลบ ผลคูณยังเป็นบวก จึงสะท้อนว่าทั้งคู่เคลื่อนไปทางเดียวกันในวันนั้น

ใช้ mean ศูนย์ร่วมกันทั้งตัวอย่างและ $\lambda$ ค่าเดียวสำหรับทุกช่อง กำหนด covariance เริ่มต้นให้สินทรัพย์ A มี SD 1%, B มี SD 1.5% และ correlation 0.2 จากนั้นเกิด residual ของ A/B เท่ากับ −5%/−3%

```python
sigma_initial = np.array([[0.000100, 0.000030],
                          [0.000030, 0.000225]])
two_asset_shocks = np.array([[-0.05, -0.03], [0.01, -0.02], [0.00, 0.01]])
covariance_states = [sigma_initial.copy()]
for e in two_asset_shocks:
    updated = lam * covariance_states[-1] + (1 - lam) * np.outer(e, e)
    covariance_states.append(updated)
covariance_states = np.array(covariance_states)
sigma_after_shock = covariance_states[1]
minimum_eigenvalues = np.array([np.linalg.eigvalsh(s).min() for s in covariance_states])
portfolio_weights = np.array([0.60, 0.40])
portfolio_variances = np.array([portfolio_weights @ s @ portfolio_weights for s in covariance_states])
correlation_after_shock = sigma_after_shock[0, 1] / np.sqrt(sigma_after_shock[0, 0] * sigma_after_shock[1, 1])
print("Covariance after first shock:\n", sigma_after_shock)
print("Smallest eigenvalues:", np.round(minimum_eigenvalues, 8))
print("Portfolio SD before / after shock (%):", np.round(100 * np.sqrt(portfolio_variances[:2]), 6))
print("Correlation after shock:", round(correlation_after_shock, 6))
assert np.all(minimum_eigenvalues >= -1e-12)
```

หลัง shock แรกได้

$$
\Sigma_{\mathrm{after}}=
\begin{bmatrix}
0.0003400 & 0.0001770\\
0.0001770 & 0.0002925
\end{bmatrix}.
$$

Correlation ที่อัปเดตเท่ากับประมาณ 0.561269 หากพอร์ตถือ A 60% และ B 40% ความเสี่ยงรายวัน $\sqrt{w^\mathsf{T}\Sigma w}$ เพิ่มจาก 0.929516% เป็น 1.594240% โดยที่น้ำหนักที่ใช้เปรียบเทียบทั้งสองกรณียังเป็นชุดเดิม รายละเอียดสูตรพอร์ตอยู่ใน [บทเริ่มจัดพอร์ต](portfolio-basics.html)

`np.outer(e, e)` คำนวณผลคูณทุกคู่ของสมาชิกเวกเตอร์ `e` ส่วน `np.linalg.eigvalsh` หาค่า eigenvalues ของเมทริกซ์สมมาตร ค่าที่เล็กที่สุดของทุกสถานะในตัวอย่างยังเป็นบวก จึงผ่านการตรวจว่าเมทริกซ์เป็น positive semidefinite หรือ PSD ภายในค่าคลาดเคลื่อนของเครื่อง

เหตุที่สูตรรักษา PSD ได้เมื่อเริ่มจาก PSD คือ สำหรับเวกเตอร์น้ำหนักใด ๆ $w$:

$$
w^\mathsf{T}(\varepsilon_t\varepsilon_t^\mathsf{T})w
=(w^\mathsf{T}\varepsilon_t)^2\geq0.
$$

เมทริกซ์เดิมกับ outer product จึงมี quadratic form ไม่ติดลบทั้งคู่ และการบวกด้วยน้ำหนัก $\lambda$ กับ $1-\lambda$ ที่ไม่ติดลบยังรักษาสมบัตินี้ไว้ ทำให้ variance ของพอร์ตไม่กลายเป็นค่าลบเพราะเมทริกซ์ขัดกันเอง

การรักษาสมบัตินี้อาศัยเวกเตอร์ residual ที่จัดวันและหน่วยตรงกัน หากเลือก $\lambda$ แยกอิสระทุกคู่ หรือใช้ข้อมูลขาดหายคนละชุดแล้วประกอบ covariance ทีละช่อง สูตรข้างบนจะไม่ใช่หลักประกัน PSD ให้โดยอัตโนมัติ [RiskMetrics §5.3.2 หน้าเอกสาร 96–98](https://www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7e95a#page=108) อภิปรายความสอดคล้องของ decay factors กับ covariance matrix ด้วย

PSD ยังไม่ได้หมายความว่าเมทริกซ์กลับด้านได้เสมอ หากมี eigenvalue เป็นศูนย์ เมทริกซ์อาจ singular และปัญหาการประมาณค่าหรือ optimization ยังต้องตรวจต่อ การอัปเดตตามเวลาแก้เรื่องน้ำหนักข้อมูลเก่า แต่ไม่ได้แก้ปัญหาจำนวนสินทรัพย์มากกว่าจำนวนข้อมูลทั้งหมดด้วยตัวมันเอง

<span id="arch-and-garch"></span>

## ARCH และ GARCH เพิ่มโครงสร้างให้ Variance

ARCH ย่อมาจาก Autoregressive Conditional Heteroskedasticity หมายถึงแบบจำลองที่ให้ conditional variance ขึ้นกับกำลังสอง residual ในอดีต เริ่มจาก ARCH(1):

$$
h_{t+1}=\omega+\alpha\varepsilon_t^2.
$$

$\omega$ เป็นค่าฐานที่มีหน่วย variance และ $\alpha$ กำหนดการตอบสนองต่อ shock ล่าสุด เราใช้ $\omega>0$ และ $\alpha\geq0$ เพื่อให้ variance บวก กรณีที่ต้องการ unconditional variance จำกัดของรูปแบบนี้กำหนด $\alpha<1$

[GARCH](glossary.html#garch) ย่อมาจาก Generalized ARCH เพิ่ม variance ที่ใช้ก่อนหน้าลงในสมการด้วย กรณี GARCH(1,1) เป็น

$$
h_{t+1}=\omega+\alpha\varepsilon_t^2+\beta h_t.
$$

เลข 1 สองตัวบอกว่าใช้กำลังสอง residual ย้อนหลังหนึ่งงวดกับ variance ย้อนหลังหนึ่งงวด ในเอกสารต่างแหล่งอาจเรียงความหมาย $p,q$ ของ GARCH ต่างกัน จึงควรอ่านสมการกำกับ สำหรับ (1,1) ไม่มีความกำกวมเรื่องจำนวนงวด

กำหนด $\omega>0$, $\alpha\geq0$, $\beta\geq0$ และ $\alpha+\beta<1$ ในตัวอย่างนี้ เงื่อนไขหลังรองรับ variance ระยะยาวที่จำกัดภายใต้โมเดลที่กำหนดให้ standardized innovations มี mean ศูนย์และ variance หนึ่ง เมื่ออยู่ในภาวะ stationary และมี second moment จะได้

$$
\overline h=E[h_t]=E[\varepsilon_t^2],
\qquad
\overline h=\omega+(\alpha+\beta)\overline h,
\qquad
\overline h=\frac{\omega}{1-\alpha-\beta}.
$$

จึงเขียน $\omega=(1-\alpha-\beta)\overline h$ แล้วมองสมการเป็นการผสม variance ระยะยาว กำลังสอง shock ล่าสุด และ variance เดิมได้ ตามกรอบใน [ARCH and GARCH Models](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/HZZPC/arch-and-garch-models) ส่วนสูตรและเงื่อนไข stationary ดู [Bollerslev (1986), Theorem 1 และหัวข้อ GARCH(1,1)](https://econ.duke.edu/~boller/Published_Papers/joe_86.pdf)

### คำนวณจากพารามิเตอร์ที่กำหนดไว้

เลือก $\omega=0.000002$, $\alpha=0.08$, $\beta=0.90$ จึงมี $\alpha+\beta=0.98$ และ $\overline h=0.0001$ หรือ SD ระยะยาว 1% ต่อวัน ตัวเลขทั้งสามตั้งขึ้นเพื่อสอน ไม่มีการ fit จากข้อมูลตลาด

ก่อน shock วันที่ 6 เรามี $h_6=0.0001$ เมื่อเห็น $\varepsilon_6=0.05$ จึงได้

$$
h_7=0.000002+0.08(0.05^2)+0.90(0.0001)
=0.000292.
$$

```python
def garch_variance(eps, omega, alpha, beta, initial_variance):
    eps = np.asarray(eps, dtype=float)
    if eps.ndim != 1 or not np.isfinite(eps).all():
        raise ValueError("eps must be a finite one-dimensional array")
    if not np.isfinite([omega, alpha, beta, initial_variance]).all():
        raise ValueError("Parameters and initial variance must be finite")
    if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 1:
        raise ValueError("This example requires positive omega, nonnegative alpha/beta and alpha+beta < 1")
    if initial_variance <= 0:
        raise ValueError("initial_variance must be positive")
    h = np.empty(len(eps) + 1)
    h[0] = initial_variance
    for t, shock in enumerate(eps):
        h[t + 1] = omega + alpha * shock**2 + beta * h[t]
    return h

omega, alpha, beta = 0.000002, 0.08, 0.90
persistence = alpha + beta
long_run_variance = omega / (1 - persistence)
garch_h = garch_variance(residuals, omega, alpha, beta, initial_variance)
arch_h = garch_variance(residuals, 0.00008, 0.20, 0.0, initial_variance)
print("Long-run variance:", round(long_run_variance, 8))
print(pd.DataFrame({
    "ARCH next-day SD (%)": 100 * np.sqrt(arch_h[1:]),
    "GARCH next-day SD (%)": 100 * np.sqrt(garch_h[1:])
}, index=residuals.index).loc[[5, 6, 7, 11]].round(6))
assert np.isclose(garch_h[6], 0.000292)
```

| หลังเห็นข้อมูลวัน | ARCH SD สำหรับวันถัดไป | GARCH SD สำหรับวันถัดไป |
|---|---:|---:|
| 5 | 1.000000% | 1.000000% |
| 6 | 2.408319% | 1.708801% |
| 7 | 1.000000% | 1.651666% |
| 11 | 1.000000% | 1.460733% |

ตัวอย่าง ARCH ใช้ $\omega=0.00008$, $\alpha=0.20$, $\beta=0$ และมี variance ระยะยาว 0.0001 เช่นกัน แต่พารามิเตอร์การตอบสนองต่อ shock ต่างจาก GARCH จึงไม่ได้ตั้งใจเปรียบเทียบว่าโมเดลใดแม่นกว่า

ARCH(1) ใช้ shock ล่าสุดเพียงตัวเดียว พอวันถัดมามี residual ขนาด 1% มันกลับเป็น variance 0.0001 ทันที ส่วน GARCH ยังนำค่าที่สูงขึ้นของ $h_t$ เข้ามาในสมการด้วย จึงลดช้ากว่าในเส้นทางนี้ หากต้องการให้ ARCH จำหลายงวดก็เพิ่มกำลังสอง residual หลาย lag ซึ่งต้องประมาณพารามิเตอร์เพิ่ม

`garch_variance` เก็บค่าก่อน/หลังเห็นข้อมูลแบบเดียวกับฟังก์ชัน EWMA โดยตรวจพารามิเตอร์ที่เป็น `NaN` หรือ infinity และตรวจขอบเขตที่ตัวอย่างรองรับ การที่ฟังก์ชันปฏิเสธ $\alpha+\beta\geq1$ หมายถึงเราเลือกสอนกรณี finite long-run variance นี้ ไม่ได้หมายความว่างานวิจัยไม่มีแบบจำลองที่พิจารณาขอบเขตอื่น

รูปแบบมาตรฐานยังตอบสนอง +5% กับ −5% เท่ากัน และการกำหนด variance เพียงสมการเดียวไม่ได้ระบุรูปการกระจายของ innovations ครบ การใช้ Normal, Student's t หรือรูปแบบ asymmetric ต้องตั้งสมมติฐานและตรวจเพิ่ม ดูชนิดโมเดลใน [เอกสาร GARCH ของ arch](https://arch.readthedocs.io/en/stable/univariate/generated/arch.univariate.GARCH.html)

<span id="multi-step-forecast"></span>

## พยากรณ์หลายวันเมื่อยังไม่รู้ Shock ในอนาคต

ตารางที่ผ่านมาอัปเดตหลังเห็นข้อมูลแต่ละวันแล้ว เราจะเปลี่ยนโจทย์เป็นหยุดข้อมูลไว้หลังวันที่ 6 จากจุดนั้นต้องพยากรณ์วันที่ 7, 8 และวันถัดไปโดยยังไม่ได้เห็น residual ของวันเหล่านั้น

หลังวันที่ 6 เรารู้ $h_7=0.000292$ สำหรับ GARCH แต่การหา $h_8$ ยังต้องใช้ $\varepsilon_7^2$ ที่ไม่รู้ สิ่งที่ใช้ได้คือ conditional expectation ภายใต้แบบจำลอง:

$$
E_t[\varepsilon_{t+1}^2]=h_{t+1},
\qquad
E_t[h_{t+2}]=\omega+(\alpha+\beta)h_{t+1}.
$$

ให้ $\phi=\alpha+\beta$ แล้วทำซ้ำได้สูตรสำหรับ horizon $k=1,2,\ldots$:

$$
E_t[h_{t+k}]=\overline h+\phi^{k-1}(h_{t+1}-\overline h).
$$

เมื่อ $k=1$ ยกกำลังศูนย์จึงได้ $h_{t+1}$ ที่รู้แล้ว หาก $0<\phi<1$ ผลต่างจากระดับระยะยาวจะค่อย ๆ ลดลง ถ้า variance เริ่มสูงกว่าระยะยาว เส้น forecast จึงลดลง และถ้าเริ่มต่ำกว่าจะเพิ่มขึ้น นี่เป็นพฤติกรรมของค่าคาดหมายในโมเดล ไม่ได้บังคับให้ variance ที่เกิดจริงในแต่ละวันต้องเคลื่อนเข้าหาระยะยาวเสมอ

สำหรับ EWMA ที่ใช้เป็นโมเดล conditional variance จะมี $\omega=0$, $\alpha=1-\lambda$ และ $\beta=\lambda$ ในเชิงรูปสมการ ผลรวม $\alpha+\beta$ จึงเท่ากับหนึ่ง ไม่มีระดับระยะยาวแบบ finite-variance mean-reverting GARCH ที่เราเพิ่งกำหนด และค่าพยากรณ์ variance จากจุดข้อมูลเดียวกันจะคงที่:

$$
E_t[h_{t+k}^{\mathrm{EWMA}}]=h_{t+1}^{\mathrm{EWMA}}.
$$

การใส่ residual อนาคตเป็นศูนย์ทุกวันจะได้เส้นที่ลดลงด้วย $\lambda$ ทุกงวด แต่นั่นคือสถานการณ์ที่เรากำหนดให้ไม่มี shock เลย ค่าเฉลี่ยของ shock เป็นศูนย์ไม่ได้ทำให้ค่าเฉลี่ยของ shock ยกกำลังสองเป็นศูนย์

```python
def garch_forecast(next_variance, omega, alpha, beta, horizon):
    if not np.isfinite([next_variance, omega, alpha, beta]).all():
        raise ValueError("Forecast inputs must be finite")
    if next_variance <= 0 or omega <= 0 or alpha < 0 or beta < 0:
        raise ValueError("Use positive variances/omega and nonnegative alpha/beta")
    phi = alpha + beta
    if not isinstance(horizon, int) or horizon < 1 or not 0 <= phi < 1:
        raise ValueError("Use a positive integer horizon and 0 <= alpha+beta < 1")
    h_bar = omega / (1 - phi)
    return h_bar + phi**np.arange(horizon) * (next_variance - h_bar)

forecast_horizon = 60
garch_forecast_path = garch_forecast(garch_h[6], omega, alpha, beta, forecast_horizon)
ewma_forecast_path = np.full(forecast_horizon, ewma_h[6])
ewma_zero_shock_path = ewma_h[6] * lam**np.arange(forecast_horizon)
forecast_table = pd.DataFrame({
    "GARCH variance": garch_forecast_path,
    "GARCH SD (%)": 100 * np.sqrt(garch_forecast_path),
    "EWMA expected variance": ewma_forecast_path,
    "EWMA forced-zero variance": ewma_zero_shock_path
}, index=pd.RangeIndex(1, forecast_horizon + 1, name="Horizon"))
print(forecast_table.loc[[1, 5, 20, 60]].round(8).to_string())
print("GARCH persistence half-life:", round(np.log(0.5) / np.log(persistence), 6))
```

| Horizon จากหลังวันที่ 6 | GARCH SD จาก variance forecast | EWMA variance forecast | EWMA variance ถ้าฝืนให้ shock ใหม่เป็นศูนย์ |
|---|---:|---:|---:|
| 1 วัน | 1.708801% | 0.00034000 | 0.00034000 |
| 5 วัน | 1.664616% | 0.00034000 | 0.00022307 |
| 20 วัน | 1.519199% | 0.00034000 | 0.00004593 |
| 60 วัน | 1.258158% | 0.00034000 | 0.00000068 |

`garch_forecast` รับ variance ของวันถัดไปที่รู้แล้วและสร้างค่าเฉลี่ย variance ใน horizons ต่อ ๆ ไป `np.arange(horizon)` เริ่มที่ศูนย์เพื่อให้พจน์แรกตรงกับ horizon 1 ส่วนคอลัมน์ SD คำนวณจาก $\sqrt{E_t[h_{t+k}]}$ ซึ่งสำหรับ horizon มากกว่าหนึ่งไม่จำเป็นต้องเท่ากับ $E_t[\sqrt{h_{t+k}}]$ เพราะการถอดรากเป็นฟังก์ชันไม่เชิงเส้น

ค่า $\phi=0.98$ ให้ half-life ของส่วนต่าง forecast จาก $\overline h$ ประมาณ 34.309618 งวด การลดความต่างครึ่งหนึ่งนี้เป็นคนละค่ากับ half-life 6.578813 ของน้ำหนัก EWMA ที่ใช้ $\lambda=0.90$ เราไม่ได้แทน $\beta$ หรือ $\lambda$ ลงแทน persistence ของ GARCH โดยตรง

เอกสาร [arch: Analytical Forecasts](https://arch.readthedocs.io/en/stable/univariate/forecasting.html#analytical-forecasts) อธิบายการใช้ค่าเฉลี่ยของ squared innovations ใน forecast หลายงวดด้วยรูปสมการเดียวกัน ตัวอย่างที่นี่เขียน recursion เองเพื่อให้ตรวจลำดับเวลาได้โดยไม่ต้องติดตั้ง package `arch`

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/advanced-risk-forecast-mobile.svg">
<img src="assets/charts/advanced-risk-forecast.svg" alt="พยากรณ์จากหลังวันที่ 6: รากของ variance ที่คาดใน GARCH ค่อย ๆ เข้าใกล้ 1% ส่วน EWMA คงที่ที่ประมาณ 1.84%" loading="lazy" width="720" height="560">
</picture>
<figcaption>ทุก horizon ใช้ข้อมูลถึงวันที่ 6 เท่ากัน ไม่ได้รับข้อมูลใหม่ระหว่างเส้น กราฟแสดงรากของ variance ที่คาดภายใต้พารามิเตอร์สมมติ ไม่ใช่เส้นทางความผันผวนที่ต้องเกิดจริง และไม่ใช่ความเสี่ยงสะสมตลอด horizon</figcaption>
</figure>

<span id="aggregate-risk"></span>

## ความเสี่ยงหนึ่งวันในอนาคต ต่างจากความเสี่ยงสะสมหลายวัน

ค่า forecast horizon 20 ในตารางเป็น variance ของผลตอบแทนวันที่ 20 จากจุดพยากรณ์ ไม่ใช่ variance ของผลตอบแทนสะสมตลอด 20 วัน

ภายใต้แบบจำลองที่ residual มี conditional mean ศูนย์และไม่สัมพันธ์ข้ามเวลาในเชิง covariance variance ของผลรวม residual หลายวันเป็นผลรวมของ variance forecasts:

$$
\operatorname{Var}_t\left(\sum_{k=1}^{D}\varepsilon_{t+k}\right)
=\sum_{k=1}^{D}E_t[h_{t+k}].
$$

เงื่อนไข mean ศูนย์แบบมีเงื่อนไขทำให้ covariance ข้ามเวลาหายไป แม้กำลังสองของ residual ยังสัมพันธ์กันได้ ถ้าแบบจำลอง mean มีความสัมพันธ์ตามเวลาเพิ่มเติม ต้องรวมผลนั้นเข้าในการพยากรณ์ด้วย

```python
holding_days = 20
aggregate_variance = garch_forecast_path[:holding_days].sum()
aggregate_sd = np.sqrt(aggregate_variance)
constant_today_sd = np.sqrt(holding_days * garch_forecast_path[0])
print("20-day additive-return SD (%):", round(100 * aggregate_sd, 6))
print("Freeze today's variance then scale (%):", round(100 * constant_today_sd, 6))
print("Average daily forecast variance:", round(aggregate_variance / holding_days, 8))
```

การรวม variance forecasts ของ GARCH 20 วันให้ SD ของผลบวกประมาณ 7.204834% แต่ถ้าค้าง variance ของวันพรุ่งนี้ไว้เท่าเดิมทุกวันแล้วคูณสเกล $\sqrt{20}$ จะได้ 7.641989% ตัวเลขต่างกันเพราะ GARCH ตัวอย่างนี้เริ่มจาก variance สูงกว่าระดับระยะยาว และคาดว่า variance เฉลี่ยของวันต่อ ๆ ไปจะลดลง

`garch_forecast_path[:holding_days]` เลือก 20 forecasts แรก และ `.sum()` บวก variance ก่อนถอดราก ห้ามนำ SD ของแต่ละวันมาบวกตรง ๆ เพื่อหาความผันผวนสะสม

ผลบวก simple returns เป็นการประมาณผลตอบแทนหลายวัน ไม่ใช่ผลตอบแทนทบต้น $\prod_k(1+r_k)-1$ โดยตรง สูตรนี้ใช้ตรงกับความเสี่ยงของผลบวก innovations ตามโมเดล หากต้องการการกระจายของผลตอบแทนทบต้นต้องคำนวณเพิ่มเติม เช่น จำลองเส้นทางแล้วทบต้น ภายใต้แบบจำลองที่เหมาะกับชนิดผลตอบแทนและขอบเขตของราคา

<span id="volatility-clustering"></span>

## จำลอง Volatility Clustering โดยยังไม่ทายทิศทางผลตอบแทน

เราเพิ่ม standardized innovation $z_t$ ที่มี mean ศูนย์และ variance หนึ่ง แล้วสร้าง residual ด้วย

$$
\varepsilon_t=\sqrt{h_t}z_t.
$$

ในช่องโค้ดนี้สุ่ม $z_t$ จาก Normal มาตรฐานและใช้พารามิเตอร์ GARCH เดิม ทุกงวดเริ่มจาก variance ที่ทราบก่อน แล้วจึงสุ่ม residual ของงวดนั้น สุดท้ายจึงนำ residual ไปอัปเดต variance งวดใหม่

เมื่อเกิด residual ขนาดใหญ่ variance งวดถัดไปเพิ่ม ทำให้การแกว่งขนาดใหญ่ในช่วงถัดไปมีโอกาสมากขึ้น เราเรียกลักษณะของขนาดการแกว่งที่เกาะกลุ่มตามเวลานี้ว่า [volatility clustering](glossary.html#volatility-clustering) ในการจำลองนี้ $z_t$ เป็น Normal มาตรฐานที่สุ่มอิสระ จึงมีโอกาสบวกและลบอย่างละครึ่งแม้ variance เปลี่ยนไป

```python
rng = np.random.default_rng(20261003)
burn_in, n_keep = 1000, 20000
innovations = rng.standard_normal(burn_in + n_keep)
simulated_h = np.empty(len(innovations) + 1)
simulated_eps = np.empty(len(innovations))
simulated_h[0] = long_run_variance
for t, z in enumerate(innovations):
    simulated_eps[t] = np.sqrt(simulated_h[t]) * z
    simulated_h[t + 1] = omega + alpha * simulated_eps[t]**2 + beta * simulated_h[t]
kept_eps = pd.Series(simulated_eps[burn_in:])
kept_h = simulated_h[burn_in:-1]
standardized_eps = kept_eps / np.sqrt(kept_h)
diagnostics = pd.Series({
    "Mean residual": kept_eps.mean(),
    "Mean conditional variance": kept_h.mean(),
    "Lag-1 residual correlation": kept_eps.autocorr(1),
    "Lag-1 squared-residual correlation": (kept_eps**2).autocorr(1),
    "Lag-1 standardized-squared correlation": (standardized_eps**2).autocorr(1)
})
print(diagnostics.round(6))
filtered_again = garch_variance(simulated_eps, omega, alpha, beta, long_run_variance)
assert np.allclose(filtered_again, simulated_h)
```

จาก seed ที่กำหนด หลังตัดช่วงเริ่มต้น 1,000 งวดและเก็บ 20,000 งวด ได้ค่าประมาณดังนี้:

| ค่าที่ตรวจ | ผลจากการจำลอง |
|---|---:|
| Mean residual | −0.000049 |
| Mean conditional variance | 0.000103 |
| Correlation ระหว่าง residual ติดกันหนึ่งงวด | 0.002118 |
| Correlation ระหว่าง squared residual ติดกันหนึ่งงวด | 0.159305 |
| Correlation ระหว่าง standardized squared residual ติดกันหนึ่งงวด | −0.000153 |

Mean conditional variance อยู่ใกล้ระดับ 0.0001 ที่กำหนดไว้ แต่ไม่จำเป็นต้องตรงเป๊ะใน sample ที่มีขนาดจำกัด ส่วน residual มี correlation ใกล้ศูนย์ ขณะที่กำลังสองมี correlation บวกในเส้นทางนี้ เมื่อหาร residual ด้วย SD ที่ใช้สร้างมัน squared standardized residual จึงกลับไปใกล้ลักษณะของ innovations ที่สุ่มอย่างเป็นอิสระ

`burn_in` คือจำนวนงวดต้นที่ไม่นำมารายงาน เพื่อลดผลของการตั้งต้นที่กำหนดไว้ การตัดออกเป็นขั้นตอนในการจำลองนี้ ไม่ได้พิสูจน์ว่าแบบจำลองที่ประมาณจากข้อมูลจริงถูกต้อง ส่วน `autocorr(1)` คำนวณ sample correlation ระหว่างข้อมูลกับข้อมูลที่เลื่อนหนึ่งงวด ผลใกล้ศูนย์จากสถิติหนึ่งค่าก็ยังไม่เท่ากับพิสูจน์ความเป็นอิสระ

ช่วงท้ายป้อน residual ที่สร้างแล้วกลับเข้าฟังก์ชัน `garch_variance` เพื่อตรวจว่ากู้ลำดับ variance เดิมได้ตรงกัน การตรวจนี้ช่วยจับข้อผิดพลาดเรื่องใช้ $h_t$ หรือ $h_{t+1}$ สลับกัน แต่เรารู้พารามิเตอร์และแบบจำลองผู้สร้างข้อมูลอยู่แล้ว จึงยังไม่ได้ทดสอบความสามารถในการประมาณหรือพยากรณ์ตลาดจริง

การใช้ Normal ในตัวอย่างเป็นสมมติฐานของ innovations เพื่อสาธิตกลไก ไม่ได้อ้างว่าผลตอบแทนตลาดหรือการกระจาย unconditional ของ GARCH เป็น Normal และโมเดล Normal สำหรับ simple returns เป็นการประมาณที่ต้องระวังขอบเขต −100% เมื่อนำไปสร้างราคา บทนี้จำลอง residual เพื่อศึกษาความเสี่ยงโดยไม่สร้างเส้นราคาหรืออ้างผลการลงทุน

<span id="factor-garch"></span>

## ใช้ความเสี่ยงของปัจจัยร่วมสร้าง Covariance ตามเวลา

ถ้ามีสินทรัพย์หลายร้อยตัว การประมาณแบบจำลองตามเวลาสำหรับทุก covariance คู่เพิ่มภาระของข้อมูลและพารามิเตอร์ แนวทาง factor model แยก residual ของสินทรัพย์เป็นส่วนจากปัจจัยร่วมกับส่วนเฉพาะ:

$$
\varepsilon_t=Bf_t+u_t,\qquad
\Sigma_t=B H_{f,t}B^\mathsf{T}+\Psi_t.
$$

$B$ คือเมทริกซ์ factor loadings, $H_{f,t}$ คือ conditional covariance ของปัจจัย และ $\Psi_t$ คือ conditional covariance ของส่วนเฉพาะ สูตรนี้สมมติให้ปัจจัยกับส่วนเฉพาะมี conditional covariance เป็นศูนย์ หากส่วนเฉพาะยังสัมพันธ์กันเอง $\Psi_t$ ก็ไม่จำเป็นต้องเป็นแนวทแยง

เพื่อให้คำนวณตัวอย่างได้ กำหนดสามสินทรัพย์ สองปัจจัย loadings คงที่ และสมมติ $\Psi_t=D$ เป็นเมทริกซ์แนวทแยงคงที่ ให้ปัจจัยทั้งสองมี conditional covariance ระหว่างกันเป็นศูนย์ จึงเขียน $H_{f,t}=\operatorname{diag}(h_{1,t},h_{2,t})$ แล้วอัปเดต variance ของแต่ละปัจจัยด้วย GARCH(1,1)

```python
factor_loadings = np.array([[1.0, 0.2], [0.8, -0.1], [0.3, 1.0]])
factor_variance_before = np.array([0.0001, 0.000225])
factor_residual = np.array([-0.05, 0.01])
factor_omega = (1 - alpha - beta) * factor_variance_before
factor_variance_after = factor_omega + alpha * factor_residual**2 + beta * factor_variance_before
specific_variances = np.array([0.000025, 0.000036, 0.000016])
factor_covariance_before = factor_loadings @ np.diag(factor_variance_before) @ factor_loadings.T + np.diag(specific_variances)
factor_covariance_after = factor_loadings @ np.diag(factor_variance_after) @ factor_loadings.T + np.diag(specific_variances)
factor_portfolio_weights = np.array([0.40, 0.35, 0.25])
print("Factor variances after update:", factor_variance_after)
print("Asset covariance after update:\n", np.round(factor_covariance_after, 8))
print("Portfolio SD before / after (%):", np.round([
    100 * np.sqrt(factor_portfolio_weights @ s @ factor_portfolio_weights)
    for s in [factor_covariance_before, factor_covariance_after]
], 6))
assert np.linalg.eigvalsh(factor_covariance_after).min() >= -1e-12
```

Variance ของสองปัจจัยหลังรับ shock เท่ากับ 0.000292 และ 0.000215 เมื่อนำมาประกอบกับ loadings และความเสี่ยงเฉพาะตัว ได้ covariance ของสินทรัพย์:

$$
\Sigma_{\mathrm{after}}=
\begin{bmatrix}
0.00032560 & 0.00022930 & 0.00013060\\
0.00022930 & 0.00022503 & 0.00004858\\
0.00013060 & 0.00004858 & 0.00025728
\end{bmatrix}.
$$

พอร์ตที่ให้น้ำหนักสินทรัพย์สามตัว 40%, 35%, 25% มี SD เพิ่มจาก 0.927325% เป็น 1.394875% ต่อวัน น้ำหนักยังเป็นชุดเดิม ความต่างเกิดจาก factor variance ที่อัปเดตแล้ว

`factor_loadings` มีสามแถวตามสินทรัพย์และสองคอลัมน์ตามปัจจัย การคูณ `B @ np.diag(h) @ B.T` จึงแปลงความเสี่ยงของปัจจัยเป็นเมทริกซ์ขนาดสามคูณสาม `np.diag(specific_variances)` เติมส่วนเฉพาะตัวที่เรากำหนดให้ไม่สัมพันธ์กัน

แบบจำลองนี้เชื่อมกับ orthogonal factor GARCH ที่ผู้สอนกล่าวถึงท้าย [ARCH and GARCH Models](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/HZZPC/arch-and-garch-models) การได้ปัจจัยที่ไม่สัมพันธ์กันใน sample ทั้งช่วง เช่น จาก PCA ยังไม่รับรองว่าจะมี conditional covariance ศูนย์ทุกวัน สมมติฐานแนวทแยงตามเวลาที่ใช้ตรงนี้จึงต้องตรวจแยก และ orthogonal ก็ไม่ได้แปลว่าเป็นอิสระในความหมายทางสถิติโดยอัตโนมัติ

ตัวอย่างกำหนด $B$, $D$ และพารามิเตอร์ของปัจจัยทั้งหมดไว้แล้ว จึงเป็นการประกอบ covariance ตามสมมติฐาน ไม่มีขั้นตอนสกัดปัจจัยหรือประมาณพารามิเตอร์ หาก loadings หรือความเสี่ยงเฉพาะตัวเปลี่ยนด้วย แต่เราอนุญาตให้เฉพาะ factor variance เปลี่ยน โมเดลก็อาจตามความเสี่ยงจริงไม่ทัน

<span id="forecast-checks"></span>

## ตรวจเวลา หน่วย และพารามิเตอร์ก่อนนำไปใช้

ก่อนใช้ค่าพยากรณ์ในพอร์ต ตรวจว่าการแก้ข้อมูลที่ยังมาไม่ถึงไม่เปลี่ยนค่าก่อนวันนั้น ในตัวอย่างเราจะแก้ residual ตั้งแต่วันที่ 11 เป็นต้นไป ค่า variance ที่ใช้ก่อนเริ่มวันที่ 11 ต้องยังเดิม เพราะคำนวณได้จากวัน 1–10 เท่านั้น

อีกจุดคือหน่วยผลตอบแทน บางโปรแกรมใช้ 1.0 หมายถึง 1% แต่บทนี้ใช้ 0.01 หมายถึง 1% ถ้าคูณ residual ด้วย 100 variance และ $\omega$ ต้องคูณด้วย $100^2$ ส่วน $\alpha$, $\beta$ เป็นสัมประสิทธิ์ที่ไม่มีหน่วยจึงคงเดิม

```python
changed_future = residuals.to_numpy().copy()
changed_future[10:] = 0.20
changed_ewma = ewma_variance(changed_future, lam, initial_variance)
changed_garch = garch_variance(changed_future, omega, alpha, beta, initial_variance)
assert np.allclose(changed_ewma[:11], ewma_h[:11])
assert np.allclose(changed_garch[:11], garch_h[:11])
percent_scale = garch_variance(
    residuals.to_numpy() * 100, omega * 100**2, alpha, beta, initial_variance * 100**2
)
assert np.allclose(percent_scale, garch_h * 100**2)
print("Forecasts through the start of day 11 are unchanged")
print("Decimal/percentage variance scaling passed")
```

ผลรันต้องผ่านเงื่อนไขทั้งสองและพิมพ์ `Forecasts through the start of day 11 are unchanged` กับ `Decimal/percentage variance scaling passed` ออกมา `changed_future[10:]` เริ่มแก้วันที่ 11 เพราะตำแหน่งใน NumPy เริ่มที่ศูนย์ ส่วน `h[:11]` รวมค่า variance ก่อนวัน 1 ถึงก่อนวัน 11 โดยยังไม่รวมการอัปเดตที่ใช้ residual วัน 11

ฟังก์ชันในบทนี้เป็นตัวคำนวณเมื่อรู้พารามิเตอร์แล้ว การทำงานกับข้อมูลจริงยังต้องเลือก mean model และกฎทำความสะอาดข้อมูล ประมาณพารามิเตอร์จากช่วงที่อนุญาต ตรวจข้อจำกัดและการลู่เข้าของตัวประมาณ แล้ววัดการพยากรณ์บนข้อมูลที่กันไว้ ค่า $\omega$, $\alpha$, $\beta$ ที่ทำให้กราฟตามข้อมูลฝึกได้ดีอาจยังพยากรณ์ช่วงใหม่ได้ไม่ดี

การประเมินยังต้องรู้ว่ากำลังใช้ตัวใดเป็นเป้าหมายตรวจความเสี่ยง กำลังสอง residual วันถัดไปเป็นข้อมูลเพียงหนึ่งค่าที่มีความผันผวนสูง ไม่ใช่ conditional variance จริงที่สังเกตได้ตรง ๆ ส่วน realized measures จากข้อมูลถี่กว่าก็มีข้อจำกัดด้านข้อมูลของตัวเอง การเห็น forecast เปลี่ยนทุกวันจึงยังไม่ใช่หลักฐานว่าแม่นกว่าค่าคงที่

ก่อนส่ง covariance เข้า optimizer ควรเก็บเวลาข้อมูล เวลาออกคำพยากรณ์ หน่วยผลตอบแทน สมมติฐาน mean ค่าเริ่มต้น และพารามิเตอร์ที่ใช้ไว้ด้วย หากเปลี่ยนการตั้งค่าแล้วผลพอร์ตดีขึ้นหลังดูข้อมูลทดสอบ ช่วงนั้นได้กลายเป็นข้อมูลพัฒนาวิธีไปแล้ว ต้องใช้ช่วงใหม่ตรวจตามแนวทาง [train/test discipline](portfolio-estimation.html#train-test-discipline)

<span id="time-varying-exercises"></span>

## แบบฝึกหัด

<details class="exercise">
<summary>1. ก่อนวันใหม่มี SD 1% ใช้ EWMA lambda 0.90 ถ้าวันนี้ได้ −5% พรุ่งนี้จะต่างจากกรณี +5% เท่าไร?</summary>

ไม่ต่างในสูตรนี้ เพราะ $(−0.05)^2=(+0.05)^2=0.0025$ ทั้งสองกรณีให้ variance $0.90(0.0001)+0.10(0.0025)=0.00034$ และ SD ประมาณ 1.843909% การตอบสนองที่ขึ้นกับเครื่องหมายของ shock ต้องใช้สมมติฐานเพิ่มเติมจาก EWMA รูปแบบนี้

</details>

<details class="exercise">
<summary>2. ถ้าข้อมูลเก่ามีน้ำหนักเหลือครึ่งหนึ่งหลังประมาณ 11 observations ต้องใช้ lambda ใกล้เท่าไร?</summary>

แก้ $\lambda^{11}=0.5$ ได้ $\lambda=0.5^{1/11}\approx0.9389$ ซึ่งใกล้ 0.94 หากข้อมูลรายวันก็ตีความเป็นประมาณ 11 วันซื้อขาย แต่ถ้าเป็นข้อมูลรายเดือนต้องอ่านเป็น 11 เดือน

</details>

<details class="exercise">
<summary>3. ทำไม finite EWMA หกข้อมูลจึงให้ variance ต่างจาก recursive EWMA แม้ใช้ lambda เดียวกัน?</summary>

Recursive EWMA ของตัวอย่างยังให้น้ำหนัก 0.531441 แก่ค่าเริ่มต้น ส่วน observations หกตัวรวมกันมีน้ำหนัก 0.468559 สูตร finite ที่ใช้ในบทหารน้ำหนัก observations ให้รวมหนึ่งทั้งหมด จึงไม่มีส่วนจากค่าเริ่มต้น การเริ่มต่างกันนี้เห็นชัดเมื่อข้อมูลมีน้อย ต้องระบุสูตรและค่าเริ่มต้นก่อนเทียบตัวเลขจากคนละโปรแกรม

</details>

<details class="exercise">
<summary>4. GARCH มี omega 0.000002, alpha 0.08, beta 0.90 ถ้า variance ล่าสุดเท่ากับระยะยาวและ shock ยกกำลังสองก็เท่าระยะยาว จะได้ค่าใหม่เท่าไร?</summary>

ระดับระยะยาวคือ $0.000002/(1-0.08-0.90)=0.0001$ เมื่อนำทั้ง $h_t$ และ $\varepsilon_t^2$ เท่ากับ 0.0001 เข้าไป จะได้ $0.000002+0.08(0.0001)+0.90(0.0001)=0.0001$ เช่นเดิม นี่ตรวจความสอดคล้องของระดับระยะยาวในสูตร ไม่ได้สมมติว่า shock ทุกวันจะมีขนาดนี้จริง

</details>

<details class="exercise">
<summary>5. ถ้าเพิ่ม alpha เป็น 0.10 แต่คง beta 0.90 และ omega บวกไว้ จะใช้สูตร variance ระยะยาวเดิมได้หรือไม่?</summary>

ผลรวม $\alpha+\beta$ กลายเป็นหนึ่ง ตัวหาร $1-\alpha-\beta$ เป็นศูนย์ จึงไม่มี finite unconditional variance ตามสูตรที่บทนี้ใช้ เมื่อ $\omega>0$ ค่าพยากรณ์ variance หลายงวดจะเพิ่มด้วยส่วน $\omega$ ภายใต้ recursion ของค่าเฉลี่ย แทนที่จะกลับสู่ระดับจำกัด ต้องเปลี่ยนขอบเขตแบบจำลองและการตีความก่อนใช้งาน ไม่ควรแทนตัวหารด้วยเลขเล็ก ๆ เพื่อให้คำนวณต่อได้

</details>

<details class="exercise">
<summary>6. ถ้าค่าเฉลี่ย shock อนาคตเป็นศูนย์ ทำไมใส่ shock ศูนย์ทุกวันแทนการพยากรณ์ไม่ได้?</summary>

เพราะ $E[\varepsilon]=0$ ยังอยู่ร่วมกับ $E[\varepsilon^2]>0$ ได้ เช่น +1% กับ −1% อย่างละครึ่งมี mean ศูนย์ แต่ squared shock เท่ากับ 0.0001 เสมอ การแทน shock ด้วยศูนย์ทำให้ variance ที่ควรเข้าจากความไม่แน่นอนหายไป จึงเป็นสถานการณ์เฉพาะที่ต่างจาก forecast โดยเฉลี่ย

</details>

<details class="exercise">
<summary>7. ถ้า variance เปลี่ยนทุกวัน แปลว่าผลตอบแทนต้องทายทิศทางได้หรือไม่?</summary>

ในตัวอย่าง GARCH เรากำหนดให้ $E[\varepsilon_t\mid\mathcal F_{t-1}]=0$ แม้ $h_t$ เปลี่ยนตามอดีต ความเสี่ยงของขนาดการแกว่งจึงเปลี่ยนได้โดยไม่มีการเปลี่ยนค่าเฉลี่ยผลตอบแทน ส่วนโอกาสบวก/ลบอย่างละครึ่งในตัวอย่างจำลองมาจาก Normal innovations ที่สมมาตรด้วย การมี mean ศูนย์เพียงเงื่อนไขเดียวไม่ได้บังคับให้โอกาสสองด้านเท่ากัน

</details>

<details class="exercise">
<summary>8. มี covariance ของทุกคู่แล้ว ยังต้องตรวจ PSD อีกหรือไม่?</summary>

ต้องตรวจ เพราะตัวเลขที่ดูสมเหตุสมผลแยกคู่ยังอาจประกอบเป็นเมทริกซ์ที่ให้ variance พอร์ตติดลบได้ สูตร EWMA แบบใช้ lambda เดียวและ outer product ของเวกเตอร์ข้อมูลชุดเดียวรักษา PSD เมื่อค่าเริ่มต้นเป็น PSD แต่การประมาณแยกช่อง ใช้ข้อมูลขาดหายต่างชุด หรือปรับบางช่องโดยอิสระอาจทำให้เหตุผลนี้ใช้ไม่ได้ ส่วน PSD ที่มี eigenvalue ศูนย์ก็ยังอาจกลับเมทริกซ์ไม่ได้

</details>

<span id="time-varying-sources"></span>

## แหล่งที่มาและขอบเขตของตัวอย่าง

อ่าน Transcript ของ Coursera ครบทั้งสามบทเมื่อ 3 ตุลาคม 2569 และเรียบเรียงคำอธิบาย ตัวเลข และโค้ดใหม่สำหรับบทนี้:

- [Portfolio Construction with Time-Varying Risk Parameters](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/D2MAC/portfolio-construction-with-time-varying-risk-parameters) ใช้ประกอบเรื่องช่วงข้อมูลย้อนหลังและพารามิเตอร์ความเสี่ยงที่เปลี่ยนตามเวลา
- [Exponentially weighted average](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/c4t09/exponentially-weighted-average) ใช้ประกอบแนวคิดให้น้ำหนักข้อมูลล่าสุดมากกว่าข้อมูลเก่า โดยบทนี้แยกสูตร finite weights ออกจาก recursion และค่าเริ่มต้น
- [ARCH and GARCH Models](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/HZZPC/arch-and-garch-models) ใช้ประกอบการเพิ่มระดับ variance ระยะยาว ความต่อเนื่องของความผันผวน และแนวทาง factor GARCH

ตรวจสมการกับ [Bollerslev (1986), หน้า 307–310 และหัวข้อ GARCH(1,1)](https://econ.duke.edu/~boller/Published_Papers/joe_86.pdf), [RiskMetrics Technical Document ฉบับธันวาคม 1996](https://www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7e95a) ในส่วน EWMA การเลือก decay factor และ Table 5.9 รวมทั้งเอกสาร [EWMAVariance](https://arch.readthedocs.io/en/stable/univariate/generated/arch.univariate.EWMAVariance.html) และ [Forecasting](https://arch.readthedocs.io/en/stable/univariate/forecasting.html) ของผู้พัฒนา arch

ตัวอย่าง 18 วัน เมทริกซ์ covariance และเส้นทางจำลอง 20,000 งวดเป็นข้อมูลที่สร้างขึ้นเพื่อฝึกคำนวณ พารามิเตอร์กำหนดไว้ล่วงหน้า ไม่มีผลประมาณจากราคาตลาด ไม่มีการทำซ้ำผลเชิงประจักษ์ของคอร์ส และไม่ได้เผยแพร่ Transcript หรือข้อมูลต้นฉบับของคอร์สในหน้านี้
