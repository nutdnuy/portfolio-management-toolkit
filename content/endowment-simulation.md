---
title: "Endowment Simulation: เงินทุน การใช้จ่าย และลำดับผลตอบแทน"
description: จำลองเงินกองทุนที่ปรับพอร์ตปีละครั้งและจ่ายเงินหลังรับผลตอบแทน แยกเงินจริงจากเงินตามราคา เปรียบเทียบ Markov กับ IID และวัดความไม่แน่นอนของ shortfall
---

# Endowment Simulation: เงินทุน การใช้จ่าย และลำดับผลตอบแทน

<p class="lead">กองทุนที่จ่ายทุนการศึกษาทุกปีต้องดูทั้งเงินที่เหลือปลายทางและความสามารถจ่ายระหว่างทาง แม้ผลตอบแทนสองเส้นทางมีค่าเฉลี่ยเท่ากัน การขาดทุนก่อนหรือหลังถอนเงินอาจทำให้เงินเหลือต่างกันได้</p>

Endowment คือเงินทุนที่นำไปลงทุนเพื่อสนับสนุนการใช้จ่ายต่อเนื่อง เช่น เงินทุนของมหาวิทยาลัย ตัวอย่างนี้เริ่มจากเงินสมมติ 100 ล้านบาทในกำลังซื้อปีฐาน คงสัดส่วนลงทุนต้นปี A 60% และ B 40% แล้วจ่ายค่าใช้จ่ายจริงปีละ 2.5 ล้านบาท ณ สิ้นปี โดยเพิ่มจำนวนเงินตามเงินเฟ้อ

เราจะเปรียบเทียบสองแบบจำลองที่มีการแจกแจงสถานะของแต่ละปีเหมือนกัน แต่มีความต่อเนื่องของสถานะต่างกัน พอร์ตทั้งคู่ใช้กฎการลงทุนและการจ่ายเงินเดียวกัน การทดลองจึงวัดผลของลำดับสถานการณ์ภายใต้ input ที่กำหนด ไม่ได้เป็นการปรับพอร์ตให้รู้ภาวะตลาดล่วงหน้า

โค้ดเป็นตัวอย่างใหม่ ใช้ NumPy และ pandas และรันจาก Notebook ว่างได้ ไม่ต้องมีราคาหุ้นหรือ Notebook ของผู้สอน เงินในโค้ดมีหน่วยล้านบาท ส่วนผลตอบแทนและเงินเฟ้อเก็บเป็นทศนิยมต่อปี

```python
import numpy as np
import pandas as pd

np.set_printoptions(precision=6, suppress=True)
```

<span id="sequence-of-returns"></span>

## ลองสลับสองปีก่อนสร้างหลายพันเส้นทาง

เริ่มด้วยตัวอย่างย่อยที่ไม่มีเงินเฟ้อ: เงินต้น 100 ล้านบาท ใช้จ่ายปลายปีปีละ 5 ล้านบาท และมีผลตอบแทนสองปีคือ +20% กับ −10% กรณีแรกได้กำไรก่อน:

$$100(1.20)-5=115,\qquad115(0.90)-5=98.5.$$

กรณีที่สองขาดทุนก่อน:

$$100(0.90)-5=85,\qquad85(1.20)-5=97.$$

หากไม่ถอนเงิน ทั้งสองลำดับจบที่ $100(1.20)(0.90)=108$ เท่ากัน แต่เมื่อถอนเงิน จำนวนเงินที่ได้รับผลตอบแทนปีถัดไปต่างกัน จึงจบต่างกัน 1.5 ล้านบาท

```python
def spend_after_return(real_returns, initial=100.0, spending=5.0):
    wealth = [float(initial)]
    for annual_return in real_returns:
        wealth.append(max(wealth[-1] * (1 + annual_return) - spending, 0.0))
    return np.array(wealth)

sequence_early_gain = spend_after_return([0.20, -0.10])
sequence_early_loss = spend_after_return([-0.10, 0.20])
print("Gain first:", sequence_early_gain)
print("Loss first:", sequence_early_loss)
print("Without spending:", 100 * 1.2 * 0.9)
```

`wealth` เริ่มด้วยเงินต้นก่อนปีแรก แล้วเพิ่มเงินคงเหลือปลายแต่ละปี `max(..., 0)` จำกัดเงินที่เหลือไม่ให้ติดลบ ฟังก์ชันสั้นนี้ใช้สอนลำดับเหตุการณ์ ส่วนฟังก์ชันเต็มข้างล่างจะบันทึกด้วยว่าจ่ายเงินไม่ครบเท่าไรเมื่อทุนไม่พอ

ความเสี่ยงจากลำดับผลตอบแทนหรือ sequence risk จึงเกี่ยวข้องกับ cash flows ขนาดและเวลาของการถอนเงิน กรณีนี้ไม่ได้เกิดจาก mean หรือ volatility ของสองผลตอบแทนต่างกัน เพราะใช้ตัวเลขชุดเดียวกันแล้วสลับลำดับเท่านั้น

ตัวอย่างหลักต่อไปใช้จ่าย 2.5 ล้านบาทจริงต่อปี ไม่ใช่ 5 ล้านบาทของตัวอย่างสองปี และใส่เงินเฟ้อ 2% เพื่อให้เห็นบัญชีเงินทั้ง nominal และ real

<span id="endowment-assumptions"></span>

## ระบุหนึ่งปีก่อนเขียนลูป

กฎของตัวอย่างหลักมีดังนี้:

| รายการ | สมมติฐาน |
|---|---|
| เงินเริ่มต้น | 100 ล้านบาท ณ กำลังซื้อปีฐาน |
| ระยะเวลา | 30 ปี |
| น้ำหนักต้นปี | A 60%, B 40%, ไม่มี short หรือ leverage |
| การปรับพอร์ต | กลับสู่น้ำหนักเป้าหมายต้นทุกปี และถือสินทรัพย์โดยไม่ปรับระหว่างปี |
| เงินที่ต้องจ่าย | 2.5 ล้านบาทต่อปีในกำลังซื้อปีฐาน จ่ายหลังรับผลตอบแทนสิ้นปี |
| เงินเฟ้อ | 2% ต่อปี คงที่ |
| เมื่อเงินไม่พอ | จ่ายเท่าที่มี บันทึกส่วนที่จ่ายไม่ได้ ทุนคงเหลือเป็นศูนย์ |
| ต้นทุนและเงินเข้าระหว่างทาง | ไม่มีค่าซื้อขาย ภาษี เงินบริจาค หรือเงินเติม |
| จำนวนเส้นทาง | 20,000 เส้นทาง ซึ่งสุ่มอย่างอิสระจากกัน |

กำหนดสถานะ Calm/Stress และพารามิเตอร์รายปีเหมือน [Regime Scenarios](regime-scenarios.html) คือ Calm มี mean ของ A/B 8%/3%, Stress มี −12%/2% และ covariance ตามตารางในบทก่อนหน้า เราจะสร้างตัวแปรเหล่านี้ใหม่เพื่อให้รันบทนี้ลำพังได้

```python
endowment_transition = np.array([[0.85, 0.15], [0.35, 0.65]])
endowment_stationary = np.array([0.70, 0.30])
endowment_means = np.array([[0.08, 0.03], [-0.12, 0.02]])
endowment_covs = np.array([[[0.0100, 0.0010], [0.0010, 0.0025]],
                           [[0.0400, -0.0020], [-0.0020, 0.0064]]])
endowment_weights = np.array([0.60, 0.40])
endowment_initial = 100.0
endowment_spending = 2.5
endowment_inflation = 0.02
endowment_years = 30
endowment_n = 20000
print("Annual nominal means by state:", endowment_means @ endowment_weights)
print("Year 1 required nominal spending:", endowment_spending * (1 + endowment_inflation))
```

`endowment_spending = 2.5` คือจำนวนเงินจริงคงที่ ไม่ใช่ถอน 2.5% ของเงินคงเหลือทุกปี เงินที่ต้องจ่าย nominal ในสิ้นปีแรกเท่ากับ $2.5(1.02)=2.55$ ล้านบาท ส่วนสิ้นปีที่สองเท่ากับ $2.5(1.02)^2=2.601$ ล้านบาท

กฎถอนเป็นเปอร์เซ็นต์ของทุน กฎเฉลี่ยทุนย้อนหลัง หรือกฎลดรายจ่ายเมื่อทุนต่ำกว่าเกณฑ์จะให้ผลอีกแบบหนึ่ง ต้องเขียน recurrence ใหม่ให้ตรงนโยบายก่อนเปรียบเทียบ การจำลองนี้ไม่เลื่อนยอดค้างจ่ายไปเป็นหนี้ในปีต่อไป จึงรายงาน missed spending เพื่อแยกความเสียหายส่วนนั้นจากเงินคงเหลือ

<span id="markov-versus-iid"></span>

## สถานะรายปีเหมือนกัน แต่การอยู่ต่อไม่เหมือนกัน

แบบ Markov ใช้

$$P=\begin{pmatrix}0.85&0.15\\0.35&0.65\end{pmatrix},\qquad
\pi=(0.7,0.3).$$

แบบ IID สุ่มสถานะทุกปีใหม่อย่างอิสระด้วยโอกาส Calm 70% และ Stress 30% จึงเขียน transition ได้ว่า

$$P_{\rm IID}=\begin{pmatrix}0.7&0.3\\0.7&0.3\end{pmatrix}.$$

เมื่อเริ่มทั้งสองแบบด้วย $\pi$ ความน่าจะเป็น Stress ของทุกปีเป็น 30% เท่ากัน แต่ Markov มีโอกาส Stress ต่อหลังปี Stress 65% ขณะที่ IID มีเพียง 30% ช่วงที่สถานะเดียวกันเกิดติดกันจึงมีโครงสร้างต่างกัน

```python
def state_paths(uniforms, transition, initial_probabilities):
    n, years = uniforms.shape
    states = np.empty((n, years), dtype=int)
    states[:, 0] = uniforms[:, 0] >= initial_probabilities[0]
    for t in range(1, years):
        states[:, t] = uniforms[:, t] >= transition[states[:, t - 1], 0]
    return states

endowment_rng = np.random.default_rng(402)
endowment_uniforms = endowment_rng.random((endowment_n, endowment_years))
endowment_shocks = endowment_rng.uniform(-np.sqrt(3), np.sqrt(3),
                                         size=(endowment_n, endowment_years, 2))
endowment_states = state_paths(endowment_uniforms, endowment_transition, endowment_stationary)
endowment_iid_transition = np.tile(endowment_stationary, (2, 1))
endowment_iid_states = state_paths(endowment_uniforms, endowment_iid_transition, endowment_stationary)
print("First Markov path:", endowment_states[0, :10])
print("First IID path:", endowment_iid_states[0, :10])
print("Same first-year states:", np.array_equal(endowment_states[:, 0], endowment_iid_states[:, 0]))
```

`state_paths` เป็น helper สำหรับสองสถานะโดยเฉพาะ ทุกแถวคือหนึ่งเส้นทาง ทุกคอลัมน์คือหนึ่งปี ตั้งปีแรกด้วย initial probabilities แล้วใช้สถานะปีก่อนเลือกแถวของ transition สำหรับปีต่อไป `uniforms[:, t]` เลือกเลขสุ่มของทุกเส้นทางในปีที่ $t$ พร้อมกัน

เราใช้เลขสุ่ม `endowment_uniforms` ชุดเดียวกันกับทั้งสองโมเดล และใช้ shocks ชุดเดียวกันด้วย เรียกว่า common random numbers เพื่อเปรียบเทียบโดยจับคู่เส้นทาง ไม่ได้ทำให้สถานะหลังปีแรกต้องเหมือนกัน เพราะ threshold ที่ใช้เลือกสถานะต่างกัน

ปีแรกใช้ prior เดียวกันและเลขสุ่มเดียวกัน จึงได้สถานะตรงกันทุกเส้นทาง ผล `Same first-year states` เป็น `True` ส่วนตัวอย่างสิบปีแรกของเส้นทางแรกเริ่มต่างกันภายหลัง โค้ดใช้ seed 402 คงที่ ไม่เปลี่ยน seed เพื่อคัดผลการเปรียบเทียบ

<span id="bounded-regime-returns"></span>

## สร้างผลตอบแทนที่มี mean และ covariance ตามสถานะ

การจำลองเงินคงเหลือต้องควบคุม gross return ให้มีความหมายสำหรับสินทรัพย์ที่ไม่ใช้ leverage ตัวอย่างนี้จึงใช้ shocks แบบ Uniform มีขอบเขต แทน Normal ของ simple return ที่มีหางต่ำกว่า −100% ทางทฤษฎี

ให้สมาชิกของเวกเตอร์ $U_t$ เป็นอิสระและแจกแจง Uniform บน $[-\sqrt3,\sqrt3]$ จะมี mean 0 และ variance 1 เมื่อ $L_sL_s^\top=\Sigma_s$ ให้

$$R_t=\mu_{S_t}+L_{S_t}U_t.$$

จะได้ conditional mean $\mu_s$ และ covariance $\Sigma_s$ ตามเดิม แต่รูปร่างการแจกแจงมีขอบเขตและไม่ใช่ Normal การมี moments เท่ากันไม่ได้ทำให้ tail risk ของสองการแจกแจงเท่ากัน

```python
def asset_returns_by_state(states, shocks, means, covariances):
    returns = np.empty_like(shocks)
    for state in range(len(means)):
        mask = states == state
        L = np.linalg.cholesky(covariances[state])
        returns[mask] = means[state] + shocks[mask] @ L.T
    return returns

endowment_returns = asset_returns_by_state(endowment_states, endowment_shocks, endowment_means, endowment_covs)
endowment_iid_returns = asset_returns_by_state(endowment_iid_states, endowment_shocks, endowment_means, endowment_covs)
print("Return array shape:", endowment_returns.shape)
print(f"Smallest simulated asset return: {100 * endowment_returns.min():.4f}%")
print("Realized stress share, Markov:", round(endowment_states.mean(), 6))
print("Realized stress share, IID:", round(endowment_iid_states.mean(), 6))
```

`mask` เลือกทุกตำแหน่งที่อยู่ในสถานะนั้น `shocks[mask]` ได้ตารางแถวละสองสินทรัพย์ แล้วคูณ `L.T` ตาม convention ที่แต่ละ observation เป็นแถว ผลลัพธ์มี shape `(20000, 30, 2)` คือเส้นทาง ปี และสินทรัพย์ตามลำดับ

สำหรับ A ใน Stress ขอบล่างตามโมเดลคือ $-0.12-0.20\sqrt3\approx-46.6410\%$ ซึ่งยังสูงกว่า −100% ส่วน B และ Calm ก็มี gross return เป็นบวกภายใต้ค่าที่กำหนดนี้ การตรวจนี้มาจากขอบเขตของ shocks และพารามิเตอร์ ไม่ใช่สรุปจากการที่ยังไม่เคยสุ่มเจอผลตอบแทนต่ำกว่า −100% เท่านั้น

สัดส่วนปี Stress ที่สุ่มได้ทั้งหมดประมาณ 30.0955% ใน Markov และ 30.1195% ใน IID ไม่ต้องตรง 30% พอดี จำนวนปีในเส้นทาง Markov ไม่เป็นอิสระกัน แต่เส้นทางแต่ละแถวเป็นการทดลองอิสระ ซึ่งเราจะใช้เป็นหน่วยนับสำหรับ MC standard error

<span id="endowment-cash-flow-ledger"></span>

## เขียนบัญชีผลตอบแทนก่อนจ่ายเงิน

ให้ $V_t$ เป็นเงิน nominal หลังจ่ายสิ้นปี $t$, $I_t=(1+i)^t$ เป็นดัชนีราคาเมื่อเงินเฟ้อ $i=0.02$ และ $c=2.5$ เป็นรายจ่ายจริงที่ต้องการในแต่ละปี ขั้นตอนหนึ่งปีคือ

$$
\begin{aligned}
R_{p,t}&=w^\top R_t,\\
A_t&=V_{t-1}(1+R_{p,t}),\\
C_t&=cI_t,\\
\text{Paid}_t&=\min(A_t,C_t),\\
V_t&=A_t-\text{Paid}_t,\\
\text{Unpaid}_t&=C_t-\text{Paid}_t.
\end{aligned}
$$

$A_t$ คือเงินหลังรับผลตอบแทนแต่ก่อนจ่าย $C_t$ คือยอดที่ต้องจ่ายตามราคาในปีนั้น หารเงินทุกจำนวนของปลายปี $t$ ด้วย $I_t$ จึงได้กำลังซื้อปีฐาน เราจะเก็บ `wealth_real`, `paid_real` และ `unpaid_real` แยกกัน

```python
def simulate_endowment(asset_returns, weights, initial, spending, inflation):
    r, w = np.asarray(asset_returns, float), np.asarray(weights, float)
    if (r.ndim != 3 or w.shape != (r.shape[2],) or not np.isfinite(r).all()
        or not np.isfinite(w).all() or np.any(r <= -1) or np.any(w < 0)
        or not np.isclose(w.sum(), 1) or not np.isfinite([initial, spending, inflation]).all()
        or initial <= 0 or spending < 0 or inflation <= -1):
        raise ValueError("Check positive wealth, long-only weights, return array and cash-flow assumptions")
    portfolio_returns = r @ w
    n, years = portfolio_returns.shape
    price_index = (1 + inflation) ** np.arange(years + 1)
    nominal = np.full(n, initial)
    wealth_real = np.empty((n, years + 1))
    wealth_real[:, 0] = initial
    paid_real = np.empty((n, years))
    unpaid_real = np.empty((n, years))
    for t in range(years):
        available = nominal * (1 + portfolio_returns[:, t])
        required = spending * price_index[t + 1]
        paid = np.minimum(available, required)
        nominal = available - paid
        wealth_real[:, t + 1] = nominal / price_index[t + 1]
        paid_real[:, t] = paid / price_index[t + 1]
        unpaid_real[:, t] = (required - paid) / price_index[t + 1]
    return {"wealth_real": wealth_real, "paid_real": paid_real,
            "unpaid_real": unpaid_real, "portfolio_returns": portfolio_returns}
```

ฟังก์ชันรับ returns สามมิติและน้ำหนักหนึ่งมิติ ตรวจค่า finite, gross return บวก, น้ำหนักไม่ติดลบและรวมหนึ่ง จากนั้น `r @ w` ยุบแกนสินทรัพย์ให้เหลือ `(จำนวนเส้นทาง, จำนวนปี)` การถ่วงด้วยน้ำหนักเดิมทุกปีหมายถึงกลับสู่น้ำหนักนั้นต้นปี ไม่ใช่ buy-and-hold น้ำหนักที่ลอยต่อเนื่องตลอด 30 ปี

`wealth_real` มี 31 คอลัมน์ รวมเงินต้นที่เวลา 0 ส่วนเงินจ่ายมี 30 คอลัมน์ตาม 30 สิ้นปี `np.minimum` จำกัดการจ่ายไม่เกินเงินที่มี ถ้าทุนเหลือศูนย์และไม่มีเงินเติม ทุนจะเป็นศูนย์ต่อไป และรายจ่ายปีต่อไปจะถูกบันทึกเป็น unpaid

ยอดถอนเป็น cash flow แยกจากผลตอบแทนลงทุน อย่านำ `(wealth_after / wealth_before) - 1` ไปเรียกผลตอบแทนกองทุนโดยไม่ปรับเงินจ่าย เช่น พอร์ตได้กำไรแต่ถอนเงินมาก มูลค่ากองทุนก็อาจลดลงได้ การวัด drawdown ของมูลค่าหลังจ่ายเงินจึงไม่ใช่ investment drawdown ของดัชนีที่ไม่มี cash flow

<span id="real-versus-nominal-wealth"></span>

## ตรวจเส้นทางเดียวให้ตรงก่อนรันทั้งหมด

ผลตอบแทนจริงเมื่อ nominal return เป็น $R$ และเงินเฟ้อเป็น $i$ เท่ากับ

$$R^{\rm real}=\frac{1+R}{1+i}-1.$$

การลบ $R-i$ เป็นเพียงค่าประมาณ ไม่ใช่สูตร exact เมื่อกลับไปใช้เงินจริง recurrence จึงเขียนได้ว่า

$$W_t=\max\left\{W_{t-1}\frac{1+R_{p,t}}{1+i}-c,0\right\},
\qquad W_t=V_t/I_t.$$

```python
endowment_demo = simulate_endowment(endowment_returns[:1, :3], endowment_weights,
    endowment_initial, endowment_spending, endowment_inflation)
print(pd.DataFrame({"Nominal return (%)": 100 * endowment_demo["portfolio_returns"][0],
    "Real spending paid": endowment_demo["paid_real"][0],
    "End-year real wealth": endowment_demo["wealth_real"][0, 1:]}, index=[1, 2, 3]).round(4))
endowment_first_return = endowment_demo["portfolio_returns"][0, 0]
endowment_first_real = (1 + endowment_first_return) / (1 + endowment_inflation) - 1
print(f"First-year real return: {100 * endowment_first_real:.4f}%")
print("First-year real wealth check:", round(100 * (1 + endowment_first_real) - 2.5, 6))
```

เส้นทางแรกได้ nominal return ปีแรกประมาณ 7.6849% คิดเป็น real return 5.5735% จึงมีเงินจริงหลังจ่ายประมาณ $100(1.05573476)-2.5=103.073476$ ล้านบาท อีกสองปีถัดไปเหลือประมาณ 106.9174 และ 104.2938 ล้านบาทจริง

แม้ปีที่สองมีสถานะ Stress ในการสุ่ม ผลตอบแทนพอร์ตปีนั้นยังบวกได้ สถานะกำหนดการแจกแจงของผลตอบแทน ไม่ได้บังคับเครื่องหมายทุก observation และกฎพอร์ต 60/40 นี้ไม่ใช้ป้ายสถานะมาทำนายหรือตัดสินใจเปลี่ยนน้ำหนัก

<span id="endowment-shortfall-definitions"></span>

## แยกเงินปลายทางไม่ถึงเป้าจากการจ่ายไม่ครบ

กำหนดเป้าทุนปลายปี 30 เป็น 50 ล้านบาทในกำลังซื้อปีฐาน เราจะนับสองเหตุการณ์แยกกัน:

- Terminal shortfall: เงินจริงปลายปี 30 ต่ำกว่า 50 ล้านบาท
- Any unpaid spending: มีอย่างน้อยหนึ่งปีที่จ่ายเงินจริง 2.5 ล้านบาทไม่ครบ

กองทุนอาจจ่ายครบทุกปีแต่เหลือทุนเพียง 40 ล้านบาท จึงเกิดเหตุการณ์แรกโดยไม่เกิดเหตุการณ์ที่สอง ส่วนในแบบจำลองที่ไม่มีเงินเติมนี้ การจ่ายไม่ครบทำให้เงินหลังจ่ายเป็นศูนย์ และจึงต่ำกว่าเป้าปลายทางบวกด้วย

```python
endowment_markov = simulate_endowment(endowment_returns, endowment_weights,
    endowment_initial, endowment_spending, endowment_inflation)
endowment_iid = simulate_endowment(endowment_iid_returns, endowment_weights,
    endowment_initial, endowment_spending, endowment_inflation)
endowment_goal = 50.0

def endowment_statistics(result, goal):
    terminal = result["wealth_real"][:, -1]
    shortfall = terminal < goal
    missed_payment = np.any(result["unpaid_real"] > 1e-10, axis=1)
    return {"Mean terminal wealth": terminal.mean(), "Median terminal wealth": np.median(terminal),
            "5th percentile terminal wealth": np.quantile(terminal, 0.05),
            "Terminal shortfall probability": shortfall.mean(),
            "Any unpaid spending probability": missed_payment.mean()}

endowment_summary = pd.DataFrame({"Markov": endowment_statistics(endowment_markov, endowment_goal),
                                 "IID": endowment_statistics(endowment_iid, endowment_goal)}).T
print(endowment_summary.round(6).to_string())
```

`terminal < goal` สร้าง Boolean หนึ่งค่าต่อเส้นทาง ค่า `True` ถูกนับเป็นหนึ่งเมื่อหา mean จึงได้สัดส่วนเส้นทางที่พลาดเป้าหมาย ส่วน `any(..., axis=1)` ตรวจว่ามี unpaid อย่างน้อยหนึ่งปีในแต่ละเส้นทางก่อนคำนวณ mean ต้องไม่เฉลี่ยช่อง unpaid ทุกปีแล้วเรียกว่าโอกาสที่เส้นทางหนึ่งเคยจ่ายไม่ครบ

| ผลจาก 20,000 เส้นทาง | Markov | IID |
|---|---:|---:|
| Mean เงินจริงปลายทาง | 40.7139 | 33.1662 |
| Median เงินจริงปลายทาง | 20.2575 | 19.3570 |
| Percentile 5 ของเงินจริงปลายทาง | 0 | 0 |
| โอกาสเงินปลายทางต่ำกว่า 50 | 70.315% | 75.635% |
| โอกาสเคยจ่ายไม่ครบ | 29.550% | 26.165% |

Mean สูงกว่า median มากเพราะบางเส้นทางจบด้วยทุนสูง ขณะที่หลายเส้นทางเหลือทุนต่ำหรือศูนย์ การดู mean อย่างเดียวจึงไม่เห็นรูปร่างของผลลัพธ์ สำหรับ input ชุดนี้ Markov มีโอกาสพลาดเป้าปลายทางต่ำกว่า แต่มีโอกาสเคยจ่ายไม่ครบสูงกว่า IID การจัดอันดับความเสี่ยงจึงเปลี่ยนตามเหตุการณ์ที่ถาม

สองโมเดลมี one-year marginal distribution เดียวกันเมื่อเริ่ม stationary แต่ผลตอบแทนข้ามปีใน Markov มี dependence ผ่านสถานะ ลำดับปีที่ดีหรือไม่ดีติดกันส่งผลต่อการทบต้นและเงินที่เหลือหลังใช้จ่าย ผลนี้ไม่ใช่ข้อสรุปว่าโมเดล Markov ให้ผลดีกว่าหรือแม่นกว่าตลาดจริงโดยทั่วไป

<span id="endowment-monte-carlo-error"></span>

## วัดความคลาดเคลื่อนจากจำนวนเส้นทาง

ถ้าสุ่ม $N$ เส้นทางเป็นอิสระ และนับได้สัดส่วน shortfall $\widehat p$ ค่า MC standard error ของสัดส่วนประมาณด้วย

$$\operatorname{SE}(\widehat p)=\sqrt{\frac{\widehat p(1-\widehat p)}{N}}.$$

ส่วน mean เงินปลายทางใช้ sample SD ของเงินปลายทางหาร $\sqrt N$ ไม่ใช้ volatility ของผลตอบแทนรายปีแทน เพราะเป็นสถิติคนละตัว

```python
endowment_shortfall = endowment_markov["wealth_real"][:, -1] < endowment_goal
endowment_probability = endowment_shortfall.mean()
endowment_probability_se = np.sqrt(endowment_probability * (1 - endowment_probability) / endowment_n)
endowment_terminal = endowment_markov["wealth_real"][:, -1]
endowment_terminal_se = endowment_terminal.std(ddof=1) / np.sqrt(endowment_n)
print(f"Shortfall probability: {100 * endowment_probability:.4f}%")
print(f"Probability MC standard error: {100 * endowment_probability_se:.4f} percentage points")
print(f"Mean terminal wealth MC standard error: {endowment_terminal_se:.6f}")
```

สำหรับ Markov ได้ probability 70.315% และ MC SE ประมาณ 0.3231 จุดเปอร์เซ็นต์ ส่วน mean เงินปลายทางมี SE ประมาณ 0.387201 ล้านบาทจริง ตัวเลขนี้วัดความคลาดเคลื่อนจากการสุ่ม finite paths ภายใต้โมเดลเดิม ไม่รวมความคลาดเคลื่อนของ transition, means, covariance, เงินเฟ้อ หรือนโยบายจ่ายเงิน

หากจำลองแล้วไม่พบ shortfall เลย สูตร plug-in ข้างต้นจะให้ SE ศูนย์ ซึ่งไม่ได้พิสูจน์ว่าเหตุการณ์เป็นไปไม่ได้ ต้องรายงานจำนวนเส้นทางและใช้ขอบเขตความน่าจะเป็นที่เหมาะสม เช่น ขอบบนแบบ binomial เมื่อพบศูนย์เหตุการณ์ แทนการสรุปความเสี่ยงศูนย์

จำนวนปี 30 ไม่ใช่จำนวนตัวอย่างอิสระเพิ่มอีก 30 เท่าสำหรับ terminal shortfall หนึ่งเส้นทางให้คำตอบเหตุการณ์ปลายทางเพียงหนึ่งค่า จึงใช้ $N=20{,}000$ เป็นตัวหารของ SE

<span id="paired-simulation-comparison"></span>

## เปรียบเทียบสองโมเดลโดยรักษาคู่การสุ่ม

เนื่องจากใช้ random numbers ร่วมกัน ผลของ Markov และ IID ในเส้นทางหมายเลขเดียวกันจึงสัมพันธ์กัน หากต้องการ SE ของความต่าง probability ให้สร้าง

$$D_n=\mathbf1\{W^{\rm Markov}_{n,30}<50\}
-\mathbf1\{W^{\rm IID}_{n,30}<50\}.$$

$D_n$ เป็น −1, 0 หรือ 1 แล้วคำนวณ mean และ sample SD ของ $D_n$ โดยตรง

```python
endowment_iid_shortfall = endowment_iid["wealth_real"][:, -1] < endowment_goal
endowment_paired_difference = endowment_shortfall.astype(float) - endowment_iid_shortfall.astype(float)
endowment_difference_se = endowment_paired_difference.std(ddof=1) / np.sqrt(endowment_n)
print(f"Markov-minus-IID shortfall probability: {100 * endowment_paired_difference.mean():.4f} percentage points")
print(f"Paired-difference MC standard error: {100 * endowment_difference_se:.4f} percentage points")
```

ความต่าง Markov ลบ IID ได้ −5.3200 จุดเปอร์เซ็นต์ และ paired MC SE ประมาณ 0.2973 จุดเปอร์เซ็นต์ การรวม SE สองฝั่งแบบสมมติอิสระจะไม่ใช้ covariance ของการจับคู่ที่เราสร้างไว้

การจับคู่เส้นทางช่วยประเมินความต่างของโมเดลภายใต้ random inputs ร่วมกัน ไม่ใช่หลักฐานว่าทั้งสองโมเดลต้องให้ลำดับผลตอบแทนจริงแบบใด การทดสอบกับข้อมูลตลาดยังต้องประเมิน conditional distributions และ transition จากข้อมูลในอดีตที่กันช่วงตรวจไว้

<span id="spending-sensitivity"></span>

## เปลี่ยนรายจ่ายบนเส้นทางเดิม

คราวนี้คงผลตอบแทน Markov ทั้ง 20,000 เส้นทางไว้ แล้วเปลี่ยนรายจ่ายจริงเป็น 2.0, 2.5 และ 3.0 ล้านบาทต่อปี การใช้เส้นทางเดิมทำให้เปรียบเทียบผลของรายจ่ายโดยไม่ปนกับการสุ่มชุดใหม่

```python
endowment_sensitivity = []
for real_spending in [2.0, 2.5, 3.0]:
    result = simulate_endowment(endowment_returns, endowment_weights,
        endowment_initial, real_spending, endowment_inflation)
    row = {"Annual real spending": real_spending}
    row.update(endowment_statistics(result, endowment_goal))
    endowment_sensitivity.append(row)
endowment_sensitivity = pd.DataFrame(endowment_sensitivity)
print(endowment_sensitivity.round(6).to_string(index=False))
```

เมื่อเพิ่มรายจ่ายจาก 2.0 เป็น 3.0 ล้านบาท โอกาสพลาดเป้าปลายทางเพิ่มจาก 60.580% เป็น 78.585% และโอกาสเคยจ่ายไม่ครบเพิ่มจาก 17.100% เป็น 43.675% ภายใต้ผลตอบแทนและสมมติฐานชุดเดิม ในแต่ละเส้นทาง รายจ่ายที่มากขึ้นไม่ทำให้เงินคงเหลือมากขึ้น จึงตรวจความสอดคล้องนี้ได้ด้วยการเทียบรายเส้นทางด้วย

นี่เป็น sensitivity analysis สามค่าที่ตั้งไว้ ยังไม่ได้หานโยบายรายจ่ายที่เหมาะสม สำหรับนโยบายที่เปลี่ยนรายจ่ายตามทุน ต้องระบุว่าใช้ทุนก่อนหรือหลังผลตอบแทน ใช้ข้อมูลถึงเมื่อไร มี minimum spending หรือไม่ และเมื่อจ่ายไม่ครบยอดนั้นเป็นภาระผูกพันต่อหรือยกเลิกไป

หากจะเพิ่ม regime-aware allocation ต้องใช้ probability ที่คำนวณจากข้อมูลที่รู้ก่อนลงทุน รวมต้นทุนเมื่อเปลี่ยนน้ำหนัก และเทียบกับ fixed mix ภายใต้ cash flows เดียวกัน การใช้ hidden state ที่โปรแกรมรู้ตอนสร้างข้อมูลไปจัดพอร์ตโดยตรงจะทำให้นักลงทุนจำลองมีข้อมูลเหนือกว่าที่นักลงทุนจริงเห็น

<span id="endowment-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

1. เงินต้น 100 ผลตอบแทนสองปี +20% กับ −10% และถอนปลายปีปีละ 5 เหตุใดกำไรก่อนจึงจบสูงกว่า 1.5

<details><summary>เฉลยข้อ 1</summary>

กรณีกำไรก่อน เงิน 5 ที่ถอนปีแรกไม่ต้องรับผลตอบแทน −10% ในปีที่สอง ส่วนกรณีขาดทุนก่อน เงิน 5 ที่ถอนปีแรกพลาดผลตอบแทน +20% ของปีที่สอง ความต่างจึงเป็น $5[0.20-(-0.10)]=1.5$ ภายใต้ลำดับและ cash flow ที่กำหนด

</details>

2. รายจ่ายจริง 2.5 และเงินเฟ้อ 2% ต้องใช้เงิน nominal สิ้นปีที่สองเท่าไร

<details><summary>เฉลยข้อ 2</summary>

$2.5(1.02)^2=2.601$ ล้านบาท หากยังจ่าย nominal 2.5 เท่าเดิม กำลังซื้อของการจ่ายจะลดลง จึงเป็นคนละนโยบายกับรายจ่ายจริงคงที่

</details>

3. พอร์ตได้ nominal return 5% เงินเฟ้อ 2% เริ่มด้วยเงินจริง 100 และจ่ายเงินจริง 2.5 ปลายปี เหลือเงินจริงเท่าไร

<details><summary>เฉลยข้อ 3</summary>

$100(1.05/1.02)-2.5\approx100.441176$ ล้านบาท real return เท่ากับประมาณ 2.941176% ไม่ใช่ 3% พอดี

</details>

4. เหตุใดสถานะ Stress 30% ทุกปีจึงยังไม่ทำให้ Markov กับ IID ให้ terminal wealth distribution เดียวกัน

<details><summary>เฉลยข้อ 4</summary>

Marginal probability ของปีเดียวกันไม่กำหนด joint distribution ข้ามเวลา Markov ของตัวอย่างมีโอกาสอยู่ Stress ต่อ 65% ส่วน IID 30% ลำดับที่ติดกันต่างกันจึงเปลี่ยนผลการทบต้นและ cash flow แม้การแจกแจงรายปีเหมือนกัน

</details>

5. ถ้า 20,000 เส้นทางมี 1,000 เส้นทางที่เคยจ่ายไม่ครบ โดยแต่ละเส้นทางขาดเฉลี่ยสี่ปี โอกาสเคยจ่ายไม่ครบเป็นเท่าไร

<details><summary>เฉลยข้อ 5</summary>

เท่ากับ $1000/20000=5\%$ ต้องนับเส้นทางที่เกิดอย่างน้อยหนึ่งครั้ง ไม่ใช่นำจำนวนปีที่ขาดทั้งหมด 4,000 หาร 20,000 แล้วตอบ 20% และไม่ใช่หารด้วยจำนวนช่อง path–year แล้วเรียกเป็นเหตุการณ์ระดับเส้นทาง

</details>

6. ต้องการลด MC SE ของ probability จากประมาณ 0.32 เป็น 0.16 จุดเปอร์เซ็นต์ ควรเพิ่มจำนวนเส้นทางเป็นเท่าไรโดยประมาณ

<details><summary>เฉลยข้อ 6</summary>

เพิ่มสี่เท่าจาก 20,000 เป็น 80,000 เส้นทาง เมื่อโมเดลและ probability ใกล้เดิม เพราะ SE แปรตาม $1/\sqrt N$ การเพิ่มจำนวนนี้ไม่ลดความผิดพลาดจากโมเดลที่ตั้ง transition หรือผลตอบแทนผิด

</details>

7. ถ้าปีหนึ่งมีเงินหลังผลตอบแทนเท่ากับ 1 ล้านบาทจริง แต่ต้องจ่าย 2.5 ฟังก์ชันบันทึกอะไร

<details><summary>เฉลยข้อ 7</summary>

จ่ายได้ 1 บันทึก unpaid 1.5 และเงินหลังจ่ายเป็นศูนย์ ในแบบจำลองนี้ไม่มีการกู้หรือเงินเติม และไม่ยก unpaid ไปเป็นยอดหนี้ปีต่อไป หากนโยบายจริงถือว่ายังติดค้าง ต้องเพิ่มบัญชี liability แยก

</details>

8. โปรแกรมรู้ว่าเส้นทางปีหน้าจะอยู่ Stress แล้วลดน้ำหนัก A ก่อนปีนั้น เป็น backtest ที่ใช้ข้อมูลได้จริงหรือไม่

<details><summary>เฉลยข้อ 8</summary>

ไม่ใช่ในแบบจำลอง hidden regime นี้ ป้ายสถานะเป็นข้อมูลของผู้สร้าง simulation นักลงทุนเห็น observations และต้องอนุมาน probabilities ที่รู้ทันเวลา หากต้องการวัดประโยชน์ของข้อมูลสมบูรณ์อาจทำเป็น oracle comparison ได้ แต่ต้องติดป้ายว่ามีข้อมูลที่นักลงทุนจริงไม่มี และไม่ปะปนกับกลยุทธ์ปฏิบัติได้

</details>

<span id="endowment-sources"></span>

## แหล่งที่มาและขอบเขตของตัวอย่าง

ทีมอ่าน transcript เต็มของ [A multi regime model for a University Endowment](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/84L90/a-multi-regime-model-for-a-university-endowment) และ [NEW Lab session: regime-based investment model](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/031T3/new-lab-session-jupyter-notebook-on-regime-based-investment-model) รวมทุกช่วงของ Lab เมื่อ 3 ตุลาคม 2026 พร้อมหน้า [รายการอ้างอิงการวิเคราะห์ regimes](https://www.coursera.org/learn/python-machine-learning-for-investment-management/supplement/qmtwE/references-for-the-module-machine-learning-techniques-for-regime-analysis)

ไม่ได้ตรวจหรือรัน instructor Notebook โดยตรง และไม่แจกข้อมูลหรือโค้ดของผู้สอน การบรรยายกับ Lab ใช้ความถี่ เกณฑ์การใช้จ่าย และเกณฑ์ขาดทุนบางส่วนต่างกัน บทนี้จึงระบุตัวอย่างใหม่เป็นรายปี ใช้เงินเฟ้อคงที่ และจ่ายหลังผลตอบแทนอย่างสอดคล้องกันทุกขั้น

การใช้ simulation ประเมินหลายเส้นทางต่อจาก [บท Monte Carlo](monte-carlo.html) และการแยกทรัพย์สินจากเป้าหมายต่อจาก [Goal-based Allocation](goal-based-allocation.html) ผลที่รายงานเป็นผลของโมเดล bounded shocks, Markov/IID และนโยบายจ่ายเงินที่แสดงไว้ทั้งหมด ไม่ใช่ผลทดสอบกองทุนมหาวิทยาลัยแห่งใดหรือข้อเสนออัตราการใช้จ่ายจริง
