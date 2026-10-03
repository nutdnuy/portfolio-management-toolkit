---
title: Smart Beta — เลือกหุ้น ให้น้ำหนัก และตรวจต้นทุน
description: เริ่มจาก Cap Weight และ Equal Weight วัดการกระจุกตัว คำนวณการปรับพอร์ตและค่าธรรมเนียม แล้วทดสอบกฎลงทุนแบบ Rolling ด้วย Python
---

# Smart Beta: เลือกหุ้นและกำหนดน้ำหนัก

<p class="lead">ถ้ามีหุ้นชุดเดียวกันสี่ตัว การแบ่งเงินเท่ากันกับการให้น้ำหนักตามมูลค่าตลาดจะทำให้พอร์ตต่างกันอย่างไร?</p>

หุ้นที่ซื้อเป็นเพียงส่วนหนึ่งของการตัดสินใจลงทุน จำนวนเงินที่จัดให้แต่ละตัวกำหนดว่าบริษัทใดมีผลต่อพอร์ตมากที่สุด และเมื่อราคาเปลี่ยน กฎที่เลือกยังเป็นตัวกำหนดว่าจะต้องซื้อขายอีกเท่าไร

บทนี้อยู่ในหัวข้อ Style & Factors ต่อจาก [การอ่านสไตล์จากผลตอบแทน](style-analysis.html) เราจะสร้างน้ำหนักจากตารางหุ้นสมมติ วัดความกระจุกตัว แล้วเขียนการทดสอบที่ใช้ข้อมูลย้อนหลัง 60 เดือนเพื่อตัดสินใจลงทุนในเดือนถัดไป คำว่า [smart beta](glossary.html#smart-beta) ในที่นี้หมายถึงกฎสร้างพอร์ตที่ปรับวิธีเลือกหุ้นหรือให้น้ำหนักจากดัชนีตามมูลค่าตลาด เพื่อให้ได้ลักษณะพอร์ตที่ต้องการ เช่น รับปัจจัย value หรือกระจายน้ำหนักมากขึ้น ชื่อนี้ไม่ได้ระบุสูตรเดียวที่ทุกดัชนีใช้ร่วมกัน

ข้อมูลหุ้น ราคา ผลตอบแทน และผลการทดสอบทั้งหมดในหน้านี้เป็นตัวอย่างสมมติ โค้ดใช้ NumPy, pandas และ SciPy เปิด Notebook ใหม่แล้วรันทุกช่องจากบนลงล่างได้ ไม่ต้องใช้ไฟล์ข้อมูลของคอร์ส หากยังไม่คุ้นกับน้ำหนักพอร์ตและ covariance ให้เริ่มจาก [การคำนวณผลตอบแทนและความเสี่ยงพอร์ต](portfolio-basics.html)

[ดาวน์โหลด Notebook ของบทนี้](notebooks/smart-beta.ipynb) เพื่อรันตัวอย่างและเทียบผลที่บันทึกไว้

| ช่วงเรียน | สิ่งที่จะคำนวณ |
|---|---|
| [มูลค่าตลาดและน้ำหนัก](#cap-and-equal-weights) | Cap Weight กับ Equal Weight จากหุ้นชุดเดียวกัน |
| [ความกระจุกตัว](#concentration-and-risk) | HHI และเหตุที่เงินเท่ากันยังรับความเสี่ยงไม่เท่ากัน |
| [ราคาเปลี่ยนและการซื้อขาย](#weight-drift) | น้ำหนักหลังผลตอบแทน ก่อนตัดสินใจปรับพอร์ต |
| [ต้นทุน](#turnover-and-cost) | One-way turnover กับค่าธรรมเนียมทั้งซื้อและขาย |
| [เลือกหุ้นก่อนให้น้ำหนัก](#selection-and-weighting) | Value signal และการลงทุนซ้อนสองชั้น |
| [ข้อจำกัดน้ำหนัก](#cap-linked-limits) | จำกัดน้ำหนักโดยตรวจว่าเงื่อนไขยังครบหลังคำนวณ |
| [ทดสอบตามเวลา](#rolling-backtest) | Train 60 เดือน ถือเดือนถัดไป แล้วเลื่อนหน้าต่าง |

<span id="cap-and-equal-weights"></span>

## จากราคาหุ้นเป็นน้ำหนักพอร์ต

มูลค่าตลาดของหุ้น หรือ market capitalization คือราคาต่อหุ้นคูณจำนวนหุ้นที่ใช้อ้างอิง ให้ $P_i$ เป็นราคาหุ้นบริษัท $i$ และ $Q_i$ เป็นจำนวนหุ้น จะได้

$$
M_i=P_iQ_i,\qquad
w_i^{\mathrm{CW}}=\frac{M_i}{\sum_j M_j}.
$$

$M_i$ คือมูลค่าตลาด และ $w_i^{\mathrm{CW}}$ คือน้ำหนักแบบ capitalization weighted หรือ CW ตัวห้อย $j$ วิ่งผ่านหุ้นทุกตัวที่อยู่ในชุดลงทุน ถ้าบริษัทหนึ่งคิดเป็นครึ่งหนึ่งของมูลค่าตลาดรวม พอร์ต CW ก็ลงเงินครึ่งหนึ่งในบริษัทนั้น

Equal Weight หรือ EW แบ่งเงินเท่ากันในหุ้น $N$ ตัว:

$$
w_i^{\mathrm{EW}}=\frac{1}{N}.
$$

สำหรับหุ้นสี่ตัว EW จึงให้ตัวละ 25% การแบ่งเงินเท่ากันอาจทำให้ถือจำนวนหุ้นต่างกัน เพราะราคาต่อหุ้นไม่จำเป็นต้องเท่ากัน

ตัวอย่างกำหนดราคาหน่วยบาท และจำนวนหุ้นหน่วยล้านหุ้น ดังนั้นผลคูณมีหน่วยล้านบาท สมมติว่าหุ้นทุกหุ้นใช้ลงทุนได้ ไม่มีการปรับ free float ซึ่งหมายถึงสัดส่วนหุ้นที่หมุนเวียนให้ผู้ลงทุนทั่วไปซื้อขายได้ ดัชนีจริงอาจใช้จำนวนหุ้นที่ปรับ free float และมีกฎจัดการ corporate actions เพิ่มเติม ดูหลักการได้ใน [S&P DJI Index Mathematics Methodology](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-index-math.pdf)

```python
import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize

stocks = pd.DataFrame({
    "Price": [50.0, 25.0, 30.0, 20.0],
    "Shares_million": [10.0, 10.0, 5.0, 5.0],
    "Book_equity_million": [400.0, 75.0, 90.0, 50.0],
    "Industry": ["X", "X", "X", "Y"]
}, index=["A", "B", "C", "D"])
stocks["Market_cap_million"] = stocks["Price"] * stocks["Shares_million"]
cw = stocks["Market_cap_million"] / stocks["Market_cap_million"].sum()
ew = pd.Series(1 / len(stocks), index=stocks.index)
print(pd.DataFrame({"Cap": stocks["Market_cap_million"], "CW": cw, "EW": ew}))
```

ตารางผลลัพธ์เป็นดังนี้:

| หุ้น | มูลค่าตลาด (ล้านบาท) | CW | EW |
|---|---:|---:|---:|
| A | 500 | 50% | 25% |
| B | 250 | 25% | 25% |
| C | 150 | 15% | 25% |
| D | 100 | 10% | 25% |

`pd.DataFrame` สร้างตารางที่มีชื่อหุ้นเป็น `index` แต่ละคอลัมน์เก็บข้อมูลชนิดหนึ่ง ส่วน `stocks["Price"] * stocks["Shares_million"]` คูณข้อมูลของหุ้นชื่อเดียวกัน ผลรวมมูลค่าตลาดเท่ากับ 1,000 ล้านบาท จึงหารแต่ละแถวด้วย 1,000 เพื่อหาน้ำหนัก CW

`len(stocks)` นับจำนวนแถวได้ 4 และ `pd.Series(1 / len(stocks), index=stocks.index)` สร้างน้ำหนัก 0.25 ให้ชื่อหุ้นทั้งสี่ตัว น้ำหนักใช้เลขทศนิยม เช่น 0.50 หมายถึง 50% ส่วนคอลัมน์มูลค่าทางบัญชีและอุตสาหกรรมจะใช้ในตัวอย่างถัดไป

ถ้าลงทุน 100,000 บาท CW จัดให้ A จำนวน 50,000 บาท ส่วน EW จัดให้ A จำนวน 25,000 บาท พอร์ต CW มีเหตุผลในฐานะตัวแทนสัดส่วนมูลค่าตลาดของหุ้นชุดนี้ แต่สูตรยังไม่ได้รับข้อมูล expected return หรือ covariance จึงไม่ได้แก้โจทย์หาพอร์ตบน [Efficient Frontier](efficient-frontier.html) ด้วยตัวมันเอง

ใน [Shortcomings of cap-weighted indices](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/Pc4Np/shortcomings-of-cap-weighted-indices) ผู้สอนใช้กราฟย้อนหลังเพื่ออภิปรายข้อจำกัดนี้ และระบุว่าการสร้าง frontier จากข้อมูลทั้งช่วงมี look-ahead bias การรู้ภายหลังว่าพอร์ตใดทำได้ดีกว่าในช่วงหนึ่ง ยังไม่บอกว่าเราจะเลือกพอร์ตนั้นได้ด้วยข้อมูลที่มีอยู่ก่อนลงทุน

<span id="concentration-and-risk"></span>

## วัดการกระจุกตัวของเงิน และอ่านความเสี่ยงแยกกัน

CW ในตัวอย่างให้ A และ B รวมกัน 75% ของเงินทั้งหมด เราวัดการกระจุกตัวของน้ำหนักด้วย Herfindahl–Hirschman Index หรือ HHI ได้จากผลรวมของน้ำหนักยกกำลังสอง:

$$
\mathrm{HHI}=\sum_{i=1}^{N}w_i^2,
\qquad
N_{\mathrm{eff}}=\frac{1}{\mathrm{HHI}}.
$$

$N_{\mathrm{eff}}$ เรียกว่า effective number of constituents ในความหมายของน้ำหนัก สำหรับพอร์ต long-only ที่น้ำหนักรวมหนึ่ง ค่านี้อยู่ระหว่าง 1 กับ $N$ ถ้าลงทุนตัวเดียวจะได้ 1 ถ้าแบ่งเงินเท่ากัน $N$ ตัวจะได้ $N$ สูตรช่วยเทียบว่าพอร์ตที่น้ำหนักไม่เท่ากันกระจุกตัวเพียงใด โดยเทียบกับพอร์ตน้ำหนักเท่ากัน

CW ของเรามี $\mathrm{HHI}=0.50^2+0.25^2+0.15^2+0.10^2=0.345$ จึงได้ $N_{\mathrm{eff}}\approx2.90$ แม้ถือหุ้นจริง 4 ตัว ส่วน EW มี $\mathrm{HHI}=4(0.25^2)=0.25$ และ $N_{\mathrm{eff}}=4$

สูตร HHI ไม่มี covariance อยู่ในนั้น หากหุ้นทั้งสี่ขึ้นลงพร้อมกันมาก ค่า 4 ก็ยังคงเดิม จำนวนเชิงประสิทธิผลนี้จึงวัดการกระจายน้ำหนัก ไม่ได้วัดจำนวนความเสี่ยงที่เป็นอิสระต่อกัน

ลองเพิ่มแบบจำลองความเสี่ยงเพื่อเปรียบเทียบ กำหนด SD ต่อปีของ A/B/C/D เป็น 10%, 20%, 30%, 40% และสมมติว่าไม่สัมพันธ์กัน สูตรสัดส่วน contribution ต่อ variance พอร์ตคือ

$$
s_i=\frac{w_i(\Sigma w)_i}{w^\mathsf{T}\Sigma w}.
$$

$\Sigma$ คือ covariance matrix และ $(\Sigma w)_i$ คือสมาชิกตำแหน่ง $i$ ของผลคูณ $\Sigma w$ ค่า $s_i$ รวมกันได้หนึ่ง สูตรเดียวกันนี้เป็นสัดส่วน contribution ต่อ SD ภายใต้การแยก contribution แบบ Euler ด้วย แต่บางโครงสร้าง covariance อาจมี contribution ติดลบได้ ตัวอย่างนี้ใช้ covariance แนวทแยงเพื่อให้เห็นความต่างจากการแบ่งเงินเท่ากันโดยตรง

```python
concentration = pd.DataFrame({
    name: {"HHI": float((w**2).sum()), "Effective N": float(1 / (w**2).sum())}
    for name, w in {"CW": cw, "EW": ew}.items()
}).T
annual_sd = np.array([0.10, 0.20, 0.30, 0.40])
independent_cov = np.diag(annual_sd**2)
equal_w = ew.to_numpy()
risk_share = equal_w * (independent_cov @ equal_w) / (equal_w @ independent_cov @ equal_w)
print(concentration.round(6))
print("EW risk contribution shares (%):", np.round(risk_share * 100, 4))
```

ได้ HHI ของ CW/EW เท่ากับ 0.345/0.250 และ $N_{\mathrm{eff}}$ เท่ากับ 2.898551/4.000000 ตามที่คำนวณไว้ ส่วนสัดส่วน risk contribution ของ EW เป็นดังนี้:

| หุ้น | เงินที่จัดให้ | สัดส่วน risk contribution |
|---|---:|---:|
| A | 25% | 3.3333% |
| B | 25% | 13.3333% |
| C | 25% | 30.0000% |
| D | 25% | 53.3333% |

`np.diag(annual_sd**2)` สร้าง covariance ที่มี variance อยู่บนแนวทแยงและศูนย์นอกแนวทแยง `@` คูณเวกเตอร์หรือเมทริกซ์ ส่วน `**2` คือยกกำลังสอง ในตัวอย่างนี้ D มี SD มากกว่า A สี่เท่า จึงมี variance สิบหกเท่า เมื่อลงเงินเท่ากัน D จึงสร้าง contribution มากกว่าด้วย

Risk parity แบบ equal risk contribution ตั้งเป้าให้แต่ละสินทรัพย์มี contribution เท่ากัน จึงต้องใช้ข้อมูลความเสี่ยงประกอบการหาน้ำหนัก EW ตั้งเป้าเงินเท่ากัน ตัวอย่างข้างบนทำให้เห็นว่ากฎทั้งสองให้ผลต่างกันได้ ส่วน minimum variance ลด variance รวมภายใต้ข้อจำกัด ซึ่งก็เป็นอีกโจทย์หนึ่ง

<span id="weight-drift"></span>

## น้ำหนักเปลี่ยนได้แม้ยังไม่ได้ซื้อขาย

สมมติผลตอบแทนหนึ่งงวดของ A/B/C/D เป็น +20%, 0%, −10%, +10% ไม่มีเงินปันผล การเพิ่มทุน หุ้นแตกพาร์ การเปลี่ยนสมาชิก หรือเงินเข้าออก ในตัวอย่างนี้ผลตอบแทนราคาจึงเท่ากับ total return

เมื่อมีน้ำหนักต้นงวด $w_i$ และผลตอบแทน $R_i$ เงินของแต่ละตัวโตด้วยตัวคูณ $1+R_i$ ผลตอบแทนพอร์ตเป็น $R_p=\sum_iw_iR_i$ น้ำหนักปลายงวดก่อนซื้อขายจึงเป็น

$$
\widetilde w_i=\frac{w_i(1+R_i)}{1+R_p}.
$$

เครื่องหมาย $\widetilde{\phantom{w}}$ บน $w$ ใช้แยกน้ำหนักที่ปล่อยให้เปลี่ยนตามราคา ออกจากน้ำหนักเป้าหมายที่จะปรับกลับไป

```python
one_period_r = pd.Series([0.20, 0.00, -0.10, 0.10], index=stocks.index)
cw_return = float(cw @ one_period_r)
ew_return = float(ew @ one_period_r)
cw_drift = cw * (1 + one_period_r) / (1 + cw_return)
ew_drift = ew * (1 + one_period_r) / (1 + ew_return)
new_caps = stocks["Market_cap_million"] * (1 + one_period_r)
cw_from_new_caps = new_caps / new_caps.sum()
assert np.allclose(cw_drift, cw_from_new_caps)
print("CW return, EW return:", cw_return, ew_return)
print(pd.DataFrame({"CW after drift": cw_drift, "EW after drift": ew_drift}).round(6))
```

พอร์ต CW ได้ผลตอบแทน 9.5% และ EW ได้ 5.0% น้ำหนักปลายงวดเป็นดังนี้:

| หุ้น | CW หลังราคาเปลี่ยน | EW หลังราคาเปลี่ยน |
|---|---:|---:|
| A | 54.7945% | 28.5714% |
| B | 22.8311% | 23.8095% |
| C | 12.3288% | 21.4286% |
| D | 10.0457% | 26.1905% |

`cw @ one_period_r` คำนวณผลรวมของน้ำหนักคูณผลตอบแทน ส่วน `np.allclose` ตรวจว่าตัวเลขสองชุดเท่ากันภายในความคลาดเคลื่อนเล็กน้อยของ floating point การใช้ `assert` ทำให้โค้ดหยุดหากเงื่อนไขไม่เป็นจริง

CW ปลายงวดตรงกับน้ำหนักที่คำนวณจากมูลค่าตลาดใหม่ เพราะทั้งมูลค่าหุ้นที่เราถือและมูลค่าตลาดบริษัทโตด้วยอัตราเดียวกัน ถ้าคงชุดหุ้นและจำนวนหุ้นอ้างอิงไว้ การตาม CW ใหม่จึงไม่ต้องซื้อ A เพิ่มเพียงเพราะราคาของ A ขึ้น น้ำหนักเพิ่มขึ้นเองขณะที่ยังถือจำนวนหุ้นเท่าเดิม

EW จะกลับไปตัวละ 25% ได้ด้วยการขายส่วนที่เกินเป้าหมาย และซื้อส่วนที่ต่ำกว่าเป้าหมาย กฎ EW จึงต้องระบุด้วยว่าจะ [rebalance](glossary.html#rebalancing) เมื่อใด เช่น สิ้นเดือนหรือสิ้นไตรมาส ระหว่างวันปรับพอร์ต น้ำหนักย่อมเคลื่อนออกจาก 25% ได้ หลักการเรื่องการเปลี่ยนน้ำหนักและรอบปรับพอร์ตอยู่ใน [วิธีคำนวณดัชนีของ S&P DJI](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-index-math.pdf)

สำหรับดัชนีจริง จำนวนหุ้นอ้างอิง free float สมาชิกดัชนี และเงินสดจาก corporate actions อาจเปลี่ยน การตาม CW ในกรณีเหล่านั้นยังเกิดการซื้อขายได้ จึงไม่ควรขยายผลจากตัวอย่างราคาเปลี่ยนอย่างเดียวไปเป็นข้อสรุปว่า CW ไม่มีต้นทุนทุกกรณี

<span id="turnover-and-cost"></span>

## นับทั้งเงินที่ซื้อ เงินที่ขาย และค่าธรรมเนียม

ก่อนปรับ EW กลับไปตัวละ 25% พอร์ตที่เริ่มด้วย 100,000 บาทมีมูลค่า 105,000 บาท แยกเป็น A/B/C/D จำนวน 30,000, 25,000, 22,500, 27,500 บาท หากยังไม่คิดค่าธรรมเนียม เป้าหมายตัวละ 26,250 บาทต้องขาย A 3,750 บาทและ D 1,250 บาท แล้วซื้อ B 1,250 บาทและ C 3,750 บาท

ยอดขาย 5,000 บาทและยอดซื้อ 5,000 บาท รวมการซื้อขายสองด้าน 10,000 บาท เราใช้ [turnover](glossary.html#turnover) แบบ one-way ซึ่งนับครึ่งหนึ่งของผลรวมการเปลี่ยนน้ำหนัก:

$$
T_{\mathrm{one\text{-}way}}
=\frac12\sum_i\left|w_i^{\mathrm{target}}-\widetilde w_i\right|
=\frac{5{,}000}{105{,}000}\approx4.7619\%.
$$

เมื่อทั้งน้ำหนักเดิมและเป้าหมายรวมหนึ่ง การหารสองช่วยไม่ให้นับเงินที่ขายไปแล้วนำมาซื้อซ้ำเป็นสองรอบ วิธีรายงานนี้สอดคล้องกับนิยาม one-way turnover ใน [S&P DJI Index Mathematics Methodology](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-index-math.pdf) แต่ต้องอ่านฐานคิดค่าธรรมเนียมแยกจากชื่อ turnover เสมอ

ถ้าค่าธรรมเนียมเป็น $c=0.001$ หรือ 0.1% ของมูลค่าที่ซื้อและของมูลค่าที่ขาย ค่าธรรมเนียมโดยประมาณคือ $2cTV$ โดย $V$ คือมูลค่าก่อนปรับพอร์ต ตัวอย่างนี้ได้ $0.001\times10{,}000=10$ บาท

การหักค่าธรรมเนียมทำให้เงินที่เหลือจัดพอร์ตลดลงด้วย หากต้องการน้ำหนักหลังจ่ายค่าธรรมเนียมเท่ากับเป้าหมายพอดี ให้ $H_i$ เป็นมูลค่าที่ถือก่อนซื้อขาย และ $V'$ เป็นเงินรวมหลังจ่ายค่าธรรมเนียม เราแก้สมการ

$$
V'+c\sum_i\left|w_i^{\mathrm{target}}V'-H_i\right|=V.
$$

พจน์ผลรวมคือมูลค่าซื้อขายจริง ส่วนเงินที่เหลือรวมค่าธรรมเนียมต้องเท่ากับเงินก่อนซื้อขาย สมการนี้ใช้ค่าธรรมเนียมสัดส่วนเดียวกันทั้งสองด้าน ไม่มีขั้นต่ำ ไม่มีภาษีหรือ market impact

```python
def rebalance_with_fee(holdings, target, fee_rate):
    holdings = np.asarray(holdings, dtype=float)
    target = np.asarray(target, dtype=float)
    if not 0 <= fee_rate < 1:
        raise ValueError("fee_rate must be in [0, 1)")
    if (target < 0).any() or not np.isclose(target.sum(), 1):
        raise ValueError("target must be long-only and sum to one")
    wealth_before = holdings.sum()
    if wealth_before <= 0 or (holdings < 0).any():
        raise ValueError("positive wealth and nonnegative holdings required")
    wealth_after = brentq(
        lambda v: v + fee_rate * np.abs(target * v - holdings).sum() - wealth_before,
        0.0, wealth_before
    )
    new_holdings = target * wealth_after
    fee = fee_rate * np.abs(new_holdings - holdings).sum()
    return new_holdings, fee

starting_wealth = 100_000.0
holdings_before_trade = starting_wealth * ew.to_numpy() * (1 + one_period_r.to_numpy())
one_way_turnover = float(np.abs(ew - ew_drift).sum() / 2)
rebalanced_holdings, rebalance_fee = rebalance_with_fee(holdings_before_trade, ew, 0.001)
print("One-way turnover (%):", round(100 * one_way_turnover, 6))
print("Wealth before trade:", holdings_before_trade.sum())
print("Fee:", round(rebalance_fee, 6))
print("Wealth after trade:", round(rebalanced_holdings.sum(), 6))
print("Gross / net return (%):", round(100 * ew_return, 6), round(100 * (rebalanced_holdings.sum() / starting_wealth - 1), 6))
```

ผลลัพธ์ได้ one-way turnover 4.761905%, ค่าธรรมเนียม 10 บาท และมูลค่าหลังปรับพอร์ต 104,990 บาท ผลตอบแทนของงวดรวมการปรับพอร์ตตอนท้ายจึงลดจาก 5.00% เป็น 4.99%

`def` ประกาศฟังก์ชัน `rebalance_with_fee` เพื่อใช้ซ้ำ ฟังก์ชันรับมูลค่าที่ถือแต่ละตัว น้ำหนักเป้าหมาย และอัตราค่าธรรมเนียม จากนั้นคืนมูลค่าที่ถือใหม่พร้อมค่าธรรมเนียม `np.abs` หาค่าสัมบูรณ์จึงนับทั้งการซื้อและขายเป็นจำนวนบวก ส่วน `brentq` ของ SciPy หาค่า $V'$ ที่ทำให้สมการเท่ากับศูนย์ในช่วง 0 ถึงเงินก่อนซื้อขาย

หลังจ่ายค่าธรรมเนียม หุ้นแต่ละตัวมีมูลค่า 26,247.50 บาท ยอดซื้อจริงรวม 4,995 บาทและยอดขายรวม 5,005 บาท ส่วนต่าง 10 บาทนำไปจ่ายค่าธรรมเนียม โค้ดจึงไม่ต้องสมมติว่ามีเงินเติมจากภายนอก

อัตรา 0.1% เป็นค่าที่ตั้งขึ้นเพื่อฝึกคำนวณ ต้นทุนจริงยังมี bid–ask spread ผลของคำสั่งซื้อขายต่อราคา ภาษี และค่าบริหารกองทุน ขนาดคำสั่งที่มากเมื่อเทียบกับปริมาณซื้อขายอาจทำให้ต้นทุนไม่เป็นสัดส่วนคงที่ตามสูตรนี้

<span id="selection-and-weighting"></span>

## เลือกหุ้นรับปัจจัยใด แล้วจึงเลือกวิธีแบ่งเงิน

การออกแบบพอร์ตมีสองคำตอบที่ต้องระบุให้ครบ คำตอบแรกคือหุ้นใดผ่านเกณฑ์ คำตอบที่สองคือหุ้นที่ผ่านเกณฑ์ได้รับเงินเท่าไร บท [From cap-weighted benchmarks to smart-weighted benchmarks](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/2uJdC/from-cap-weighted-benchmarks-to-smart-weighted-benchmarks) ใช้การแยกสองขั้นนี้อธิบายการสร้างพอร์ตที่รับ factor exposure

ตัวอย่าง value ใช้อัตราส่วนมูลค่าทางบัญชีของส่วนผู้ถือหุ้นต่อมูลค่าตลาด หรือ book-to-market:

$$
\mathrm{B/M}_i=\frac{\text{Book equity}_i}{\text{Market equity}_i}.
$$

เราใช้มูลค่ารวมบริษัททั้งเศษและส่วนในหน่วยล้านบาทเดียวกัน อัตราส่วนจึงไม่มีหน่วย ค่า B/M สูงหมายถึงมีมูลค่าทางบัญชีมากเมื่อเทียบกับราคาที่ตลาดให้ ภายใต้นิยามนี้จึงเป็นลักษณะ value แต่ไม่ได้รับรองว่าราคาต่ำกว่ามูลค่าที่เหมาะสม หรือว่าธุรกิจจะฟื้นตัว

สมมติว่าตัวเลข book equity ของตารางประกาศแล้วก่อนวันตัดสินใจ และยังไม่มีการแก้ไขย้อนหลังในข้อมูล เลือกสองตัวที่ B/M สูงที่สุด แล้วเปรียบเทียบการให้น้ำหนักสองวิธีในรายชื่อเดียวกัน

```python
book_to_market = stocks["Book_equity_million"] / stocks["Market_cap_million"]
selected_names = book_to_market.nlargest(2).index
value_cw = pd.Series(0.0, index=stocks.index)
value_ew = pd.Series(0.0, index=stocks.index)
selected_caps = stocks.loc[selected_names, "Market_cap_million"]
value_cw.loc[selected_names] = selected_caps / selected_caps.sum()
value_ew.loc[selected_names] = 1 / len(selected_names)
print(pd.DataFrame({"Book / market": book_to_market, "Selected CW": value_cw, "Selected EW": value_ew}).round(6))
```

| หุ้น | B/M | CW เฉพาะหุ้นที่เลือก | EW เฉพาะหุ้นที่เลือก |
|---|---:|---:|---:|
| A | 0.80 | 76.9231% | 50% |
| B | 0.30 | 0% | 0% |
| C | 0.60 | 23.0769% | 50% |
| D | 0.50 | 0% | 0% |

`nlargest(2)` เลือกชื่อหุ้นที่อัตราส่วนสูงที่สุดสองตัว `loc[selected_names]` เข้าถึงแถวตามชื่อที่เลือก พอร์ต CW ภายในชุด A/C ใช้มูลค่าตลาดรวม 650 ล้านบาทเป็นตัวหารใหม่ จึงให้น้ำหนัก A เท่ากับ $500/650$ ส่วน EW แบ่งครึ่งให้ทั้งสองตัว

A เป็นบริษัทใหญ่ที่สุดในชุด และมี B/M สูงที่สุดด้วย ขนาดบริษัทวัดจากมูลค่าตลาด ส่วน value/growth ใช้ข้อมูลเกี่ยวกับราคาสัมพัทธ์และการเติบโต จึงเป็นคนละคุณลักษณะ ตัวอย่างเช่น [MSCI Value and Growth Indexes](https://www.msci.com/indexes/group/value-and-growth-indexes) ระบุหลายตัวแปรในการจัดกลุ่ม รวมทั้ง book-to-price สำหรับ value และอัตราการเติบโตของกำไรสำหรับ growth การเรียกหุ้นใหญ่ทุกตัวว่า growth จึงทำให้สับสนระหว่าง size กับ style

เกณฑ์เลือกหุ้นอาจเปลี่ยนเป็น momentum หรือ volatility ที่ประมาณจากอดีตได้ แต่ต้องระบุช่วงข้อมูล ความถี่ และวิธีจัดการข้อมูลที่ยังไม่ประกาศ ส่วนแนวคิด low-volatility anomaly เป็นข้อสังเกตจากงานศึกษาหรือข้อมูลภายใต้นิยามที่ใช้ ไม่ใช่ข้อสรุปของ CAPM ว่าหุ้นที่ SD ต่ำต้องให้ผลตอบแทนสูงกว่า หุ้นที่ SD ต่ำยังอาจมี market beta หรือความเสี่ยงด้านอื่นที่ต้องตรวจเพิ่ม

แม้คัดหุ้นตาม factor แล้ว น้ำหนักสุดท้ายยังเปลี่ยน exposure ได้ เช่น A มีสัดส่วนต่างกัน 26.9231 จุดเปอร์เซ็นต์ระหว่างสองพอร์ตในตาราง และการเลือกเพียงสองหุ้นทำให้จำนวนชื่อที่ถือเหลือน้อยลง เราจึงต้องดูทั้ง factor exposure ความกระจุกตัว และต้นทุนของกฎนั้นร่วมกัน

<span id="industry-weighting"></span>

## น้ำหนักเท่ากันในอุตสาหกรรม กับน้ำหนักเท่ากันข้ามอุตสาหกรรม

ใน Foundations Lab ผู้สอนใช้ข้อมูลผลตอบแทนของพอร์ตอุตสาหกรรม แต่ละคอลัมน์จึงอาจมีหุ้นหลายตัวอยู่ข้างใน การถัวเฉลี่ยคอลัมน์ให้เท่ากันเป็นการแบ่งเงินเท่ากันระหว่างอุตสาหกรรม ส่วนกฎที่ใช้แบ่งเงินภายในแต่ละอุตสาหกรรมเป็นอีกชั้นหนึ่ง

ให้ A/B/C อยู่ในอุตสาหกรรม X และ D อยู่ในอุตสาหกรรม Y ถ้าให้ X และ Y กลุ่มละ 50% แล้วภายในแต่ละกลุ่มแบ่งเงินเท่ากัน A/B/C จะได้ตัวละ $50\%/3=16.6667\%$ ส่วน D ได้ 50% ของพอร์ต เพราะเป็นหุ้นตัวเดียวใน Y

```python
industry = stocks["Industry"]
n_industries = industry.nunique()
stocks_per_industry = industry.map(industry.value_counts())
industry_caps = stocks.groupby("Industry")["Market_cap_million"].transform("sum")
within_ew_across_ew = (1 / n_industries) / stocks_per_industry
within_cw_across_ew = (1 / n_industries) * stocks["Market_cap_million"] / industry_caps
print(pd.DataFrame({
    "EW all stocks": ew,
    "Within EW, across EW": within_ew_across_ew,
    "Within CW, across EW": within_cw_across_ew
}).round(6))
```

| หุ้น | EW หุ้นทั้งหมด | ภายในกลุ่ม EW / ข้ามกลุ่ม EW | ภายในกลุ่ม CW / ข้ามกลุ่ม EW |
|---|---:|---:|---:|
| A | 25% | 16.6667% | 27.7778% |
| B | 25% | 16.6667% | 13.8889% |
| C | 25% | 16.6667% | 8.3333% |
| D | 25% | 50.0000% | 50.0000% |

`nunique()` นับกลุ่มที่ชื่อไม่ซ้ำ `value_counts()` นับจำนวนหุ้นแต่ละกลุ่ม ส่วน `groupby("Industry")...transform("sum")` หามูลค่าตลาดรวมของกลุ่ม แล้วนำผลรวมของกลุ่มนั้นกลับมาใส่ทุกแถวที่เป็นสมาชิก ตัวอย่างเช่น A/B/C ทุกแถวได้ผลรวมกลุ่ม X เท่ากับ 900 ล้านบาท

น้ำหนักสุดท้ายของหุ้นคำนวณจากน้ำหนักกลุ่มคูณน้ำหนักภายในกลุ่ม จึงต้องอ่านคำอธิบายข้อมูลให้รู้ว่า return series แต่ละคอลัมน์เป็นหุ้น กองทุน หรือพอร์ตอุตสาหกรรม คำว่า value-weighted หรือ VW ในชุดผลตอบแทนลักษณะนี้มักใช้หมายถึงน้ำหนักตามมูลค่าตลาด ไม่ได้หมายถึงคัดหุ้นด้วย value factor

ผู้สอนระบุใน [Lab Session – Foundations](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/ZdgGw/module-1-lab-session-foundations) ว่าตัวอย่างพอร์ต 49 อุตสาหกรรมของเขาไม่ได้แสดง Sharpe ratio ของ EW ที่ดีกว่า CW ในช่วงนั้น การเปลี่ยนชนิดข้อมูล ระดับที่ให้น้ำหนัก หรือช่วงทดสอบจึงอาจให้ผลต่างจากอีกตัวอย่างในบทเดียวกันได้

<span id="cap-linked-limits"></span>

## จำกัดน้ำหนักเทียบกับ CW โดยไม่ทำให้เพดานหายหลังหารปรับสัดส่วน

EW อาจทำให้พอร์ตขนาดใหญ่ต้องถือหุ้นของบริษัทเล็กมากเมื่อเทียบกับมูลค่าบริษัท แนวทางหนึ่งคือกำหนดเกณฑ์คัดชื่อที่เล็กเกินไปออก และตั้งเพดานน้ำหนักเป็นจำนวนเท่าของ CW ผู้สอนเรียกแนวคิดนี้ว่า cap-weight tethering ใน Foundations Lab พร้อมระบุว่าเป็นคำที่เขาตั้งใช้ในบทนั้น เราจะระบุเงื่อนไขเป็นตัวเลขแทนการถือว่าชื่อนี้มีสูตรมาตรฐาน

ใช้หุ้นเดิมเพื่อให้คำนวณมือได้ กำหนดเกณฑ์สมมติสองข้อ:

1. หุ้นที่ CW ต่ำกว่า 12% ไม่ผ่านเกณฑ์ จึงตัด D ออก
2. หุ้นที่เหลือมีน้ำหนักไม่เกิน 1.5 เท่าของ CW เดิมก่อนตัดชื่อ

เพดาน A/B/C/D จึงเป็น 75%, 37.5%, 22.5%, 0% ถ้าต้องการ EW ของหุ้นที่ผ่านเกณฑ์ เป้าหมายเริ่มต้นจะเป็นตัวละ $1/3$ สำหรับ A/B/C

การตัดค่าที่เกินเพดานแล้วหารให้รวมหนึ่งอีกครั้งอาจพาค่าที่เพิ่งตัดกลับไปเกินเพดาน ตัวอย่างนี้ตัด C ลงเหลือ 22.5% แล้วผลรวมน้ำหนักเหลือประมาณ 89.1667% เมื่อหารทุกตัวด้วยผลรวมดังกล่าว C จะกลายเป็นประมาณ 25.2336% ซึ่งเกิน 22.5% อีกครั้ง

เราจึงหาเวกเตอร์ที่ใกล้เป้าหมาย EW โดยคงข้อจำกัดไว้ตลอดการคำนวณ:

$$
\underset{w}{\operatorname{minimize}}\quad
\frac12\sum_i(w_i-w_i^{\mathrm{target}})^2
\quad\text{subject to}\quad
\sum_iw_i=1,\quad0\leq w_i\leq u_i.
$$

$u_i$ คือเพดานของหุ้น $i$ โจทย์นี้หาน้ำหนักที่ใกล้ EW ในแง่ระยะทางกำลังสอง โดยยังไม่ได้ใช้ covariance หรือคาดการณ์ผลตอบแทน จึงไม่ได้อ้างว่าคำตอบมี variance หรือ tracking error ต่ำที่สุด

```python
eligible = cw.to_numpy() >= 0.12
upper = np.where(eligible, np.minimum(1.0, 1.5 * cw.to_numpy()), 0.0)
target_eligible_ew = eligible.astype(float) / eligible.sum()
naive_clipped = np.minimum(target_eligible_ew, upper)
naive_renormalized = naive_clipped / naive_clipped.sum()
if upper.sum() < 1 - 1e-12:
    raise ValueError("Caps cannot support a fully invested portfolio")
projection = minimize(
    lambda w: 0.5 * np.sum((w - target_eligible_ew)**2),
    x0=upper / upper.sum(),
    jac=lambda w: w - target_eligible_ew,
    method="SLSQP",
    bounds=list(zip(np.zeros(len(upper)), upper)),
    constraints={"type": "eq", "fun": lambda w: w.sum() - 1,
                 "jac": lambda w: np.ones(len(w))},
    options={"ftol": 1e-12, "maxiter": 500}
)
if not projection.success:
    raise RuntimeError(projection.message)
capped_weights = projection.x
assert np.isclose(capped_weights.sum(), 1)
assert np.all(capped_weights >= -1e-10)
assert np.all(capped_weights <= upper + 1e-10)
print(pd.DataFrame({"Upper": upper, "Clip then normalize": naive_renormalized, "Constrained": capped_weights}, index=stocks.index).round(6))
```

| หุ้น | เพดาน | ตัดแล้วหารใหม่ | คำตอบที่ผ่านข้อจำกัด |
|---|---:|---:|---:|
| A | 75.0% | 37.3832% | 40.0% |
| B | 37.5% | 37.3832% | 37.5% |
| C | 22.5% | 25.2336% | 22.5% |
| D | 0.0% | 0.0000% | 0.0% |

`eligible` เป็นชุดค่า `True/False` สำหรับหุ้นที่ผ่านเกณฑ์ `np.where` เลือกว่าจะใช้เพดานบวกหรือศูนย์ `minimize` ลดระยะทางจากเป้าหมาย ส่วน `bounds` กำหนดขอบล่าง/บนรายตัว และ `constraints` บังคับให้น้ำหนักรวมหนึ่ง การใส่ `jac` ให้อนุพันธ์ที่คำนวณได้ตรงตามสูตร ช่วยให้ตัวแก้โจทย์ไม่ต้องประมาณอนุพันธ์นั้นเอง

หลังคำนวณ เราตรวจทั้งสถานะ `success` ผลรวมน้ำหนัก ขอบล่าง และขอบบน ไม่ควรหยุดตรวจที่โปรแกรมคืนคำตอบมาแล้ว ค่าคลาดเคลื่อน $10^{-10}$ ใน `assert` รองรับการคำนวณ floating point ไม่ได้เปิดให้ฝ่าเพดานในระดับที่มีนัยต่อพอร์ต

ก่อนเรียก optimizer เราตรวจด้วยว่าผลรวมเพดานไม่น้อยกว่าหนึ่ง ถ้าเปลี่ยนตัวคูณเป็น 1.0 ขณะที่ยังตัด D ออก ผลรวมเพดานจะเหลือ 0.9 และไม่มีพอร์ตที่ลงทุนครบ 100% ตามเงื่อนไขนี้ ต้องเปลี่ยนข้อจำกัดหรืออนุญาตส่วนเงินสดก่อนหาคำตอบ

เกณฑ์ 12% และตัวคูณ 1.5 ตั้งสูงเพื่อให้เห็นผลในหุ้นเพียงสี่ตัว ไม่ใช่ค่าที่เสนอให้นำไปใช้กับตลาดจริง และมูลค่าตลาดเพียงตัวเดียวก็ยังไม่บอกว่าจะซื้อขายได้คล่องเพียงใด การประเมินสภาพคล่องต้องดูปริมาณซื้อขาย free float ขนาดคำสั่ง และกฎเข้าลงทุนเพิ่มด้วย

<span id="rolling-backtest"></span>

## วางลำดับเวลาให้ตรงก่อนเริ่ม Backtest

Backtest จำลองว่ากฎที่ระบุไว้จะทำอะไรในแต่ละวันตัดสินใจ โดยให้กฎเห็นเฉพาะข้อมูลที่รู้ในวันนั้น โครงสร้างนี้แยกได้เป็นข้อมูลย้อนหลัง ฟังก์ชันหาน้ำหนัก และบัญชีพอร์ตที่ติดตามการถือครองกับต้นทุน

ในตัวอย่างต่อไปมีผลตอบแทนสมมติ 72 เดือน ใช้ 60 เดือนแรกสำหรับเริ่มประมาณค่า และใช้ 12 เดือนที่เหลือประเมินผลแบบ rolling:

| รอบ | ข้อมูลที่ใช้ตัดสินใจ | งวดที่ถือพอร์ตและวัดผล |
|---|---|---|
| 1 | มกราคม 2010–ธันวาคม 2014 | มกราคม 2015 |
| 2 | กุมภาพันธ์ 2010–มกราคม 2015 | กุมภาพันธ์ 2015 |
| 3 | มีนาคม 2010–กุมภาพันธ์ 2015 | มีนาคม 2015 |

หลังจบเดือนแรกที่ทดสอบ เราใช้ผลตอบแทนเดือนนั้นเป็นข้อมูลอดีตสำหรับเดือนถัดไปได้ จึงเป็นการประเมินนอกหน้าต่างประมาณค่าของแต่ละรอบ หากใช้ผลตอบแทนมกราคม 2015 มาช่วยเลือกพอร์ตที่จะถือในมกราคม 2015 จะเกิด [look-ahead bias](glossary.html#look-ahead-bias)

กำหนดกฎสามแบบล่วงหน้าก่อนเปิดดูผลของ 12 เดือนทดสอบ:

- `CW` ใช้มูลค่าตลาดที่รู้ก่อนเริ่มเดือนนั้น
- `EW` แบ่งเงินเท่ากันทั้งสี่ตัว และปรับกลับต้นเดือน
- `LowVol-EW` เลือกสองตัวที่ sample SD รายเดือนจาก 60 เดือนย้อนหลังต่ำที่สุด แล้วแบ่งเงินเท่ากันสองตัว

กฎสุดท้ายเป็นตัวอย่างเลือกหุ้นตาม volatility ในอดีตแล้วให้น้ำหนัก EW ไม่ได้ประมาณ minimum variance portfolio และไม่ใช้ผลตอบแทนอนาคตในการจัดอันดับ การเลือก SD ต่ำย้อนหลังยังมี estimation error และไม่ได้ทำให้พอร์ตมีความเสี่ยงต่ำที่สุดในเดือนถัดไป

### สร้างข้อมูลราคาและผลตอบแทนที่สอดคล้องกัน

เริ่มจากราคาของหุ้น A/B/C/D ในตัวอย่างเดิม จำนวนหุ้นคงที่ ไม่มีเงินปันผลหรือเปลี่ยนสมาชิก ทุกตัวได้รับ log-return shock ร่วมกับ shock เฉพาะตัว สมมติให้ส่วนร่วมมี mean รายเดือน 0.004 และ SD 0.025 ส่วนเฉพาะมี mean ศูนย์และ SD รายเดือน 0.020, 0.035, 0.025, 0.045 ตามลำดับ

จาก log return $\ell$ แปลงเป็น simple return ด้วย $R=e^\ell-1$ ค่าที่สร้างจึงมากกว่า −100% และราคายังคงบวก ตัวเลข 0.004 เป็น mean ของส่วนร่วมใน log return ไม่ใช่ mean ของ simple return หลังแปลงแล้ว

```python
rng = np.random.default_rng(20261002)
months = pd.period_range("2010-01", periods=72, freq="M")
common_log_shock = rng.normal(0.004, 0.025, (72, 1))
specific_log_shocks = rng.normal(0.0, [0.020, 0.035, 0.025, 0.045], (72, 4))
sim_returns = pd.DataFrame(np.expm1(common_log_shock + specific_log_shocks), index=months, columns=stocks.index)
initial_prices = stocks["Price"].to_numpy()
price_states = np.vstack([
    initial_prices,
    initial_prices * (1 + sim_returns.to_numpy()).cumprod(axis=0)
])
cap_before = pd.DataFrame(
    price_states[:-1] * stocks["Shares_million"].to_numpy(),
    index=months, columns=stocks.index
)
print("Return rows:", sim_returns.shape, "Price states:", price_states.shape)
print("First train:", months[0], "to", months[59], "First test:", months[60])
```

ได้ตารางผลตอบแทนขนาด `(72, 4)` และตารางราคาขนาด `(73, 4)` ราคามีมากกว่าผลตอบแทนหนึ่งแถวเพราะต้องมีราคาเริ่มต้นด้วย `np.expm1(x)` คำนวณ $e^x-1$ ส่วน `cumprod(axis=0)` คูณตัวคูณการเติบโตสะสมไปตามเวลาแยกแต่ละหุ้น

`price_states[0]` คือราคาก่อนมกราคม 2010 และ `price_states[60]` คือราคาหลังธันวาคม 2014 แต่ก่อนรับผลตอบแทนมกราคม 2015 เราจึงใช้ `price_states[:-1]` สร้าง `cap_before` ที่แต่ละแถวเก็บมูลค่าตลาดก่อนงวดที่มีชื่อกำกับ วิธีนี้หลีกเลี่ยงการเอาราคาปลายเดือนที่ยังไม่รู้มาให้น้ำหนักผลตอบแทนของเดือนเดียวกัน

`default_rng(20261002)` ตั้ง seed ให้รันซ้ำได้ การกำหนด seed ช่วยตรวจคำตอบของโค้ด แต่ไม่ได้เพิ่มหลักฐานว่าการกระจายผลตอบแทนสมมตินี้แทนตลาดจริงได้

### แยกกฎหาน้ำหนักออกจากบัญชีพอร์ต

`choose_weights` รับประวัติผลตอบแทนกับมูลค่าตลาดที่รู้แล้ว และคืนค่าน้ำหนัก `walk_forward` เลื่อนหน้าต่างข้อมูล เรียกกฎนั้น ปรับการถือครอง หักค่าธรรมเนียม แล้วจึงรับผลตอบแทนของเดือนทดสอบ

เราเริ่มเงินลงทุนที่ 1 หน่วย และยกเว้นค่าซื้อเริ่มต้นเหมือนกันทุกกฎ เพื่อเปรียบเทียบต้นทุนการปรับพอร์ตภายหลัง แต่ละเดือนคิดค่าธรรมเนียม 0.1% ของมูลค่าซื้อและขายตามฟังก์ชันเดิม ก่อนรับผลตอบแทนเดือนนั้น สมมติว่าซื้อขายได้ที่ราคาที่ใช้ตัดสินใจ ไม่มีความล่าช้าและไม่มี price impact เป็นข้อสมมติที่เอื้อกว่าการลงทุนจริง

```python
def choose_weights(history, known_caps, rule):
    n = history.shape[1]
    if rule == "CW":
        w = known_caps.to_numpy() / known_caps.sum()
    elif rule == "EW":
        w = np.full(n, 1 / n)
    elif rule == "LowVol-EW":
        chosen = history.std(ddof=1).nsmallest(2).index
        w = np.array([0.5 if name in chosen else 0.0 for name in history.columns])
    else:
        raise ValueError("Unknown rule")
    return w

def walk_forward(returns, known_caps, rule, window=60, fee_rate=0.001):
    if not returns.index.equals(known_caps.index) or not returns.columns.equals(known_caps.columns):
        raise ValueError("Returns and caps must have the same labels")
    if len(returns) <= window or returns.isna().any().any() or known_caps.isna().any().any():
        raise ValueError("Need complete data and at least one test month")
    records, weight_rows = [], []
    holdings = None
    for t in range(window, len(returns)):
        history = returns.iloc[t-window:t]
        target = choose_weights(history, known_caps.iloc[t], rule)
        if holdings is None:
            holdings = target.copy()  # Initial wealth 1; initial entry fee excluded for all rules.
        wealth_before = holdings.sum()
        drift_weights = holdings / wealth_before
        turnover = np.abs(target - drift_weights).sum() / 2
        holdings, fee = rebalance_with_fee(holdings, target, fee_rate)
        holdings = holdings * (1 + returns.iloc[t].to_numpy())
        records.append({
            "Train last": history.index[-1], "Net return": holdings.sum() / wealth_before - 1,
            "Wealth": holdings.sum(), "One-way turnover": turnover, "Fee": fee
        })
        weight_rows.append(target)
    result = pd.DataFrame(records, index=returns.index[window:])
    weights = pd.DataFrame(weight_rows, index=result.index, columns=returns.columns)
    return result, weights

paths, target_paths = {}, {}
for rule in ["CW", "EW", "LowVol-EW"]:
    paths[rule], target_paths[rule] = walk_forward(sim_returns, cap_before, rule)
print(paths["EW"][["Train last", "Net return"]].head(2))
```

ตัวอย่างสองแถวแรกของ EW เป็นดังนี้:

| เดือนทดสอบ | เดือนสุดท้ายที่ใช้ประมาณค่า | ผลตอบแทนหลังต้นทุน |
|---|---|---:|
| 2015-01 | 2014-12 | ประมาณ −4.0779% |
| 2015-02 | 2015-01 | ประมาณ −2.6414% |

`returns.iloc[t-window:t]` เลือกข้อมูลย้อนหลัง 60 แถว โดยไม่รวมแถวตำแหน่ง `t` ส่วน `returns.iloc[t]` เป็นผลตอบแทนที่จะได้รับหลังตั้งพอร์ตแล้ว กฎ CW ใช้ `known_caps.iloc[t]` ซึ่งในตารางของเราหมายถึงมูลค่าตลาดก่อนเริ่มงวด ไม่ใช่มูลค่าตลาดของเดือนแรกในหน้าต่างย้อนหลัง

`holdings` เก็บมูลค่าการถือครองที่เปลี่ยนตามผลตอบแทนจริงของแต่ละงวดไว้ข้ามรอบ จึงใช้คำนวณน้ำหนักที่เปลี่ยนไปก่อน rebalance ได้ หากนำเป้าหมายเดือนก่อนมาเทียบกับเป้าหมายเดือนใหม่โดยไม่ผ่านการเปลี่ยนราคา จะนับ turnover ของ EW ต่ำกว่าที่เกิดขึ้นได้ แม้เป้าหมายทั้งสองเดือนจะเป็น 25% เหมือนกันก็ตาม

โค้ดใช้ `records` เป็นรายการแถวผลลัพธ์ และ `weight_rows` เก็บน้ำหนักเป้าหมายในแต่ละรอบ ก่อนแปลงเป็น DataFrame เมื่อจบการทดสอบ โครงสร้างการส่งกฎให้น้ำหนักเข้าไปทดสอบต่อเนื่องนี้เชื่อมกับ [Foundations Lab](https://www.coursera.org/learn/advanced-portfolio-construction-python/lecture/ZdgGw/module-1-lab-session-foundations) โดยตัวอย่างที่นี่สร้างข้อมูลและบัญชีต้นทุนขึ้นใหม่ทั้งหมด

<span id="read-backtest-results"></span>

## อ่านผลทดสอบพร้อมต้นทุนและช่วงข้อมูล

เรารายงานผลตอบแทนรวม 12 เดือน, SD รายเดือนคูณ $\sqrt{12}$, maximum drawdown และ tracking error เทียบ CW คำว่า annualized ในคอลัมน์ SD หมายถึงการแปลงสเกลภายใต้สมมติฐานที่ใช้กฎ square-root-of-time ไม่ได้ทำให้ประวัติเพียง 12 เดือนกลายเป็นหลักฐานระยะยาว

Tracking error ในตารางนี้คือ sample SD ของผลต่างผลตอบแทนสุทธิรายเดือนระหว่างกลยุทธ์กับ CW แล้วคูณ $\sqrt{12}$ จึงมีหน่วยต่อปี:

$$
\mathrm{TE}=\operatorname{SD}_{\mathrm{sample}}
\left(R_{\mathrm{strategy},t}^{\mathrm{net}}-R_{\mathrm{CW},t}^{\mathrm{net}}\right)\sqrt{12}.
$$

เรารวมเงินเริ่มต้นไว้ก่อนคำนวณ drawdown เพื่อไม่ให้การขาดทุนเดือนแรกหายไปจากประวัติจุดสูงสุด และรวมค่าธรรมเนียมที่จ่ายจริงทุกครั้ง ไม่ใช่นำค่า turnover เฉลี่ยไปแทนต้นทุนทั้งหมด

```python
summary_rows = []
for rule, path in paths.items():
    wealth_with_start = np.r_[1.0, path["Wealth"].to_numpy()]
    drawdown = wealth_with_start / np.maximum.accumulate(wealth_with_start) - 1
    active_return = path["Net return"] - paths["CW"]["Net return"]
    summary_rows.append({
        "Rule": rule,
        "Total return (%)": 100 * (path["Wealth"].iloc[-1] - 1),
        "Annualized SD (%)": 100 * path["Net return"].std(ddof=1) * np.sqrt(12),
        "Max drawdown (%)": 100 * drawdown.min(),
        "TE vs CW (%)": 100 * active_return.std(ddof=1) * np.sqrt(12),
        "Turnover sum (%)": 100 * path["One-way turnover"].sum(),
        "Fees per initial 100k": 100_000 * path["Fee"].sum()
    })
backtest_summary = pd.DataFrame(summary_rows).set_index("Rule")
print(backtest_summary.round(4).to_string())
assert all(len(path) == 12 for path in paths.values())
assert all((path["Train last"].to_numpy() < path.index.to_numpy()).all() for path in paths.values())
assert np.allclose(paths["CW"]["One-way turnover"], 0, atol=1e-12)
changed_future = sim_returns.copy()
changed_future.iloc[65:] = 0.30
_, changed_weights = walk_forward(changed_future, cap_before, "LowVol-EW")
assert np.allclose(target_paths["LowVol-EW"].iloc[:6], changed_weights.iloc[:6])
print("Timing checks passed")
```

| กฎ | ผลตอบแทนรวม | Annualized SD | Max drawdown | TE เทียบ CW |
|---|---:|---:|---:|---:|
| CW | −3.8380% | 9.8147% | −9.4003% | 0.0000% |
| EW | −5.3937% | 11.0447% | −11.5318% | 2.6865% |
| LowVol-EW | −1.3768% | 8.2990% | −8.2704% | 5.6906% |

| กฎ | ผลรวม one-way turnover ทั้งช่วง | ค่าธรรมเนียม ถ้าเริ่ม 100,000 บาท |
|---|---:|---:|
| CW | 0.0000% | 0.0000 บาท |
| EW | 12.8734% | 23.8298 บาท |
| LowVol-EW | 8.2160% | 15.6508 บาท |

Turnover ที่แสดงเป็นผลรวมสัดส่วนของแต่ละรอบ โดยแต่ละรอบมีฐานเป็นมูลค่าพอร์ตก่อนปรับของตัวเอง จึงไม่ควรคูณผลรวมนี้กับเงินเริ่มต้นแล้วถือว่าเท่ากับยอดซื้อขายจริงทั้งหมดโดยไม่ตรวจฐานเงิน ส่วนค่าธรรมเนียมในตารางใช้ผลรวมจำนวนเงินที่หักออกจริง แล้วแปลงสเกลจากเงินเริ่มต้น 1 เป็น 100,000

CW ไม่มี turnover ภายใต้เงื่อนไขชุดหุ้นและจำนวนหุ้นคงที่ที่เราตั้งไว้ ผลลัพธ์นี้เป็นอีกวิธีตรวจความสอดคล้องระหว่างราคา ผลตอบแทน และมูลค่าตลาดในโค้ด หาก CW ในข้อมูลสมมติชุดนี้ต้องซื้อขายทุกเดือน ควรย้อนตรวจเวลาและสูตรก่อนอธิบายผลเชิงการลงทุน

LowVol-EW ขาดทุนน้อยกว่าในเส้นทางสมมตินี้ แต่ยังขาดทุน และมี tracking error เทียบ CW มากกว่า EW การมี SD รวมต่ำกว่าจึงอยู่ร่วมกับการให้ผลต่างจาก benchmark มากกว่าได้ ตารางนี้ไม่ได้พิสูจน์ว่ากฎใดชนะตลาด ตัวอย่างมีเพียง 12 เดือนทดสอบจากแบบจำลองที่เรากำหนด และยังยกเว้นต้นทุนซื้อเริ่มต้น ภาษี และ market impact

ท้ายโค้ดทดลองเปลี่ยนผลตอบแทนตั้งแต่ตำแหน่ง 65 เป็นต้นไป แล้วตรวจว่าน้ำหนักก่อนเห็นข้อมูลเหล่านั้นไม่เปลี่ยน การตรวจนี้ใช้เฉพาะน้ำหนักช่วงที่ยังไม่รับข้อมูลที่แก้ ไม่ได้นำเส้นทางดัดแปลงมารายงานผลการลงทุน ผลลัพธ์ `Timing checks passed` บอกว่าผ่านเงื่อนไขที่ตรวจ ไม่ได้ยืนยันว่า backtest ตลาดจริงจะไม่มีความผิดพลาดทุกชนิด

หากลองปรับช่วงย้อนหลัง จำนวนหุ้นที่เลือก หรือเกณฑ์คัดหุ้นหลังเห็นตารางแล้ว ช่วง 2015 ก็กลายเป็นส่วนหนึ่งของการพัฒนากฎ ต้องเก็บข้อมูลอีกช่วงที่ยังไม่เคยใช้ตัดสินใจไว้ประเมินครั้งต่อไป ตามแนวทาง [แยกการประมาณค่าออกจากการทดสอบ](portfolio-estimation.html#train-test-discipline) ข้อมูลจริงยังต้องมีสมาชิกที่มีอยู่ในอดีต หุ้นที่ถูกเพิกถอน และเวลาประกาศงบ เพื่อไม่เลือกเฉพาะบริษัทที่รอดมาถึงวันนี้หรือใช้ข้อมูลเร็วกว่าที่เคยรู้ได้

<span id="smart-beta-exercises"></span>

## แบบฝึกหัด

ลองคำนวณก่อนเปิดเฉลย ใช้ข้อมูล A/B/C/D และสมมติฐานของแต่ละส่วนตามเดิม

<details class="exercise">
<summary>1. ถ้าราคาหุ้นทุกตัวเพิ่มขึ้น 10% พร้อมกัน ต้องปรับพอร์ต CW หรือ EW หรือไม่?</summary>

เมื่อทุกตัวโตด้วยตัวคูณ 1.10 เท่ากัน เศษและส่วนในสูตรน้ำหนักหลังราคาเปลี่ยนเพิ่มเท่ากัน น้ำหนักจึงเท่าเดิมทั้ง CW และ EW ภายใต้ชุดหุ้นและจำนวนหุ้นคงที่จึงไม่ต้องซื้อขายเพื่อกลับไปยังเป้าหมายเดิม มูลค่าพอร์ตเพิ่ม 10% แต่ turnover เป็นศูนย์

</details>

<details class="exercise">
<summary>2. ทำไม EW มี effective number เท่ากับ 4 แต่ D มี risk contribution เกินครึ่ง?</summary>

Effective number ใช้น้ำหนักอย่างเดียว หุ้นทุกตัวได้น้ำหนัก 0.25 จึงมีค่า 4 ส่วนตัวอย่างความเสี่ยงกำหนด SD ต่างกันและ covariance นอกแนวทแยงเป็นศูนย์ สัดส่วนของ D จึงเป็น $0.40^2/(0.10^2+0.20^2+0.30^2+0.40^2)=16/30=53.3333\%$ จำนวนชื่อและจำนวนเงินที่เท่ากันไม่ได้บังคับให้ contribution ต่อความเสี่ยงเท่ากัน

</details>

<details class="exercise">
<summary>3. ค่า one-way turnover 4.7619% กับค่าธรรมเนียม 0.1% ทำไมจึงไม่เสียเพียง 5 บาท?</summary>

One-way turnover นับเพียงด้านเดียวของการย้ายเงิน ส่วนอัตราค่าธรรมเนียมในโจทย์คิดทั้งซื้อและขาย ต้องซื้อประมาณ 5,000 บาทและขายประมาณ 5,000 บาท จึงคิดจากยอดรวม 10,000 บาท ได้ 10 บาท ถ้าผู้ให้บริการใช้อัตราที่รวมการไปกลับมาแล้ว ต้องใช้ฐานตามอัตรานั้นและไม่คูณสองซ้ำ

</details>

<details class="exercise">
<summary>4. เพดาน C อยู่ที่ 22.5% ทำไมการตัดน้ำหนักแล้วหารใหม่จึงยังผิดเงื่อนไข?</summary>

หลังตัดค่า ผลรวมน้ำหนักเหลือประมาณ 0.891667 การหาร C ด้วยผลรวมนี้ทำให้ $0.225/0.891667\approx0.252336$ ซึ่งสูงกว่าเพดานเดิม คำตอบที่ตรวจข้อจำกัดแล้วคือ A/B/C/D เท่ากับ 40%, 37.5%, 22.5%, 0% หากเปลี่ยนเพดาน ต้องตรวจผลรวมเพดานว่ารองรับเงินลงทุนครบหนึ่งได้ก่อน แล้วตรวจคำตอบทุกข้ออีกครั้ง

</details>

<details class="exercise">
<summary>5. จะเลือกพอร์ตสำหรับกุมภาพันธ์ 2015 ด้วยข้อมูลเดือนใดได้บ้าง?</summary>

หน้าต่าง 60 เดือนใช้ผลตอบแทนกุมภาพันธ์ 2010 ถึงมกราคม 2015 และใช้มูลค่าตลาด ณ หลังมกราคม 2015 ก่อนเริ่มกุมภาพันธ์ ผลตอบแทนกุมภาพันธ์ 2015 ต้องเข้าบัญชีหลังเลือกน้ำหนักแล้ว หากข้อมูลบัญชีสำหรับหุ้นบางตัวประกาศกลางกุมภาพันธ์ ข้อมูลนั้นก็ยังใช้ไม่ได้ในคำสั่งต้นเดือนเดียวกัน

</details>

<details class="exercise">
<summary>6. ต้องเปลี่ยนอะไรบ้างก่อนเรียกตัวอย่างนี้ว่าเป็นการทดสอบกลยุทธ์กับตลาดจริง?</summary>

ต้องเปลี่ยนข้อมูลสมมติเป็นชุดข้อมูลที่มีแหล่งที่มา ช่วงเวลา นิยามผลตอบแทนและองค์ประกอบย้อนหลังตรวจสอบได้ จัดข้อมูลตามเวลาที่ผู้ลงทุนรู้จริง ระบุเวลาส่งคำสั่งและราคาที่ซื้อขายได้ รวมต้นทุนตามขนาดการลงทุน และกำหนดช่วงพัฒนากฎกับช่วงทดสอบที่ยังไม่เคยใช้เลือกกฎไว้ล่วงหน้า การเพิ่มจำนวนแถวจากแบบจำลองเดิมอย่างเดียวไม่ทดแทนขั้นตอนเหล่านี้

</details>
