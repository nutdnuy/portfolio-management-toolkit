# Portfolio Management Toolkit Notes

เว็บไซต์สาธารณะ: [Portfolio Management Toolkit Notes](https://nutdnuy.github.io/portfolio-management-toolkit/)

Repository: [nutdnuy/portfolio-management-toolkit](https://github.com/nutdnuy/portfolio-management-toolkit)

เมื่อ commit และ push ไปที่ `main` ระบบ **Publish toolkit** จะตรวจและเผยแพร่ GitHub Pages อัตโนมัติ

หนังสือออนไลน์ภาษาไทยเรื่องการบริหารพอร์ต โดย QuantCorner เริ่มจากบท **How to Calculate return** ว่าด้วยผลตอบแทนและการทบต้น ต่อด้วยบท **ความเสี่ยงในการลงทุน** ตั้งแต่ที่มาของแนวคิดจนถึงการวัดความเสี่ยง พร้อมบท **Portfolio Insurance** อ้างอิงวิทยานิพนธ์ *Portfolio Insurance Strategies: Friend or Foe?* ของ Paulo José Martins Jorge da Silva (2018) ใช้รูปแบบเดียวกับ [บท Binomial Model](https://nutdnuy.github.io/quantitative-finance-notes/binomial-model.html): พื้นขาว สารบัญด้านซ้าย เนื้อหาต่อเนื่อง สมการ และเครื่องมือทดลองแทรกในบทเรียน

โปรเจกต์นี้แยกจาก Quantitative Finance Notes ทั้งโฟลเดอร์ เนื้อหา การ build และพอร์ต preview เว็บไซต์เดิมไม่มีการแก้ไข

## เปิดในเครื่อง

ใช้ Node.js 22 ขึ้นไป:

```sh
npm ci
npm run dev
```

เปิด http://127.0.0.1:8764/ หรือดับเบิลคลิก `Preview.command` เมื่อบันทึกเนื้อหาหรือโค้ด ระบบ rebuild ให้ จากนั้น refresh browser

## เนื้อหาและเครื่องมือ

- Welcome: แนะนำหนังสือและวิธีอ่าน
- How to Calculate return: Simple/Log return และคุณสมบัติการบวกข้ามเวลา ผ่านเงิน 1 ล้านบาทที่ได้ +100% แล้ว −50% พร้อมภาพคำนวณ 2 ภาพ ตัวทดลองปรับผลตอบแทนรายปี ค่าเฉลี่ย CAGR ผลตอบแทนพอร์ต และคำถามพร้อมเฉลย
- ความเสี่ยงในการลงทุน: นิยาม ประวัติ และทฤษฎีของความเสี่ยง ก่อนคำนวณ Volatility, Downside, Drawdown, Diversification, VaR, ES, EWMA และ Stress test พร้อมตัวทดลอง 3 ชุดและแหล่งอ้างอิงต้นฉบับ
- Portfolio Insurance: บทเรียน 13 หัวข้อหลักแบบละเอียด ไล่จาก Put และงบ OBPI สู่ CPPI หลายรอบ, Variable-Multiplier Portfolio Insurance พร้อมตัวอย่างใน Notebook, TIPP แบบ Ratchet, Gap risk พร้อมดอกเบี้ย, EUT/CPT พร้อมคำนวณคะแนน และการประเมิน Shortfall/Drawdown มีผลทดสอบ S&P 500 ปี 2018–2025 พร้อมกราฟมูลค่าและ Drawdown รายวันเทียบ Buy & Hold แทรกใน SLPI, CPPI, TIPP และ Variable Multiplier พร้อมข้อดีข้อเสียของแต่ละวิธี และโจทย์พร้อมเฉลย 8 ข้อและเครื่องมือทดลองในบท
- อภิธานศัพท์: 47 คำพร้อมนิยามภาษาไทย ค้นหาคำ และลิงก์กลับไปยังตัวอย่าง
- Notebook: คำอธิบายและสมการครบจากบทเรียน พร้อมโค้ด Python และกราฟที่คำนวณซ้ำได้

Lab ใช้ 4 เส้นทางสมมติ 12 เดือน เปรียบเทียบ CPPI กับ Buy & Hold และ Constant Mix 60/40 ไม่ใช่ backtest หรือการทำซ้ำวิทยานิพนธ์ คำนวณใน browser ไม่มีการเรียกข้อมูลตลาด ไม่มี analytics และไม่ส่งพารามิเตอร์ไป server ดาวน์โหลดผลรายเดือนพร้อมพารามิเตอร์เป็น CSV ได้

## ไฟล์ที่แก้ได้

| ไฟล์ | หน้าที่ |
|---|---|
| `content/*.md` | เนื้อหาหน้าเว็บและสมการ |
| `site.config.json` | ชื่อเว็บไซต์ สารบัญ และ metadata |
| `src/math.mjs` | แบบจำลองและเส้นทางสมมติ |
| `src/app.jsx` | เครื่องมือทดลองและกราฟ |
| `src/risk.jsx`, `src/risk.css`, `src/risk-math.mjs` | ตัวทดลองและตัวคำนวณบทความเสี่ยง |
| `src/site.js` | ค้นหา เมนู และธีม |
| `src/components/` | React Bits ที่ปรับสำหรับเว็บไซต์นี้ |
| `style.css`, `book.css` | บทเรียน เครื่องมือ และโครงหนังสือ |
| `scripts/make_notebook.py` | สร้างและรัน Notebook จากเนื้อหาบทเรียน |
| `notebooks/portfolio-insurance.ipynb` | Notebook ที่สร้างแล้วสำหรับดาวน์โหลด |
| `assets/` | ฟอนต์และ approved assets ที่ใช้ในเครื่องได้ |
| `build.cjs` | Static HTML, KaTeX และ JS bundling |
| `_site/` | ผล build อัตโนมัติ ไม่แก้ตรงนี้ |

เพิ่มบทเรียนด้วย Markdown ใน `content/` แล้วเพิ่มหน้าใน `site.config.json` รองรับ HTML anchor, inline/display LaTeX และ relative links หน้าเรียนเป็น static HTML ที่อ่านได้ก่อน JavaScript ทำงาน

## ตรวจและ build

```sh
npm test
npm run notebook       # Python 3.9+; ใช้ standard library
npm run check:notebook
npm run check:sp500
npm run build:pages
npm run check:site  # ต้องเปิด preview ที่พอร์ต 8764
```

ใช้ `npm run build` แล้วเปิด `_site/index.html` ได้แบบ offline พร้อมกราฟและฟอนต์ในเครื่อง เผยแพร่เฉพาะ `_site/` ดู `DEPLOYMENT.md` สำหรับ GitHub Pages

ต้นฉบับ PDF และไฟล์ตรวจหลักฐานใน `.research/` เก็บในเครื่อง ไม่รวมใน Git/ชุดเว็บ ข้อมูลอ้างอิงสาธารณะ: https://hdl.handle.net/10400.5/16515 รายการสิทธิ์ของ dependencies และ assets อยู่ใน `THIRD_PARTY_NOTICES.md`

เมื่อแก้เนื้อหาหรือแบบจำลองที่อยู่ใน Notebook ให้สร้าง Notebook นั้นใหม่ก่อน build ดูแนวทางใน `EDITING.md`

ภาพปกใช้โลโก้ QuantCorner / Quantsera ต้นฉบับบนพื้นดำ ชื่อผู้เรียบเรียงบนเว็บคือ QuantCorner

Visual route: `no-image-generator` ตาม QuantCorner / QuantSeras Material 2 ใช้ฟอนต์ Roboto / Noto Sans Thai / Roboto Mono ในเครื่อง พื้นขาวเป็นค่าเริ่มต้น มีธีมมืดให้เลือก ปุ่มและคำอธิบายเป็นภาษาไทยตามรูปแบบที่เจ้าของเลือก
