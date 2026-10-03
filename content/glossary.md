---
title: คำศัพท์
description: คำศัพท์และสัญลักษณ์เรื่องการป้องกันพอร์ต พร้อมลิงก์กลับไปยังตัวอย่างในบทเรียน
---

# คำศัพท์

หน้านี้รวมคำที่ใช้ในหนังสือ แต่ละคำมีนิยามสั้นและลิงก์กลับไปยังบทเรียน คำด้านความเสี่ยงอ้างอิง[บทความเสี่ยงในการลงทุน](risk.html#references) ส่วนเลขหน้าของบท Portfolio Insurance อ้างถึง[วิทยานิพนธ์ da Silva (2018)](portfolio-insurance.html#references)

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

[เปรียบเทียบ Drawdown ของเส้นทางที่จบเท่ากัน](risk.html#drawdown)

</section>

<section class="glossary-term" id="shortfall">

### Shortfall · เงินที่ขาดจากเป้าหมาย

จำนวนเงินที่ต่ำกว่า Floor เช่น ณ วันครบกำหนด $L_T=\max(F_T-V_T,0)$ ถ้าพอร์ตอยู่เหนือหรือเท่ากับ Floor จะเป็นศูนย์ ความถี่ของการเกิด Shortfall กับขนาดเงินที่ขาดเมื่อเกิดเป็นคนละข้อมูล ต้องอ่านทั้งสองอย่าง

[ดูตัวอย่างห้าผลลัพธ์ที่ความถี่หลุดเท่ากันแต่เสียหายต่างกัน](portfolio-insurance.html#how-to-compare)

</section>

<section class="glossary-term" id="turnover">

### Turnover · ขนาดรวมของการซื้อขายเพื่อปรับพอร์ต

ในห้องทดลอง Portfolio Insurance นับผลรวมจำนวนเงินฝั่งสินทรัพย์เสี่ยงที่ซื้อหรือขายหลังเดือนที่ 1–11 ไม่รวมการจัดพอร์ตครั้งแรกและไม่มีการซื้อขาย ณ วันครบกำหนด เป็นหน่วยเงิน ไม่ใช่ค่าธรรมเนียมและไม่ใช่เปอร์เซ็นต์ ความหมายของ Turnover อาจต่างกันระหว่างรายงาน จึงต้องตรวจวิธีนับก่อนเทียบ

[ดูตัวอย่างรายการซื้อขายและต้นทุน](portfolio-insurance.html#strategies) ส่วน[บททดสอบ Diversification](diversification-backtest.html) แสดงมูลค่าซื้อรวมขายเทียบกับทุนก่อนซื้อขาย และระบุการคิดต้นทุนทั้งสองฝั่ง

</section>

<section class="glossary-term" id="high-water-mark">

### High-water mark · มูลค่าสูงสุดของพอร์ตที่เคยสังเกต

ถ้าพอร์ตมีมูลค่า $V_t$ จะได้ $H_t=\max_{s\leq t}V_s$ โดยระบุชุดเวลาที่สังเกตด้วย ใช้วัด Drawdown และตั้ง Floor แบบ Ratchet จุดสูงสุดนี้เป็นของพอร์ตที่กำลังประเมิน ไม่จำเป็นต้องตรงกับจุดสูงสุดของหุ้นหรือดัชนีอ้างอิง

[ดูตัวอย่าง TIPP ที่ไม่ลด Floor ตามพอร์ตขาลง](portfolio-insurance.html#tipp)

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

[เรียนสูตรและตัวอย่าง CPPI](cppi-dynamic-allocation.html#cppi-basics) · [เปรียบเทียบกับการซื้อ Option](portfolio-insurance.html#cppi-rule)

</section>

<section class="glossary-term" id="cushion">

### Cushion · ส่วนต่างเหนือ Floor

ผลต่าง $C_t=V_t-F_t$ ระหว่างมูลค่าพอร์ตกับ Floor ณ เวลาเดียวกัน วัดเป็นหน่วยเงินเดียวกับพอร์ต ใน CPPI เป็นฐานที่นำไปคูณ Multiplier เพื่อกำหนดเงินลงทุนเสี่ยง

[คำนวณจากพอร์ต 1,000 บาทและ Floor 800 บาท](cppi-dynamic-allocation.html#cppi-basics) · [ทดลองเปลี่ยน Floor](portfolio-insurance.html#cppi-example)

</section>

<section class="glossary-term" id="multiplier">

### Multiplier · ตัวคูณ Cushion

พารามิเตอร์ $m$ ที่แปลง Cushion เป็นเงินลงทุนในสินทรัพย์เสี่ยงก่อนใช้ข้อจำกัดอื่น ไม่มีหน่วย $m=3$ หมายถึงสามเท่าของ Cushion ไม่ใช่สามเท่าของมูลค่าพอร์ต

[ดูกฎและเพดานเงินลงทุนเสี่ยง](cppi-dynamic-allocation.html#cppi-basics) · [ต่อยอดเป็นตัวคูณที่ปรับได้](portfolio-insurance.html#variable-multiplier)

</section>

<section class="glossary-term" id="rebalancing">

### Rebalancing · การปรับสัดส่วนพอร์ต

การซื้อขายเพื่อให้จำนวนเงินหรือสัดส่วนสินทรัพย์ตรงกับกฎหลังราคาและมูลค่าพอร์ตเปลี่ยน การกำหนดเป้าหมายต่อเนื่องในสูตรกับการซื้อขายจริงเป็นรอบให้ผลต่างกันได้

[ดูการปรับพอร์ตทีละเดือน](cppi-dynamic-allocation.html#cppi-worked-example) · [ทดลองปรับพอร์ต](portfolio-insurance.html#cppi-example)

</section>

<section class="glossary-term" id="gap-risk">

### Gap risk · ความเสี่ยงที่ราคาผ่านเกณฑ์ก่อนปรับได้ทัน

ความเสี่ยงที่ราคาหรือมูลค่าพอร์ตเคลื่อนที่ผ่านระดับป้องกันก่อนจะลดการถือสินทรัพย์เสี่ยงได้ การขายหลังจากหลุดเกณฑ์ไม่ได้ทำให้พอร์ตกลับไปมีมูลค่าเท่าเกณฑ์โดยอัตโนมัติ

[เรียน Gap risk จากตัวเลข](cppi-dynamic-allocation.html#cppi-gap-risk) · [ต่อยอดเมื่อมีดอกเบี้ยและเพดาน Exposure](portfolio-insurance.html#gap-risk)

</section>

<section class="glossary-term" id="cash-lock">

### Cash lock · พอร์ตติดอยู่ในสินทรัพย์ปลอดความเสี่ยง

ภาวะที่ Cushion หมดจนกฎป้องกันให้เงินลงทุนในสินทรัพย์เสี่ยงลดเหลือศูนย์ และกลยุทธ์ไม่กลับเข้าตลาดในช่วงที่เหลือ จึงอาจไม่มีส่วนร่วมกับการฟื้นตัวของตลาด ต่างจากการเลือก Multiplier เป็นศูนย์ตั้งแต่ต้น

[ดูเหตุใดตลาดฟื้นแต่พอร์ตไม่ตาม](portfolio-insurance.html#gap-risk) · แหล่งแนวคิด: พิมพ์ น. 14 / PDF 41

</section>

<section class="glossary-term" id="variable-multiplier">

### Variable-Multiplier Portfolio Insurance · การป้องกันพอร์ตด้วยตัวคูณที่ปรับได้

แนวทาง Proportional Portfolio Insurance ที่ให้ $m_t$ เปลี่ยนตามกฎและข้อมูลความเสี่ยงที่มี ณ เวลาจัดพอร์ต แทนการตรึง Multiplier เช่น ลดตัวคูณเมื่อความผันผวนที่ประเมินสูงขึ้น เงินเสี่ยงยังขึ้นกับ Cushion และเพดานที่กำหนด วิธีนี้ยังมีความเสี่ยงจากการประมาณค่า ราคากระโดด และต้นทุนซื้อขาย; ไม่ใช่การรับประกัน Floor

[ดูสูตรและตัวอย่างเทียบ CPPI คงที่](portfolio-insurance.html#variable-multiplier) · [แหล่งวิจัยประกอบ](portfolio-insurance.html#variable-multiplier-source)

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

<section class="glossary-term" id="ratchet">

### Ratchet · กฎยกระดับป้องกันโดยไม่ลดกลับ

กฎอัปเดต Floor ให้สูงขึ้นเมื่อเข้าเงื่อนไข เช่น ตัวอย่าง TIPP ดอกเบี้ย 0% ของบทนี้ใช้ 90% ของ High-water mark และไม่ลด Floor ตามมูลค่าพอร์ตที่ถอยลง การยกเป้าหมายไม่สร้างเงินเพิ่มและยังต้องซื้อขายได้ทันจึงจะรักษาเป้าหมายได้

[คำนวณ Floor และเงินเสี่ยงของ TIPP หลายรอบ](portfolio-insurance.html#tipp)

</section>

<section class="glossary-term" id="put-call-parity">

### Put–call parity · ความสัมพันธ์ราคาระหว่าง Put กับ Call

สำหรับ European options ที่อ้างอิงสินทรัพย์เดียวกัน ราคาใช้สิทธิและวันครบกำหนดเดียวกัน เมื่อไม่มีเงินปันผลและใช้ดอกเบี้ยคงที่ เงื่อนไขไม่มี Arbitrage ให้ $S_0+P_0=Ke^{-rT}+C_0$ เพราะสองโครงสร้างให้กระแสเงินปลายทางเท่ากัน ต้องจับคู่จำนวนหน่วยและกระแสเงินให้ตรงก่อนใช้

[พิสูจน์จาก Payoff แล้วจัดงบเริ่มต้น 100](portfolio-insurance.html#option-budget)

</section>

<section class="glossary-term" id="self-financing">

### Self-financing · ปรับพอร์ตโดยใช้เงินภายในพอร์ตเอง

การเพิ่มสินทรัพย์ด้านหนึ่งใช้เงินจากการลดอีกด้าน ไม่มีการเติมหรือถอนเงินจากภายนอก ในตัวอย่างที่ไม่มีต้นทุน มูลค่าก่อนและหลังซื้อขาย ณ ราคาเดียวกันเท่ากัน ถ้ามีค่าซื้อขาย เงินจ่ายนั้นต้องออกจากพอร์ตและถูกหักในการคำนวณมูลค่าด้วย

[ดูบัญชีเงินก่อนและหลัง Rebalancing](portfolio-insurance.html#cppi-rule)

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

<section class="glossary-term" id="risk-aversion">

### Risk aversion · ความหลีกเลี่ยงความเสี่ยงในเกณฑ์การตัดสินใจ

ใน EUT ฟังก์ชัน Utility ที่เพิ่มขึ้นและโค้งเว้าทำให้เงินแน่นอนเท่าค่าเฉลี่ยของทางเลือกเสี่ยงมี Utility ไม่ต่ำกว่าทางเลือกเสี่ยงนั้น ความหลีกเลี่ยงความเสี่ยงไม่ได้หมายถึงปฏิเสธสินทรัพย์เสี่ยงทุกชนิด และต่างจาก Loss aversion ที่ให้คุณค่าขาดทุนกับกำไรเทียบจุดอ้างอิงไม่เท่ากัน

[คำนวณ Expected utility และ Certainty equivalent](portfolio-insurance.html#eut-cpt)

</section>

<section class="glossary-term" id="certainty-equivalent">

### Certainty equivalent · เงินแน่นอนที่ให้คุณค่าเท่าทางเลือกเสี่ยง

จำนวนเงินแน่นอน $CE$ ที่ทำให้ $U(CE)=\mathbb E[U(W)]$ ภายใต้ Utility ที่กำหนด สำหรับผู้หลีกเลี่ยงความเสี่ยง CE ไม่เกินเงินคาดหมายของทางเลือกเสี่ยง ค่านี้แปลงคะแนน Utility กลับเป็นจำนวนเงินเพื่อช่วยตีความ ไม่ใช่ราคา Option โดยอัตโนมัติ

[ดูตัวอย่างเงินปลายทาง 50/170 และ Log utility](portfolio-insurance.html#eut-cpt)

</section>

<section class="glossary-term" id="probability-weighting">

### Probability weighting · การให้น้ำหนักความน่าจะเป็นในการตัดสินใจ

ฟังก์ชันแปลงความน่าจะเป็นให้เป็นน้ำหนักสำหรับประเมินทางเลือก ใน CPT ต้องเรียงผลลัพธ์แล้วหาผลต่างของน้ำหนักความน่าจะเป็นสะสม น้ำหนักนี้สะท้อนการตัดสินใจ ไม่ใช่ความน่าจะเป็นเกิดจริงที่แก้ใหม่

[ดูตัวอย่าง Cumulative weighting](portfolio-insurance.html#eut-cpt)

</section>

<section class="glossary-term" id="risk-capacity">

### Risk capacity · ความสามารถทางการเงินในการรับความเสี่ยง

ความสามารถรับผลขาดทุนโดยยังรองรับเป้าหมายและภาระทางการเงินได้ ขึ้นกับกำหนดใช้เงิน เงินสำรอง รายรับ และภาระ ไม่ใช่เพียงความรู้สึกว่ายอมรับราคาผันผวนได้มากแค่ไหน

[เทียบความสามารถกับความเต็มใจรับความเสี่ยง](portfolio-insurance.html#robo-advisors)

</section>

<section class="glossary-term" id="risk-tolerance">

### Risk tolerance · ความเต็มใจยอมรับความเสี่ยง

ความเต็มใจยอมรับความไม่แน่นอนและการขาดทุนในการลงทุน ต้องพิจารณาร่วมกับความสามารถทางการเงินในการรับผลขาดทุน ผู้ลงทุนอาจยอมรับความผันผวนทางความรู้สึกได้ แต่ยังมีข้อจำกัดจากเงินที่ต้องใช้ในเวลาใกล้กัน

[ดูตัวอย่างผู้ลงทุนที่มีภาระใช้เงินต่างกัน](portfolio-insurance.html#robo-advisors)

</section>

</section>

<section class="glossary-group" id="group-risk">

## ความเสี่ยงและตัววัด

<section class="glossary-term" id="investment-risk">

### Investment risk · ความเสี่ยงในการลงทุน

ความไม่แน่นอนของผลลัพธ์ทางการเงิน โดยเฉพาะโอกาสและขนาดของผลลัพธ์ที่ไม่ต้องการ ต้องกำหนดพอร์ต ช่วงเวลา หน่วย และจุดอ้างอิงก่อนเลือกตัววัด ความผันผวนเป็นเพียงตัววัดหนึ่ง

[เริ่มจากความหมายของความเสี่ยง](risk.html#risk-definition)

</section>

<section class="glossary-term" id="volatility">

### Volatility · ความผันผวน

การกระจายตัวของผลตอบแทนที่มักวัดด้วย Standard deviation รวมทั้งค่าที่สูงกว่าและต่ำกว่าค่าเฉลี่ย บทความเสี่ยงใช้ Sample standard deviation ตัวหาร $n-1$ และรายงานความถี่ของข้อมูลเสมอ

[คำนวณความผันผวนรายเดือน](returns.html#risk-volatility)

</section>

<section class="glossary-term" id="downside-deviation">

### Downside deviation · การกระจายตัวต่ำกว่าเกณฑ์

รากที่สองของค่าเฉลี่ยกำลังสองของส่วนที่ผลตอบแทนต่ำกว่าเกณฑ์ บทนี้หารด้วยจำนวนช่วงทั้งหมด และกำหนดเกณฑ์ในความถี่เดียวกับผลตอบแทน จึงต้องตรวจนิยามก่อนเทียบคนละโปรแกรม

[เทียบเกณฑ์และตัวหารของ Downside deviation](extreme-risk.html#downside-measures)

</section>

<section class="glossary-term" id="covariance">

### Covariance · ความแปรปรวนร่วม

ค่าเฉลี่ยของผลคูณระหว่างการเบี่ยงเบนจากค่าเฉลี่ยของตัวแปรสองตัว ใช้อธิบายว่าสินทรัพย์เคลื่อนไหวร่วมกันอย่างไร และเป็นส่วนหนึ่งของสูตร Variance ของพอร์ต หน่วยขึ้นกับตัวแปรทั้งสอง

[คำนวณ Covariance ทีละขั้น](portfolio-basics.html#covariance) · [ใช้คำนวณความเสี่ยงพอร์ต](portfolio-basics.html#portfolio-variance)

</section>

<section class="glossary-term" id="correlation">

### Correlation · สหสัมพันธ์

Covariance ที่หารด้วยผลคูณ Standard deviation ของตัวแปรทั้งสองเมื่อค่านี้ไม่เป็นศูนย์ อยู่ระหว่าง −1 กับ 1 และไม่มีหน่วย วัดความสัมพันธ์เชิงเส้น; ค่าเป็นศูนย์ไม่ได้รับรองความเป็นอิสระ

[เปลี่ยน Correlation แล้วเทียบพอร์ต 50/50](risk.html#diversification)

</section>

<section class="glossary-term" id="diversification">

### Diversification · การกระจายความเสี่ยง

การผสมสถานะที่มีโครงสร้างการเคลื่อนไหวต่างกันเพื่อลดความเสี่ยงรวมในมิติที่สนใจ ต้องดูขนาดสถานะและความสัมพันธ์ร่วมด้วย การถือหลายชื่อที่รับแรงกระทบเดียวกันอาจยังมีความเสี่ยงกระจุกตัว

[อ่านความเสี่ยงที่เกิดจากการเคลื่อนไหวร่วมกัน](risk.html#diversification)

</section>

<section class="glossary-term" id="value-at-risk">

### Value at Risk (VaR) · ควอนไทล์ของผลขาดทุน

เส้นแบ่งของการแจกแจงผลขาดทุน ณ ระดับความน่าจะเป็นและช่วงเวลาที่กำหนด ต้องบอกสกุลเงินและแบบจำลองด้วย VaR ไม่ใช่ขาดทุนสูงสุด; ตัวอย่างข้อมูลจำกัดในบทใช้ Inverse empirical CDF

[อ่านนิยามและตัวอย่าง Historical VaR](extreme-risk.html#historical-loss-quantiles)

</section>

<section class="glossary-term" id="expected-shortfall">

### Expected Shortfall (ES) · ค่าเฉลี่ยผลขาดทุนส่วนที่แย่ที่สุด

ค่าเฉลี่ยของผลขาดทุนในส่วนหางที่แย่ที่สุดตามสัดส่วนที่กำหนด เช่น ES 95% เฉลี่ยส่วนที่แย่ที่สุด 5% เมื่อมีค่าซ้ำตรง VaR ต้องจัดน้ำหนักให้ครอบคลุมมวลความน่าจะเป็น 5% พอดี; บางแหล่งใช้ชื่อ CVaR

[คำนวณ Expected Shortfall](extreme-risk.html#expected-shortfall-weights) · [ทดลอง VaR เท่ากันแต่ ES ต่างกัน](risk.html#expected-shortfall)

</section>

<section class="glossary-term" id="ewma">

### EWMA · Exponentially Weighted Moving Average

วิธีให้น้ำหนักข้อมูลย้อนหลังลดลงแบบเรขาคณิต ในแบบจำลอง Variance น้ำหนัก $\lambda$ คูณค่าประมาณเดิม และ $1-\lambda$ คูณผลตอบแทนส่วนที่ไม่คาดหมายยกกำลังสอง ใช้ข้อมูลที่สังเกตแล้วเพื่อประมาณช่วงถัดไป

[ทดลองน้ำหนักข้อมูลหลัง Shock](risk.html#ewma)

</section>

<section class="glossary-term" id="conditional-volatility">

### Conditional volatility · ความผันผวนตามข้อมูลที่มี

ความผันผวนที่ประมาณโดยมีเงื่อนไขจากข้อมูล ณ เวลาหนึ่ง จึงอาจเปลี่ยนตามสถานการณ์ ต่างจากการรวมข้อมูลทุกช่วงแล้วรายงานค่าการกระจายตัวเดียว

[อ่านความผันผวนตามเวลา](risk.html#ewma)

</section>

<section class="glossary-term" id="risk-factor">

### Risk factor · ปัจจัยเสี่ยง

ตัวแปรที่การเปลี่ยนแปลงส่งผลต่อมูลค่าสถานะ เช่น ราคาหุ้น อัตราผลตอบแทนพันธบัตร หรือค่าเงิน ต้องแยกตัวปัจจัย ขนาดสถานะ และความไวของมูลค่าต่อปัจจัยออกจากตัววัดความเสี่ยงรวม

[แยกปัจจัยเสี่ยง Exposure และตัววัด](risk.html#theory-map)

</section>

<section class="glossary-term" id="systematic-risk">

### Systematic risk · ความเสี่ยงร่วมกับตลาด

ความเสี่ยงที่กระจายออกไม่ได้ด้วยการเพิ่มจำนวนหลักทรัพย์ในกรอบ CAPM และเกี่ยวข้องกับพอร์ตตลาด แบบจำลองเชื่อมผลตอบแทนคาดหวังส่วนเกินกับ Beta; ความสัมพันธ์นี้ไม่รับประกันผลตอบแทนที่จะเกิดจริง

[อ่านที่มาของ CAPM](risk.html#risk-history)

</section>

</section>

<section class="glossary-group" id="group-portfolio-construction">

## การสร้างพอร์ตและค่าประมาณ

<section class="glossary-term" id="portfolio-weight">

### Portfolio weight · น้ำหนักพอร์ต

มูลค่าเงินที่ลงทุนในสินทรัพย์หนึ่งหารด้วยมูลค่าพอร์ตรวม ณ เวลาเดียวกัน ใช้น้ำหนักต้นงวดคูณผลตอบแทนของงวดนั้นเมื่อไม่มีซื้อขายหรือฝากถอนระหว่างงวด น้ำหนักอาจเปลี่ยนเองเมื่อราคาสินทรัพย์เปลี่ยน

[คำนวณจากเงิน 10,000 บาท](portfolio-basics.html#portfolio-weights)

</section>

<section class="glossary-term" id="efficient-frontier">

### Efficient frontier · ขอบพอร์ตที่มีประสิทธิภาพ

พอร์ตที่ไม่มีพอร์ตอื่นในชุดทางเลือกให้ผลตอบแทนคาดหมายสูงขึ้นโดยไม่เพิ่ม variance หรือให้ variance ต่ำลงโดยไม่ลดผลตอบแทนคาดหมาย ขอบนี้ขึ้นกับพารามิเตอร์และข้อจำกัดที่ใส่ในแบบจำลอง ส่วนล่างของเส้น minimum-variance locus ไม่ใช่ efficient frontier

[สร้างขอบพอร์ตจากสินทรัพย์สามตัว](efficient-frontier.html#gmv-efficient-branch)

</section>

<section class="glossary-term" id="gmv">

### GMV · Global Minimum Variance

พอร์ตที่มี variance ต่ำสุดภายใต้ข้อจำกัดที่กำหนด โดยไม่ตั้งเป้าผลตอบแทน น้ำหนักจึงไม่ต้องใช้ค่าประมาณ expected return แต่ยังขึ้นกับ covariance matrix ที่อาจประมาณผิดได้

[เปรียบเทียบ GMV, MSR และ Equal Weight](portfolio-estimation.html#gmv-equal-weight)

</section>

<section class="glossary-term" id="msr">

### MSR · Maximum Sharpe Ratio

พอร์ตที่ทำให้ผลตอบแทนคาดหมายส่วนเกินจากอัตราปลอดความเสี่ยงต่อหน่วย SD สูงสุดในชุดพอร์ตที่อนุญาต ต้องใช้ mean, covariance และ risk-free rate บนหน่วยเวลาที่สอดคล้องกัน ค่าที่เหมาะที่สุดตามข้อมูลเข้าอาจไม่ให้ Sharpe สูงสุดในอนาคต

[คำนวณพอร์ต MSR](portfolio-estimation.html#maximum-sharpe)

</section>

<section class="glossary-term" id="capital-allocation-line">

### Capital Allocation Line · เส้นการผสมกับสินทรัพย์ปลอดความเสี่ยง

เส้นแสดง expected return และ SD เมื่อผสมพอร์ตเสี่ยงหนึ่งชุดกับสินทรัพย์ปลอดความเสี่ยงในสัดส่วนต่าง ๆ ความชันเท่ากับ Sharpe ratio ของพอร์ตเสี่ยง ภายใต้เงื่อนไขการลงทุนและอัตราดอกเบี้ยที่ใช้ เส้นที่อ้างถึงพอร์ตตลาดในกรอบดุลยภาพ CAPM เรียกว่า Capital Market Line

[อ่าน CAL และ CML พร้อมสมมติฐาน](portfolio-estimation.html#cal-cml)

</section>

<section class="glossary-term" id="estimation-error">

### Estimation error · ความคลาดเคลื่อนของค่าประมาณ

ความต่างระหว่างพารามิเตอร์ที่ประมาณจากข้อมูลกับค่าที่ต้องการรู้ เช่น expected return และ covariance การแก้ optimization ได้แม่นตามตัวเลขเข้าไม่ได้ทำให้ค่าประมาณเหล่านั้นถูกต้องขึ้น

[ทดลองเปลี่ยนค่าประมาณแล้วดูน้ำหนักพอร์ต](portfolio-estimation.html#estimation-error)

</section>

<section class="glossary-term" id="look-ahead-bias">

### Look-ahead bias · การใช้ข้อมูลอนาคตในการทดสอบย้อนหลัง

ความเอนเอียงที่เกิดเมื่อการตัดสินใจ ณ เวลาหนึ่งใช้ข้อมูลซึ่งยังไม่ทราบในเวลานั้น เช่น นำน้ำหนักจากมูลค่าตลาดปลายเดือนมาคูณผลตอบแทนของเดือนเดียวกัน ต้องตรวจวันประกาศและเวลาที่ข้อมูลใช้งานได้ รวมถึงเวลาตัดสินใจและซื้อขาย

[เปรียบเทียบน้ำหนักต้นงวดกับปลายงวด](diversification-limits.html#weight-timing)

</section>

<section class="glossary-term" id="monte-carlo">

### Monte Carlo · การคำนวณด้วยการสุ่มซ้ำ

สร้างผลลัพธ์จำนวนมากจากแบบจำลองและสมมติฐานที่กำหนด แล้วประมาณค่าเฉลี่ย ความถี่ หรือการแจกแจง การเพิ่มจำนวนตัวอย่างช่วยลดความคลาดเคลื่อนจากการสุ่ม แต่ไม่ได้ยืนยันว่าแบบจำลองอธิบายตลาดจริงได้

[จำลอง GBM และประเมิน CPPI](monte-carlo.html#gbm-python)

</section>

</section>

<section class="glossary-group" id="group-asset-liability">

## เงินที่ต้องใช้และพอร์ตที่รองรับ

<section class="glossary-term" id="present-value">

### Present value · มูลค่าปัจจุบัน

มูลค่าวันนี้ของเงินที่จะได้รับหรือจ่ายในอนาคต โดยใช้ตัวคูณคิดลดที่ตรงกับกำหนดเวลา สกุลเงิน และประเภทกระแสเงิน การประเมินภาระ nominal คงที่ไม่ควรใช้อัตราผลตอบแทนหุ้นที่คาดหวังแทนอัตราคิดลดโดยไม่มีเหตุผลรองรับ

[คิดลดเงินที่ต้องจ่ายสามวัน](asset-liability.html#present-value)

</section>

<section class="glossary-term" id="funding-ratio">

### Funding ratio · อัตราส่วนสินทรัพย์ต่อมูลค่าภาระ

มูลค่าสินทรัพย์หารด้วยมูลค่าปัจจุบันของภาระ ณ วันเดียวกัน ค่า 1 หมายถึงมีมูลค่าเท่ากันตามวิธีประเมินที่ใช้ อัตราส่วนยังเปลี่ยนได้จากราคาสินทรัพย์ อัตราคิดลด และการปรับภาระ จึงต้องระบุทั้งวันที่และสมมติฐาน

[คำนวณและเปลี่ยนอัตราคิดลด](asset-liability.html#funding-ratio)

</section>

<section class="glossary-term" id="zero-coupon-bond">

### Zero-coupon bond · พันธบัตรไม่มีคูปองระหว่างทาง

ตราสารที่จ่ายเงินก้อนเดียวเมื่อครบกำหนด จับคู่กับภาระจำนวนเงินคงที่ในวันเดียวกันได้ในแบบจำลองที่ไม่มีการผิดนัด หากขายก่อนวันครบกำหนด ราคายังอาจขึ้นลงตามอัตราดอกเบี้ย

[สร้างพอร์ตที่จ่ายเงินตรงกับเป้าหมาย](asset-liability.html#goal-hedging-portfolio)

</section>

<section class="glossary-term" id="duration">

### Duration · เวลาเฉลี่ยถ่วงน้ำหนักและความไวต่อ Yield

Macaulay duration คือเวลาเฉลี่ยของ cash flow ถ่วงน้ำหนักด้วยสัดส่วนมูลค่าปัจจุบัน ส่วน modified duration ใช้ประมาณการเปลี่ยนแปลงราคาต่อการเปลี่ยน yield ขนาดเล็ก ต้องจับคู่ทั้งมูลค่าและความไวหากต้องการให้สินทรัพย์รองรับภาระภายใต้การเลื่อนเส้น yield ที่สมมติ

[คำนวณ duration และจับคู่ภาระห้าปี](bonds-duration.html#duration-matching)

</section>

<section class="glossary-term" id="cir">

### CIR · แบบจำลองอัตราดอกเบี้ย Cox–Ingersoll–Ross

แบบจำลอง short rate ที่มีแรงดึงเข้าหาระดับระยะยาวและขนาดความผันผวนแปรตามรากที่สองของอัตราดอกเบี้ย ต้องแยกพารามิเตอร์สำหรับจำลองสถานการณ์จริงกับพารามิเตอร์สำหรับคิดราคา และตรวจวิธีคำนวณเป็นช่วงเวลาซึ่งอาจมีข้อจำกัดต่างจากสมการต่อเนื่อง

[อ่าน short rate และการคิดราคา ZCB](interest-rate-models.html#cir-zero-coupon-price)

</section>

<section class="glossary-term" id="psp">

### PSP · Performance-Seeking Portfolio

ส่วนพอร์ตที่รับความเสี่ยงเพื่อหาโอกาสเติบโต เช่น พอร์ตหุ้นที่กระจายการลงทุน การกำหนดบทบาทว่า PSP ไม่ได้ระบุว่าต้องเป็นหุ้นทั้งหมด และไม่ได้รับรองผลตอบแทนที่จะเกิดขึ้น

[แยกหน้าที่ PSP และ GHP](asset-liability.html#psp-ghp)

</section>

<section class="glossary-term" id="ghp">

### GHP · Goal-Hedging Portfolio

พอร์ตที่ออกแบบให้มูลค่าหรือกระแสเงินเคลื่อนไหวสอดคล้องกับเป้าหมายที่ต้องรองรับ การเลือกสินทรัพย์ขึ้นกับจำนวนเงิน วันจ่าย เงินเฟ้อ และสกุลเงินของเป้าหมาย เงินสดอาจไม่ใช่สินทรัพย์ที่ลดความเสี่ยงต่อเป้าหมายได้ดีที่สุด

[เริ่มจาก cash flow ของเป้าหมาย](asset-liability.html#goal-hedging-portfolio)

</section>

<section class="glossary-term" id="glidepath">

### Glidepath · แผนเปลี่ยนสัดส่วนตามเวลา

กฎกำหนดน้ำหนักพอร์ตตามเวลาที่เหลือ เช่น ลดสัดส่วนหุ้นเมื่อใกล้วันใช้เงิน กฎที่ขึ้นกับเวลาเพียงอย่างเดียวไม่ได้ตอบสนองต่อ funding ratio หรือความเปลี่ยนแปลงของเป้าหมาย จึงยังเกิดเงินขาดได้

[เปรียบเทียบ Fixed Mix, Glidepath และ Dynamic Allocation](goal-based-allocation.html#glide-path)

</section>

</section>

<section class="glossary-group" id="group-factors">

## ปัจจัย สไตล์ และ Benchmark

<section class="glossary-term" id="capm">

### CAPM · Capital Asset Pricing Model

แบบจำลองดุลยภาพที่เชื่อมผลตอบแทนคาดหวังส่วนเกินกับ market beta ภายใต้ข้อสมมติ ค่า alpha/beta จากการ fit ข้อมูลย้อนหลังเป็นค่าประมาณที่ต้องแยกจากข้ออ้างเรื่องผลตอบแทนคาดหวัง

[อ่านข้อสมมติและคำนวณ expected return](factor-investing.html#capm-pricing)

</section>

<section class="glossary-term" id="beta">

### Beta / Factor loading · ความไวต่อปัจจัย

สัมประสิทธิ์ของผลตอบแทนปัจจัยในแบบจำลอง เช่น market beta 1.2 หมายถึงเส้นที่ fit มีความชัน 1.2 ค่านี้ไม่ใช่น้ำหนักเงินจริงโดยอัตโนมัติ และ beta ศูนย์ยังอยู่ร่วมกับความเสี่ยงเฉพาะตัวได้

[คำนวณ beta จาก covariance](factor-investing.html#ols-from-scratch)

</section>

<section class="glossary-term" id="alpha">

### Alpha · ค่าคงที่ของแบบจำลองผลตอบแทน

Intercept ที่เหลือหลังใช้ปัจจัยที่เลือกอธิบายผลตอบแทนส่วนเกิน หน่วยตรงกับความถี่ข้อมูล ค่า alpha เปลี่ยนได้เมื่อเปลี่ยนแบบจำลอง ช่วงเวลา หรือข้อมูล และค่าบวกยังไม่ยืนยันฝีมือผู้จัดการ

[แยก alpha กับ residual ของแต่ละเดือน](factor-investing.html#fitted-residuals)

</section>

<section class="glossary-term" id="smb">

### SMB · Small Minus Big

ผลตอบแทนพอร์ตหุ้นเล็กลบพอร์ตหุ้นใหญ่ตามกฎสร้างปัจจัยของ Fama–French เป็น factor spread ค่า loading บวกสื่อความไวต่อ size factor ในแบบจำลอง ไม่ใช่สัดส่วนหุ้นเล็กโดยตรง

[อ่านการสร้างและตีความ SMB](multifactor-models.html)

</section>

<section class="glossary-term" id="hml">

### HML · High Minus Low

ผลตอบแทนพอร์ตที่ book-to-market สูงลบพอร์ตที่อัตราส่วนต่ำตามกฎ Fama–French ใช้แทน value factor; high/low ในชื่อนี้ไม่ได้หมายถึงราคาหุ้นต่อหน่วยสูงหรือต่ำ

[แยก book-to-market ออกจากราคาหุ้น](multifactor-models.html)

</section>

<section class="glossary-term" id="style-analysis">

### Returns-based style analysis · การประมาณสไตล์จากผลตอบแทน

หาส่วนผสมดัชนีที่อธิบายผลตอบแทนกองทุนภายใต้ข้อจำกัดน้ำหนัก เช่น long-only และรวมหนึ่ง ต้องระบุ objective และการใส่ intercept ผล fit เป็น benchmark ทางสถิติ ไม่ใช่รายชื่อ holdings ที่ตรวจพบจริง

[สร้างสมการและตรวจน้ำหนัก](style-analysis.html#style-objective)

</section>

<section class="glossary-term" id="tracking-error">

### Tracking Error · ความผันผวนของผลต่างจาก Benchmark

โดย convention ที่บทเรียนระบุ คือ SD ของ active return ในความถี่เดียวกัน บางโค้ดใช้ชื่อนี้กับรากผลรวม residual ยกกำลังสอง จึงต้องตรวจสูตรและหน่วยก่อนเทียบผล

[เทียบ TE, RMSE และค่าเฉลี่ยส่วนต่าง](style-analysis.html#tracking-error-conventions)

</section>

<section class="glossary-term" id="smart-beta">

### Smart beta · กฎเลือกหุ้นและให้น้ำหนักที่ปรับจาก Cap Weight

กลุ่มแนวทางสร้างพอร์ตตามกฎเพื่อให้ได้ exposure หรือการกระจายน้ำหนักที่ต้องการ ไม่มีสูตรเดียวที่ใช้กับทุกดัชนี ต้องตรวจการเลือกหุ้น น้ำหนัก เวลาใช้ข้อมูล และต้นทุนของแต่ละกฎ

[เลือกหุ้นก่อนกำหนดน้ำหนัก](smart-beta.html#selection-and-weighting)

</section>

</section>

<section class="glossary-group" id="group-covariance-estimation">

## การประมาณความเสี่ยง

<section class="glossary-term" id="sample-covariance">

### Sample covariance · Covariance จากตัวอย่าง

ค่าที่คำนวณจากผลคูณของผลตอบแทนที่ลบค่าเฉลี่ยแล้ว บทเรียนใช้ข้อมูลครบทุกสินทรัพย์ในงวดเดียวกันและหารด้วยจำนวนงวดลบหนึ่ง ค่านี้ยังมีความคลาดเคลื่อนจากข้อมูลที่นำมาประมาณ

[คำนวณจากตารางผลตอบแทน](covariance-estimation.html)

</section>

<section class="glossary-term" id="matrix-rank">

### Rank · จำนวนทิศทางอิสระของ Matrix

จำนวนคอลัมน์อิสระที่ matrix มีอยู่จริง สำหรับผลตอบแทน N สินทรัพย์ที่มี T งวด หลังลบค่าเฉลี่ย sample covariance มี rank ไม่เกิน min(N, T−1) ถ้า rank ต่ำกว่า N จะหา inverse ตามปกติไม่ได้

[ตรวจข้อมูลซ้ำและ covariance ที่ singular](covariance-estimation.html)

</section>

<section class="glossary-term" id="positive-semidefinite">

### Positive semidefinite · PSD

คุณสมบัติที่ทำให้ผลคูณ wᵀΣw ไม่ติดลบสำหรับเวกเตอร์ w ทุกค่า ซึ่งจำเป็นสำหรับ matrix ที่ใช้เป็น covariance ถ้าเป็นบวกเสมอสำหรับ w ที่ไม่ใช่ศูนย์ เรียก positive definite หรือ PD และมี inverse

[ตรวจ covariance ก่อนหาน้ำหนักพอร์ต](covariance-shrinkage.html)

</section>

<section class="glossary-term" id="covariance-shrinkage">

### Covariance shrinkage · การดึงค่าประมาณเข้าหา Target

การผสม sample covariance S กับ matrix เป้าหมาย F เช่น δF + (1−δ)S เมื่อ δ อยู่ระหว่างศูนย์กับหนึ่ง ลดการพึ่งค่าจากตัวอย่างเพียงชุดเดียว แต่ต้องยอมรับความคลาดเคลื่อนที่โครงสร้าง target อาจสร้างขึ้น

[ลองเปลี่ยน δ และตรวจผลต่อพอร์ต](covariance-shrinkage.html)

</section>

<section class="glossary-term" id="constant-correlation">

### Constant-correlation target · Target ที่ใช้ Correlation ร่วมค่าเดียว

Covariance matrix ที่คง variance ของแต่ละสินทรัพย์ไว้ แต่แทน correlation ระหว่างสินทรัพย์ต่างคู่ด้วยค่าเฉลี่ยร่วมค่าเดียว คำว่า constant ในที่นี้หมายถึงเหมือนกันทุกคู่ภายใน matrix นั้น; ค่าเฉลี่ยยังเปลี่ยนได้เมื่อเลื่อนช่วงข้อมูล

[สร้าง target จาก SD และ correlation](covariance-shrinkage.html)

</section>

<section class="glossary-term" id="volatility-clustering">

### Volatility clustering · ความผันผวนที่รวมตัวเป็นช่วง

ลักษณะที่ช่วงผลตอบแทนแกว่งมากมักตามด้วยช่วงที่แกว่งมาก และช่วงสงบมักตามด้วยช่วงสงบ เป็นเรื่องขนาดการเปลี่ยนแปลง ไม่ได้บอกเครื่องหมายผลตอบแทนงวดหน้า

[แยกการคาดการณ์ความเสี่ยงจากผลตอบแทน](time-varying-risk.html)

</section>

<section class="glossary-term" id="garch">

### GARCH · Generalized Autoregressive Conditional Heteroskedasticity

แบบจำลอง variance ที่มีเงื่อนไขจากข้อมูลที่ผ่านมา ใน GARCH(1,1) ค่าของงวดหน้าขึ้นกับค่าคงที่ shock ล่าสุดยกกำลังสอง และ variance ปัจจุบัน ต้องแยกพารามิเตอร์ที่ตั้งเพื่อสาธิตออกจากพารามิเตอร์ที่ประมาณจากข้อมูลจริง

[คำนวณ GARCH ทีละงวด](time-varying-risk.html)

</section>

</section>

<section class="glossary-group" id="group-expected-returns">

## ค่าคาดหวังและมุมมองผลตอบแทน

<section class="glossary-term" id="expected-return">

### Expected return · ผลตอบแทนคาดหวัง

ค่าเฉลี่ยของผลตอบแทนภายใต้การแจกแจงและข้อมูลที่กำหนด ต้องระบุช่วงเวลาและว่าเป็น total หรือ excess return ค่าเฉลี่ยจากอดีตเป็นตัวประมาณหนึ่งซึ่งอาจห่างจากค่าเฉลี่ยในอนาคต

[เริ่มจาก sample mean และความไม่แน่นอน](expected-return-estimation.html)

</section>

<section class="glossary-term" id="standard-error">

### Standard Error · ความผันผวนของตัวประมาณ

SD ของตัวประมาณเมื่อสุ่มข้อมูลซ้ำ เช่น Standard Error ของ sample mean ประมาณด้วย s/√T ภายใต้ข้อมูลอิสระจากการแจกแจงเดียวกัน เป็นความไม่แน่นอนของค่าเฉลี่ยที่ประมาณ ไม่ใช่ SD ของผลตอบแทนเดือนหน้า

[คำนวณและอ่านช่วงความเชื่อมั่น](expected-return-estimation.html)

</section>

<section class="glossary-term" id="mean-shrinkage">

### Mean shrinkage · การดึงค่าเฉลี่ยเข้าหา Target

การผสมค่าเฉลี่ยจากตัวอย่างกับค่าตั้งต้นที่กำหนด เช่น ค่าเฉลี่ยรวมของสินทรัพย์ เพื่อลดการพึ่งตัวเลขที่ประมาณแยกจากข้อมูลสั้น ๆ ต้องระบุ target และกฎให้น้ำหนัก เพราะโครงสร้างที่เลือกยังอาจสร้าง bias ได้

[ทดลองผสมค่าประมาณผลตอบแทน](expected-return-estimation.html)

</section>

<section class="glossary-term" id="prior">

### Prior · การแจกแจงก่อนรวมข้อมูลหรือ Views ชุดใหม่

การระบุสิ่งที่แบบจำลองเชื่อเกี่ยวกับพารามิเตอร์ก่อนรับข้อมูลเพิ่มเติม ใน Black–Litterman ระบุทั้งค่ากลางของ expected returns และ covariance ของความไม่แน่นอนรอบค่ากลางนั้น

[แยก prior mean ออกจากความเสี่ยงของผลตอบแทน](black-litterman.html)

</section>

<section class="glossary-term" id="posterior">

### Posterior · การแจกแจงหลังรวมข้อมูลหรือ Views

ผลการปรับ prior ด้วยข้อมูลเพิ่มเติมและแบบจำลองความคลาดเคลื่อนของข้อมูลนั้น Posterior mean เป็นค่ากลางใหม่ ส่วน posterior covariance ของค่าเฉลี่ยยังต่างจาก covariance ที่ใช้พยากรณ์ผลตอบแทน

[คำนวณ posterior ด้วยตัวอย่างหนึ่งมิติ](black-litterman.html)

</section>

<section class="glossary-term" id="implied-returns">

### Implied returns · ผลตอบแทนที่ย้อนหาได้จากพอร์ตและแบบจำลอง

Expected returns ที่ทำให้น้ำหนักอ้างอิงสอดคล้องกับเงื่อนไขความเหมาะสมในโจทย์ที่กำหนด สูตร Π = δΣw ต้องระบุ covariance, risk aversion และข้อจำกัดพอร์ต น้ำหนักเพียงอย่างเดียวไม่ได้ระบุ expected returns ได้เป็นชุดเดียว

[ย้อนจากน้ำหนักสู่ผลตอบแทน](implied-returns-views.html)

</section>

<section class="glossary-term" id="active-views">

### Active views · มุมมองเพิ่มเติมต่อผลตอบแทน

ข้อสมมติเรื่อง expected returns ที่ต้องการรวมเข้ากับ prior เช่น ค่าคาดหวังของสินทรัพย์หนึ่งตัว หรือผลต่างของพอร์ตสองชุด เมทริกซ์ P ระบุส่วนผสมสินทรัพย์ และ Q ระบุค่าของมุมมองในหน่วยเวลาที่ตรงกัน

[เขียนมุมมอง Absolute และ Relative](implied-returns-views.html)

</section>

<section class="glossary-term" id="view-uncertainty">

### View uncertainty · ความไม่แน่นอนของมุมมอง

Covariance matrix Ω ของความคลาดเคลื่อนใน views แนวทแยงเป็น variance และช่องนอกแนวทแยงบอกความสัมพันธ์ของความคลาดเคลื่อน ไม่ใช่โอกาสที่ราคาจะขึ้น และไม่จำเป็นต้องเท่ากับความเสี่ยงของพอร์ตที่ปรากฏใน view

[แยกความเสี่ยงของพอร์ต View จากความคลาดเคลื่อนของ View](implied-returns-views.html)

</section>

<section class="glossary-term" id="black-litterman">

### Black–Litterman · การรวม Prior กับ Views ของผลตอบแทน

กรอบประมาณ expected returns ที่ผสมค่าตั้งต้นกับมุมมองเพิ่มเติมตามความไม่แน่นอนที่ระบุ ผลลัพธ์ขึ้นกับ prior, covariance, views และความเชื่อมั่น การเปลี่ยนข้อมูลเข้าหรือข้อจำกัดพอร์ตยังเปลี่ยนคำตอบได้

[คำนวณและตรวจพอร์ต Black–Litterman](black-litterman.html)

</section>

</section>

<section class="glossary-group" id="group-risk-budgeting">

## การกระจายพอร์ตและส่วนแบ่งความเสี่ยง

<section class="glossary-term" id="effective-number-assets">

### Effective Number of Constituents · ENC

ค่ากลับของผลรวมน้ำหนักยกกำลังสอง 1/Σw² สำหรับพอร์ต long-only ที่น้ำหนักรวมหนึ่ง มีค่าตั้งแต่ 1 ถึงจำนวนสินทรัพย์ ใช้อ่านการกระจุกตัวของเงิน จำนวนชื่อที่มากขึ้นไม่ได้รับรองว่ามีแหล่งความเสี่ยงอิสระมากขึ้น

[คำนวณ ENC และเพิ่มข้อจำกัดการกระจายเงิน](diversification-methods.html)

</section>

<section class="glossary-term" id="diversification-ratio">

### Diversification ratio · DR

อัตราส่วนระหว่างผลรวมถ่วงน้ำหนักของ SD รายสินทรัพย์กับ SD ของพอร์ตรวม เป็นเกณฑ์ด้านการกระจายความผันผวนภายใต้ covariance ที่เลือก และไม่ใช่ผลตอบแทนที่พอร์ตจะได้รับ

[เทียบ Maximum DR กับ GMV](diversification-methods.html)

</section>

<section class="glossary-term" id="maximum-decorrelation">

### Maximum decorrelation · ลดความสัมพันธ์ตามเกณฑ์ที่กำหนด

ในบทนี้หมายถึงการลด wᵀCorr w ภายใต้ long-only และน้ำหนักรวมหนึ่ง โดยใช้ correlation matrix แทน covariance ถ้า SD ต่างกัน น้ำหนักที่ได้ต่างจาก GMV และ Maximum DR ได้

[ตรวจผลของการเปลี่ยนเมทริกซ์ใน objective](diversification-methods.html)

</section>

<section class="glossary-term" id="risk-contribution">

### Risk contribution · ส่วนของความเสี่ยงที่จัดสรรให้สินทรัพย์

การแยกค่าความเสี่ยงของพอร์ตออกเป็นส่วนของแต่ละสินทรัพย์ตามกฎที่ระบุ ต้องบอกว่าใช้ variance, volatility หรือสัดส่วนของค่ารวมนั้น เพราะหน่วยและตัวเลขไม่เหมือนกัน

[เริ่มจากความเสี่ยงรวมแล้วแยกทีละสินทรัพย์](risk-contributions.html)

</section>

<section class="glossary-term" id="marginal-risk">

### Marginal risk · ความเสี่ยงที่เปลี่ยนต่อการเพิ่ม exposure

อนุพันธ์ของความเสี่ยงพอร์ตตาม exposure ของสินทรัพย์หนึ่งตัวโดยตรึงตัวอื่น สำหรับ volatility เป็น (Σw)ᵢ/σₚ หากย้ายเงินจากสินทรัพย์หนึ่งไปอีกตัว ต้องหาผลต่างของ marginal risks ของสองตัวนั้น

[ตรวจอนุพันธ์ด้วยการขยับน้ำหนักเล็กน้อย](risk-contributions.html)

</section>

<section class="glossary-term" id="component-risk">

### Component risk · ส่วนจัดสรรตาม Euler

สำหรับ volatility คำนวณ wᵢ(Σw)ᵢ/σₚ ผลรวมทุกสินทรัพย์เท่ากับ σₚ เมื่อ σₚ มากกว่าศูนย์ ส่วนจัดสรรอาจติดลบจากผลการหักล้างความเสี่ยง ไม่ใช่ค่าความน่าจะเป็น

[แยก Component จาก Marginal และ Relative risk](risk-contributions.html)

</section>

<section class="glossary-term" id="risk-budget">

### Risk budget · สัดส่วนความเสี่ยงเป้าหมาย

กำหนดส่วนแบ่งของความเสี่ยงรวมที่ต้องการให้แต่ละสินทรัพย์รับ เช่น 40/30/20/10 แล้วแก้หาน้ำหนักเงินที่ให้ส่วนแบ่งตามนั้นภายใต้ covariance และข้อจำกัดที่ระบุ งบความเสี่ยงไม่ใช่น้ำหนักเงิน

[ทดลองงบความเสี่ยงที่ไม่เท่ากัน](risk-parity.html)

</section>

<section class="glossary-term" id="risk-parity">

### Risk parity · การทำส่วนแบ่งความเสี่ยงให้เท่ากัน

ในบทนี้หมายถึง Equal Risk Contribution ของสินทรัพย์ตาม volatility covariance ที่เลือก ทุกตัวมี relative contribution เท่ากับ 1/N การแบ่งเงินเท่ากันหรือถือ inverse-volatility ไม่ได้ให้เงื่อนไขนี้ใน covariance ทั่วไป

[จากสูตรสองสินทรัพย์สู่ตัวแก้ Risk budgets](risk-parity.html)

</section>

<section class="glossary-term" id="inverse-volatility">

### Inverse volatility · น้ำหนักผกผันกับ SD

ให้น้ำหนักตาม 1/σᵢ แล้วหารให้รวมหนึ่ง ใช้เฉพาะ SD รายตัวและไม่ใช้ correlation ในการเลือกน้ำหนัก ให้ ERC ได้ภายใต้เงื่อนไขบางกรณี เช่นสองสินทรัพย์ที่ไม่มีการหักล้างจนความเสี่ยงพอร์ตเป็นศูนย์

[ตรวจกรณีที่ Inverse volatility ตรงหรือไม่ตรง ERC](risk-parity.html)

</section>

<section class="glossary-term" id="effective-number-bets">

### Effective number of risk contributions · การกระจุกตัวของส่วนแบ่งความเสี่ยง

ถ้า relative risk contributions pᵢ ไม่ติดลบและรวมหนึ่ง ค่ากลับ 1/Σpᵢ² ใช้อ่านว่าความเสี่ยงกระจุกอยู่กี่ส่วนโดยเทียบกับกรณีส่วนเท่ากัน ต้องระบุฐานสินทรัพย์หรือ factors ที่ใช้ และไม่ถือว่าเท่ากับจำนวนปัจจัยอิสระโดยอัตโนมัติ

[อ่านส่วนแบ่งความเสี่ยงและกรณีค่าติดลบ](risk-contributions.html)

</section>

</section>

<section class="glossary-group" id="group-machine-learning">

## Machine Learning และภาวะตลาด

<section class="glossary-term" id="feature">

### Feature · ตัวแปรที่ใช้เป็นข้อมูลเข้า

ข้อมูลที่โมเดลใช้สร้างคำพยากรณ์ เช่น ผลตอบแทนล่าสุดหรือความผันผวนย้อนหลัง ต้องมีอยู่จริง ณ เวลาตัดสินใจ หน่วยและเวลาพร้อมใช้เป็นส่วนหนึ่งของนิยาม ไม่ใช่เพียงชื่อคอลัมน์

[อ่านคำอธิบายและตัวอย่าง](ml-foundations.html)

</section>

<section class="glossary-term" id="target-label">

### Target / Label · คำตอบที่ต้องการเรียนรู้

ค่าที่ให้โมเดลเรียนรู้หรือใช้ตรวจคำพยากรณ์ อาจเป็นตัวเลขหรือหมวดหมู่ ต้องระบุช่วงเวลาที่คำตอบอธิบายและวันที่รู้คำตอบ เช่น ผลตอบแทนเดือนหน้าไม่พร้อมใช้ในวันนี้

[อ่านคำอธิบายและตัวอย่าง](ml-foundations.html)

</section>

<section class="glossary-term" id="supervised-learning">

### Supervised learning · เรียนจากตัวอย่างที่มีคำตอบ

การเรียนความสัมพันธ์จากข้อมูลเข้าคู่กับคำตอบ ตัวอย่างที่ใช้ฝึกต้องมีคำตอบพร้อมใช้แล้ว ส่วนคำตอบของชุดทดสอบใช้ประเมินหลังออกคำพยากรณ์

[อ่านคำอธิบายและตัวอย่าง](ml-foundations.html)

</section>

<section class="glossary-term" id="unsupervised-learning">

### Unsupervised learning · เรียนโครงสร้างของข้อมูล

วิธีค้นรูปแบบโดยไม่มี target ที่กำหนดให้ เช่น PCA หรือ clustering การไม่มี target ไม่ได้แปลว่าใช้ข้อมูลอนาคตฝึกก่อนการตัดสินใจได้

[อ่านคำอธิบายและตัวอย่าง](ml-foundations.html)

</section>

<section class="glossary-term" id="regression">

### Regression · พยากรณ์ตัวเลข

โจทย์ supervised learning ที่คำตอบเป็นค่าตัวเลข เช่น ผลตอบแทนเดือนหน้า ต้องเลือก loss และ baseline ที่สอดคล้องกับหน่วยและวัตถุประสงค์

[อ่านคำอธิบายและตัวอย่าง](supervised-learning.html)

</section>

<section class="glossary-term" id="classification">

### Classification · จำแนกประเภท

โจทย์พยากรณ์หมวดหมู่ เช่น เกิดเหตุการณ์หรือไม่เกิด หลายโมเดลให้ probability ก่อนนำไปเทียบ threshold การเลือก threshold จึงเป็นขั้นตอนแยกจากการประมาณ probability

[อ่านคำอธิบายและตัวอย่าง](supervised-learning.html)

</section>

<section class="glossary-term" id="training-set">

### Training set · ชุดฝึก

ข้อมูลที่อนุญาตให้ใช้ประมาณพารามิเตอร์ของโมเดล รวมถึง preprocessing เช่นค่าเฉลี่ยที่ใช้ปรับสเกล สำหรับการพยากรณ์ตามเวลา คำตอบของแต่ละแถวต้องประกาศแล้ว ณ วันฝึก

[อ่านคำอธิบายและตัวอย่าง](model-validation.html)

</section>

<section class="glossary-term" id="validation-set">

### Validation set · ชุดเลือกแบบจำลอง

ข้อมูลที่ใช้เปรียบเทียบโมเดล ค่า hyperparameters หรือกฎตัดสินใจ แยกจากชุดฝึกและ final test เพราะคะแนนที่ใช้เลือกย่อมมีผลต่อวิธีที่เลือก

[อ่านคำอธิบายและตัวอย่าง](model-validation.html)

</section>

<section class="glossary-term" id="test-set">

### Test set · ชุดประเมินที่กันไว้

ข้อมูลที่ใช้ประเมินกระบวนการหลังตรึงวิธีเลือกโมเดลแล้ว หากนำผลไปปรับวิธีซ้ำ ชุดนั้นจะกลายเป็นส่วนหนึ่งของการเลือก ควรมีข้อมูลใหม่สำหรับประเมินครั้งถัดไป

[อ่านคำอธิบายและตัวอย่าง](model-validation.html)

</section>

<section class="glossary-term" id="overfitting">

### Overfitting · เรียนรายละเอียดเฉพาะชุดฝึกมากเกินไป

สถานการณ์ที่โมเดลจับ noise หรือรายละเอียดของตัวอย่างจนผลบนข้อมูลฝึกดูดี แต่ไม่คงคุณภาพบนข้อมูลใหม่ การเพิ่มความซับซ้อนไม่ได้รับรองการพยากรณ์ที่ดีขึ้น

[อ่านคำอธิบายและตัวอย่าง](model-validation.html)

</section>

<section class="glossary-term" id="data-leakage">

### Data leakage · ข้อมูลที่ไม่ควรรู้รั่วเข้าสู่กระบวนการ

การใช้ข้อมูลที่ยังไม่พร้อมหรือไม่ควรใช้ในขั้นฝึกและเลือกโมเดล เช่น fit scaler จากทั้งไฟล์ ใช้ label ที่ประกาศภายหลัง หรือคัด features จากคะแนน final test

[อ่านคำอธิบายและตัวอย่าง](model-validation.html)

</section>

<section class="glossary-term" id="cross-validation">

### Cross-validation · ตรวจหลายส่วนของข้อมูล

การแบ่งข้อมูลเพื่อฝึกและประเมินหลายรอบตามกฎที่กำหนด อนุกรมเวลาควรคงลำดับอดีตก่อนอนาคต และเว้นข้อมูลที่ target ยังไม่ครบหรือยังไม่ประกาศ

[อ่านคำอธิบายและตัวอย่าง](model-validation.html)

</section>

<section class="glossary-term" id="log-loss">

### Log loss · ค่าความผิดพลาดของ Probability แบบลอการิทึม

สำหรับ binary event คือค่าเฉลี่ยของ −[y log(p)+(1−y) log(1−p)] ให้ค่าปรับสูงเมื่อมั่นใจผิด คะแนนต่ำดีกว่าภายใต้เกณฑ์นี้ และต้องแยกจาก accuracy ที่ใช้ threshold

[อ่านคำอธิบายและตัวอย่าง](event-probabilities.html)

</section>

<section class="glossary-term" id="confusion-matrix">

### Confusion matrix · ตารางคำตอบจริงกับคำตอบที่ทาย

นับกรณีทายถูกและผิดแยกตามประเภท ช่วยอ่าน false positive และ false negative ต้องระบุลำดับแถว คอลัมน์ และ class ที่ถือเป็นเหตุการณ์เสมอ

[อ่านคำอธิบายและตัวอย่าง](event-probabilities.html)

</section>

<section class="glossary-term" id="knn">

### K-nearest neighbors · เรียนจากเพื่อนบ้านใกล้ที่สุด

ใช้คำตอบของข้อมูลฝึกที่อยู่ใกล้จุดใหม่ที่สุด K จุดมาประมาณคำตอบ ความหมายของระยะทาง สเกล feature และค่า K มีผลต่อผลลัพธ์

[อ่านคำอธิบายและตัวอย่าง](supervised-learning.html)

</section>

<section class="glossary-term" id="standardization">

### Standardization · ปรับด้วยค่าเฉลี่ยและ SD

แปลง feature ด้วย (x−mean)/SD เพื่อเปลี่ยนสเกล ค่าที่ใช้แปลงต้องเรียนจากชุดฝึกของรอบนั้นแล้วนำไปใช้กับชุดถัดไป การปรับสเกลไม่ได้ทำให้ตัวแปรเป็น Normal หรือเป็นอิสระ

[อ่านคำอธิบายและตัวอย่าง](regularized-factor-models.html)

</section>

<section class="glossary-term" id="ensemble-learning">

### Ensemble learning · รวมหลายแบบจำลอง

รวมคำพยากรณ์จากตัวเรียนรู้หลายตัว เช่น เฉลี่ย probability หรือใช้ Forest/Boosting ซึ่งมีกระบวนการสร้างต่างกัน ผลที่รวมไม่จำเป็นต้องดีกว่าสมาชิกทุกตัว

[อ่านคำอธิบายและตัวอย่าง](recession-models.html)

</section>

<section class="glossary-term" id="regularization">

### Regularization · จำกัดความซับซ้อนระหว่างฝึก

เพิ่ม penalty หรือข้อจำกัดเพื่อลดความไวของค่าประมาณ โดยยอมแลกกับ bias ที่อาจเพิ่มขึ้น ผลต่อข้อมูลใหม่ต้องประเมินแยก

[อ่านคำอธิบายและตัวอย่าง](regularized-factor-models.html)

</section>

<section class="glossary-term" id="ridge-regression">

### Ridge regression · ลงโทษผลรวม Coefficient ยกกำลังสอง

ใช้ squared L2 penalty หด coefficients โดยทั่วไปไม่ทำให้เป็นศูนย์พอดี ค่าความแรงขึ้นกับ convention ของ loss และ penalty จึงต้องตรวจสูตรเมื่อเปลี่ยนเครื่องมือ

[อ่านคำอธิบายและตัวอย่าง](regularized-factor-models.html)

</section>

<section class="glossary-term" id="lasso">

### Lasso · ลงโทษผลรวมค่าสัมบูรณ์

ใช้ L1 penalty และอาจทำให้ coefficients บางตัวเป็นศูนย์ ไม่ใช่การนับจำนวนตัวแปรโดยตรง การเลือกในกลุ่ม feature ที่สัมพันธ์กันอาจไม่เสถียร

[อ่านคำอธิบายและตัวอย่าง](regularized-factor-models.html)

</section>

<section class="glossary-term" id="elastic-net">

### Elastic Net · ผสม L1 และ Squared L2

ใช้ทั้ง penalty แบบ Lasso และ Ridge โดยมีค่าควบคุมความแรงรวมและสัดส่วนผสม ช่วยจัดรูปแบบการหด coefficients แต่ไม่ได้รับประกันว่าเหนือกว่าวิธีอื่นในข้อมูลใหม่

[อ่านคำอธิบายและตัวอย่าง](regularized-factor-models.html)

</section>

<section class="glossary-term" id="multicollinearity">

### Multicollinearity · ตัวแปรอธิบายซ้ำกันเชิงเส้น

บางคอลัมน์อธิบายได้ด้วยชุดผสมเชิงเส้นของคอลัมน์อื่นหรือใกล้เคียงมาก ทำให้แยก coefficients รายตัวได้ยาก ความสัมพันธ์สูงทั้งบวกและลบก่อปัญหาได้

[อ่านคำอธิบายและตัวอย่าง](factor-model-estimation.html)

</section>

<section class="glossary-term" id="hyperparameter">

### Hyperparameter · ค่าที่กำหนดวิธีฝึก

ค่าที่ตั้งก่อนประมาณพารามิเตอร์ เช่น K ของ KNN หรือ penalty ของ Ridge ควรเลือกด้วย validation ที่เหมาะสม ไม่ใช้ final test เป็นตัวเลือก

[อ่านคำอธิบายและตัวอย่าง](model-validation.html)

</section>

<section class="glossary-term" id="pipeline">

### Pipeline · ลำดับการแปลงข้อมูลและฝึกโมเดล

รวม preprocessing กับ estimator ให้ fit บนข้อมูลฝึกชุดเดียวกันภายในแต่ละ fold ช่วยลดการเผลอปรับสเกลหรือเลือก feature จากข้อมูล validation

[อ่านคำอธิบายและตัวอย่าง](factor-model-validation.html)

</section>

<section class="glossary-term" id="pca">

### Principal Component Analysis · PCA

สร้างแกนตั้งฉากที่เรียงตาม variance ของข้อมูลที่ center แล้ว PCA บน covariance กับ correlation ให้ความหมายต่างกัน ส่วนแบ่ง variance ของข้อมูลไม่เท่ากับส่วนแบ่งความเสี่ยงของพอร์ตทุกน้ำหนัก

[อ่านคำอธิบายและตัวอย่าง](pca-diversification.html)

</section>

<section class="glossary-term" id="asset-clustering">

### Asset clustering · จัดกลุ่มสินทรัพย์

แบ่งสินทรัพย์ตามความคล้ายกันภายใต้ feature และระยะทางที่เลือก กลุ่มที่ได้ขึ้นกับช่วงข้อมูลและวิธี ไม่ใช่หมวดหมู่ทางเศรษฐกิจที่แน่นอนหรือกฎเลือกน้ำหนักพอร์ตสำเร็จรูป

[อ่านคำอธิบายและตัวอย่าง](asset-clustering.html)

</section>

<section class="glossary-term" id="partial-correlation">

### Partial correlation · ความสัมพันธ์หลังปรับตัวแปรอื่น

วัดความสัมพันธ์เชิงเส้นส่วนที่เหลือหลังหักความสัมพันธ์กับตัวแปรที่กำหนด สำหรับ multivariate Gaussian ค่า precision นอกแนวทแยงเป็นศูนย์เชื่อมกับ conditional independence แต่โดยทั่วไปไม่ใช่หลักฐานเชิงเหตุและผล

[อ่านคำอธิบายและตัวอย่าง](asset-networks.html)

</section>

<section class="glossary-term" id="brier-score">

### Brier score · Squared error ของ Probability

ในโจทย์ binary คือค่าเฉลี่ย (p−y)² มีช่วง 0 ถึง 1 และยิ่งต่ำยิ่งดี บางแหล่งนิยาม QPS เป็นสองเท่าของค่านี้ ต้องดูสูตรก่อนเปรียบเทียบ

[อ่านคำอธิบายและตัวอย่าง](event-probabilities.html)

</section>

<section class="glossary-term" id="probability-calibration">

### Probability calibration · ความสอดคล้องของโอกาสกับความถี่

ตรวจว่ากลุ่มคำพยากรณ์ที่ให้ probability ใกล้กันมีอัตราเกิดเหตุการณ์ใกล้ probability นั้นหรือไม่ ต้องประเมินนอกข้อมูลที่ใช้ปรับ probability และคำนึงถึงจำนวนตัวอย่างในแต่ละกลุ่ม

[อ่านคำอธิบายและตัวอย่าง](event-probabilities.html)

</section>

<section class="glossary-term" id="market-regime">

### Market regime · ภาวะตลาดในแบบจำลอง

สถานะที่กำหนดให้ผลตอบแทนหรือความเสี่ยงมีลักษณะใกล้กันภายในช่วง เช่น ภาวะปกติและตึงเครียด นิยามจากตลาดหุ้นไม่จำเป็นต้องตรงกับภาวะถดถอยทางเศรษฐกิจ

[อ่านคำอธิบายและตัวอย่าง](market-regimes.html)

</section>

<section class="glossary-term" id="transition-matrix">

### Transition matrix · ความน่าจะเป็นเปลี่ยนสถานะ

ตารางที่ระบุโอกาสจากสถานะปัจจุบันไปสถานะถัดไป ต้องระบุแถว/คอลัมน์และระยะเวลาหนึ่งช่วงให้ชัด เช่น ตารางรายเดือนไม่ควรถูกใช้เป็นรายปีโดยตรง

[อ่านคำอธิบายและตัวอย่าง](market-regimes.html)

</section>

<section class="glossary-term" id="trend-filtering">

### Trend filtering · ประมาณแนวโน้มด้วย Penalty

หาค่าที่สมดุลระหว่างการ fit ข้อมูลกับการจำกัดความเปลี่ยนแปลง First-difference L1 ให้เส้นคงที่เป็นช่วง ส่วน second-difference L1 ให้เส้นตรงเป็นช่วง การใช้ทั้งประวัติอาจนำอนาคตมาแก้ค่าช่วงอดีต

[อ่านคำอธิบายและตัวอย่าง](market-regimes.html)

</section>

<section class="glossary-term" id="scenario-probability">

### Scenario probability · น้ำหนักความน่าจะเป็นของสถานการณ์

โอกาสที่กำหนดให้แต่ละสถานการณ์ ต้องไม่ติดลบและรวมหนึ่ง ใช้คำนวณค่าเฉลี่ย ความเสี่ยง และ loss ของพอร์ตภายใต้ชุดสถานการณ์ที่ระบุ

[อ่านคำอธิบายและตัวอย่าง](regime-scenarios.html)

</section>

</section>
