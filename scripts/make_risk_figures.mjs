/** Hypothetical scenario and diversification figures; no empirical observations. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'assets/charts');
const font=(name,file)=>`@font-face{font-family:'${name}';src:url(data:font/woff2;base64,${fs.readFileSync(path.join(root,'assets/fonts',file)).toString('base64')}) format('woff2')}`;
const fonts=font('Roboto','roboto-latin-400-normal.woff2')+font('Noto Sans Thai','noto-sans-thai-thai-400-normal.woff2');
const purple='#6200ee',teal='#00796e';
const sigma=rho=>.2*Math.sqrt((1+rho)/2);
assert.ok(Math.abs(sigma(-.5)-.1)<1e-12);assert.ok(Math.abs(sigma(0)-Math.sqrt(.02))<1e-12);assert.equal(sigma(1),.2);
for(const outcomes of [[.05,.15],[-.2,.4]])assert.ok(Math.abs((outcomes[0]+outcomes[1])/2-.1)<1e-12);
const text=(x,y,s,size=18,extra='')=>`<text x="${x}" y="${y}" font-size="${size}" ${extra}>${s}</text>`;
const line=(x1,y1,x2,y2,extra='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" ${extra}/>`;
function save(name,w,h,title,desc,body){fs.writeFileSync(path.join(out,name),`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-labelledby="title desc"><title id="title">${title}</title><desc id="desc">${desc}</desc><metadata>Original hypothetical teaching example. Generated deterministically by scripts/make_risk_figures.mjs. QuantCorner / QuantSeras Material 2.</metadata><style>${fonts}text{font-family:Roboto,'Noto Sans Thai',sans-serif;fill:#212121}.muted{fill:#616161}</style><rect width="${w}" height="${h}" fill="#fff"/>${body}</svg>\n`)}
fs.mkdirSync(out,{recursive:true});
for(const mobile of [false,true]){
 const w=mobile?400:720,h=mobile?480:450,left=mobile?48:70,right=w-32,x=r=>left+(r+.2)/.6*(right-left),size=mobile?16:19;
 let b=text(24,40,'ค่าเฉลี่ยเท่ากัน แต่ผลลัพธ์ต่างกัน',mobile?22:28)+text(24,72,'ผลตอบแทนปลายปี · สถานการณ์ละ 50%',size,'class="muted"');
 for(const tick of [-.2,-.1,0,.1,.2,.3,.4]){b+=line(x(tick),116,x(tick),344,`stroke="${tick===0?'#616161':'#e1e1e1'}" ${tick===0?'stroke-dasharray="5 5"':''}`);b+=text(x(tick),374,`${Math.round(tick*100)}%`,mobile?14:17,'text-anchor="middle" class="muted"')}
 for(const [i,[label,returns,sd,color]] of [['P',[.05,.15],5,purple],['Q',[-.2,.4],30,teal]].entries()){
 const y=180+i*130;b+=text(24,y-38,`พอร์ต ${label} · SD ${sd}% ต่อปี`,size);
 b+=line(x(returns[0]),y,x(returns[1]),y,`stroke="${color}" stroke-width="4"`);
 for(const r of returns)b+=`<circle cx="${x(r)}" cy="${y}" r="7" fill="${color}"/>`+text(x(r),y+30,`${r>0?'+':''}${Math.round(r*100)}%`,size,`text-anchor="${r===-.2?'start':r===.4?'end':'middle'}"`);
 b+=`<path d="M ${x(.1)} ${y-8} l 8 8 l -8 8 l -8 -8 z" fill="#fff" stroke="#212121" stroke-width="2"/>`;
 }
 b+=text(24,415,'◇ ค่าเฉลี่ยคาดหวัง +10% ทั้งสองพอร์ต',size);
 if(mobile)b+=text(24,446,'จุดทึบ = ผลลัพธ์ที่เป็นไปได้ 2 กรณี',15,'class="muted"');
 save(`risk-outcomes${mobile?'-mobile':''}.svg`,w,h,'ค่าเฉลี่ยสิบเปอร์เซ็นต์เท่ากัน แต่พอร์ต P กับ Q กระจายตัวต่างกัน','ตัวอย่างสมมติ พอร์ต P ให้ผลตอบแทน 5 หรือ 15 เปอร์เซ็นต์ พอร์ต Q ให้ผลตอบแทนลบ 20 หรือบวก 40 เปอร์เซ็นต์ โอกาสกรณีละครึ่ง ส่วนเบี่ยงเบนมาตรฐานตามการแจกแจงคือ 5 และ 30 เปอร์เซ็นต์ตามลำดับ เส้นเชื่อมแสดงระยะระหว่างสองผลลัพธ์ ไม่ใช่ผลลัพธ์ต่อเนื่อง',b);
 const H=mobile?480:470,X=r=>left+(r+1)/2*(right-left),Y=v=>358-v/.2*222;
 let c=text(24,40,'ความสัมพันธ์เปลี่ยน ความเสี่ยงก็เปลี่ยน',mobile?20:28)+text(24,72,'พอร์ต 50/50 · สินทรัพย์ละ 20% ต่อปี',size,'class="muted"')+text(24,105,'Volatility พอร์ต (% ต่อปี)',mobile?15:18,'class="muted"');
 for(const t of [0,.05,.1,.15,.2])c+=line(left,Y(t),right,Y(t),'stroke="#e1e1e1"')+text(left-10,Y(t)+6,`${Math.round(t*100)}%`,mobile?14:17,'text-anchor="end" class="muted"');
 for(const r of [-1,-.5,0,.5,1])c+=text(X(r),388,String(r),mobile?15:18,'text-anchor="middle" class="muted"');
 const points=Array.from({length:201},(_,i)=>{const r=-1+i/100;return `${X(r)},${Y(sigma(r))}`}).join(' ');
 c+=`<polyline points="${points}" fill="none" stroke="${purple}" stroke-width="3"/>`;
 for(const r of [-.5,0,1]){const yy=Y(sigma(r));c+=`<circle cx="${X(r)}" cy="${yy}" r="5" fill="#fff" stroke="${purple}" stroke-width="3"/>`+text(X(r)+(r===0?8:0),yy+(r===0?28:-16),`${(sigma(r)*100).toFixed(2)}%`,size,`text-anchor="${r===1?'end':r===0?'start':'middle'}"`)}
 c+=text((left+right)/2,425,'Correlation (ρ)',size,'text-anchor="middle"')+text(24,455,'แบบจำลองสมมติ · คงน้ำหนักและความผันผวน',mobile?14:17,'class="muted"');
 save(`risk-correlation${mobile?'-mobile':''}.svg`,w,H,'ความผันผวนของพอร์ตสองสินทรัพย์เทียบกับ correlation','น้ำหนักตัวละครึ่ง ความผันผวนสินทรัพย์ละ 20 เปอร์เซ็นต์ต่อปี คอร์เรเลชันลบ 0.5 ให้พอร์ต 10 เปอร์เซ็นต์ ศูนย์ให้ 14.14 เปอร์เซ็นต์ และหนึ่งให้ 20 เปอร์เซ็นต์ ความสัมพันธ์ลบหนึ่งทำให้ความเสี่ยงตามแบบจำลองนี้เป็นศูนย์ ไม่ใช่หลักฐานว่าทำได้จริงในตลาด',c);
}
console.log('Generated 4 responsive SVG assets from explicit scenario probabilities and two-asset variance.');
