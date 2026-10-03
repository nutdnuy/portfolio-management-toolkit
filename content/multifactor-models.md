---
title: หลายปัจจัย Fama–French และ alpha ที่เปลี่ยนตามแบบจำลอง
description: สร้างและอ่าน SMB HML แยก SML ออกจาก CML แล้วทำ multiple regression ด้วย NumPy พร้อมตรวจหน่วย ปัจจัยตกหล่น และเวลาในการใช้ข้อมูล
---

# หลายปัจจัย Fama–French และ alpha ที่เปลี่ยนตามแบบจำลอง

<p class="lead">ถ้ากองทุนมี alpha บวกเมื่อเทียบกับตลาด เหตุใดการเพิ่มปัจจัยอีกสองตัวจึงทำให้ alpha ลดเหลือศูนย์ได้?</p>

ใน[บท beta และ alpha](factor-investing.html#ols-from-scratch) เราใช้ผลตอบแทนตลาดอธิบายผลตอบแทนกองทุนด้วยเส้นตรงหนึ่งเส้น แต่กองทุนอาจถือหุ้นเล็กหรือหุ้นที่มีลักษณะ value มากกว่าตลาด หากการเคลื่อนไหวเหล่านี้ยังไม่อยู่ในแบบจำลอง ส่วนหนึ่งอาจปรากฏอยู่ใน alpha หรือ residual ของการ fit ตลาดเพียงตัวเดียว

เราจะสร้างกองทุนสมมติที่ทราบปัจจัยครบตั้งแต่ต้น แล้วลองซ่อนบางปัจจัยจากการวิเคราะห์ เรียนทั้งความหมายของ Fama–French model และคำสั่ง multiple regression ที่ทำให้ประมาณความไวหลายตัวพร้อมกันได้ ตัวเลขทั้งหมดในตัวอย่าง Python เขียนขึ้นเพื่อสอน ไม่มีข้อมูลราคาตลาดจริง และไม่ใช่หลักฐานว่าปัจจัยใดจะให้ผลตอบแทนบวกในอนาคต

บทนี้ประกอบหัวข้อแบบจำลองหลายปัจจัยในคอร์ส Advanced Portfolio Construction and Analysis with Python เปิด Notebook ใหม่และรันทุกช่องตามลำดับได้โดยไม่พึ่งตัวแปรจากบทก่อนหน้า [ดาวน์โหลด Notebook ของบทนี้](notebooks/multifactor-models.ipynb) หากยังไม่คุ้นกับ excess return หรือ residual ให้อ่าน[แบบจำลองปัจจัยเดียว](factor-investing.html#excess-return)ก่อน

<span id="fama-french-factors"></span>

## จากลักษณะหุ้นสู่ผลตอบแทนปัจจัย

Fama–French three-factor model ใช้ผลตอบแทนตลาดส่วนเกินและผลตอบแทนส่วนต่างอีกสองชุด เราต้องอ่านก่อนว่าแต่ละคอลัมน์สร้างจากอะไร

| คอลัมน์ | ความหมาย | เมื่อค่าของเดือนนั้นเป็นบวก |
|---|---|---|
| Mkt−RF | ผลตอบแทนตลาดลบผลตอบแทนปลอดความเสี่ยง | ตลาดให้ผลตอบแทนสูงกว่า RF |
| SMB หรือ Small Minus Big | ผลตอบแทนพอร์ตหุ้นเล็กลบพอร์ตหุ้นใหญ่ตามวิธีสร้าง factor | ฝั่งหุ้นเล็กของ factor ชนะฝั่งหุ้นใหญ่ |
| HML หรือ High Minus Low | ผลตอบแทนพอร์ต book-to-market สูงลบพอร์ต book-to-market ต่ำ | ฝั่ง book-to-market สูงชนะฝั่งต่ำ |

Book-to-market ใช้มูลค่าทางบัญชีของส่วนผู้ถือหุ้นเทียบกับมูลค่าตลาดของส่วนผู้ถือหุ้น ค่าสูงหมายถึงมูลค่าทางบัญชีมากเมื่อเทียบกับมูลค่าตลาด จึงใช้เป็นนิยาม value แบบหนึ่ง มาตรวัดนี้ไม่ได้ยืนยันว่าหุ้นมีราคาผิดจากมูลค่าที่ควรเป็น และไม่เหมือนคำว่าเป็นบริษัทที่ดีในความหมายทั่วไป

วิธีสร้าง [FF3 ของ Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html) ใช้พอร์ตจากการแบ่งขนาดสองกลุ่มและ book-to-market สามกลุ่ม รวมเป็นหกพอร์ต สูตร SMB เฉลี่ยส่วนต่าง small กับ big ครบสามกลุ่ม ส่วน HML เปรียบเทียบ value กับ growth โดยเฉลี่ยข้ามขนาด บทเรียนวิดีโอใช้ deciles หรือการแบ่งสิบกลุ่มเพื่อให้เห็นแนวคิดการเรียงหุ้น แต่สูตร factor ทางการต้องอ่านจากรายละเอียดชุดข้อมูลนั้นโดยตรง

### คำนวณ SMB และ HML จากหกพอร์ตสมมติ

กำหนดผลตอบแทนหนึ่งเดือนของหกพอร์ตตามตารางในโค้ด ค่าเหล่านี้เป็นผลตอบแทนของพอร์ตที่สร้างเสร็จแล้ว เราไม่ได้จำลองการเลือกหุ้นหรือการถ่วงน้ำหนักภายในแต่ละพอร์ตในตัวอย่างนี้

`pd.Series` เก็บผลตอบแทนพร้อมชื่อ `six[[...]]` เลือกหลายชื่อ และ `.mean()` หาค่าเฉลี่ยของรายการที่เลือก

```python
import numpy as np
import pandas as pd
from scipy import stats

six = pd.Series({"SV": 0.018, "SN": 0.010, "SG": 0.006,
                 "BV": 0.012, "BN": 0.008, "BG": 0.002})
smb_example = six[["SV", "SN", "SG"]].mean() - six[["BV", "BN", "BG"]].mean()
hml_example = six[["SV", "BV"]].mean() - six[["SG", "BG"]].mean()
print(f"SMB: {smb_example:.2%}; HML: {hml_example:.2%}")
```

S ย่อจาก small, B จาก big ส่วน V/N/G หมายถึง value/neutral/growth ฝั่ง small ได้เฉลี่ย $(1.8+1.0+0.6)/3=1.1333\%$ และ big ได้ $(1.2+0.8+0.2)/3=0.7333\%$ ผลต่าง SMB เท่ากับ 0.40 จุดเปอร์เซ็นต์ ส่วน HML เท่ากับ $(1.8+1.2)/2-(0.6+0.2)/2=1.10$ จุดเปอร์เซ็นต์

SMB และ HML เป็นผลตอบแทนส่วนต่างของสองขา จึงไม่หัก RF อีกรอบเหมือนผลตอบแทนรวมของกองทุน ถ้าสองขาหัก RF ตัวเดียวกันอยู่แล้ว ผลต่าง $(R_L-R_f)-(R_S-R_f)$ ก็เท่ากับ $R_L-R_S$

การตีความส่วนต่างนี้เป็นกลยุทธ์ long–short ต้องกำหนดเงินอ้างอิงของแต่ละขา เงินประกัน การกู้ยืม และต้นทุนซื้อขายด้วย สถานะที่มูลค่าขา long กับ short เท่ากันมี net exposure เป็นศูนย์ แต่ผลต่าง 1% ไม่ใช่ “กำไร 1% จากเงินทุนศูนย์” ที่นำไปซื้อขายได้โดยไม่มีเงินประกัน

### FF3, FF5 และ momentum ใช้ชื่อให้ตรงแบบจำลอง

FF3 มีตลาด SMB และ HML ส่วน [FF5](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html) เพิ่ม RMW ซึ่งเปรียบเทียบ profitability สูงกับต่ำ และ CMA ซึ่งเปรียบเทียบการลงทุนของบริษัทแบบ conservative กับ aggressive ตามนิยามของข้อมูล ในที่นี้ investment หมายถึงการขยายสินทรัพย์ของบริษัท ไม่ใช่ระดับความกล้าเสี่ยงของผู้ถือกองทุน

Momentum เป็นปัจจัยเพิ่มเติมที่เปรียบเทียบผู้ชนะและผู้แพ้ตามผลตอบแทนย้อนหลังในช่วงที่ระบุ ไม่ใช่หนึ่งในสามตัวของ FF3 หรือหนึ่งในห้าตัวของ FF5 โดยอัตโนมัติ ต้องอ่านชื่อชุดข้อมูลและวิธีสร้างให้ครบ เช่น FF3 บวก momentum เป็นอีก specification หนึ่ง

แม้ FF3 และ FF5 มีคอลัมน์ชื่อ SMB เหมือนกัน วิธีรวมพอร์ตเพื่อสร้าง SMB ของ FF5 ใช้การจัดกลุ่มมากกว่า FF3 จึงไม่ควรสลับคอลัมน์ข้ามไฟล์โดยคิดว่าเหมือนกันทุกค่า นิยาม factor, ตลาดที่ครอบคลุม, สกุลเงิน และรุ่นข้อมูลเป็นส่วนหนึ่งของผลวิเคราะห์

<span id="sml-versus-cml"></span>

## SML ใช้ beta ส่วน CML ใช้ความผันผวน

ก่อนเพิ่มจำนวน factor ต้องแยกเส้นสองเส้นที่อาจพบในบท CAPM ให้ได้ Security Market Line หรือ SML วาง beta บนแกนนอนและ expected return บนแกนตั้ง:

$$
E[R_i]=R_f+\beta_i(E[R_M]-R_f).
$$

เป็นความสัมพันธ์ของสินทรัพย์หรือพอร์ตภายใต้ CAPM ส่วน Capital Market Line หรือ CML วาง standard deviation ของผลตอบแทนบนแกนนอน:

$$
E[R_p]=R_f+\frac{E[R_M]-R_f}{\sigma_M}\sigma_p.
$$

CML ใช้กับพอร์ตมีประสิทธิภาพที่ผสมสินทรัพย์ปลอดความเสี่ยงกับพอร์ตตลาดในดุลยภาพ ตามเงื่อนไขการกู้และให้กู้ของแบบจำลอง เส้นที่ผสมเงินสดกับพอร์ตเสี่ยงใด ๆ เรียกว่า CAL จะเรียก CML ได้เมื่อพอร์ตนั้นเป็นพอร์ตตลาดตามกรอบดังกล่าว ดู[ความต่าง CAL และ CML](portfolio-estimation.html#cal-cml)ในบทการประมาณพอร์ต

สมมติ RF 3% ต่อปี, ตลาดคาดหวัง 8% และ SD ตลาด 16% สินทรัพย์ A/B มี beta 0.8 เท่ากัน แต่ส่วนความเสี่ยงที่ไม่สัมพันธ์กับตลาดมี SD 5% และ 15% ตามลำดับ กำหนดในตัวอย่างให้ส่วนที่เหลือนี้มี covariance กับตลาดเป็นศูนย์ จึงรวม variance ได้

```python
rf_year = 0.03
market_mean_year = 0.08
market_sd_year = 0.16
beta_common = 0.8
residual_sds = np.array([0.0, 0.05, 0.15])
asset_sds = np.sqrt((beta_common * market_sd_year) ** 2 + residual_sds ** 2)
comparison = pd.DataFrame({
    "Beta": beta_common,
    "Expected return": rf_year + beta_common * (market_mean_year - rf_year),
    "SD": asset_sds,
}, index=["80% market + 20% RF", "Asset A", "Asset B"])
print(comparison.round(4))
```

ทั้งสามแถวมี expected return 7% และ beta 0.8 แต่ SD ของพอร์ตตลาดผสมเงินสดเท่ากับ 12.8% ส่วน A และ B ประมาณ 13.7419% และ 19.7190% ตามลำดับ หากใช้ CAPM กำหนด expected return ทั้งหมดอยู่จุดเดียวกันบน SML แต่ A/B ไม่อยู่บน CML เพราะมีความผันผวนมากกว่าพอร์ตผสมที่ให้ expected return เท่ากัน

การพล็อตผลตอบแทนที่เกิดขึ้นจริงหนึ่งปีเทียบกับ beta ไม่ทำให้ทุกจุดต้องอยู่บน SML ผลที่ทฤษฎีกล่าวถึงคือค่าคาดหวังภายใต้สมมติฐานของ CAPM ไม่ใช่ผลย้อนหลังแต่ละปี

<span id="multifactor-data"></span>

## สร้าง 16 เดือนที่มีปัจจัยสัมพันธ์กันบางส่วน

ต่อไปใช้หน่วยรายเดือนทั้งหมด เราสร้างผลตอบแทนส่วนเกินตลาดให้มีค่าเฉลี่ย 0.4%, SMB เฉลี่ย 0.6% และ HML เฉลี่ย 0.1% แล้วสร้างความสัมพันธ์ระหว่างปัจจัยไว้ด้วย หุ้นเล็กกับหุ้นใหญ่จึงไม่จำเป็นต้องให้ factor ที่เป็นอิสระจากตลาด และ HML ก็ไม่จำเป็นต้องเป็นอิสระจาก SMB

ให้ผลตอบแทนส่วนเกินกองทุนสมมติเป็น

$$
y_t=1.1f_{M,t}+0.8f_{S,t}-0.4f_{H,t}+e_t.
$$

ตัว $f$ หมายถึงผลตอบแทน factor และตัวห้อย M/S/H หมายถึงตลาด SMB/HML ตามลำดับ เราตั้ง alpha ของสมการนี้เป็นศูนย์ แล้วเพิ่ม $e_t$ ขนาด −0.2 หรือ +0.2 จุดเปอร์เซ็นต์เพื่อให้ยังมีส่วนที่อธิบายไม่ได้

`np.tile` ทำรูปแบบสั้นซ้ำให้ครบ 16 ค่า ส่วน `np.repeat([-1, 1], 8)` ทำ −1 ซ้ำแปดครั้งแล้ว +1 ซ้ำแปดครั้ง รูปแบบเหล่านี้เป็นอุปกรณ์สร้างโจทย์ที่รู้คำตอบ ไม่มีข้ออ้างว่าข้อมูล factor จริงสลับเครื่องหมายตามนี้ และไม่ได้ใช้ส่วนที่เหลือนี้อนุมาน p-value

```python
s1 = np.tile([-1, 1], 8)
s2 = np.tile([-1, -1, 1, 1], 4)
s3 = np.tile([-1, -1, -1, -1, 1, 1, 1, 1], 2)
s4 = np.repeat([-1, 1], 8)
F = pd.DataFrame({"Mkt-RF": 0.004 + 0.025 * s1,
                  "SMB": 0.006 + 0.3 * 0.025 * s1 + 0.010 * s2,
                  "HML": 0.001 - 0.2 * 0.025 * s1 + 0.012 * s3},
                 index=pd.period_range("2025-01", periods=16, freq="M"))
y_multi = F.to_numpy() @ np.array([1.1, 0.8, -0.4]) + 0.002 * s4
rf_multi = 0.002
print((F.head(4) * 100).round(2))
print(F.corr().round(3))
```

`F.to_numpy()` เป็นตารางตัวเลข 16 แถว 3 คอลัมน์ เครื่องหมาย `@` คือการคูณเมทริกซ์กับเวกเตอร์ โดยแต่ละแถวคูณกับ `[1.1, 0.8, -0.4]` แล้วรวมสามพจน์ ได้ผลตอบแทนกองทุนหนึ่งค่าต่อเดือน `y_multi` เป็น excess return อยู่แล้ว ถ้าต้องการผลตอบแทนรวมให้บวก `rf_multi`

เดือนแรก factor เป็น −2.10%, −1.15%, −0.60% ตามลำดับ Correlation ตลาดกับ SMB เท่ากับ 0.600, ตลาดกับ HML ประมาณ −0.385 และ SMB กับ HML ประมาณ −0.231 เราเห็นว่าปัจจัยเคลื่อนไหวร่วมกันบางส่วน แต่ยังมีข้อมูลที่ต่างกันให้แยกความไวได้

<span id="matrix-ols"></span>

## เมทริกซ์ OLS คือการเขียนสมการหลายแถวพร้อมกัน

แบบจำลองสามปัจจัยที่มี intercept คือ

$$
y_t=\alpha+b_M f_{M,t}+b_S f_{S,t}+b_H f_{H,t}+\varepsilon_t.
$$

สำหรับหนึ่งเดือน เราต้องคูณตัวเลขสี่ตัวกับ coefficient สี่ตัว: $[1,f_M,f_S,f_H]$ คูณ $[\alpha,b_M,b_S,b_H]$ ตัวเลข 1 ทำให้พจน์แรกเป็น alpha ทุกแถว จากนั้นนำแถวเดือนต่าง ๆ มาเรียงเป็นเมทริกซ์ $X$ ได้สมการย่อ $y=X\theta+\varepsilon$

| ชิ้นส่วน | ขนาดในตัวอย่าง | ความหมาย |
|---|---|---|
| $X$ | 16 แถว × 4 คอลัมน์ | คอลัมน์หนึ่งทั้งหมด ตามด้วย factor สามตัว |
| $\theta$ | 4 ค่า | alpha และ loading สามตัว |
| $y$ | 16 ค่า | ผลตอบแทนส่วนเกินกองทุน |
| $X\theta$ | 16 ค่า | fitted excess return ของแต่ละเดือน |

OLS เลือก $\theta$ ให้ $\sum_t(y_t-(X\theta)_t)^2$ ต่ำที่สุด หากคอลัมน์เป็นอิสระเชิงเส้น คำตอบเชิงพีชคณิตเขียนได้ว่า $(X^\top X)^{-1}X^\top y$ โดย $X^\top$ คือการสลับแถวกับคอลัมน์ แต่เวลาคำนวณจริงเราใช้ `np.linalg.lstsq` ให้ไลบรารีแก้ปัญหาโดยไม่สร้างเมทริกซ์ผกผันเอง

`np.ones(n)` สร้างเลขหนึ่ง $n$ ตัว และ `np.column_stack` วางข้อมูลข้างกันเป็นคอลัมน์ ส่วน `.shape` บอกขนาด array

```python
X = np.column_stack([np.ones(len(F)), F.to_numpy()])
coef, solver_sse, rank, singular_values = np.linalg.lstsq(X, y_multi, rcond=None)
fitted_multi = X @ coef
residual_multi = y_multi - fitted_multi
coefficients = pd.Series(coef, index=["Alpha", "Mkt-RF", "SMB", "HML"])
print("X shape:", X.shape, "rank:", rank)
print(coefficients.round(6))
```

ได้ `X shape: (16, 4)` และ rank 4 แปลว่าข้อมูลมีคอลัมน์อิสระพอให้ระบุ coefficient สี่ค่า ผลคือ alpha ใกล้ศูนย์, ตลาด 1.1, SMB 0.8 และ HML −0.4 ตรงกับข้อมูลที่สร้าง ค่า alpha อาจปรากฏเป็นจำนวนเล็กมาก เช่น $-1.7\times10^{-18}$ จากเลขทศนิยมในคอมพิวเตอร์

`lstsq` คืนค่าหลายชิ้นจึงใช้ชื่อตัวแปรสี่ชื่อรับพร้อมกัน `solver_sse` เป็นผลรวมกำลังสองที่ตัวแก้สมการคืนมา ไม่ใช่ residual รายเดือน และอาจเป็น array ว่างได้ในบางกรณี เช่น rank ไม่ครบ เราจึงคำนวณ `residual_multi = y_multi - X @ coef` เองเมื่ออยากดูแต่ละเดือน รายละเอียดรูปแบบผลลัพธ์อยู่ใน[เอกสาร NumPy](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html)

<span id="omitted-factor-alpha"></span>

## ซ่อน SMB และ HML แล้ว alpha ปรากฏ

ตอนนี้ทำเหมือนยังไม่รู้ปัจจัยอีกสองตัว แล้ว fit กองทุนเดียวกันด้วยตลาดอย่างเดียว ไม่เปลี่ยนผลตอบแทนกองทุนหรือเลือกช่วงข้อมูลใหม่

```python
X_market = np.column_stack([np.ones(len(F)), F["Mkt-RF"].to_numpy()])
one_factor_coef = np.linalg.lstsq(X_market, y_multi, rcond=None)[0]
residual_market = y_multi - X_market @ one_factor_coef
tss_multi = np.sum((y_multi - y_multi.mean()) ** 2)
r2_market = 1 - np.sum(residual_market ** 2) / tss_multi
r2_multi = 1 - np.sum(residual_multi ** 2) / tss_multi
print(f"One-factor alpha: {one_factor_coef[0]:.3%}; beta: {one_factor_coef[1]:.4f}")
print(f"Three-factor alpha: {coef[0]:.3%}")
print(f"R-squared: one factor {r2_market:.6f}; three factors {r2_multi:.6f}")
```

`[0]` หลัง `lstsq(...)` เลือกผลลัพธ์ชิ้นแรกซึ่งเป็น coefficient array แล้ว `one_factor_coef[0]` คือ intercept และ `[1]` คือ market beta ได้ alpha ตลาดตัวเดียว 0.312% ต่อเดือน และ beta 1.4200 เมื่อใช้สามปัจจัย alpha เป็นศูนย์ตามความละเอียดการคำนวณ ส่วน $R^2$ เพิ่มจาก 0.932627 เป็น 0.997040

เรารู้คำตอบเพราะเป็นผู้สร้างข้อมูล กองทุนนี้ไม่มี alpha ในสมการสามปัจจัยตั้งแต่ต้น ค่า alpha 0.312% จากแบบจำลองแรกจึงไม่ใช่หลักฐานฝีมือ แต่เป็นผลจากการอธิบายข้อมูลด้วยปัจจัยไม่ครบและค่าเฉลี่ยของปัจจัยที่ตกหล่น

ในข้อมูลจริง การเพิ่มปัจจัยไม่ได้พิสูจน์ทันทีว่าพบคำอธิบายที่ถูกต้อง การเพิ่มตัวแปรให้ OLS ใน sample เดิมทำให้ SSE ไม่เพิ่มและ $R^2$ ไม่ลดอยู่แล้ว แม้ตัวแปรใหม่จะช่วยเพียงเล็กน้อยจากความบังเอิญ ต้องพิจารณาเหตุผลทางเศรษฐศาสตร์ ความเสถียร และข้อมูลที่ไม่ได้ใช้เลือกแบบจำลองด้วย

### คำนวณผลของปัจจัยตกหล่นด้วย covariance

เพื่อเห็นว่าค่า 1.42 มาจากไหน เขียนความชันจากตลาดเพียงตัวเดียวในตัวอย่างนี้ได้ว่า

$$
\tilde b_M=b_M+b_S\frac{\operatorname{Cov}(f_M,f_S)}{\operatorname{Var}(f_M)}
+b_H\frac{\operatorname{Cov}(f_M,f_H)}{\operatorname{Var}(f_M)}.
$$

สูตรนี้ใช้กับชุดที่ residual ไม่มี covariance กับตลาดตามที่สร้างไว้ ในประชากรทั่วไปต้องเพิ่มพจน์จาก covariance กับ error หากไม่เป็นศูนย์ ส่วน intercept ของแบบจำลองที่ตัดตัวแปรออกคือ $\tilde\alpha=\bar y-\tilde b_M\bar f_M$

```python
factor_cov = F.cov()
market_variance = factor_cov.loc["Mkt-RF", "Mkt-RF"]
beta_from_omission = (coef[1]
    + coef[2] * factor_cov.loc["Mkt-RF", "SMB"] / market_variance
    + coef[3] * factor_cov.loc["Mkt-RF", "HML"] / market_variance)
alpha_from_omission = y_multi.mean() - beta_from_omission * F["Mkt-RF"].mean()
print(f"Omitted-factor beta: {beta_from_omission:.4f}")
print(f"Omitted-factor alpha: {alpha_from_omission:.3%}")
```

อัตราส่วน covariance ต่อ variance ในสองพจน์เท่ากับ 0.3 และ −0.2 จึงได้ $1.1+0.8(0.3)+(-0.4)(-0.2)=1.42$ ทั้ง SMB และ HML ที่ตกหล่นทำให้ตลาดรับความสัมพันธ์บางส่วนไปด้วย แล้ว intercept ต้องขยับเพื่อให้เส้นผ่านค่าเฉลี่ยของข้อมูล

ดังนั้น beta 1.42 จากปัจจัยเดียวกับ loading ตลาด 1.1 จากสามปัจจัยตอบคนละเงื่อนไข ค่า 1.1 อธิบายการเปลี่ยนตลาดเมื่อควบคุมค่าของ SMB และ HML ในสมการให้คงเดิม ขณะที่ 1.42 รวมความสัมพันธ์ร่วมกับปัจจัยที่ไม่ได้แยกออกมา

<span id="loadings-not-weights"></span>

## Loading คือความไว ไม่ใช่น้ำหนักเงินลงทุน

ผลลัพธ์ `[1.1, 0.8, -0.4]` รวมเป็น 1.5 แต่การ fit ไม่มีเงื่อนไขให้รวมหนึ่ง OLS พยายามอธิบายผลตอบแทน และแต่ละ factor อาจเป็นผลต่างพอร์ตที่มีทั้งขา long และ short อยู่แล้ว เราจึงอ่านค่า 0.8 ว่า loading ต่อ SMB เท่ากับ 0.8 ไม่ใช่กองทุนถือหุ้นเล็ก 80% ของมูลค่าทรัพย์สิน

เมื่อ SMB เปลี่ยนเพิ่ม 1 จุดเปอร์เซ็นต์โดยปัจจัยอื่นคงเดิม fitted excess return จะเพิ่ม 0.8 จุดเปอร์เซ็นต์ ส่วน HML loading −0.4 หมายถึงความสัมพันธ์เชิงเงื่อนไขในทิศตรงข้ามกับ factor HML แต่ยังไม่เพียงพอจะบอกชื่อหุ้นหรือสัดส่วนหุ้น growth จริงที่ถืออยู่

เราคำนวณส่วนอธิบายของเดือนแรกเพื่อตรวจผลรวม `F.iloc[0]` เลือกแถวแรกด้วยตำแหน่ง `.mul(...)` คูณแต่ละค่า และ `pd.concat` ต่อ Series ที่มีชื่อไว้ด้วยกัน

```python
first_contributions = F.iloc[0].mul(coef[1:])
first_breakdown = pd.concat([
    pd.Series({"RF": rf_multi, "Alpha": coef[0]}),
    first_contributions,
    pd.Series({"Residual": residual_multi[0]}),
])
print((first_breakdown * 100).round(4))
print(f"Sum: {first_breakdown.sum():.2%}")
print(f"Actual total return: {rf_multi + y_multi[0]:.2%}")
```

`coef[1:]` เลือกตั้งแต่ coefficient ตำแหน่ง 1 จนจบ จึงเหลือ loading สามตัว ในเดือนแรกส่วนจากตลาดคือ −2.31 จุดเปอร์เซ็นต์, SMB −0.92, HML +0.24, residual −0.20, alpha ศูนย์ และ RF +0.20 รวมเป็นผลตอบแทนกองทุน −2.99%

HML ของเดือนนั้นติดลบและ loading ก็ติดลบ ผลคูณจึงเป็นบวก นี่เป็นการแจกแจงผลตอบแทนที่เกิดขึ้นแล้วด้วยค่า factor ของเดือนเดียวกัน ไม่ได้บอกว่ารู้ก่อนต้นเดือนว่าจะได้กำไรจาก HML 0.24 จุดเปอร์เซ็นต์

<span id="factor-risk-model"></span>

## ใช้ factor อธิบายความเสี่ยงต้องนับ covariance ระหว่างปัจจัย

เมื่อมีหลายปัจจัย ความเสี่ยงส่วนที่อธิบายได้ไม่เท่ากับการรวม $b_j^2\operatorname{Var}(f_j)$ อย่างเดียว เพราะ factor มี covariance กัน ให้ $b$ เป็นเวกเตอร์ loading สามค่า และ $\Omega$ เป็นเมทริกซ์ covariance ของ factor จะได้

$$
\operatorname{Var}(b^\top f)=b^\top\Omega b.
$$

สำหรับกองทุน $y=\alpha+b^\top f+\varepsilon$ สูตร variance แบบเต็มยังมี $2\operatorname{Cov}(b^\top f,\varepsilon)$ ด้วย ถ้า factor กับ residual มี covariance ศูนย์จึงลดเหลือ $b^\top\Omega b+\operatorname{Var}(\varepsilon)$ การ fit OLS พร้อม intercept ให้เงื่อนไขตั้งฉากใน sample ของเรา แต่การใช้กับความเสี่ยงอนาคตเป็นสมมติฐานที่ต้องตรวจเพิ่ม

```python
loadings = coef[1:]
Omega = F.cov().to_numpy()
factor_variance = loadings @ Omega @ loadings
residual_variance = np.var(residual_multi, ddof=1)
total_variance = np.var(y_multi, ddof=1)
diagonal_only = np.sum(loadings ** 2 * np.diag(Omega))
print(f"Factor variance with covariances: {factor_variance:.8f}")
print(f"Using only diagonal terms: {diagonal_only:.8f}")
print("Variance identity:", np.isclose(total_variance, factor_variance + residual_variance))
```

`np.diag(Omega)` เลือก variance ตามแนวทแยงของเมทริกซ์ การใช้ covariance ครบได้ factor variance ประมาณ 0.00143711 ส่วนการใช้เฉพาะแนวทแยงได้ 0.00094218 ในชุดนี้การทิ้ง covariance จึงประเมินความเสี่ยงส่วน factor ต่ำลง บรรทัดสุดท้ายได้ `True` หน่วยของตัวเลข variance ในที่นี้เป็นผลตอบแทนทศนิยมรายเดือนยกกำลังสอง ต้องถอดรากก่อนอ่านเป็น SD และคูณ 100 เมื่อต้องการแสดงเป็นเปอร์เซ็นต์

งานนี้เป็น factor risk model ในความหมายที่ใช้ปัจจัยลดจำนวนความสัมพันธ์ที่ต้องอธิบาย ส่วนการกำหนด expected return ต้องมีข้อมูลเพิ่มว่าคาด factor premium เท่าไร แบบจำลองที่อธิบาย covariance ได้ดีจึงยังไม่ได้ให้คำตอบว่าควรคาดหวังผลตอบแทน 8% หรือ 12% ต่อปี

<span id="multifactor-units"></span>

## หน่วย factor และลำดับคอลัมน์เป็นส่วนหนึ่งของคำตอบ

ถ้าไฟล์เก็บ `1.5` โดยหมายถึง 1.5% ต้องหาร 100 ก่อนใช้กับผลตอบแทนกองทุนที่เก็บเป็น `0.015` การเปลี่ยนหน่วยของตัวแปรอธิบายเพียงตัวเดียวทำให้ coefficient ของตัวนั้นเปลี่ยนตาม ลองคูณเฉพาะ SMB ด้วย 100

```python
F_percent_smb = F.copy()
F_percent_smb["SMB"] = 100 * F_percent_smb["SMB"]
X_percent_smb = np.column_stack([np.ones(len(F)), F_percent_smb.to_numpy()])
coef_percent_smb = np.linalg.lstsq(X_percent_smb, y_multi, rcond=None)[0]
print(f"Original SMB loading: {coef[2]:.4f}")
print(f"SMB loading after unit change: {coef_percent_smb[2]:.4f}")
print("Same fitted returns:", np.allclose(X @ coef, X_percent_smb @ coef_percent_smb))
```

SMB loading เปลี่ยนจาก 0.8000 เป็น 0.0080 แต่ fitted return เหมือนเดิม เพราะตัวแปร SMB ใหญ่ขึ้น 100 เท่า `np.allclose` เปรียบเทียบ array ทั้งชุดโดยยอมให้คลาดเล็กน้อยจากเลขทศนิยม ถ้าใครนำ loading 0.008 ไปเทียบกับ 0.8 โดยไม่อ่านหน่วย อาจเข้าใจผิดว่ากองทุนแรกไวต่อ SMB น้อยกว่าร้อยเท่า

เมื่อแปลง DataFrame เป็น array แล้ว ชื่อคอลัมน์ไม่ได้ช่วยจับคู่การคูณอีกต่อไป `coef[1:]` ในบทนี้เรียง Mkt−RF, SMB, HML เสมอ ถ้าสลับคอลัมน์ของ $X$ ต้องสลับ loading ให้ตรงก่อนคูณ การตรวจชื่อ factor และลำดับจึงต้องทำก่อนละทิ้ง labels

<span id="collinearity"></span>

## ปัจจัยซ้ำกันทำให้แยก coefficient ไม่ได้

ปัจจัยสัมพันธ์กันบางส่วนยังทำ regression ได้ แต่ถ้าคอลัมน์หนึ่งเป็นผลรวมเชิงเส้นของคอลัมน์อื่นพอดี ข้อมูลจะระบุ coefficient ทุกตัวอย่างมีคำตอบเดียวไม่ได้ ตัวอย่างเช่นเพิ่มคอลัมน์ใหม่ที่เท่ากับสองเท่าของ SMB

```python
X_duplicate = np.column_stack([X, 2 * F["SMB"].to_numpy()])
coef_duplicate, _, rank_duplicate, _ = np.linalg.lstsq(X_duplicate, y_multi, rcond=None)
print("Columns:", X_duplicate.shape[1], "rank:", rank_duplicate)
print(f"Original SMB: {coef[2]:.4f}")
print(f"Split coefficients: {coef_duplicate[2]:.4f}, {coef_duplicate[4]:.4f}")
print("Same fitted returns:", np.allclose(X_duplicate @ coef_duplicate, fitted_multi))
```

มี 5 คอลัมน์แต่ rank เท่ากับ 4 NumPy ยังคืนคำตอบหนึ่งให้ โดยในชุดนี้ coefficient สองคอลัมน์ SMB ถูกแบ่งเป็น 0.16 และ 0.32 เมื่อรวมผลจึงได้ $0.16\times SMB+0.32\times(2SMB)=0.8\times SMB$ เหมือนเดิม `_` เป็นชื่อตัวแปรที่นิยมใช้รับค่าที่ไม่ต้องนำไปอ่านต่อ

คำตอบชุดนี้เป็นคำตอบที่ `lstsq` เลือกตามเกณฑ์ของมันจากหลายคำตอบที่ fit ได้เท่ากัน จึงไม่ควรตีความว่าเราค้นพบความเสี่ยงใหม่สองชนิด เมื่อตัวแปรเกือบซ้ำกันแต่ไม่เท่าพอดี coefficient อาจแกว่งมากจากการเปลี่ยนข้อมูลเพียงเล็กน้อย แม้ fitted return ยังใกล้เคียงเดิม

ก่อนรายงาน loading จึงต้องตรวจจำนวน observations, rank และความสัมพันธ์ระหว่าง factor การมีเดือนมากกว่าจำนวน coefficient เป็นเงื่อนไขหนึ่งสำหรับการประเมิน residual variance แต่ยังไม่พอรับประกันว่าแบบจำลองเสถียรหรือถูกต้อง

<span id="factor-data-timing"></span>

## ข้อมูลเดือนเดียวกันช่วยอธิบายย้อนหลัง แต่ยังใช้ทำนายล่วงหน้าไม่ได้

การคำนวณ contribution ของเดือนมกราคมใช้ทั้งผลตอบแทนกองทุนและ factor ของมกราคม ซึ่งเรารู้หลังเดือนจบ หากต้องตัดสินใจต้นเดือน ต้องใช้ข้อมูลที่มีอยู่ก่อนตัดสินใจ และต้องพยากรณ์ค่า factor ของเดือนนั้นแยกต่างหาก

ลองแบ่งข้อมูลตามเวลา ใช้ 12 เดือนแรกประมาณ loading แล้วนำ coefficient เดิมไปอธิบายกองทุนใน 4 เดือนที่เหลือ โดยใช้ factor ที่เกิดขึ้นจริงในสี่เดือนนั้น การทดสอบนี้ตรวจความสัมพันธ์นอกช่วง fit แต่ยังเป็น conditional attribution เพราะรู้ factor ของเดือนทดสอบแล้ว

`X[:12]` เลือกแถวก่อนตำแหน่ง 12 ส่วน `X[12:]` เลือกตั้งแต่ตำแหน่ง 12 จนจบ เราไม่สุ่มสลับเดือนก่อนแบ่ง เพื่อให้ช่วงทดสอบเกิดหลังช่วงประมาณ

```python
train_coef = np.linalg.lstsq(X[:12], y_multi[:12], rcond=None)[0]
heldout_fitted = X[12:] @ train_coef
heldout_errors = y_multi[12:] - heldout_fitted
heldout_rmse = np.sqrt(np.mean(heldout_errors ** 2))
print(pd.Series(train_coef, index=coefficients.index).round(6))
print(f"Held-out conditional RMSE: {heldout_rmse:.3%}")
```

ค่า fit จาก 12 เดือนแรกได้ alpha −0.085% ต่อเดือน, market loading ประมาณ 1.083333, SMB 0.8 และ HML −0.483333 ส่วน RMSE ในสี่เดือนหลังเท่ากับ 0.400% ต่อเดือน RMSE คือรากของค่าเฉลี่ย error กำลังสอง จึงกลับมาอยู่ในหน่วยผลตอบแทนเดียวกับ $y$

แม้สมการที่ใช้สร้างกองทุนไม่เปลี่ยน แต่รูปแบบ residual ในช่วงสั้นทำให้ coefficient ที่ประมาณต่างจากค่าที่ตั้งไว้ได้ การแบ่งช่วงนี้สาธิตขั้นตอนเท่านั้น ข้อมูล 16 เดือนที่สร้างเป็นแพตเทิร์นไม่รองรับข้อสรุปว่าแบบจำลองจะทำงานกับตลาดจริงดีเพียงใด

สำหรับไฟล์จริงให้ตรวจวันที่ก่อน fit: หนึ่งแถวต้องเป็นช่วงเดียวกัน ห้ามให้เดือนธันวาคมของกองทุนจับคู่กับเดือนมกราคมของ factor เพราะแถวเรียงอยู่ตำแหน่งเดียวกัน เมื่อต่อ Series ด้วย index แล้วตัดแถวขาดหาย ต้องรายงานช่วงเวลาที่เหลือและจำนวนเดือน การแทน factor ที่ขาดด้วยศูนย์แปลว่าใส่ผลตอบแทน factor เท่ากับศูนย์เอง ไม่ใช่การบอกว่าไม่มีข้อมูล

ถ้าสร้าง factor จากงบการเงิน ต้องใช้วันที่ข้อมูลเปิดเผยต่อผู้ลงทุนจริงด้วย งบที่ระบุปีบัญชีสิ้นสุดธันวาคมอาจยังไม่ประกาศในสิ้นเดือนนั้น การเลือกหุ้นด้วยค่าที่รู้ในภายหลังจะทำให้ผลย้อนหลังใช้ข้อมูลอนาคตหรือ look-ahead bias ได้

<span id="factor-premium-scenario"></span>

## คาดผลตอบแทนต้องตั้ง factor premium แยกจาก loading

สมมติว่าเรามี loading สามตัวจากแบบจำลอง และต้องการสำรวจผลตอบแทนคาดหวังเดือนถัดไป ให้ตั้งค่าคาดหวังของ factor เองอย่างชัดเจน ในสถานการณ์นี้ตั้ง market premium 0.4%, SMB 0.2% และ HML 0.1% ต่อเดือน พร้อม RF 0.2% และสมมติ expected alpha เป็นศูนย์

$$
E[R_i]=R_f+\alpha_{\mathrm{assumed}}+b_M E[f_M]+b_S E[f_S]+b_H E[f_H].
$$

เราเลือกค่าคาดหวังนี้เป็นข้อมูลเข้าใหม่ ไม่ได้อ้างว่าค่าเฉลี่ย 16 เดือนเท่ากับค่าคาดหวังที่ทราบแน่นอน `reindex` เรียง Series ตามชื่อคอลัมน์ของ `F` ก่อนแปลงเป็น array เพื่อให้จับคู่ loading ถูกตัว

```python
assumed_premiums = pd.Series({"Mkt-RF": 0.004, "SMB": 0.002, "HML": 0.001})
assumed_alpha = 0.0
expected_excess = assumed_alpha + loadings @ assumed_premiums.reindex(F.columns).to_numpy()
expected_total = rf_multi + expected_excess
print(f"Scenario expected excess return: {expected_excess:.3%}")
print(f"Scenario expected total return: {expected_total:.3%}")
```

ได้ excess return คาดหวัง 0.560% และผลตอบแทนรวมคาดหวัง 0.760% ต่อเดือน เพราะ $0.2+1.1(0.4)+0.8(0.2)-0.4(0.1)=0.76\%$ ถ้าปรับค่าคาดหวัง SMB ลง ผลตอบแทนคาดหวังของกองทุนที่ loading SMB เป็นบวกก็ลดลง แม้สมการอธิบายความเสี่ยงจะใช้ loading ชุดเดิม

ผลตอบแทนนี้ไม่ใช่ CAGR และไม่ได้รวมความไม่แน่นอนของ coefficient หรือ factor premium การตั้ง alpha เป็นศูนย์คือข้อสมมติของสถานการณ์ ต้องบอกผู้อ่านทุกครั้งที่ใช้ หากใส่ estimated alpha ย้อนหลังเพื่อคาดอนาคต ก็ต้องมีเหตุผลว่าค่านั้นคงอยู่ต่อได้อย่างไร

<span id="historical-factor-example"></span>

## ลองอ่านผลจากข้อมูล Berkshire ในชุดคอร์ส

ส่วนนี้เปลี่ยนจากข้อมูลสมมติเป็นกรณีศึกษาย้อนหลังตามหัวข้อใน [Foundations Lab](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/ZdgGw/module-1-lab-session-foundations) เราคำนวณใหม่จากไฟล์ `brka_d_ret.csv` และ `F-F_Research_Data_Factors_m.csv` ใน ZIP ข้อมูลของคอร์ส ชุดที่ใช้เป็น snapshot ถึงธันวาคม 2018 ผลด้านล่างอ้างถึงไฟล์ชุดนี้โดยเฉพาะ

ไฟล์แรกมีผลตอบแทนรายวัน 7,307 แถว ตั้งแต่ 2 มกราคม 1990 ถึง 31 ธันวาคม 2018 เก็บเป็นทศนิยมอยู่แล้ว เรารวมภายในแต่ละเดือนด้วย $\prod_{d\in\text{month}}(1+R_d)-1$ ได้ 348 เดือน ตั้งแต่มกราคม 1990 ถึงธันวาคม 2018 การรวมรายวันเป็นรายเดือนใช้การทบต้น ไม่ใช้ค่าเฉลี่ยรายวันคูณ 21 และไม่ต้องใช้ 252 วัน

ไฟล์ factor เก็บผลตอบแทนรายเดือนเป็นเปอร์เซ็นต์ จึงหาร 100 ก่อนจับคู่เดือนเดียวกัน ใช้ $y=R_{\mathrm{BRKA}}-R_f$ เป็นตัวแปรตาม และเพิ่มคอลัมน์หนึ่งสำหรับ intercept ทั้งสองแบบจำลองใช้ 348 เดือนเดียวกัน `Mkt-RF` หัก RF ไว้แล้ว จึงไม่หักซ้ำจากคอลัมน์นี้

| ค่าประมาณจากข้อมูล ม.ค. 1990–ธ.ค. 2018 | ตลาดตัวเดียว + intercept | FF3 + intercept |
|---|---:|---:|
| Alpha (% ต่อเดือน) | 0.606943% | 0.516540% |
| Market loading | 0.577946 | 0.709605 |
| SMB loading | — | −0.482937 |
| HML loading | — | 0.405283 |
| $R^2$ | 0.181434 | 0.317293 |

หลังเพิ่ม SMB และ HML ค่า alpha ลดลงแต่ยังเป็นบวก ค่า loading SMB ติดลบและ HML เป็นบวกสอดคล้องกับการเอียงไปทางหุ้นใหญ่และ value เมื่ออ่านผ่านแบบจำลองนี้ ทั้งสองค่าไม่ได้ระบุสัดส่วนหุ้นที่บริษัทถือจริง และ $R^2$ ไม่ใช่สัดส่วนกำไรสะสมที่มาจาก factor

ผลนี้เป็นการอธิบายใน sample เดียวกับที่ใช้ประมาณ ยังแยกไม่ได้ว่าส่วน alpha ที่เหลือเกิดจากฝีมือ ปัจจัยที่ตกหล่น การเปลี่ยน exposure หรือความบังเอิญ และไม่ได้รับรองว่า alpha จะคงอยู่ในอนาคต ค่า alpha ในตารางมีหน่วยต่อเดือน ซึ่งต่างจาก CAGR ของหุ้นตลอด 29 ปี

### คำนวณซ้ำจาก ZIP โดยไม่ต้องแก้ Notebook หลัก

ดาวน์โหลด [สคริปต์วิเคราะห์ข้อมูลคอร์ส](downloads/analyze-course-factors.py) ไว้ในเครื่องเดียวกับ ZIP แล้วเปิด Terminal ในโฟลเดอร์ที่เก็บสคริปต์ ใช้ NumPy และ pandas ตามที่ติดตั้งสำหรับ Notebook เปลี่ยน `/path/to/data.zip` ในคำสั่งเป็นตำแหน่งจริงของไฟล์ โดยใส่เครื่องหมายคำพูดเพื่อรองรับชื่อโฟลเดอร์ที่มีช่องว่าง:

```sh
python3 analyze-course-factors.py "/path/to/data.zip"
```

สคริปต์อ่าน CSV สองไฟล์ภายใน ZIP โดยไม่ต้องแตกไฟล์ คำนวณและพิมพ์ผลรวมเป็น JSON ไม่มีการดึงข้อมูลใหม่จากอินเทอร์เน็ต ข้างในใช้ `groupby` รวมวันตามเดือน, `prod` ทบต้น และ `np.linalg.lstsq` แบบเดียวกับแนวคิดในบทนี้ พร้อมตรวจเดือนซ้ำ ลำดับเวลา ข้อมูลขาดหาย และ rank

เทียบผลได้กับ [JSON ผลคำนวณที่ใช้ในตาราง](downloads/advanced-factor-results.json) ซึ่งมี SHA-256 ของ ZIP และ CSV สำหรับระบุว่าใช้ข้อมูลชุดเดียวกัน การตรวจครั้งนี้เทียบผล NumPy กับ SciPy และ statsmodels แล้ว coefficient ต่างกันไม่เกิน $3\times10^{-16}$ และตรวจผลตอบแทนรายเดือนกับอัตราส่วนราคาปรับแล้วสิ้นเดือนจาก `BRK-A.csv` เพิ่มด้วย

ผู้ที่ไม่มี ZIP ยังรันตัวอย่างสมมติและ Notebook หลักได้ครบ ไฟล์ข้อมูลดิบไม่ได้รวมอยู่ในเว็บไซต์ หากใช้ข้อมูลใหม่จาก [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) ต้องบันทึกรุ่นข้อมูลและตรวจตัวเลขใหม่ เพราะผู้จัดทำอาจปรับปรุงข้อมูลย้อนหลัง

<span id="multifactor-exercises"></span>

## ลองอ่านผล regression ด้วยตัวเอง

### 1. Loading รวมเกินหนึ่ง

ผล regression ให้ตลาด 1.1, SMB 0.8 และ HML −0.4 มีคนเสนอให้หารทุกตัวด้วย 1.5 เพื่อให้รวมหนึ่ง ควรทำหรือไม่?

เฉลย: ไม่ควรแก้ coefficient เช่นนั้น เพราะมันเป็นความไวของสมการและไม่ได้มีเงื่อนไขเป็นน้ำหนักลงทุน การหารจะเปลี่ยน fitted return โดยไม่มีเหตุผลจากการ fit ถ้าต้องการหาน้ำหนักพอร์ตต้องนิยามปัญหาพอร์ตและข้อจำกัดใหม่ให้ตรงวัตถุประสงค์

### 2. HML ติดลบทั้ง factor และ loading

เดือนหนึ่ง HML เท่ากับ −2% และ loading เท่ากับ −0.3 contribution เป็นเท่าไร?

เฉลย: $(-0.3)(-2\%)=+0.6$ จุดเปอร์เซ็นต์ ส่วนนี้ยังต้องรวม factor อื่น alpha residual และ RF เพื่อกลับเป็นผลตอบแทนรวมกองทุน

### 3. หน่วยไม่ตรงกัน

ไฟล์ factor เก็บ `2.0` โดยหมายถึง 2% แต่ผลตอบแทนกองทุนเก็บ 2% เป็น `0.02` ควรแก้ขั้นไหนก่อน fit?

เฉลย: แปลงผลตอบแทน factor เป็นทศนิยมโดยหาร 100 และตรวจ RF ด้วย ตรวจจากคู่มือข้อมูลก่อน เพราะไฟล์ที่เป็นทศนิยมอยู่แล้วจะผิดทันทีถ้าหารซ้ำ จากนั้นตรวจความถี่ วันที่ และลำดับคอลัมน์

### 4. เพิ่ม factor แล้ว R² สูงขึ้น

แบบจำลองใหม่มี $R^2$ สูงกว่าเดิมในข้อมูลที่ใช้ fit จึงรับประกันว่าพยากรณ์ดีกว่าเดิมหรือไม่?

เฉลย: OLS ใช้ตัวแปรเพิ่มเพื่อทำ SSE ให้ไม่สูงกว่าเดิมใน sample ได้อยู่แล้ว ต้องทดสอบข้อมูลภายหลังโดยกำหนด specification ไว้ก่อน และแยกการอธิบายด้วย factor ที่รู้หลังเดือนจบออกจากการพยากรณ์ต้นเดือน

### 5. เปรียบเทียบ alpha ข้ามรายงาน

รายงานแรกให้ alpha 0.3% ต่อเดือน ส่วนอีกรายงานให้ 1% ต่อปี จึงสรุปว่าแบบแรกดีกว่าได้เลยหรือไม่?

เฉลย: ต้องอ่านก่อนว่าใช้ปัจจัยใด หน่วยและวิธี annualization แบบใด ช่วงข้อมูลเดียวกันหรือไม่ หักค่าธรรมเนียมอย่างไร และความไม่แน่นอนของค่าประมาณเท่าไร แม้แปลงหน่วยตรงกันแล้ว alpha จากคนละแบบจำลองก็ยังอาจอ้างถึงความเสี่ยงที่ควบคุมต่างกัน

<span id="multifactor-sources"></span>

## แหล่งเรียนและการนำไปใช้ต่อ

อ่าน Transcript เต็มของ [Multi-Factor models and Fama-French](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/iVahP/multi-factor-models-and-fama-french) และ [Factor models and the CAPM](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/19WkH/factor-models-and-the-capm) เมื่อ 2 ตุลาคม 2026 ใช้เป็นโครงหัวข้อการขยายปัจจัยและอ่านความไว คำอธิบายไทย ชุดข้อมูลสมมติ โค้ด และโจทย์ในหน้านี้เขียนขึ้นใหม่

ตรวจนิยามการสร้าง factor กับ [Kenneth French: Fama/French 3 Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html) และ [Fama/French 5 Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html) และรูปแบบผลลัพธ์ OLS กับ [NumPy: linalg.lstsq](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) คำอธิบาย size/value ในวิดีโอเป็นแรงจูงใจของแบบจำลอง ไม่ถูกใช้เป็นคำรับประกันว่าหุ้นกลุ่มใดจะชนะต่อจากวันนี้

ขั้นถัดไปคือ[การวิเคราะห์ style ของกองทุน](style-analysis.html) ซึ่งต้องกำหนดให้ชัดก่อนว่า coefficient ที่กำลังหาเป็นความไวแบบ unconstrained regression หรือเป็นส่วนผสมของพอร์ตอ้างอิงภายใต้ข้อจำกัดที่เลือก
