# Portfolio Management Toolkit

เว็บไซต์ภาษาไทยสำหรับเรียนรู้การบริหารพอร์ตจากงานวิจัยและเครื่องมือทดลอง โดย QuantCorner เริ่มจากหมวด **Portfolio Insurance** อ้างอิงวิทยานิพนธ์ *Portfolio Insurance Strategies: Friend or Foe?* ของ Paulo José Martins Jorge da Silva (2018)

โปรเจกต์นี้แยกจาก Quantitative Finance Notes ทั้งโฟลเดอร์ เนื้อหา การ build และพอร์ต preview เว็บไซต์เดิมไม่มีการแก้ไข

## เปิดในเครื่อง

ใช้ Node.js 22 ขึ้นไป:

```sh
npm ci
npm run dev
```

เปิด http://127.0.0.1:8764/ หรือดับเบิลคลิก `Preview.command` เมื่อบันทึกเนื้อหาหรือโค้ด ระบบ rebuild ให้ จากนั้น refresh browser

## เนื้อหาและเครื่องมือ

- Overview: หน้าแรกของ Toolkit และกราฟตัวอย่าง
- Portfolio insurance: Floor, Cushion, SLPI, OBPI, CPPI, TIPP, gap risk และ cash lock
- Strategy lab: CPPI simulator, allocation walkthrough และ Protective Put calculator
- Research notes: วิธีจำลอง EUT/CPT, ผลที่ตรวจจากต้นฉบับ และข้อจำกัด robo-advisor case study
- Glossary: คำศัพท์พร้อมลิงก์กลับบทเรียน

Lab ใช้ 4 เส้นทางสมมติ 12 เดือน เปรียบเทียบ CPPI กับ Buy & Hold และ Constant Mix 60/40 ไม่ใช่ backtest หรือการทำซ้ำวิทยานิพนธ์ คำนวณใน browser ไม่มีการเรียกข้อมูลตลาด ไม่มี analytics และไม่ส่งพารามิเตอร์ไป server ดาวน์โหลดผลรายเดือนพร้อมพารามิเตอร์เป็น CSV ได้

## ไฟล์ที่แก้ได้

| ไฟล์ | หน้าที่ |
|---|---|
| `content/*.md` | เนื้อหาหน้าเว็บและสมการ |
| `site.config.json` | ชื่อเว็บไซต์ สารบัญ และ metadata |
| `src/math.mjs` | แบบจำลองและเส้นทางสมมติ |
| `src/app.jsx` | เครื่องมือทดลองและกราฟ |
| `src/site.js` | ค้นหา เมนู และธีม |
| `src/components/` | React Bits ที่ปรับสำหรับเว็บไซต์นี้ |
| `style.css` | โครงหน้าและ design tokens |
| `assets/` | ฟอนต์และ approved assets ที่ใช้ในเครื่องได้ |
| `build.cjs` | Static HTML, KaTeX และ JS bundling |
| `_site/` | ผล build อัตโนมัติ ไม่แก้ตรงนี้ |

เพิ่มบทเรียนด้วย Markdown ใน `content/` แล้วเพิ่มหน้าใน `site.config.json` รองรับ HTML anchor, inline/display LaTeX และ relative links หน้าเรียนเป็น static HTML ที่อ่านได้ก่อน JavaScript ทำงาน

## ตรวจและ build

```sh
npm test
npm run build:pages
npm run check:site  # ต้องเปิด preview ที่พอร์ต 8764
```

ใช้ `npm run build` แล้วเปิด `_site/index.html` ได้แบบ offline พร้อมกราฟและฟอนต์ในเครื่อง เผยแพร่เฉพาะ `_site/` ดู `DEPLOYMENT.md` สำหรับ GitHub Pages

ต้นฉบับ PDF และไฟล์ตรวจหลักฐานใน `.research/` เก็บในเครื่อง ไม่รวมใน Git/ชุดเว็บ ข้อมูลอ้างอิงสาธารณะ: https://hdl.handle.net/10400.5/16515 รายการสิทธิ์ของ dependencies และ assets อยู่ใน `THIRD_PARTY_NOTICES.md`

Visual route: `no-image-generator` ตาม QuantCorner / QuantSeras Material 2; dark default และ light supporting. UI หลักเป็นภาษาอังกฤษ เนื้อหาเรียนรู้เป็นภาษาไทย ตามบริบทซีรีส์ของเจ้าของ
