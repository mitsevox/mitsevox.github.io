"""Safari history throttling must not turn an ordinary click into a route failure."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ScrollStateTests(unittest.TestCase):
    def test_sustained_scroll_flush_cooldown_and_navigation_fallback(self):
        script = r'''
import assert from 'node:assert/strict';
import {createScrollState,pushRoute} from './assets/scroll-state.js';
let time=0,y=0,eligible=true,nextID=0;
const timers=new Map(),writes=[];
const location={href:'https://example.test/games/test/'};
const history={state:{scrollY:0,retained:'metadata'},replaceState(state,unused,url){
  const recent=writes.filter(row=>time-row.time<10000);
  if(recent.length>=100)throw new DOMException('Too many history calls','SecurityError');
  this.state=state;writes.push({time,state,url});
},pushState(state,unused,url){this.state=state;location.href=String(url);}};
const state=createScrollState({history,location,readY:()=>y,canSave:()=>eligible,now:()=>time,
  setTimer:(fn,delay)=>{const id=++nextID;timers.set(id,{fn,at:time+Math.max(1,delay)});return id;},
  clearTimer:id=>timers.delete(id)});
function advance(to){
  while(true){const due=[...timers].filter(([,task])=>task.at<=to).sort((a,b)=>a[1].at-b[1].at)[0];if(!due)break;
    time=due[1].at;timers.delete(due[0]);due[1].fn();
  }
  time=to;
}
// A full minute of 120 Hz scrolling used to saturate Safari in under a second.
for(let frame=1;frame<=7200;frame++){advance(frame*1000/120);y=frame;state.save();}
advance(60500);
assert.ok(writes.length<=122);
assert.ok(writes.every(row=>writes.filter(other=>other.time>=row.time&&other.time<row.time+10000).length<=21));
assert.equal(history.state.scrollY,7200);assert.equal(history.state.retained,'metadata');
const count=writes.length;for(let i=0;i<100;i++)state.save();assert.equal(writes.length,count);
// Save the exact outgoing position even if a trailing scroll timer is pending.
y=8000;state.save();y=8123;state.save(true);
assert.equal(history.state.scrollY,8123);assert.equal(timers.size,0);
// A late timer cannot overwrite a route that's no longer eligible for saving.
y=9000;state.save();eligible=false;advance(time+500);assert.equal(history.state.scrollY,8123);
eligible=true;
// Reproduce the screenshot: replaceState throws, then a navigation tries to save.
let attempts=0;
history.replaceState=()=>{attempts++;throw new DOMException('Rate limited','SecurityError');};
y=10000;assert.doesNotThrow(()=>state.save(true));
for(let i=0;i<500;i++){advance(time+1);state.save();}
assert.equal(attempts,1);
assert.equal(pushRoute({scrollY:0},'https://example.test/wiki/',history,()=>assert.fail('Unnecessary reload')),true);
assert.equal(location.href,'https://example.test/wiki/');
// After quota recovery, saving works again and preserves unrelated state.
history.replaceState=function(value){this.state=value;attempts++;};
advance(time+10000);state.save();assert.equal(history.state.scrollY,10000);
let destination;
history.pushState=()=>{throw new DOMException('Rate limited','SecurityError');};
assert.equal(pushRoute({scrollY:0},'https://example.test/games/other/?x=1#map',history,url=>destination=url),false);
assert.equal(destination,'https://example.test/games/other/?x=1#map');
history.pushState=()=>{throw new TypeError('Genuine programming error');};
assert.throws(()=>pushRoute({},'/bad',history,()=>assert.fail()),TypeError);
console.log('Sustained scroll, exact flush, stale timer, Safari cooldown and document fallback passed.');
'''
        result = subprocess.run(['node', '--input-type=module'], input=script,
                                cwd=ROOT, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
