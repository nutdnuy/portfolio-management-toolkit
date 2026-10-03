---
title: "Market Regimes: ภาวะตลาดและข้อมูลที่รู้ได้ในเวลานั้น"
description: อ่าน transition matrix คำนวณความน่าจะเป็นของภาวะตลาด แยก filtering จาก smoothing และทดลอง first-difference penalty โดยไม่ใช้ป้ายย้อนหลังเป็นสัญญาณล่วงหน้า
---

# Market Regimes: ภาวะตลาดและข้อมูลที่รู้ได้ในเวลานั้น

<p class="lead">ผลตอบแทน −15% อาจเกิดในตลาดที่ผันผวนปกติหรือในช่วงที่ความเสี่ยงสูงขึ้น เราจะคำนวณว่าข้อมูลหนึ่งปีเปลี่ยนความเชื่อต่อภาวะตลาดอย่างไร และตรวจว่าตัวเลขใดต้องรอข้อมูลอนาคตก่อนจึงจะรู้ได้</p>

ภาวะตลาดหรือ regime คือสถานะของแบบจำลองที่มีลักษณะต่างกัน เช่น ค่าเฉลี่ย ความผันผวน หรือความสัมพันธ์ระหว่างสินทรัพย์ ตัวเลขปีปฏิทินเป็นเพียงเวลา สถานะเดียวกันอาจกลับมาเกิดหลายครั้ง และการขาดทุนหนึ่งงวดไม่ได้ทำให้รู้สถานะนั้นแน่นอน

[EWMA และ GARCH](time-varying-risk.html) ปรับความแปรปรวนตามข้อมูลที่ผ่านมา ส่วนตัวอย่างในบทนี้สมมติว่ามีสองสถานะและความน่าจะเป็นสำหรับย้ายระหว่างสถานะ จากนั้นจะทดลองอีกวิธีหนึ่งซึ่งประมาณระดับผลตอบแทนเป็นช่วง ๆ โดยไม่สมมติ transition matrix ทั้งสองวิธีมีสิ่งที่ประมาณต่างกัน จึงต้องอ่านชื่อผลลัพธ์ให้ตรงกับวิธี

โค้ดใช้ NumPy, pandas และ SciPy ตัวเลขทุกชุดเป็นตัวอย่างที่สร้างใหม่ หน่วยเวลาของตัวอย่าง Markov และชุดผลตอบแทนท้ายบทคือหนึ่งปี ไม่มีข้อมูลตลาดจริงหรือไฟล์จากผู้สอน

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm

np.set_printoptions(precision=6, suppress=True)
```

NumPy จัดการเวกเตอร์และเมทริกซ์ pandas ใช้แสดงตาราง `norm` ใช้คำนวณความหนาแน่น Normal ส่วน `minimize` จะหาค่าที่ทำให้ objective ต่ำที่สุด รันทุกบล็อกจากบนลงล่างใน Notebook ใหม่ได้

<span id="transition-probabilities"></span>

## อ่านโอกาสย้ายจากสถานะหนึ่งไปอีกสถานะ

ให้ $S_t$ เป็นสถานะในปี $t$: `0` คือ Calm และ `1` คือ Stress ชื่อทั้งสองเป็นป้ายสำหรับแบบจำลองสมมติ ไม่ใช่คำวินิจฉัยเศรษฐกิจจริง เรากำหนดเมทริกซ์

$$
P=\begin{pmatrix}0.85&0.15\\0.35&0.65\end{pmatrix},
\qquad P_{ij}=\Pr(S_{t+1}=j\mid S_t=i).
$$

อ่านจากแถวซึ่งเป็นสถานะปัจจุบันไปยังคอลัมน์ของปีถัดไป หากปีนี้ Calm ปีหน้ามีโอกาส Calm 85% และ Stress 15% หากปีนี้ Stress ปีหน้ามีโอกาสกลับ Calm 35% หรืออยู่ Stress ต่อ 65% แต่ละแถวจึงรวมเป็นหนึ่ง

สมมติฐาน Markov ในตัวอย่างบอกว่า เมื่อกำหนดสถานะปีนี้แล้ว โอกาสของปีหน้าขึ้นกับสถานะปีนี้ผ่าน $P$ โดยไม่ต้องรู้ลำดับสถานะก่อนหน้านั้นเพิ่ม เป็นข้อสมมติของแบบจำลอง ไม่ใช่ข้อพิสูจน์ว่าประวัติที่เก่ากว่าไม่มีข้อมูลในตลาด

```python
regime_transition = np.array([[0.85, 0.15], [0.35, 0.65]])
regime_names = ["Calm", "Stress"]
print(pd.DataFrame(regime_transition, index=regime_names, columns=regime_names))
print("Row sums:", regime_transition.sum(axis=1))
regime_now = np.array([1.0, 0.0])
print("Next year:", regime_now @ regime_transition)
print("Two years ahead:", regime_now @ np.linalg.matrix_power(regime_transition, 2))
```

`sum(axis=1)` รวมตามแต่ละแถว `regime_now = [1, 0]` เป็นกรณีสมมติว่ารู้ว่าปีนี้ Calm แน่นอน คูณ `@ P` หนึ่งครั้งได้ความน่าจะเป็นปีหน้า `[0.85, 0.15]` คูณสองครั้งได้ `[0.775, 0.225]`

คำนวณโอกาส Stress ในอีกสองปีด้วยมือได้ $0.85(0.15)+0.15(0.65)=0.225$ โดยรวมสองเส้นทางที่ลงท้าย Stress คือ Calm → Calm → Stress และ Calm → Stress → Stress โค้ด `matrix_power(P, 2)` คูณเมทริกซ์กับตัวเอง ไม่ใช่ยกกำลังแต่ละช่อง

บางไลบรารีเก็บ transition โดยให้คอลัมน์รวมเป็นหนึ่ง ตัวอย่างนี้ใช้แถวรวมเป็นหนึ่งตลอด จึงอัปเดตเวกเตอร์แถวด้วย `probability @ P` ต้องตรวจ convention ก่อนนำเมทริกซ์จากที่อื่นมาใช้ และห้ามนำ $P$ รายปีไปใช้เป็น $P$ รายเดือนโดยตรง

<span id="stationary-regime"></span>

## สัดส่วนระยะยาวไม่ใช่คำทำนายของปีหน้า

เวกเตอร์ stationary $\pi$ ทำให้ $\pi P=\pi$ เมื่อระบบเริ่มด้วยการแจกแจงนี้ การแจกแจงของสถานะในแต่ละปีจะยังเป็น $\pi$ สำหรับเมทริกซ์สองสถานะนี้

$$
\pi_{\rm Calm}=\frac{0.35}{0.15+0.35}=0.70,
\qquad \pi_{\rm Stress}=0.30.
$$

```python
regime_stationary = np.array([0.35, 0.15]) / (0.35 + 0.15)
regime_duration = 1 / (1 - np.diag(regime_transition))
print("Stationary probabilities:", regime_stationary)
print("Stationary check:", regime_stationary @ regime_transition)
print("Expected spell length in years:", regime_duration)
```

ผลตรวจคูณกลับได้ `[0.7, 0.3]` เมทริกซ์นี้มีโอกาสย้ายได้ทุกคู่ จึงมี stationary distribution เดียว และความน่าจะเป็นเมื่อเดินต่อหลายปีเข้าใกล้ค่านี้ แต่ถ้ารู้ว่าปีปัจจุบัน Stress โอกาส Stress ปีหน้าคือ 65% ไม่ใช่ 30%

ระยะเวลาคาดหมายของการอยู่สถานะเดิมติดต่อกัน นับตั้งแต่ปีที่เริ่มอยู่สถานะนั้น เท่ากับ $1/(1-P_{ii})$ เพราะแต่ละปีมีโอกาสออกจากสถานะ $1-P_{ii}$ ได้ประมาณ 6.6667 ปีสำหรับ Calm และ 2.8571 ปีสำหรับ Stress เป็นค่าเฉลี่ยของหลายเหตุการณ์ ไม่ใช่กำหนดเวลาว่าสถานะต้องจบเมื่อครบจำนวนนั้น

<span id="regime-observations"></span>

## มองไม่เห็นสถานะโดยตรง แต่เห็นผลตอบแทน

แบบจำลองนี้เรียกว่า **Hidden Markov Model (HMM)**: สถานะเปลี่ยนตามกฎ Markov แต่เรามองไม่เห็นสถานะโดยตรง เห็นเพียงข้อมูลที่มีการแจกแจงขึ้นกับสถานะนั้น จึงต้องใช้ข้อมูลที่สังเกตได้ช่วยปรับความน่าจะเป็นของแต่ละสถานะ

คราวนี้เราไม่รู้ว่าแต่ละปีอยู่ในสถานะใด เห็นเพียงผลตอบแทน $R_t$ สมมติว่าเมื่อกำหนดสถานะแล้ว

$$
R_t\mid S_t=s\sim\mathcal N(\mu_s,\sigma_s^2),
$$

โดย Calm มีค่าเฉลี่ย 8% และ SD 10% ต่อปี ส่วน Stress มีค่าเฉลี่ย −12% และ SD 20% ต่อปี และผลตอบแทนแต่ละปีเป็นอิสระกันเมื่อกำหนดลำดับสถานะแล้ว Normal สองชุดนี้ทับซ้อนกัน: ปีที่ผลตอบแทนบวกจึงอาจยังอยู่ Stress ได้

เราเริ่มก่อนเห็นผลตอบแทนปีแรกด้วยความน่าจะเป็น `[0.7, 0.3]` แล้วพบผลตอบแทน +5% ให้ $f_s(0.05)$ เป็นความหนาแน่นของผลตอบแทนนี้ภายใต้สถานะ $s$ กฎ Bayes ให้

$$
\Pr(S_1=s\mid R_1=0.05)
=\frac{\pi_s f_s(0.05)}{\sum_j\pi_j f_j(0.05)}.
$$

```python
regime_mu = np.array([0.08, -0.12])
regime_sd = np.array([0.10, 0.20])
regime_observed = np.array([0.05, 0.09, -0.15, -0.22, 0.03, 0.06])
regime_likelihood = norm.pdf(regime_observed[0], loc=regime_mu, scale=regime_sd)
regime_first = regime_stationary * regime_likelihood
regime_first /= regime_first.sum()
print("First-year likelihood densities:", regime_likelihood)
print("First-year filtered probabilities:", regime_first)
```

`norm.pdf` รับค่าเฉลี่ยผ่าน `loc` และ SD ผ่าน `scale` ความหนาแน่นได้ประมาณ 3.813878 กับ 1.389924 ความหนาแน่นไม่ใช่ probability ของจุดเดียว จึงมากกว่าหนึ่งได้ สิ่งที่ใช้คือความหนาแน่นสัมพัทธ์คูณ prior แล้วหารผลรวม

สำหรับ Stress ได้ $0.3(1.389924)/[0.7(3.813878)+0.3(1.389924)]\approx0.135089$ ข้อมูล +5% ทำให้ความน่าจะเป็น Stress ลดจาก 30% เป็นประมาณ 13.51% ภายใต้พารามิเตอร์ชุดนี้

Normal ของ simple return มีโอกาสทางทฤษฎีให้ค่าต่ำกว่า −100% ที่นี่ใช้เพื่อสอนการอนุมานจากตัวเลขผลตอบแทน ไม่ได้สร้างกระบวนการราคาที่รับรองราคาเป็นบวก บท [จำลองเงินทุนพร้อมการใช้จ่าย](endowment-simulation.html) จะใช้ผลตอบแทนมีขอบเขตสำหรับคำนวณเงินคงเหลือ

<span id="filtered-regime-probabilities"></span>

## เดินไปข้างหน้าทีละปีด้วย filtering

ในปีที่ $t$ มีสองขั้นตอนที่ต้องเก็บเวลาให้ถูก:

1. ก่อนเห็น $R_t$ คำนวณ predicted probability จาก filtered probability ปีที่แล้วคูณ $P$
2. หลังเห็น $R_t$ ใช้ Bayes อัปเดตเป็น filtered probability ของปีนี้

หลังจากนั้นค่อยใช้ filtered probability ทำนายสถานะปี $t+1$ หากต้องตัดสินใจก่อนปี $t$ เริ่ม เราใช้ค่าที่อัปเดตหลังเห็น $R_t$ ไม่ได้

```python
def filter_regimes(observed, transition, prior, means, sds):
    observed = np.asarray(observed, dtype=float)
    transition = np.asarray(transition, dtype=float)
    prior = np.asarray(prior, dtype=float)
    means, sds = np.asarray(means, dtype=float), np.asarray(sds, dtype=float)
    k = len(prior)
    if (observed.ndim != 1 or len(observed) == 0
        or transition.shape != (k, k) or means.shape != (k,) or sds.shape != (k,)
        or not all(np.isfinite(a).all() for a in [observed, transition, prior, means, sds])
        or np.any(transition <= 0) or not np.allclose(transition.sum(axis=1), 1)
        or np.any(prior <= 0) or not np.isclose(prior.sum(), 1) or np.any(sds <= 0)):
        raise ValueError("Check observations, probabilities, shapes and positive SDs")
    predicted = np.empty((len(observed), k))
    filtered = np.empty_like(predicted)
    next_prior = prior.copy()
    for t, value in enumerate(observed):
        predicted[t] = next_prior
        log_mass = np.log(next_prior) + norm.logpdf(value, means, sds)
        mass = np.exp(log_mass - log_mass.max())
        filtered[t] = mass / mass.sum()
        next_prior = filtered[t] @ transition
    return predicted, filtered

regime_predicted, regime_filtered = filter_regimes(
    regime_observed, regime_transition, regime_stationary, regime_mu, regime_sd)
print(pd.DataFrame({"Return (%)": 100 * regime_observed,
    "Stress before return": regime_predicted[:, 1],
    "Stress after return": regime_filtered[:, 1]}, index=np.arange(1, 7)).round(6))
```

ฟังก์ชันรับผลตอบแทนหนึ่งมิติ เมทริกซ์ transition เวกเตอร์ prior ค่าเฉลี่ย และ SD ของแต่ละสถานะ โค้ดนี้จำกัด prior และช่อง transition ให้เป็นบวก ตรวจผลรวมความน่าจะเป็น และคืนสองตารางรูป `(จำนวนปี, จำนวนสถานะ)` `empty` จองพื้นที่ก่อนเติมค่าทีละแถว ส่วน `enumerate` ให้ทั้งตำแหน่งและผลตอบแทนในแต่ละรอบ

ภายในใช้ log-density บวก log-prior แล้วลบค่ามากที่สุดก่อน `exp` เป็นวิธีรักษาสัดส่วนเดียวกับการคูณความหนาแน่น โดยช่วยลดปัญหาตัวเลขเล็กมากเมื่อข้อมูลอยู่ไกลจากค่าเฉลี่ย `copy()` ป้องกันไม่ให้การอัปเดตไปเปลี่ยน prior ที่ส่งเข้ามา

หลังเห็นผลตอบแทน −15% ในปีที่สาม ความน่าจะเป็น Stress เพิ่มจากประมาณ 18.73% ก่อนเห็นข้อมูลเป็น 61.60% หลังเห็นข้อมูล ปีที่สี่ซึ่งได้ −22% ทำให้เพิ่มเป็น 97.11% ส่วนปีที่ห้าได้ +3% แต่ filtered probability ยังประมาณ 42.72% เพราะมีทั้ง prior จากสถานะก่อนหน้าและข้อมูลปีใหม่เข้ามาร่วมกัน

ตัวเลขทั้งหมดใช้พารามิเตอร์ที่กำหนดไว้ล่วงหน้า หากในงานจริงประมาณ $P,\mu,\sigma$ จากข้อมูลทั้งชุดก่อน แล้วค่อยเรียกผลว่า filtered ก็ยังมีข้อมูลอนาคตรั่วผ่านพารามิเตอร์อยู่ ต้องประมาณพารามิเตอร์จากช่วงที่มีจริง ณ วันตัดสินใจด้วย

<span id="smoothed-regime-probabilities"></span>

## smoothing ใช้อนาคตเพื่ออธิบายอดีต

Filtered probability คือ $\Pr(S_t\mid R_1,\ldots,R_t)$ ส่วน smoothed probability คือ $\Pr(S_t\mid R_1,\ldots,R_T)$ เมื่อ $T$ เป็นปลายชุดข้อมูล จึงใช้ปีที่เกิดหลัง $t$ มาช่วยตีความด้วย [เอกสาร statsmodels](https://www.statsmodels.org/stable/examples/notebooks/generated/markov_autoregression.html) แยกความหมายนี้ไว้ชัดเจน

เมื่อคำนวณ filtering ครบแล้ว เราเริ่มจากปีสุดท้ายซึ่งยังไม่มีอนาคตเพิ่ม แล้วเดินย้อนหลัง การเห็นปีถัดไปที่มีโอกาส Stress สูงจะส่งข้อมูลย้อนมายังปีปัจจุบันผ่าน transition

```python
def smooth_regimes(transition, predicted, filtered):
    smoothed = filtered.copy()
    for t in range(len(filtered) - 2, -1, -1):
        ratio = np.divide(smoothed[t + 1], predicted[t + 1],
                          out=np.zeros_like(smoothed[t + 1]), where=predicted[t + 1] > 0)
        smoothed[t] = filtered[t] * (transition @ ratio)
        smoothed[t] /= smoothed[t].sum()
    return smoothed

regime_smoothed = smooth_regimes(regime_transition, regime_predicted, regime_filtered)
print(pd.DataFrame({"Filtered stress": regime_filtered[:, 1],
                    "Smoothed stress": regime_smoothed[:, 1]}, index=np.arange(1, 7)).round(6))
```

`smooth_regimes` ใช้ตารางที่ได้จากฟังก์ชันก่อนหน้าเท่านั้น ไม่ใช่ตัวประมาณพารามิเตอร์ชุดใหม่ ปีที่สองมี filtered Stress ประมาณ 7.45% แต่ smoothed เพิ่มเป็น 22.50% เพราะผลตอบแทนติดลบมากในปีที่สามและสี่ช่วยอธิบายย้อนหลัง ส่วนปีสุดท้าย filtered กับ smoothed เท่ากันเพราะใช้ข้อมูลถึงจุดเดียวกัน

<details><summary>สูตรที่ใช้ในขั้นย้อนหลัง</summary>

ให้ $a_t(i)$ เป็น filtered probability, $b_{t+1}(j)$ เป็น predicted probability และ $c_t(i)$ เป็น smoothed probability จะได้

$$c_t(i)=a_t(i)\sum_j P_{ij}\frac{c_{t+1}(j)}{b_{t+1}(j)}.$$

โค้ดคำนวณอัตราส่วนตามคอลัมน์ปีถัดไป แล้วใช้ `transition @ ratio` รวมผลต่อสถานะปัจจุบัน จากนั้น normalize เพื่อลดความคลาดเคลื่อนของเลขทศนิยม สูตรนี้อยู่ภายใต้ emission model และ transition ที่กำหนดไว้ ไม่ได้ใช้การคาดเดาป้ายจากเครื่องหมายผลตอบแทน

</details>

ลองแก้ผลตอบแทนปีสุดท้ายจาก +6% เป็น −40% โดยคงห้าปีแรกและพารามิเตอร์ทั้งหมดไว้

```python
regime_changed = regime_observed.copy()
regime_changed[-1] = -0.40
changed_predicted, changed_filtered = filter_regimes(
    regime_changed, regime_transition, regime_stationary, regime_mu, regime_sd)
changed_smoothed = smooth_regimes(regime_transition, changed_predicted, changed_filtered)
print("Earlier filtered values unchanged:", np.allclose(regime_filtered[:-1], changed_filtered[:-1]))
print(f"Year 5 smoothed stress before: {regime_smoothed[4, 1]:.6f}")
print(f"Year 5 smoothed stress after: {changed_smoothed[4, 1]:.6f}")
```

Filtered probabilities ห้าปีแรกไม่เปลี่ยน แต่ smoothed Stress ของปีที่ห้าเปลี่ยนจากประมาณ 32.10% เป็น 76.36% การแสดงป้าย smoothed บนกราฟย้อนหลังจึงใช้ศึกษาประวัติได้ แต่ถ้านำป้ายนั้นไปกำหนดพอร์ตที่อ้างว่าตัดสินใจในปีที่ห้า จะนำข้อมูลปีที่หกเข้ามาใช้ก่อนเวลา

<span id="first-difference-regimes"></span>

## ประมาณระดับเป็นช่วงด้วย first-difference penalty

อีกแนวทางไม่เริ่มจากสองสถานะหรือ transition แต่ประมาณระดับ $\beta_t$ ของผลตอบแทนแต่ละปีให้ใกล้ข้อมูล $y_t$ และเปลี่ยนระหว่างปีไม่บ่อยเกินไป โจทย์ที่ใช้คือ

$$
\min_{\beta}\ \frac12\sum_{t=1}^{T}(y_t-\beta_t)^2
+\lambda\sum_{t=2}^{T}|\beta_t-\beta_{t-1}|.
$$

พจน์แรกทำให้ระดับตามข้อมูล พจน์ที่สองลงโทษผลรวมขนาดการเปลี่ยนระดับ เรียกว่า total variation หรือ TV เมื่อใช้ผลต่างอันดับหนึ่งแบบนี้มักได้ระดับคงที่เป็นช่วง ๆ หรือ piecewise constant เป็นการประมาณระดับผลตอบแทน ไม่ใช่ราคาของสินทรัพย์

$\lambda$ มากขึ้นให้ความสำคัญกับการลดการเปลี่ยนระดับมากขึ้น แต่ penalty ไม่ได้นับจำนวนครั้งที่เปลี่ยนเครื่องหมาย และไม่ได้ให้ probability ว่าขณะนั้นอยู่สถานะเศรษฐกิจใด

```python
trend_y = np.array([0.06, 0.05, 0.08, 0.04, 0.07, -0.08, -0.10, -0.06,
                    -0.11, -0.07, 0.03, 0.04, 0.02, 0.05, 0.03, 0.01])
trend_D = np.diff(np.eye(len(trend_y)), axis=0)
print("First difference rows:")
print(trend_D[:2, :4])
print("First five differences:", (trend_D @ trend_y)[:5])
print(f"Raw total variation: {np.abs(trend_D @ trend_y).sum():.6f}")
```

`np.diff(np.eye(T), axis=0)` สร้างเมทริกซ์ $D$ ขนาด $(T-1)\times T$ แถวแรกมี −1 และ +1 เพื่อคำนวณ $y_2-y_1$ แถวถัดไปเลื่อนตำแหน่ง ผลต่างห้าตัวแรกคือ −0.01, 0.03, −0.04, 0.03, −0.15 ผลรวมค่าสัมบูรณ์ทั้งชุดเท่ากับ 0.61

ตัวอย่างนี้เปลี่ยนหน่วยผลตอบแทนจากทศนิยมเป็นเปอร์เซ็นต์ไม่ได้โดยคง $\lambda$ เดิมไว้ หากคูณ $y$ และ $\beta$ ด้วย 100 จะต้องคูณ $\lambda$ ด้วย 100 เพื่อให้โจทย์ให้รูปร่างคำตอบเดิม เพราะ squared loss กับ TV มีระดับกำลังต่างกัน

```python
def fused_level(observed, penalty):
    y = np.asarray(observed, dtype=float)
    if y.ndim != 1 or len(y) < 2 or not np.isfinite(y).all():
        raise ValueError("Need a finite one-dimensional series with at least two values")
    if not np.isfinite(penalty) or penalty < 0:
        raise ValueError("Penalty must be finite and nonnegative")
    D = np.diff(np.eye(len(y)), axis=0)
    if penalty == 0:
        return y.copy(), np.zeros(len(y) - 1)
    def objective(u):
        level = y - D.T @ u
        return 0.5 * (level @ level), -D @ level
    result = minimize(objective, np.zeros(len(y) - 1), jac=True,
        method="L-BFGS-B", bounds=[(-penalty, penalty)] * (len(y) - 1),
        options={"ftol": 1e-15, "gtol": 1e-10, "maxiter": 5000})
    if not result.success:
        raise RuntimeError(result.message)
    return y - D.T @ result.x, result.x

trend_penalty = 0.06
trend_level, trend_dual = fused_level(trend_y, trend_penalty)
print("Fitted annual levels:", np.round(trend_level, 4))
```

ฟังก์ชันคืนระดับที่ประมาณได้กับตัวแปรช่วย `trend_dual` เมื่อ $\lambda=0.06$ ระดับโดยประมาณคือ 4.8% ในห้าปีแรก, −6.0% ในห้าปีถัดมา และ 2.0% ในหกปีท้าย ค่าที่ใกล้กันระดับความละเอียดของเครื่องอาจไม่เท่ากันทุกหลัก จึงปัดเฉพาะตอนแสดงผล

<details><summary>เหตุใดโค้ดแก้โจทย์ด้วยตัวแปร u</summary>

Absolute value ไม่เรียบตรงศูนย์ เราใช้โจทย์ dual ที่มีขอบเขตง่ายแทน:

$$\min_{|u_j|\le\lambda}\frac12\|y-D^\top u\|_2^2,
\qquad \widehat\beta=y-D^\top\widehat u.$$

Gradient ต่อ $u$ คือ $-D(y-D^\top u)$ ฟังก์ชัน `objective` จึงคืนทั้งค่าและ gradient โดย `jac=True` บอก SciPy ว่ามี gradient ให้แล้ว `bounds` จำกัดทุกสมาชิกในช่วง $[-\lambda,\lambda]$ และ `result.success` ตรวจว่า solver แจ้งการลู่เข้า ดูความหมาย tolerance ใน [SciPy L-BFGS-B](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html)

เพื่อไม่อาศัยเพียงข้อความ success เราตรวจ primal–dual gap เพิ่ม โดยค่าฝั่ง dual ที่เป็น lower bound คือ $\frac12\|y\|^2-\frac12\|\widehat\beta\|^2$ ความต่างจาก objective เดิมควรใกล้ศูนย์ ค่าที่คำนวณได้เล็กน้อยไม่ใช่หลักฐานว่าพารามิเตอร์เหมาะกับตลาด เพียงตรวจว่าแก้โจทย์ที่กำหนดได้สอดคล้องกัน

</details>

```python
trend_residual = trend_y - trend_level
trend_primal = 0.5 * (trend_residual @ trend_residual) + trend_penalty * np.abs(trend_D @ trend_level).sum()
trend_dual_value = 0.5 * (trend_y @ trend_y) - 0.5 * (trend_level @ trend_level)
trend_gap = trend_primal - trend_dual_value
print(f"Fitted total variation: {np.abs(trend_D @ trend_level).sum():.6f}")
print(f"Primal-minus-dual gap: {trend_gap:.10f}")
print("Mean preserved:", np.isclose(trend_level.mean(), trend_y.mean()))
```

TV ลดจาก 0.61 เป็นประมาณ 0.188 และ gap ประมาณ $5.1\times10^{-9}$ ค่าเฉลี่ยของระดับยังเท่าค่าเฉลี่ยข้อมูล เพราะ penalty ลงโทษผลต่าง ซึ่งไม่เปลี่ยนเมื่อบวกค่าคงที่ให้ทุกปี

```python
trend_rows = []
for strength in [0.0, 0.03, 0.06, 0.20, 0.50]:
    fitted_level, _ = fused_level(trend_y, strength)
    trend_rows.append({"Penalty": strength,
        "Squared residual sum": np.sum((trend_y - fitted_level) ** 2),
        "Total variation": np.abs(np.diff(fitted_level)).sum()})
trend_path = pd.DataFrame(trend_rows)
print(trend_path.round(6))
```

ที่ penalty 0.03 TV ประมาณ 0.224 ส่วน penalty 0.20 เหลือประมาณ 0.024667 และ 0.50 ทำให้ระดับแทบเป็นเส้นคงที่ทั้งชุด ขณะเดียวกัน squared residual sum เพิ่มขึ้น เราจึงแลกความใกล้ข้อมูลกับความเรียบ ไม่ได้ทำให้ข้อมูลใหม่เกิดขึ้นจากการลดความแกว่ง

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/ml-tv-levels-mobile.svg">
<img src="assets/charts/ml-tv-levels.svg" alt="ผลตอบแทนสมมติ 16 ปี และระดับคงที่เป็นช่วงที่ประมาณด้วย total variation" loading="lazy" width="720" height="560">
</picture>
<figcaption>โค้ดใช้ผลตอบแทนทั้ง 16 ปีพร้อมกันและ penalty 0.06 ระดับที่ได้เป็น 4.8%, −6.0% และ 2.0% ต่อปี เส้นขั้นบันไดเชื่อมกึ่งกลางระหว่างปีเพื่อแสดงค่าที่ fit ไม่ใช่ป้ายภาวะตลาดที่ผู้ลงทุนรู้ล่วงหน้า</figcaption>
</figure>

<span id="trend-timing-and-order"></span>

## การ fit ทั้งชุดย้อนแก้ระดับในอดีตได้

แม้ชื่อวิธีมีคำว่า filtering แต่การแก้ objective ด้วยข้อมูลครบ 16 ปีเป็นการใช้ข้อมูลทั้งชุด ระดับปีที่สิบอาจเปลี่ยนเมื่อเติมปีที่สิบเอ็ดถึงสิบหก ลองเทียบกับการ fit เฉพาะสิบปีแรก

```python
trend_prefix, _ = fused_level(trend_y[:10], trend_penalty)
trend_revision = np.max(np.abs(trend_prefix - trend_level[:10]))
linear_level = np.array([0.01, 0.02, 0.03, 0.04])
print(f"Largest revision of first ten fitted levels: {trend_revision:.6f}")
print("First differences of a line:", np.diff(linear_level))
print("Second differences of a line:", np.round(np.diff(linear_level, n=2), 12))
```

คำตอบสิบปีแรกต่างกันมากที่สุดประมาณ 0.012 หรือ 1.2 จุดเปอร์เซ็นต์ การนำคำตอบที่ fit ยาวถึงปีที่สิบหกไปใช้เป็น signal ของปีที่สิบจึงผิดเวลา ต้องเก็บผลที่คำนวณได้ ณ แต่ละวันจริง และเลือก penalty จากอดีตด้วย

ผลต่างอันดับสองมีความหมายอีกอย่างหนึ่ง: เส้น `[0.01, 0.02, 0.03, 0.04]` มี first differences 0.01 ทุกจุด แต่ second differences เป็นศูนย์ การลงโทษ $\sum|\beta_{t+1}-2\beta_t+\beta_{t-1}|$ จึงสนับสนุนเส้นตรงเป็นช่วง ๆ หรือ piecewise linear งาน [Kim, Koh, Boyd และ Gorinevsky: L1 Trend Filtering](https://web.stanford.edu/~boyd/papers/l1_trend_filter.html) ใช้แนวทางผลต่างอันดับสองนี้ ไม่ควรเรียกผลของโค้ด first-difference ข้างต้นว่าเส้นแนวโน้มเชิงเส้นแบบเดียวกัน

การเพิ่มจำนวนสถานะหรือปรับ penalty จนแบ่งประวัติได้ละเอียดขึ้นต้องแลกกับพารามิเตอร์และความไม่แน่นอนที่เพิ่มขึ้น หากต้องการใช้กับการลงทุน ขั้นถัดไปคือกำหนดว่า probability หรือระดับที่รู้ทันเวลาจะเปลี่ยน [สถานการณ์ผลตอบแทนและ covariance](regime-scenarios.html) อย่างไร ก่อนทดสอบพอร์ตและต้นทุนในข้อมูลที่กันไว้

<span id="market-regime-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

1. ถ้าปีนี้รู้ว่า Stress โอกาส Calm ในปีหน้าและอีกสองปีเป็นเท่าไร

<details><summary>เฉลยข้อ 1</summary>

ปีหน้าคือ 35% อีกสองปีคือ $0.35(0.85)+0.65(0.35)=0.525$ หรือ 52.5% ต้องรวมทุกเส้นทางที่ลงท้าย Calm ไม่ใช่คูณ $0.35^2$

</details>

2. เพราะเหตุใด stationary Stress 30% จึงไม่แทน filtered Stress 97.11% ในปีที่สี่

<details><summary>เฉลยข้อ 2</summary>

30% เป็นสัดส่วนตาม stationary distribution ของ transition ส่วน 97.11% มีเงื่อนไขบนผลตอบแทนที่เห็นถึงปีที่สี่ จึงเป็นคำถามคนละเงื่อนไข หากต้องทำนายปีที่ห้าให้ใช้ filtered probability คูณ transition จะได้ predicted Stress ประมาณ 63.55%

</details>

3. ค่าความหนาแน่น 3.81 เป็น probability ที่ผิดเพราะเกินหนึ่งหรือไม่

<details><summary>เฉลยข้อ 3</summary>

ไม่ผิด ความหนาแน่นของตัวแปรต่อเนื่องมีหน่วยกลับของตัวแปรและเกินหนึ่งได้ Probability ได้จากการรวมความหนาแน่นบนช่วง ใน Bayes เราคูณ density กับ prior แล้ว normalize เพื่อให้ posterior probabilities รวมเป็นหนึ่ง

</details>

4. เหตุใดปีที่สองจึงมี smoothed Stress สูงกว่า filtered ทั้งที่ผลตอบแทนปีนั้น +9%

<details><summary>เฉลยข้อ 4</summary>

Smoothing ใช้ปีที่สามและสี่ซึ่งผลตอบแทนติดลบมากมาช่วยตีความอดีตผ่าน transition ด้วย ความต่างไม่ได้แปลว่า filtering คำนวณผิด แต่ข้อมูลที่ใช้ต่างกัน

</details>

5. ถ้า fit พารามิเตอร์ HMM ด้วยข้อมูลถึงปี 16 แล้วใช้ filtered probability ปี 10 ทดสอบกลยุทธ์ ยังมี look-ahead หรือไม่

<details><summary>เฉลยข้อ 5</summary>

มีได้ เพราะพารามิเตอร์ที่ใช้คำนวณปี 10 เรียนจากปี 11–16 ต้องควบคุมทั้งช่วงประมาณพารามิเตอร์และช่วง observations ที่ป้อนเข้า filter การใช้สูตรเดินไปข้างหน้าเพียงอย่างเดียวไม่ตัดการรั่วไหลจากขั้น fit

</details>

6. ชุดระดับ `[0, 0.02, 0]` มี TV เท่าไร และ penalty นับจำนวนครั้งที่ข้ามศูนย์หรือไม่

<details><summary>เฉลยข้อ 6</summary>

TV คือ $|0.02-0|+|0-0.02|=0.04$ เป็นผลรวมขนาดการเปลี่ยน ไม่ใช่จำนวนการข้ามศูนย์ ชุด `[0,0.2,0]` มีรูปการขึ้นลงเหมือนกันแต่ TV เท่ากับ 0.4 มากกว่าสิบเท่า

</details>

7. คูณผลตอบแทนทั้งหมดด้วย 100 แล้วต้องเปลี่ยน $\lambda=0.06$ เป็นเท่าไรเพื่อรักษารูปร่างคำตอบ

<details><summary>เฉลยข้อ 7</summary>

เปลี่ยนเป็น 6 เพราะการคูณข้อมูลและระดับด้วย 100 ทำให้ squared loss คูณ 10,000 และ TV คูณ 100 จึงต้องคูณ penalty อีก 100 ให้ objective ทั้งสองพจน์เปลี่ยนสเกลเท่ากัน

</details>

8. ระดับ `[0, 0.01, 0.02, 0.03]` มี first-difference และ second-difference penalty ต่างกันอย่างไร

<details><summary>เฉลยข้อ 8</summary>

ผลรวมค่าสัมบูรณ์ของ first differences คือ 0.03 ส่วน second differences ทุกตัวเป็นศูนย์ วิธีแรกลงโทษการเปลี่ยนระดับ วิธีที่สองลงโทษการเปลี่ยนความชัน

</details>

<span id="market-regime-sources"></span>

## แหล่งที่มาและขอบเขตของตัวอย่าง

เรียบเรียงหัวข้อจาก transcript เต็มของ [Introduction to economic regimes](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/CHpGz/introduction-to-economic-regimes), [Portfolio Decisions with Time-Varying Market Conditions](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/H2uZe/portfolio-decisions-with-time-varying-market-conditions) และ [Trend filtering](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/vDLHd/trend-filtering) ที่ทีมอ่านเมื่อ 3 ตุลาคม 2026 พร้อมหน้า [ข้อมูลประกอบวิดีโอ trend filtering](https://www.coursera.org/learn/python-machine-learning-for-investment-management/supplement/M2bDu/information-on-the-trend-filtering-video) ไม่ได้อ้างว่าอ่านรายงาน PDF แนบคอร์สครบ

ตัวอย่าง Bayes, transition และ TV รวมถึงโค้ดทั้งหมดเขียนขึ้นใหม่ ตรวจนิยาม filtered/smoothed กับเอกสาร statsmodels และตรวจความแตกต่างของผลต่างอันดับหนึ่งกับสองจากเอกสารผู้เขียน L1 Trend Filtering การอ่านแหล่งเหล่านี้ไม่ได้ทำให้สถานะสมมติสองสถานะกลายเป็นป้ายเศรษฐกิจที่ผ่านการทดสอบกับข้อมูลจริง
