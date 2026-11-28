import asyncio, threading, functools, http.server, socketserver, json
from playwright.async_api import async_playwright
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.TCPServer(('127.0.0.1',0),functools.partial(Q,directory=str(__import__('pathlib').Path(__file__).resolve().parents[1])));P=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
RES=[]
def check(n,name,ok,detail):RES.append((n,name,ok,detail));print(('PASS' if ok else 'FAIL'),n,name,'|',detail)
SETUP="""(kind)=>{const A=window.__A8,R=A.R;R.radio=null;R.roo=null;R.rooT=1e9;R.booms=[];R.parts.length=0;R.fx.length=0;
  for(const c of R.cars){c.auto=false;c.vx=0;c.vy=0}
  const pl=R.pl,ox=pl.x+60,oy=pl.y;R.roo={x:ox,y:oy,vx:0,vy:0,t:0,trav:0,hit:{},big:0,h:0,kind};
  pl.x=ox-10;pl.y=oy;pl.vx=300;pl.vy=0;return {ox,oy}}"""
async def race(pg):
    await pg.goto(f'http://127.0.0.1:{P}/play/');await pg.wait_for_timeout(1500);await pg.keyboard.press('Enter');await pg.wait_for_timeout(200)
    await pg.click('[data-act=new]');await pg.click('[data-act="ch:0"]')
    if await pg.query_selector('[data-act=paddock]'): await pg.click('[data-act=paddock]')
    await pg.click('[data-act=garage]');await pg.click('[data-act=race]');await pg.wait_for_timeout(400)
    await pg.evaluate("window.__A8.gridChoice('ignore')");await pg.wait_for_timeout(3800)
    await pg.keyboard.press('Escape');await pg.wait_for_timeout(200)   # pause the live loop; we step frames by hand
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    pg=await b.new_page(viewport={'width':1400,'height':900});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await race(pg)
    paused=await pg.evaluate("!!window.__A8.R.paused");print('paused for manual stepping:',paused)
    cv=await pg.query_selector('#cv');bb=await cv.bounding_box();sc=bb['width']/960
    out={}
    for kind in ['emu','roo']:
      # step one frame at a time through update + a forced render, logging every FX frame drawn
      r=await pg.evaluate("""(kind)=>{const A=window.__A8,R=A.R;const s=("""+SETUP+""")(kind);const pl=R.pl;
        window.__fxLog=[];
        // the hit: player truck and an AI truck both overlap the animal on the same frame
        const ai=R.cars.find(c=>!c.isP);ai.x=s.ox+8;ai.y=s.oy+4;ai.vx=120;ai.vy=-40;const snap=c=>({vx:c.vx,vy:c.vy,a:c.a,dmg:c.dmg});const v0={p:snap(pl),ai:snap(ai),pen:R.pen};
        const roo=R.roo;R.radioG=9;A.updRoo(1/60);
        const hit={booms:R.booms.length,bx:R.booms[0]&&R.booms[0].x,by:R.booms[0]&&R.booms[0].y,rx:roo.x,ry:roo.y,poof:!!roo.poof,
          v1:{p:snap(pl),ai:snap(ai),pen:R.pen},hits:Object.keys(roo.hit),parts:R.parts.length,fx:R.fx.length,v0};
        // keep calling updRoo (as the race would): still one boom, animal gone
        for(let i=0;i<120;i++)A.updRoo(1/60);hit.boomsAfter=R.booms.length;hit.rooGone=R.roo===null;
        return hit}""",kind)
      out[kind]=r
      # play the animation in real time while unpaused, capturing frames
      await pg.evaluate("window.__fxLog=[]")
      shots=[]
      await pg.keyboard.press('Escape')
      for k in range(4):
        await pg.wait_for_timeout(110 if k else 30)
        if k in (0,1): 
          await pg.screenshot(path=f'/tmp/b20_{kind}_{k}.png',clip={'x':bb['x'],'y':bb['y'],'width':960*sc,'height':640*sc})
      await pg.wait_for_timeout(1400)
      await pg.keyboard.press('Escape')
      r['log']=await pg.evaluate("window.__fxLog")
      r['boomsEnd']=await pg.evaluate("window.__A8.R.booms.length")
      r['A']=await pg.evaluate("((x,y)=>{const o=window.__A8;return null})()")
    # world -> art buffer mapping used by the game: A(x,y) = {x/2,(y+40)/2}
    for kind,r in out.items():
      log=r['log'];ax,ay=r['bx']/2,(r['by']+40)/2
      imp=[l for l in log if l[1]=='impact'];bur=[l for l in log if l[1].endswith('_burst')];fea=[l for l in log if l[1]=='emu_feathers']
      # 1. timing: every logged frame index equals floor(t/85ms); all frames seen
      bad=[l for l in imp+bur if l[2]!=int(l[0]*1000//85)]
      check(1,f'{kind}: 85 ms per frame',not bad and sorted({l[2] for l in imp})==[0,1,2,3] and sorted({l[2] for l in bur})==[0,1,2,3,4,5],
            f'impact frames {sorted({l[2] for l in imp})}, burst frames {sorted({l[2] for l in bur})}, mistimed {len(bad)}')
      # 2. species-specific
      want='emu_burst' if kind=='emu' else 'wallaby_burst';other='wallaby_burst' if kind=='emu' else 'emu_burst'
      sp_ok=all(l[1]!=other for l in log) and any(l[1]==want for l in log) and ((len(fea)>0) if kind=='emu' else len(fea)==0)
      check(2,f'{kind}: species burst ({want}{", feathers" if kind=="emu" else ", no feathers"})',sp_ok,f'feather draws {len(fea)}')
      # 3. location: impact + burst centred on the collision point
      off=max([abs(l[3]-ax)+abs(l[4]-ay) for l in imp+bur] or [99])
      check(3,f'{kind}: centred on collision point',r['bx']==r['rx'] and r['by']==r['ry'] and off==0,f'boom at world ({r["bx"]:.1f},{r["by"]:.1f}) = animal at hit; max draw offset {off} px')
      # 4. no duplicates
      check(4,f'{kind}: one explosion only',r['booms']==1 and r['boomsAfter']==1,f'two trucks overlapped the animal on the same frame -> {r["booms"]} boom; after 120 more updates -> {r["boomsAfter"]}')
      # 5. animal removed once, no remains, old effects gone
      check(5,f'{kind}: animal removed, no remains, sprite FX only',r['poof'] and r['rooGone'] and r['parts']==0 and r['fx']==0 and r['boomsEnd']==0,
            f'removed {r["rooGone"]}, leftover particles {r["parts"]}, generic crash fx {r["fx"]}, booms after 1.5 s {r["boomsEnd"]}')
      # 6. vehicle physics, damage, penalties unchanged
      v0,v1=r['v0'],r['v1'];ok6=v1['pen']==v0['pen'];det=[]
      for k in ('p','ai'):
        a,b2=v0[k],v1[k];ok6=ok6 and abs(b2['vx']-a['vx']*.5)<1e-6 and abs(b2['vy']-a['vy']*.5)<1e-6 and abs(b2['a']-a['a'])<=.5 and b2['dmg']==a['dmg']
        det.append(f"{'player' if k=='p' else 'AI'} speed {a['vx']:.0f}->{b2['vx']:.0f} (x0.5), heading {abs(b2['a']-a['a']):.2f} rad, dmg {a['dmg']:.1f}->{b2['dmg']:.1f}")
      check(6,f'{kind}: each truck gets the original hit response; damage and penalties unchanged',ok6,'; '.join(det)+f"; penalty {v0['pen']}->{v1['pen']}; trucks hit {r['hits']}")
    print('errors',errs)
    await b.close()
  print('\nSUMMARY',sum(1 for x in RES if x[2]),'/',len(RES),'passed')
asyncio.run(main())
