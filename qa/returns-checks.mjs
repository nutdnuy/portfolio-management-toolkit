import test from 'node:test';
import assert from 'node:assert/strict';
import {calculateReturns} from '../src/returns-math.mjs';
const close=(a,b)=>assert.ok(Math.abs(a-b)<=1e-10*Math.max(1,Math.abs(b)),`${a} != ${b}`);
test('one million doubles then halves; simple addition disagrees with actual wealth',()=>{
  const m=calculateReturns(1e6,[1,-.5]);
  assert.deepEqual(m.wealth,[1e6,2e6,1e6]);
  assert.deepEqual(m.gains,[1e6,-1e6]);
  close(m.cumulative,0);close(m.logSum,0);close(m.fromLog,0);close(m.naiveSum,.5);
});
test('nonzero, negative and flat examples retain the same wealth under both representations',()=>{
  for(const [returns,expected] of [[[1,-.25],1.5e6],[[.2,-.2],960000],[[0,0],1e6],[[-.95,-.95],2500],[[2,2],9e6]]){
    const m=calculateReturns(1e6,returns);close(m.wealth[2],expected);close(m.fromLog,expected/1e6-1);
  }
});
test('all slider values: log conversion, signs, positive wealth and order-independent ending',()=>{
  for(let a=-95;a<=200;a+=5)for(let b=-95;b<=200;b+=5){
    const m=calculateReturns(1e6,[a/100,b/100]), reversed=calculateReturns(1e6,[b/100,a/100]);
    close(m.fromLog,m.cumulative);close(m.logSum,Math.log(m.wealth[2]/1e6));close(reversed.wealth[2],m.wealth[2]);
    close(m.naiveSum-m.cumulative,-(a/100)*(b/100));
    assert.ok(m.wealth.every(v=>v>0));
  }
});
test('scaling initial wealth preserves return; intermediate observations cancel',()=>{
  const m=calculateReturns(1e6,[1,-.5]), scaled=calculateReturns(250,[1,-.5]);
  close(m.cumulative,scaled.cumulative);
  const subdivided=Math.log(Math.sqrt(2))+Math.log(Math.sqrt(2))+Math.log(.5);
  close(subdivided,m.logSum);
});
test('reject nonpositive wealth, undefined logarithms and invalid inputs',()=>{
  for(const initial of [0,-1,NaN,Infinity])assert.throws(()=>calculateReturns(initial,[1,-.5]),RangeError);
  for(const returns of [[-1,.5],[-2,1],[NaN,0],[Infinity,0],[0],null])assert.throws(()=>calculateReturns(1e6,returns),RangeError);
});
