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
- How to Calculate return: บทเริ่มต้นจากเปอร์เซ็นต์ เงินทบต้น ค่าเฉลี่ย และ Python/pandas แบบทีละขั้น ตามหัวข้อ Module 1 ของคอร์ส EDHEC ต่อด้วย Volatility, Sharpe ratio, Drawdown, Skewness, Semi-deviation และ VaR/ES ใช้ข้อมูลสมมติและโค้ดสั้นพร้อมผลลัพธ์ มี Log return เป็นบทอ่านต่อ พร้อมภาพคำนวณ 2 ภาพ ตัวทดลองเดิม และคำถามพร้อมเฉลย
- เมื่อผลตอบแทนไม่เป็น Normal: บทต่อ Section 2 ของ Module 1 สอนรูปร่างผลตอบแทน Moments, Normality, Python module, Semi-deviation และ Historical/Gaussian/Cornish–Fisher VaR พร้อม CVaR แบบถ่วงน้ำหนักปลายหาง กราฟสมมติ และแบบฝึกหัด
- ความเสี่ยงในการลงทุน: นิยาม ประวัติ และทฤษฎีของความเสี่ยง ก่อนคำนวณ Volatility, Downside, Drawdown, Diversification, VaR, ES, EWMA และ Stress test พร้อมตัวทดลอง 3 ชุดและแหล่งอ้างอิงต้นฉบับ
- Portfolio Insurance: บทเรียน 13 หัวข้อหลักแบบละเอียด ไล่จาก Put และงบ OBPI สู่ CPPI หลายรอบ, Variable-Multiplier Portfolio Insurance พร้อมตัวอย่างใน Notebook, TIPP แบบ Ratchet, Gap risk พร้อมดอกเบี้ย, EUT/CPT พร้อมคำนวณคะแนน และการประเมิน Shortfall/Drawdown มีผลทดสอบ S&P 500 ปี 2018–2025 พร้อมกราฟมูลค่าและ Drawdown รายวันเทียบ Buy & Hold แทรกใน SLPI, CPPI, TIPP และ Variable Multiplier พร้อมข้อดีข้อเสียของแต่ละวิธี และโจทย์พร้อมเฉลย 8 ข้อและเครื่องมือทดลองในบท
- อภิธานศัพท์: นิยามภาษาไทย ค้นหาคำ และลิงก์กลับไปยังตัวอย่าง
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
npm run check:course  # รันโค้ดชุด Introduction และตรวจ Notebook ให้ตรงต้นฉบับ
npm run check:advanced
npm run check:ml       # ต้องมี dependencies ตาม qa/ml-requirements.txt
npm run check:extreme # ต้องมี NumPy/pandas/SciPy ตาม qa/extreme-risk-requirements.txt
npm run build:pages
npm run check:site  # ต้องเปิด preview ที่พอร์ต 8764
```

ใช้ `npm run build` แล้วเปิด `_site/index.html` ได้แบบ offline พร้อมกราฟและฟอนต์ในเครื่อง เผยแพร่เฉพาะ `_site/` ดู `DEPLOYMENT.md` สำหรับ GitHub Pages

ต้นฉบับ PDF และไฟล์ตรวจหลักฐานใน `.research/` เก็บในเครื่อง ไม่รวมใน Git/ชุดเว็บ ข้อมูลอ้างอิงสาธารณะ: https://hdl.handle.net/10400.5/16515 รายการสิทธิ์ของ dependencies และ assets อยู่ใน `THIRD_PARTY_NOTICES.md`

เมื่อแก้เนื้อหาหรือแบบจำลองที่อยู่ใน Notebook ให้สร้าง Notebook นั้นใหม่ก่อน build ดูแนวทางใน `EDITING.md`

ภาพปกใช้โลโก้ QuantCorner / Quantsera ต้นฉบับบนพื้นดำ ชื่อผู้เรียบเรียงบนเว็บคือ QuantCorner

Visual route: `no-image-generator` ตาม QuantCorner / QuantSeras Material 2 ใช้ฟอนต์ Roboto / Noto Sans Thai / Roboto Mono ในเครื่อง พื้นขาวเป็นค่าเริ่มต้น มีธีมมืดให้เลือก ปุ่มและคำอธิบายเป็นภาษาไทยตามรูปแบบที่เจ้าของเลือก

บทความเสี่ยงมีภาพประกอบแนวคิดที่สร้างด้วย AI ตามคำขอเจ้าของ พร้อมกราฟ P/Q และ Correlation ที่คำนวณจากตัวอย่างสมมติ ภาพประกอบแยกจากกราฟข้อมูลอย่างชัดเจน; ดู provenance ใน `data/risk-provenance.json`


## Module 2–4

บทเรียนต่อเนื่องแยกเป็นสิบหน้า โดยจัดสารบัญตามโมดูล:

- Module 2: เริ่มจัดพอร์ตจากสินทรัพย์สองตัว, Efficient frontier, และ MSR/GMV/ความคลาดเคลื่อนของค่าประมาณ
- Module 3: ข้อจำกัดของ Diversification, CPPI จากศูนย์, และ Monte Carlo
- Module 4: Asset-Liability Management, พันธบัตรและ Duration, CIR/อัตราดอกเบี้ย, และการจัดพอร์ตตามเป้าหมาย

ทุกหน้ามี Python ที่รันจาก namespace ว่างได้และ Notebook ของบทนั้นพร้อมผลรัน ตัวอย่างใหม่ทั้งหมดเป็นข้อมูลสมมติหรือการจำลองที่กำหนด seed; ไม่มีการแจก CSV, toolkit หรือ Transcript ของคอร์ส ขอบเขตและแหล่งที่มาอยู่ใน `data/course-provenance.json`.

หลังแก้บทเหล่านี้ ใช้ `npm run notebook:course` เพื่อสร้าง Notebook ใหม่ แล้ว `npm run check:course`, `npm run build:pages` และ `npm run check:site` กราฟคำนวณด้วย `python3 scripts/make_course_figures.py` และเก็บค่าที่พล็อตใน `data/course-figures.json`.

## Advanced course · Module 1

Four beginner lessons cover Factor/CAPM, Fama–French, constrained Style Analysis and Smart Beta. Each has a complete executed Notebook. The main examples are original hypothetical data; the separately labelled BRKA case uses the supplied 2018 course snapshot and exposes aggregate estimates plus an optional local-ZIP analysis script. Raw course data and transcripts stay outside Git.

```sh
python3 scripts/make_advanced_figures.py
python3 scripts/make_course_notebooks.py --course advanced --module 1
npm run check:advanced
npm run build:pages
```

Sources and conventions: `data/advanced-module1-provenance.json`. The public optional loader is `examples/advanced/analyze_course_factors.py`; it reads an explicit local ZIP argument and never downloads data or exports raw observations.

## Advanced course · Module 2

Three lessons cover sample/factor covariance, constant-correlation shrinkage and time-varying risk. Each begins with small worked examples before introducing matrix calculations or rolling experiments. The examples use original hypothetical data and fixed seeds. Fixed shrinkage intensities and GARCH parameters are teaching choices, not estimated market recommendations.

Export these notebooks with `python3 scripts/make_course_notebooks.py --course advanced --module 2`. Run `npm run check:advanced`, `npm run build:pages` and the browser checks after changes. Sources, data conventions and the scope of course-code inspection are recorded in `data/advanced-module2-provenance.json`.

The rolling-window and fixed-origin forecast charts are computed with `python3 scripts/make_covariance_figures.py`; their numeric series are saved in `data/advanced-covariance-figures.json`. Refresh figures before exporting the notebooks that embed them.

## Advanced course · Module 3

Three lessons cover expected-return estimation, reverse optimization and views, then Black–Litterman. Small original examples distinguish sampling uncertainty from return volatility, the covariance of the posterior mean from predictive return covariance, and unconstrained allocations with cash from fully invested constrained portfolios. The views are hypothetical teaching assumptions.

Use `python3 scripts/make_course_notebooks.py --course advanced --module 3` to export these notebooks. The same `npm run check:advanced`, build/link and browser checks cover this module. Source access and conventions are recorded in `data/advanced-module3-provenance.json`.

Module 3 figures are recomputed with `python3 scripts/make_expected_return_figures.py`; the chart values and both SVG sizes are checked independently in `qa/advanced-module3-checks.py`.

## Advanced course · Module 4

Four lessons cover diversification methods, Euler risk contributions, risk budgets and a common rolling comparison. All methods use original teaching data and stated constraints. The comparison separates the forecast covariance from realized performance, uses data strictly before each decision, and accounts for proportional transaction costs through a self-financing cash ledger.

Export with `python3 scripts/make_course_notebooks.py --course advanced --module 4`. Run `npm run check:advanced`, build/link checks and the browser checks after changes. Record source scope in `data/advanced-module4-provenance.json`; do not publish original course notebooks or infer universal strategy rankings from either the course tables or our simulation.

Module 4 figures are recomputed with `python3 scripts/make_risk_budget_figures.py`. Refresh them before exporting Notebooks; `qa/advanced-module4-checks.py` verifies their numerical data and both SVG sizes.

## Machine Learning for Asset Management

Sixteen beginner Thai chapters extend the book through data/targets and supervised learning (4), robust factor estimation (3), PCA/clustering/networks (3), market regimes/scenarios/endowments (3), and event probabilities/forecasting/feature selection (3). Every chapter has an independently executable Notebook with full prose, equations and saved outputs. New examples are original hypothetical data or seeded simulations. Source coverage and corrections are documented in `data/ml-*-sources.json`; private Coursera transcripts and instructor assets are not redistributed.

```sh
python3 -m pip install -r qa/ml-requirements.txt
python3 scripts/make_ml_figures.py
python3 scripts/make_ml_diversification_figures.py
python3 scripts/make_course_notebooks.py --course machine-learning
npm run check:ml
npm run build:pages
npm run check:site
```

Internal `module` and `lesson` metadata preserve course order and allow optional `--module` export/check filters. Public navigation uses topic names without numbered Module labels. Calculated chart arrays are saved in `data/ml-figures.json` and `data/ml-diversification-figures.json`. The numerical checks independently verify analytical results, timing boundaries, preprocessing, future-data invariance and source/Notebook consistency; browser checks cover all course pages and responsive figures.
