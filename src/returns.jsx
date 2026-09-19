import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import {calculateReturns} from './returns-math.mjs';
import './returns.css';

const number = (n, digits=0) => (Math.abs(n)<1e-10?0:n).toLocaleString('en-US',{minimumFractionDigits:digits,maximumFractionDigits:digits});
const signed = (n,digits=0) => `${n>1e-10?'+':n< -1e-10?'−':''}${number(Math.abs(n),digits)}`;
const presets = [
  {label:'+100% แล้ว −50%', values:[100,-50]},
  {label:'+100% แล้ว −25%', values:[100,-25]},
  {label:'+20% แล้ว −20%', values:[20,-20]},
];

function WealthChart({model}) {
  const values=model.wealth.map(v=>v/1e6);
  const max=Math.ceil(Math.max(...values)*1.15*2)/2;
  const y=v=>250-v/max*194;
  return <svg viewBox="0 0 480 302" role="img" aria-labelledby="returns-wealth-title returns-wealth-desc">
    <title id="returns-wealth-title">เงินลงทุน ณ เริ่มต้นและสิ้นปีทั้งสอง หน่วยล้านบาท</title>
    <desc id="returns-wealth-desc">{model.wealth.map((v,i)=>`${['เริ่มต้น','สิ้นปี 1','สิ้นปี 2'][i]} ${number(v)} บาท`).join(' · ')}</desc>
    {[0,max/2,max].map(v=><g key={v}><line className="rv-grid" x1="54" x2="468" y1={y(v)} y2={y(v)}/><text className="rv-tick" x="44" y={y(v)+6} textAnchor="end">{number(v,v%1?2:0)}</text></g>)}
    {values.map((v,i)=>{const x=112+i*146;return <g key={i}>
      <rect x={x-35} y={y(v)} width="70" height={250-y(v)} className={`rv-bar rv-bar-${i}`}/>
      <text className="rv-value" x={x} y={y(v)-12} textAnchor="middle">{number(v,3)}</text>
      <text className="rv-axis" x={x} y="283" textAnchor="middle">{['เริ่มต้น','ปี 1','ปี 2'][i]}</text>
    </g>})}
  </svg>;
}

function LogChart({model}) {
  const values=[...model.logs,model.logSum];
  const max=Math.ceil(Math.max(.25,...values.map(Math.abs))*1.2*2)/2;
  const y=v=>153-v/max*100;
  return <svg viewBox="0 0 480 302" role="img" aria-labelledby="returns-log-title returns-log-desc">
    <title id="returns-log-title">Log return ของปี 1 ปี 2 และผลรวม หน่วยทศนิยม</title>
    <desc id="returns-log-desc">ปี 1 {number(values[0],6)} บวกปี 2 {number(values[1],6)} เท่ากับ {number(values[2],6)}</desc>
    {[-max,0,max].map(v=><g key={v}><line className={v===0?'rv-zero':'rv-grid'} x1="62" x2="468" y1={y(v)} y2={y(v)}/><text className="rv-tick" x="50" y={y(v)+6} textAnchor="end">{number(v,1)}</text></g>)}
    {values.map((v,i)=>{const x=116+i*143;return <g key={i}>
      {Math.abs(v)<1e-10?<line x1={x-34} x2={x+34} y1={y(0)} y2={y(0)} className="rv-total-zero"/>:<rect x={x-34} y={Math.min(y(v),y(0))} width="68" height={Math.abs(y(v)-y(0))} className={`rv-log-bar rv-log-bar-${i}`}/>}
      <text className="rv-value" x={x} y={y(v)+(v< -1e-10?24:-12)} textAnchor="middle">{signed(v,4)}</text>
      <text className="rv-axis" x={x} y="289" textAnchor="middle">{['ปี 1','ปี 2','รวม'][i]}</text>
    </g>})}
  </svg>;
}

function ReturnsLab() {
  const [rates,setRates]=useState([100,-50]);
  const model=calculateReturns(1e6,rates.map(v=>v/100));
  const setRate=(i,v)=>setRates(prev=>prev.map((x,j)=>i===j?v:x));
  const same=Math.abs(model.cumulative-model.naiveSum)<1e-10;
  return <section className="returns-viz" aria-labelledby="returns-lab-title">
    <div className="rv-heading"><p className="rv-eyebrow">ลองด้วยตัวเอง · เงินเริ่มต้น 1,000,000 บาท</p><h3 id="returns-lab-title">เปลี่ยนผลตอบแทน แล้วติดตามเงินก้อนเดิม</h3><p>เลื่อนค่าทั้งสองปี หรือเลือกตัวอย่าง แล้วเทียบตัวคูณเงินกับผลรวม Log return</p></div>
    <div className="rv-presets" role="group" aria-label="เลือกตัวอย่างผลตอบแทน">{presets.map(p=><button key={p.label} type="button" aria-pressed={rates.every((v,i)=>v===p.values[i])} onClick={()=>setRates([...p.values])}>{p.label}</button>)}</div>
    <div className="rv-controls">{rates.map((rate,i)=><div className="rv-control" key={i}>
      <label htmlFor={`returns-year-${i+1}`}>ผลตอบแทนปีที่ {i+1}<output htmlFor={`returns-year-${i+1}`}>{signed(rate)}%</output></label>
      <input id={`returns-year-${i+1}`} type="range" min="-95" max="200" step="5" value={rate} aria-valuetext={`${rate} เปอร์เซ็นต์`} onChange={e=>setRate(i,Number(e.target.value))}/>
      <div className="rv-bounds" aria-hidden="true"><span>−95%</span><span>+200%</span></div>
    </div>)}</div>
    <div className="rv-toolbar"><button type="button" onClick={()=>setRates(([a,b])=>[b,a])}>สลับลำดับปี</button><p>สลับแล้วลองดูว่าเงินระหว่างทางกับเงินปลายทางเปลี่ยนเหมือนกันไหม</p></div>
    <div className="rv-answer" role="status" aria-live="polite" aria-atomic="true">
      <div><span>เงินเมื่อสิ้นปีที่ 2</span><strong data-testid="terminal-wealth">{number(model.wealth[2])} <small>บาท</small></strong></div>
      <p>ผลตอบแทนสะสม <b data-testid="cumulative-return">{signed(model.cumulative*100,2)}%</b><br/>จากเงินเริ่มต้น 1,000,000 บาท</p>
    </div>
    <div className="rv-charts">
      <figure><figcaption><strong>1. เงินโตด้วยการคูณ</strong><span>มูลค่า ณ สิ้นปี · ล้านบาท</span></figcaption><WealthChart model={model}/></figure>
      <figure><figcaption><strong>2. Log return รวมด้วยการบวก</strong><span>Log return · ทศนิยม ไม่ใช่เปอร์เซ็นต์กำไร</span></figcaption><LogChart model={model}/></figure>
    </div>
    <div className="rv-equations">
      <div><span>คูณตัวคูณเงินแต่ละปี</span><p data-testid="gross-equation">{number(model.gross[0],2)} × {number(model.gross[1],2)} = <b>{number(model.wealth[2]/model.initial,4)} เท่า</b></p><small>หักเงินต้น 1 เท่า → ผลตอบแทน {signed(model.cumulative*100,2)}%</small></div>
      <div><span>บวก Log return แต่ละปี</span><p data-testid="log-equation">{signed(model.logs[0],4)} {model.logs[1]<0?'−':'+'} {number(Math.abs(model.logs[1]),4)} = <b>{signed(model.logSum,4)}</b></p><small>แปลงกลับด้วย e<sup>{number(model.logSum,4)}</sup> − 1 → {signed(model.fromLog*100,2)}%</small></div>
    </div>
    <p className="rv-pitfall"><strong>ถ้าบวกเปอร์เซ็นต์ตรง ๆ:</strong> {signed(rates[0])}% {rates[1]<0?'−':'+'} {number(Math.abs(rates[1]))}% = <span data-testid="naive-return">{signed(model.naiveSum*100,2)}%</span> {same?'กรณีนี้ได้เท่ากันเพราะมีปีหนึ่งให้ผลตอบแทนศูนย์ ลองปรับให้ทั้งสองปีไม่เป็นศูนย์':'ซึ่งต่างจากผลตอบแทนสะสม เพราะแต่ละปีคิดจากฐานเงินต่างกัน'}</p>
    <details className="rv-details"><summary>ดูจำนวนเงินและผลตอบแทนทีละปี</summary><div className="table-scroll" tabIndex="0" role="region" aria-label="ตารางเงินลงทุนสองปี เลื่อนแนวนอนเพื่อดูครบ"><table><thead><tr><th scope="col">ปี</th><th scope="col">เงินต้นช่วง (บาท)</th><th scope="col">Simple return</th><th scope="col">กำไร / ขาดทุน (บาท)</th><th scope="col">เงินปลายช่วง (บาท)</th><th scope="col">Log return</th></tr></thead><tbody>{rates.map((v,i)=><tr key={i}><th scope="row">{i+1}</th><td>{number(model.wealth[i])}</td><td>{signed(v)}%</td><td>{signed(model.gains[i])}</td><td>{number(model.wealth[i+1])}</td><td>{signed(model.logs[i],6)}</td></tr>)}</tbody></table></div></details>
    <p className="rv-note">ตัวอย่างสมมติ 2 ปี ไม่มีฝากถอน ปันผล ภาษี หรือค่าใช้จ่าย · ตัวทดลองจำกัดผลตอบแทนให้มากกว่า −100% เพื่อให้มูลค่าเป็นบวกและคำนวณ log ได้ · คำนวณด้วยค่าก่อนปัดเศษ แสดง log 4 ตำแหน่ง</p>
  </section>;
}
const node=document.getElementById('returns-lab');
if(node)createRoot(node).render(<ReturnsLab/>);
