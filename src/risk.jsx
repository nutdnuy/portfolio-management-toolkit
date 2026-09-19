import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import {flushSync} from 'react-dom';
import {summarizePath, empiricalTail, ewmaUpdate, ewmaDecay} from './risk-math.mjs';
import './risk.css';

const number = (value, digits=0) => (Math.abs(value)<1e-10?0:value).toLocaleString('en-US', {minimumFractionDigits:digits, maximumFractionDigits:digits});
const percent = (value, digits=2) => `${number(value*100,digits)}%`;
const signedPercent = value => `${value>0?'+':value<0?'−':''}${percent(Math.abs(value),0)}`;
const paths = [
  {name:'พอร์ต A', label:'ขึ้นสองครั้ง แล้วลงสองครั้ง', returns:[.1,.1,-.1,-.1]},
  {name:'พอร์ต B', label:'ขึ้นและลงสลับกัน', returns:[.1,-.1,.1,-.1]},
];

function Metric({label, value, testId, note}) {
  return <div><span>{label}</span><strong data-testid={testId}>{value}</strong>{note&&<small>{note}</small>}</div>;
}

function PathChart({values, underwater=false}) {
  const id=underwater?'risk-drawdown':'risk-wealth';
  const x=i=>68+i*98;
  const y=underwater?v=>34+v/(-.2)*140:v=>174-(v/1e6-.9)/.4*140;
  const ticks=underwater?[0,-.1,-.2]:[.9e6,1.1e6,1.3e6];
  const format=underwater?v=>percent(v,0):v=>number(v/1e6,1);
  const points=values.map((v,i)=>`${x(i)},${y(v)}`).join(' ');
  return <svg viewBox="0 0 500 236" role="img" aria-labelledby={`${id}-title ${id}-desc`}>
    <title id={`${id}-title`}>{underwater?'Drawdown จากจุดสูงสุดก่อนหน้า หน่วยเปอร์เซ็นต์':'มูลค่าพอร์ต หน่วยล้านบาท'}</title>
    <desc id={`${id}-desc`}>{values.map((v,i)=>`${i===0?'เริ่มต้น':`สิ้นเดือน ${i}`}: ${underwater?percent(v):`${number(v)} บาท`}`).join(' · ')}</desc>
    {ticks.map(v=><g key={v}><line className={underwater&&v===0?'risk-zero':'risk-grid'} x1="68" x2="460" y1={y(v)} y2={y(v)}/><text className="risk-tick" x="56" y={y(v)+6} textAnchor="end">{format(v)}</text></g>)}
    {underwater&&<polygon points={`${x(0)},${y(0)} ${points} ${x(values.length-1)},${y(0)}`} className="risk-drawdown-area"/>}
    <polyline points={points} className={underwater?'risk-line risk-line-comparison':'risk-line risk-line-primary'}/>
    {values.map((v,i)=><g key={i}><circle className={underwater?'risk-point risk-point-comparison':'risk-point risk-point-primary'} cx={x(i)} cy={y(v)} r="4"/><text className="risk-tick" x={x(i)} y="203" textAnchor="middle">{i}</text></g>)}
    <text className="risk-axis-label" x="264" y="230" textAnchor="middle">เดือน · 0 คือเงินเริ่มต้น</text>
  </svg>;
}

function PathLab() {
  const [selected,setSelected]=useState(0);
  const path=paths[selected];
  const model=summarizePath(path.returns);
  return <section className="risk-viz" aria-labelledby="risk-path-title">
    <div className="risk-heading"><p className="risk-eyebrow">ทดลอง 1 · ข้อมูลสมมติ 4 เดือน</p><h3 id="risk-path-title">เงินปลายทางเท่ากัน แต่ขาดทุนระหว่างทางไม่เท่ากัน</h3><p>สลับลำดับผลตอบแทน แล้วดูว่าตัววัดใดเปลี่ยนตามเส้นทาง</p></div>
    <div className="risk-presets" role="group" aria-label="เลือกเส้นทางพอร์ต">{paths.map((p,i)=><button key={p.name} type="button" aria-pressed={selected===i} onClick={()=>setSelected(i)}><strong>{p.name}</strong><span>{p.label}</span></button>)}</div>
    <p className="risk-sequence" aria-label={`ผลตอบแทนของ${path.name}`}>{path.returns.map((v,i)=><React.Fragment key={i}>{i>0&&<span aria-hidden="true"> → </span>}<b>{signedPercent(v)}</b></React.Fragment>)}</p>
    <div className="risk-metrics" role="status" aria-live="polite" aria-atomic="true">
      <Metric label="Maximum drawdown" value={percent(model.maxDrawdown)} testId="path-mdd" note="ลดจากจุดสูงสุดมากที่สุดใน 4 เดือน"/>
      <Metric label="Volatility ต่อเดือน" value={percent(model.volatility)} testId="path-volatility" note="Sample SD · หารด้วย n − 1"/>
      <Metric label="เงินปลายทาง" value={`${number(model.wealth.at(-1))} บาท`} testId="path-terminal" note="เงินเริ่มต้น 1,000,000 บาท"/>
    </div>
    <div className="risk-path-charts">
      <figure className="risk-chart"><figcaption><strong>มูลค่าพอร์ต</strong><span>หน่วย: ล้านบาท</span></figcaption><PathChart values={model.wealth}/></figure>
      <figure className="risk-chart"><figcaption><strong>ระยะที่ลดลงจากจุดสูงสุด</strong><span>Drawdown · หน่วย: % · ค่าลบคืออยู่ต่ำกว่าจุดสูงสุด</span></figcaption><PathChart values={model.drawdowns} underwater/></figure>
    </div>
    <p className="risk-insight">ทั้งสองพอร์ตมีผลตอบแทนชุดเดียวกัน จึงมีค่าเฉลี่ยและ Volatility เท่ากัน แต่ Maximum drawdown เปลี่ยนตามลำดับผลตอบแทน</p>
    <details className="risk-details"><summary>ดูเงินและ Drawdown ทีละเดือน</summary><div className="table-scroll" role="region" aria-label="ตารางเส้นทางพอร์ต เลื่อนแนวนอนเพื่ออ่านครบ" tabIndex="0"><table><caption>{path.name} · ตัวอย่างสมมติ ไม่มีเงินเข้าออกหรือค่าใช้จ่าย</caption><thead><tr><th scope="col">เดือน</th><th scope="col">ผลตอบแทน</th><th scope="col">มูลค่า (บาท)</th><th scope="col">Drawdown</th></tr></thead><tbody>{model.wealth.map((wealth,i)=><tr key={i}><th scope="row">{i===0?'เริ่มต้น':i}</th><td>{i===0?'—':signedPercent(path.returns[i-1])}</td><td>{number(wealth)}</td><td>{percent(model.drawdowns[i])}</td></tr>)}</tbody></table></div></details>
    <p className="risk-note">ผลตอบแทนรายเดือน · ไม่แปลง Volatility เป็นรายปี · Maximum drawdown เป็นค่าของเส้นทางตัวอย่างนี้ ไม่ใช่ขีดจำกัดความเสียหายในอนาคต</p>
  </section>;
}

function TailChart({extreme,tail}) {
  const values=[extreme,20000,20000,20000,20000,20000];
  const x=value=>64+value/400000*366;
  return <svg viewBox="0 0 500 350" role="img" aria-labelledby="risk-tail-chart-title risk-tail-chart-desc">
    <title id="risk-tail-chart-title">ผลขาดทุนมากที่สุด 6 ค่า จากตัวอย่าง 100 ค่า หน่วยพันบาท</title>
    <desc id="risk-tail-chart-desc">ผลขาดทุน {number(extreme)} บาทหนึ่งค่า และ 20,000 บาทห้าค่า VaR 95% เท่ากับ {number(tail.var)} บาท ES 95% เท่ากับ {number(tail.es)} บาท หาง 5% ใช้ค่ารุนแรงหนึ่งค่าและค่า 20,000 บาทอีกสี่ค่า</desc>
    {[0,100000,200000,300000,400000].map(v=><g key={v}><line className="risk-grid" x1={x(v)} x2={x(v)} y1="65" y2="282"/><text className="risk-tick" x={x(v)} y="308" textAnchor="middle">{number(v/1000)}</text></g>)}
    {values.map((v,i)=>{const y=72+i*35;return <g key={i}><text className="risk-tick" x="49" y={y+19} textAnchor="end">{i+1}</text><rect className={i<5?'risk-tail-included':'risk-tail-boundary'} x={x(0)} y={y} width={x(v)-x(0)} height="24"/><text className="risk-bar-label" x={v>=300000?x(v)-8:x(v)+8} y={y+18} textAnchor={v>=300000?'end':'start'} fill={v>=300000?'var(--on-primary)':'var(--text)'}>{number(v/1000)}</text></g>})}
    <line className="risk-var-line" x1={x(tail.var)} x2={x(tail.var)} y1="40" y2="282"/><text className="risk-reference-label" x={x(tail.var)} y="28">VaR</text>
    <line className="risk-es-line" x1={x(tail.es)} x2={x(tail.es)} y1="62" y2="282"/><text className="risk-reference-label risk-es-label" x={x(tail.es)} y="52">ES</text>
    <text className="risk-axis-label" x="248" y="336" textAnchor="middle">ผลขาดทุน · พันบาท</text>
  </svg>;
}

function TailLab() {
  const [extreme,setExtreme]=useState(200000);
  const losses=[...Array(94).fill(0),...Array(5).fill(20000),extreme];
  const tail=empiricalTail(losses,.95);
  return <section className="risk-viz" aria-labelledby="risk-tail-title">
    <div className="risk-heading"><p className="risk-eyebrow">ทดลอง 2 · ข้อมูลสมมติ 100 ค่า · Confidence 95%</p><h3 id="risk-tail-title">VaR เท่าเดิม แต่วันที่แย่อาจเสียหายหนักขึ้น</h3><p>ชุดข้อมูลมีผลขาดทุน 0 บาท 94 ค่า, 20,000 บาท 5 ค่า และค่ารุนแรง 1 ค่า เลื่อนเฉพาะค่ารุนแรงแล้วเปรียบเทียบ VaR กับ ES</p></div>
    <div className="risk-controls risk-controls-single"><div className="risk-control"><label htmlFor="risk-extreme">ผลขาดทุนที่รุนแรงที่สุด<output htmlFor="risk-extreme">{number(extreme)} บาท</output></label><input id="risk-extreme" type="range" min="200000" max="400000" step="10000" value={extreme} aria-valuetext={`${number(extreme)} บาท`} onChange={e=>setExtreme(Number(e.target.value))}/><div className="risk-bounds" aria-hidden="true"><span>200,000 บาท</span><span>400,000 บาท</span></div></div></div>
    <div className="risk-metrics risk-metrics-two" role="status" aria-live="polite" aria-atomic="true">
      <Metric label="VaR 95%" value={`${number(tail.var)} บาท`} testId="tail-var" note="จุดตัดผลขาดทุนที่เปอร์เซ็นไทล์ 95"/>
      <Metric label="Expected Shortfall 95%" value={`${number(tail.es)} บาท`} testId="tail-es" note="ค่าเฉลี่ยของหางผลขาดทุนที่แย่ที่สุด 5%"/>
    </div>
    <figure className="risk-chart risk-tail-chart"><figcaption><strong>ขยายดูผลขาดทุนมากที่สุด 6 ค่า</strong><span>แถบทึบ 5 แถบเป็นหาง 5% · แถบโปร่งมีค่าเท่าจุดตัด</span></figcaption><TailChart extreme={extreme} tail={tail}/><div className="risk-legend" aria-hidden="true"><span><i className="risk-legend-var"/> VaR · เส้นประ</span><span><i className="risk-legend-es"/> ES · เส้นทึบ</span></div></figure>
    <p className="risk-insight">ES = ({number(extreme)} + 4 × 20,000) ÷ 5 = <strong>{number(tail.es)} บาท</strong> ใช้ผลขาดทุน 20,000 บาทเพียง 4 จาก 5 ค่าที่ซ้ำกัน เพื่อให้มวลของหางเท่ากับ 5% พอดี</p>
    <details className="risk-details"><summary>ดูข้อมูลและวิธีเลือกหาง</summary><div className="table-scroll" role="region" aria-label="ตารางข้อมูลผลขาดทุนและจำนวนที่ใช้ในหาง" tabIndex="0"><table><caption>ทุกค่ามีน้ำหนักเท่ากัน 1% · ผลขาดทุนเป็นจำนวนบวก</caption><thead><tr><th scope="col">ผลขาดทุน (บาท)</th><th scope="col">จำนวนในชุดข้อมูล</th><th scope="col">จำนวนที่ใช้ในหาง 5%</th></tr></thead><tbody><tr><th scope="row">0</th><td>94</td><td>0</td></tr><tr><th scope="row">20,000</th><td>5</td><td>4</td></tr><tr><th scope="row">{number(extreme)}</th><td>1</td><td>1</td></tr></tbody></table></div><p className="risk-note">VaR ใช้ inverse ECDF: เรียงผลขาดทุนจากน้อยไปมากแล้วเลือกอันดับ 95 โดยไม่แทรกค่าระหว่างข้อมูล ส่วน ES เฉลี่ยมวลหาง 5% เมื่อมีค่าซ้ำตรงจุดตัดจึงใช้เฉพาะน้ำหนักที่ต้องการ</p></details>
    <p className="risk-note">ตัวอย่างเพื่ออธิบายตัววัด ไม่ใช่ข้อมูลตลาดหรือความน่าจะเป็นของผลขาดทุนจริง · VaR ไม่บอกขนาดความเสียหายเมื่อขาดทุนเกินจุดตัด</p>
  </section>;
}

function EwmaChart({values}) {
  const top=Math.ceil(Math.max(...values)*100*1.15/.5)*.5;
  const x=i=>62+i/(values.length-1)*398;
  const y=v=>202-v*100/top*160;
  return <svg viewBox="0 0 500 265" role="img" aria-labelledby="risk-ewma-chart-title risk-ewma-chart-desc">
    <title id="risk-ewma-chart-title">ความผันผวน EWMA หลังผลตอบแทนที่กำหนด แล้วตามด้วยผลตอบแทนศูนย์</title>
    <desc id="risk-ewma-chart-desc">ความผันผวนเดิม {percent(values[0],4)} หลังผลตอบแทนที่กำหนด {percent(values[1],4)} จากนั้นสมมติผลตอบแทนเป็นศูนย์จนสิ้นช่วง 20 ความผันผวนเหลือ {percent(values.at(-1),4)}</desc>
    {[0,top/2,top].map(v=><g key={v}><line className="risk-grid" x1="62" x2="460" y1={y(v/100)} y2={y(v/100)}/><text className="risk-tick" x="50" y={y(v/100)+6} textAnchor="end">{number(v,2)}%</text></g>)}
    <line className="risk-event-line" x1={x(1)} x2={x(1)} y1="35" y2="202"/>
    <polyline points={values.map((v,i)=>`${x(i)},${y(v)}`).join(' ')} className="risk-line risk-line-primary"/>
    {[0,1,20].map(i=><circle key={i} className="risk-point risk-point-primary" cx={x(i)} cy={y(values[i])} r="4"/>)}
    {[0,5,10,15,20].map(i=><text key={i} className="risk-tick" x={x(i)} y="228" textAnchor="middle">{i}</text>)}
    <text className="risk-axis-label" x="260" y="258" textAnchor="middle">ลำดับการอัปเดต · ช่วงละ 1 วัน</text>
  </svg>;
}

function EwmaLab() {
  const [lambda,setLambda]=useState(.94);
  const [shock,setShock]=useState(-4);
  const sigma=.01;
  const next=ewmaUpdate(sigma,shock/100,lambda);
  const values=ewmaDecay(sigma,shock/100,lambda,20);
  return <section className="risk-viz" aria-labelledby="risk-ewma-title">
    <div className="risk-heading"><p className="risk-eyebrow">ทดลอง 3 · EWMA · ความผันผวนเดิม 1% ต่อวัน</p><h3 id="risk-ewma-title">ข้อมูลล่าสุดเปลี่ยนประมาณการความเสี่ยงแค่ไหน?</h3><p>ปรับ λ และผลตอบแทนล่าสุด เพื่อดูน้ำหนักของข้อมูลเก่ากับข่าวใหม่ในประมาณการวันถัดไป</p></div>
    <div className="risk-controls"><div className="risk-control"><label htmlFor="risk-lambda">น้ำหนักข้อมูลเดิม (λ)<output htmlFor="risk-lambda">{number(lambda,2)}</output></label><input id="risk-lambda" type="range" min="0.80" max="0.99" step="0.01" value={lambda} aria-valuetext={`${number(lambda,2)} น้ำหนักความแปรปรวนเดิม ${number(lambda*100)} เปอร์เซ็นต์`} onChange={e=>setLambda(Number(e.target.value))}/><div className="risk-bounds" aria-hidden="true"><span>0.80 · ตอบสนองเร็ว</span><span>0.99 · ตอบสนองช้า</span></div></div><div className="risk-control"><label htmlFor="risk-shock">ผลตอบแทนล่าสุด<output htmlFor="risk-shock">{shock>0?'+':''}{number(shock,1)}%</output></label><input id="risk-shock" type="range" min="-6" max="6" step="0.5" value={shock} aria-valuetext={`${number(shock,1)} เปอร์เซ็นต์`} onChange={e=>setShock(Number(e.target.value))}/><div className="risk-bounds" aria-hidden="true"><span>−6%</span><span>+6%</span></div></div></div>
    <div className="risk-metrics risk-metrics-two" role="status" aria-live="polite" aria-atomic="true">
      <Metric label="ความผันผวนประมาณการวันถัดไป" value={percent(next,4)} testId="ewma-next" note="คำนวณจากความแปรปรวน ไม่ใช่เฉลี่ยค่า SD"/>
      <Metric label="น้ำหนักผลตอบแทนล่าสุดยกกำลังสอง" value={percent(1-lambda,0)} testId="ewma-new-weight" note={`อีก ${percent(lambda,0)} เป็นความแปรปรวนเดิม`}/>
    </div>
    <figure className="risk-chart"><figcaption><strong>สถานการณ์สมมติ: หลัง Shock ผลตอบแทนทุกวันเป็นศูนย์</strong><span>แกนตั้ง: ความผันผวนต่อวัน (%) · เส้นประ: อัปเดตหลังผลตอบแทนล่าสุด</span></figcaption><EwmaChart values={values}/></figure>
    <p className="risk-insight">σ ใหม่ = √[{number(lambda,2)} × 0.01² + {number(1-lambda,2)} × ({number(shock/100,3)})²] = <strong>{percent(next,4)} ต่อวัน</strong><br/>ผลตอบแทนบวกและลบขนาดเท่ากันให้ผลเหมือนกัน เพราะสูตรใช้ผลตอบแทนยกกำลังสอง</p>
    <details className="risk-details"><summary>ดูค่าความผันผวนแต่ละช่วง</summary><div className="table-scroll" role="region" aria-label="ตารางค่า EWMA ทั้ง 20 ช่วง" tabIndex="0"><table><caption>จุด 0 เป็นค่าก่อนอัปเดต จุด 1 ใช้ผลตอบแทนล่าสุด จุด 2–20 ใช้ผลตอบแทน 0%</caption><thead><tr><th scope="col">ลำดับ</th><th scope="col">ผลตอบแทนที่ใช้อัปเดต</th><th scope="col">ความผันผวนต่อวัน</th></tr></thead><tbody>{values.map((v,i)=><tr key={i}><th scope="row">{i}</th><td>{i===0?'—':`${number(i===1?shock:0,1)}%`}</td><td>{percent(v,4)}</td></tr>)}</tbody></table></div></details>
    <p className="risk-note">สมมติค่าเฉลี่ยผลตอบแทนเป็นศูนย์ จึงใช้ผลตอบแทนเป็น residual · หลังจุด 1 กำหนดผลตอบแทนทุกวันเป็น 0% เพื่อแสดงการลดน้ำหนักของ shock เท่านั้น กราฟนี้ไม่ใช่การพยากรณ์ราคา หรือค่าคาดหมายของความผันผวนในอนาคต</p>
  </section>;
}

// Commit all lab heights before resolving an initial deep link below a lab.
flushSync(() => {
  for (const [id,Component] of [['risk-path-lab',PathLab],['risk-tail-lab',TailLab],['risk-ewma-lab',EwmaLab]]) {
    const node=document.getElementById(id);
    if(node)createRoot(node).render(<Component/>);
  }
});
const initialHash=window.location.hash;
if(initialHash)document.fonts.ready.then(() => {
  if(window.location.hash!==initialHash)return;
  let id;
  try{id=decodeURIComponent(initialHash.slice(1));}catch{return;}
  const target=document.getElementById(id);
  if(target?.closest('main'))target.scrollIntoView({behavior:'instant',block:'start'});
});
