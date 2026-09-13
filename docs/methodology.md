---
title: วิธีคำนวณในห้องทดลอง
description: สูตร สมมติฐาน และขอบเขตของ CPPI กับ Protective Put ใน Toolkit
---

ห้องทดลองนี้ใช้ **เส้นทางสมมติที่กำหนดไว้ล่วงหน้า** 4 แบบ แบบละ 12 ผลตอบแทนรายเดือน เพื่อให้เปลี่ยนค่าพารามิเตอร์แล้วเปรียบเทียบผลบนเส้นทางเดียวกันได้ ไม่ใช่ข้อมูลตลาด การทดสอบย้อนหลัง หรือการทำซ้ำผลวิจัยของวิทยานิพนธ์

## CPPI คิดอย่างไร

ให้ $V_t$ เป็นมูลค่าพอร์ต ณ เดือน $t$, $K_T$ เป็น floor เป้าหมาย ณ สิ้นปี, $r$ เป็นอัตราดอกเบี้ยทบต้นต่อเนื่องรายปี และ $m$ เป็น multiplier

$$
F_t = K_T e^{-r(1-t/12)},\qquad C_t = V_t-F_t
$$

จำนวนเงินที่ลงทุนในสินทรัพย์เสี่ยงคือ

$$
E_t = \min\{V_t,\max(0,mC_t)\}
$$

ส่วนที่เหลือ $V_t-E_t$ ลงทุนในสินทรัพย์ปลอดความเสี่ยง จึงไม่มีการกู้ยืมหรือขายชอร์ตในห้องทดลองนี้ หากผลตอบแทนสินทรัพย์เสี่ยงในเดือนถัดไปเท่ากับ $R_{t+1}$ พอร์ตจะมีมูลค่า

$$
V_{t+1} = E_t(1+R_{t+1})+(V_t-E_t)e^{r/12}
$$

คำนวณพอร์ตหลังผลตอบแทนเกิดขึ้นแล้วจึงปรับสัดส่วนสำหรับเดือนถัดไป ไม่มีการนำราคาที่จะเกิดในอนาคตมาใช้จัดพอร์ต ตัวควบคุม floor แสดงเป็นเปอร์เซ็นต์ของเงินตั้งต้น **ณ สิ้นปี**; เมื่อดอกเบี้ยเป็นศูนย์ floor ระหว่างทางจึงเท่ากับเป้าหมายสิ้นปีทุกเดือน

สูตรการจำกัด exposure อ้างอิงแนวคิดใน da Silva (2018), สมการ 4.27 หน้าเลขพิมพ์ 52–53 ส่วน floor และ cushion ดูสมการ 2.6 หน้า 14–15 งานต้นฉบับใช้การปรับพอร์ตรายวันในส่วนการทดลองนั้น แต่ Toolkit ใช้รายเดือนเพื่อแสดงการคำนวณทีละขั้น

## Floor อาจหลุดได้

เมื่อดอกเบี้ยเป็นศูนย์และข้อจำกัด exposure ยังไม่ทำงาน จะได้ $C_{t+1}=C_t(1+mR_{t+1})$ ถ้า $C_t>0$ และผลตอบแทนระหว่างการปรับพอร์ตต่ำกว่า $-1/m$ พอร์ตอาจหลุด floor เช่น เงิน 100, floor 90 และ $m=3$ ลงทุนเสี่ยง 30 และปลอดความเสี่ยง 70 หากสินทรัพย์เสี่ยงลดลง 40% ในงวดเดียว พอร์ตเหลือ $30(0.6)+70=88$ ซึ่งต่ำกว่า floor 90

เมื่อ cushion หมดหรือเป็นลบ สูตรกำหนด exposure เป็นศูนย์ พอร์ตอาจไม่ร่วมรับการฟื้นตัวของตลาดในเดือนต่อมา เรียกว่า **cash lock** ผลนี้ขึ้นกับเส้นทางและค่าที่เลือก เส้นทางขึ้นลงสลับกันในค่าเริ่มต้นของ Toolkit ทำให้ cushion ลดลง แต่ยังไม่ทำให้เกิด cash lock

Floor เป็นเป้าหมายของกฎจัดสรรสินทรัพย์ ไม่ใช่สัญญาค้ำประกันจากบุคคลภายนอก ค่าที่แสดงตรวจการหลุด floor เฉพาะจุดรายเดือน

## ตัวเปรียบเทียบและตัวชี้วัด

- **Buy & Hold:** ลงสินทรัพย์เสี่ยง 100% ตั้งแต่เริ่ม แล้วถือครบปี
- **Constant Mix:** ลงสินทรัพย์เสี่ยง 60% และปลอดความเสี่ยง 40% แล้วปรับกลับสัดส่วนเดิมทุกเดือน
- **ผลตอบแทน:** $(V_{12}/V_0-1)\times100$ เป็นเปอร์เซ็นต์ ไม่ใช่อัตราที่ประมาณจากตลาด
- **Maximum drawdown:** การลดลงมากที่สุดจากมูลค่าสูงสุดที่เคยสังเกตถึงเดือนนั้น รายงานเป็นเปอร์เซ็นต์บวกของการสูญเสีย และรวมจุดเริ่มต้นในการคำนวณ
- **Turnover:** ผลรวมจำนวนเงินที่ซื้อหรือขายฝั่งสินทรัพย์เสี่ยงหลังเดือนที่ 1–11 ไม่นับการจัดพอร์ตครั้งแรก ไม่ใช่เปอร์เซ็นต์ ไม่ใช่ค่าธรรมเนียม และไม่ได้นำไปหักออกจากพอร์ต

Exposure ที่แสดง ณ เดือนที่ 12 เป็นค่าจากสูตรเพื่ออธิบายการจัดสรร หากต่ออายุพอร์ตด้วย floor เดิม ไม่ได้ส่งคำสั่งซื้อขาย ณ สิ้นสุดการทดลอง และไม่นับรวมใน turnover

ทั้งสามกลยุทธ์เริ่มด้วยเงินจำนวนเดียวกัน สมมติให้แบ่งหน่วยสินทรัพย์เป็นเศษส่วนได้ และไม่มีค่าธรรมเนียม ภาษี สเปรด slippage หรือข้อจำกัดสภาพคล่อง เงินปลอดความเสี่ยงเติบโตด้วยอัตราที่กำหนดแน่นอน ข้อสมมติเหล่านี้ทำให้ผลต่างจากการลงทุนจริง

## Protective Put คิดอย่างไร

ส่วนนี้เป็นเครื่องคิดเลขมูลค่า **ณ วันหมดอายุ** ของหุ้นกับ Put ที่อ้างอิงหุ้นเดียวกันและมีจำนวนหน่วยเท่ากัน ใช้ premium สมมติที่ผู้ใช้กรอก ไม่มีแบบจำลองตีราคา Option ระหว่างทาง

$$
\text{Put payoff}=n\max(K-S_T,0)
$$

$$
\text{Terminal wealth}=nS_T+n\max(K-S_T,0)
$$

$$
\text{Initial cost}=n(S_0+P),\qquad
\text{Profit}=\text{Terminal wealth}-\text{Initial cost}
$$

$S_0$ คือราคาหุ้นเริ่มต้น, $S_T$ คือราคาหุ้นวันหมดอายุ, $K$ คือ strike, $P$ คือ premium ต่อหน่วย และ $n$ คือจำนวนหน่วย ตัวอย่าง $S_0=100$, $K=90$, $P=4$, $S_T=80$, $n=1$: หุ้นมีมูลค่า 80, Put จ่าย payoff 10, เงินปลายทางรวม 90 แต่เงินตั้งต้นที่จ่ายคือ 104 จึงขาดทุน 14 ไม่ใช่กำไร 10

ตัวอย่างนี้สมมติถือจนหมดอายุ ได้รับการชำระตามสัญญาครบถ้วน ไม่มีเงินปันผล ดอกเบี้ยเงินที่ใช้ซื้อ ค่าธรรมเนียม หรือภาษี มูลค่าที่ถูกป้องกัน ณ วันหมดอายุจึงต้องอ่านแยกจากกำไรสุทธิ แนวคิด Stock + Put อ้างอิง da Silva (2018), หัวข้อ 2.2.2 หน้าเลขพิมพ์ 10–13

## ทำซ้ำผลและขอบเขตของการตีความ

ไฟล์ CSV เก็บพารามิเตอร์ ผลตอบแทนรายเดือน และมูลค่าทั้ง 13 จุดรวมเดือนเริ่มต้น ไฟล์ `src/math.mjs` เป็นสูตรที่เว็บไซต์ใช้จริงและมีการตรวจด้วย `qa/math-checks.mjs` เส้นทางเดียวไม่ได้บอกความน่าจะเป็นของเหตุการณ์หรือพิสูจน์ว่ากลยุทธ์ใดเหมาะกับผู้ลงทุนทุกคน

## Expanded worked examples — 2026-09-13

The chapter now develops the formulas and walks through matched-budget OBPI, self-financing CPPI across four early rebalancing periods, gap thresholds with positive interest and capped exposure, and a multi-period illustrative TIPP ratchet. These are new teaching examples. The original monthly JavaScript model and three interactive components remain unchanged.

The continuous CPPI derivation assumes continuous prices and trading, no costs, constant parameters, unconstrained exposure, and borrowing/lending at the same rate. Its exponential cushion solution must not be substituted for the capped monthly simulator. The TIPP example uses zero interest and its own observed portfolio high-water mark; its drawdown statements refer to those observation times.

EUT/CE and CPT examples show the difference between transforming wealth, averaging values, and using cumulative decision weights. The two-asset correlation example and five-outcome shortfall comparison are teaching constructions. No probabilities are attached to the four authored market paths in the interactive lab.

The Notebook includes executable checks for all principal new numerical examples. It still captures the complete canonical chapter, and its original two charts and 16 Python/JavaScript scenario comparisons remain part of verification.
