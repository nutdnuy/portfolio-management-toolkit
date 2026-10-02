---
title: จัดพอร์ตให้สอดคล้องกับเป้าหมาย
description: เปรียบเทียบ Fixed mix, Glide path และ Dynamic floor จากราคาเป้าหมายต้นงวด พร้อมวัดโอกาสและขนาดเงินขาดจากทุกเส้นทาง
---

# จัดพอร์ตให้สอดคล้องกับเป้าหมาย

<p class="lead">มีเงินวันนี้ 100,000 บาทและต้องใช้ 100,000 บาทในอีกห้าปี จะกันเงินให้เป้าหมายเท่าไร และนำส่วนใดไปรับความเสี่ยงเพื่อให้มีเงินเหลือเพิ่ม?</p>

เมื่อระบุจำนวนเงินและวันใช้แล้ว เราคำนวณต้นทุนของพอร์ตที่รองรับเป้าหมายได้ การจัดสรรที่เหลือขึ้นกับความเสี่ยงที่ยอมรับ เงินที่เติมได้ และความยืดหยุ่นของเป้าหมาย บทนี้เปรียบเทียบกติกาสามแบบด้วยสถานการณ์สมมติเดียวกัน แล้วแยกให้เห็นว่าขาดเป้าบ่อยเพียงใดและขาดมากแค่ไหน

เนื้อหาต่อจาก [เงินลงทุนกับเป้าหมาย](asset-liability.html) และ [ราคา ZCB](interest-rate-models.html#cir-zero-coupon-price) แต่โค้ดเริ่มใหม่ทั้งหมด รันตามลำดับใน Notebook ใหม่ได้ด้วย NumPy และ pandas ตัวเลขจำลองมีไว้ศึกษากติกา ไม่มีการประมาณพารามิเตอร์จากสินทรัพย์จริง

[ดาวน์โหลด Notebook ของบทนี้](notebooks/goal-based-allocation.ipynb) เพื่อรันตัวอย่างตามลำดับและเทียบผลลัพธ์ที่บันทึกไว้

<span id="goal-policy"></span>

## ตั้งเป้าหมายและงบความเสี่ยงก่อนเลือกสัดส่วน

Performance-seeking portfolio หรือ PSP คือส่วนที่หวังให้เงินโต และ goal-hedging portfolio หรือ GHP คือส่วนที่เลือกให้มูลค่าเคลื่อนไหวสอดคล้องกับต้นทุนเป้าหมาย ถ้าเป้าหมายจ่ายเงินบาทจำนวนแน่นอนในวันเดียว ZCB ที่จ่ายตรงวันนั้นเป็น GHP ในแบบจำลองที่ไม่มีผิดนัดและซื้อได้ตามต้องการ สำหรับเงินใช้ที่เพิ่มตามเงินเฟ้อหรือมีหลายวันจ่าย ต้องออกแบบ GHP ใหม่ตามภาระเหล่านั้น

เราสมมติเป้าหมาย 100,000 บาทในอีกห้าปีและอัตราผลตอบแทน effective คงที่ 3% ต่อปี ต้นทุนซื้อเงินครบกำหนดตามเป้าหมายวันนี้คือ

$$
L_0=\frac{100{,}000}{1.03^5}\approx86{,}260.88\text{ บาท}.
$$

ถ้าซื้อ GHP รองรับครบเป้าหมายทันที เงินจากทุนเริ่ม 100,000 บาทจะเหลือ 13,739.12 บาทสำหรับ PSP การซื้อให้ครบนี้ต้องเข้าถึงพันธบัตรตรงอายุในราคาที่สมมติ หากย้ายเงินจากส่วนรองรับเป้าหมายไปเสี่ยงเพิ่ม ต้องยอมรับโอกาสมีเงินไม่พอด้วย

```python
import numpy as np
import pandas as pd

initial_wealth = 100_000.0
terminal_goal = 100_000.0
years = 5
annual_safe_yield = 0.03
initial_goal_cost = terminal_goal / (1 + annual_safe_yield) ** years
initial_cushion = initial_wealth - initial_goal_cost
print(f"Cost of matching the goal: {initial_goal_cost:,.2f}")
print(f"Wealth above that cost: {initial_cushion:,.2f}")
print(f"Initial funding ratio: {initial_wealth / initial_goal_cost:.6f}")
```

ได้ 86,260.88 บาท, 13,739.12 บาท และ funding ratio 1.159274 ตามลำดับ คำว่า cushion หมายถึงส่วนที่เงินลงทุนสูงกว่า floor ที่กำหนด ถ้า floor คือ PV เป้าหมาย cushion จึงวัดส่วนเกินจากต้นทุนของเป้าหมาย ณ ขณะนั้น

ก่อนกำหนดกติกา เจ้าของเงินต้องตัดสินใจว่าเงินก้อนนี้จำเป็นเพียงใด ถ้าขาดจะเลื่อนวันใช้ ลดจำนวน หรือเติมเงินได้หรือไม่ ตัวอย่างเช่น ผู้ที่เติมได้ปีละ 10,000 บาทมีทางปรับแผนต่างจากผู้ที่เติมไม่ได้ ความพอใจต่อผลตอบแทนเฉลี่ยเพียงอย่างเดียวยังไม่บอกว่าจะรับเงินขาดปลายทางเท่าไรได้

การตั้ง expected return ให้สูงขึ้นในตารางไม่สร้างเงินเพิ่ม เช่นเดียวกับการใช้อัตราคิดลดสูงเพื่อให้ PV ภาระดูต่ำลง หากอัตรานั้นไม่ใช่ต้นทุนของสินทรัพย์ที่รองรับภาระจริง แผนอาจดู fully funded ทั้งที่ยังซื้อเงินให้ครบวันใช้ไม่ได้ แนวคิดเรื่องนโยบายลงทุนในคอร์สเชื่อม risk budget เข้ากับ contribution budget จึงต้องคุยเรื่องการเติมเงินควบคู่กับสัดส่วน PSP

<span id="fixed-mix"></span>

## Fixed mix ใช้สัดส่วนเดิมทุกครั้งที่ปรับพอร์ต

สมมติกำหนด PSP 60% และ GHP 40% ตอนต้นทุกเดือน หลังสินทรัพย์ให้ผลตอบแทน สัดส่วนจะเปลี่ยน เดือนถัดไปจึงซื้อขายให้กลับมา 60/40 กติกานี้เรียกว่า constant mix หรือ fixed mix แบบปรับพอร์ตตามงวด

ถ้ารู้ผลตอบแทน PSP และ GHP ในงวดนั้นแล้ว ผลตอบแทนพอร์ตคำนวณจากน้ำหนักที่เลือกก่อนเริ่มงวด

$$
R_{W,t}=w_tR_{P,t}+(1-w_t)R_{G,t},\qquad
W_{t+1}=W_t(1+R_{W,t}).
$$

ให้ $W_t$ เป็นเงินก่อนงวด $t$, $w_t$ เป็นสัดส่วน PSP ที่ใช้ตลอดงวดนั้น, $R_P$ และ $R_G$ เป็น simple returns ของแต่ละส่วน น้ำหนักต้องไม่ใช้ผลตอบแทนของงวดที่ยังไม่เกิดในการตัดสินใจ

เริ่มจากตัวอย่างสองงวดที่คำนวณด้วยมือได้ PSP ได้ +10% แล้ว −10% ส่วน GHP ได้ 0% ทั้งสองงวด หาก rebalancing เป็น 60/40 ทุกครั้ง เงิน 100 บาทจะโตเป็น 106 แล้วลดเหลือ $106(1-0.06)=99.64$ บาท

```python
toy_psp = np.array([0.10, -0.10])
toy_ghp = np.array([0.0, 0.0])
toy_weight = 0.60
toy_mixed_returns = toy_weight * toy_psp + (1 - toy_weight) * toy_ghp
toy_rebalanced = 100 * np.prod(1 + toy_mixed_returns)
toy_buy_and_hold = 60 * np.prod(1 + toy_psp) + 40 * np.prod(1 + toy_ghp)
print(f"Rebalance each period: {toy_rebalanced:.2f}")
print(f"Buy and hold original units: {toy_buy_and_hold:.2f}")
```

ได้ 99.64 บาทกับ 99.40 บาท buy and hold เก็บหน่วยที่ซื้อเริ่มต้นไว้ จึงปล่อยน้ำหนักเปลี่ยนตามราคา การกล่าวว่า “พอร์ต 60/40” ต้องบอกด้วยว่าตั้งสัดส่วนครั้งเดียวหรือปรับกลับเมื่อใด ผลต่างในตัวอย่างนี้ไม่ได้พิสูจน์ว่า rebalancing ชนะทุกเส้นทาง ถ้า PSP ขึ้นต่อเนื่อง การขายส่วนที่ขึ้นกลับมาที่ 60% อาจทำให้เงินน้อยกว่าการถือหน่วยเดิม

<span id="goal-scenarios"></span>

## สร้างชุดสถานการณ์เดียวเพื่อเทียบกติกา

เราจะสร้างผลตอบแทน PSP จาก GBM สมมติ 2,000 เส้นทาง นานห้าปีเป็นรายเดือน กำหนด drift ของราคาต่อปี 7% และ volatility 20% ผลตอบแทนอย่างง่ายรายเดือนคำนวณจาก

$$
R_{P,t}=\exp\left[(\mu-\tfrac12\sigma^2)\Delta t
+\sigma\sqrt{\Delta t}\,Z_t\right]-1.
$$

ค่า $\mu=0.07$ เป็น drift ของราคาใน GBM ทำให้ผลตอบแทนคาดหมายหนึ่งปีเป็น $e^{0.07}-1\approx7.2508\%$ ไม่ใช่ 7% พอดี เรากำหนดพารามิเตอร์นี้เป็นสมมติฐาน real-world สำหรับการทดลอง ส่วน $Z_t$ เป็น Normal มาตรฐานอิสระตามเวลาและข้ามเส้นทาง โมเดลนี้ยังไม่มีเหตุการณ์กระโดด วิกฤตเปลี่ยน regime ค่าธรรมเนียม หรือภาษี

GHP เป็น ZCB อายุครบตรงห้าปี ใช้อัตรา effective คงที่ 3% จึงมีราคา $P(t,T)=1.03^{-(T-t)}$ บาทต่อเงินครบกำหนด 1 บาท ในการทดลองนี้ GHP ให้ผลตอบแทนแต่ละเดือนคงที่ หากต้องการดอกเบี้ยสุ่ม สามารถต่อยอดด้วยเส้นราคาใน [บท CIR](interest-rate-models.html) โดยต้องเลือก measure ของสถานการณ์ให้เหมาะกับงาน

```python
steps_per_year = 12
steps = years * steps_per_year
paths = 2_000
dt = 1 / steps_per_year
mu, volatility = 0.07, 0.20
rng = np.random.default_rng(20261005)
shocks = rng.standard_normal((steps, paths))
psp_returns = np.expm1(
    (mu - 0.5 * volatility ** 2) * dt
    + volatility * np.sqrt(dt) * shocks
)
times = np.arange(steps + 1) * dt
single_zc_path = (1 + annual_safe_yield) ** -(years - times)
goal_prices = np.repeat(single_zc_path[:, None], paths, axis=1)
ghp_returns = goal_prices[1:] / goal_prices[:-1] - 1
print("Return array:", psp_returns.shape)
print("ZCB state array:", goal_prices.shape)
print(f"Monthly GHP return: {ghp_returns[0, 0]:.6%}")
print("Final ZCB price is one:", np.allclose(goal_prices[-1], 1))
```

ผลตอบแทนมี 60 แถว × 2,000 เส้นทาง แต่ราคามี 61 แถว เพราะรวมสถานะเริ่มต้นก่อนงวดแรก ผลตอบแทน GHP ต่อเดือนประมาณ 0.246627% และราคาปลายทางเท่ากับ 1 ทุกคอลัมน์ `np.repeat(..., axis=1)` ทำสำเนาเส้นราคาเดียวกันให้ครบทุกเส้นทาง ส่วน PSP ต่างกันตาม shock ที่สุ่ม

โค้ดต่อไปเป็นตัวช่วยคำนวณมูลค่าสำหรับน้ำหนักที่กำหนดไว้ล่วงหน้า `weights` ต้องมีหนึ่งแถวต่อช่วงผลตอบแทน และหนึ่งคอลัมน์ต่อเส้นทาง การใช้ `axis=0` สะสมผลตอบแทนลงตามเวลา โดยคงแต่ละเส้นทางแยกกัน

```python
def wealth_with_weights(psp, ghp, weights, initial):
    psp = np.asarray(psp, dtype=float)
    ghp = np.asarray(ghp, dtype=float)
    weights = np.broadcast_to(np.asarray(weights, dtype=float), psp.shape)
    if psp.ndim != 2 or ghp.shape != psp.shape:
        raise ValueError("Returns must be two-dimensional arrays of the same shape.")
    if initial <= 0 or not all(np.all(np.isfinite(x)) for x in (psp, ghp, weights)):
        raise ValueError("Use positive initial wealth and finite returns.")
    if np.any(psp < -1) or np.any(ghp < -1) or np.any((weights < 0) | (weights > 1)):
        raise ValueError("This example uses unlevered weights and returns of at least -100%.")
    mixed = weights * psp + (1 - weights) * ghp
    return np.vstack([
        np.full((1, psp.shape[1]), initial),
        initial * np.cumprod(1 + mixed, axis=0),
    ])

fixed_weights = np.full(psp_returns.shape, 0.60)
fixed_wealth = wealth_with_weights(psp_returns, ghp_returns, fixed_weights, initial_wealth)
print("Wealth including initial row:", fixed_wealth.shape)
print("Initial wealth correct:", np.allclose(fixed_wealth[0], initial_wealth))
```

ได้มูลค่าขนาด 61 × 2,000 และผลตรวจแถวเริ่มเป็น `True` ฟังก์ชันนี้ถือว่า rebalancing ทำได้ที่ขอบงวดโดยไม่มีต้นทุน ถ้ามีค่าซื้อขายต้องหักจาก wealth ตามปริมาณที่ซื้อขายจริง การคูณผลตอบแทนอย่างเดียวจะยังไม่สะท้อนต้นทุนนั้น

<span id="glide-path"></span>

## Glide path ลดสัดส่วนตามปฏิทิน

Glide path กำหนดน้ำหนัก PSP ให้ลดลงเมื่อใกล้วันใช้เงิน ตัวอย่างนี้ใช้ 80% ในเดือนแรกแล้วลดเป็นเส้นตรงจนถึง 20% ในเดือนสุดท้าย เส้นทางเงินที่รุ่งขึ้นหรือขาดทุนยังได้รับน้ำหนักตามเดือนเดียวกัน เพราะกติกาไม่ได้อ่านยอดเงินที่เกิดจริง

```python
glide_weights_one_path = np.linspace(0.80, 0.20, steps)
glide_weights = np.repeat(glide_weights_one_path[:, None], paths, axis=1)
glide_wealth = wealth_with_weights(
    psp_returns, ghp_returns, glide_weights, initial_wealth,
)
print(f"Weight used during first month: {glide_weights[0, 0]:.0%}")
print(f"Weight used during last month: {glide_weights[-1, 0]:.0%}")
print("Same calendar weights in every scenario:", np.allclose(
    glide_weights[:, 0], glide_weights[:, -1]
))
```

ได้ 80%, 20% และ `True` `np.linspace(start, stop, steps)` รวมทั้งค่าเริ่มและค่าสุดท้าย กติกานี้จึงมีน้ำหนัก 60 ค่าใช้กับ 60 ช่วง ไม่มีน้ำหนักซื้อขายเพิ่มหลังวันใช้เงินที่เวลา 5 ปี

การลด PSP ตามอายุของแผนอาจลดความเสี่ยงปลายทางบางส่วน แต่ไม่ได้ตอบสนองต่อการขาดเป้าหมายในแต่ละเส้นทาง ถ้าขาดทุนหนักตั้งแต่ต้น การลด PSP ตามตารางอาจล็อกโอกาสฟื้นตัวไว้ต่ำ ในทางกลับกัน การเพิ่ม PSP เพื่อเร่งให้ทันเป้าหมายก็เพิ่มโอกาสขาดหนักกว่าเดิม การเปรียบเทียบต้องดูทั้งความถี่และขนาดของ shortfall ภายใต้สมมติฐานเดียวกัน

<span id="dynamic-goal-floor"></span>

## Dynamic floor อ่านเงินที่มีและต้นทุนเป้าหมายทุกงวด

ให้ floor ณ ต้นงวด $t$ เป็นต้นทุนซื้อเงินปลายทางตามเป้าหมาย $G$:

$$
F_t=G P(t,T),\qquad C_t=\max(W_t-F_t,0).
$$

กำหนดจำนวนเงิน PSP เป็น $E_t=\min(mC_t,W_t)$ และน้ำหนัก PSP เป็น $w_t=E_t/W_t$ เมื่อ $W_t>0$ ตัวคูณ $m$ หรือ multiplier ขยายจำนวนเงินที่เปิดรับความเสี่ยงจาก cushion โดยตัวอย่างใช้ $m=3$ และจำกัดน้ำหนักไว้ระหว่าง 0 ถึง 1

จากเงินเริ่ม 100,000 บาทและ floor 86,260.88 บาท มี cushion 13,739.12 บาท ดังนั้นเปิด PSP $3\times13{,}739.12=41{,}217.36$ บาท หรือ 41.2174% ที่เหลือซื้อ GHP เมื่อ PSP ขาดทุน cushion มักลดและกติกาจึงลดจำนวนเงิน PSP เมื่อมีส่วนเกินมากขึ้นก็มักเพิ่ม PSP ภายในเพดาน

คำว่า floor ในสูตรคือระดับอ้างอิงของกติกา การซื้อขายเป็นรายเดือนอาจไม่ทันการตกแรงระหว่างงวด จึงไม่ใช่สัญญารับประกันว่ามูลค่าจะไม่ต่ำกว่าระดับนี้ บท [Portfolio insurance](portfolio-insurance.html) อธิบาย cushion และ gap risk เพิ่มเติม

```python
def wealth_with_goal_floor(psp, ghp, zc_states, goal, initial, multiplier):
    if psp.shape != ghp.shape or zc_states.shape != (psp.shape[0] + 1, psp.shape[1]):
        raise ValueError("Need N return rows and N+1 ZCB state rows.")
    if goal <= 0 or initial <= 0 or multiplier < 0:
        raise ValueError("Use positive goal and wealth, and a nonnegative multiplier.")
    if np.any(zc_states <= 0) or not np.all(np.isfinite(zc_states)):
        raise ValueError("ZCB prices must be finite and positive.")
    if not np.allclose(1 + ghp, zc_states[1:] / zc_states[:-1]):
        raise ValueError("The GHP returns must match the ZCB used for the floor.")
    if not np.all(np.isfinite(psp)) or np.any(psp < -1):
        raise ValueError("Use finite unlevered PSP returns.")
    wealth = np.empty_like(zc_states, dtype=float)
    weights = np.empty_like(psp, dtype=float)
    wealth[0] = initial
    for step in range(psp.shape[0]):
        floor_now = goal * zc_states[step]
        cushion = np.maximum(wealth[step] - floor_now, 0)
        risky_amount = np.minimum(multiplier * cushion, wealth[step])
        weights[step] = np.divide(
            risky_amount, wealth[step],
            out=np.zeros_like(risky_amount), where=wealth[step] > 0,
        )
        wealth[step + 1] = (
            risky_amount * (1 + psp[step])
            + (wealth[step] - risky_amount) * (1 + ghp[step])
        )
    return wealth, weights

dynamic_wealth, dynamic_weights = wealth_with_goal_floor(
    psp_returns, ghp_returns, goal_prices,
    terminal_goal, initial_wealth, multiplier=3,
)
print(f"First PSP weight: {dynamic_weights[0, 0]:.6%}")
print("All weights between zero and one:", np.all(
    (dynamic_weights >= 0) & (dynamic_weights <= 1)
))
```

ได้ 41.217365% และ `True` ในลูป `zc_states[step]` กับ `wealth[step]` เป็นข้อมูลต้นงวดที่มีอยู่ตอนตัดสินใจ ส่วน `psp[step]` และ `ghp[step]` เป็นผลตอบแทนที่จะเกิดระหว่างงวดนั้น หากนำราคา ZCB ของแถว `step + 1` มาใช้กำหนดน้ำหนักต้นงวด จะใช้ข้อมูลอนาคต กรณีดอกเบี้ยคงที่อาจไม่เห็นผลเสียชัด แต่เมื่อดอกเบี้ยสุ่มจะทำให้การทดลองไม่ตรงกับสิ่งที่ทำได้จริง

ฟังก์ชันตรวจว่า GHP ให้ผลตอบแทนตรงกับ ZCB ที่ใช้สร้าง floor ด้วย ถ้าใช้เงินสดอายุสั้นเป็น GHP แต่ floor อิง ZCB ระยะยาว สินทรัพย์อาจเคลื่อนไหวไม่ตรงกับภาระ โดยเฉพาะเมื่ออัตราดอกเบี้ยเปลี่ยน ความปลอดภัยของเงินต้นระยะสั้นจึงไม่ได้ตอบคำถามว่ารองรับเป้าหมายระยะยาวได้เท่าใด

<span id="goal-gap-risk"></span>

## การตกแรงหนึ่งงวดทำให้หลุด Floor ได้อย่างไร

ใช้ตัวเลขเล็กเพื่อเห็นกลไกชัด เริ่ม 100 บาท floor 80 บาท multiplier 3 และดอกเบี้ยศูนย์ จะมี PSP 60 บาทกับ GHP 40 บาท หาก PSP ลด 40% ก่อนถึงครั้งปรับถัดไป จะเหลือ $60(0.60)+40=76$ บาท ต่ำกว่า floor สี่บาท

```python
gap_psp = np.array([[-0.40]])
gap_ghp = np.array([[0.0]])
gap_prices = np.ones((2, 1))
gap_wealth, gap_weights = wealth_with_goal_floor(
    gap_psp, gap_ghp, gap_prices,
    goal=80, initial=100, multiplier=3,
)
print(f"Initial PSP amount: {100 * gap_weights[0, 0]:.2f}")
print(f"Wealth after the gap: {gap_wealth[-1, 0]:.2f}")
print(f"Goal deficit: {max(80 - gap_wealth[-1, 0], 0):.2f}")
```

ได้ 60, 76 และ 4 บาท กติกาอาจลด PSP เป็นศูนย์ในงวดถัดไป แต่การลดนั้นไม่คืนเงินที่ขาดไปแล้ว หาก GHP ตรงกับภาระ เงินส่วนที่เหลือจะรักษาสัดส่วนที่ต่ำกว่าเป้าหมายไว้ เมื่อไม่มีเงินเติมจึงอาจติดอยู่กับเงินไม่พอหรือเกิด cash lock

ให้ $S_t=W_t-F_t$ เป็นส่วนเกินแบบมีเครื่องหมาย ซึ่งติดลบได้ ต่างจาก cushion ที่กำหนด $C_t=\max(S_t,0)$ สำหรับงวดที่เริ่มด้วย $S_t>0$ และจำนวนเงิน PSP เท่ากับ $mS_t$ โดยยังไม่ติดเพดานน้ำหนัก จะได้

$$
S_{t+1}=S_t\left[(1+R_{G,t})+m(R_{P,t}-R_{G,t})\right].
$$

สูตรนี้ใช้ว่า floor โตตาม GHP ที่ match กัน จะหลุด floor ถ้าพจน์ในวงเล็บติดลบ ทำให้ $S_{t+1}<0$ เมื่อนำไปจัดพอร์ตรอบถัดไปจึงใช้ $C_{t+1}=\max(S_{t+1},0)=0$ เมื่อ $R_G=0$ และ $m=3$ จุดวิกฤตคือ PSP ลดมากกว่า $1/3$ ในหนึ่งช่วง ตัวคูณสูงทำให้เปิดความเสี่ยงมากขึ้นและทนการตกแรงต่อช่วงได้น้อยลง การจำลอง GBM เพียง 2,000 เส้นทางอาจไม่พบเหตุการณ์แบบนี้ จึงควรตรวจ stress scenario แยกด้วย [Paulot และ Lacroze ศึกษา gap risk ของ CPPI แบบปรับตามช่วงเวลา](https://arxiv.org/abs/0905.2926)

ถ้าเลือก $m=1$ ขณะมีเงินเหนือ floor จำนวนเงิน GHP จะพอดีกับต้นทุนเป้าหมายและนำเพียงส่วนเกินไป PSP ภายใต้เงื่อนไข GHP match จริง ไม่มีต้นทุน และ PSP ขาดทุนได้ไม่เกินเงินที่ลง พอร์ตจึงยังรองรับ floor หลังแต่ละงวดได้ คุณสมบัติในกรณีจำกัดนี้ไม่ครอบคลุม multiplier 3 ที่ทดลองหลัก

```python
funded_wealth, funded_weights = wealth_with_goal_floor(
    psp_returns, ghp_returns, goal_prices,
    terminal_goal, initial_wealth, multiplier=1,
)
print("Multiplier one stays funded in these paths:", np.all(
    funded_wealth >= terminal_goal * goal_prices - 1e-8
))
```

ผลเป็น `True` ค่า `1e-8` ใช้เผื่อความคลาดเคลื่อนการคำนวณเลขทศนิยมเล็กมากเท่านั้น ไม่ได้อนุญาตเงินขาดทางเศรษฐกิจ ถ้ามีความเสี่ยงผิดนัด ค่าธรรมเนียม หรืออายุสินทรัพย์ไม่ตรงภาระ ข้อสรุปตามสมการต้องประเมินใหม่

<span id="terminal-shortfall-statistics"></span>

## วัดทั้งความถี่และจำนวนเงินที่ขาด

ให้เงินปลายทางของเส้นทางที่ $i$ เป็น $W_T^{(i)}$ และเป้าหมายเป็น $G$ จำนวนเงินขาดคือ $D_i=\max(G-W_T^{(i)},0)$ ต้องเก็บค่าศูนย์จากเส้นทางที่ไม่ขาดไว้ด้วยเมื่อคำนวณค่าเฉลี่ยทุกเส้นทาง

| ตัววัด | คำนวณจากอะไร | ตอบคำถาม |
|---|---|---|
| Breach probability | จำนวนเส้นทางที่ $W_T<G$ หารจำนวนทั้งหมด | ขาดเป้าบ่อยเพียงใดในแบบจำลอง |
| Mean deficit, all paths | ค่าเฉลี่ย $D_i$ รวมค่าศูนย์ | โดยเฉลี่ยทุกสถานการณ์ เงินขาดเท่าไร |
| Mean deficit, breached paths | ค่าเฉลี่ย $D_i$ เฉพาะเส้นทางที่ขาด | เมื่อเกิดขาดแล้ว ขาดหนักเท่าไร |
| Median terminal wealth | ค่ากลางของเงินปลายทาง | เส้นทางกึ่งกลางมีเงินเท่าไร |
| Terminal wealth quantile | เช่นเปอร์เซ็นไทล์ 5 และ 95 | เงินปลายทางกระจายกว้างเพียงใด |

ตัวอย่างเงินปลายทาง [70, 90, 100, 140] บาท เป้าหมาย 100 บาท มีสองเส้นทางขาดจากทั้งหมดสี่เส้นทาง โอกาสขาดจึง 50% เงินขาดคือ [30, 10, 0, 0] ค่าเฉลี่ยทุกเส้นทาง 10 บาท ส่วนค่าเฉลี่ยเฉพาะเส้นทางขาด 20 บาท การนำ 20 บาทไปเรียกว่าเงินขาดเฉลี่ยโดยไม่บอกเงื่อนไขจะทำให้ผู้อ่านเข้าใจผิด

```python
def terminal_statistics(terminal_values, goal):
    values = np.asarray(terminal_values, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.all(np.isfinite(values)) or goal <= 0:
        raise ValueError("Use a nonempty finite vector and a positive goal.")
    tolerance = 1e-12 * goal
    breached = values < goal - tolerance
    deficits = np.where(breached, goal - values, 0.0)
    return pd.Series({
        "Breach probability": breached.mean(),
        "Mean deficit, all paths": deficits.mean(),
        "Mean deficit, breached paths": deficits[breached].mean() if breached.any() else np.nan,
        "Mean terminal wealth": values.mean(),
        "Median terminal wealth": np.median(values),
        "5% terminal wealth": np.quantile(values, 0.05),
        "95% terminal wealth": np.quantile(values, 0.95),
    })

print(terminal_statistics(np.array([70, 90, 100, 140]), goal=100).round(4))
print("Breach probability when no path is short:", terminal_statistics(np.array([100, 120]), 100)[
    "Breach probability"
])
```

ตัวอย่างแรกได้ breach 0.5, mean deficit ทุกเส้นทาง 10 และเฉพาะเส้นทางขาด 20 เงินเฉลี่ยปลายทางเท่ากับ 100 แต่ median เท่ากับ 95 จึงเห็นว่าค่าเฉลี่ยเงินถึงเป้าหมายไม่ได้แปลว่าเส้นทางส่วนใหญ่มีเงินครบ ตัวอย่างที่สองได้ breach 0.0 แม้ค่าเฉลี่ยเฉพาะกลุ่มที่ขาดเป็น `NaN` เพราะไม่มีกลุ่มนั้นให้เฉลี่ย

ตัวคูณ tolerance ข้างต้นกันการนับข้อผิดพลาดระดับทศนิยมจากการคำนวณให้กลายเป็นเหตุการณ์ขาดเป้า สำหรับเป้าหมาย 100,000 บาทมีค่าเพียง 0.0000001 บาท หากจะมีช่วงยอมรับเงินขาดจริง เช่น 1,000 บาท ต้องกำหนดเป็นเงื่อนไขแผนแยกต่างหาก

```python
strategy_wealth = {
    "Fixed 60/40": fixed_wealth,
    "Glide 80 to 20": glide_wealth,
    "Dynamic m=3": dynamic_wealth,
    "Matched goal plus surplus m=1": funded_wealth,
}
strategy_summary = pd.DataFrame({
    name: terminal_statistics(wealth[-1], terminal_goal)
    for name, wealth in strategy_wealth.items()
}).T
print(strategy_summary.round(4).to_string())
```

ผลชุดนี้พบ breach 19.8% สำหรับ fixed mix และ 18.2% สำหรับ glide path ส่วน dynamic m=3 กับ m=1 ไม่พบ breach ใน 2,000 เส้นทางนี้ กรณี stress ก่อนหน้าซึ่ง PSP ลด 40% ยังทำให้ m=3 หลุด floor ได้

แต่ละแถวคำนวณจากเงินปลายทาง 2,000 ค่าโดยใช้ shock ชุดเดียวกัน การเปลี่ยนจำนวนเส้นทาง seed หรือพารามิเตอร์จะเปลี่ยนตัวเลขที่รายงานได้ ในการเปรียบเทียบเชิงวิจัยยังต้องลองสมมติฐานเรื่องความผันผวน การตกกระโดด ดอกเบี้ย และต้นทุนด้วย ผลจากสมมติฐานชุดเดียวไม่เพียงพอให้เลือกกติกาลงทุนจริง

ถ้าไม่มีเส้นทางใดขาดเลย ค่า breach ของตัวอย่างเป็นศูนย์ ค่านี้ยังไม่ได้ยืนยันว่าความน่าจะเป็นจริงเป็นศูนย์ หากสมมติว่าเส้นทางอิสระและโมเดลถูกต้อง ความน่าจะเป็นไม่พบเหตุการณ์เลยเมื่อโอกาสจริงเท่ากับ $p$ คือ $(1-p)^N$ เมื่อมี $N=2{,}000$ เส้นทาง แก้ $(1-p)^{2000}=0.05$ ได้ $p\approx0.001497$ หรือประมาณ 0.15% แสดงว่าตัวอย่างจำกัดยังแยกเหตุการณ์หายากออกได้ไม่เด็ดขาด และการคำนวณนี้ไม่ได้รวม model error

<span id="drawdown-goal-floor"></span>

## Floor จากจุดสูงสุดตอบอีกเป้าหมายหนึ่ง

บางคนสนใจเงินปลายทางครบเป้าหมาย ขณะที่บางคนรับไม่ได้หากพอร์ตลดจากจุดสูงสุดมากระหว่างทาง กติกา drawdown floor จึงกำหนด $H_t=\max(W_0,\ldots,W_t)$ และ $F_t=(1-d)H_t$ โดย $d$ เป็นสัดส่วนการลดลงจากยอดสูงสุดที่ใช้ตั้ง floor

ถ้าเริ่ม 100 บาทและกำหนด $d=20\%$ floor เริ่มที่ 80 บาท ต่อมา wealth ขึ้นเป็น 150 บาท floor จะยกเป็น 120 บาทและไม่ลดตาม wealth การเหลือ 110 บาทปลายทางอาจเกินเป้าหมายเดิม 100 บาท แต่ต่ำกว่า drawdown floor ที่ยกขึ้นแล้ว ตัววัดสองแบบจึงให้คำตอบต่างกันได้โดยไม่ขัดกัน

ฟังก์ชันต่อไปใช้บัญชีดอกเบี้ยคงที่เป็นสินทรัพย์รองรับ nominal drawdown floor ในแต่ละช่วง ในสถานการณ์นี้ผลตอบแทนเท่ากับ GHP เพราะดอกเบี้ยคงที่ แต่เมื่อดอกเบี้ยสุ่ม เงินสดกับ ZCB อายุยาวจะมีความเสี่ยงต่างกัน ต้องเลือกสินทรัพย์ให้ตรงกับ floor ที่ตั้ง

```python
def wealth_with_drawdown_floor(psp, cash_returns, initial, max_drawdown, multiplier):
    if psp.shape != cash_returns.shape or not 0 < max_drawdown < 1 or multiplier < 0:
        raise ValueError("Use matching arrays, a drawdown in (0, 1), and a nonnegative multiplier.")
    wealth = np.empty((psp.shape[0] + 1, psp.shape[1]))
    wealth[0] = initial
    peak = np.full(psp.shape[1], initial)
    floors = np.empty_like(wealth)
    floors[0] = (1 - max_drawdown) * peak
    for step in range(psp.shape[0]):
        risky_amount = np.minimum(
            multiplier * np.maximum(wealth[step] - floors[step], 0), wealth[step],
        )
        wealth[step + 1] = (
            risky_amount * (1 + psp[step])
            + (wealth[step] - risky_amount) * (1 + cash_returns[step])
        )
        peak = np.maximum(peak, wealth[step + 1])
        floors[step + 1] = (1 - max_drawdown) * peak
    return wealth, floors

cash_returns = np.full_like(psp_returns, (1 + annual_safe_yield) ** dt - 1)
drawdown_wealth, drawdown_floors = wealth_with_drawdown_floor(
    psp_returns, cash_returns, initial_wealth,
    max_drawdown=0.20, multiplier=3,
)
running_peaks = np.maximum.accumulate(drawdown_wealth, axis=0)
realized_drawdowns = drawdown_wealth / running_peaks - 1
print(f"Worst observed drawdown: {realized_drawdowns.min():.4%}")
print("Floor never decreases:", np.all(np.diff(drawdown_floors, axis=0) >= 0))
print(terminal_statistics(drawdown_wealth[-1], terminal_goal).round(4))
```

`np.maximum.accumulate` หาจุดสูงสุดสะสมรวมแถวเริ่มต้น ส่วนการหารแล้วลบหนึ่งได้ drawdown ที่เป็นศูนย์เมื่อทำจุดสูงสุดใหม่และติดลบเมื่ออยู่ต่ำกว่าจุดสูงสุด การทดลองนี้มี drawdown ต่ำสุด −18.5998% และเงินปลายทางขาดเป้าใน 17.85% ของเส้นทาง ผลตรวจ floor ไม่ลดเป็น `True` แต่กติกายังมี gap risk จึงต้องตรวจว่ามูลค่าจริงหลุด floor หรือไม่ แทนการสรุปจากชื่อพารามิเตอร์ `max_drawdown` ว่ารับประกันการลดไม่เกิน 20%

การดูเงินปลายทางกับ drawdown ควรทำร่วมกัน หากความเสี่ยงที่สนใจคือความสามารถจ่ายภาระระหว่างทาง อาจต้องวัด drawdown ของ funding ratio ด้วย เพราะมูลค่าภาระเปลี่ยนได้ ขนาดการลดของ wealth อย่างเดียวไม่แสดงการเปลี่ยนของเงินที่ต้องใช้รองรับเป้าหมาย

<span id="liability-friendly-equity"></span>

## เลือก PSP ให้ความเสี่ยงสอดคล้องกับภาระ

คอร์สเรียกแนวคิดนี้ว่า liability-friendly equity คือเลือกส่วนหุ้นโดยพิจารณาว่ามันเคลื่อนไหวสัมพันธ์กับภาระอย่างไร ร่วมกับผลตอบแทนที่คาดหวังและความเสี่ยงของหุ้นเอง เช่น ภาระเพิ่มตามเงินเฟ้อ พอร์ตหุ้นบางลักษณะอาจมี exposure ต่อเงินเฟ้อใกล้ภาระมากกว่าหุ้นอีกชุดหนึ่ง แต่ความสัมพันธ์ที่วัดได้ไม่ใช่สัญญาจ่ายเงินตามภาระ

ถ้าผลตอบแทนสินทรัพย์เป็น $R_A$ และผลตอบแทนของมูลค่าภาระเป็น $R_L$ ผลตอบแทนของ funding ratio ที่ตรงตามนิยามคือ

$$
R_{FR}=\frac{1+R_A}{1+R_L}-1.
$$

สำหรับการเปลี่ยนแปลงขนาดเล็กใช้ $R_A-R_L$ เป็นค่าประมาณได้ ความแปรปรวนของผลต่างนี้เท่ากับ

$$
\operatorname{Var}(R_A-R_L)
=\sigma_A^2+\sigma_L^2-2\rho_{A,L}\sigma_A\sigma_L.
$$

สมการแสดงว่าลดความผันผวนของสินทรัพย์อย่างเดียวอาจไม่ลดความเสี่ยงเทียบภาระได้มากที่สุด ความสัมพันธ์กับภาระมีส่วนด้วย ตัวอย่างสมมติหกสถานการณ์ต่อไปตั้งให้ PSP สองแบบมีผลตอบแทนชุดเดียวกันเพียงเรียงต่างกัน จึงมีค่าเฉลี่ยและ volatility เท่ากัน แต่จับคู่กับภาระต่างกัน

```python
liability_changes = np.array([-0.06, -0.04, -0.02, 0.02, 0.04, 0.06])
aligned_psp = liability_changes + 0.03
reversed_psp = aligned_psp[::-1]
equity_comparison = pd.DataFrame({
    "Aligned hypothetical PSP": aligned_psp,
    "Reversed hypothetical PSP": reversed_psp,
})
relative_funding_returns = (1 + equity_comparison).div(1 + liability_changes, axis=0) - 1
equity_metrics = pd.DataFrame({
    "Mean asset return": equity_comparison.mean(),
    "Asset volatility": equity_comparison.std(ddof=0),
    "Funding-return volatility": relative_funding_returns.std(ddof=0),
})
print(equity_metrics.round(6).to_string())
```

ค่าเฉลี่ยผลตอบแทนสินทรัพย์ทั้งคู่เท่ากับ 3% และ volatility ของสินทรัพย์เท่ากัน แต่ funding-return volatility ของชุดที่เรียงตรงกับภาระประมาณ 0.1300% เทียบกับ 8.7994% ของชุดที่เรียงกลับกัน ตัวเลขนี้เป็นข้อมูลสร้างเพื่อแยกผลของความสัมพันธ์โดยเฉพาะ ไม่ใช่หลักฐานว่ามีหุ้นชุดใดทำได้จริงหรือจะรักษาความสัมพันธ์นี้ได้ตลอด

หุ้นที่จ่ายเงินปันผลยังอยู่ใน PSP เพราะบริษัทอาจลดหรือหยุดปันผลได้ หุ้นที่เคยช่วย offset เงินเฟ้อหรือดอกเบี้ยก็อาจเปลี่ยนความสัมพันธ์ในช่วงวิกฤต หากเพิ่มน้ำหนักหุ้นบางกลุ่มเพื่อให้ใกล้ภาระ ต้องตรวจความกระจุกตัว สภาพคล่อง และ basis risk ที่ยังเหลือ รวมทั้งโอกาสเสียผลตอบแทนจากการจำกัดชุดลงทุน แนวคิดนี้จึงต้องประเมินทั้งการรองรับภาระและต้นทุนของข้อจำกัดที่เลือก

<span id="goal-allocation-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

1. พอร์ต 100 บาท PSP 60% ได้ −10% และ GHP ได้ +2% ในหนึ่งงวด เงินเหลือเท่าไร?
2. ใช้เป้าหมาย 100,000 บาทในอีกห้าปี อัตรา 3% แต่มีทุนเริ่ม 80,000 บาท Dynamic floor ที่ใช้สูตรข้างต้นจะให้น้ำหนัก PSP เท่าไร และการลด PSP แก้ underfunding หรือไม่?
3. เริ่ม 100 บาท floor 80 บาท multiplier 3 และ GHP return 0% ถ้า PSP ลด 30% จะหลุด floor หรือยัง? ถ้าลด 40% ล่ะ?
4. เงินปลายทาง [80, 100, 120, 140] เป้าหมาย 100 บาท มี breach probability, mean deficit ทุกเส้นทาง และ mean deficit เมื่อขาดเท่าไร?
5. ในลูปงวดที่ 10 ควรอ่าน floor จากราคา ZCB ต้นงวดที่ 10 หรือราคาปลายงวดเดียวกัน?
6. พอร์ตขึ้นจาก 100 เป็น 150 แล้วลดเหลือ 115 บาท เป้าหมายปลายทางคือ 100 บาท และตั้ง drawdown floor 20% ผลผ่านเป้าหมายใดและหลุดเป้าหมายใด?
7. หุ้นที่มีเงินปันผลสูงและเคยสัมพันธ์กับเงินเฟ้อเป็น GHP ที่รับประกันรายจ่ายเพิ่มตามเงินเฟ้อหรือไม่?

<details>
<summary>เปิดแนวคำตอบ</summary>

ข้อ 1 ผลตอบแทน $0.6(-0.10)+0.4(0.02)=-0.052$ เงินจึงเหลือ 94.80 บาท ข้อ 2 floor เริ่ม 86,260.88 บาท สูงกว่าเงินที่มี cushion จึงเป็นศูนย์และ PSP เป็นศูนย์ การลงทุนที่ match ภาระจะรักษาสัดส่วนที่ขาดอยู่ไว้ ต้องพิจารณาเติมเงิน ลดเป้าหมาย หรือเปลี่ยนวันใช้ การรับความเสี่ยงเพิ่มเป็นอีกทางเลือกที่อาจขาดมากขึ้นและไม่ได้อยู่ในกติกานี้

ข้อ 3 เงินเหลือ 82 บาทเมื่อ PSP ลด 30% จึงยังเหนือ floor แต่เหลือ 76 บาทเมื่อ PSP ลด 40% ข้อ 4 ขาดหนึ่งจากสี่เส้นทางจึง 25% เงินขาด [20, 0, 0, 0] เฉลี่ยทุกเส้นทาง 5 บาทและเฉพาะที่ขาด 20 บาท

ข้อ 5 อ่านราคาและ wealth ต้นงวด ซึ่งมีอยู่ตอนตัดสินใจ ผลตอบแทนงวดนั้นจึงค่อยนำมาอัปเดต wealth ข้อ 6 มีเงินเกินเป้าหมายปลายทาง 100 บาท แต่ drawdown เท่ากับ $115/150-1\approx-23.33\%$ และต่ำกว่า floor 120 บาท ข้อ 7 ปันผลและความสัมพันธ์ในอนาคตไม่แน่นอน หุ้นยังมีความเสี่ยงและ basis risk เทียบภาระ ต้องไม่เรียกว่าเป็นการรับประกัน

</details>

<span id="goal-allocation-sources"></span>

## แหล่งเรียน

แนวคิดจาก Transcript ของ [Choosing the policy portfolio](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/IQo8M/choosing-the-policy-portfolio), [Beyond LDI](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/9OIfJ/beyond-ldi) และ [Liability-friendly equity portfolios](https://www.coursera.org/learn/introduction-portfolio-construction-python/lecture/8hNda/liability-friendly-equity-portfolios) ใน Module 4 ประกอบโค้ด `lab_128.ipynb`, `lab_129.ipynb` และ toolkit ที่ผู้เรียนให้มา

ตัวอย่างหน้านี้สร้างข้อมูลและกติกาคำนวณขึ้นใหม่ ตรวจการเรียงเวลาระหว่างน้ำหนัก ราคา และผลตอบแทนอย่างชัดเจน สถิติ shortfall แยกตัวหารทุกเส้นทางออกจากกลุ่มที่ขาด และรายงาน breach probability เป็นศูนย์เมื่อไม่พบเหตุการณ์ โดยไม่ตีความว่าแบบจำลองรับประกันผลในอนาคต
