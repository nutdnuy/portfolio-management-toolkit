---
title: คำศัพท์
description: คำศัพท์และสัญลักษณ์เรื่องการป้องกันพอร์ต พร้อมลิงก์กลับไปยังตัวอย่างในบทเรียน
---

# คำศัพท์

หน้านี้รวมคำที่ใช้ในบท [Portfolio Insurance Strategies: Friend or Foe?](portfolio-insurance.html) แต่ละคำมีนิยามสั้นและลิงก์กลับไปยังตัวอย่างที่อธิบายไว้ เลขหน้าแหล่งแนวคิดอ้างถึง [วิทยานิพนธ์ da Silva (2018)](portfolio-insurance.html#references)

<div class="glossary-search">
<label for="glossary-query">ค้นหาคำศัพท์</label>
<input id="glossary-query" type="search" placeholder="เช่น การป้องกัน, Floor หรือ CPPI" autocomplete="off" aria-describedby="glossary-status">
<p id="glossary-status" role="status" aria-live="polite"></p>
</div>

<section class="glossary-group" id="group-goals">

## เป้าหมายและการวัดผล

<section class="glossary-term" id="portfolio-insurance">

### Portfolio Insurance · กลยุทธ์ป้องกันพอร์ต

กลุ่มกลยุทธ์ที่มุ่งจำกัดการลดลงของมูลค่าพอร์ต พร้อมเหลือโอกาสรับการเติบโต อาจใช้ Option หรือกฎปรับสินทรัพย์ คำว่า Insurance ในชื่อไม่ได้หมายความว่าทุกแบบมีบริษัทประกันหรือคู่สัญญารับประกันผลลัพธ์

[กลับไปเริ่มบทเรียน](portfolio-insurance.html#floor-and-cushion) · แหล่งแนวคิด: พิมพ์ น. 4–16 / PDF 31–43

</section>

<section class="glossary-term" id="floor">

### Floor · ระดับมูลค่าที่มุ่งป้องกัน

เป้าหมายขั้นต่ำของมูลค่าพอร์ต ต้องระบุจำนวนเงินและเวลา Floor เมื่อครบกำหนด $F_T$ อาจต่างจากมูลค่าปัจจุบัน $F_t$ ที่ใช้ในกฎปรับพอร์ต การรักษา Floor ปลายทางกับการจำกัดการลดลงตลอดช่วงลงทุนเป็นคนละเงื่อนไข

[ดูว่าปกป้องเท่าไรและเมื่อไร](portfolio-insurance.html#floor-and-cushion) · แหล่งแนวคิด: พิมพ์ น. 9, 13–15 / PDF 36, 40–42

</section>

<section class="glossary-term" id="payoff">

### Payoff · มูลค่าที่จ่ายตามผลลัพธ์เมื่อครบกำหนด

มูลค่าที่ได้ตามสินทรัพย์หรือสัญญาเมื่อรู้ผลลัพธ์ปลายทาง เช่น Payoff ของ Put คือ $\max(K-S_T,0)$ ตัวเลขนี้ยังไม่ได้หักเงินที่ใช้ซื้อสัญญาวันนี้ จึงยังไม่ใช่กำไรของผู้ซื้อ

[ดูตัวอย่างหุ้นหนึ่งหน่วยบวก Put](portfolio-insurance.html#protective-put) · แหล่งแนวคิด: พิมพ์ น. 10–13 / PDF 37–40

</section>

<section class="glossary-term" id="drawdown">

### Drawdown · การลดลงจากจุดสูงสุดก่อนหน้า

ถ้า $H_t$ เป็นจุดสูงสุดของมูลค่าพอร์ตจนถึงเวลา $t$ ขนาด Drawdown คือ $1-V_t/H_t$ ส่วน Maximum drawdown คือค่าสูงสุดของขนาดดังกล่าวตลอดช่วงที่วัด การลดจากจุดสูงสุดต่างจากการขาดทุนเทียบเงินตั้งต้นและการหลุด Floor

[ดูตัวอย่าง 100 → 120 → 108](portfolio-insurance.html#how-to-compare) · นิยามประกอบการวัดผลในบทเรียน

</section>

</section>

<section class="glossary-group" id="group-strategies">

## สัญญาและกฎจัดสรรพอร์ต

<section class="glossary-term" id="put-option">

### Put option · สิทธิที่จะขายสินทรัพย์ที่ราคากำหนด

สัญญาที่ให้ผู้ถือสิทธิขายสินทรัพย์อ้างอิงที่ราคาใช้สิทธิ $K$ ภายใต้เงื่อนไขและเวลาของสัญญา บทเรียนใช้ European Put ที่พิจารณาการใช้สิทธิเมื่อหมดอายุ และหนึ่งหน่วย Option อ้างอิงสินทรัพย์หนึ่งหน่วย

[ดูมูลค่า Put ที่วันหมดอายุ](portfolio-insurance.html#protective-put) · แหล่งแนวคิด: พิมพ์ น. 10–13 / PDF 37–40

</section>

<section class="glossary-term" id="premium">

### Premium · ราคา Option ที่จ่ายวันนี้

เงินที่ผู้ซื้อจ่ายเพื่อได้สิทธิตาม Option ต้องนับรวมในงบลงทุนและต้นทุนเมื่อต้องการคำนวณกำไร ค่า Premium ที่กรอกในเครื่องมือเป็นค่าตัวอย่าง ไม่ใช่ราคายุติธรรมที่เครื่องมือคำนวณให้

[ดูต้นทุนรวม 100 + 4](portfolio-insurance.html#protective-put) · แหล่งแนวคิด: พิมพ์ น. 10–13 / PDF 37–40

</section>

<section class="glossary-term" id="slpi">

### SLPI · Stop Loss Portfolio Insurance

กฎถือสินทรัพย์เสี่ยงแล้วขายไปถือสินทรัพย์ปลอดความเสี่ยงเมื่อมูลค่าลดถึงเกณฑ์ ในรุ่นที่วิทยานิพนธ์ศึกษา เมื่อขายแล้วจะไม่กลับเข้าตลาดจนจบช่วงลงทุน ราคาอาจกระโดดผ่านเกณฑ์ก่อนขายได้

[ดูการเปรียบเทียบสี่กลยุทธ์](portfolio-insurance.html#strategies) · แหล่งแนวคิด: พิมพ์ น. 9, 50 / PDF 36, 77

</section>

<section class="glossary-term" id="obpi">

### OBPI · Option Based Portfolio Insurance

การจัดพอร์ตให้มีลักษณะการป้องกันด้วย Option เช่น สินทรัพย์เสี่ยงบวก Put หรือสินทรัพย์ปลอดความเสี่ยงบวก Call การซื้อ Option จริงกับการปรับสินทรัพย์เพื่อเลียนแบบ Option มีเงื่อนไขดำเนินงานต่างกัน

[ดูการจัดงบซื้อการป้องกัน](portfolio-insurance.html#option-budget) · แหล่งแนวคิด: พิมพ์ น. 10–13 / PDF 37–40

</section>

<section class="glossary-term" id="cppi">

### CPPI · Constant Proportion Portfolio Insurance

กฎจัดสรรเงินลงทุนเสี่ยงตามตัวคูณคงที่ของ Cushion เมื่อ Cushion เล็กลง เงินลงทุนเสี่ยงตามกฎจะลดลง รุ่นที่ไม่กู้และไม่ขายชอร์ตจะจำกัดเงินลงทุนเสี่ยงให้อยู่ระหว่างศูนย์กับมูลค่าพอร์ต

[ดูสูตร CPPI](portfolio-insurance.html#cppi-rule) · แหล่งแนวคิด: พิมพ์ น. 13–15, 52–53 / PDF 40–42, 79–80

</section>

<section class="glossary-term" id="cushion">

### Cushion · ส่วนต่างเหนือ Floor

ผลต่าง $C_t=V_t-F_t$ ระหว่างมูลค่าพอร์ตกับ Floor ณ เวลาเดียวกัน วัดเป็นหน่วยเงินเดียวกับพอร์ต ใน CPPI เป็นฐานที่นำไปคูณ Multiplier เพื่อกำหนดเงินลงทุนเสี่ยง

[ดูตัวอย่างพอร์ต 100 และ Floor 90](portfolio-insurance.html#cppi-example) · แหล่งแนวคิด: พิมพ์ น. 13–15 / PDF 40–42

</section>

<section class="glossary-term" id="multiplier">

### Multiplier · ตัวคูณ Cushion

พารามิเตอร์ $m$ ที่แปลง Cushion เป็นเงินลงทุนในสินทรัพย์เสี่ยงก่อนใช้ข้อจำกัดอื่น ไม่มีหน่วย $m=3$ หมายถึงสามเท่าของ Cushion ไม่ใช่สามเท่าของมูลค่าพอร์ต

[ดูกฎและเพดานเงินลงทุนเสี่ยง](portfolio-insurance.html#cppi-rule) · แหล่งแนวคิด: พิมพ์ น. 14–15, 52–53 / PDF 41–42, 79–80

</section>

<section class="glossary-term" id="rebalancing">

### Rebalancing · การปรับสัดส่วนพอร์ต

การซื้อขายเพื่อให้จำนวนเงินหรือสัดส่วนสินทรัพย์ตรงกับกฎหลังราคาและมูลค่าพอร์ตเปลี่ยน การกำหนดเป้าหมายต่อเนื่องในสูตรกับการซื้อขายจริงเป็นรอบให้ผลต่างกันได้

[ดูการปรับพอร์ตหนึ่งรอบ](portfolio-insurance.html#cppi-example) · แหล่งแนวคิด: พิมพ์ น. 14–16, 52–53 / PDF 41–43, 79–80

</section>

<section class="glossary-term" id="gap-risk">

### Gap risk · ความเสี่ยงที่ราคาผ่านเกณฑ์ก่อนปรับได้ทัน

ความเสี่ยงที่ราคาหรือมูลค่าพอร์ตเคลื่อนที่ผ่านระดับป้องกันก่อนจะลดการถือสินทรัพย์เสี่ยงได้ การขายหลังจากหลุดเกณฑ์ไม่ได้ทำให้พอร์ตกลับไปมีมูลค่าเท่าเกณฑ์โดยอัตโนมัติ

[ดูตัวอย่างพอร์ต 100 เหลือ 88](portfolio-insurance.html#gap-risk) · แหล่งแนวคิด: พิมพ์ น. 32–33 / PDF 59–60

</section>

<section class="glossary-term" id="cash-lock">

### Cash lock · พอร์ตติดอยู่ในสินทรัพย์ปลอดความเสี่ยง

ภาวะที่ Cushion หมดจนกฎป้องกันให้เงินลงทุนในสินทรัพย์เสี่ยงลดเหลือศูนย์ และกลยุทธ์ไม่กลับเข้าตลาดในช่วงที่เหลือ จึงอาจไม่มีส่วนร่วมกับการฟื้นตัวของตลาด ต่างจากการเลือก Multiplier เป็นศูนย์ตั้งแต่ต้น

[ดูเหตุใดตลาดฟื้นแต่พอร์ตไม่ตาม](portfolio-insurance.html#gap-risk) · แหล่งแนวคิด: พิมพ์ น. 14 / PDF 41

</section>

<section class="glossary-term" id="tipp">

### TIPP · Time Invariant Portfolio Protection

แนวทางต่อยอดจาก CPPI ที่ยก Floor ตามเงื่อนไขเมื่อมูลค่าพอร์ตเพิ่มขึ้น เพื่อเก็บการเติบโตบางส่วนไว้ในเป้าหมายป้องกัน ต้องระบุกฎยก Floor และความถี่ปรับพอร์ตให้ชัดก่อนเปรียบเทียบผล

[ดูตัวอย่างพอร์ตโตเป็น 120](portfolio-insurance.html#tipp) · แหล่งแนวคิด: พิมพ์ น. 15–16 / PDF 42–43

</section>

<section class="glossary-term" id="constant-mix">

### Constant Mix · การปรับกลับสู่สัดส่วนคงที่

กฎซื้อขายเพื่อให้พอร์ตกลับมามีสัดส่วนเป้าหมาย เช่น สินทรัพย์เสี่ยง 60% และสินทรัพย์ปลอดความเสี่ยง 40% ในแต่ละรอบ ต่างจากการจัดสัดส่วน 60/40 เพียงครั้งแรกแล้วถือโดยไม่ปรับ

[ดูตัวเปรียบเทียบในเครื่องมือ CPPI](portfolio-insurance.html#gap-risk) · นิยามประกอบเครื่องมือของบทเรียน

</section>

</section>

<section class="glossary-group" id="group-models">

## แบบจำลองและการตัดสินใจ

<section class="glossary-term" id="gbm">

### GBM · Geometric Brownian Motion

แบบจำลองการเคลื่อนที่ของราคาที่รักษาระดับราคาให้เป็นบวก ภายใต้ Drift และ Volatility คงที่ Log return ของช่วงเวลาที่กำหนดเป็น Normal และราคาปลายช่วงเป็น Lognormal ไม่ได้รวมการกระโดดของราคาแบบฉับพลันไว้ในกระบวนการต่อเนื่องพื้นฐาน

[ดูวิธีจำลองในวิทยานิพนธ์](portfolio-insurance.html#study-design) · แหล่งแนวคิด: พิมพ์ น. 48–49, 85 / PDF 75–76, 112

</section>

<section class="glossary-term" id="sampling-error">

### Sampling error · ความคลาดเคลื่อนจากการสุ่ม

ความต่างของค่าประมาณที่เกิดจากใช้ตัวอย่างสุ่มจำนวนจำกัด แม้ใช้แบบจำลองและพารามิเตอร์เดิม การเพิ่มจำนวนเส้นทางช่วยลดส่วนนี้ได้ แต่ไม่ได้แก้การเลือกแบบจำลองที่ไม่ตรงกับตลาด

[อ่านข้อจำกัดของผลจำลอง](portfolio-insurance.html#limitations) · คำอธิบายประกอบการอ่านงานที่บทเรียนเพิ่ม

</section>

<section class="glossary-term" id="model-risk">

### Model risk · ความเสี่ยงจากแบบจำลอง

ความเสี่ยงที่สมมติฐาน โครงสร้าง พารามิเตอร์ หรือการนำแบบจำลองไปใช้ไม่เหมาะกับสิ่งที่ต้องการประเมิน เช่น ใช้แบบราคาต่อเนื่องเพื่อสรุปว่ากฎซื้อขายรับมือการกระโดดของราคาได้เสมอ

[อ่านข้อจำกัดของผลจำลอง](portfolio-insurance.html#limitations) · คำอธิบายประกอบการอ่านงานที่บทเรียนเพิ่ม

</section>

<section class="glossary-term" id="expected-utility">

### Expected utility · อรรถประโยชน์คาดหมาย

ค่าเฉลี่ยของ Utility ที่ได้จากผลลัพธ์หลายแบบ ถ้า $W_T$ เป็นความมั่งคั่งปลายทาง เกณฑ์คือ $\mathbb{E}[U(W_T)]$ รูปร่างของ $U$ สะท้อนว่าผู้ลงทุนให้คุณค่ากับความมั่งคั่งและความเสี่ยงอย่างไร

[อ่าน EUT กับ CPT](portfolio-insurance.html#eut-cpt) · แหล่งแนวคิด: พิมพ์ น. 43–47, 86–89 / PDF 70–74, 113–116

</section>

<section class="glossary-term" id="loss-aversion">

### Loss aversion · ความไวต่อการสูญเสีย

การให้ผลกระทบด้านลบแก่การขาดทุนมากกว่าผลกระทบด้านบวกจากกำไรขนาดเท่ากัน เมื่อวัดจากจุดอ้างอิงเดียวกัน เป็นคนละแนวคิดกับการไม่ชอบความผันผวนโดยรวม

[อ่าน Value function ใน CPT](portfolio-insurance.html#eut-cpt) · แหล่งแนวคิด: พิมพ์ น. 81–84 / PDF 108–111

</section>

<section class="glossary-term" id="reference-point">

### Reference point · จุดอ้างอิง

ฐานที่ใช้ตัดสินว่าผลลัพธ์หนึ่งเป็นกำไรหรือขาดทุน ในตาราง CPT ของวิทยานิพนธ์ใช้เงินตั้งต้น 100 หรือผลตอบแทน 0% การปรับ Floor ไม่ได้หมายความว่าจุดอ้างอิงต้องเปลี่ยนตาม

[ดูความต่างระหว่าง Floor กับจุดอ้างอิง](portfolio-insurance.html#eut-cpt) · แหล่งแนวคิด: พิมพ์ น. 84, 90, 95 / PDF 111, 117, 122

</section>

<section class="glossary-term" id="cpt">

### CPT · Cumulative Prospect Theory

กรอบอธิบายการตัดสินใจที่ประเมินกำไรและขาดทุนเทียบจุดอ้างอิง ร่วมกับน้ำหนักการตัดสินใจที่คำนวณจากความน่าจะเป็นสะสม คะแนน CPT จึงมีความหมายตาม Value function และน้ำหนักที่เลือก ไม่ใช่ผลตอบแทนจากการลงทุน

[อ่านตัวอย่างคะแนนจากงานวิจัย](portfolio-insurance.html#findings) · แหล่งแนวคิด: พิมพ์ น. 83–91 / PDF 110–118

</section>

</section>
