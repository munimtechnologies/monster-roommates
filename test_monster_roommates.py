"""Tests for Monster Roommates (Apache-2.0), by MV2 of Munim, Inc., made with AI agents.

Static checks always run. With Node.js installed, the rules block (<script id="logic">) runs and
selfTestLogic() must return no problems (every house on the street and every Daily House has exactly one
answer, proved by the solver), and the whole page runs against a stub browser (a canvas that rejects NaN
and negative radii, pointer and key events, localStorage, a fake clock) in five modes: #selftest, normal
play, #demo, #cover, and normal play on RUN with a fake RUN SDK (saved street, a friend's share link,
the rewarded ad, sharing, the daily leaderboard and a reminder).
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

GAME_FILE = "index.html"

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, GAME_FILE), encoding="utf-8") as f:
    HTML = f.read()
LOGIC = re.search(r'<script id="logic">(.*?)</script>', HTML, re.S).group(1)
PAGE = "\n".join(re.findall(r"<script>(.*?)</script>", HTML, re.S))

HARNESS = """
;(function(){
  const problems=selfTestLogic();
  console.log(JSON.stringify({problems:problems.slice(0,25)}));
  process.exitCode=problems.length?1:0;
})();
"""

# a stub browser: enough of document, window, canvas, events and storage to run the page script
STUB = r"""
"use strict";
const __clock={t:1000};
try{Object.defineProperty(globalThis,"performance",{value:{now:()=>__clock.t},configurable:true,writable:true});}catch(e){performance.now=()=>__clock.t;}
const __raf=[];globalThis.requestAnimationFrame=cb=>{__raf.push(cb);return __raf.length;};
const __handlers={};globalThis.addEventListener=(type,fn)=>{(__handlers[type]=__handlers[type]||[]).push(fn);};
function __fire(type,props){const e=Object.assign({preventDefault(){},button:0,pointerType:"mouse",shiftKey:false},props);for(const fn of (__handlers[type]||[]))fn(e);}
function __click(x,y,button){__fire("pointermove",{clientX:x,clientY:y});__fire("pointerdown",{clientX:x,clientY:y,button:button||0});}
function __clickL(x,y,button){__click(view.ox+x*view.scale,view.oy+y*view.scale,button);}
function __key(key,extra){__fire("keydown",Object.assign({key},extra||{}));}
function __frames(n,dt){for(let k=0;k<n;k++){__clock.t+=dt*1000;const cbs=__raf.splice(0);for(const cb of cbs)cb(__clock.t);}}
function __num(p,a){for(const x of a)if(typeof x==="number"&&!isFinite(x))throw new Error("non-finite number passed to "+String(p));}
const __any=new Proxy(function(){},{get(t,p){if(p===Symbol.toPrimitive)return()=>0;if(p==="then")return undefined;return __any;},apply(){return __any;},construct(){return __any;},set(){return true;}});
function __ctx(){
  const store={};
  return new Proxy({},{
    get(t,p){
      if(p in store)return store[p];
      if(p==="measureText")return s=>({width:String(s).length*11});
      if(p==="createLinearGradient")return(...a)=>{__num(p,a);return {addColorStop(){}};};
      return(...a)=>{
        __num(p,a);
        if(p==="arc"&&a[2]<0)throw new Error("negative arc radius "+a[2]);
        if(p==="ellipse"&&(a[2]<0||a[3]<0))throw new Error("negative ellipse radius");
        if(p==="arcTo"&&a[4]<0)throw new Error("negative arcTo radius");
      };
    },
    set(t,p,v){if(typeof v==="number"&&!isFinite(v))throw new Error("bad "+String(p)+": "+v);store[p]=v;return true;}
  });
}
function __el(tag){
  const e={tag,hidden:true,textContent:"",style:{},children:[],onclick:null,classList:{add(){}},appendChild(c){this.children.push(c);return c;}};
  if(tag==="canvas"){e.width=300;e.height=150;e.getContext=()=>__ctx();e.toDataURL=()=>"data:image/png;base64,AAAA";}
  return e;
}
const __els={c:__el("canvas"),test:__el("div"),covers:__el("div")};
globalThis.document={getElementById:id=>__els[id],createElement:__el,body:__el("body"),hidden:false,addEventListener(){}};
globalThis.window=globalThis;globalThis.innerWidth=1280;globalThis.innerHeight=720;globalThis.devicePixelRatio=1;
globalThis.location={hash:__HASH__};
const __ls=new Map();
Object.defineProperty(globalThis,"localStorage",{value:{getItem:k=>__ls.has(k)?__ls.get(k):null,setItem:(k,v)=>__ls.set(k,String(v))},configurable:true,writable:true});
globalThis.AudioContext=__any;
// move every tenant into its room with clicks: the tenant's card, then the room
function __solve(){for(let a=0;a<house.n;a++){const t=tokenRect(a,house.n);__clickL(t.x+20,t.y+20);const r=roomRect(house,house.sol[a]);__clickL(r.x+r.w/2,r.y+r.h/2);}}
"""

# a fake RUN SDK with the calls the game uses; storage follows RUN's rules (string values, no dots in keys)
RUN_STUB = r"""
const __runStore=new Map([["monsterroommates_v1",JSON.stringify({level:5,hints:0,met:6,solved:4,stars:{"1":3,"2":3,"3":3,"4":2},mode:"street"})]]);
const __shares=[],__notes=[],__scores=[],__ads={shown:0};
globalThis.RundotGameAPI={
  appStorage:{
    getItem:async k=>__runStore.has(k)?__runStore.get(k):null,
    setItem:async(k,v)=>{if(typeof v!=="string"||String(k).includes("."))throw new Error("bad storage call");__runStore.set(k,v);}
  },
  app:{resolveLaunchIntent:async()=>({kind:"share",params:{house:"L2",moves:"7"}})},
  social:{shareLinkAsync:async o=>{__shares.push(o);return {shareUrl:"link",shareLinkId:"1"};}},
  leaderboard:{submitScore:async o=>{__scores.push(o);return {accepted:true,rank:3,isAnomaly:false};}},
  ads:{isRewardedAdReadyAsync:async()=>true,showRewardedAdAsync:async()=>{__ads.shown++;return true;}},
  notifications:{submitMessageAsync:async o=>{__notes.push(o);return {results:[]};}}
};
const __tick=()=>new Promise(r=>setTimeout(r,10));
"""

AFTER = {
    "#selftest": r"""
__frames(3,0.016);
console.log(JSON.stringify({box:__els.test.textContent,hidden:__els.test.hidden}));
""",
    "": r"""
const __out={};
__frames(5,0.016);
__out.lands=key==="L1"&&phase==="play"&&overlay===null&&house.n===3&&pos.every(p=>p<0);
__key("m");__out.muted=save.mute===true;__key("M");__out.unmuted=save.mute===false;
// house 1 with clicks
__solve();
__out.won1=phase==="won"&&result.stars===3&&save.level===2;
__frames(12,0.05);__clickL(nextBtn().x+20,nextBtn().y+20);__frames(2,0.016);
__out.house2=key==="L2"&&phase==="play";
__out.savedLevel=JSON.parse(__ls.get(SAVE_KEY)).level;
// a broken rule makes its room go bump
{let ta=-1,tp=-1;const R=house.cols*house.rows;
 for(let a=0;a<house.n&&ta<0;a++)for(let p=0;p<R&&ta<0;p++){const q=house.ms.map(()=>-1);q[a]=p;if(house.rules.some(r=>ruleStatus(house,r,q)==="bad")){ta=a;tp=p;}}
 if(ta>=0){const t=tokenRect(ta,house.n);__clickL(t.x+20,t.y+20);const r=roomRect(house,tp);__clickL(r.x+r.w/2,r.y+r.h/2);
   __out.bump=pos[ta]===tp&&bumps[tp]!=null;
   // the same card tapped twice sends the tenant back to the doorstep
   __clickL(t.x+20,t.y+20);__clickL(t.x+20,t.y+20);__out.unplace=pos[ta]===-1;}}
// keys: 1 picks the first tenant, Escape lets go
__key("1");__out.keySel=sel===0;__key("Escape");__out.keyEsc=sel===null;
{const h0=save.hints;__clickL(BTN.hint.x+20,BTN.hint.y+20);__out.hint=save.hints===h0-1&&used===1&&fixed.some(Boolean);}
__clickL(BTN.restart.x+20,BTN.restart.y+20);__out.restart=pos.every((p,a)=>fixed[a]?p===house.sol[a]:p<0);
__solve();
__out.won2=phase==="won"&&result.stars<=2&&save.level===3;
__frames(12,0.05);__key("Enter");__frames(2,0.016);__out.keyNext=key==="L3";
// the Daily House and back
__clickL(BTN.mode.x+20,BTN.mode.y+20);__out.daily=save.mode==="daily"&&key==="D"+today()&&house.n===7;
__solve();__out.dailyWon=phase==="won"&&result.first===true&&save.daily.streak===1&&save.dailyDone===today();
__frames(12,0.05);__clickL(nextBtn().x+20,nextBtn().y+20);__out.back=save.mode==="street"&&key==="L3";
// house 4 brings a new tenant
__solve();__frames(12,0.05);__clickL(nextBtn().x+20,nextBtn().y+20);
__out.tenant=overlay==="tenant"&&key==="L4"&&tenantIdx===5;
__clickL(TENANT_BTN.x+20,TENANT_BTN.y+20);__out.tenantClosed=overlay===null&&save.met===6;
// a phone-shaped window
globalThis.innerWidth=390;globalThis.innerHeight=844;__fire("resize",{});__frames(3,0.016);
__out.phone=Math.abs(view.scale-390/720)<1e-9&&Math.abs(view.ox)<1e-6;
{const t=tokenRect(0,house.n);__clickL(t.x+20,t.y+20);__out.phoneTap=sel===0;}
__frames(10,0.05);
console.log(JSON.stringify(__out));
""",
    "#demo": r"""
for(let k=0;k<1200;k++)__frames(1,0.05);
console.log(JSON.stringify({level:save.level,saved:__ls.has(SAVE_KEY),demo}));
""",
    "#cover": r"""
__frames(2,0.016);
console.log(JSON.stringify({children:__els.covers.children.length,hidden:__els.covers.hidden,srcs:__els.covers.children.filter(c=>c.tag==="img").map(c=>c.src.slice(0,22))}));
""",
}

RUN_AFTER = r"""
(async()=>{
const __o={};
__o.waits=ready===false;
__frames(2,0.016);
{const r=tokenRect(0,house.n);__clickL(r.x+20,r.y+20);__o.blocked=sel===null;}
await __tick();await __tick();
__o.ready=ready===true;
__o.loaded=save.solved===4&&save.met===6&&save.level===5;
__o.friend=save.mode==="friend"&&key==="L2"&&save.friendMoves===7;
await __tick();
__o.adOffered=adOffer();
__clickL(BTN.hint.x+20,BTN.hint.y+20);await __tick();await __tick();
__o.adPaid=__ads.shown===1&&save.hints===2;
__solve();
__o.friendWon=phase==="won"&&result.mode==="friend"&&result.friendMoves===7&&save.friend==="";
await __tick();
__o.savedRun=JSON.parse(__runStore.get("monsterroommates_v1")).friend==="";
__frames(12,0.05);
__clickL(SHARE_BTN.x+20,SHARE_BTN.y+20);await __tick();
__o.shared=__shares.length===1&&__shares[0].shareParams.house==="L2"&&__shares[0].shareParams.moves==="3";
__clickL(nextBtn().x+20,nextBtn().y+20);__frames(2,0.016);
__o.backHome=save.mode==="street"&&key==="L5";
// today's Daily House: the leaderboard and tomorrow's reminder
__clickL(BTN.mode.x+20,BTN.mode.y+20);__frames(2,0.016);
__o.daily=save.mode==="daily"&&key==="D"+today();
__solve();await __tick();await __tick();
__o.dailyWon=phase==="won"&&result.first===true&&result.score>0;
__o.scored=__scores.length===1&&__scores[0].score===result.score&&__scores[0].duration>=1;
__o.rank=dailyRank===3;
const __n=__notes[__notes.length-1];
__o.reminder=!!__n&&__n.channels.join()==="local"&&__n.notificationId==="daily-house"&&!isNaN(Date.parse(__n.triggerAt));
__o.runSaved=JSON.parse(__runStore.get("monsterroommates_v1")).dailyDone===today();
console.log(JSON.stringify(__o));
})().catch(e=>{console.log(JSON.stringify({error:String(e&&e.stack||e)}));process.exitCode=1;});
"""


def node(path):
    return subprocess.run(["node", path], capture_output=True, text=True, encoding="utf-8", timeout=600)


def run_page(hash_, prelude="", after=None):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "page.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(STUB.replace("__HASH__", json.dumps(hash_)) + prelude + LOGIC + "\n" + PAGE + "\n"
                    + (AFTER[hash_] if after is None else after))
        out = node(path)
    if out.returncode != 0:
        raise AssertionError("page run %r failed:\n%s\n%s" % (hash_, out.stdout[-3000:], out.stderr[-3000:]))
    lines = [l for l in out.stdout.splitlines() if l.startswith("{")]
    return json.loads(lines[-1])


class Static(unittest.TestCase):
    def test_one_self_contained_file(self):
        # RUN serves the build folder as is; one file that works offline and inside an app webview
        self.assertIsNone(re.search(r'\b(src|href)\s*=\s*["\']?(https?:)?//', HTML))
        self.assertIsNone(re.search(r'\b(fetch|import)\(\s*["\']https?://', HTML))
        self.assertIsNone(re.search(r"<link\b[^>]*stylesheet", HTML))
        self.assertNotIn("http://", HTML)
        self.assertNotIn("https://", HTML)

    def test_logic_has_no_browser_code(self):
        for name in ("document", "window", "AudioContext", "requestAnimationFrame", "localStorage", "RundotGameAPI"):
            self.assertIsNone(re.search(r"\b" + name + r"\b", LOGIC), name + " in the rules block")
        self.assertIn("function selfTestLogic(", LOGIC)
        self.assertIn("function countSolutions(", LOGIC)
        self.assertRegex(LOGIC, r"\bconst W=720,H=1280;")

    def test_audio_waits_for_a_gesture(self):
        self.assertEqual(len(re.findall(r"new \(window\.AudioContext", PAGE)), 1)
        self.assertRegex(PAGE, r'addEventListener\("pointerdown",[^\n]*audio\.unlock\(\)')
        self.assertRegex(PAGE, r'addEventListener\("keydown",e=>\{\s*audio\.unlock\(\)')
        self.assertIn("audio.started()", PAGE)

    def test_sound_can_be_turned_off_on_screen_and_with_m(self):
        self.assertRegex(PAGE, r'e\.key==="m"\|\|e\.key==="M"\)\{audio\.toggle\(\)')
        self.assertIn('"🔇 Sound"', PAGE)

    def test_progress_is_kept(self):
        self.assertIn('SAVE_KEY="monsterroommates.v1"', PAGE)
        self.assertRegex(PAGE, r"localStorage\.setItem\(SAVE_KEY")
        # RUN has no localStorage in its game frame; its storage keys may not contain a dot
        key = re.search(r'RUN_KEY="([^"]+)"', PAGE).group(1)
        self.assertNotIn(".", key)
        self.assertIn("RUN.appStorage.setItem(RUN_KEY", PAGE)
        self.assertNotIn("requestFullscreen", HTML)

    def test_every_run_sdk_call_is_guarded(self):
        # RUN's docs: every SDK method can reject, and unhandled rejections crash the app
        calls = list(re.finditer(r"RUN\.\w+\.\w+\(", PAGE))
        self.assertGreaterEqual(len(calls), 8)
        for m in calls:
            self.assertEqual(PAGE[m.start() - 8:m.start()], "sdk(()=>", PAGE[m.start() - 40:m.end() + 20])
        self.assertIn("const RUN=window.RundotGameAPI||null;", PAGE)
        self.assertIn("RUN.leaderboard.submitScore(", PAGE)

    def test_selftest_cover_and_demo_hooks(self):
        self.assertIn('location.hash==="#selftest"', PAGE)
        self.assertIn('location.hash==="#cover"', PAGE)
        self.assertIn('location.hash==="#demo"', PAGE)

    def test_disclosure_licence_and_wording(self):
        self.assertIn("Made by MV2 of Munim, Inc. with AI agents", HTML)
        self.assertIn("Apache-2.0", HTML)
        self.assertIsNone(re.search(r"MV2[^.]{0,60}\b(an AI|a bot|AI assistant)\b", HTML))
        self.assertIsNone(re.search(r"(License|Licence)\s*:\s*MIT|MIT License", HTML))


@unittest.skipUnless(shutil.which("node"), "Node.js is not installed")
class Node(unittest.TestCase):
    def test_rules(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "logic.js")
            with open(path, "w", encoding="utf-8") as f:
                f.write(LOGIC + "\n" + HARNESS)
            out = node(path)
        self.assertEqual(out.returncode, 0, out.stdout[-3000:] + out.stderr[-3000:])
        self.assertEqual(json.loads(out.stdout[out.stdout.index("{"):])["problems"], [])

    def test_page_script_parses(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "page.js")
            with open(path, "w", encoding="utf-8") as f:
                f.write(LOGIC + "\n" + PAGE)
            out = subprocess.run(["node", "--check", path], capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr[-3000:])

    def test_page_selftest(self):
        r = run_page("#selftest")
        self.assertFalse(r["hidden"])
        self.assertIn("No problems found.", r["box"], r["box"])
        self.assertIn("(v0.1.0)", r["box"])

    def test_page_play(self):
        r = run_page("")
        for key in ("lands", "muted", "unmuted", "won1", "house2", "bump", "unplace", "keySel", "keyEsc", "hint",
                    "restart", "won2", "keyNext", "daily", "dailyWon", "back", "tenant", "tenantClosed", "phone",
                    "phoneTap"):
            self.assertTrue(r.get(key), "%s failed: %r" % (key, r))
        self.assertEqual(r["savedLevel"], 2, r)

    def test_page_on_run_with_the_sdk(self):
        r = run_page("", prelude=RUN_STUB, after=RUN_AFTER)
        self.assertNotIn("error", r)
        for key in ("waits", "blocked", "ready", "loaded", "friend", "adOffered", "adPaid", "friendWon", "savedRun",
                    "shared", "backHome", "daily", "dailyWon", "scored", "rank", "reminder", "runSaved"):
            self.assertTrue(r.get(key), "%s failed: %r" % (key, r))

    def test_page_demo_plays_itself_and_never_saves(self):
        r = run_page("#demo")
        self.assertTrue(r["demo"])
        self.assertGreaterEqual(r["level"], 12, r)
        self.assertFalse(r["saved"], r)

    def test_page_covers(self):
        r = run_page("#cover")
        self.assertFalse(r["hidden"])
        self.assertEqual(r["children"], 6, r)
        self.assertEqual(r["srcs"], ["data:image/png;base64,"] * 3, r)


if __name__ == "__main__":
    unittest.main()
