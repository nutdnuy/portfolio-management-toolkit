---
title: พันธบัตร กระแสเงินสด และ Duration
description: คำนวณราคาพันธบัตรจากเงินรับแต่ละงวด แยกคูปองออกจาก Yield และใช้ Duration จับคู่ความเสี่ยงของสินทรัพย์กับภาระ
---

# พันธบัตร กระแสเงินสด และ Duration

<p class="lead">พันธบัตรจ่ายคูปอง 4% แต่ผู้ซื้อจ่ายต่ำกว่าเงินต้นครบกำหนด ผลตอบแทนของผู้ซื้อจะยังเป็น 4% หรือไม่?</p>

เราจะเขียนเงินรับแต่ละงวดก่อนคำนวณราคา แล้วตรวจว่าราคาเปลี่ยนอย่างไรเมื่อ yield เปลี่ยน จากนั้นนำพันธบัตรสองอายุมารวมกันเพื่อรองรับเงินที่ต้องจ่ายในอีกห้าปี ตัวอย่างใช้จำนวนเงินสมมติ ไม่มีการผิดนัด ภาษี ค่าธรรมเนียม หรือสิทธิไถ่ถอนก่อนกำหนด และประเมินราคาบนวันจ่ายคูปองเพื่อยังไม่ต้องคิดดอกเบี้ยค้างรับ

หัวข้อสอดคล้องกับ Module 4 และ Lab 126–127 ของ EDHEC/Coursera โค้ดแต่ละกรอบใช้ค่าจากกรอบก่อนหน้าในหน้านี้ แต่ไม่ต้อง import โค้ดจากบทอื่น ให้เริ่ม Notebook ใหม่ด้วยกรอบแรก

[ดาวน์โหลด Notebook ของบทนี้](notebooks/bonds-duration.ipynb) เพื่อรันตัวอย่างตามลำดับและเทียบผลลัพธ์ที่บันทึกไว้

<span id="bond-cashflows"></span>

## เริ่มจากเงินที่จะได้รับตามสัญญา

สมมติพันธบัตรมี face value หรือเงินต้นตามสัญญา 1,000 บาท อายุเหลือสามปี จ่ายคูปองปีละครั้งในอัตรา 4% ของ face value ดังนั้นได้รับคูปองปีละ 40 บาท และได้รับเงินต้น 1,000 บาทคืนพร้อมคูปองงวดสุดท้าย

| เวลาจากวันนี้ | คูปอง | คืนเงินต้น | เงินรับรวม |
|---:|---:|---:|---:|
| 1 ปี | 40 | 0 | 40 |
| 2 ปี | 40 | 0 | 40 |
| 3 ปี | 40 | 1,000 | 1,040 |

Coupon rate กำหนดเงินสดตามสัญญา ส่วนราคาที่ผู้ซื้อจ่ายวันนี้ขึ้นกับอัตราที่ตลาดต้องการและความเสี่ยงของตราสาร ถ้าคูปองคงที่ที่ 40 บาท ราคาซื้อ 900 บาทกับ 1,100 บาทย่อมให้ผลตอบแทนแก่ผู้ซื้อไม่เท่ากัน

```python
import numpy as np
import pandas as pd

face_value = 1_000.0
coupon_rate = 0.04
cashflows = pd.Series([40.0, 40.0, 1_040.0], index=[1.0, 2.0, 3.0])
cashflows.index.name = "Years from today"
print(cashflows)
print(f"Total promised cash: {cashflows.sum():,.2f}")
```

เงินรับรวมตามสัญญาเท่ากับ `1,120.00` บาท แต่ยังนำมาลบเงินซื้อแล้วเรียกว่า “ผลตอบแทนต่อปี” ไม่ได้ เพราะได้รับเงินต่างเวลา หากอยากเปรียบเทียบกับเงินวันนี้ต้องคิดลด

เราจะใช้จำนวนบาทเต็มในตัวอย่าง ไม่ใช้ราคาที่เสนอเป็นเปอร์เซ็นต์ของ face value ตัวเลขราคา 97.2768 ต่อ face 100 จึงเท่ากับราคา 972.768 บาทสำหรับ face 1,000 บาท ต้องแปลงหน่วยให้ตรงก่อนคำนวณจำนวนหน่วยซื้อ

<span id="bond-price-yield"></span>

## ราคาคือมูลค่าปัจจุบันของเงินรับทุกก้อน

ให้ $C_i$ เป็นเงินรับในอีก $t_i$ ปี และ $y$ เป็น yield ต่อปีแบบ effective ราคาในแบบจำลองคือ

$$
B(y)=\sum_i\frac{C_i}{(1+y)^{t_i}}.
$$

ตัวอย่างนี้ใช้ flat yield กับทุก cash flow เมื่อ $y=5\%$ เราหารคูปองปีแรกด้วย 1.05 หารปีที่สองด้วย $1.05^2$ และหารเงินปีสุดท้ายด้วย $1.05^3$

```python
def bond_value(flows, annual_yield):
    if annual_yield <= -1:
        raise ValueError("Annual effective yield must exceed -100%.")
    times = flows.index.to_numpy(dtype=float)
    amounts = flows.to_numpy(dtype=float)
    return float(np.sum(amounts / (1 + annual_yield) ** times))

yield_rate = 0.05
price = bond_value(cashflows, yield_rate)
print(f"Price at 5% annual effective yield: {price:,.6f}")
```

ได้ราคา 972.767520 บาท ต่ำกว่า face value 1,000 บาท เพราะคูปอง 4% ต่ำกว่า yield 5% ที่ใช้คิดลด ผู้ซื้อได้รับทั้งคูปองและส่วนต่างระหว่างราคาซื้อกับเงินต้นที่ได้รับคืนเมื่อครบกำหนด

`flows` คือ Series เงินรับ ส่วน `annual_yield` คือทศนิยมของอัตราต่อปี `return float(...)` ส่งผลรวมกลับเป็นตัวเลขหนึ่งค่า เราใส่เงื่อนไข $y>-1$ เพื่อให้ฐานการทบต้นเป็นบวก ฟังก์ชันนี้เป็นตัวอย่างสำหรับ cash flow ที่ตรวจแล้วว่าครบและเป็นตัวเลข ไม่ใช่ระบบตรวจสัญญาตราสารหนี้ทุกแบบ

```python
price_rows = []
for y in [0.03, 0.04, 0.05, 0.06, 0.07]:
    price_rows.append({"Yield": y, "Price": bond_value(cashflows, y)})
print(pd.DataFrame(price_rows).round(6))
```

ที่ yield 4% ราคาจะเท่ากับ 1,000 บาท เมื่อ yield สูงขึ้นแต่ cash flow เดิม ราคาเงินรับในอนาคตลดลง จึงทำให้ราคาพันธบัตรลดลง ส่วนเมื่อ yield ลดลงราคาจะสูงขึ้น กลไกนี้มาจากตัวหารในสูตร ไม่ต้องสมมติว่าผู้ออกเปลี่ยนคูปองตามราคาตลาด [TreasuryDirect อธิบายความสัมพันธ์ของราคา ดอกเบี้ย และ yield](https://www.treasurydirect.gov/marketable-securities/understanding-pricing/)

### Yield to maturity สรุปเงินรับหลายงวดด้วยอัตราเดียว

ถ้ารู้ราคาตลาดแล้ว เราหา yield ที่ทำให้ PV ของเงินรับเท่ากับราคานั้นได้ เรียกว่า yield to maturity หรือ YTM ในตัวอย่างที่รู้เงินรับแน่นอน YTM เป็นอัตราผลตอบแทนภายในของกระแสเงินตามสัญญา

```python
from scipy.optimize import brentq

observed_price = 972.7675197062952
recovered_yield = brentq(
    lambda y: bond_value(cashflows, y) - observed_price,
    0.0,
    0.20,
)
print(f"Yield recovered from price: {recovered_yield:.6%}")
```

ได้ 5.000000% `lambda y: ...` สร้างฟังก์ชันสั้นที่รับ yield แล้วคืนส่วนต่างระหว่างราคาคำนวณกับราคาที่กำหนด `brentq` หา yield ที่ทำให้ส่วนต่างเป็นศูนย์ภายในช่วง 0% ถึง 20% ตัวอย่างนี้เลือกช่วงที่ครอบคำตอบและมีเครื่องหมายของส่วนต่างต่างกันที่ปลายทั้งสอง

การรายงาน YTM ยังไม่รับรองว่าเงินทุกก้อนจะได้รับตามสัญญา และถ้าจะตีความว่าเงินลงทุนทั้งหมดโตทบต้นด้วย YTM จนถึงวันสุดท้าย ต้องนำคูปองที่ได้รับก่อนหน้าไปลงทุนต่อในอัตราที่สอดคล้องกันด้วย หากขายก่อนครบกำหนด ราคาขายจะขึ้นกับ yield ณ วันขาย [FINRA: Bond Yield and Return](https://www.finra.org/investors/insights/bond-yield-return)

<span id="coupon-frequency"></span>

## จ่ายคูปองบ่อยขึ้น ต้องรักษาหน่วยอัตราให้ตรง

พันธบัตร face 1,000 บาท coupon rate 4% ที่จ่ายปีละสองครั้งจะจ่ายคูปองครั้งละ 20 บาท ไม่ใช่ครั้งละ 40 บาท หากเหลือสามปี จะมีเงินรับหกงวดที่เวลา 0.5, 1.0, 1.5, 2.0, 2.5 และ 3.0 ปี

```python
def coupon_cashflows(face, coupon, maturity, frequency):
    periods = maturity * frequency
    if frequency <= 0 or not np.isclose(periods, round(periods)):
        raise ValueError("Use a positive frequency and a whole coupon schedule.")
    n = int(round(periods))
    if n < 1:
        raise ValueError("At least one payment must remain.")
    amounts = np.full(n, face * coupon / frequency)
    amounts[-1] += face
    times = np.arange(1, n + 1) / frequency
    return pd.Series(amounts, index=times)

semiannual_flows = coupon_cashflows(1_000.0, 0.04, 3, 2)
print(semiannual_flows)
```

ห้างวดแรกเป็น 20 บาท และงวดสุดท้ายเป็น 1,020 บาท `np.full(n, value)` สร้าง array ความยาว `n` ที่ทุกตำแหน่งเริ่มด้วยค่าเดียวกัน `amounts[-1] += face` เพิ่มเงินต้นเข้าเฉพาะงวดสุดท้าย ส่วน `np.arange(1, n + 1)` นับเลขงวดจาก 1 ถึง 6

ตลาดอาจเสนอ yield เป็น nominal annual yield ที่ทบต้นปีละ $m$ ครั้ง ถ้า quoted yield เท่ากับ $y_q$ อัตราต่องวดคือ $y_q/m$ และอัตราต่อปีแบบ effective คือ

$$
y_{\mathrm{eff}}=\left(1+\frac{y_q}{m}\right)^m-1.
$$

```python
quoted_yield = 0.05
frequency = 2
period_yield = quoted_yield / frequency
effective_yield = (1 + period_yield) ** frequency - 1

price_by_years = bond_value(semiannual_flows, effective_yield)
period_numbers = np.arange(1, len(semiannual_flows) + 1)
price_by_periods = np.sum(
    semiannual_flows.to_numpy() / (1 + period_yield) ** period_numbers
)
print(f"Effective annual yield: {effective_yield:.4%}")
print(f"Price using years: {price_by_years:.6f}")
print(f"Price using coupon periods: {price_by_periods:.6f}")
print(np.isclose(price_by_years, price_by_periods))
```

Nominal yield 5% ทบต้นครึ่งปีเท่ากับ effective yield 5.0625% สองวิธีให้ราคา 972.459373 บาทเท่ากัน ส่วน effective yield 5% พอดีต้องใช้อัตราครึ่งปี $(1.05)^{1/2}-1$ จึงจะตรงหน่วย การหาร 5% ด้วยสองโดยไม่ดู convention จะเปลี่ยนสมมติฐานของราคา

ตัวอย่างนี้ไม่มีงวดคูปองสั้นหรือยาวผิดปกติ หากซื้อระหว่างวันจ่ายคูปอง ต้องคำนวณ accrued interest และใช้วิธีนับวันของสัญญา Clean price เป็นราคาที่ไม่รวมดอกเบี้ยค้างรับ ส่วน dirty price รวมรายการนั้นแล้ว การใช้ราคาชนิดหนึ่งที่ต้นงวดและอีกชนิดที่ปลายงวดทำให้ total return ผิดได้

<span id="bond-total-return"></span>

## ผลตอบแทนต้องนับทั้งราคาและเงินที่จ่ายออกมา

หลังจ่ายคูปอง มูลค่าพันธบัตรส่วนที่เหลือจะไม่รวมเงินคูปองที่ผู้ถือได้รับไปแล้ว เราเรียกราคาแบบนี้ว่า ex-coupon price การคำนวณผลตอบแทนหนึ่งงวดต้องนำเงินรับระหว่างงวดกลับมารวม

$$
R_t=\frac{B_t+C_t}{B_{t-1}}-1.
$$

ในสูตรนี้ $C_t$ หมายถึงเงินรับทั้งหมดที่ปลายงวด รวมเงินคืนต้นถ้าเป็นงวดครบกำหนด หลังชำระเงินครบสัญญาแล้วตั้ง $B_T=0$ เพราะไม่มี cash flow ของพันธบัตรฉบับเดิมเหลืออยู่

```python
valuation_times = np.array([0.0, 1.0, 2.0, 3.0])
ex_coupon_prices = []
for now in valuation_times:
    future = cashflows[cashflows.index > now]
    if len(future) == 0:
        ex_coupon_prices.append(0.0)
    else:
        remaining = pd.Series(
            future.to_numpy(), index=future.index.to_numpy() - now
        )
        ex_coupon_prices.append(bond_value(remaining, yield_rate))
ex_coupon_prices = np.array(ex_coupon_prices)
payments = np.array([0.0, 40.0, 40.0, 1_040.0])
holding_returns = (
    ex_coupon_prices[1:] + payments[1:]
) / ex_coupon_prices[:-1] - 1
print(pd.DataFrame({
    "Time": valuation_times,
    "Ex-coupon price": ex_coupon_prices,
    "Payment at time": payments,
}).round(6))
print("Annual holding returns:", holding_returns.round(6))
```

ได้ holding returns `0.05, 0.05, 0.05` เมื่อ yield คงที่ 5% และรับเงินตรงเวลา งวดสุดท้ายใช้ $0+1{,}040$ เป็นมูลค่ารับ ไม่ใช้ราคา 1,040 แล้วบวกคูปอง 40 ซ้ำอีกครั้ง

โค้ดใช้ `[1:]` เลือกตั้งแต่แถวแรกหลังวันเริ่ม และ `[:-1]` เลือกทุกแถวยกเว้นแถวสุดท้าย ทำให้จำนวนตัวตั้งและตัวหารเท่ากัน เราใช้ array ซึ่งจับคู่ตามตำแหน่ง หลังจากตรวจเวลาแล้ว หากใช้ Series ที่ติด index เดิม ต้องระวัง pandas จับคู่ด้วยป้ายกำกับ

```python
terminal_with_reinvestment = 40 * 1.05 ** 2 + 40 * 1.05 + 1_040
terminal_without_interest = payments.sum()
print(f"Coupons reinvested at 5%: {terminal_with_reinvestment:,.2f}")
print(f"Coupons kept with zero interest: {terminal_without_interest:,.2f}")
print(f"Initial price compounded at 5%: {price * 1.05 ** 3:,.2f}")
```

ถ้านำคูปองไปลงทุนต่อที่ 5% เงินวันสุดท้ายรวม 1,126.10 บาท เท่ากับราคาซื้อทบต้น 5% สามปี หากพักคูปองไว้โดยไม่มีดอกเบี้ยจะรวมเพียง 1,120.00 บาท สูตร holding return บอกผลตอบแทนแต่ละงวด ส่วนการเชื่อมผลตอบแทนหลายงวดเป็นเส้น wealth ต้องบอกด้วยว่าจัดการเงินคูปองอย่างไร

<span id="macaulay-duration"></span>

## Macaulay duration เป็นเวลาเฉลี่ยที่ถ่วงด้วย PV

พันธบัตรสามปีในตัวอย่างเริ่มคืนเงินบางส่วนตั้งแต่ปีแรก อายุครบกำหนดสามปีจึงต่างจากเวลาเฉลี่ยของเงินรับ เราคิดน้ำหนักของแต่ละงวดจาก PV ของเงินงวดนั้นหารด้วยราคาพันธบัตร

$$
w_i=\frac{C_i/(1+y)^{t_i}}{B(y)},\qquad
D_{\mathrm{Mac}}=\sum_i w_i t_i.
$$

น้ำหนักรวมเท่ากับหนึ่ง และเมื่อ $t_i$ วัดเป็นปี duration ก็มีหน่วยปี สูตรไม่ได้ถามว่าใช้เวลากี่ปีจึงได้เงินสดสะสมคืนเท่าราคาซื้อ แต่เป็นค่าเฉลี่ยวันรับเงินโดยใช้มูลค่าวันนี้เป็นน้ำหนัก

```python
times = cashflows.index.to_numpy()
discounted_cash = cashflows.to_numpy() / (1 + yield_rate) ** times
pv_weights = discounted_cash / discounted_cash.sum()
macaulay = np.sum(times * pv_weights)
print(pd.DataFrame({
    "Years": times,
    "PV": discounted_cash,
    "PV weight": pv_weights,
    "Weighted years": times * pv_weights,
}).round(6))
print(f"Weight sum: {pv_weights.sum():.6f}")
print(f"Macaulay duration: {macaulay:.6f} years")
```

ได้ 2.884380 ปี ซึ่งสั้นกว่าอายุสามปีเล็กน้อย เพราะมีเงินรับปีแรกและปีที่สองด้วย สำหรับ ZCB ที่จ่ายเพียงครั้งเดียวในอีกห้าปี น้ำหนักทั้งหมดอยู่ปีที่ห้า Macaulay duration จึงเท่ากับห้าปี

<span id="modified-duration"></span>

## Modified duration ใช้ประมาณการเปลี่ยนราคา

สำหรับ yield ต่อปีแบบ effective ในสูตรที่ใช้อยู่ การหาอนุพันธ์ของราคาทำให้ได้

$$
D_{\mathrm{mod}}=\frac{D_{\mathrm{Mac}}}{1+y},\qquad
\frac{\Delta B}{B}\approx-D_{\mathrm{mod}}\Delta y.
$$

ตัวอย่างนี้ modified duration เท่ากับประมาณ 2.747028 หาก yield เพิ่ม 0.1 percentage point จาก 5% เป็น 5.1% ต้องใช้ $\Delta y=0.001$ จึงประมาณว่าราคาลดลงประมาณ 0.2747%

```python
modified = macaulay / (1 + yield_rate)
yield_change = 0.001
approximate_change = -modified * yield_change
new_price = bond_value(cashflows, yield_rate + yield_change)
actual_change = new_price / price - 1
print(f"Modified duration: {modified:.6f}")
print(f"Approximate price change: {approximate_change:.4%}")
print(f"Actual repriced change: {actual_change:.4%}")
```

ราคาเมื่อคำนวณใหม่ลด 0.2742% ใกล้กับค่าประมาณ −0.2747% ความต่างเกิดจากเส้นราคาต่อยีลด์โค้ง ส่วน duration ใช้เส้นตรงประมาณใกล้จุดเดิม ถ้าขยับ yield มากขึ้น ความคลาดเคลื่อนอาจเพิ่มขึ้น จึงต้อง reprice ด้วย cash flow หรือใช้ convexity ช่วยเมื่อเหมาะสม

กรณี yield เป็น nominal annual ที่ทบต้น $m$ ครั้งต่อปี ความไวต่อ quoted yield จะเป็น $D_{\mathrm{Mac}}/(1+y_q/m)$ เมื่อ Macaulay วัดเป็นปี ต้องระบุให้ครบว่ากำลังขยับ yield ชนิดใด การเปลี่ยน convention แล้วใช้ duration ตัวเดิมอาจทำให้หน่วยไม่ตรง [CFA Institute อธิบาย money duration และการจับคู่ภาระ](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/liability-driven-index-based-strategies)

<span id="duration-matching"></span>

## จับคู่มูลค่าและ Duration ของภาระห้าปี

สมมติต้องจ่าย 100,000 บาทในอีกห้าปี และเส้นอัตราแบนที่ effective yield 5% มูลค่าภาระวันนี้เท่ากับ 78,352.62 บาท มี ZCB อายุสองปีและแปดปีให้ใช้ เราต้องการน้ำหนักตามมูลค่าตลาด $w$ ในตราสารสองปี และ $1-w$ ในตราสารแปดปี

$$
2w+8(1-w)=5\quad\Rightarrow\quad w=0.5.
$$

แบ่งเงิน PV ของภาระครึ่งหนึ่งซื้อ ZCB สองปี และอีกครึ่งซื้อ ZCB แปดปี จำนวน face value ที่ได้รับเมื่อครบกำหนดจะไม่เท่ากัน เพราะราคาต่อเงินครบกำหนด 1 บาทต่างกัน

```python
goal_amount = 100_000.0
goal_time = 5.0
base_yield = 0.05
goal_pv = goal_amount / (1 + base_yield) ** goal_time
short_time, long_time = 2.0, 8.0
short_weight = (long_time - goal_time) / (long_time - short_time)
short_face = goal_pv * short_weight * (1 + base_yield) ** short_time
long_face = goal_pv * (1 - short_weight) * (1 + base_yield) ** long_time

print(f"Liability PV: {goal_pv:,.6f}")
print(f"Short-bond market-value weight: {short_weight:.2%}")
print(f"Short bond face: {short_face:,.6f}")
print(f"Long bond face: {long_face:,.6f}")
print(f"Portfolio Macaulay duration: {short_weight * 2 + (1-short_weight) * 8:.2f}")
```

ได้ราคาเริ่ม 78,352.616647 บาท น้ำหนัก 50%/50% และ duration ห้าปีเหมือนภาระ เงื่อนไข PV เท่ากันทำให้จำนวนบาทที่เปลี่ยนจากการขยับ yield เล็กน้อยใกล้กันด้วย หากใช้พอร์ตที่ duration ห้าปีแต่ใส่เงินเพียงครึ่งหนึ่งของ PV ภาระ ความไวคิดเป็นบาทก็เหลือเพียงครึ่งเดียว

```python
matching_rows = []
for y in [0.03, 0.04, 0.05, 0.06, 0.07]:
    liability = goal_amount / (1 + y) ** goal_time
    assets = short_face / (1 + y) ** short_time + long_face / (1 + y) ** long_time
    matching_rows.append({
        "Yield": y,
        "Matched assets": assets,
        "Liability PV": liability,
        "Matched funding ratio": assets / liability,
        "Cash funding ratio": goal_pv / liability,
    })
matching_results = pd.DataFrame(matching_rows)
print(matching_results.round(6).to_string(index=False))
```

| Yield หลังขยับทั้งเส้น | PV สินทรัพย์จับคู่ | PV ภาระ | Funding ratio |
|---:|---:|---:|---:|
| 3% | 86,404.48 | 86,260.88 | 100.1665% |
| 4% | 82,226.58 | 82,192.71 | 100.0412% |
| 5% | 78,352.62 | 78,352.62 | 100.0000% |
| 6% | 74,756.03 | 74,725.82 | 100.0404% |
| 7% | 71,412.88 | 71,298.62 | 100.1603% |

ผลไม่ได้เท่ากับ 100% ทุกช่อง พอร์ตเงินรับสองจุดมีความโค้งของราคาในตัวอย่างนี้มากกว่าเงินรับจุดเดียวของภาระ การเปรียบเทียบนี้เกิด ณ วันเดียวกัน โดยยังไม่ปล่อยให้เวลาผ่าน ยังไม่ถือเงินที่ครบกำหนดสองปีไปลงทุนต่อ และยังไม่ขายตราสารแปดปีในปีที่ห้า

<figure class="course-figure">
<picture>
<source media="(max-width: 600px)" srcset="assets/charts/course-duration-mobile.svg">
<img src="assets/charts/course-duration.svg" alt="Funding ratio ของพอร์ตจับคู่ Duration เทียบกับเงินสด เมื่อ Yield เลื่อนพร้อมกันจาก 3 ถึง 7 เปอร์เซ็นต์" loading="lazy" width="720" height="560">
</picture>
<figcaption>ข้อมูลสมมติจากตัวอย่างเดียวกัน: ทั้งสองพอร์ตเริ่มด้วยเงินเท่ากับ PV ของภาระ 100,000 บาทในอีกห้าปีที่ yield 5% พอร์ต ZCB อายุสองและแปดปีแบ่ง PV เท่ากันจึงมี Macaulay duration ห้าปี เส้นที่อยู่ใกล้ 100% แสดงผลของการจับคู่ภายใต้การเลื่อน yield พร้อมกัน; กราฟนี้ยังไม่รวมการเปลี่ยนรูปทรงเส้นอัตราดอกเบี้ย</figcaption>
</figure>

<span id="matching-limits"></span>

## Duration เท่ากันยังไม่ทำให้ cash flow ตรงกัน

ตราสารสองปีคืนเงินก่อนวันจ่ายเป้าหมายสามปี เราต้องลงทุนเงินนั้นต่อ ส่วนตราสารแปดปียังไม่ครบกำหนดในวันที่ต้องจ่ายปีที่ห้า จึงต้องขายบางส่วนหรือจัดกระแสเงินวิธีอื่น การจับคู่ duration ลดความไวเฉพาะรูปแบบที่แบบจำลองกำหนด และต้องติดตามปรับพอร์ตเมื่อเวลาและอัตราเปลี่ยน

ถ้าเส้นอัตราไม่ได้ขยับขนานกัน การจับคู่ด้วย duration ตัวเดียวอาจไม่ครอบคลุม ลองให้ yield สองปีและห้าปียังคง 5% แต่ yield แปดปีเพิ่มเป็น 7%

```python
twisted_assets = short_face / 1.05 ** 2 + long_face / 1.07 ** 8
twisted_liability = goal_amount / 1.05 ** 5
print(f"Assets after curve twist: {twisted_assets:,.2f}")
print(f"Funding ratio after curve twist: {twisted_assets / twisted_liability:.4%}")
```

สินทรัพย์เหลือ 72,863.72 บาท และ funding ratio ลดเป็น 92.9946% เพราะตราสารแปดปีลดราคา ขณะที่ PV ของภาระห้าปีไม่เปลี่ยน การจัดการเส้นอัตราหลายช่วงอาจใช้ key-rate durations หรือจับคู่ cash flow ละเอียดขึ้น การใช้ตราสารหลายอายุอย่างเดียวไม่ได้รับรองว่าจับคู่ความเสี่ยงเหล่านี้แล้ว

ยังมีความเสี่ยงจากการผิดนัด การเปลี่ยน credit spread สภาพคล่อง การไถ่ถอนก่อนกำหนด และจำนวนภาระที่เปลี่ยน หาก cash flow เปลี่ยนตามดอกเบี้ย เช่น พันธบัตร callable สูตร duration ของ cash flow คงที่ในบทนี้ต้องปรับ วิธีคำนวณที่เหมาะสมจะต้อง reprice ภายใต้เงื่อนไขสัญญาใหม่ด้วย

<span id="bond-duration-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

1. Face value 1,000 บาท coupon rate 6% จ่ายครึ่งปี คูปองต่องวดเป็นเท่าไร?
2. ZCB จ่าย 1,000 บาทในอีกสองปี yield effective 4% ราคาและ Macaulay duration เท่าไร?
3. Modified duration เท่ากับ 6 ถ้า yield ขึ้น 0.25 percentage point ราคาจะเปลี่ยนประมาณกี่เปอร์เซ็นต์?
4. ต้องการ duration สี่ปีจาก ZCB สองปีกับหกปี ควรใช้สัดส่วนมูลค่าตลาดเท่าไร?
5. พันธบัตรถึงวันครบกำหนดและจ่ายเงินต้นพร้อมคูปองแล้ว เหตุใดจึงไม่ควรเก็บเงินต้นไว้ทั้งในราคาปลายงวดและใน cash payment?
6. หาก matching ด้วย duration ทำให้พอร์ตได้ผลดีเมื่ออัตราทุกอายุขยับพร้อมกัน แปลว่าป้องกันการ steepen ของเส้นอัตราแล้วหรือไม่?

<details>
<summary>เปิดวิธีคำนวณและตรวจหน่วย</summary>

ข้อ 1 คูปองเท่ากับ $1{,}000(0.06)/2=30$ บาทต่องวด ข้อ 2 ราคา $1{,}000/1.04^2\approx924.56$ บาท และ Macaulay duration สองปี ส่วน modified duration ต่อ effective yield เท่ากับ $2/1.04\approx1.9231$

ข้อ 3 ใช้ $\Delta y=0.0025$ จึงประมาณ $-6(0.0025)=-1.5\%$ ข้อ 4 แก้ $2w+6(1-w)=4$ ได้ $w=0.5$ แล้วต้องใส่เงินรวมให้ PV สอดคล้องกับภาระด้วย

ข้อ 5 การนับทั้งสองแห่งทำให้เงินรับเกินจริง หลังชำระครบสัญญา ex-coupon price เป็นศูนย์ เงินต้นและคูปองอยู่ใน cash payment ครั้งเดียว ข้อ 6 ยังสรุปไม่ได้ เพราะอัตราต่างอายุอาจขยับต่างทิศหรือคนละขนาด ต้องทดสอบรูปแบบ curve change นั้นโดยตรง

</details>

<span id="bond-duration-sources"></span>

## แหล่งเรียนและการอ่าน Lab

ต้นทางคือหัวข้อ [Liability hedging portfolios](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/JT5zQ/liability-hedging-portfolios), [Lab Session–Liability driven investing](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/1CUzi/lab-session-liability-driven-investing) และ [Lab Session–Monte Carlo simulation of coupon-bearing bonds using CIR](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/nQUCQ/lab-session-monte-carlo-simulation-of-coupon-bearing-bonds-using-cir) ประกอบ `lab_126.ipynb` และ `lab_127.ipynb` ที่อ่านในเครื่อง

Lab ใช้เลขงวดคูปองในบางฟังก์ชัน และใช้อัตราต่องวด จึงต้องแปลง duration จากจำนวนงวดเป็นปีให้ตรงความหมาย ส่วนตัวอย่างหน้านี้ใช้เวลาเป็นปีและระบุ effective yield เป็นหลัก นอกจากนี้เรากำหนดราคาหลังชำระครบสัญญาให้เป็นศูนย์แล้วบันทึกเงินคืนต้นใน cash payment เพื่อป้องกันการนับเงินก้อนสุดท้ายซ้ำ
