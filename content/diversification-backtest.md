---
title: "ทดสอบ Diversification: ข้อมูล เวลา และต้นทุน"
description: สร้างการทดสอบ EW, inverse volatility, GMV, ERC และ maximum diversification ด้วยข้อมูลจำลองชุดเดียว ตรวจเวลาเลือกน้ำหนัก บัญชีซื้อขาย ต้นทุน และผลตอบแทนหลังหักค่าใช้จ่าย
---

# ทดสอบ Diversification: ข้อมูล เวลา และต้นทุน

<p class="lead">น้ำหนักพอร์ตที่ดูเหมาะกับ covariance วันนี้ จะให้ผลอย่างไรเมื่อถือผ่านเดือนถัดไป และต้องจ่ายเงินทุกครั้งที่ปรับพอร์ต?</p>

บท [วิธีกระจายความเสี่ยง](diversification-methods.html) เปรียบเทียบเกณฑ์เลือกน้ำหนัก ส่วน [Risk Contributions](risk-contributions.html) กับ [Risk Parity](risk-parity.html) อธิบายว่าความเสี่ยงของพอร์ตมาจากสินทรัพย์ใดและทำให้แต่ละส่วนสมดุลได้อย่างไร บทนี้นำวิธีเหล่านั้นมาใช้ซ้ำทุกเดือน โดยเลือกน้ำหนักจากข้อมูลที่มีอยู่ก่อนเริ่มถือพอร์ตเท่านั้น

เราจะสร้างข้อมูลสมมติ 96 เดือน ใช้ 36 เดือนแรกเพื่อประเมินความเสี่ยง แล้วทดสอบการถือพอร์ตในเดือน 37–96 รวม 60 เดือน ทุกวิธีใช้สินทรัพย์และผลตอบแทนชุดเดียวกัน เริ่มเงินทุนเท่ากัน ปรับพอร์ตตามรอบเดียวกัน และคิดต้นทุนแบบเดียวกัน ผลลัพธ์จึงช่วยตรวจกลไกของการทดสอบ แต่ยังไม่บอกว่าวิธีใดจะดีที่สุดในตลาดจริง

โค้ดใช้ NumPy, pandas และ SciPy เปิด Notebook ใหม่แล้วรันทั้งบทตามลำดับได้ ฟังก์ชันจัดน้ำหนักจากบทก่อนถูกใส่ไว้ครบเพื่อให้บทนี้รันแยกได้ ไม่ต้องโหลดไฟล์ข้อมูลคอร์สหรือนำตัวแปรจาก Notebook อื่นเข้ามา

| ช่วงเรียน | สิ่งที่จะตรวจ |
|---|---|
| [ข้อมูลและกติกา](#experiment-design) | ทุกวิธีได้ข้อมูลและโอกาสซื้อขายเท่ากันหรือไม่ |
| [สร้างข้อมูลสมมติ](#simulated-data) | ความเสี่ยงที่ใช้สร้างข้อมูลต่างจากค่าประมาณอย่างไร |
| [ฟังก์ชันเลือกน้ำหนัก](#allocation-functions) | EW, IV, GMV, ERC และ MaxDR ใช้ inputs ต่างกันอย่างไร |
| [เลื่อนหน้าต่างข้อมูล](#rolling-schedule) | เดือน 37 ใช้ข้อมูลถึงเดือนไหน |
| [จ่ายต้นทุนจากเงินในพอร์ต](#self-financing-costs) | เงินที่นำไปลงทุนจริงเหลือเท่าไร |
| [ติดตามมูลค่าและน้ำหนักที่เปลี่ยน](#holdings-ledger) | น้ำหนักก่อนปรับครั้งหน้าเกิดจากอะไร |
| [วัดผลบนช่วงเดียวกัน](#performance-metrics) | CAGR, Sharpe และ drawdown นับตั้งแต่จุดใด |
| [ตรวจเวลาและบัญชี](#future-information-test) | มีข้อมูลอนาคตหรือเงินที่ไม่มีที่มาปะปนหรือไม่ |

<span id="experiment-design"></span>

## กำหนดกติกาก่อนดูผล

เราใช้ห้าวิธี โดยน้ำหนักทุกวิธีไม่ติดลบและรวมหนึ่ง จึงไม่มี short หรือ leverage:

| ชื่อในโค้ด | วิธีเลือกน้ำหนัก | ข้อมูลที่วิธีนั้นนำไปใช้ |
|---|---|---|
| EW | Equal weight: น้ำหนักเท่ากันทุกสินทรัพย์ | จำนวนสินทรัพย์ |
| IV | Inverse volatility: น้ำหนักแปรผกผันกับ SD | แนวทแยงของ covariance |
| GMV | Global minimum variance: ทำ variance ต่ำสุด | Covariance ทั้งเมทริกซ์ |
| ERC | Equal risk contribution: แบ่งสัดส่วนความเสี่ยงเท่ากัน | Covariance ทั้งเมทริกซ์ |
| MaxDR | Maximum diversification ratio | SD และ covariance ทั้งเมทริกซ์ |

ไม่มีวิธีใดรับค่าประมาณ expected return ในการเลือกน้ำหนัก แม้ข้อมูลจำลองจะต้องกำหนด mean เพื่อสร้างผลตอบแทนขึ้นมาก็ตาม ทุกเดือนเราประมาณ sample covariance จาก 36 เดือนล่าสุดด้วยตัวหาร $36-1$ แล้วส่งเมทริกซ์ชุดเดียวให้ฟังก์ชันทั้งห้า EW ไม่ใช้ค่าของ covariance และ IV ใช้เฉพาะ SD ตามนิยามของมัน

ขอบเขตน้ำหนักของการทดสอบนี้คือ $0\leq w_i\leq1$ และ $\sum_iw_i=1$ ไม่มีเพดานน้ำหนักที่แคบกว่านี้ คอร์สตอน [Comparing Diversification Options](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/lulgY/comparing-diversification-options) มีการทดลอง GMV ที่ใส่ขอบเขตต่ำสุดและสูงสุดรอบน้ำหนักเท่ากันด้วย การเปรียบเทียบผลของเราจึงเป็นการทดลองใหม่ ไม่ใช่การทำผลตอบแทนจากตารางในคอร์สซ้ำ

กำหนด seed `20261004` ก่อนเปรียบเทียบผลทั้งห้าวิธี เพื่อให้สร้างข้อมูลชุดเดิมได้ ตัวเลขนี้เป็นรหัสสุ่มของตัวอย่าง ไม่ใช่ช่วงวันที่ตลาด ส่วนอัตราต้นทุน 0, 10 และ 50 basis points เป็นกรณีเปรียบเทียบที่กำหนดไว้ โดย 1 basis point หรือ 1 bp เท่ากับ 0.01% หรือ 0.0001 ในหน่วยทศนิยม

<span id="simulated-data"></span>

## สร้างผลตอบแทนที่รู้สมมติฐานและมีขอบเขต

ใช้สินทรัพย์ A/B/C/D ชุดเดียวกับบทก่อน กำหนด SD รายปีเป็น 20%, 15%, 10%, 25% และ correlation เป็น

$$
C=\begin{bmatrix}
1&0.5&0.2&0.65\\
0.5&1&0.1&0.4\\
0.2&0.1&1&0.15\\
0.65&0.4&0.15&1
\end{bmatrix}.
$$

เมื่อ $D$ เป็นเมทริกซ์แนวทแยงของ SD จะได้ covariance สเกลรายปี $\Sigma_{\mathrm{annual}}=DCD$ เราตั้ง covariance ของผลตอบแทนรายเดือนเป็น $\Sigma_{\mathrm{monthly}}=\Sigma_{\mathrm{annual}}/12$ ภายใต้แบบจำลองรายเดือนที่เป็นอิสระข้ามเวลา คำว่า SD รายปีตรงนี้เป็นการ annualize ความเสี่ยงรายเดือนด้วย $\sqrt{12}$ ไม่ได้อ้างว่าเท่ากับ SD ของ simple return ที่ทบต้นครบปีทุกกรณี

สร้างตัวเลขสุ่มอิสระ $z_{t,j}$ จาก Uniform ช่วง $[-\sqrt3,\sqrt3]$ ซึ่งมีค่าเฉลี่ยศูนย์และ variance หนึ่ง แล้วคูณ Cholesky factor $L$ ที่ทำให้ $LL^\top=\Sigma_{\mathrm{monthly}}$:

$$
r_t=0.005\mathbf1+Lz_t.
$$

ดังนั้น $E[r_{t,i}]=0.5\%$ ต่อเดือนเท่ากันทุกสินทรัพย์ และ $\operatorname{Cov}(r_t)=LL^\top=\Sigma_{\mathrm{monthly}}$ ค่าต่าง ๆ เหล่านี้เป็นคุณสมบัติของกระบวนการที่กำหนด ส่วนข้อมูลที่สุ่มได้เพียง 96 เดือนย่อมมี sample mean และ sample covariance ต่างออกไป

Uniform มีขอบเขต เราจึงตรวจผลตอบแทนต่ำสุดที่กระบวนการนี้สร้างได้จาก $0.005-\sqrt3\sum_j|L_{ij}|$ หากทุกสินทรัพย์มีค่าต่ำสุดมากกว่า −1 ก็ไม่เกิดผลตอบแทนต่ำกว่า −100% ในตัวอย่างนี้ โครงสร้างที่จำกัดหางแบบนี้ใช้สอนบัญชีพอร์ตได้ แต่ไม่ใช่แบบจำลองวิกฤตตลาด

```python
import numpy as np
import pandas as pd
from scipy.optimize import minimize, brentq

assets = pd.Index(["A", "B", "C", "D"], name="Asset")
annual_sd = np.array([0.20, 0.15, 0.10, 0.25])
correlation = np.array([
    [1.00, 0.50, 0.20, 0.65],
    [0.50, 1.00, 0.10, 0.40],
    [0.20, 0.10, 1.00, 0.15],
    [0.65, 0.40, 0.15, 1.00],
])
population_covariance = np.outer(annual_sd, annual_sd) * correlation
monthly_covariance = population_covariance / 12
monthly_cholesky = np.linalg.cholesky(monthly_covariance)
monthly_mean_return = 0.005
seed = 20261004
window = 36
rng = np.random.default_rng(seed)
innovations = rng.uniform(-np.sqrt(3), np.sqrt(3), size=(96, len(assets)))
asset_returns = pd.DataFrame(
    monthly_mean_return + innovations @ monthly_cholesky.T,
    index=pd.RangeIndex(1, 97, name="Month"), columns=assets,
)
return_lower_bounds = monthly_mean_return - np.sqrt(3) * np.abs(monthly_cholesky).sum(axis=1)
assert np.all(return_lower_bounds > -1)
print("Population monthly return lower bounds:", np.round(return_lower_bounds, 6))
print("First three months (%):")
print((asset_returns.head(3) * 100).round(4).to_string())
print("Observed sample means (% per month):")
print((asset_returns.mean() * 100).round(4).to_string())
```

ขอบเขตล่างของ A/B/C/D ประมาณ −9.5%, −9.7452%, −5.3990% และ −18.3965% ต่อเดือน ทุกค่ามากกว่า −100% ข้อมูลที่สุ่มได้มีค่าเฉลี่ยรายเดือนประมาณ 0.8031%, 0.9973%, 0.6453% และ 0.9002% ซึ่งต่างจาก population mean 0.5% แม้ใช้กระบวนการเดียวกัน นี่เป็นความคลาดเคลื่อนจากตัวอย่าง finite sample ไม่ใช่ alpha ที่ใส่ให้สินทรัพย์แต่ละตัว

`np.outer(annual_sd, annual_sd)` สร้างผลคูณ SD ทุกคู่ แล้ว `* correlation` คูณทีละช่องเพื่อสร้าง covariance ส่วน `innovations @ monthly_cholesky.T` ใช้แถวเป็นเดือนและคอลัมน์เป็นสินทรัพย์ จึงใช้ transpose ของ $L$ `.T` หมายถึงการสลับแถวกับคอลัมน์

`default_rng(seed)` สร้างตัวสุ่ม และ `uniform(low, high, size)` ระบุขอบเขตกับขนาดตารางตาม [เอกสาร NumPy](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.uniform.html) ตาราง `asset_returns` เก็บผลตอบแทนทศนิยม เช่น −0.0851926 หมายถึง −8.51926% ไม่ใช่ราคา

โมเดลนี้กำหนด correlation และความเสี่ยงคงที่ ไม่มี volatility clustering, liquidity shock หรือการเปลี่ยน regime ส่วนวิธีจัดพอร์ตจะเห็นเพียงข้อมูลย้อนหลังที่สุ่มออกมา ไม่ได้ใช้ `population_covariance` ซึ่งเป็นค่าที่ผู้สร้างการทดลองรู้

<span id="first-estimation-window"></span>

## ประมาณ covariance ครั้งแรกจากเดือน 1–36

ก่อนเริ่มถือในเดือน 37 เรามีผลตอบแทนเดือน 1–36 แล้ว จึงคำนวณ covariance จากข้อมูล 36 แถวนี้ ส่วนเดือน 37 ยังไม่ถูกนำมาประมาณ ตัวอย่างมีเพียงสี่สินทรัพย์ และ covariance ของหน้าต่างเหล่านี้เป็น positive definite จึงใช้ฟังก์ชันจัดน้ำหนักที่ต้องการ PD ได้

เพิ่มฟังก์ชันอ่านความเสี่ยงของน้ำหนัก $w$ จาก covariance ที่กำหนด:

$$
\sigma_p=\sqrt{w^\top\Sigma w},\qquad
\operatorname{RRC}_i=\frac{w_i(\Sigma w)_i}{w^\top\Sigma w},\qquad
\operatorname{DR}=\frac{\sum_iw_i\sigma_i}{\sigma_p}.
$$

RRC เป็น [สัดส่วน risk contribution](glossary.html#risk-contribution) ที่รวมหนึ่ง ส่วน [diversification ratio](glossary.html#diversification-ratio) เปรียบเทียบค่าเฉลี่ยถ่วงน้ำหนักของ SD รายสินทรัพย์กับ SD ของพอร์ต การคูณ covariance ทั้งเมทริกซ์ด้วยค่าบวก เช่น เปลี่ยนจากสเกลเดือนเป็นปี ไม่เปลี่ยน RRC หรือ DR

```python
def checked_covariance(cov):
    cov = np.asarray(cov, dtype=float)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1] or cov.size == 0:
        raise ValueError("Covariance must be a nonempty square matrix")
    if not np.all(np.isfinite(cov)) or not np.allclose(cov, cov.T, atol=1e-12, rtol=1e-10):
        raise ValueError("Covariance must be finite and symmetric")
    if np.linalg.eigvalsh(cov).min() <= 1e-12:
        raise ValueError("This example requires positive definite covariance")
    return cov


def portfolio_risk(weights, cov):
    variance = float(weights @ cov @ weights)
    volatility = np.sqrt(variance)
    relative_contributions = weights * (cov @ weights) / variance
    diversification_ratio = float(weights @ np.sqrt(np.diag(cov)) / volatility)
    return volatility, relative_contributions, diversification_ratio

def sample_covariance(training):
    values = np.array(training.to_numpy(), dtype=float, order="C", copy=True)
    return checked_covariance(np.cov(values, rowvar=False, ddof=1))

first_covariance = sample_covariance(asset_returns.iloc[:window])
print("First estimation window:", asset_returns.index[0], "to", asset_returns.index[window - 1])
print("First holding month:", asset_returns.index[window])
print("Estimated monthly covariance eigenvalues:",
      np.round(np.linalg.eigvalsh(first_covariance), 8))
```

ผลลัพธ์ระบุ training เดือน 1 ถึง 36, holding เดือน 37 และ eigenvalues รายเดือนประมาณ `[0.00096124, 0.00130704, 0.00216627, 0.00844976]` ทุกค่าเป็นบวก ฟังก์ชันจะหยุดหาก covariance ไม่ผ่านเงื่อนไข แทนการเติมค่าหรือเปลี่ยน estimator โดยไม่บอกผู้เรียน

`iloc[:window]` เลือกตำแหน่งตั้งแต่ 0 ถึง 35 โดยไม่รวมตำแหน่ง 36 ใน `sample_covariance`, `np.cov(..., rowvar=False, ddof=1)` บอกว่าคอลัมน์เป็นสินทรัพย์และใช้ sample covariance ตัวหาร $T-1$ เราคัดลอก array ด้วย `order="C"` เพื่อให้รูปแบบการเก็บตัวเลขสม่ำเสมอเมื่อใช้ข้อมูลต้นฉบับกับข้อมูลที่ copy มาทดสอบ

ฟังก์ชัน `portfolio_risk` คืนสามรายการ ได้แก่ SD, เวกเตอร์ RRC และ DR เราจะใช้ covariance ที่ประเมิน ณ วันเลือกน้ำหนักวัดความเสี่ยงตามแบบจำลอง และใช้ผลตอบแทนที่เกิดขึ้นใน 60 เดือนถัดไปวัดผลที่เกิดจริงแยกกัน

<span id="allocation-functions"></span>

## ฟังก์ชันจัดน้ำหนักสำหรับห้าวิธี

### EW, inverse volatility, GMV และ MaxDR

IV ใช้ $w_i\propto1/\sigma_i$ แล้วหารด้วยผลรวมเพื่อให้เป็นหนึ่ง ส่วน GMV แก้ $\min_w w^\top\Sigma w$ ภายใต้ข้อจำกัดน้ำหนักไม่ติดลบและรวมหนึ่ง เมื่อ covariance เป็น PD นี่เป็นโจทย์ convex ที่มีคำตอบเอกลักษณ์

สำหรับ MaxDR เราใช้การแปลงตัวแปรใน [บทวิธีกระจายความเสี่ยง](diversification-methods.html) ให้ $z_i=\sigma_iw_i/(\sum_j\sigma_jw_j)$ จะได้ $z_i\geq0$, $\sum_i z_i=1$ และ

$$
\operatorname{DR}(w)=\frac1{\sqrt{z^\top C z}}.
$$

จึงหาคำตอบ GMV บน correlation matrix $C$ ก่อน แล้วแปลงกลับด้วย $w_i\propto z_i/\sigma_i$ วิธีนี้ใช้ข้อจำกัด long-only และผลรวมน้ำหนักเท่านั้น หากมีเพดานน้ำหนักรายสินทรัพย์เพิ่ม ต้องแปลงข้อจำกัดให้ตรงกันด้วย

```python
def minimum_variance_weights(cov):
    cov = checked_covariance(cov)
    n = len(cov)
    scaled_cov = cov / np.mean(np.diag(cov))
    result = minimize(
        lambda w: float(w @ scaled_cov @ w), np.full(n, 1 / n),
        jac=lambda w: 2 * scaled_cov @ w,
        method="SLSQP", bounds=[(0, 1)] * n,
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1,
                     "jac": lambda w: np.ones(n)},
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if (not result.success or not np.all(np.isfinite(result.x))
            or result.x.min() < -1e-9 or abs(result.x.sum() - 1) > 1e-8):
        raise RuntimeError("Minimum-variance optimization failed")
    weights = np.maximum(result.x, 0)
    weights /= weights.sum()
    gradient = 2 * scaled_cov @ weights
    active = weights > 1e-7
    multiplier = gradient[active].mean()
    if (np.max(np.abs(gradient[active] - multiplier)) > 1e-5
            or np.any(gradient[~active] < multiplier - 1e-5)):
        raise RuntimeError("Minimum-variance optimality check failed")
    return weights


def inverse_volatility_weights(cov):
    inverse_sd = 1 / np.sqrt(np.diag(checked_covariance(cov)))
    return inverse_sd / inverse_sd.sum()


def maximum_diversification_weights(cov):
    cov = checked_covariance(cov)
    sd = np.sqrt(np.diag(cov))
    corr = cov / np.outer(sd, sd)
    risk_unit_weights = minimum_variance_weights(corr)
    weights = risk_unit_weights / sd
    return weights / weights.sum()

print("GMV at first decision:", np.round(minimum_variance_weights(first_covariance), 6))
print("MaxDR at first decision:", np.round(maximum_diversification_weights(first_covariance), 6))
```

คำตอบ GMV ครั้งแรกประมาณ `[0.001349, 0.307892, 0.683870, 0.006889]` ส่วน MaxDR ประมาณ `[0.096359, 0.237469, 0.550998, 0.115173]` ลำดับคือ A/B/C/D เสมอ

`minimize` รับฟังก์ชันที่ต้องการลดค่า จุดเริ่ม น้ำหนักที่อนุญาต และข้อจำกัดผลรวม `jac` เป็นอนุพันธ์ที่คำนวณให้ solver ใช้ เราหาร covariance ด้วยค่าเฉลี่ยบนแนวทแยงเพื่อปรับขนาดตัวเลขของ objective ซึ่งไม่เปลี่ยนตำแหน่งที่ให้ค่าต่ำสุด

หลัง solver รายงานสำเร็จ โค้ดยังตรวจความเป็นไปได้ของน้ำหนักและเงื่อนไขส่วนเพิ่มของความเสี่ยง: สินทรัพย์ที่มีน้ำหนักบวกต้องมี gradient เท่ากันโดยประมาณ ส่วนสินทรัพย์ที่น้ำหนักศูนย์ต้องไม่มี gradient ต่ำกว่านั้นจนสามารถย้ายเงินเข้าไปลด objective ได้ การปัดค่าติดลบเล็กมากจากการคำนวณเป็นศูนย์เกิดก่อนตรวจเงื่อนไขนี้

ตัวเลข tolerance ในฟังก์ชันเป็นเกณฑ์ตรวจความแม่นยำเชิงตัวเลขสำหรับการทดลอง ไม่ได้บอกความแม่นของ covariance เมื่อตลาดเปลี่ยน

### ERC จาก risk budget เท่ากัน

ใช้ฟังก์ชันเดียวกับ [บท Risk Parity](risk-parity.html) โดยส่ง budget `[0.25, 0.25, 0.25, 0.25]` เข้าไป ฟังก์ชันรับ covariance ที่เป็น PD และ budget ทุกตัวเป็นบวกรวมหนึ่ง แก้โจทย์ convex ในตัวแปร risk units จากนั้นคืนค่าน้ำหนักเงินลงทุนที่รวมหนึ่ง

```python
def risk_budget_weights(cov, budget):
    cov = np.asarray(cov, dtype=float)
    budget = np.asarray(budget, dtype=float)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1] or cov.shape[0] == 0:
        raise ValueError("Covariance must be a nonempty square matrix")
    n = cov.shape[0]
    if budget.shape != (n,):
        raise ValueError("Budget must have one entry per asset")
    if not np.isfinite(cov).all() or not np.isfinite(budget).all():
        raise ValueError("Inputs must be finite")
    if not np.allclose(cov, cov.T, rtol=1e-10, atol=1e-12):
        raise ValueError("Covariance must be symmetric")
    if np.any(budget <= 0) or not np.isclose(budget.sum(), 1.0, rtol=0, atol=1e-10):
        raise ValueError("Budgets must be positive and sum to one")
    cov = (cov + cov.T) / 2
    np.linalg.cholesky(cov)
    vol = np.sqrt(np.diag(cov))
    corr = cov / np.outer(vol, vol)

    def objective(z):
        return 0.5 * z @ corr @ z - budget @ np.log(z)

    def gradient(z):
        return corr @ z - budget / z

    fit = minimize(objective, np.sqrt(budget), jac=gradient,
                   method="L-BFGS-B", bounds=[(1e-12, None)] * n,
                   options={"ftol": 1e-15, "gtol": 1e-8, "maxiter": 2000})
    if not fit.success or not np.isfinite(fit.x).all():
        raise RuntimeError("Risk-budget optimization did not converge")
    x = fit.x / vol
    weights = x / x.sum()
    variance = weights @ cov @ weights
    shares = weights * (cov @ weights) / variance
    if np.any(weights <= 0) or np.max(np.abs(shares - budget)) > 1e-7:
        raise RuntimeError("Risk shares do not match the requested budgets")
    return weights


print("ERC at first decision:", np.round(
    risk_budget_weights(first_covariance, np.full(len(assets), 1 / len(assets))), 6))
```

ได้ ERC ครั้งแรกประมาณ `[0.155960, 0.236364, 0.461585, 0.146090]` น้ำหนักเงินไม่เท่ากัน แม้ budget ของความเสี่ยงจะเท่ากันทุกสินทรัพย์

ฟังก์ชันใช้ `np.log(z)` จึงกำหนด $z>0$ และตรวจว่า optimizer สำเร็จจริง จากนั้นคำนวณ RRC กลับจากน้ำหนักที่ได้ ถ้าต่างจาก budget เกิน $10^{-7}$ จะหยุดด้วยข้อผิดพลาด เราจึงไม่ได้รับคำตอบเพียงเพราะ solver ส่ง array กลับมา

เมื่อนำไปใช้กับจักรวาลสินทรัพย์ใหญ่กว่าเดิม จำนวนสินทรัพย์อาจมากกว่าจำนวน observations จน sample covariance ไม่เป็น PD กรณีนั้นต้องออกแบบ estimator ใหม่ เช่น วิธีใน [บท Covariance Shrinkage](covariance-shrinkage.html) และใช้การตัดสินใจนั้นกับทุกวิธีที่นำมาเปรียบเทียบ ตัวอย่างนี้ไม่มีการสลับ estimator เฉพาะเดือนที่ solver ทำงานยาก

<span id="first-decision"></span>

## เปรียบเทียบน้ำหนักและความเสี่ยง ณ การตัดสินใจครั้งแรก

เก็บฟังก์ชันไว้ใน dictionary `methods` เพื่อให้ backtest เรียกผ่านชื่อเดียวกัน แต่ละฟังก์ชันรับ covariance และคืนเวกเตอร์น้ำหนักยาวสี่รายการ

```python
methods = {
    "EW": lambda cov: np.full(len(cov), 1 / len(cov)),
    "IV": inverse_volatility_weights,
    "GMV": minimum_variance_weights,
    "ERC": lambda cov: risk_budget_weights(cov, np.full(len(cov), 1 / len(cov))),
    "MaxDR": maximum_diversification_weights,
}
first_weights = pd.DataFrame(
    {name: method(first_covariance) for name, method in methods.items()}, index=assets,
).T
first_risk_rows = []
for name, weights in first_weights.iterrows():
    sd, contribution, ratio = portfolio_risk(weights.to_numpy(), first_covariance)
    first_risk_rows.append({"Method": name, "Estimated annual SD (%)": 100 * sd * np.sqrt(12),
                            "DR": ratio, **{f"RC {asset} (%)": 100 * contribution[i]
                                             for i, asset in enumerate(assets)}})
first_risk_report = pd.DataFrame(first_risk_rows).set_index("Method")
print("First target weights (%):")
print((first_weights * 100).round(4).to_string())
print("Risk measured using the first 36 months:")
print(first_risk_report.round(4).to_string())
```

| วิธี | A | B | C | D | Estimated annual SD |
|---|---:|---:|---:|---:|---:|
| EW | 25.0000% | 25.0000% | 25.0000% | 25.0000% | 13.9080% |
| IV | 18.5033% | 26.1002% | 38.5098% | 16.8867% | 11.6782% |
| GMV | 0.1349% | 30.7892% | 68.3870% | 0.6889% | 9.1336% |
| ERC | 15.5960% | 23.6364% | 46.1585% | 14.6090% | 10.8397% |
| MaxDR | 9.6359% | 23.7469% | 55.0998% | 11.5173% | 9.9206% |

คอลัมน์ SD คูณค่าประเมินรายเดือนด้วย $\sqrt{12}$ ยังไม่ได้ใช้ผลตอบแทนเดือน 37 ค่า RRC ของ EW ประมาณ 34.50%, 21.76%, 5.52%, 38.22% แสดงว่าน้ำหนักเงินเท่ากันไม่ได้ทำให้ความเสี่ยงเท่ากัน ส่วน ERC ได้ RRC 25% ทุกตัวตาม covariance ที่ประมาณไว้

GMV มี estimated SD ต่ำที่สุดในชุดนี้เพราะทุกวิธีใช้อยู่ในชุดน้ำหนักที่ GMV ค้นหา แต่ GMV ถือ C ถึง 68.39% ขณะที่ MaxDR ให้ DR สูงที่สุดประมาณ 1.5171 ตาม objective ของมัน สิ่งเหล่านี้ตรวจว่าแก้โจทย์ที่ตั้งไว้ได้ ส่วนความเสี่ยงที่จะเกิดในเดือนถัดไปยังขึ้นกับข้อมูลที่เรายังไม่เห็น

<span id="rolling-schedule"></span>

## เลื่อนหน้าต่างข้อมูลทีละเดือนแล้วเลือกน้ำหนักล่วงหน้า

แต่ละเดือนใช้ข้อมูล 36 เดือนล่าสุด รอบแรกเริ่มหลังจบเดือน 36 และรอบสุดท้ายเริ่มหลังจบเดือน 95:

| ใช้ถือในเดือน | ข้อมูลที่นำมาประมาณ covariance | ข้อมูลที่ยังห้ามใช้ |
|---:|---|---|
| 37 | เดือน 1–36 | ผลตอบแทนเดือน 37 เป็นต้นไป |
| 38 | เดือน 2–37 | ผลตอบแทนเดือน 38 เป็นต้นไป |
| 61 | เดือน 25–60 | ผลตอบแทนเดือน 61 เป็นต้นไป |
| 96 | เดือน 60–95 | ผลตอบแทนเดือน 96 |

สมมติให้ซื้อขายที่รอยต่องวดหลังได้รับข้อมูลเดือนที่เพิ่งจบ โดยไม่มีราคากระโดดระหว่างรอคำสั่ง ต้นทุนซื้อขายจะถูกหักก่อนถือผ่านงวดใหม่ เมื่อนำระบบไปใช้จริงต้องกำหนดเวลาที่ข้อมูลมาถึง ราคาที่ส่งคำสั่งได้ และ execution lag เพิ่มเติมให้ตรงกับข้อมูลผลตอบแทน

```python
def make_weight_schedules(returns, estimation_window=36):
    values = returns.to_numpy(dtype=float)
    if (not returns.index.is_unique or not returns.index.is_monotonic_increasing
            or not returns.columns.is_unique or not np.all(np.isfinite(values))
            or np.any(values <= -1) or not isinstance(estimation_window, int)
            or estimation_window < 2 or estimation_window >= len(returns)):
        raise ValueError("Returns or estimation window are invalid")
    rows = {name: [] for name in methods}
    for t in range(estimation_window, len(returns)):
        training = returns.iloc[t - estimation_window:t]
        cov = sample_covariance(training)
        for name, method in methods.items():
            rows[name].append(method(cov))
    return {name: pd.DataFrame(weights, index=returns.index[estimation_window:],
                               columns=returns.columns)
            for name, weights in rows.items()}

weight_schedules = make_weight_schedules(asset_returns, window)
print("Holding months:", weight_schedules["EW"].index[0], "to", weight_schedules["EW"].index[-1])
print("Number of decisions per method:", {name: len(table) for name, table in weight_schedules.items()})
print("ERC target for month 38 (%):")
print((weight_schedules["ERC"].loc[38] * 100).round(4).to_string())
```

ทุกวิธีได้ตารางน้ำหนัก 60 แถวสำหรับเดือน 37–96 น้ำหนัก ERC สำหรับเดือน 38 ประมาณ A 15.9939%, B 23.3163%, C 45.9511%, D 14.7387% ต่างจากเดือน 37 เพราะข้อมูลเดือน 1 ออกจากหน้าต่างและข้อมูลเดือน 37 เข้ามาแทน

ใน Python ตัวแปร `t=36` เป็นตำแหน่งแถวของเดือน 37 คำสั่ง `returns.iloc[t - estimation_window:t]` จึงเลือกตำแหน่ง 0–35 เท่านั้น Python ไม่รวมขอบขวา `t` ทำให้ผลตอบแทนของเดือนที่จะถือยังไม่เข้า training window

แม้โค้ดจะเก็บตารางน้ำหนักทั้ง 60 เดือนก่อนคำนวณ wealth แต่แต่ละแถวใช้ข้อมูลที่มี ณ เวลาตัดสินใจของแถวนั้นเท่านั้น เราจะแก้ข้อมูลอนาคตเพื่อทดสอบเงื่อนไขนี้อีกครั้งท้ายบท

<span id="self-financing-costs"></span>

## หักต้นทุนจากเงินที่พอร์ตมีอยู่จริง

การ [rebalancing](glossary.html#rebalancing) เปลี่ยนมูลค่าที่ถือในแต่ละสินทรัพย์ มีทั้งรายการซื้อและรายการขาย สมมติคิดค่าซื้อขายอัตราเดียวกัน $c$ ต่อมูลค่าที่ซื้อหรือขาย เช่น $c=0.001$ คือ 10 bps ต่อมูลค่าธุรกรรมหนึ่งด้าน หากขาย 100 บาทแล้วซื้ออีก 100 บาท ต้นทุนรวมเป็น $0.001(100+100)=0.20$ บาท

การซื้อขายแบบ [self-financing](glossary.html#self-financing) ใช้เงินและสินทรัพย์ที่มีอยู่ในพอร์ตจ่ายต้นทุน จึงทำให้เงินที่จัดสรรตามน้ำหนักเป้าหมายลดลง กำหนดตัวแปรก่อนปรับพอร์ต:

- $V^-$ เป็นมูลค่าพอร์ตรวมก่อนจ่ายต้นทุน
- $d_i$ เป็นมูลค่าถือสินทรัพย์ $i$ หารด้วย $V^-$ ซึ่งเป็นน้ำหนักที่ drift มาจากเดือนก่อน
- $w_i$ เป็นน้ำหนักเป้าหมายหลังจ่ายต้นทุน โดย $\sum_iw_i=1$
- $s=V^+/V^-$ เป็นสัดส่วนมูลค่าที่เหลือหลังต้นทุน

มูลค่าที่ต้องซื้อขายของสินทรัพย์ $i$ เท่ากับ $V^-(sw_i-d_i)$ เครื่องหมายบวกคือซื้อ ลบคือขาย จึงได้สมการเงินทุน

$$
s=1-c\sum_i|sw_i-d_i|.
$$

ด้านขวาหักต้นทุนตามมูลค่าธุรกรรมจริงที่ทำให้เงินหลังซื้อขายอยู่ในสัดส่วนเป้าหมาย ตัวแปร $s$ ปรากฏทั้งสองด้าน จึงใช้วิธีหาค่าที่ทำให้สมการสมดุล สำหรับ $0\leq c<1$, น้ำหนักเป้าหมายไม่ติดลบรวมหนึ่ง และน้ำหนักสินทรัพย์ก่อนซื้อขายรวมไม่เกินหนึ่ง สมการมีคำตอบเอกลักษณ์ในช่วง $[0,1]$

ถ้าเริ่มจากเงินสดทั้งหมด จะมี $d_i=0$ ทุกตัว ดังนั้น $s=1-cs$ หรือ

$$
s=\frac1{1+c}.
$$

เมื่อมีเงิน 1,000 บาทและค่าซื้อ 10 bps จะลงทุนได้ประมาณ 999.000999 บาท จ่ายค่าซื้อประมาณ 0.999001 บาท รวมแล้วพอดีกับ 1,000 บาท

### ตัวอย่างปรับพอร์ตสองสินทรัพย์ด้วยมือ

สมมติมีน้ำหนักก่อนซื้อขาย 80/20 ต้องการกลับไปเป็น 60/40 และคิดต้นทุน 10 bps จะขายสินทรัพย์แรกแล้วซื้อสินทรัพย์ที่สอง มูลค่าธุรกรรมต่อหนึ่งหน่วยทุนก่อนซื้อขายคือ

$$
(0.8-0.6s)+(0.4s-0.2)=0.6-0.2s.
$$

แก้ $s=1-0.001(0.6-0.2s)$ ได้ $s=(1-0.0006)/(1-0.0002)\approx0.999599919984$ จึงมีต้นทุนประมาณ 0.000400080016 ของทุนก่อนซื้อขาย ตัวอย่างสองสินทรัพย์นี้ใช้ตรวจฟังก์ชันต้นทุน ส่วน backtest หลักยังมีสี่สินทรัพย์

```python
def exact_rebalance(pretrade_weights, target_weights, cost_rate):
    before = np.asarray(pretrade_weights, dtype=float)
    target = np.asarray(target_weights, dtype=float)
    if (before.ndim != 1 or target.shape != before.shape or before.size == 0
            or not np.all(np.isfinite(before)) or not np.all(np.isfinite(target))
            or np.any(before < 0) or before.sum() > 1 + 1e-10
            or np.any(target < 0) or abs(target.sum() - 1) > 1e-10
            or not np.isfinite(cost_rate) or not 0 <= cost_rate < 1):
        raise ValueError("Invalid long-only weights or transaction cost")
    def balance(s):
        return s + cost_rate * np.abs(s * target - before).sum() - 1
    scale = 1.0 if cost_rate == 0 else brentq(balance, 0, 1, xtol=1e-14, rtol=1e-14)
    trades = scale * target - before
    fee_fraction = cost_rate * np.abs(trades).sum()
    if abs(scale + fee_fraction - 1) > 1e-10:
        raise RuntimeError("Self-financing balance failed")
    return scale, trades, float(fee_fraction)

initial_scale, initial_trades, initial_fee = exact_rebalance(np.zeros(4), np.full(4, 0.25), 0.001)
toy_scale, toy_trades, toy_fee = exact_rebalance(np.array([0.8, 0.2]), np.array([0.6, 0.4]), 0.001)
print("Initial all-cash scale:", round(initial_scale, 10))
print("Initial fee per unit of wealth:", round(initial_fee, 10))
print("Two-asset rebalance scale:", round(toy_scale, 10))
print("Trades as fractions of pretrade wealth:", np.round(toy_trades, 10))
print("Fee per unit of pretrade wealth:", round(toy_fee, 10))
```

ผลลัพธ์การซื้อครั้งแรกให้ `scale = 0.9990009990` ส่วนตัวอย่าง 80/20 ไป 60/40 ให้รายการซื้อขายประมาณ `[-0.2002400480, 0.1998399680]` รวมยอดขายมากกว่ายอดซื้อเล็กน้อยเพื่อจ่ายต้นทุน 0.0004000800 ของทุนก่อนซื้อขาย

`brentq(balance, 0, 1)` หาค่า $s$ ที่ทำให้ `balance(s)` เป็นศูนย์ภายในช่วงที่กำหนด โดยฟังก์ชันต่อเนื่องและมีค่าคร่อมศูนย์ตาม [เงื่อนไขของ SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html) หลัง solve เรายังตรวจว่า $s+\text{fee fraction}=1$ ภายใน tolerance

เราใช้ผลรวมมูลค่าซื้อบวกมูลค่าขายเป็นฐานต้นทุน ซึ่งต่างจาก [one-way turnover](glossary.html#turnover) ที่มักเขียนเป็นครึ่งหนึ่งของผลรวมการเปลี่ยนน้ำหนัก หากหยิบ turnover ที่หารสองแล้วมาคูณอัตราค่าธรรมเนียมต่อรายการโดยไม่ปรับ convention จะนับต้นทุนไม่ครบ

แบบจำลองนี้ใช้ต้นทุนเชิงเส้นอัตราคงที่ ไม่มีขั้นต่ำต่อคำสั่ง market impact ภาษี หรือข้อจำกัดสภาพคล่อง คำว่าแก้ต้นทุนได้ตรงสมการหมายถึงตรงตามสมมติฐานนี้ ไม่ได้หมายถึงจำลองต้นทุนจริงได้ครบทุกประเภท

<span id="holdings-ledger"></span>

## ถือผ่านเดือนแล้วคำนวณน้ำหนักที่ drift ไป

เมื่อจ่ายต้นทุนแล้วและซื้อสินทรัพย์ตามเป้าหมาย $w_t$ ให้ $r_{t,i}$ เป็นผลตอบแทนสินทรัพย์ในเดือนที่ถือ มูลค่าพอร์ตสิ้นเดือนคือ

$$
V_t=V_t^+\left(1+\sum_iw_{t,i}r_{t,i}\right).
$$

มูลค่าสินทรัพย์ $i$ สิ้นเดือนเท่ากับ $V_t^+w_{t,i}(1+r_{t,i})$ เมื่อหารด้วยมูลค่าพอร์ตรวม จะได้น้ำหนักก่อนปรับครั้งถัดไป:

$$
d_{t+1,i}=\frac{w_{t,i}(1+r_{t,i})}{1+w_t^\top r_t}.
$$

ดังนั้นแม้ EW ตั้งเป้า 25% ทุกเดือน ก็ยังอาจต้องซื้อขาย เพราะเดือนก่อนสินทรัพย์ขึ้นลงไม่เท่ากัน การคำนวณธุรกรรมจาก “เป้าหมายใหม่ลบเป้าหมายเดือนก่อน” จะพลาดน้ำหนักที่ drift ตามราคา

สร้าง ledger หรือตารางบัญชี เก็บมูลค่าก่อนซื้อขาย ต้นทุน เป้าหมาย รายการซื้อขาย และมูลค่าสินทรัพย์สิ้นเดือนทุกครั้ง เพื่อให้ย้อนตรวจที่มาของ wealth ได้

```python
def run_backtest(returns, schedules, cost_rate):
    names = list(schedules)
    holding_months = schedules[names[0]].index
    if any(not table.index.equals(holding_months) or not table.columns.equals(returns.columns)
           for table in schedules.values()):
        raise ValueError("All schedules must have identical holding months and assets")
    wealth_columns = {}
    ledger_rows = []
    for name, targets in schedules.items():
        wealth = 1.0
        pretrade_weights = np.zeros(returns.shape[1])
        path = [wealth]
        for month, target_row in targets.iterrows():
            target = target_row.to_numpy(dtype=float)
            asset_return = returns.loc[month].to_numpy(dtype=float)
            if not np.all(np.isfinite(asset_return)) or np.any(asset_return <= -1):
                raise ValueError("Holding-period gross returns must be finite and positive")
            pretrade_wealth = wealth
            scale, trades, fee_fraction = exact_rebalance(pretrade_weights, target, cost_rate)
            after_fee_wealth = pretrade_wealth * scale
            portfolio_return = float(target @ asset_return)
            end_values = after_fee_wealth * target * (1 + asset_return)
            wealth = float(end_values.sum())
            row = {"Method": name, "Month": month,
                   "Pretrade wealth": pretrade_wealth, "After-fee wealth": after_fee_wealth,
                   "Cash before": 1 - pretrade_weights.sum(), "Scale": scale,
                   "Traded notional": float(np.abs(trades).sum()),
                   "Fee": pretrade_wealth * fee_fraction, "End wealth": wealth,
                   "Gross portfolio return": portfolio_return,
                   "Net portfolio return": wealth / pretrade_wealth - 1}
            for j, asset in enumerate(returns.columns):
                row[f"Before {asset}"] = pretrade_weights[j]
                row[f"Target {asset}"] = target[j]
                row[f"Trade {asset}"] = trades[j]
                row[f"Return {asset}"] = asset_return[j]
                row[f"End value {asset}"] = end_values[j]
            ledger_rows.append(row)
            pretrade_weights = end_values / wealth
            path.append(wealth)
        wealth_columns[name] = path
    wealth_index = pd.Index([holding_months[0] - 1, *holding_months], name="Month")
    wealth_table = pd.DataFrame(wealth_columns, index=wealth_index)
    ledger = pd.DataFrame(ledger_rows).set_index(["Method", "Month"])
    return wealth_table, ledger

print("Backtest records pretrade wealth, fees, holdings and month-end wealth.")
```

`run_backtest` เริ่มแต่ละวิธีด้วยมูลค่า 1 และน้ำหนักสินทรัพย์เป็นศูนย์ จึงมีเงินสดหนึ่งหน่วยเต็มก่อนซื้อครั้งแรก แต่หลังจัดสรรแต่ละรอบจะลงทุนในสินทรัพย์ทั้งหมด `end_values / wealth` คำนวณน้ำหนักที่ drift ไปแล้วสำหรับใช้เป็นฐานการซื้อขายรอบหน้า

`trades` เป็นสัดส่วนต่อมูลค่าก่อนซื้อขาย ส่วน `Fee` และ `End value A` เป็นต้น เป็นจำนวนเงินในหน่วยเดียวกับทุนเริ่มต้น การแยกสองหน่วยนี้ทำให้ไม่เผลอเอาน้ำหนักมาบวกกับจำนวนเงิน `ledger` ใช้ชื่อวิธีกับเดือนเป็นดัชนีสองชั้น จึงเรียกรายการของ ERC ได้ด้วย `ledger.loc["ERC"]`

หากเริ่มทุนจริง 1,000,000 บาท ให้นำคอลัมน์มูลค่าและค่าธรรมเนียมคูณ 1,000,000 ขณะที่สัดส่วนต้นทุน น้ำหนัก และผลตอบแทนไม่เปลี่ยนภายใต้ต้นทุนเชิงเส้นนี้

<span id="wealth-results"></span>

## เริ่ม wealth ก่อนถือเดือน 37 แล้วติดตามครบ 60 เดือน

สร้างเส้น wealth สองกรณี ได้แก่ไม่มีต้นทุนและมีต้นทุน 10 bps ใช้ตารางน้ำหนักเดียวกันทั้งคู่ เพราะกลยุทธ์ที่กำหนดไว้รับเพียง covariance ไม่ได้นำระดับ wealth หรือต้นทุนไปปรับเป้าหมายให้ต่างกัน

```python
gross_wealth, gross_ledger = run_backtest(asset_returns, weight_schedules, cost_rate=0.0)
net_wealth, net_ledger = run_backtest(asset_returns, weight_schedules, cost_rate=0.001)
print("Wealth after months 36, 37, 38 and 96, with 10 bps cost:")
print(net_wealth.loc[[36, 37, 38, 96]].round(6).to_string())
print("ERC first three fee entries:")
print(net_ledger.loc["ERC", ["Pretrade wealth", "Traded notional", "Fee", "End wealth"]]
      .head(3).round(8).to_string())
print("Wealth table shape:", net_wealth.shape)
```

| จุดเวลา | EW | IV | GMV | ERC | MaxDR |
|---|---:|---:|---:|---:|---:|
| หลังเดือน 36 ก่อนซื้อครั้งแรก | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| หลังเดือน 37 | 1.047971 | 1.044145 | 1.035762 | 1.040977 | 1.037897 |
| หลังเดือน 38 | 1.001711 | 1.013481 | 1.039353 | 1.015738 | 1.020788 |
| หลังเดือน 96 | 1.908984 | 1.924726 | 1.878754 | 1.930098 | 1.916386 |

ตาราง wealth มี 61 แถว ได้แก่เงินตั้งต้นหนึ่งแถวกับปลายงวด 60 แถว เดือน 1–36 เป็นช่วงเก็บข้อมูลเพื่อเริ่มกลยุทธ์ ไม่ได้ถูกนำมานับเป็นผลตอบแทนของพอร์ตที่ทดสอบ

ERC จ่ายค่าซื้อครั้งแรกประมาณ 0.000999001 ต่อทุนเริ่มต้นหนึ่งหน่วย รายการเดือน 38 ซื้อขายรวมประมาณ 2.2603% ของมูลค่าก่อนซื้อขายและจ่ายต้นทุนประมาณ 0.00002353 หน่วยทุนเริ่มต้น เพราะฐานมูลค่าพอร์ตตอนนั้นเกินหนึ่งหน่วยแล้ว

เมื่อจบเดือน 96 เรารายงานมูลค่าตามราคาของสินทรัพย์ที่ยังถืออยู่ ไม่มีคำสั่งขายปิดพอร์ตเพิ่ม หากโจทย์จริงต้องถอนเงินสดทั้งหมด ต้องเพิ่มการขายและต้นทุนปลายทางให้ทุกวิธีเหมือนกัน

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/advanced-diversification-net-wealth-mobile.svg">
<img src="assets/charts/advanced-diversification-net-wealth.svg" alt="มูลค่าพอร์ตสุทธิห้าวิธีในข้อมูลจำลอง เริ่มด้วยทุนหนึ่งหน่วยก่อนเดือน 37 และติดตามถึงเดือน 96" loading="lazy" width="720" height="560">
</picture>
<figcaption>ทุกวิธีใช้ผลตอบแทนจำลอง seed 20261004 และช่วงประมาณย้อนหลัง 36 เดือนเดียวกัน คิดต้นทุน 10 bps ของมูลค่าทุกการซื้อและขาย รวมการซื้อครั้งแรกจากเงินสด แต่ยังไม่ขายปิดพอร์ตเมื่อจบเดือน 96 เส้นทางเดียวนี้ใช้ตรวจวิธีคำนวณ ไม่ใช่หลักฐานจัดอันดับกลยุทธ์ในตลาดจริง</figcaption>
</figure>

<span id="performance-metrics"></span>

## วัดผลตอบแทน ความเสี่ยง และต้นทุนบนช่วงเดียวกัน

ให้ $n=60$ เป็นจำนวนเดือนถือจริง และ $V_0=1$ เป็นมูลค่าก่อนซื้อครั้งแรก เราคำนวณ CAGR จาก

$$
\operatorname{CAGR}=\left(\frac{V_n}{V_0}\right)^{12/n}-1.
$$

ผลตอบแทนสุทธิรายเดือนคำนวณจาก $V_t/V_{t-1}-1$ จึงรวมค่าซื้อครั้งแรกไว้ในงวดแรกด้วย สำหรับ Sharpe ตัวอย่างกำหนด risk-free rate เป็นศูนย์และใช้ arithmetic mean รายเดือน:

$$
\widehat\mu_{\mathrm{ann}}=12\bar r,\qquad
\widehat\sigma_{\mathrm{ann}}=\sqrt{12}\,s_r,\qquad
\operatorname{Sharpe}_{\mathrm{ann}}
=\sqrt{12}\frac{\bar r}{s_r}.
$$

$s_r$ เป็น sample SD ของผลตอบแทนรายเดือน ใช้ตัวหาร $n-1$ การคูณด้วย $\sqrt{12}$ เป็น convention ของการรายงาน ไม่ได้ตรวจว่าผลตอบแทนกลยุทธ์มี serial correlation หรือไม่ หากนำไปอนุมานความเสี่ยงระยะยาวหรือทดสอบนัยสำคัญ ต้องตรวจเงื่อนไขการ annualize เพิ่มเติม

Drawdown คำนวณจาก wealth เทียบกับจุดสูงสุดที่เคยเกิดขึ้นโดยรวมทุนตั้งต้นไว้ด้วย ถ้างวดแรกขาดทุน drawdown จะเริ่มนับจาก 1 ไม่ใช่เริ่มยอดสูงสุดหลังขาดทุนไปแล้ว

```python
def performance_summary(wealth_table, ledger):
    rows = []
    for name in wealth_table.columns:
        wealth = wealth_table[name]
        monthly_returns = wealth.pct_change().dropna()
        n_months = len(monthly_returns)
        annual_mean = 12 * monthly_returns.mean()
        annual_volatility = np.sqrt(12) * monthly_returns.std(ddof=1)
        cagr = (wealth.iloc[-1] / wealth.iloc[0]) ** (12 / n_months) - 1
        drawdown = wealth / wealth.cummax() - 1
        method_ledger = ledger.loc[name]
        rows.append({"Method": name, "CAGR (%)": 100 * cagr,
                     "Annual mean (%)": 100 * annual_mean,
                     "Annual SD (%)": 100 * annual_volatility,
                     "Sharpe, RF = 0": annual_mean / annual_volatility if annual_volatility > 0 else np.nan,
                     "Max drawdown (%)": -100 * drawdown.min(),
                     "End wealth": wealth.iloc[-1], "Total fees": method_ledger["Fee"].sum(),
                     "Mean rebalance traded (%)": 100 * method_ledger["Traded notional"].iloc[1:].mean()})
    return pd.DataFrame(rows).set_index("Method")

gross_summary = performance_summary(gross_wealth, gross_ledger)
net_summary = performance_summary(net_wealth, net_ledger)
print("With 10 bps per unit bought or sold:")
print(net_summary.round(6).to_string())
```

| วิธี | Net CAGR | Realized annual SD | Sharpe, RF = 0 | Max drawdown |
|---|---:|---:|---:|---:|
| EW | 13.8048% | 12.1676% | 1.1276 | 9.9186% |
| IV | 13.9918% | 10.2460% | 1.3349 | 7.4447% |
| GMV | 13.4420% | 8.5485% | 1.5247 | 6.2996% |
| ERC | 14.0554% | 9.7872% | 1.3987 | 6.8870% |
| MaxDR | 13.8929% | 9.2706% | 1.4559 | 6.8105% |

ตารางนี้เป็นผลของข้อมูลจำลองชุดเดียว ERC มี terminal wealth และ CAGR สูงที่สุดในห้าวิธี ขณะที่ GMV มี realized SD ต่ำที่สุดและ Sharpe สูงที่สุด การเลือกผู้ชนะจึงยังต้องบอกว่าใช้เกณฑ์ใด แม้ก่อนพิจารณาความคลาดเคลื่อนจากการสุ่มและความเสี่ยงในตลาดจริง

CAGR ของ ERC ประมาณ 14.0554% ส่วน arithmetic mean รายเดือนคูณ 12 ประมาณ 13.6890% ค่าแรกใช้การทบต้นเพื่อหาผลตอบแทนคงที่รายปี ค่าอีกตัวเป็นค่าเฉลี่ยรายเดือนที่ขยายสเกลแบบเส้นตรง จึงไม่ควรแทน CAGR ลงในสูตร Sharpe ข้างบน และไม่ควรนำลำดับของสองค่านี้ไปสรุปว่า geometric mean รายเดือนสูงกว่า arithmetic mean รายเดือน

คอลัมน์ `Mean rebalance traded (%)` เฉลี่ยผลรวมมูลค่าซื้อและขายหารด้วยมูลค่าก่อนซื้อขายของแต่ละงวด โดยตัดการซื้อครั้งแรกออก เช่น EW ประมาณ 3.0134% และ MaxDR ประมาณ 5.8267% ต่อรอบที่ปรับพอร์ต ค่านี้ใช้ฐานทั้งซื้อและขายเต็มจำนวนตามต้นทุน ไม่ได้หารสอง

`Total fees` เป็นเงินที่จ่ายรวมตลอดช่วงในหน่วยทุนเริ่มต้น เช่น ERC ประมาณ 0.003823 หน่วย แต่ผลต่าง terminal wealth ก่อนกับหลังต้นทุนยังรวมผลจากเงินค่าธรรมเนียมที่ไม่ได้อยู่ทบผลตอบแทนต่อ จึงไม่จำเป็นต้องเท่ากับผลรวมค่าธรรมเนียมที่จ่าย

<span id="cost-sensitivity"></span>

## เพิ่มต้นทุนโดยคงเป้าหมายการลงทุนเดิม

เปรียบเทียบอัตราต้นทุน 0, 10 และ 50 bps โดยไม่เปลี่ยนหน้าต่างข้อมูล วิธีประมาณ covariance หรือน้ำหนักเป้าหมาย การทดลองนี้วัดผลของค่าใช้จ่ายที่สูงขึ้นต่อกติกาเดิม ไม่ได้หากลยุทธ์ที่เหมาะที่สุดสำหรับแต่ละอัตราต้นทุน

```python
cost_wealth = {0: gross_wealth, 10: net_wealth}
cost_ledgers = {0: gross_ledger, 10: net_ledger}
cost_wealth[50], cost_ledgers[50] = run_backtest(asset_returns, weight_schedules, cost_rate=0.005)
cost_summary = pd.DataFrame({
    f"Cost {bps} bps: end wealth": wealth.iloc[-1] for bps, wealth in cost_wealth.items()
})
print(cost_summary.round(6).to_string())
print("Each cost scenario uses the same target weights and holds to month 96 without liquidation.")
```

| วิธี | ไม่มีต้นทุน | ต้นทุน 10 bps | ต้นทุน 50 bps |
|---|---:|---:|---:|
| EW | 1.914294 | 1.908984 | 1.887912 |
| IV | 1.930464 | 1.924726 | 1.901960 |
| GMV | 1.886714 | 1.878754 | 1.847264 |
| ERC | 1.936312 | 1.930098 | 1.905455 |
| MaxDR | 1.924909 | 1.916386 | 1.882679 |

ทุกช่องเป็น terminal wealth จากทุนหนึ่งหน่วยและยังถือสินทรัพย์อยู่ เช่น MaxDR ลดจากประมาณ 1.924909 เป็น 1.882679 เมื่อต้นทุนเพิ่มจากศูนย์เป็น 50 bps การซื้อขายบ่อยและน้ำหนักที่เปลี่ยนมากทำให้พอร์ตสัมผัสต้นทุนมากขึ้นได้ แม้กติกานั้นจะให้ risk metric ที่ต้องการก่อนคิดค่าใช้จ่าย

หากจะเพิ่ม no-trade band หรือปรับพอร์ตทุกไตรมาส ต้องสร้างกติกาใหม่และทดสอบด้วยช่วงข้อมูลที่ยังไม่ถูกใช้เลือกพารามิเตอร์ ไม่ควรเลือกความถี่ที่ให้ผลดีที่สุดจากตารางเดิมแล้วรายงานเหมือนเป็นผลนอกตัวอย่างอีกครั้ง

<span id="future-information-test"></span>

## เปลี่ยนข้อมูลอนาคตแล้วตรวจน้ำหนักที่เลือกไปแล้ว

[Look-ahead bias](glossary.html#look-ahead-bias) เกิดเมื่อข้อมูลที่ยังไม่รู้ ณ เวลาตัดสินใจเข้าไปมีผลต่อน้ำหนักย้อนหลัง เราทดสอบด้วยการ copy ข้อมูล แล้วเปลี่ยนผลตอบแทนตั้งแต่เดือน 61 เป็นต้นไปให้ต่างจากเดิม

น้ำหนักสำหรับถือเดือน 61 ต้องยังเหมือนเดิม เพราะเลือกจากเดือน 25–60 แต่น้ำหนักสำหรับเดือน 62 สามารถเปลี่ยนได้ เพราะตอนนั้นข้อมูลเดือน 61 เข้าสู่ training window แล้ว ส่วน wealth ต้องเหมือนเดิมถึงสิ้นเดือน 60 และสามารถเริ่มต่างในเดือน 61 เมื่อผลตอบแทนที่ถือจริงเปลี่ยน

```python
changed_returns = asset_returns.copy()
changed_returns.loc[61:] = changed_returns.loc[61:] + np.array([0.03, -0.02, 0.01, 0.015])
changed_schedules = make_weight_schedules(changed_returns, window)
max_early_weight_change = max(
    np.abs(changed_schedules[name].loc[:61].to_numpy() - weights.loc[:61].to_numpy()).max()
    for name, weights in weight_schedules.items()
)
max_next_weight_change = max(
    np.abs(changed_schedules[name].loc[62].to_numpy() - weights.loc[62].to_numpy()).max()
    for name, weights in weight_schedules.items()
)
changed_wealth, _ = run_backtest(changed_returns, changed_schedules, cost_rate=0.001)
assert max_early_weight_change < 1e-12
assert np.allclose(changed_wealth.loc[:60], net_wealth.loc[:60], atol=1e-12, rtol=0)
print("Maximum change in targets through month 61:", max_early_weight_change)
print("Maximum change in targets for month 62:", round(max_next_weight_change, 8))
print("Wealth through month 60 is unchanged.")
```

ผลลัพธ์ให้ความต่างสูงสุดของน้ำหนักถึงเดือน 61 เท่ากับ 0.0 ส่วนความต่างสูงสุดของน้ำหนักเดือน 62 ประมาณ 0.01098392 หรือ 1.098392 จุดเปอร์เซ็นต์เมื่อเทียบข้ามทุกวิธีและสินทรัพย์ wealth ถึงสิ้นเดือน 60 เหมือนเดิมด้วย

`changed_returns.loc[61:]` เลือกตามป้ายเดือน จึงรวมเดือน 61 ต่างจากขอบขวาของ `iloc` ที่ไม่รวมตำแหน่งปลายทาง ตัวเลขที่เพิ่มเป็นการรบกวนข้อมูลเพื่อตรวจเวลา ไม่ได้อ้างว่าเป็นตัวอย่างจากกระบวนการ Uniform เดิม และไม่ได้ถูกนำมาเลือก seed หรือรายงานตารางผลงานหลัก

การตรวจนี้ยืนยันเส้นทางข้อมูลของโค้ดชุดนี้ ยังไม่ครอบคลุมปัญหาข้อมูลจริง เช่น สมาชิกดัชนีที่เลือกจากรายชื่อปัจจุบัน งบการเงินที่มีการแก้ย้อนหลัง หรือราคาที่ไม่มีให้ซื้อขาย ณ เวลาที่อ้างว่าตัดสินใจ

<span id="ledger-verification"></span>

## ตรวจว่าเงินทุกบาทมีที่มา

เมื่อไม่คิดต้นทุน wealth ต้องตรงกับการทบต้นผลตอบแทนพอร์ตโดยตรง:

$$
V_n=\prod_{t=1}^{n}(1+w_t^\top r_t).
$$

เมื่อมีต้นทุนให้ตรวจอีกสามด้าน ได้แก่เงินสดก่อนซื้อขายพอจ่ายยอดซื้อสุทธิกับค่าธรรมเนียม, มูลค่าหลังต้นทุนรวมค่าธรรมเนียมเท่ากับมูลค่าก่อนซื้อขาย และมูลค่าสินทรัพย์สิ้นเดือนรวมกันเท่ากับ wealth ที่รายงาน

```python
for name, targets in weight_schedules.items():
    holding_returns = asset_returns.loc[targets.index].to_numpy()
    direct_gross_returns = np.sum(targets.to_numpy() * holding_returns, axis=1)
    direct_wealth = np.r_[1.0, np.cumprod(1 + direct_gross_returns)]
    assert np.allclose(gross_wealth[name], direct_wealth, atol=1e-12, rtol=1e-12)
    assert np.allclose(targets.sum(axis=1), 1, atol=1e-10, rtol=0)
    assert np.all(targets.to_numpy() >= 0)
for bps, ledger in cost_ledgers.items():
    cost_rate = bps / 10000
    for (_, month), row in ledger.iterrows():
        signed_trade = sum(row[f"Trade {asset}"] for asset in assets)
        traded_notional = sum(abs(row[f"Trade {asset}"]) for asset in assets)
        fee_fraction = row["Fee"] / row["Pretrade wealth"]
        assert abs(row["Cash before"] - signed_trade - fee_fraction) < 1e-10
        assert abs(fee_fraction - cost_rate * traded_notional) < 1e-10
        assert abs(row["After-fee wealth"] + row["Fee"] - row["Pretrade wealth"]) < 1e-10
        assert abs(sum(row[f"End value {asset}"] for asset in assets) - row["End wealth"]) < 1e-10
        if month == 37:
            assert abs(row["Scale"] - 1 / (1 + cost_rate)) < 1e-12
assert np.all(net_wealth.iloc[-1] <= gross_wealth.iloc[-1] + 1e-12)
assert np.all(cost_wealth[50].iloc[-1] <= net_wealth.iloc[-1] + 1e-12)
print("All five zero-cost paths match direct compounding.")
print("All 900 ledger rows balance cash, fees and asset values.")
print("Initial purchase costs are included; no terminal sale is added.")
```

ผ่านการตรวจเส้นไม่มีต้นทุนครบห้าวิธี และ ledger 900 แถวจากห้าวิธี × 60 เดือน × สามอัตราต้นทุน ทุกแถวใช้ยอดซื้อขายจริงและทุกกรณีรวมค่าซื้อครั้งแรก

`assert` จะหยุดโค้ดถ้าเงื่อนไขไม่จริง `np.allclose` ใช้เปรียบเทียบตัวเลขภายใน tolerance เพื่อไม่ให้ความต่างระดับการแทนเลขทศนิยมกลายเป็นข้อผิดพลาดทางบัญชี การตรวจน้ำหนักกับ cash flow เหล่านี้ยืนยันว่าการคำนวณทำตามกติกาที่ระบุ แต่ยังไม่ยืนยันว่ากติกาหรือข้อมูลจำลองแทนตลาดได้ดี

<span id="interpreting-backtests"></span>

## อ่านผลโดยแยกตัวเลขสามชุด

Estimated risk เป็นความเสี่ยงจาก covariance 36 เดือนที่มีในวันเลือกน้ำหนัก Realized risk เป็นความเสี่ยงที่วัดจากผลตอบแทนพอร์ตที่เกิดขึ้นระหว่างถือ 60 เดือน ส่วน population risk เป็นคุณสมบัติของกระบวนการจำลองที่เรากำหนดไว้เอง ทั้งสามชุดไม่จำเป็นต้องเท่ากัน

ERC แบ่ง RRC เท่ากันตาม covariance ที่ส่งเข้า solver ได้ แต่ RRC ที่นำไปคำนวณใหม่ด้วย covariance ของอนาคตอาจไม่เท่ากัน GMV ลด variance ตาม covariance ที่ใช้ตัดสินใจได้ ส่วน realized volatility ในช่วงใหม่อาจไม่ต่ำที่สุดเสมอ ข้อจำกัดเดียวกันนี้ใช้กับ MaxDR ด้วย

ข้อมูลตัวอย่างมี mean ที่เท่ากันทุกสินทรัพย์ ไม่มีสัญญาณทำนาย mean ให้กลยุทธ์ใช้ แต่เส้นทางที่สุ่มได้ทำให้ผลตอบแทนเฉลี่ยของสินทรัพย์ต่างกัน การที่วิธีหนึ่งได้ CAGR สูงกว่าในตารางจึงยังไม่เป็นหลักฐานว่ามันค้นพบสินทรัพย์ที่มี expected return สูงกว่า

หากต่อยอดไปยังข้อมูลจริง ควรกำหนด universe และข้อมูลที่มีให้ใช้ ณ แต่ละวัน จัดการสินทรัพย์ที่เข้าหรือออกจากตลาด เงินปันผล และข้อมูลที่ขาดหาย รวมถึงใช้ราคาและต้นทุนที่ซื้อขายได้จริง การเพิ่มหลายช่วงตลาดหรือหลายการจำลองช่วยเห็นความแปรปรวนของผล แต่ไม่ทำให้สมมติฐานที่ผิดกลายเป็นถูก

<span id="exercises"></span>

## แบบฝึกหัด

### 1. เดือน 70 ใช้ข้อมูลใด

ใช้ rolling window 36 เดือน ถ้าจะเลือกน้ำหนักสำหรับถือเดือน 70 ต้องใช้เดือนแรกและเดือนสุดท้ายใด? ผลตอบแทนเดือน 70 เริ่มมีผลต่อน้ำหนักครั้งไหน?

<details>
<summary>ดูเฉลย</summary>

ใช้เดือน 34–69 รวม 36 เดือน ผลตอบแทนเดือน 70 เข้า training window สำหรับเลือกน้ำหนักถือเดือน 71 การใช้เดือน 35–70 เพื่อถือน้ำหนักในเดือน 70 จะรู้ผลตอบแทนของงวดที่กำลังทดสอบก่อนตัดสินใจ

</details>

### 2. EW ต้องปรับพอร์ตหรือไม่

เริ่มถือสองสินทรัพย์อย่างละ 50% เดือนนั้น A ได้ +10% และ B ได้ 0% ถ้าไม่คิดต้นทุน น้ำหนัก A ก่อนปรับรอบใหม่เท่าไร? หากยังต้องการ EW จะต้องทำธุรกรรมหรือไม่?

<details>
<summary>ดูเฉลย</summary>

จากทุนหนึ่งหน่วย มูลค่า A เป็น 0.55 และ B เป็น 0.50 รวม 1.05 น้ำหนัก A จึงเป็น $0.55/1.05\approx52.381\%$ การกลับไป 50/50 ต้องขาย A แล้วซื้อ B แม้น้ำหนักเป้าหมายของสองเดือนจะเหมือนกัน

</details>

### 3. เริ่มเงินสด 100,000 บาทที่ต้นทุน 50 bps

ถ้าลงทุนเต็มจำนวนหลังหักค่าใช้จ่าย ควรซื้อสินทรัพย์รวมเท่าไร และจ่ายค่าซื้อเท่าไร?

<details>
<summary>ดูเฉลย</summary>

$c=0.005$ ให้ $s=1/1.005$ ซื้อสินทรัพย์รวมประมาณ 99,502.487562 บาทและจ่ายค่าใช้จ่าย 497.512438 บาท ยอดรวมเป็น 100,000 บาท ถ้าซื้อเต็ม 100,000 บาทแล้วจ่ายเพิ่มอีก 500 บาท จะใช้เงินเกินทุนที่มี

</details>

### 4. นับผลตอบแทนกี่งวด

ตาราง wealth ของ backtest มี 61 แถวตั้งแต่เดือน 36 ถึง 96 เหตุใดจึงใช้ $12/60$ ใน CAGR แทน $12/61$? ควรนำ 36 เดือนแรกที่เก็บข้อมูลมารวมใน CAGR หรือไม่?

<details>
<summary>ดูเฉลย</summary>

แถวแรกเป็นเงินทุนก่อนเริ่มถือ อีก 60 แถวเป็นปลายเดือนของผลตอบแทน 60 งวด จึงใช้เลขชี้กำลัง $12/60$ ช่วง training ไม่มีผลตอบแทนการถือของกลยุทธ์นี้ในบัญชีที่สร้างไว้ จึงไม่เอามารวมใน CAGR

</details>

### 5. ต้นทุนซื้อขายกับ one-way turnover

พอร์ตมีเงินสดเตรียมไว้จ่ายค่าใช้จ่าย ขายสินทรัพย์ 20% ของทุนก่อนซื้อขาย แล้วซื้อสินทรัพย์อื่นอีก 20% หากอัตราต้นทุนคือ 10 bps ต่อมูลค่าธุรกรรม ต้นทุนคิดเป็นกี่เปอร์เซ็นต์ของทุน? สำหรับโจทย์นี้ให้ใช้มูลค่าธุรกรรมที่ระบุเป็นยอดจริงแล้ว

<details>
<summary>ดูเฉลย</summary>

มูลค่าธุรกรรมทั้งสองด้านรวม 40% ของทุน ต้นทุนคือ $0.001\times0.4=0.0004$ หรือ 0.04% ของทุน ถ้าใช้ one-way turnover 20% ต้องคูณอัตราสองด้านที่สอดคล้องกัน จึงจะได้ต้นทุนเดียวกัน ใน backtest ยอดซื้อและขายจริงเกิดจากการ solve สมการที่หักเงินต้นทุนออกด้วย

</details>

### 6. ERC ชนะด้านใดในตาราง

จากกรณีต้นทุน 10 bps ERC มี CAGR สูงสุด ส่วน GMV มี Sharpe สูงสุด ข้อมูลนี้เพียงพอให้เลือกว่ากลยุทธ์ใดดีที่สุดสำหรับทุกคนหรือไม่? ถ้าต้องการใช้ Sharpe ที่เขียนไว้ในบท ควรใช้ numerator ตัวใด?

<details>
<summary>ดูเฉลย</summary>

ยังเลือกเช่นนั้นไม่ได้ ต้องระบุวัตถุประสงค์ ข้อจำกัด และความเสี่ยงที่ผู้ลงทุนรับได้ อีกทั้งผลมาจากข้อมูลจำลองชุดเดียว Sharpe ของบทใช้ arithmetic mean รายเดือนหัก risk-free rate ศูนย์ แล้วหารด้วย sample SD รายเดือนและคูณ $\sqrt{12}$ ค่า CAGR ใช้อธิบายการเติบโตของทุนแยกต่างหาก

</details>

หากจะทดลองกติกาใหม่ ให้เก็บตารางน้ำหนักก่อนถือและ ledger แบบเดิมไว้ด้วย จะได้ตรวจย้อนกลับได้ว่าผลที่ต่างมาจากข้อมูลที่ใช้เลือกน้ำหนัก จังหวะซื้อขาย หรือต้นทุนที่จ่าย

<span id="sources"></span>

## แหล่งอ้างอิงและขอบเขตของตัวอย่าง

ตรวจแหล่งข้อมูลวันที่ 3 ตุลาคม 2569 อ่าน transcript เต็มของ Coursera ทั้งสองตอนด้านล่าง บทนี้ใช้ข้อมูลและโค้ดที่สร้างสำหรับการสอน ไม่ได้นำผลตอบแทนหุ้นหรือ industry portfolios ของคอร์สมาคำนวณซ้ำ และไม่เผยแพร่ transcript

- Coursera, EDHEC, [Comparing Diversification Options](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/lulgY/comparing-diversification-options): ใช้ตรวจแนวทางเทียบหลายวิธีบน universe เดียว ผลของขอบเขตน้ำหนัก และการอ่านผลที่ขึ้นกับช่วงตลาด ไม่ยกสถิติทางประวัติศาสตร์ใน transcript มาใช้เป็นผลของตัวอย่างนี้
- Coursera, EDHEC, [Module 4 Lab Session — Risk Contribution and Risk Parity](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/u0D4G/module-4-lab-session-risk-contribution-and-risk-parity): ใช้ตรวจการคำนวณ fractional risk contributions การสร้างฟังก์ชันจัดน้ำหนัก และการเทียบ backtest ด้วยหน้าต่าง 36 เดือนเหมือนกัน ตัวอย่างนี้เพิ่มบัญชีต้นทุน การตรวจ convergence และการตรวจเวลาใช้ข้อมูลของตนเอง
- [NumPy: Generator.uniform](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.uniform.html): ตรวจความหมายของขอบเขตและรูปร่างตัวอย่างสุ่ม
- [SciPy: brentq](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html): ตรวจการหารากของฟังก์ชันต่อเนื่องในช่วงคร่อมคำตอบ สมการต้นทุนและตัวอย่างสองสินทรัพย์ในบทคำนวณจากกติกาซื้อขายที่ระบุไว้ข้างต้น
