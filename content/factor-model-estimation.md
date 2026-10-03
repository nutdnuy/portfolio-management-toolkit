---
title: "Lab Factor Model: ประมาณค่าและตรวจความเสถียร"
description: "ฝึกใช้ scikit-learn ประมาณ factor loadings ตรวจ residual covariance และทดลองว่าปัจจัยใกล้ซ้ำกับหน่วยข้อมูลทำให้ค่าประมาณเปลี่ยนอย่างไร"
---

<span id="factor-models-จ-ดข-อม-ลและอ-านค-า-loading"></span>

# Lab Factor Model: ประมาณค่าและตรวจความเสถียร

<p class="lead">Lab นี้ใช้ scikit-learn ประมาณ Factor Model จากข้อมูลที่รู้คำตอบ แล้วเปลี่ยนข้อมูลเพียงเล็กน้อยเพื่อดูว่า loading แกว่งได้มากเพียงใด เราจะตรวจทั้งค่าที่โมเดล fit ได้ ค่า residual และหน่วยของ coefficient ก่อนใช้ Ridge หรือ Lasso ในบทถัดไป</p>

ใช้แนวคิด OLS และ residual จาก [Factor Investing](factor-investing.html#ols-from-scratch) และสมการหลายปัจจัยจาก [Multifactor Models](multifactor-models.html#matrix-ols) เป็นพื้นฐาน ตัวอย่างด้านล่างสร้างข้อมูลและ import ใหม่ทั้งหมด จึงรัน Lab นี้แยกได้ โดยเน้นการเรียกใช้ไลบรารีและตรวจผลที่โปรแกรมคืนมา

<span id="factor-data-question"></span>

## กำหนดก่อนว่าหนึ่งแถวบอกอะไร

เราจะอธิบายผลตอบแทนของกองทุนสมมติด้วยปัจจัยสองตัว ได้แก่ `Market` ซึ่งเป็นผลตอบแทนพอร์ตตลาดสมมติ และ `Rate` ซึ่งเป็นผลตอบแทนพอร์ตพันธบัตรสมมติ ชื่อ `Rate` ในตัวอย่างนี้หมายถึงผลตอบแทนของพอร์ต ไม่ใช่ระดับอัตราดอกเบี้ยหรือการเปลี่ยนแปลงของ yield

| ข้อมูล | หนึ่งค่าหมายถึงอะไร | หน่วยที่เก็บใน Python |
|---|---|---|
| `Market` | ผลตอบแทนพอร์ตตลาดในเดือนนั้น | ทศนิยมต่อเดือน เช่น 0.02 คือ 2% |
| `Rate` | ผลตอบแทนพอร์ตพันธบัตรในเดือนเดียวกัน | ทศนิยมต่อเดือน |
| `Fund` | ผลตอบแทนกองทุนที่ต้องการอธิบาย | ทศนิยมต่อเดือน |
| index | เดือนของข้อมูลทั้งสามคอลัมน์ | เดือนปฏิทิน |

ข้อมูลทั้งหมดเป็นผลตอบแทนสมมติที่สร้างโดยตรงในโค้ด ไม่ต้องดาวน์โหลดราคาหรือเงินปันผลเพิ่ม ในงานจริงควรใช้ผลตอบแทนที่รวมการจ่ายเงินออกตามนิยามของชุดข้อมูล และตรวจสกุลเงิน ความถี่ และช่วงวันที่ให้ตรงกัน ถ้าใช้ excess return ต้องหักอัตราปลอดความเสี่ยงของช่วงเดียวกันตามนิยามโมเดล ไม่หักซ้ำจากปัจจัย long–short ที่เป็นผลต่างอยู่แล้ว

เริ่มด้วย NumPy สำหรับคำนวณอาร์เรย์ pandas สำหรับตาราง และ `LinearRegression` จาก scikit-learn สำหรับ Ordinary Least Squares หรือ OLS ซึ่งเลือกสมการด้วยผลรวม residual กำลังสอง ตัวอย่างทั้งหน้ารันต่อกันจาก namespace ว่างได้ โดยใช้ scikit-learn 1.6.1 ในการตรวจผล

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

np.set_printoptions(precision=6, suppress=True)
```

`import ... as ...` ตั้งชื่อย่อให้ไลบรารี ส่วน `from ... import ...` ดึงคลาสที่ต้องการมาใช้ `set_printoptions` ปรับการแสดงตัวเลขเท่านั้น ไม่ปัดค่าที่ใช้คำนวณจริง

```python
factor_dates = pd.period_range("2024-01", periods=8, freq="M")
market = np.array([-1, -1, -1, -1, 1, 1, 1, 1]) * 0.02
rate = np.array([-1, -1, 1, 1, -1, -1, 1, 1]) * 0.01
specific = np.array([-1, 1, -1, 1, -1, 1, -1, 1]) * 0.003
factor_data = pd.DataFrame({
    "Market": market,
    "Rate": rate,
    "Fund": 0.001 + 0.8 * market - 0.4 * rate + specific,
}, index=factor_dates)
print((factor_data * 100).round(2))
```

`np.array([...])` สร้างชุดตัวเลขที่คำนวณพร้อมกันได้ เช่น คูณทุกสมาชิกด้วย `0.02` ส่วน `pd.period_range` สร้างชื่อเดือนแปดเดือน เริ่มมกราคม 2024 และ `DataFrame` นำคอลัมน์มาเรียงตาม index เดียวกัน

ตารางที่พิมพ์คูณ 100 เพื่อให้อ่านเป็นเปอร์เซ็นต์ เดือนแรกได้ Market −2%, Rate −1% และ Fund −1.4% ส่วนตัวแปร `factor_data` ยังเก็บทศนิยมเดิม เราสร้าง Fund ด้วย loading ที่รู้ล่วงหน้าเพื่อใช้ตรวจวิธีประมาณค่า นักวิเคราะห์ที่ใช้ข้อมูลจริงจะเห็นเพียงตารางและไม่รู้ค่าที่ใช้สร้างผลตอบแทน

<span id="จากตารางไปเป-นสมการ"></span>

<span id="factor-equation-shapes"></span>

## จัด X และ y สำหรับส่งเข้า .fit

ใช้ [สมการหลายปัจจัย](multifactor-models.html#matrix-ols) กับ `Market` และ `Rate` ที่สร้างไว้: ผลตอบแทนกองทุนเท่ากับ intercept บวก loading คูณผลตอบแทนแต่ละปัจจัย แล้วบวก residual สำหรับ `LinearRegression` เราเก็บเฉพาะปัจจัยใน `X` และให้ estimator จัดการ intercept เอง จึงไม่เติมคอลัมน์หนึ่งเหมือนตัวอย่าง `np.linalg.lstsq` ในบทหลัก

```python
factor_X = factor_data[["Market", "Rate"]]
factor_y = factor_data["Fund"]
first_explained = 0.001 + factor_X.iloc[0].to_numpy() @ np.array([0.8, -0.4])
print("X shape:", factor_X.shape, "y shape:", factor_y.shape)
print(f"First explained return: {100 * first_explained:.2f}%")
print(f"First observed return: {100 * factor_y.iloc[0]:.2f}%")
```

วงเล็บคู่ `[["Market", "Rate"]]` เลือกตาราง `X` รูป `(8, 2)` ส่วน `factor_data["Fund"]` เลือก Series `y` รูป `(8,)` เครื่องหมาย `@` คูณสมาชิกที่ตรงกันแล้วรวม และ `.iloc[0]` เลือกเดือนแรก สมการที่ใช้สร้างข้อมูลให้ $0.001+0.8(-0.02)-0.4(-0.01)=-0.011$ หรือ −1.1% เทียบกับผลจริง −1.4% จึงเหลือ residual −0.3 จุดเปอร์เซ็นต์

แถว `X` และ `y` ต้องเป็นเดือนเดียวกัน การใส่ผลตอบแทนปัจจัยที่เกิดแล้วใช้ตรวจความสัมพันธ์ย้อนหลัง ส่วนการพยากรณ์ก่อนเดือนเริ่มยังต้องมีข้อสมมติของปัจจัย ตาม [เงื่อนไขด้านเวลา](multifactor-models.html#factor-data-timing)

<span id="ols-เล-อก-loading-อย-างไร"></span>

<span id="fit-and-residuals"></span>

## Fit ด้วย scikit-learn แล้วตรวจ residual

`LinearRegression(fit_intercept=True)` แก้ [โจทย์ OLS](factor-investing.html#ols-from-scratch) โดยประมาณทั้ง loading และ intercept ส่งตารางปัจจัยเข้า `.fit(X, y)` แล้วอ่านผลจาก estimator ที่ fit แล้ว

```python
factor_ols = LinearRegression(fit_intercept=True).fit(factor_X, factor_y)
factor_beta = pd.Series(factor_ols.coef_, index=factor_X.columns)
factor_alpha = factor_ols.intercept_
print("Loadings:")
print(factor_beta.round(6))
print(f"Monthly intercept: {100 * factor_alpha:.4f}%")
```

ได้ loading ของ Market เท่ากับ 0.8, Rate เท่ากับ −0.4 และ intercept เท่ากับ 0.1% ต่อเดือน `coef_` เก็บ loading หลังฝึก ส่วน `intercept_` เก็บค่าคงที่ ชื่อที่ลงท้ายด้วย `_` ใน scikit-learn มักใช้กับผลที่ได้จากการฝึกแล้ว

เราเลือกข้อมูลให้ residual ตั้งฉากกับปัจจัย จึงกู้ค่าที่ใช้สร้างข้อมูลได้พอดี ผลนี้ไม่ได้หมายความว่า OLS จะกู้ loading จริงได้พอดีในข้อมูลทั่วไป หรือว่าแปดเดือนเพียงพอต่อการใช้งานจริง

```python
factor_fitted = pd.Series(factor_ols.predict(factor_X), index=factor_X.index)
factor_residual = factor_y - factor_fitted
factor_rmse = np.sqrt(np.mean(factor_residual ** 2))
factor_r2 = 1 - np.sum(factor_residual ** 2) / np.sum((factor_y - factor_y.mean()) ** 2)
factor_cross = factor_X.to_numpy().T @ factor_residual.to_numpy()
print(f"RMSE: {100 * factor_rmse:.4f} percentage points per month")
print(f"In-sample R squared: {factor_r2:.6f}")
print("Residual mean:", round(factor_residual.mean(), 12))
print("X.T @ residual:", np.round(factor_cross, 12))
```

`.predict` นำสมการที่ฝึกแล้วมาใช้กับแต่ละแถว เราคำนวณ `observed - fitted` แล้วได้ RMSE (Root Mean Squared Error หรือรากของค่าเฉลี่ย residual กำลังสอง) 0.3 จุดเปอร์เซ็นต์ต่อเดือน และ $R^2$ ประมาณ 0.967972 ตัวแรกเป็นขนาด residual ในหน่วยเดียวกับผลตอบแทน ตัวหลังเปรียบเทียบผลรวม residual กำลังสองกับความแปรปรวนรอบค่าเฉลี่ยในชุดข้อมูลนี้

OLS ที่มี intercept และแก้ปัญหาได้ตรงตามสมการให้ residual มีค่าเฉลี่ยศูนย์และมี dot product กับแต่ละคอลัมน์ของ X เป็นศูนย์ นี่คือความตั้งฉากในข้อมูลที่ใช้ฝึก ไม่ได้พิสูจน์ว่า residual เป็นตัวแปรสุ่มที่เป็นอิสระจากปัจจัย หรือว่าความสัมพันธ์จะเหมือนเดิมในอนาคต

การตีความ intercept ต้องประเมิน [ความไม่แน่นอนของ alpha](factor-investing.html#scipy-ols) และ [ผลจากปัจจัยที่ตกหล่น](multifactor-models.html#omitted-factor-alpha) แยกจากการตรวจว่า `.fit` คืนคำตอบถูกต้องหรือไม่

<span id="ใช-สมการอธ-บายความเส-ยง"></span>

<span id="factor-risk-covariance"></span>

## ตรวจ covariance ที่สร้างกลับจากผล fit

ตรวจ [variance decomposition ของ Factor Model](multifactor-models.html#factor-risk-model) กับผลจาก `.fit` โดยคำนวณส่วน factor, residual และ variance ของ `y` แยกกัน ปัจจัยของชุดทดลองนี้ไม่มี covariance กัน แต่โค้ดยังคูณ covariance matrix เต็มเพื่อใช้ตรวจวิธีคำนวณ

```python
factor_cov = factor_X.cov(ddof=0).to_numpy()
factor_systematic_variance = factor_ols.coef_ @ factor_cov @ factor_ols.coef_
factor_specific_variance = factor_residual.var(ddof=0)
factor_total_variance = factor_y.var(ddof=0)
print(f"Factor variance: {factor_systematic_variance:.8f}")
print(f"Residual variance: {factor_specific_variance:.8f}")
print(f"Total variance: {factor_total_variance:.8f}")
print(f"Monthly SD: {100 * np.sqrt(factor_total_variance):.4f}%")
```

ตัวอย่างนี้ใช้ `ddof=0` ทุกพจน์เพื่อแยก variance ของแปดแถวที่มีอยู่ให้ตรงกัน ผลได้ 0.000272 จากปัจจัย และ 0.000009 จาก residual รวมเป็น 0.000281 หน่วยคือผลตอบแทนทศนิยมกำลังสองต่อหนึ่งเดือน ถอดรากได้ SD รายเดือน 1.6763% หากเลือก sample covariance แบบ `ddof=1` ต้องใช้ convention เดียวกันทุกพจน์ของการเปรียบเทียบ

สำหรับหลายกองทุน ให้แต่ละแถวของ $B$ เป็น loading ของหนึ่งกองทุน ให้ $\Sigma_F$ เป็น covariance ของปัจจัย และ $\Omega$ เป็น covariance ของ residual:

$$
\Sigma_Y=B\Sigma_F B^\mathsf T+\Omega.
$$

การบังคับ $\Omega$ ให้เป็น diagonal แปลว่าสมมติว่า residual ของแต่ละกองทุนไม่สัมพันธ์กัน ไม่ใช่ผลอัตโนมัติของการทำ OLS เราลองเพิ่มกองทุน B ซึ่งมี residual ร่วมกับกองทุน A บางส่วน

```python
second_noise = np.array([-1, 1, 1, -1, 1, -1, -1, 1]) * 0.002
factor_Y = pd.DataFrame({
    "Fund A": factor_y,
    "Fund B": 0.0005 + 1.2 * market + 0.1 * rate + 0.5 * specific + second_noise,
}, index=factor_dates)
factor_multi = LinearRegression().fit(factor_X, factor_Y)
factor_B = factor_multi.coef_
factor_E = factor_Y.to_numpy() - factor_multi.predict(factor_X)
factor_Omega = np.cov(factor_E, rowvar=False, ddof=0)
factor_full_cov = factor_B @ factor_cov @ factor_B.T + factor_Omega
factor_diagonal_cov = factor_B @ factor_cov @ factor_B.T + np.diag(np.diag(factor_Omega))
print("Residual covariance:")
print(np.array2string(factor_Omega, precision=8))
print("Full model covariance:")
print(np.array2string(factor_full_cov, precision=8))
print(f"Off-diagonal change if residual covariance is removed: {factor_full_cov[0, 1] - factor_diagonal_cov[0, 1]:.8f}")
```

`factor_Y` มีสองคอลัมน์จึงประมาณสองสมการพร้อมกันได้ `factor_B` มีขนาด 2 × 2: แถวเป็นกองทุน คอลัมน์เป็นปัจจัย ส่วน `np.cov(..., rowvar=False)` บอกว่าแต่ละคอลัมน์เป็นตัวแปรที่จะหา covariance

ได้ residual covariance ระหว่างกองทุนเท่ากับ 0.0000045 หากลบทิ้งด้วยสมมติฐาน diagonal covariance รวมระหว่างกองทุนจะลดลงเท่าจำนวนนี้ การลดจำนวนพารามิเตอร์จึงแลกกับข้อสมมติ ไม่ใช่การกำจัดความเสี่ยงที่เหลือจริง อ่านต่อได้ที่ [Factor Covariance และจำนวนพารามิเตอร์](covariance-estimation.html)

สำหรับตัวอย่าง OLS นี้ที่มี intercept และใช้ช่วงข้อมูลเดียวกัน การคง residual covariance เต็มจะสร้าง sample covariance ของกองทุนกลับมาได้ ส่วนการเปลี่ยน loading เป็นค่าจาก penalized regression ในบทถัดไปอาจทำให้ residual ไม่ตั้งฉากกับ X อีก การแยก covariance ของข้อมูลที่เกิดขึ้นจริงจึงต้องตรวจพจน์ไขว้ใหม่ ไม่ควรยกเอกลักษณ์ของ OLS ไปใช้โดยไม่ตรวจ

<span id="unstable-factor-loadings"></span>

## ปัจจัยใกล้ซ้ำกันทำให้ Loading แกว่ง

สร้าง `Proxy` ให้เกือบเหมือน Market แล้วประมาณกองทุนที่รับ Market loading 0.8 เราจะเปลี่ยนผลตอบแทนกองทุนเพียงเดือนละ ±0.00001 หรือ ±0.001 จุดเปอร์เซ็นต์

```python
near_X = pd.DataFrame({"Market": market, "Proxy": market + 0.001 * rate})
near_y = 0.001 + 0.8 * market + specific
near_ols = LinearRegression().fit(near_X, near_y)
changed_y = near_y + 0.00001 * (rate / 0.01)
changed_ols = LinearRegression().fit(near_X, changed_y)
near_comparison = pd.DataFrame({
    "Original": near_ols.coef_,
    "Tiny change in y": changed_ols.coef_,
}, index=near_X.columns)
print(f"Factor correlation: {near_X.corr().iloc[0, 1]:.9f}")
print(near_comparison.round(6))
print(f"Largest change in observed return: {100 * np.max(np.abs(changed_y - near_y)):.4f} percentage points")
```

correlation ระหว่างปัจจัยประมาณ 0.999999875 ก่อนเปลี่ยนข้อมูลได้ loading ประมาณ `[0.8, 0]` หลังเปลี่ยนเล็กน้อยกลับได้ `[-0.2, 1.0]` ทั้งสองสมการยังมีผลรวม loading ใกล้ 0.8 เพราะ Market และ Proxy เคลื่อนไหวแทบเหมือนกัน สมการจึงแบ่งความสัมพันธ์ระหว่างสองคอลัมน์ได้ยาก

ภาวะนี้เรียกว่า [multicollinearity](glossary.html#multicollinearity) การเพิ่มข้อมูลที่แทบซ้ำกันจึงไม่ได้เพิ่มข้อมูลอิสระเท่าจำนวนคอลัมน์ ในกรณีซ้ำกันพอดี อาจมี loading หลายชุดที่ให้ค่าทำนายชุดเดียวกัน

correlation ติดลบใกล้ −1 ก็มีปัญหาเดียวกัน เพราะคอลัมน์หนึ่งเกือบเท่ากับอีกคอลัมน์คูณ −1 และในกรณีหลายปัจจัย ความซ้ำอาจเป็นผลรวมของหลายคอลัมน์โดยไม่มีคู่ใดมี correlation สูงมาก การดูตาราง correlation เป็นเพียงจุดเริ่มตรวจ ไม่ใช่การตรวจ rank ทั้งหมด

<span id="factor-units-and-scaling"></span>

## ขนาด Loading เปลี่ยนตามหน่วยข้อมูล

ทดสอบ [การเปลี่ยนหน่วย factor](multifactor-models.html#multifactor-units) ด้วย `LinearRegression`: คูณเฉพาะ `Rate` ด้วย 100 แล้ว fit ใหม่ โดยคง `y` และปัจจัยอื่นไว้ ตรวจทั้ง coefficient และ fitted returns

```python
unit_X = factor_X.copy()
unit_X["Rate"] = 100 * unit_X["Rate"]
unit_ols = LinearRegression().fit(unit_X, factor_y)
print("New loadings:", unit_ols.coef_)
print("Same fitted returns:", np.allclose(unit_ols.predict(unit_X), factor_fitted))
print(f"Correlation with negative proxy: {np.corrcoef(market, -near_X['Proxy'])[0, 1]:.9f}")
```

ผลได้ Rate loading −0.004 และ `Same fitted returns: True` ซึ่งยืนยันว่า coefficient ชดเชยหน่วยที่เปลี่ยนไป บรรทัดสุดท้ายยังตรวจกรณี proxy กลับเครื่องหมาย ได้ correlation ใกล้ −1

บทถัดไปจะใช้ [standardization](glossary.html#standardization) เพื่อทำให้แต่ละคอลัมน์มีสเกลเทียบกันได้ก่อนลงโทษขนาด coefficient แล้วค่อยแปลง loading กลับสู่หน่วยเดิม โดยยังต้องดูความสัมพันธ์ระหว่างปัจจัยร่วมด้วย

<span id="factor-expectation-scenario"></span>

## เปลี่ยนจากผลตอบแทนที่เกิดแล้วเป็นข้อสมมติเกี่ยวกับอนาคต

เมื่อมี loading แล้ว เรายังต้องมีข้อสมมติของผลตอบแทนปัจจัยก่อนประมาณ expected return ของกองทุน สมมติ Market มีค่าเฉลี่ยรายเดือน 0.5% และ Rate มีค่าเฉลี่ย 0.2% หากยอมให้ intercept เดิมคงอยู่ จะได้

$$
0.1\%+0.8(0.5\%)-0.4(0.2\%)=0.42\%\text{ ต่อเดือน}.
$$

```python
factor_assumptions = pd.DataFrame({"Market": [0.005], "Rate": [0.002]})
factor_expected_monthly = factor_ols.predict(factor_assumptions)[0]
factor_zero_alpha_monthly = factor_assumptions.iloc[0].to_numpy() @ factor_ols.coef_
print(f"Conditional monthly estimate: {100 * factor_expected_monthly:.4f}%")
print(f"Arithmetic annualized estimate: {100 * 12 * factor_expected_monthly:.4f}%")
print(f"Monthly estimate if alpha is set to zero: {100 * factor_zero_alpha_monthly:.4f}%")
```

ผลรายเดือน 0.42% คูณ 12 เป็น 5.04% แบบ arithmetic annualization ซึ่งใช้เทียบในหน่วยปี ไม่ใช่ CAGR หรือผลตอบแทนทบต้นที่ได้รับแน่นอน หากสมมติให้ alpha เป็นศูนย์ จะเหลือ 0.32% ต่อเดือน การกำหนด alpha เป็นศูนย์เป็นข้อสมมติด้านแบบจำลองที่เพิ่มเข้ามา ไม่ใช่สิ่งที่ `.fit` บังคับให้

ตัวอย่างนี้ใช้ปัจจัยเป็นผลตอบแทนพอร์ต สำหรับโมเดลที่ใช้การเปลี่ยนแปลง GDP หรือ inflation เป็นตัวแปรอธิบาย หน่วย loading และวิธีเชื่อมกับ risk premium จะต่างออกไป ส่วนปัจจัยเชิงสถิติ เช่น PCA มาจากการรวมข้อมูลตามเกณฑ์ทางคณิตศาสตร์ และไม่ได้มีคำอธิบายทางเศรษฐศาสตร์ที่แน่นอนโดยอัตโนมัติ

<span id="factor-estimation-practice"></span>

## แบบฝึกหัด

ลองคำนวณจากสมการก่อนเปิดเฉลย ตัวเลขทั้งหมดเป็นข้อมูลสมมติของบทนี้

<details><summary>1. ถ้า Market ได้ 1% และ Rate ได้ −2% สมการที่ประมาณได้อธิบายผลตอบแทน Fund เท่าไร</summary>

$0.1\%+0.8(1\%)-0.4(-2\%)=1.7\%$ เป็นส่วนที่โมเดลอธิบายได้ ผลจริงยังมี residual เพิ่มเข้ามา

</details>

<details><summary>2. ถ้าเดือนนั้น Fund ได้จริง 1.1% จากค่าที่อธิบายได้ 1.7% residual เท่าไร</summary>

$1.1\%-1.7\%=-0.6$ จุดเปอร์เซ็นต์ สัญญาณลบหมายถึงผลจริงต่ำกว่าค่าที่สมการให้

</details>

<details><summary>3. X มี 120 แถวและ 5 คอลัมน์ แถวและคอลัมน์หมายถึงอะไร และ coef_ ยาวเท่าไร</summary>

ในรูปแบบที่ใช้ที่นี่ แถวคือ 120 เดือน คอลัมน์คือ 5 ปัจจัย ถ้า y เป็นผลตอบแทนของกองทุนเดียว `coef_` มี 5 ค่า ส่วน intercept เก็บแยกต่างหาก

</details>

<details><summary>4. Residual ตั้งฉากกับ X ในชุดฝึก พิสูจน์ว่า residual เป็นอิสระจากปัจจัยหรือไม่</summary>

ไม่พิสูจน์ ความตั้งฉากเป็นเงื่อนไขของ OLS ในข้อมูลชุดนั้น ความเป็นอิสระเป็นเงื่อนไขที่แรงกว่าและไม่ได้ตามมาจาก covariance ศูนย์ทั่วไป

</details>

<details><summary>5. ปัจจัยคู่หนึ่งมี correlation −0.9999 ถือว่าห่างจากปัญหา multicollinearity หรือไม่</summary>

ยังเสี่ยง เพราะปัจจัยหนึ่งเกือบเป็นค่าติดลบของอีกปัจจัย สมการสามารถแลก loading ระหว่างกันได้มากโดยเปลี่ยน fitted returns น้อย

</details>

<details><summary>6. Loading ของ Rate เท่ากับ −0.4 เมื่อ Rate ใช้ทศนิยม ถ้าเปลี่ยนเป็นเปอร์เซ็นต์ตัวเลขจะเป็นเท่าไร</summary>

เป็น −0.004 เมื่อผลตอบแทนกองทุนยังใช้ทศนิยมเดิม เพราะ input ใหญ่ขึ้น 100 เท่า coefficient จึงต้องเล็กลง 100 เท่า

</details>

<details><summary>7. เหตุใดการใส่ผลตอบแทน Market ที่เกิดจริงในเดือนหน้า จึงยังไม่ใช่การพยากรณ์ก่อนเดือนหน้าเริ่ม</summary>

ตอนที่ต้องพยากรณ์ยังไม่รู้ค่านั้น การใส่ค่าที่เกิดจริงภายหลังใช้ตรวจความสัมพันธ์นอกชุดฝึกได้ แต่การพยากรณ์ล่วงหน้าต้องมีข้อสมมติหรือแบบจำลองของปัจจัยที่ใช้ข้อมูลซึ่งทราบในวันตัดสินใจ

</details>

<span id="factor-estimation-sources"></span>

## แหล่งอ่านและขอบเขตของตัวอย่าง

เรียบเรียงใหม่จากการอ่าน Transcript ฉบับเต็มของ Coursera ได้แก่ [Basics of Factor Investing](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/lTGHZ/introduction-to-module-2-basics-of-factor-investing), [Introducing Factor Models](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/PXj5n/introducing-factor-models), [Typology of Factor Models](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/pH2yb/typology-of-factor-models) และ [Using Factor Models](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/JNYfl/using-factor-models-in-portfolio-construction-and-analysis) พร้อม [Factor Models Lab](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/zxZH1/lab-session-jupiter-notebook-on-factor-models) ตรวจเมื่อ 3 ตุลาคม 2026

ตัวอย่างและโค้ดในหน้านี้เขียนใหม่ ไม่มีการแจก Transcript, notebook, ชุดข้อมูล หรือไลบรารีของผู้สอน รายละเอียดการเรียกใช้ไลบรารีอ้างอิง [LinearRegression](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.LinearRegression.html) เราใช้คำว่า residual ตั้งฉากกับ regressors ในข้อมูลฝึก แทนการสรุปว่าเป็นอิสระ และไม่ใช้ตัวเลขผลตอบแทนหรือสภาวะตลาดในวิดีโอเก่าเป็นข้อสมมติปัจจุบัน
