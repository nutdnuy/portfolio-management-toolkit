---
title: จำลองอัตราดอกเบี้ยและราคา Zero-Coupon Bond
description: เรียนหน่วย Short rate แบบจำลอง CIR ข้อจำกัด Euler การคิดราคา ZCB และการเทียบเงินสดกับพอร์ตที่รองรับภาระ
---

# จำลองอัตราดอกเบี้ยและราคา Zero-Coupon Bond

<p class="lead">ถ้าดอกเบี้ยในอนาคตเปลี่ยนได้ การฝากเงินต่อไปเรื่อย ๆ กับการซื้อพันธบัตรให้ครบกำหนดตรงวันใช้เงินจะให้ผลต่างกันอย่างไร?</p>

เราจะสร้างแบบจำลองอัตราดอกเบี้ย คำนวณราคา zero-coupon bond แล้วติดตาม funding ratio ของเป้าหมายเงินก้อนเดียว ตัวอย่างสอดคล้องกับหัวข้อ CIR และ cash versus zero-coupon bonds ใน Module 4 และ Lab 125–127 ใช้พารามิเตอร์สมมติทั้งหมด ไม่ได้ประมาณจากตลาดไทยหรือตลาดใด

โค้ดในหน้านี้รันเรียงกันใน Notebook ใหม่ได้ด้วย NumPy และ pandas เราจะใช้วิธีสุ่มที่ให้การแจกแจงของ CIR ณ จุดเวลาในแบบจำลองตรงตามสูตร แทนการบังคับค่าที่ติดลบจาก Euler ให้กลับเป็นบวก ราคาพันธบัตรคูปองในส่วนท้ายจะใช้เส้นทางดอกเบี้ยเดียวกัน

[ดาวน์โหลด Notebook ของบทนี้](notebooks/interest-rate-models.ipynb) เพื่อรันตัวอย่างตามลำดับและเทียบผลลัพธ์ที่บันทึกไว้

<span id="short-rate-units"></span>

## Short rate กับอัตราทบต้นหนึ่งปี

Short rate คืออัตราดอกเบี้ยสำหรับช่วงเวลาสั้นมาก ณ ขณะนั้น ในแบบจำลองนี้เขียนเป็นอัตราต่อปีแบบทบต้นต่อเนื่อง ถ้าตรึงอัตรา $r$ ไว้คงที่ เงิน 1 บาทจะโตเป็น $e^{rT}$ หลังผ่านไป $T$ ปี

เมื่อ $r=0.03$ และตรึงไว้หนึ่งปี ผลตอบแทน effective เท่ากับ $e^{0.03}-1\approx3.0455\%$ ส่วน effective rate 3% แปลงกลับเป็นอัตราทบต้นต่อเนื่องด้วย $\ln(1.03)\approx0.029559$

```python
import numpy as np
import pandas as pd

continuous_rate = 0.03
annual_effective = np.expm1(continuous_rate)
continuous_from_effective = np.log1p(0.03)
print(f"Effective rate if 3% continuous is held for one year: {annual_effective:.4%}")
print(f"Continuous equivalent of 3% effective: {continuous_from_effective:.6f}")
```

`np.expm1(x)` คำนวณ $e^x-1$ และ `np.log1p(x)` คำนวณ $\ln(1+x)$ โดยช่วยรักษาความแม่นเมื่อค่าเล็ก ถ้า short rate เปลี่ยนระหว่างปี ผลตอบแทนที่เกิดจริงต้องใช้เส้นทางอัตราตลอดปี ไม่ใช่นำ short rate วันนี้ไปแปลงแล้วเรียกว่าอัตราที่จะได้รับแน่นอน

$$
\frac{M_T}{M_0}=\exp\left(\int_0^T r_s\,ds\right).
$$

สัญลักษณ์ integral หมายถึงสะสมอัตราตลอดเวลา ถ้าแบ่งเป็นเดือนและใช้อัตราต้นเดือนคงที่ในเดือนนั้น เราประมาณผลรวมด้วย $\sum_t r_t\Delta t$ โดย $\Delta t=1/12$ ปี ส่วน $M$ คือมูลค่าบัญชีที่นำดอกเบี้ยกลับไปลงทุนต่อ

<span id="cir-mechanism"></span>

## CIR ให้ดอกเบี้ยเปลี่ยนด้วยแรงดึงกลับและความสุ่ม

แบบจำลอง Cox–Ingersoll–Ross หรือ CIR เขียนได้ว่า

$$
dr_t=\kappa(\theta-r_t)dt+\sigma\sqrt{r_t}\,dW_t.
$$

ให้ $r_t$ เป็น short rate, $\theta$ เป็นระดับเฉลี่ยระยะยาวของ short rate, $\kappa$ เป็นความเร็วการดึงกลับ และ $\sigma$ เป็นพารามิเตอร์ขนาดความสุ่ม เมื่ออัตราต่ำกว่า $\theta$ พจน์แรกดึงขึ้น เมื่อสูงกว่าก็ดึงลง แต่ความสุ่มทำให้แต่ละเส้นทางไม่ได้เคลื่อนกลับด้วยความเร็วคงที่ทุกงวด

$dW_t$ คือการเปลี่ยนแปลงของ Brownian motion เมื่อใช้ช่วงเวลา $\Delta t$ เราคิดขนาดของ shock เป็น $\sqrt{\Delta t}Z$ โดย $Z$ มีการแจกแจง Normal มาตรฐาน ค่า $\sigma$ จึงไม่ใช่ส่วนเบี่ยงเบนมาตรฐานของระดับดอกเบี้ยรายปีโดยตรง เพราะพจน์สุ่มยังคูณด้วย $\sqrt{r_t}$

เราใช้เวลาเป็นปีทั้งในสมการและโค้ด ดังนั้น $\kappa$ ต้องสอดคล้องกับหน่วยปี และ $r_0$ กับ $\theta$ ต้องเป็น short rate ใน convention เดียวกัน การแปลงเฉพาะ $r_0$ จาก effective rate แต่ปล่อย $\theta$ เป็นอีก convention จะทำให้กระบวนการดึงไปหาระดับที่ไม่ตรงกับคำอธิบาย

| พารามิเตอร์สมมติ | ค่า | ความหมายในตัวอย่าง |
|---|---:|---|
| $r_0$ | 0.03 | short rate เริ่มต้น 3% แบบต่อเนื่อง |
| $\theta$ | 0.04 | ระดับเฉลี่ยระยะยาว 4% ในหน่วยเดียวกัน |
| $\kappa$ | 0.4 | ความเร็ว mean reversion ต่อปี |
| $\sigma$ | 0.12 | พารามิเตอร์ diffusion |
| $\Delta t$ | 1/12 | ระยะห่างจุดเวลาหนึ่งเดือน |

ระดับคาดหมายภายใต้ measure ที่กำหนดพารามิเตอร์นั้นคือ

$$
\mathbb{E}[r_t\mid r_0]=\theta+(r_0-\theta)e^{-\kappa t}.
$$

```python
kappa, theta, sigma = 0.4, 0.04, 0.12
r0 = 0.03
horizon = 5.0
expected_rate_at_five = theta + (r0 - theta) * np.exp(-kappa * horizon)
print(f"Model mean short rate after five years: {expected_rate_at_five:.6%}")
print(f"Mean-reversion half-life: {np.log(2) / kappa:.4f} years")
```

ค่าเฉลี่ยตามแบบจำลองเมื่อครบห้าปีคือ 3.864665% ส่วน half-life ประมาณ 1.7329 ปี บอกเวลาที่ระยะห่างของค่าเฉลี่ยจาก $\theta$ ลดลงครึ่งหนึ่ง ไม่ได้กำหนดว่าทุกเส้นทางจะถึงจุดนั้นพร้อมกัน

<span id="cir-euler-caveat"></span>

## ทำไม Euler ยังสร้างอัตราติดลบได้

ภายใต้พารามิเตอร์บวก กระบวนการ CIR ในเวลาต่อเนื่องไม่ติดลบ และถ้า $2\kappa\theta\geq\sigma^2$ พร้อมค่าเริ่มบวก จะไม่ชนศูนย์ เงื่อนไขนี้มักเรียกว่า Feller condition อย่างไรก็ตามสูตรประมาณแบบ Euler ใช้การกระโดดครั้งละช่วงเวลาจำกัด จึงอาจกระโดดเลยศูนย์ได้

$$
r_{t+\Delta t}^{\mathrm{Euler}}
=r_t+\kappa(\theta-r_t)\Delta t
+\sigma\sqrt{r_t\Delta t}\,Z_t.
$$

```python
dt = 1 / 12
near_zero_rate = 0.0001
large_negative_shock = -5.0
raw_euler_next = (
    near_zero_rate
    + kappa * (theta - near_zero_rate) * dt
    + sigma * np.sqrt(near_zero_rate * dt) * large_negative_shock
)
print(f"Feller condition holds: {2 * kappa * theta >= sigma ** 2}")
print(f"Raw Euler next rate: {raw_euler_next:.6f}")
print(f"Clipped to zero: {max(raw_euler_next, 0):.6f}")
print(f"Reflected with abs: {abs(raw_euler_next):.6f}")
```

แม้พารามิเตอร์ผ่าน Feller condition ค่าที่ได้จาก Euler เท่ากับ −0.000302 การใช้ `max(value, 0)` กับ `abs(value)` ให้ผลต่างกัน อันแรกตัดลงที่ศูนย์ อันหลังสะท้อนค่าลบกลับเป็นบวก ทั้งสองเปลี่ยนการแจกแจงของค่าที่ได้จากขั้น Euler จึงต้องเรียกว่าเป็นทางเลือกของการประมาณเชิงตัวเลข ไม่ควรอธิบายทุกค่าติดลบว่าเป็นเพียงการปัดเศษ

วิธี full-truncation Euler ยังมีรายละเอียดเกี่ยวกับค่าที่ใช้ใน drift และ diffusion จึงควรระบุสูตรจริง การลดขนาดช่วงเวลาช่วยศึกษาความคลาดเคลื่อนของการประมาณได้ แต่ไม่ใช่หลักฐานว่า CIR อธิบายตลาดได้ดีขึ้นโดยตัวมันเอง

<span id="exact-cir-grid"></span>

## สุ่ม CIR ณ จุดเวลาด้วยการแจกแจงที่ตรงกับแบบจำลอง

สำหรับ CIR ที่ $\kappa,\theta,\sigma>0$ เราสุ่มค่าถัดไปโดยใช้ noncentral chi-square distribution ได้ ไม่จำเป็นต้องเข้าใจการแจกแจงนี้ทั้งหมดก่อนใช้ตัวอย่าง แต่ต้องรู้ว่าแต่ละพารามิเตอร์มาจากอะไร และผลที่ตรงตามสูตรเป็นผลภายใต้ CIR เท่านั้น

ให้ $u=e^{-\kappa\Delta t}$ แล้วกำหนด

$$
c=\frac{\sigma^2(1-u)}{4\kappa},\qquad
\nu=\frac{4\kappa\theta}{\sigma^2},\qquad
\lambda_t=\frac{r_tu}{c}.
$$

จากนั้นสุ่ม $X$ จาก noncentral chi-square ที่มี degrees of freedom $\nu$ และ noncentrality $\lambda_t$ แล้วตั้ง $r_{t+\Delta t}=cX$ การสุ่มนี้ให้การแจกแจงตามเงื่อนไขของ CIR ณ จุดเวลาที่เลือก รวมถึงเมื่อ Feller condition ไม่ผ่าน แต่การอนุมานว่าอัตราไม่แตะศูนย์ระหว่างจุดเวลาจะใช้ไม่ได้ในกรณีนั้น

```python
def simulate_cir_grid(kappa, theta, sigma, r0, years, steps_per_year, paths, seed):
    if min(kappa, theta, sigma) <= 0 or r0 < 0:
        raise ValueError("This sampler needs positive parameters and nonnegative r0.")
    intervals = years * steps_per_year
    if years <= 0 or steps_per_year <= 0 or paths < 1 or not np.isclose(intervals, round(intervals)):
        raise ValueError("Use a whole number of intervals and positive sizes.")
    n = int(round(intervals))
    dt = 1 / steps_per_year
    rng = np.random.default_rng(seed)
    decay = np.exp(-kappa * dt)
    scale = sigma ** 2 * (1 - decay) / (4 * kappa)
    degrees = 4 * kappa * theta / sigma ** 2
    rates = np.empty((n + 1, paths))
    rates[0] = r0
    for step in range(n):
        noncentrality = rates[step] * decay / scale
        rates[step + 1] = scale * rng.noncentral_chisquare(degrees, noncentrality)
    return np.arange(n + 1) * dt, rates

times, rates = simulate_cir_grid(
    kappa, theta, sigma, r0,
    years=5, steps_per_year=12, paths=2_000, seed=20261004,
)
print("Rate array shape:", rates.shape)
print("All rates nonnegative:", np.all(rates >= 0))
print(f"Simulated final mean: {rates[-1].mean():.6%}")
print(f"Analytic final mean: {expected_rate_at_five:.6%}")
```

ได้ array ขนาด 61 × 2,000 เพราะเวลาห้าปีรายเดือนมี 60 ช่วงและต้องเก็บแถวเริ่มต้นเพิ่มอีกหนึ่งแถว แต่ละคอลัมน์เป็นหนึ่งเส้นทาง ผลตรวจไม่ติดลบเป็น `True` ค่าเฉลี่ยสุ่มที่ได้ประมาณ 3.856864% เทียบกับค่าตามสูตร 3.864665% ความต่างเล็กน้อยเป็น Monte Carlo error ของตัวอย่างนี้

`rates[0] = r0` ใส่อัตราเริ่มต้นเดียวกันในทุกเส้นทาง `for step in range(n)` เดินจากช่วง 0 ถึง 59 และคำนวณแถวถัดไปจากแถวที่ทราบแล้ว `seed` ทำให้ตรวจการทดลองเดิมซ้ำได้เมื่อใช้เวอร์ชันเครื่องมือเดียวกัน [NumPy อธิบายพารามิเตอร์ noncentral chi-square](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.noncentral_chisquare.html)

<span id="physical-risk-neutral"></span>

## ความน่าจะเป็นเพื่อวางแผน กับความน่าจะเป็นเพื่อคิดราคา

การใช้แบบจำลองอัตราดอกเบี้ยมีอย่างน้อยสองงาน งานหนึ่งจำลองสิ่งที่อาจเกิดจริงเพื่อวางแผน เรียก measure นี้ว่า physical หรือ real-world measure และมักใช้สัญลักษณ์ $\mathbb P$ อีกงานใช้ risk-neutral measure $\mathbb Q$ เพื่อคิดราคาที่สอดคล้องกับกรอบ no-arbitrage

พารามิเตอร์ drift ภายใต้สอง measure อาจต่างกัน การเปลี่ยน measure ไม่ได้แปลว่าทุกคนไม่กลัวความเสี่ยง แต่เป็นการจัดส่วนชดเชยความเสี่ยงเข้าไปในวิธีคิดราคา การนับจำนวนเส้นทางที่เงินขาดจากการสุ่มภายใต้ $\mathbb Q$ จึงไม่ใช่ประมาณการความน่าจะเป็นขาดเงินจริงโดยตรง

ในส่วนคิดราคาต่อจากนี้ เรากำหนดให้ `kappa`, `theta` และ `sigma` เป็นพารามิเตอร์ ภายใต้ $\mathbb Q$ และใช้เส้นทางที่สุ่มจากพารามิเตอร์ชุดนี้เพื่อสาธิตราคาเท่านั้น ถ้าจะใช้ในแผนการเงินจริง ต้องประมาณหรือกำหนดพารามิเตอร์ภายใต้ $\mathbb P$ แยก แล้วใช้โมเดลราคา $\mathbb Q$ คิดราคาตามสถานะดอกเบี้ยที่จำลองมา รวมถึงกำหนดความสัมพันธ์กับสินทรัพย์อื่นด้วย

แบบจำลองที่มีเพียง short rate ตัวเดียวไม่สามารถทำให้เส้นอัตราตั้งต้นทุกรูปทรงตรงตลาดได้อย่างอิสระ การใช้พารามิเตอร์สมมติชุดเดียวสร้างทั้งราคาและสถานการณ์ในบทนี้จึงเป็นห้องทดลองทางคณิตศาสตร์ ไม่มีขั้น calibration กับราคาตลาด

<span id="cir-zero-coupon-price"></span>

## ราคา Zero-Coupon Bond ภายใต้ CIR

Zero-coupon bond ที่จ่าย 1 บาท ณ เวลา $T$ มีราคาภายใต้ CIR เท่ากับ

$$
P(t,T)=A(\tau)e^{-B(\tau)r_t},\qquad \tau=T-t.
$$

เมื่อใช้พารามิเตอร์ $\mathbb Q$ กำหนด $h=\sqrt{\kappa^2+2\sigma^2}$ จะได้

$$
B(\tau)=\frac{2(e^{h\tau}-1)}{2h+(\kappa+h)(e^{h\tau}-1)},
$$

$$
A(\tau)=\left[
\frac{2h e^{(\kappa+h)\tau/2}}
{2h+(\kappa+h)(e^{h\tau}-1)}
\right]^{2\kappa\theta/\sigma^2}.
$$

ตัวอักษร $B(\tau)$ ในสูตรนี้เป็นสัมประสิทธิ์ ไม่ใช่ราคาพันธบัตร $P(t,T)$ เราใช้ชื่อ `coefficient_b` ในโค้ดเพื่อแยกความหมาย ราคาเป็นบาทต่อเงินครบกำหนด 1 บาท หากพันธบัตรจ่าย 100,000 บาท ให้คูณราคานี้ด้วย 100,000

```python
def cir_zcb_price(short_rate, time_to_maturity, kappa, theta, sigma):
    r = np.asarray(short_rate, dtype=float)
    tau = np.asarray(time_to_maturity, dtype=float)
    if np.any(r < 0) or np.any(tau < 0) or kappa <= 0 or theta < 0 or sigma < 0:
        raise ValueError("Invalid CIR rate, maturity or parameter.")
    if sigma == 0:
        integrated_rate = theta * tau + (r - theta) * (-np.expm1(-kappa * tau)) / kappa
        return np.exp(-integrated_rate)
    h = np.sqrt(kappa ** 2 + 2 * sigma ** 2)
    growth_minus_one = np.expm1(h * tau)
    denominator = 2 * h + (kappa + h) * growth_minus_one
    coefficient_b = 2 * growth_minus_one / denominator
    log_a = (2 * kappa * theta / sigma ** 2) * (
        np.log(2 * h) + (kappa + h) * tau / 2 - np.log(denominator)
    )
    return np.exp(log_a - coefficient_b * r)

time_remaining = horizon - times
zc_prices = cir_zcb_price(
    rates, time_remaining[:, None], kappa, theta, sigma
)
print(f"Initial five-year ZCB price: {zc_prices[0, 0]:.6f}")
print("Maturity prices all equal one:", np.allclose(zc_prices[-1], 1.0))
print("Every price is positive:", np.all(zc_prices > 0))
```

ราคา ZCB เริ่มต้นประมาณ 0.839011 บาทต่อเงินครบกำหนด 1 บาท ผลตรวจราคาวันครบกำหนดเท่ากับหนึ่งทุกเส้นทางเป็น `True` เพราะเมื่อ $\tau=0$ จะได้ $A(0)=1$ และ $B(0)=0$ ผู้ถือกำลังรับเงิน 1 บาท ณ วันนั้น ราคาที่สุ่มขึ้นลงก่อนวันครบกำหนดต้องมาบรรจบที่ payoff ตามสัญญาในแบบจำลองที่ไม่ผิดนัด

`time_remaining[:, None]` เปลี่ยน array เวลา 61 ค่าให้มีรูป 61 × 1 เพื่อให้ NumPy จับคู่กับ rates ขนาด 61 × 2,000 โดยใช้เวลาเดียวกันกับทุกเส้นทางในแต่ละแถว วิธีขยายมิติเพื่อคำนวณร่วมกันนี้เรียกว่า broadcasting

กรณี `sigma == 0` ไม่มีความสุ่มของอัตรา เราจึงคิดลดจาก integral ของเส้น mean reversion ที่แน่นอนได้โดยตรง โดยไม่หารด้วย $\sigma^2$ สูตรหลักตรวจเทียบได้กับ [โค้ด CIR ของ QuantLib](https://github.com/lballabio/QuantLib/blob/master/ql/models/shortrate/onefactormodels/coxingersollross.cpp) ซึ่งแยกสัมประสิทธิ์ $A$ และ $B$ เช่นกัน

<span id="cir-cash-vs-bond"></span>

## เงินต้นเท่ากัน แต่ความเสี่ยงเทียบเป้าหมายต่างกัน

กำหนดเป้าหมายจ่าย 100,000 บาทเมื่อครบห้าปี และให้ทุนเริ่มต้นเท่ากับ 95% ของ PV เป้าหมายที่โมเดลคำนวณ การซื้อ ZCB ที่อายุครบตรงกันด้วยเงินนี้ทำให้ถือเงินต้นครบกำหนด 95,000 บาท ไม่ว่าอัตราดอกเบี้ยจะเดินเส้นทางใดตามแบบจำลอง

```python
goal = 100_000.0
initial_liability = goal * zc_prices[0, 0]
initial_assets = 0.95 * initial_liability
units = initial_assets / zc_prices[0, 0]
bond_assets = units * zc_prices
liability_values = goal * zc_prices
bond_funding = bond_assets / liability_values

print(f"Initial assets: {initial_assets:,.2f}")
print(f"Bond units paying one baht each: {units:,.2f}")
print("Funding ratio always 95%:", np.allclose(bond_funding, 0.95))
print(f"Terminal matched assets: {bond_assets[-1, 0]:,.2f}")
```

คำตอบปลายทางคือ 95,000 บาท และ funding ratio 95% ทุกจุด เพราะสินทรัพย์และภาระใช้ราคา ZCB เดียวกัน การเริ่ม underfunded ยังเหลือเงินขาด 5,000 บาทในวันจ่าย แม้ความเสี่ยงของอัตราส่วนในแบบจำลองถูก hedge แล้ว

โค้ดซื้อจำนวนหน่วยด้วย `zc_prices[0, 0]` ซึ่งเป็นราคาจากโมเดลเดียวกับที่ใช้ประเมินต่อ ถ้าเปลี่ยนไปใช้ $1/1.03^5$ โดยไม่มีเหตุผล ทั้งที่ราคา CIR เริ่มต้นไม่เท่ากัน เงินลงทุนวันแรกและจำนวนหน่วยจะไม่ตรงกับแบบจำลองราคา

ต่อไปลองนำทุนเริ่มต้นเดียวกันพักในบัญชีที่ได้ short rate และปรับอัตรารายเดือน เราประมาณ integral โดยใช้อัตรา ต้นช่วง จึงใช้ `rates[:-1]` และเริ่มแถวศูนย์ด้วยเงินต้นตรง ๆ

```python
monthly_cash_growth = np.exp(rates[:-1] * dt)
cash_assets = np.vstack([
    np.full((1, rates.shape[1]), initial_assets),
    initial_assets * np.cumprod(monthly_cash_growth, axis=0),
])
cash_funding = cash_assets / liability_values
print("Cash wealth shape:", cash_assets.shape)
print("Initial cash equals initial assets:", np.allclose(cash_assets[0], initial_assets))
print(pd.Series(cash_funding[-1]).quantile([0.05, 0.50, 0.95]).round(6))
```

Funding ratio ของเงินสดที่เปอร์เซ็นไทล์ 5, 50 และ 95 ประมาณ 0.863850, 0.939860 และ 1.092564 ตามลำดับ เพราะอัตราที่ได้รับระหว่างรอไม่ถูกล็อกไว้ ในตัวอย่างนี้อัตราทั้งหมดไม่ติดลบ เงินสดแต่ละเส้นทางจึงไม่ลดจากการทบต้น แต่ PV ของภาระยังขึ้นลงได้ก่อนถึงวันจ่าย

การสุ่ม CIR ณ จุดเดือนในส่วนก่อนตรงตาม transition distribution แต่การสะสมดอกเบี้ยด้วยอัตราต้นเดือนยังเป็นการประมาณ integral คนละส่วนกัน ถ้าศึกษาความแม่นของเงินสดต้องลองลดช่วงเวลา หรือใช้วิธีที่จำลอง integral ร่วมกับอัตราได้เหมาะสม ห้ามอ้างว่าใช้ exact transition แล้วผลทุกส่วนของระบบจึง exact ทั้งหมด

<span id="zcb-terminal-return"></span>

## รวมผลตอบแทนให้ถึงวันครบกำหนดโดยไม่บวกเงินต้นซ้ำ

เส้น `zc_prices` ด้านบนใช้ราคา 1 ในแถวสุดท้ายเป็นมูลค่าที่ได้รับคืนเมื่อครบกำหนด จึงคำนวณผลตอบแทน ZCB ด้วยราคาติดกันได้ และไม่บวกเงินคืนต้นอีกครั้ง

```python
zc_returns = zc_prices[1:] / zc_prices[:-1] - 1
terminal_growth = np.prod(1 + zc_returns, axis=0)
direct_growth = zc_prices[-1] / zc_prices[0]
print("Return compounding equals endpoint ratio:", np.allclose(terminal_growth, direct_growth))
print(f"Cumulative ZCB return per invested baht: {terminal_growth[0] - 1:.4%}")
```

ได้ `True` และทุกเส้นทางมีผลตอบแทนรวมประมาณ 19.1880% เท่ากัน เพราะซื้อที่ราคาเริ่มต้นเดียวกันและได้รับ 1 บาทปลายทางเหมือนกัน ผลตอบแทนระหว่างเดือนยังแกว่งได้ และหากต้องขายก่อนครบห้าปีก็จะได้รับราคาของวันขาย

อีก convention ที่ใช้ได้คือให้ราคาหลังไถ่ถอนเป็นศูนย์และใส่ cash payment 1 ในงวดสุดท้าย ทั้งสองวิธีให้ total return เดียวกันถ้าทำสอดคล้องกัน บท [พันธบัตรและ Duration](bonds-duration.html#bond-total-return) ใช้วิธีหลังสำหรับพันธบัตรคูปอง ขณะที่หน้านี้ใช้มูลค่าไถ่ถอนเป็นจุดสุดท้ายของเส้น ZCB

<span id="cir-coupon-bonds"></span>

## พันธบัตรคูปองบนเส้นทางดอกเบี้ยเดียวกัน

Lab 127 ต่อจาก ZCB ไปสู่พันธบัตรคูปอง เราจะสร้างพันธบัตรเงินต้น 1,000 บาท จ่ายคูปองปีละ 40 บาท อายุห้าปี บนเส้นทาง CIR ที่มีอยู่แล้ว กระแสเงินสดเป็น 40, 40, 40, 40 และ 1,040 บาท ณ สิ้นปีที่ 1 ถึง 5 ตามลำดับ

ราคาก่อนครบกำหนดคือผลรวมราคา ZCB ที่รองรับแต่ละกระแสเงินสด เมื่ออยู่ ณ เวลา $t$ ให้รวมเฉพาะเงินที่ยังไม่ได้รับ

$$
B_t=\sum_{t_j>t} C_j P(t,t_j).
$$

ในส่วนนี้ $B_t$ เป็นราคาพันธบัตรคูปองหลังจ่ายเงิน ณ เวลา $t$ แล้ว จึงกำหนดราคาหลังไถ่ถอนเป็นศูนย์ และเก็บเงินต้นกับคูปองงวดสุดท้ายไว้ในช่องเงินรับ การใช้ convention นี้ทำให้เห็นชัดว่าต้องนำเงินจ่ายกลับเข้าผลตอบแทนอย่างไร

```python
steps_per_year = 12
payment_steps = np.arange(12, 61, 12)
coupon_flows = np.full(len(payment_steps), 40.0)
coupon_flows[-1] += 1_000.0
coupon_prices = np.zeros_like(rates)
coupon_payments = np.zeros(len(times))
coupon_payments[payment_steps] = coupon_flows

for step in range(len(times) - 1):
    still_due = payment_steps > step
    remaining_years = (payment_steps[still_due] - step) / steps_per_year
    discounts = cir_zcb_price(
        rates[step, :, None], remaining_years[None, :],
        kappa, theta, sigma,
    )
    coupon_prices[step] = (discounts * coupon_flows[still_due]).sum(axis=1)

coupon_returns = (
    (coupon_prices[1:] + coupon_payments[1:, None]) / coupon_prices[:-1] - 1
)
print(f"Initial coupon bond price: {coupon_prices[0, 0]:,.4f}")
print("Final ex-redemption price is zero:", np.allclose(coupon_prices[-1], 0))
print(f"Final payment per original bond: {coupon_payments[-1]:,.2f}")
print("Return shape:", coupon_returns.shape)
```

ราคาเริ่มต้น 1,019.7433 บาท ราคาปลายทางศูนย์ เงินรับงวดสุดท้าย 1,040 บาท และผลตอบแทนขนาด 60 × 2,000 การเปรียบเทียบ `payment_steps > step` ตัดเงินที่จ่ายไปแล้วออกจากราคา ส่วน `coupon_payments` เก็บเงินนั้นเพื่อรวมในผลตอบแทนงวดที่ได้รับ ในเดือนที่ไม่มีคูปอง ช่องเงินรับเป็นศูนย์

การคูณ `1 + coupon_returns` สะสมหมายถึงนำเงินคูปองกลับซื้อพันธบัตรเดิม ณ ราคาหลังจ่ายคูปองทันที โดยซื้อเศษหน่วยได้ ถ้าต้องการถือพันธบัตรเดิมหนึ่งหน่วยตลอด แล้วพักคูปองในบัญชี short rate ต้องคำนวณอีกวิธีหนึ่ง จำนวนพันธบัตรคงที่แต่บัญชีเงินสดเพิ่มจากดอกเบี้ยและเงินที่รับ

```python
reinvested_bond_growth = np.prod(1 + coupon_returns, axis=0)
coupon_cash = np.zeros_like(rates)
for step in range(len(times) - 1):
    coupon_cash[step + 1] = (
        coupon_cash[step] * monthly_cash_growth[step]
        + coupon_payments[step + 1]
    )
one_bond_total_wealth = coupon_prices + coupon_cash
terminal_coupon_wealth = pd.DataFrame({
    "Reinvest in same bond": coupon_prices[0] * reinvested_bond_growth,
    "Keep one bond; save coupons": one_bond_total_wealth[-1],
})
print(terminal_coupon_wealth.quantile([0.05, 0.50, 0.95]).round(2))
print("Initial wealth equals purchase price:", np.allclose(
    one_bond_total_wealth[0], coupon_prices[0]
))
```

ค่ากลางของเงินปลายทางในสองคอลัมน์ประมาณ 1,214.90 และ 1,214.06 บาทตามลำดับ สองวิธีใช้ต้นทุนเริ่มเดียวกัน แต่กติกาลงทุนต่อของคูปองต่างกัน จึงให้เงินปลายทางต่างกันได้ สำหรับวิธีพักคูปองในเงินสด เงิน 1,040 บาทสุดท้ายเพิ่งได้รับในวันครบกำหนดและไม่มีช่วงให้รับดอกเบี้ยเพิ่ม โค้ดจึงทบต้นยอดเงินสดเดิมก่อนบวกเงินรับใหม่ การนำเงินรับไปทบต้นตั้งแต่ต้นเดือนที่ยังไม่ได้รับจะนับดอกเบี้ยเกินจริง

ผลทั้งหมดนี้ยังอยู่ภายใต้สถานการณ์ $\mathbb Q$ สมมติชุดเดิม ตาราง quantile ใช้ดูการทำงานของราคาและกระแสเงินสด หากจะรายงานโอกาสได้เงินไม่พอสำหรับผู้ลงทุน ต้องจำลองสถานการณ์ด้วยสมมติฐาน real-world และประเมินพารามิเตอร์อย่างเหมาะสมก่อน

<span id="cir-model-checks"></span>

## ตรวจแบบจำลองก่อนนำผลไปวางแผน

เมื่อเพิ่มจำนวนเส้นทาง ค่าเฉลี่ยสุ่มควรนิ่งขึ้นใกล้ค่าเฉลี่ยตามสูตร แต่ถ้าค่าเฉลี่ยระยะยาวหรือความผันผวนที่ตั้งไว้ไม่เหมาะกับตลาด การสุ่มเพิ่มจะเพียงทำให้สรุปสมมติฐานเดิมได้ละเอียดขึ้น CIR พื้นฐานยังบังคับอัตราไม่ติดลบ จึงไม่ครอบคลุมสภาพอัตราดอกเบี้ยติดลบโดยตรง

จำนวนเส้นทางกับความละเอียดเวลาเป็นคนละแกนของการตรวจ จำนวนเส้นทางช่วยลด Monte Carlo error ส่วนความละเอียดเวลามีผลกับส่วนที่ยังประมาณระหว่างจุด เช่น integral ดอกเบี้ยหรือการปรับพอร์ต ความผิดของแบบจำลองเกิดจากการเลือกโครงสร้างหรือพารามิเตอร์ และจะยังอยู่แม้แก้สองอย่างแรกแล้ว

การแปลง rate เป็น effective rate รายปีมีไว้แสดง convention ไม่ได้เปลี่ยนมันให้เป็น yield ของพันธบัตรห้าปี Yield ของ ZCB ห้าปีต้องคำนวณจากราคาและเวลาที่เหลือ เช่น $P(0,5)^{-1/5}-1$ เมื่อเลือก effective annual convention

```python
initial_five_year_yield = zc_prices[0, 0] ** (-1 / horizon) - 1
initial_short_rate_effective = np.expm1(r0)
print(f"Five-year effective zero yield: {initial_five_year_yield:.4%}")
print(f"Effective equivalent of current short rate: {initial_short_rate_effective:.4%}")
```

ได้ zero yield ห้าปีประมาณ 3.5730% กับ effective equivalent ของ short rate 3.0455% ทั้งสองต่างกันเพราะราคาพันธบัตรห้าปีสะท้อนอัตราตลอดอายุภายใต้โมเดลราคา ไม่ได้ตรึง short rate วันนี้ไว้ห้าปี

<span id="cir-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

1. Short rate ต่อเนื่อง 4% ถ้าตรึงหนึ่งปี ให้ effective return เท่ากับ 4% พอดีหรือไม่?
2. มีเวลา 3 ปีและจุดเวลารายเดือน ต้องมีแถวอัตรากี่แถว และมีช่วงผลตอบแทนกี่ช่วง?
3. หาก Euler ให้ค่าลบ แม้ Feller condition ผ่าน ต้องสรุปว่า CIR ในเวลาต่อเนื่องติดลบด้วยหรือไม่?
4. ทำไม ZCB ที่จ่าย 1 บาทเมื่อครบกำหนดต้องมีราคา 1 ในแถวไถ่ถอนของหน้านี้?
5. ถ้าซื้อ ZCB ตรงเป้าหมายด้วยเงิน 90% ของ PV เงินขาดปลายทางจะหายไปเพราะ hedge แล้วหรือไม่?
6. การนับเส้นทางที่ funding ratio ต่ำกว่าหนึ่งจากการสุ่ม $\mathbb Q$ ใช้เป็นโอกาสขาดเงินจริงได้ทันทีหรือไม่?

<details>
<summary>เปิดแนวคำตอบ</summary>

ข้อ 1 ได้ $e^{0.04}-1\approx4.0811\%$ ข้อ 2 มี 37 แถวและ 36 ช่วง โดยแถวแรกคือสถานะก่อนเริ่มรับผลตอบแทน

ข้อ 3 ค่าลบอาจเกิดจากการประมาณ Euler ที่ช่วงเวลาจำกัด ต้องตรวจวิธี discretization แยกจากคุณสมบัติของกระบวนการ ข้อ 4 แถวสุดท้ายบันทึกเงินไถ่ถอน 1 บาทแล้ว จึงไม่มีส่วนลดของเวลาที่เหลือและไม่บวกเงินต้นซ้ำ

ข้อ 5 เงินที่ขาดยังเท่ากับ 10% ของเป้าหมาย การ matching รักษาสัดส่วนที่เริ่มต้น ข้อ 6 ต้องใช้สมมติฐาน real-world ที่เหมาะสมสำหรับการประมาณความถี่จริง และรายงานความเสี่ยงของแบบจำลองด้วย

</details>

<span id="cir-sources"></span>

## แหล่งเรียนและความต่างของตัวอย่างนี้

อ่านแนวคิดจาก [Liability hedging portfolios](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/JT5zQ/liability-hedging-portfolios) และโค้ดของ [Lab Session–CIR Model and cash vs ZC bonds](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/TzdrX/lab-session-cir-model-and-cash-vs-zc-bonds) รวมถึง [Lab Session–Monte Carlo simulation of coupon-bearing bonds using CIR](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/nQUCQ/lab-session-monte-carlo-simulation-of-coupon-bearing-bonds-using-cir) ประกอบ `lab_125.ipynb`, `lab_127.ipynb` และฟังก์ชันที่เกี่ยวข้องใน toolkit ที่ผู้เรียนให้มา

พื้นฐานแบบจำลองมาจาก Cox, Ingersoll และ Ross, *A Theory of the Term Structure of Interest Rates*, Econometrica 53(2), 1985, หน้า 385–407 [บทความต้นฉบับ](https://roycheng.cn/files/papers/interestRate/paper_Cox%26Ingersoll%26Ross_1985.pdf) ตัวอย่างใหม่ใช้ short rate convention เดียวทั้ง $r_0$ และ $\theta$ กำหนด measure ของการคิดราคาให้ชัด และใช้ราคาเริ่มจากสูตรเดียวกับราคาที่ประเมินต่อ การสุ่มผ่าน noncentral chi-square แยกจากวิธี Euler ที่พบใน Lab เพื่อให้ตรวจคุณสมบัติของแบบจำลองกับความคลาดเคลื่อนของวิธีคำนวณได้
