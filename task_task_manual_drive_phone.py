# task_task_manual_drive_phone.py
# Phone-based dual-joystick control for QCar (Virtual Lab or hardware).
# Left pad = steering (X). Right pad = throttle (Y, up = forward).
# Run:
#   pip install aiohttp
#   python task_task_manual_drive_phone.py --host 0.0.0.0 --port 8000 --rate 50

import argparse, asyncio, json, os, time, csv
from datetime import datetime
from typing import Dict, Any
import numpy as np
from aiohttp import web, WSMsgType

from pal.products.qcar import QCar
from pal.utilities.math import Calculus

HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<title>QCar Controller — Chieh · ACL Lab</title>
<style>
  :root{
    --bg:#0b0f14; --fg:#e8eef6; --mut:#9fb3c8; --accent:#4da3ff; --panel:#111927; --border:#1f2a37;
    --ok:#1e8c47; --ok-br:#2fb564; --warn:#be2f2f; --warn-br:#e04b4b; --idle:#0e1726; --idle-br:#243244;
    --radius:14px;
  }

  html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font-family:system-ui,Segoe UI,Roboto,Arial}
  .wrap{display:flex;flex-direction:column;height:100dvh;gap:10px;padding:10px;box-sizing:border-box}

  /* ===== Header ===== */
  .hdr{display:flex;align-items:center;justify-content:space-between;
       background:linear-gradient(180deg, #0f1520, #0a1017);
       border:1px solid #1b2735;border-radius:var(--radius);padding:10px 14px;gap:12px;flex-wrap:wrap}
  .brand{display:flex;align-items:center;gap:10px;min-width:220px}
  .logo{width:28px;height:28px;border-radius:7px;background:#0d1726;border:1px solid #243244;
        display:grid;place-items:center;font-weight:800}
  .logo span{font-size:14px;letter-spacing:0.5px;color:var(--accent)}
  .title{font-weight:800}
  .subtitle{font-size:12px;color:var(--mut)}
  .hdr-rights{display:flex;gap:12px;align-items:center;margin-left:auto}
  .hdr-chip{font-size:12px;color:var(--mut);padding:4px 8px;border:1px solid var(--border);border-radius:10px;background:rgba(0,0,0,.15)}

  /* ===== Pads row (landscape-first) ===== */
  .row{display:flex;gap:12px;flex:1;min-height:52vh}
  .pad{position:relative;flex:1;background:var(--panel);border:1px solid var(--border);border-radius:16px;touch-action:none;overflow:hidden}
  .pad:before,.pad:after{content:""; position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); background:#223043; opacity:0.22}
  .pad:before{width:2px;height:80%;}
  .pad:after{height:2px;width:80%;}

  /* pad title & instruction */
  .pad-title{
    position:absolute; top:10px; left:10px;
    background:rgba(0,0,0,.25); border:1px solid var(--border); color:var(--fg);
    font-weight:800; font-size:13px; padding:6px 10px; border-radius:10px; letter-spacing:.3px;
    backdrop-filter: blur(2px);
  }
  .pad-instr{
    position:absolute; left:50%; bottom:10px; transform:translateX(-50%);
    color:var(--mut); font-size:12px; text-align:center; width:90%;
    background:rgba(0,0,0,.15); padding:6px 10px; border:1px dashed var(--border); border-radius:10px;
  }

  .stick{
    position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    width:38%;aspect-ratio:1;border-radius:50%;background:#18202b;border:2px solid var(--accent);
    box-shadow:0 0 0 2px rgba(77,163,255,0.15), inset 0 0 12px rgba(0,0,0,0.35);
    display:block; overflow:hidden;
    font-size:clamp(28px, 7.5vmin, 64px); /* hint arrow size */
  }
  .stick-hint{position:absolute;inset:0;pointer-events:none;color:#d9ecff;opacity:0.95;
              text-shadow:0 2px 2px rgba(0,0,0,.35); font-weight:900; line-height:1}
  .stick-hint .u{position:absolute; top:6%;  left:50%; transform:translateX(-50%);}
  .stick-hint .d{position:absolute; bottom:6%;left:50%; transform:translateX(-50%);}
  .stick-hint .l{position:absolute; left:6%; top:50%;  transform:translateY(-50%);}
  .stick-hint .r{position:absolute; right:6%;top:50%;  transform:translateY(-50%);}

  /* HUD below pads in landscape */
  .hud{display:grid;grid-template-columns:1fr 1fr; gap:12px}
  .card{background:var(--panel);border:1px solid var(--border);border-radius:var(--radius);padding:12px}
  .kvs{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;font-family:ui-monospace,Consolas}
  .btnrow{display:flex;gap:10px;flex-wrap:wrap}

  button{
    background:var(--idle); color:var(--fg); border:1px solid var(--idle-br);
    border-radius:10px; padding:10px 14px; font-weight:700; display:inline-flex; align-items:center; gap:8px;
    transition:transform .04s ease, box-shadow .1s ease, background .15s ease, border-color .15s ease, color .15s ease, opacity .15s ease;
  }
  button .ico{font-weight:900;line-height:1}
  button.arm{background:#123e1f;border-color:#1e6b37}
  button.disarm{background:#2a2020;border-color:#5a2f2f}
  button.estop{background:#5b1414;border-color:#b72d2d}
  button.arm.active{background:var(--ok); border-color:var(--ok-br); box-shadow:0 0 0 2px rgba(47,181,100,0.25) inset}
  button.disarm.active{background:#3c3c46; border-color:#68688a; box-shadow:0 0 0 2px rgba(150,150,200,0.2) inset}
  button.estop.active{background:var(--warn); border-color:var(--warn-br); box-shadow:0 0 0 2px rgba(224,75,75,0.25) inset}
  button:disabled{opacity:.6}

  input[type=range]{width:100%}
  label{font-size:12px;color:var(--mut)}
  .meter{height:8px;background:#17212c;border-radius:6px;overflow:hidden}
  .meter>div{height:100%;background:linear-gradient(90deg,#47d163,#e6d44c,#d14c4c)}
  .mut{color:var(--mut)}
  .footer{margin-top:8px;font-size:11px;color:var(--mut);text-align:center;opacity:0.75}

  /* ===== Rotate overlay (phones) ===== */
  .rotate{
    position:fixed; inset:0; display:none; align-items:center; justify-content:center;
    background:linear-gradient(180deg, rgba(10,13,18,.95), rgba(10,13,18,.95));
    color:#e8eef6; text-align:center; z-index:9999; padding:24px;
  }
  .rotate .box{
    border:1px solid var(--border); border-radius:14px; padding:16px 18px; background:#0e1726;
    max-width:520px;
  }
  .rotate h2{margin:0 0 8px 0; font-size:18px}
  .rotate p{margin:0; color:var(--mut); font-size:14px}

  /* ===== Responsive: Portrait vs Landscape ===== */
  @media (orientation: portrait) {
    .hdr{display:none;}              /* hide header in portrait */
    .row, .hud, .footer{display:none;}
    .rotate{display:flex;}           /* show "rotate device" overlay */
  }
  @media (orientation: landscape) {
    .hdr{display:flex;}
    .row{display:flex;}
    .hud{display:grid;}
    .rotate{display:none;}
  }
</style>
</head>
<body>
<div class="wrap">
  <!-- ===== Header with branding ===== -->
  <div class="hdr">
    <div class="brand">
      <div class="logo" aria-hidden="true"><span>ACL</span></div>
      <div>
        <div class="title">QCar Controller</div>
        <div class="subtitle">Chieh · ACL Lab</div>
      </div>
    </div>
    <div class="hdr-rights">
      <div class="hdr-chip" id="hdrInfo">Connecting…</div>
      <div class="hdr-chip">
        <label for="theme" style="margin-right:6px;">Theme</label>
        <select id="theme">
          <option value="qcar">QCar</option>
          <option value="amazon">Amazon</option>
          <option value="pubg">PUBG</option>
        </select>
      </div>
    </div>
  </div>

  <!-- Rotate overlay for portrait -->
  <div class="rotate" id="rotateHint">
    <div class="box">
      <h2>Please rotate your phone</h2>
      <p>This controller is optimized for <b>landscape</b>. Turn your device sideways.</p>
    </div>
  </div>

  <div class="row">
    <!-- LEFT: STEERING -->
    <div class="pad" id="padLeft" aria-label="Steering">
      <div class="pad-title">Steering (X-axis)</div>
      <div class="stick" id="stickLeft" title="Steer (X)">
        <div class="stick-hint" aria-hidden="true">
          <span class="u">↑</span><span class="d">↓</span><span class="l">←</span><span class="r">→</span>
        </div>
      </div>
      <div class="pad-instr">Slide <b>left/right</b> to steer the wheels.</div>
    </div>

    <!-- RIGHT: SPEED / THROTTLE -->
    <div class="pad" id="padRight" aria-label="Throttle">
      <div class="pad-title">Speed / Throttle (Y-axis)</div>
      <div class="stick" id="stickRight" title="Throttle (Y)">
        <div class="stick-hint" aria-hidden="true">
          <span class="u">↑</span><span class="d">↓</span><span class="l">←</span><span class="r">→</span>
        </div>
      </div>
      <div class="pad-instr"><b>Up</b> = forward, <b>Down</b> = reverse.</div>
    </div>
  </div>

  <div class="hud">
    <div class="card">
      <div class="title">Controls</div>
      <div class="btnrow">
        <button id="armBtn" class="arm"><span class="ico">▶</span><span>ARM</span></button>
        <button id="disarmBtn" class="disarm"><span class="ico">■</span><span>DISARM</span></button>
        <button id="estopBtn" class="estop"><span class="ico">⛔</span><span>E-STOP</span></button>
      </div>
      <div style="margin-top:10px">
        <label>Max Speed (m/s): <span id="maxSpeedVal">0.20</span></label>
        <input id="maxSpeed" type="range" min="0" max="0.6" step="0.01" value="0.20">
      </div>
      <div>
        <label>Steering Gain: <span id="steerGainVal">0.50</span></label>
        <input id="steerGain" type="range" min="0" max="1.0" step="0.01" value="0.50">
      </div>
      <div>
        <label>Deadzone: <span id="deadVal">0.06</span></label>
        <input id="dead" type="range" min="0" max="0.25" step="0.01" value="0.06">
      </div>
      <div>
        <label>Smoothing (0-1): <span id="smVal">0.35</span></label>
        <input id="smooth" type="range" min="0" max="1" step="0.01" value="0.35">
      </div>
      <div class="mut" style="margin-top:6px">Left pad = steer (X). Right pad = throttle (Y).</div>
    </div>
    <div class="card">
      <div class="title">Telemetry</div>
      <div class="kvs">
        <div>Battery</div><div><span id="batPct">--</span>%</div>
        <div>Speed</div><div><span id="spd">--</span> m/s</div>
        <div>Throttle</div><div><span id="thr">--</span></div>
        <div>Steering</div><div><span id="ste">--</span> rad</div>
      </div>
      <div style="margin-top:10px"><div class="meter"><div id="batBar" style="width:0%"></div></div></div>
      <div class="mut" style="margin-top:8px">Logging on robot.</div>
    </div>
  </div>

  <div class="footer">© Chieh · ACL Lab</div>
</div>

<script>
(function(){
  const ws = new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws');

  const hdrInfo = document.getElementById('hdrInfo');
  hdrInfo.textContent = location.host;

  const leftPad = document.getElementById('padLeft');
  const rightPad = document.getElementById('padRight');
  const leftStick = document.getElementById('stickLeft');
  const rightStick = document.getElementById('stickRight');

  const armBtn = document.getElementById('armBtn');
  const disarmBtn = document.getElementById('disarmBtn');
  const estopBtn = document.getElementById('estopBtn');

  const maxSpeed = document.getElementById('maxSpeed');
  const steerGain = document.getElementById('steerGain');
  const dead = document.getElementById('dead');
  const smooth = document.getElementById('smooth');
  const maxSpeedVal = document.getElementById('maxSpeedVal');
  const steerGainVal = document.getElementById('steerGainVal');
  const deadVal = document.getElementById('deadVal');
  const smVal = document.getElementById('smVal');

  const batPct = document.getElementById('batPct');
  const spd = document.getElementById('spd');
  const thr = document.getElementById('thr');
  const ste = document.getElementById('ste');
  const batBar = document.getElementById('batBar');

  const themeSel = document.getElementById('theme');

  /* ===== Theme switcher with persistence ===== */
  const root = document.documentElement;
  const savedTheme = localStorage.getItem('qcar_theme') || 'qcar';
  applyTheme(savedTheme);
  themeSel.value = savedTheme;
  themeSel.addEventListener('change', () => {
    applyTheme(themeSel.value);
    localStorage.setItem('qcar_theme', themeSel.value);
  });
  function applyTheme(name){
    root.classList.remove('theme-qcar','theme-amazon','theme-pubg');
    root.classList.add('theme-'+name);
  }

  // UI state helpers
  let uiState = { armed:false, estop:false };
  function setActive(btn, active){ btn.classList.toggle('active', !!active); }
  function renderArmState(armed, estop){
    uiState.armed = !!armed;
    uiState.estop = !!estop;
    setActive(armBtn,  armed && !estop);
    setActive(disarmBtn, !armed && !estop);
    setActive(estopBtn, estop);
    armBtn.disabled   = estop || armed;
    disarmBtn.disabled= estop || !armed;
  }

  // label sync
  function labelSync(){
    maxSpeedVal.textContent = (+maxSpeed.value).toFixed(2);
    steerGainVal.textContent = (+steerGain.value).toFixed(2);
    deadVal.textContent = (+dead.value).toFixed(2);
    smVal.textContent = (+smooth.value).toFixed(2);
  }
  [maxSpeed,steerGain,dead,smooth].forEach(x=>x.addEventListener('input',labelSync)); labelSync();

  let leftId=null,rightId=null;
  let leftAxes={x:0,y:0}, rightAxes={x:0,y:0};

  function handlePad(pad, stick, isLeft, ev){
    const rect = pad.getBoundingClientRect();
    const cx = rect.left + rect.width/2;
    const cy = rect.top  + rect.height/2;
    const maxR = Math.min(rect.width, rect.height) * 0.5 * 0.85;

    const touches = ev.changedTouches ? Array.from(ev.changedTouches) : [ev];
    touches.forEach(t=>{
      if (ev.type==='touchstart' || ev.type==='pointerdown'){
        if (isLeft && leftId===null) leftId = t.identifier ?? 'mouse';
        if (!isLeft && rightId===null) rightId = t.identifier ?? 'mouse';
      }
      const myId = isLeft ? leftId : rightId;
      if (myId !== (t.identifier ?? 'mouse')) return;

      if (['touchend','pointerup','pointercancel'].includes(ev.type)){
        if (isLeft){ leftId=null; leftAxes={x:0,y:0}; } else { rightId=null; rightAxes={x:0,y:0}; }
        stick.style.left='50%'; stick.style.top='50%'; send(); return;
      }

      const x = (t.clientX - cx), y = (t.clientY - cy);
      const r = Math.hypot(x,y); const k = r>maxR ? maxR/r : 1;
      const sx = x*k, sy = y*k;
      stick.style.left = (50 + 50*sx/maxR) + '%';
      stick.style.top  = (50 + 50*sy/maxR) + '%';

      const nx =  sx/maxR;     // [-1,1], right +
      const ny = -sy/maxR;     // [-1,1], up +
      if (isLeft) leftAxes={x:nx,y:ny}; else rightAxes={x:nx,y:ny};
      send();
    });
    ev.preventDefault();
  }

  function bind(pad, stick, isLeft){
    pad.addEventListener('touchstart', e=>handlePad(pad,stick,isLeft,e), {passive:false});
    pad.addEventListener('touchmove',  e=>handlePad(pad,stick,isLeft,e), {passive:false});
    pad.addEventListener('touchend',   e=>handlePad(pad,stick,isLeft,e), {passive:false});
    pad.addEventListener('pointerdown',e=>handlePad(pad,stick,isLeft,e));
    pad.addEventListener('pointermove',e=>handlePad(pad,stick,isLeft,e));
    pad.addEventListener('pointerup',  e=>handlePad(pad,stick,isLeft,e));
    pad.addEventListener('pointercancel',e=>handlePad(pad,stick,isLeft,e));
  }
  bind(leftPad,leftStick,true);
  bind(rightPad,rightStick,false);

  // Buttons
  armBtn.onclick   = ()=>{ renderArmState(true,  false); ws.send(JSON.stringify({type:'arm'}));   };
  disarmBtn.onclick= ()=>{ renderArmState(false, false); ws.send(JSON.stringify({type:'disarm'}));};
  estopBtn.onclick = ()=>{ renderArmState(false, true ); ws.send(JSON.stringify({type:'estop'})); };

  ;[maxSpeed,steerGain,dead,smooth].forEach(el=>el.addEventListener('change',()=>send(true)));

  function send(){
    if (ws.readyState!==1) return;
    ws.send(JSON.stringify({
      type:'control',
      left:leftAxes, right:rightAxes,
      params:{
        maxSpeed:+maxSpeed.value, steerGain:+steerGain.value,
        dead:+dead.value, smooth:+smooth.value
      },
      ts: Date.now()
    }));
  }

  ws.onopen = ()=>{ hdrInfo.textContent = location.host + " · Connected"; };
  ws.onclose = ()=>{ hdrInfo.textContent = location.host + " · Disconnected"; };

  ws.onmessage = (ev)=>{
    try{
      const msg = JSON.parse(ev.data);
      if (msg.type==='telemetry'){
        batPct.textContent = (msg.battery_pct ?? 0).toFixed(1);
        spd.textContent    = (msg.speed_mps ?? 0).toFixed(3);
        thr.textContent    = (msg.throttle ?? 0).toFixed(3);
        ste.textContent    = (msg.steering ?? 0).toFixed(3);
        batBar.style.width = Math.max(0, Math.min(100, msg.battery_pct ?? 0)) + '%';
        if ('armed' in msg || 'estop' in msg){
          renderArmState(!!msg.armed, !!msg.estop);
        }
      }
    }catch(_){}
  }

  // (Optional) Try to lock landscape in supported contexts (e.g., installed PWA)
  document.addEventListener('click', ()=> {
    if (screen.orientation && screen.orientation.lock) {
      screen.orientation.lock('landscape').catch(()=>{});
    }
  }, {once:true});

})();
</script>
</body></html>
"""

# ---------------- Python server + controller ----------------

class ControllerState:
    def __init__(self):
        self.armed = False
        self.estop = False
        self.left  = {'x':0.0,'y':0.0}   # steering on X
        self.right = {'x':0.0,'y':0.0}   # throttle on Y
        self.params = {'maxSpeed':0.20,'steerGain':0.50,'dead':0.06,'smooth':0.35}
        self.throttle = 0.0
        self.steering = 0.0

    @staticmethod
    def _deadzone(v, dz): return 0.0 if abs(v) < dz else float(np.clip(v, -1.0, 1.0))

    def update_from_msg(self, msg: Dict[str, Any]):
        t = msg.get('type')
        if t == 'arm':
            self.armed = True; self.estop = False
        elif t == 'disarm':
            self.armed = False; self.throttle = 0.0; self.steering = 0.0
        elif t == 'estop':
            self.estop = True; self.armed = False; self.throttle = 0.0; self.steering = 0.0
        elif t == 'control':
            self.left = msg.get('left', self.left)
            self.right = msg.get('right', self.right)
            self.params.update(msg.get('params', {}))

    def compute(self, prev_throttle, prev_steering):
        dz      = float(self.params['dead'])
        smooth  = float(self.params['smooth'])
        vmax    = float(self.params['maxSpeed'])   # m/s cap
        steer_k = float(self.params['steerGain'])  # rad scaling

        lx = self._deadzone(float(self.left.get('x',0.0)), dz)
        ry = self._deadzone(float(self.right.get('y',0.0)), dz)

        # ===== Steering mapping (FIXED DIRECTION) =====
        # Invert sign so moving stick RIGHT turns RIGHT on the car
        steering_cmd = -steer_k * lx           # rad (inverted)
        throttle_cmd =  vmax   * ry            # m/s

        # simple EMA smoothing
        alpha = np.clip(1.0 - smooth, 0.0, 1.0)
        throttle = (1-alpha)*prev_throttle + alpha*throttle_cmd
        steering = (1-alpha)*prev_steering + alpha*steering_cmd

        if not self.armed or self.estop:
            throttle = 0.0; steering = 0.0

        # Clamp to sane bounds
        throttle = float(np.clip(throttle, -vmax, vmax))
        steering = float(np.clip(steering, -1.2, 1.2))
        self.throttle, self.steering = throttle, steering
        return throttle, steering

state = ControllerState()
ws_clients = set()

async def handle_index(_):
    return web.Response(text=HTML, content_type='text/html')

async def handle_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    ws_clients.add(ws)
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try: state.update_from_msg(json.loads(msg.data))
                except Exception: pass
    finally:
        ws_clients.discard(ws)
    return ws

async def push_telemetry(batt_pct, speed_mps, throttle, steering):
    if not ws_clients: return
    payload = json.dumps({
        'type':'telemetry',
        'battery_pct': batt_pct,
        'speed_mps': speed_mps,
        'throttle': throttle,
        'steering': steering,
        'armed': state.armed,
        'estop': state.estop,
        'ts': time.time()
    })
    await asyncio.gather(*[c.send_str(payload) for c in list(ws_clients) if not c.closed], return_exceptions=True)

async def controller_task(sample_rate: float, log_path: str, read_mode: int):
    sample_time = 1.0 / sample_rate
    myCar = QCar(readMode=read_mode)   # 0 = immediate I/O (Virtual Lab OK)
    _ = Calculus().differentiator_variable(sample_time)  # kept for parity

    # CSV header
    with open(log_path, 'w', newline='') as f:
        csv.writer(f).writerow(['Timestamp','LinearSpeed_mps','Battery_pct','Throttle_cmd','Steering_cmd','Armed','EStop'])

    print(f"[QCar] {sample_rate} Hz loop started. Open the page from your phone to drive.")
    try:
        while True:
            t0 = time.time()
            throttle, steering = state.compute(state.throttle, state.steering)

            # LED indicators
            LEDs = np.array([0,0,0,0,0,0,1,1])
            if steering > 0.3: LEDs[0]=LEDs[2]=1
            elif steering < -0.3: LEDs[1]=LEDs[3]=1
            if throttle < 0: LEDs[5]=1

            # Perform I/O
            myCar.read_write_std(throttle=throttle, steering=steering, LEDs=LEDs)

            # Telemetry
            batteryVoltage = myCar.batteryVoltage
            bat_pct = float(np.clip(100 - (batteryVoltage - 10.5)*100/(12.6-10.5), 0, 100))
            linearSpeed = float(myCar.motorTach)

            # Log
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open(log_path, 'a', newline='') as f:
                csv.writer(f).writerow([ts, linearSpeed, bat_pct, throttle, steering, int(state.armed), int(state.estop)])

            # Stream to clients
            await push_telemetry(bat_pct, linearSpeed, throttle, steering)

            # Maintain loop rate
            elapsed = time.time() - t0
            sleep = sample_time - (elapsed % sample_time)
            if sleep > 0: await asyncio.sleep(sleep)
    except asyncio.CancelledError:
        pass
    finally:
        myCar.terminate()
        print("[QCar] Stopped.")

def make_app():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/ws', handle_ws)
    return app

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='0.0.0.0')
    ap.add_argument('--port', type=int, default=8000)
    ap.add_argument('--rate', type=float, default=50.0)
    ap.add_argument('--log', default='manual_drive_log.csv')
    ap.add_argument('--readmode', type=int, default=0)  # 0 immediate I/O
    args = ap.parse_args()

    app = make_app()
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, host=args.host, port=args.port); await site.start()
    print(f"[Server] http://{args.host}:{args.port}")

    ctrl = asyncio.create_task(controller_task(args.rate, args.log, args.readmode))

    try:
        if os.name != 'nt':
            import signal
            loop = asyncio.get_running_loop()
            stop = asyncio.Future()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda: (not stop.done()) and stop.set_result(True))
            await stop
        else:
            print("[Server] Press Ctrl+C in this window to stop.")
            while True:
                await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        ctrl.cancel()
        try:
            await ctrl
        except asyncio.CancelledError:
            pass
        await runner.cleanup()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
