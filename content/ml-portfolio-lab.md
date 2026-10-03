---
title: "จากข้อมูลรายวันสู่พอร์ตที่ทดสอบได้"
description: "ตรวจข้อมูลผลตอบแทน ทบต้นเป็นรายสัปดาห์ ประมาณ Mean–Covariance และจัดพอร์ต GMV/MSR ก่อนติดตาม Buy-and-hold, Cash และค่าซื้อขายในช่วงที่กันไว้"
---

# จากข้อมูลรายวันสู่พอร์ตที่ทดสอบได้

<p class="lead">หลังสร้างคำพยากรณ์ เราต้องแปลงข้อมูลและสมมติฐานให้เป็นการถือเงินจริง บทนี้ฝึกตั้งแต่ผลตอบแทนรายวัน ไปจนถึงเลือกน้ำหนักจากอดีตแล้วติดตามพอร์ตในช่วงถัดไป พร้อมตรวจว่าการทบต้น การปรับน้ำหนัก และค่าซื้อขายเปลี่ยนคำตอบอย่างไร</p>

Lab ของคอร์สใช้การจัดพอร์ตเพื่อเชื่อมงานข้อมูลกับงานลงทุน การคำนวณ mean–variance ด้วย optimizer เป็นขั้นตัดสินใจจัดสรรเงิน ไม่ใช่การฝึก classifier โดยตัวมันเอง ในบทนี้เราจะใช้ค่าเฉลี่ยย้อนหลังเป็นตัวประมาณ expected return ก่อน หากภายหลังแทนด้วยค่าพยากรณ์ ML กฎเรื่องเวลาที่รู้ข้อมูลและการกันช่วงทดสอบยังเหมือนเดิม

โค้ดใช้ข้อมูลสมมติที่สร้างขึ้นใหม่ทั้งหมด พร้อม NumPy, pandas และ SciPy ไม่ต้องโหลด CSV หรือไฟล์ของคอร์ส รันเรียงใน Notebook ใหม่ได้ หากยังไม่คุ้นกับผลตอบแทนทศนิยม อ่าน[พื้นฐาน Returns](returns.html)ก่อน และใช้[บททดสอบโมเดล](model-validation.html)ทบทวนความต่างระหว่างข้อมูลฝึกกับข้อมูลที่กันไว้

<span id="ml-portfolio-daily-data"></span>

## หนึ่งแถวหมายถึงผลตอบแทนของช่วงใด

ตารางแรกมีสินทรัพย์ A และ B และผลตอบแทนจากราคาปิดวันก่อนถึงราคาปิดวันที่อยู่ใน index สมมติว่าเป็น total return ที่รวมเงินจ่ายออกและนำกลับลงทุนแล้ว หน่วย 0.01 หมายถึง 1% จึงไม่ต้องหาร 100 อีก

เราสร้างปฏิทินตัวอย่างสองสัปดาห์ สัปดาห์ละห้าวัน ไม่มีวันหยุด และใส่ผลตอบแทน B ที่หายไปหนึ่งวันเพื่อศึกษาวิธีจัดการ ข้อมูลจริงต้องตรวจปฏิทินตลาดของสินทรัพย์ ไม่ใช้สมมติฐานห้าวันกับทุกสัปดาห์โดยอัตโนมัติ

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize, brentq

daily_returns = pd.DataFrame({
    "A": [0.01, -0.02, 0.005, 0.0, 0.015, -0.01, 0.02, -0.005, 0.01, 0.0],
    "B": [0.002, 0.002, 0.002, 0.002, 0.002, 0.002, np.nan, 0.002, 0.002, 0.002],
}, index=pd.bdate_range("2024-01-08", periods=10))
missing_daily_counts = daily_returns.isna().sum()
print(daily_returns)
print("Missing observations:", missing_daily_counts.to_dict())
```

`pd.bdate_range` สร้างวันที่จันทร์ถึงศุกร์ในตัวอย่าง `np.nan` หมายถึงค่าที่ไม่มี ส่วน `.isna()` สร้างตาราง True/False แล้ว `.sum()` นับจำนวนช่องที่หายต่อสินทรัพย์ ได้ A ศูนย์ช่องและ B หนึ่งช่อง

การเติมผลตอบแทนที่หายด้วยศูนย์จะตั้งสมมติฐานว่าสินทรัพย์ไม่เปลี่ยนมูลค่าในวันนั้น ทั้งที่เราอาจเพียงไม่มีข้อมูล การใช้ค่าจากอนาคตมาเติมย้อนหลังก็อาจทำให้ feature รู้ข้อมูลเกินเวลา ต้องหาสาเหตุของช่องว่างก่อน เช่น วันหยุด ตลาดไม่เปิด ราคาไม่ถูกส่งมา หรือสินทรัพย์ยังไม่เริ่มซื้อขาย

<span id="ml-portfolio-weekly-data"></span>

## รวมผลตอบแทนด้วยการคูณ Gross Return

ผลตอบแทนหนึ่งสัปดาห์ที่มีห้าวันคือ

$$
r_{\mathrm{week}}=\prod_{d=1}^{5}(1+r_d)-1.
$$

ถ้าบวกผลตอบแทนจะละเลยการเปลี่ยนฐานเงิน เช่น +10% แล้ว −10% ทำให้เงิน 100 เหลือ 99 ผลตอบแทนรวมจึงเป็น −1% การ resample ต่อไปจัดข้อมูลเป็นกลุ่มสัปดาห์สิ้นสุดวันศุกร์ แล้วคูณ gross return ในแต่ละกลุ่ม

```python
weekly_observation_counts = daily_returns.resample("W-FRI").count()
weekly_from_daily = (1 + daily_returns).resample("W-FRI").prod(min_count=5) - 1
first_week_a_by_hand = np.prod(1 + daily_returns["A"].iloc[:5]) - 1
print("Counts by week:\n", weekly_observation_counts)
print("Weekly returns (%):\n", (100 * weekly_from_daily).round(4))
print("First week A matches:", np.isclose(weekly_from_daily["A"].iloc[0], first_week_a_by_hand))
```

A ได้ประมาณ 0.9670% ในสัปดาห์แรก และ 1.4799% ในสัปดาห์ที่สอง ส่วน B ได้ 1.0040% ในสัปดาห์แรกและ `NaN` ในสัปดาห์ที่สอง `min_count=5` กำหนดให้คำนวณเมื่อมีค่าครบห้าตัว จึงไม่ปล่อยให้ผลคูณของเพียงสี่วันดูเหมือนผลตอบแทนครบสัปดาห์ อ่านพฤติกรรมนี้ได้ใน [pandas Resampler.prod](https://pandas.pydata.org/pandas-docs/version/2.3/reference/api/pandas.core.resample.Resampler.prod.html)

เกณฑ์ห้าค่าใช้ได้กับปฏิทินสมมติที่กำหนดไว้เท่านั้น สัปดาห์ที่มีวันหยุดและเหลือสี่วันทำการอาจมีข้อมูลครบแล้ว และข้อมูลที่เริ่มกลางสัปดาห์อาจยังไม่ครบแม้ไม่มี `NaN` ในไฟล์ ควรตรวจจำนวนวันที่คาดว่าจะมีตามปฏิทิน ไม่เพียงลบสัปดาห์แรกและสุดท้ายทุกครั้ง

การเลือกหุ้นที่มีข้อมูลครบจนถึงวันสุดท้ายก่อนย้อนกลับไปทดสอบอดีตอาจใช้ความรู้เรื่องการอยู่รอดของหุ้นในอนาคตด้วย สำหรับการทดลองจริงต้องกำหนดรายชื่อที่ลงทุนได้ ณ แต่ละวันและนโยบายช่องว่างจากข้อมูลที่มีอยู่ในเวลานั้น

<span id="ml-portfolio-train-test"></span>

## สร้างชุดฝึกและกันช่วงติดตามพอร์ต

สองสัปดาห์ไม่พอประมาณความเสี่ยงของพอร์ต ต่อไปเป็นข้อมูลสมมติอีกชุดหนึ่งที่สร้างเป็นรายสัปดาห์โดยตรง มีสามสินทรัพย์ A, B และ C รวม 156 สัปดาห์ กำหนด 104 สัปดาห์แรกไว้ประมาณน้ำหนัก และ 52 สัปดาห์หลังไว้ติดตามพอร์ต วิธีและวันแบ่งถูกกำหนดก่อนดูผลช่วงหลัง

ค่าที่ใช้สร้างโลกจำลองคือค่าเฉลี่ยรายสัปดาห์ 0.20%, 0.15%, 0.10% และ volatility 1.50%, 1.10%, 0.70% ตามลำดับ Correlation เป็นตารางที่ระบุในโค้ด เราสุ่ม simple returns จาก multivariate Normal เพื่อสร้างแบบฝึกหัดคงพารามิเตอร์ ไม่มีการอ้างว่าตลาดจริงมี distribution นี้

```python
portfolio_rng = np.random.default_rng(20261004)
portfolio_assets = ["A", "B", "C"]
generating_weekly_mean = np.array([0.0020, 0.0015, 0.0010])
generating_weekly_vol = np.array([0.015, 0.011, 0.007])
generating_correlation = np.array([[1.0, 0.35, 0.15], [0.35, 1.0, 0.25], [0.15, 0.25, 1.0]])
generating_weekly_cov = np.outer(generating_weekly_vol, generating_weekly_vol) * generating_correlation
portfolio_returns = pd.DataFrame(
    portfolio_rng.multivariate_normal(generating_weekly_mean, generating_weekly_cov, size=156),
    index=pd.date_range("2020-01-03", periods=156, freq="W-FRI"), columns=portfolio_assets,
)
portfolio_train = portfolio_returns.iloc[:104].copy()
portfolio_test = portfolio_returns.iloc[104:].copy()
rf_weekly = 0.0005
assert portfolio_returns.index.is_unique and (portfolio_returns > -1).all().all()
assert portfolio_train.index.max() < portfolio_test.index.min()
print("Training ends:", portfolio_train.index.max().date())
print("Held-out weeks:", len(portfolio_test), portfolio_test.index.min().date(), portfolio_test.index.max().date())
```

`np.outer(vol, vol)` สร้างตารางผลคูณ $\sigma_i\sigma_j$ แล้วคูณ correlation รายช่องเพื่อได้ covariance วันที่สิ้นสุดข้อมูลฝึกคือ 24 ธันวาคม 2021 และข้อมูลทดสอบครอบคลุม 31 ธันวาคม 2021 ถึง 23 ธันวาคม 2022

ทุกค่าผลตอบแทนในเส้นทางที่ได้มากกว่า −100% จึงคูณเป็นมูลค่าที่เป็นบวกได้ อย่างไรก็ตาม Normal ของ simple return ยังให้โอกาสค่าต่ำกว่า −100% ในทางทฤษฎี การตรวจตัวอย่างนี้ผ่านไม่ทำให้สมมติฐานนั้นเหมาะกับการจำลองราคาจริงทั่วไป และไม่ได้ทำให้ราคากลายเป็น Lognormal แบบ GBM

`rf_weekly=0.0005` คือผลตอบแทนเงินสด 0.05% ต่อสัปดาห์ที่กำหนดคงที่และทราบล่วงหน้า อัตรานี้เป็น holding-period return โดยตรง จึงไม่ต้องแปลงจาก yield ของตั๋วเงิน Treasury ซึ่งมี convention การเสนอราคาและการถือครองอีกขั้นหนึ่ง

<span id="ml-portfolio-estimates"></span>

## ประมาณ Mean และ Covariance จาก Train เท่านั้น

ค่าเฉลี่ยที่ใช้สร้างการจำลองเป็นสิ่งที่เรารู้ในฐานะผู้สร้างแบบฝึกหัด แต่ผู้จัดพอร์ตในตัวอย่างเห็นเพียงผลตอบแทนย้อนหลัง เราจึงประมาณจาก `portfolio_train` โดยไม่ส่งพารามิเตอร์จริงให้ optimizer

```python
estimated_weekly_mean = portfolio_train.mean().to_numpy()
estimated_weekly_cov = portfolio_train.cov(ddof=1).to_numpy()
estimated_weekly_vol = np.sqrt(np.diag(estimated_weekly_cov))
estimate_table = pd.DataFrame({
    "sample_mean_weekly": estimated_weekly_mean,
    "sample_vol_weekly": estimated_weekly_vol,
    "annual_arithmetic_mean": 52 * estimated_weekly_mean,
    "annualized_vol": np.sqrt(52) * estimated_weekly_vol,
}, index=portfolio_assets)
covariance_eigenvalues = np.linalg.eigvalsh(estimated_weekly_cov)
print((100 * estimate_table).round(4))
print("Positive covariance eigenvalues:", covariance_eigenvalues)
```

ค่าเฉลี่ยตัวอย่างรายสัปดาห์ประมาณ −0.00754%, −0.03795% และ +0.07096% แม้ค่าเฉลี่ยที่ใช้สร้างโลกจำลองเป็นบวกทั้งหมด เราคงผลสุ่มนี้ไว้เพื่อเห็นว่าค่าประมาณในตัวอย่างจำกัดคลาดจากพารามิเตอร์จริงได้ ดูการคำนวณความไม่แน่นอนต่อใน [Expected Return](expected-return-estimation.html)

Covariance มีหน่วยผลตอบแทนทศนิยมยกกำลังสองต่อช่วง สูตร `.cov(ddof=1)` ใช้จำนวนแถวลบหนึ่งเป็นตัวหาร `np.diag` ดึง variance ของแต่ละสินทรัพย์ ส่วน `np.linalg.eigvalsh` คำนวณ eigenvalues ของเมทริกซ์สมมาตร ค่าเป็นบวกทุกตัวในชุดนี้จึงตรวจได้ว่า covariance เป็น positive definite และพอร์ตที่ไม่เป็นศูนย์มี variance เป็นบวก

การคูณ mean ด้วย 52 ให้ค่าเฉลี่ยเลขคณิตที่ปรับความถี่ ส่วนการคูณ SD ด้วย $\sqrt{52}$ ใช้กฎรวม variance เมื่อผลตอบแทนข้ามสัปดาห์ไม่มี autocovariance และสมมติว่าพารามิเตอร์ใช้ต่อเนื่องได้ ตัวเลขแรกไม่ใช่ CAGR และตัวเลขทั้งสองไม่ใช่ค่าที่รู้แน่ว่าจะเกิดในปีถัดไป

<span id="ml-portfolio-weight-functions"></span>

## น้ำหนักแปลงข้อมูลสินทรัพย์เป็นข้อมูลพอร์ต

ให้ $w_A+w_B+w_C=1$ และ $w_i\geq0$ น้ำหนักเท่ากันคือ $1/3$ ต่อสินทรัพย์ สำหรับน้ำหนักที่กำหนดก่อนช่วงผลตอบแทนหนึ่งสัปดาห์ ค่าเฉลี่ยและ volatility ที่ประมาณคือ

$$
\hat\mu_p=w^\mathsf{T}\hat\mu,\qquad
\hat\sigma_p=\sqrt{w^\mathsf{T}\hat\Sigma w}.
$$

Sharpe ratio รายสัปดาห์ใช้ส่วนเกินจากเงินสด $\hat\mu_p-r_f$ หารด้วย SD เราใช้เงินสดที่คงที่จึงมี SD ของ excess return เท่ากับ SD ของ total return สำหรับกรณีอัตราเงินสดเปลี่ยน ต้องคำนวณ series ของ excess returns ให้ตรงกัน

```python
equal_weights = np.repeat(1 / 3, 3)

def estimated_variance(weights):
    return float(weights @ estimated_weekly_cov @ weights)

def estimated_sharpe(weights):
    return (weights @ estimated_weekly_mean - rf_weekly) / np.sqrt(estimated_variance(weights))

equal_weight_train_mean = float(equal_weights @ estimated_weekly_mean)
equal_weight_train_vol = np.sqrt(estimated_variance(equal_weights))
print(f"EW weekly mean: {equal_weight_train_mean:.5%}; volatility: {equal_weight_train_vol:.5%}")
print(f"EW annualized estimated Sharpe: {np.sqrt(52) * estimated_sharpe(equal_weights):.4f}")
```

ได้ mean ประมาณ 0.00849% และ volatility 0.81549% ต่อสัปดาห์ Mean ต่ำกว่าเงินสด 0.05% จึงมี estimated Sharpe ที่เป็นลบ ประมาณ −0.3670 เมื่อปรับด้วย $\sqrt{52}$ การได้ Sharpe ติดลบไม่ใช่ข้อผิดพลาดของสูตร แต่บอกว่าค่าเฉลี่ยส่วนเกินในช่วงที่ใช้ประมาณติดลบ

เครื่องหมาย `@` เป็นการคูณเวกเตอร์หรือเมทริกซ์ตามแนวที่กำหนด และ `float` คืนตัวเลขหนึ่งค่าให้ optimizer แทน array สูตรความเสี่ยงและ covariance อธิบายจากสองสินทรัพย์ได้ใน[พื้นฐานพอร์ต](portfolio-basics.html)

<span id="ml-portfolio-gmv"></span>

## หา Global Minimum Variance ภายใต้ข้อจำกัด

[GMV](glossary.html#gmv) ลด $w^\mathsf{T}\hat\Sigma w$ โดยให้งบลงทุนรวมหนึ่งและไม่มี short ตรงนี้ไม่ใช้ estimated mean เป้าหมายจึงไม่ใช่หาผลตอบแทนสูงสุด เราใช้ `minimize` ของ SciPy และ `method="SLSQP"` เพื่อแก้โจทย์มีข้อจำกัด

`bounds` กำหนดแต่ละน้ำหนักอยู่ระหว่าง 0 กับ 1 ส่วน constraint แบบ `eq` กำหนดให้ฟังก์ชันมีค่าเป็นศูนย์ จึงเขียนเป็น `w.sum()-1` คูณ objective ด้วย $10^4$ เพื่อให้ขนาดตัวเลขสะดวกกับเกณฑ์หยุด โดยไม่เปลี่ยนน้ำหนักที่ทำให้ variance ต่ำที่สุด

```python
portfolio_bounds = [(0.0, 1.0)] * 3
budget_constraint = {"type": "eq", "fun": lambda w: w.sum() - 1}
optimizer_options = {"ftol": 1e-12, "maxiter": 1000}
gmv_result = minimize(lambda w: 1e4 * estimated_variance(w), equal_weights,
                      method="SLSQP", bounds=portfolio_bounds,
                      constraints=budget_constraint, options=optimizer_options)
assert gmv_result.success, gmv_result.message
gmv_weights = gmv_result.x
gmv_closed_form = np.linalg.solve(estimated_weekly_cov, np.ones(3))
gmv_closed_form /= gmv_closed_form.sum()
assert np.allclose(gmv_weights, gmv_closed_form, atol=1e-6)
assert np.isclose(gmv_weights.sum(), 1) and gmv_weights.min() >= -1e-9
print("GMV weights:", pd.Series(gmv_weights, index=portfolio_assets).round(6))
```

น้ำหนัก GMV ประมาณ A 3.13%, B 20.94% และ C 75.93% เราตรวจซ้ำด้วยสูตรไม่มีข้อจำกัด short คือ $\hat\Sigma^{-1}\mathbf1/(\mathbf1^\mathsf{T}\hat\Sigma^{-1}\mathbf1)$ ซึ่งบังเอิญให้น้ำหนักไม่ติดลบในชุดนี้ จึงเป็นคำตอบภายใต้ข้อจำกัด long-only ด้วย โค้ดใช้ `solve` แก้ระบบสมการโดยไม่สร้าง inverse โดยตรง

เมื่อ covariance เป็น positive definite ฟังก์ชัน variance เป็น convex และ constraints นี้เป็นเซต convex จึงมีคำตอบ GMV เดียว หากข้อมูลอีกชุดให้สูตรปิดติดลบ จะนำสูตรนั้นมาใช้แทน long-only GMV ไม่ได้ ต้องแก้ข้อจำกัดให้ถูกต้อง

<span id="ml-portfolio-msr"></span>

## Max Sharpe อาจเลือกเพียงสินทรัพย์เดียว

ต่อไปลดค่าลบของ Sharpe เพื่อให้ `minimize` ทำงานเทียบเท่ากับการหา Sharpe สูงสุด ใช้ข้อจำกัดและ train ชุดเดิมกับ GMV การหา Sharpe สูงสุดเป็นโจทย์อัตราส่วน การที่ solver แจ้ง success เพียงอย่างเดียวไม่ใช่ข้อพิสูจน์ว่าได้ global optimum

```python
msr_result = minimize(lambda w: -estimated_sharpe(w), equal_weights,
                      method="SLSQP", bounds=portfolio_bounds,
                      constraints=budget_constraint, options=optimizer_options)
assert msr_result.success, msr_result.message
msr_weights = msr_result.x
estimated_excess_means = estimated_weekly_mean - rf_weekly
assert np.all(estimated_weekly_cov >= 0)
assert np.all(estimated_excess_means[:2] < 0) and estimated_excess_means[2] > 0
assert np.allclose(msr_weights, [0, 0, 1], atol=1e-6)
chosen_weights = pd.DataFrame({"EW": equal_weights, "GMV": gmv_weights, "MSR": msr_weights},
                              index=portfolio_assets)
print(chosen_weights.round(6))
print("Weekly excess mean estimates:", estimated_excess_means.round(7))
```

MSR ลง C เกือบ 100% เพราะ C เป็นตัวเดียวที่มีค่าเฉลี่ยสูงกว่าเงินสดในข้อมูลฝึก ทั้ง A และ B มี estimated excess mean ติดลบ ในชุดนี้ covariance ทุกช่องไม่ติดลบด้วย จึงตรวจคำตอบแยกจาก solver ได้:

เมื่อผลตอบแทนส่วนเกินของพอร์ตเป็นบวก จะมี $w_C>0$ และ $w^\mathsf{T}\hat e\leq w_C\hat e_C$ ขณะเดียวกัน $\hat\sigma_p\geq w_C\hat\sigma_C$ เนื่องจากพจน์อื่นใน variance ไม่ติดลบ ดังนั้น Sharpe ของพอร์ตไม่เกิน $\hat e_C/\hat\sigma_C$ ซึ่งการถือ C ล้วนทำได้ หากพอร์ตมี excess mean ไม่บวกก็ยิ่งไม่ชนะ Sharpe บวกของ C

นี่เป็นเหตุผลเฉพาะค่าประมาณและข้อจำกัดของตัวอย่าง ไม่ใช่กฎว่าควรถือสินทรัพย์ความผันผวนต่ำสุดเสมอ MSR ใช้ mean ที่คลาดเคลื่อนได้ จึงอาจกระจุกตัว แม้ชื่อโจทย์เกี่ยวกับการจัดพอร์ตหลายสินทรัพย์ก็ตาม

<span id="ml-portfolio-frontier"></span>

## ตรวจเส้น Target-return ก่อนเรียกว่า Efficient Frontier

เราลองกำหนดค่าเฉลี่ยเป้าหมายแล้วหา variance ต่ำที่สุดที่ทำได้ เมื่อห้าม short เป้าหมายต้องอยู่ระหว่างค่าเฉลี่ยต่ำสุดกับสูงสุดของสินทรัพย์ จากนั้นเพิ่มข้อจำกัด $w^\mathsf{T}\hat\mu=\mu_\mathrm{target}$

```python
frontier_targets = np.linspace(estimated_weekly_mean.min(), estimated_weekly_mean.max(), 7)
frontier_rows = []
for target in frontier_targets:
    target_constraint = {"type": "eq", "fun": lambda w, t=target: w @ estimated_weekly_mean - t}
    result = minimize(lambda w: 1e4 * estimated_variance(w), equal_weights,
                      method="SLSQP", bounds=portfolio_bounds,
                      constraints=[budget_constraint, target_constraint], options=optimizer_options)
    assert result.success, result.message
    assert abs(result.x @ estimated_weekly_mean - target) < 1e-9
    frontier_rows.append([target, np.sqrt(estimated_variance(result.x))])
target_return_frontier = pd.DataFrame(frontier_rows, columns=["weekly_mean", "weekly_vol"])
gmv_estimated_mean = float(gmv_weights @ estimated_weekly_mean)
target_return_frontier["on_efficient_branch"] = target_return_frontier["weekly_mean"] >= gmv_estimated_mean - 1e-9
print(target_return_frontier.round(6).to_string(index=False))
```

`np.linspace` แบ่งเป้าหมายเป็นเจ็ดค่าระยะเท่ากัน `lambda w, t=target` เก็บค่าเป้าหมายของรอบนั้นไว้ในฟังก์ชัน เป้าหมายที่ต่ำกว่า mean ของ GMV อยู่บนแขนที่ไม่มีประสิทธิภาพ: GMV มี mean สูงกว่าและ variance ไม่สูงกว่า จึงไม่เรียกจุดทุกจุดในตารางว่า efficient

การวาดเส้นด้วยค่าประมาณจาก train อธิบายโอกาสที่โมเดลคาดไว้ ไม่ได้แสดงชุดพอร์ตที่รู้ล่วงหน้าว่าจะมีผลตอบแทนและความเสี่ยงเท่านั้นจริง เปลี่ยนข้อมูลฝึกก็อาจได้เส้นและน้ำหนักต่างออกไป ดูภาพและวิธีหลายสินทรัพย์ใน[บท Efficient Frontier](efficient-frontier.html)

<span id="ml-portfolio-held-out-wealth"></span>

## ใช้น้ำหนักที่เลือกแล้วกับช่วงที่กันไว้

เราตัดสินใจหลังข้อมูลสัปดาห์สุดท้ายของ train ครบ แล้วซื้อสินทรัพย์ก่อนผลตอบแทน test สัปดาห์แรกเกิดขึ้น เริ่มด้วยเงินหนึ่งหน่วยและถือจำนวนหน่วยสินทรัพย์เดิมตลอด 52 สัปดาห์ ไม่มีการใส่เงินเพิ่ม ถอนเงิน หรือปรับกลับสู่น้ำหนักเป้าหมาย วิธีนี้เรียก buy-and-hold

ถ้าเงินตั้งต้นในสินทรัพย์ $i$ เท่ากับ $w_i$ มูลค่าปลายสัปดาห์ $t$ คือ $w_i\prod_{s=1}^t(1+r_{s,i})$ แล้วรวมทุกสินทรัพย์เป็นมูลค่าพอร์ต ฟังก์ชันต่อไปเตรียมทางเลือกค่าซื้อครั้งแรกไว้ด้วย แต่รอบแรกตั้งค่าเป็นศูนย์

```python
initial_portfolio_date = portfolio_train.index[-1]

def buy_hold_wealth(returns, weights, fee_rate=0.0):
    invested_amount = 1 / (1 + fee_rate)
    asset_values = (1 + returns).cumprod().mul(weights * invested_amount, axis="columns")
    path = asset_values.sum(axis="columns")
    return pd.concat([pd.Series([1.0], index=[initial_portfolio_date]), path])

heldout_gross_wealth = pd.DataFrame({name: buy_hold_wealth(portfolio_test, chosen_weights[name].to_numpy())
                                    for name in chosen_weights.columns})
heldout_gross_wealth["Cash"] = (1 + rf_weekly) ** np.arange(len(heldout_gross_wealth))
ew_terminal_asset_values = equal_weights * (1 + portfolio_test).prod().to_numpy()
ew_terminal_weights = ew_terminal_asset_values / ew_terminal_asset_values.sum()
print("Final gross wealth:", heldout_gross_wealth.iloc[-1].round(6).to_dict())
print("EW final weights:", np.round(ew_terminal_weights, 6))
```

ปลายช่วง เงินหนึ่งหน่วยของ EW, GMV และ MSR กลายเป็นประมาณ 1.061710, 1.055006 และ 1.072597 ตามลำดับ เงินสดที่เติบโต 0.05% ต่อสัปดาห์มีมูลค่าประมาณ 1.026334 ตัวเลขทั้งหมดมาจากเส้นทางสมมติเดียวและยังไม่หักค่าซื้อขาย

น้ำหนักปลายทางของ EW เป็นประมาณ 35.57%, 30.75% และ 33.68% เพราะสินทรัพย์เติบโตต่างกัน ถ้าใช้ `portfolio_test @ equal_weights` ทุกสัปดาห์ จะหมายถึงนำเงินกลับสู่น้ำหนักหนึ่งในสามก่อนแต่ละช่วง ซึ่งเป็นอีกนโยบายหนึ่ง เราจะคำนวณนโยบายนั้นพร้อมค่าซื้อขายภายหลัง

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/ml-portfolio-heldout-mobile.svg">
<img src="assets/charts/ml-portfolio-heldout.svg" alt="มูลค่าพอร์ต EW GMV MSR และเงินสดในช่วงทดสอบ 52 สัปดาห์ จากข้อมูลจำลอง" loading="lazy" width="720" height="560">
</picture>
<figcaption>น้ำหนักคำนวณจากข้อมูล 104 สัปดาห์แรก แล้วซื้อและถือใน 52 สัปดาห์ถัดไป จุดตั้งต้นอยู่ที่ 24 ธันวาคม 2021; จุดสุดท้าย 23 ธันวาคม 2022 รวม 53 จุด ไม่ปรับน้ำหนักระหว่างทาง เส้นทั้งหมดเป็นมูลค่าก่อนหักต้นทุนและใช้ข้อมูลจำลอง seed 20261004</figcaption>
</figure>

<span id="ml-portfolio-evaluation"></span>

## รายงานผลตอบแทนและความเสี่ยงที่เกิดขึ้นจริง

เริ่มจากมูลค่าพอร์ตที่มีจุดตั้งต้นหนึ่งหน่วย แล้วคำนวณผลตอบแทนแต่ละสัปดาห์เป็น $W_t/W_{t-1}-1$ วิธีนี้สะท้อนน้ำหนักที่ไหลไปจริงใน buy-and-hold จากนั้นคำนวณ CAGR, SD, Sharpe และ max drawdown ด้วย convention เดียวกัน

```python
def realized_summary(wealth, periods_per_year=52, cash_return=rf_weekly):
    returns = wealth.pct_change(fill_method=None).dropna()
    years = len(returns) / periods_per_year
    volatility = returns.std(ddof=1) * np.sqrt(periods_per_year)
    sharpe = np.sqrt(periods_per_year) * (returns.mean() - cash_return) / returns.std(ddof=1)
    drawdown = wealth / wealth.cummax() - 1
    return pd.Series({"total_return": wealth.iloc[-1] / wealth.iloc[0] - 1,
                      "cagr": (wealth.iloc[-1] / wealth.iloc[0]) ** (1 / years) - 1,
                      "annualized_vol": volatility, "annualized_sharpe": sharpe,
                      "max_drawdown": drawdown.min()})

heldout_summary = heldout_gross_wealth[["EW", "GMV", "MSR"]].apply(realized_summary).T
print(heldout_summary.round(6))
```

| พอร์ต | ผลตอบแทนรวม / CAGR ใน 52 ช่วง | Annualized volatility | Annualized Sharpe | Max drawdown |
|---|---:|---:|---:|---:|
| EW | 6.1710% | 6.0342% | 0.5916 | −5.8225% |
| GMV | 5.5006% | 3.7185% | 0.7598 | −3.2631% |
| MSR | 7.2597% | 3.8312% | 1.1706 | −1.8441% |

เราใช้ 52 ช่วงต่อปีเพื่อ annualize โดยวันที่เป็นป้ายรายสัปดาห์ ไม่ได้ใช้จำนวนวันปฏิทินแบบ ACT/365 ช่วง test มี 52 แถวพอดี ผลตอบแทนรวมจึงเท่ากับ CAGR ภายใต้ convention นี้ Max drawdown ใช้จุดตั้งต้นหนึ่งหน่วยร่วมในการหาจุดสูงสุดด้วย ทำให้ไม่หลงลืมการขาดทุนตั้งแต่สัปดาห์แรก

ผลช่วงหลังไม่ตรงกับค่าประมาณจาก train เพราะเป็นอีกตัวอย่างหนึ่ง และน้ำหนัก buy-and-hold เปลี่ยนไปตลอดทาง จึงไม่ควรอธิบายความต่างทั้งหมดว่าเกิดจาก skewness หรือ kurtosis ของผลตอบแทน ความคลาดเคลื่อนในการประมาณ นโยบายปรับน้ำหนัก และหน่วยเวลามีผลด้วย

GMV มี realized volatility ต่ำสุดในสามวิธีสำหรับเส้นทางนี้ แต่ชื่อ GMV หมายถึงต่ำสุดตาม covariance ที่ประมาณไว้ ไม่รับประกันว่าจะต่ำสุดในทุกช่วงที่ยังไม่เกิด เช่นเดียวกัน การที่ MSR ชนะผลตอบแทนในตารางนี้ยังไม่ใช่หลักฐานว่าการเลือก mean ย้อนหลังชนะตลาดจริง

<span id="ml-portfolio-cash"></span>

## ผสมเงินสดให้ตรงกับสมมติฐานการถือครอง

ให้สัดส่วนสินทรัพย์เสี่ยงเป็น $a=0.6$ และเงินสด 0.4 หากปรับกลับสัดส่วนนี้ทุกสัปดาห์โดยยังไม่คิดต้นทุน ค่าประมาณหนึ่งช่วงคือ

$$
\hat\mu_{\mathrm{mix}}=(1-a)r_f+a\hat\mu_p,
\qquad \hat\sigma_{\mathrm{mix}}=|a|\hat\sigma_p.
$$

สูตร SD ใช้เงินสดที่มีผลตอบแทนแน่นอน จึงมี variance และ covariance กับพอร์ตเสี่ยงเป็นศูนย์ ในตัวอย่าง MSR เท่ากับ C ล้วน การปรับน้ำหนักฝั่งเสี่ยงจึงไม่ซับซ้อน

```python
risky_fraction = 0.6
cash_mix_mean = (1 - risky_fraction) * rf_weekly + risky_fraction * (msr_weights @ estimated_weekly_mean)
cash_mix_vol = abs(risky_fraction) * np.sqrt(estimated_variance(msr_weights))
cash_mix_weekly_returns = risky_fraction * (portfolio_test @ msr_weights) + (1 - risky_fraction) * rf_weekly
cash_mix_wealth = pd.concat([
    pd.Series([1.0], index=[initial_portfolio_date]), (1 + cash_mix_weekly_returns).cumprod()
])
print(f"Estimated weekly mix mean: {cash_mix_mean:.5%}; volatility: {cash_mix_vol:.5%}")
print(f"Gross rebalanced cash-mix final wealth: {cash_mix_wealth.iloc[-1]:.6f}")
```

Estimated mean ประมาณ 0.06258% และ SD 0.39819% ต่อสัปดาห์ ลดสัดส่วนสินทรัพย์เสี่ยงเหลือ 60% จึงลด SD เหลือ 60% ของเดิมเมื่อใช้สมมติฐานนี้ เส้นที่ผสมเงินสดกับพอร์ตเสี่ยงที่กำหนดเรียก capital allocation line หรือ CAL ส่วนชื่อ CML ต้องมีเงื่อนไขดุลยภาพที่ทำให้พอร์ตเสี่ยงนั้นเป็น market portfolio เพิ่มเติม

หากให้ $a>1$ จะต้องกู้เงินและมีน้ำหนักเงินสดติดลบ สูตรที่ใช้ $r_f$ ตัวเดียวสมมติว่าสามารถกู้และให้กู้ในอัตราเดียวกันโดยไม่มีข้อจำกัดที่ขวางการจัดพอร์ต ตัวอย่างนี้เลือก $a=0.6$ จึงไม่ได้กู้เงิน ดูข้อจำกัดของการขยายเส้นต่อใน[บทการประมาณพอร์ต](portfolio-estimation.html#cal-cml)

<span id="ml-portfolio-costs"></span>

## จ่ายค่าซื้อขายจากเงินในพอร์ต

สมมติค่าซื้อขาย $c=0.001$ หรือ 0.1% ของมูลค่าที่ซื้อหรือขายแต่ละด้าน ไม่มีขั้นต่ำ ภาษี slippage หรือค่าขายปิดบัญชีปลายตัวอย่าง เราเริ่มด้วยเงินสดหนึ่งหน่วย ถ้าซื้อทั้งหมดโดยจ่ายค่าซื้อจากเงินนี้ มูลค่าสินทรัพย์ที่ซื้อได้คือ $V=1/(1+c)$ เพราะ $V+cV=1$ ฟังก์ชัน buy-and-hold ก่อนหน้ารองรับ convention นี้แล้ว

สำหรับการปรับกลับ EW ทุกสัปดาห์ ให้ $H_i$ เป็นมูลค่าสินทรัพย์เดิมก่อนซื้อขาย $W$ เป็นมูลค่ารวมก่อนจ่ายค่าธรรมเนียม และ $V$ เป็นมูลค่าที่เหลือหลังจ่าย เราต้องแก้

$$
V+c\sum_i|Vw_i-H_i|=W.
$$

ยอดซื้อขายของแต่ละตัวคือความต่างระหว่างมูลค่าเป้าหมายหลังหักค่าใช้จ่ายกับมูลค่าเดิม การบวกค่าสัมบูรณ์คิดทั้งยอดซื้อและยอดขาย จึงไม่มีตัวหารสองที่ใช้ในนิยาม one-way turnover บางแห่ง

```python
def rebalanced_wealth_with_fees(returns, weights, fee_rate):
    holdings = np.zeros(len(weights))
    path = [1.0]
    fees = []
    for row in returns.to_numpy():
        wealth_before = path[-1]
        remaining = brentq(lambda v: v + fee_rate * np.abs(v * weights - holdings).sum() - wealth_before,
                           0.0, wealth_before)
        fee_paid = fee_rate * np.abs(remaining * weights - holdings).sum()
        assert abs(remaining + fee_paid - wealth_before) < 1e-10
        holdings = remaining * weights * (1 + row)
        fees.append(fee_paid)
        path.append(holdings.sum())
    dates = pd.DatetimeIndex([initial_portfolio_date]).append(returns.index)
    return pd.Series(path, index=dates), np.array(fees)

trading_fee = 0.001
net_buy_hold_ew = buy_hold_wealth(portfolio_test, equal_weights, fee_rate=trading_fee)
net_rebalanced_ew, rebalancing_fees = rebalanced_wealth_with_fees(portfolio_test, equal_weights, trading_fee)
print(f"EW buy-and-hold net final: {net_buy_hold_ew.iloc[-1]:.6f}")
print(f"EW weekly-rebalanced net final: {net_rebalanced_ew.iloc[-1]:.6f}")
print(f"Total fees paid along rebalanced path: {rebalancing_fees.sum():.6f}")
```

`brentq` หาค่า $V$ ที่ทำให้สมการเป็นศูนย์ในช่วงตั้งแต่ 0 ถึง $W$ สำหรับน้ำหนัก long-only รวมหนึ่งและอัตราค่าธรรมเนียมระหว่าง 0 กับ 1 แบบนี้ สมการต่อเนื่องและเพิ่มตาม $V$ จึงมีคำตอบเดียว เราจ่ายค่าธรรมเนียมก่อน แล้วจึงคูณผลตอบแทนของสัปดาห์นั้น ไม่หักค่าใช้จ่ายจากเงินภายนอก

EW buy-and-hold หลังค่าซื้อครั้งแรกจบที่ประมาณ 1.060649 ส่วน EW ที่ปรับทุกสัปดาห์จบที่ 1.060472 และจ่ายค่าธรรมเนียมรวมระหว่างทางประมาณ 0.001362 หน่วยเงินตั้งต้น ความต่างระหว่างสองมูลค่าปลายทางไม่ได้เท่ากับผลรวมค่าธรรมเนียมโดยตรง เพราะมีทั้งน้ำหนักที่เปลี่ยนและเวลาที่จ่ายเงิน

ถ้าจะทดลองกฎปรับน้ำหนักอื่นจากผลตารางนี้ ถือเป็นการพัฒนาวิธีรอบใหม่ ต้องกันข้อมูลช่วงใหม่สำหรับประเมินขั้นตอนที่เลือกแล้ว ไม่เปลี่ยนนโยบายแล้วย้อนนำผลที่ดีที่สุดมาเรียกว่า test เดิมที่ยังไม่เคยใช้

<span id="ml-portfolio-exercises"></span>

## แบบฝึกหัดพร้อมวิธีคิด

### 1. ผลตอบแทน 2% สองวันรวมเป็นเท่าไร

$(1.02)^2-1=0.0404$ หรือ 4.04% ถ้าบวกเป็น 4% จะขาดผลจากการทบต้น 0.04 จุดเปอร์เซ็นต์

### 2. หายหนึ่งวัน เติมศูนย์ได้เลยหรือไม่

ต้องมีเหตุผลว่าผลตอบแทนจริงเป็นศูนย์ก่อน การไม่มีข้อมูลไม่ยืนยันข้อเท็จจริงนั้น ในตัวอย่างที่กำหนดให้ครบห้าวัน เราคืน `NaN` ให้สัปดาห์ของ B ที่หายหนึ่งค่า เพื่อไม่แสดงผลสี่วันเป็นผลครบสัปดาห์

### 3. ใช้ Mean ที่ผู้สร้าง Simulation รู้ได้หรือไม่

ทำได้หากต้องการ benchmark ที่ประกาศว่าใช้พารามิเตอร์จริงของโลกจำลอง แต่จะไม่เป็นการทดสอบนักลงทุนที่ต้องประมาณจากข้อมูล เราจึงเก็บ `generating_weekly_mean` แยกจาก `estimated_weekly_mean` และส่งเฉพาะตัวหลังให้ optimizer

### 4. ซื้อสองสินทรัพย์เท่ากันแล้วตัวหนึ่งขึ้น 10%

เริ่มด้วยสินทรัพย์ละ 50 หน่วย อีกตัวผลตอบแทนศูนย์ มูลค่าปลายทางเป็น 55 กับ 50 รวม 105 น้ำหนักตัวแรกจึงเป็น $55/105\approx52.38\%$ หากต้องการกลับไป 50/50 ต้องซื้อขายเพิ่ม จึงเป็นคนละนโยบายกับถือเฉย ๆ

### 5. GMV ต้องชนะผลตอบแทนหรือไม่

ไม่จำเป็น Objective ลด estimated variance ภายใต้ constraints ไม่ได้เพิ่ม mean และค่าที่เกิดใน test ก็อาจต่างจากค่าประมาณได้ ในตัวอย่าง GMV มีความผันผวนน้อยกว่าอีกสองวิธี แต่ผลตอบแทนปลายทางต่ำกว่าทั้งคู่

### 6. Target ต่ำกว่า GMV อยู่บนแขน Efficient หรือไม่

เมื่อ GMV มี mean สูงกว่า target นั้นและ variance ต่ำกว่าหรือเท่ากัน GMV ครอบงำจุดนั้นในมุม mean–variance จุดที่ลด variance ภายใต้ target ต่ำจึงไม่ใช่จุดบนแขน efficient แม้ optimizer แก้ target constraint ได้ถูกต้อง

### 7. เริ่มเงินหนึ่งหน่วยและค่าซื้อ 1% ซื้อได้เท่าไร

แก้ $V+0.01V=1$ ได้ $V=1/1.01\approx0.990099$ ค่าซื้อเป็น 0.009901 การลงทุนเต็มหนึ่งหน่วยแล้วจ่ายอีก 0.01 ต้องอาศัยเงินเพิ่มซึ่งต่างจากงบตั้งต้นหนึ่งหน่วยของโจทย์

### 8. ผลจาก Lab ต้นทางเป็น Out-of-sample หรือไม่

ใน transcript ของ Lab ผู้สอนตั้งวันเริ่มและวันจบของช่วง training กับช่วงประเมินให้เหมือนกัน ตัวอย่างส่วนนั้นจึงเป็น in-sample illustration เราขยายบทเรียนที่นี่ด้วย train 104 สัปดาห์และ holdout 52 สัปดาห์แยกกัน แต่ยังเป็นข้อมูลจำลองเพื่อฝึกกระบวนการ ไม่ใช่หลักฐานผลลงทุนในตลาดจริง

<span id="ml-portfolio-sources"></span>

## ที่มาและขอบเขต

อ่าน transcript เต็มของ [Lab Session: Optimal Portfolio](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/fZLXq/lab-session-optimal-portfolio) และหน้าประกอบ [Lab Session: Optimal Portfolio](https://www.coursera.org/learn/python-machine-learning-for-investment-management/supplement/sk2he/lab-session-optimal-portfolio) เมื่อ 3 ตุลาคม 2026 เนื้อหาต้นทางครอบคลุมการทำความสะอาดผลตอบแทนรายวัน การทบต้นรายสัปดาห์ mean–variance, Sharpe, เงินสด และการติดตาม wealth บทนี้สร้างข้อมูลและโค้ดใหม่ พร้อมแยกช่วงประมาณกับช่วงทดสอบ และนิยามค่าซื้อขายให้ชัดเจน

พบ ZIP ของ Lab ในหน้า Resources แต่การอ่านไฟล์ดาวน์โหลดถูกจำกัดโดยระบบ จึงไม่ได้ใช้เนื้อหา Notebook ภายใน ZIP เป็นแหล่งที่ตรวจยืนยัน โค้ดในหน้านี้ไม่อ้างว่าเป็นการรันหรือทำซ้ำผลของ Notebook นั้น และไม่มีข้อมูลดิบของคอร์สเผยแพร่ร่วมกับบทเรียน

ตรวจ API กับ [pandas Resampler.prod](https://pandas.pydata.org/pandas-docs/version/2.3/reference/api/pandas.core.resample.Resampler.prod.html), [SciPy SLSQP](https://docs.scipy.org/doc/scipy-1.13.1/reference/optimize.minimize-slsqp.html) และ [SciPy brentq](https://docs.scipy.org/doc/scipy-1.13.1/reference/generated/scipy.optimize.brentq.html) ข้อสรุปเชิงตัวเลขทุกจุดในตารางคำนวณจากข้อมูลสมมติที่แสดงไว้ในหน้านี้
