/** Same moments, different shapes: authored hypothetical monthly observations. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const regular=[-3,-2,-1,-1,0,0,1,1,2,3].map(z=>1+2*z/Math.sqrt(3));
const left=[-3,...Array(9).fill(1/3)].map(z=>1+2*z);
const bins=[-6,-4,-2,0,2,4,6];
const rows=[['Regular',regular,'#6200ee'],['LeftTail',left,'#00796e']];
const counts=data=>bins.slice(0,-1).map((lo,i)=>data.filter(x=>x>=lo&&(i===5?x<=bins[i+1]:x<bins[i+1])).length);
assert.deepEqual(counts(regular),[0,1,3,2,3,1]);
assert.deepEqual(counts(left),[1,0,0,9,0,0]);
const font=(name,file)=>`@font-face{font-family:'${name}';src:url(data:font/woff2;base64,${fs.readFileSync(path.join(root,'assets/fonts',file)).toString('base64')}) format('woff2');font-weight:400}`;
for(const width of [720,400]){
 const mobile=width===400, height=mobile?640:670, leftX=48,right=width-24,plotWidth=right-leftX;
 const size=mobile?15:19;
 let body=`<rect width="${width}" height="${height}" fill="#fff"/><text x="24" y="36" font-size="${mobile?20:25}">ค่าเฉลี่ยและ SD เท่ากัน แต่รูปทรงต่างกัน</text><text x="24" y="65" font-size="${size}" fill="#616161">ข้อมูลสมมติ 10 เดือน · ไม่ใช่ข้อมูลตลาด</text>`;
 rows.forEach(([name,data,color],panel)=>{
   const top=110+panel*255,baseline=top+157,step=plotWidth/6,cs=counts(data);
   body+=`<text x="24" y="${top-10}" font-size="${size+2}">${name} · mean 1% · SD 2%</text><text x="24" y="${top+12}" font-size="${size-1}" fill="#616161">จำนวนเดือน</text>`;
   for(const count of [0,5,10]){const y=baseline-count*13;body+=`<line x1="${leftX}" x2="${right}" y1="${y}" y2="${y}" stroke="#ddd"/><text x="${leftX-8}" y="${y+5}" text-anchor="end" font-size="${size-1}">${count}</text>`;}
   cs.forEach((count,i)=>{const x=leftX+i*step+2,y=baseline-count*13;body+=`<rect data-series="${name}" data-bin-left="${bins[i]}" data-count="${count}" x="${x}" y="${y}" width="${step-4}" height="${count*13}" fill="${color}"/><text x="${x+(step-4)/2}" y="${y-7}" text-anchor="middle" font-size="${size}">${count}</text>`;});
   bins.forEach((n,i)=>body+=`<text x="${leftX+i*step}" y="${baseline+23}" text-anchor="middle" font-size="${size-1}">${n}</text>`);
   body+=`<text x="${width/2}" y="${baseline+49}" text-anchor="middle" font-size="${size}">ผลตอบแทนรายเดือน (%)</text>`;
 });
 body+=`<text x="24" y="${height-47}" font-size="${size-1}" fill="#616161">แต่ละช่วงกว้าง 2 percentage points</text><text x="24" y="${height-23}" font-size="${size-1}" fill="#616161">SD ใช้ตัวหาร n · ทั้งสองชุดไม่ใช่ Normal</text>`;
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="chart-title chart-desc"><title id="chart-title">Same mean and SD, different monthly return shapes</title><desc id="chart-desc">Ten hypothetical observations in each panel, shared axes. Six bins from minus six to plus six percent in two-percentage-point steps. Regular counts zero, one, three, two, three, one. LeftTail counts one, zero, zero, nine, zero, zero. Both means one percent and population standard deviations two percent.</desc><metadata>Original hypothetical data. Bar heights show actual counts. No empirical claim. QuantCorner / QuantSeras no-image-generator route.</metadata><style>${font('Roboto','roboto-latin-400-normal.woff2')}${font('Noto Sans Thai','noto-sans-thai-thai-400-normal.woff2')}text{font-family:Roboto,'Noto Sans Thai',sans-serif;fill:#212121}</style>${body}</svg>\n`;
 fs.writeFileSync(path.join(root,'assets/charts',`extreme-risk-shapes${mobile?'-mobile':''}.svg`),svg);
}
console.log('Verified histogram counts and generated 720px/400px Extreme Risk figures.');
