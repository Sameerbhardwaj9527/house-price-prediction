"""Animated, clickable house scene (pure HTML/SVG/JS) rendered inside Streamlit via components.html."""
import json

TEMPLATE = r"""
<style>
  *{box-sizing:border-box} body{margin:0;font-family:Inter,system-ui,sans-serif;background:transparent}
  #root{position:relative;border-radius:18px;overflow:hidden;--sky1:#8fd3ff;--sky2:#e6f6ff;--ground:#6fbf5a;--ground2:#5aa84a;--road:#4a4f57;--ink:#1d2433;--win:#cfeaff;--card:rgba(255,255,255,.88);--cardink:#1d2433}
  #root.night{--sky1:#0b1030;--sky2:#2a2f63;--ground:#2c5a3a;--ground2:#234b30;--road:#23262c;--win:#ffd36b;--card:rgba(20,24,48,.82);--cardink:#f2f4ff}
  svg{display:block;width:100%;height:auto}
  .card{position:absolute;left:16px;top:14px;background:var(--card);color:var(--cardink);padding:10px 16px;border-radius:14px;backdrop-filter:blur(6px);box-shadow:0 6px 20px rgba(0,0,0,.18);transform-origin:top left;animation:pop .7s cubic-bezier(.2,1.4,.4,1) both}
  .card small{display:block;font-size:11px;letter-spacing:.12em;opacity:.7;font-weight:600}
  .card b{font-size:34px;line-height:1.1;font-variant-numeric:tabular-nums}
  .card span{font-size:12px;opacity:.75}
  .tog{position:absolute;right:14px;bottom:12px;border:0;border-radius:999px;padding:8px 14px;font-weight:600;cursor:pointer;background:var(--card);color:var(--cardink);box-shadow:0 4px 12px rgba(0,0,0,.2)}
  .hint{position:absolute;left:16px;bottom:12px;font-size:12px;color:#fff;text-shadow:0 1px 3px rgba(0,0,0,.6)}
  @keyframes pop{from{transform:scale(.6) translateY(-10px);opacity:0}to{transform:none;opacity:1}}
  @keyframes cloud{from{transform:translateX(-200px)}to{transform:translateX(1100px)}}
  @keyframes spin{to{transform:rotate(360deg)}}
  @keyframes road{to{transform:translateX(-60px)}}
  @keyframes sway{0%,100%{transform:rotate(-2.5deg)}50%{transform:rotate(2.5deg)}}
  @keyframes smoke{0%{transform:translate(0,0) scale(.4);opacity:.0}15%{opacity:.7}100%{transform:translate(14px,-70px) scale(1.7);opacity:0}}
  @keyframes drive{0%{transform:translateX(var(--from))}70%{transform:translateX(calc(var(--to) + 6px))}100%{transform:translateX(var(--to))}}
  @keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-1.5px)}}
  @keyframes twinkle{0%,100%{opacity:.2}50%{opacity:1}}
  @keyframes swing{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(6deg)}}
  @keyframes rays{to{transform:rotate(360deg)}}
  @keyframes beep{0%{opacity:0;transform:translateY(6px) scale(.6)}20%{opacity:1;transform:none}80%{opacity:1}100%{opacity:0;transform:translateY(-10px)}}
  .cloud{animation:cloud linear infinite}
  .wheel{transform-box:fill-box;transform-origin:center;animation:spin .6s linear infinite}
  .car{cursor:pointer}
  .car .body{animation:bounce .35s ease-in-out infinite}
  .car.parked .wheel,.car.parked .body{animation-play-state:paused}
  .tree{transform-box:fill-box;transform-origin:50% 100%;animation:sway 4s ease-in-out infinite}
  .puff{transform-box:fill-box;transform-origin:center;animation:smoke 3.2s ease-out infinite}
  .fan{transform-box:fill-box;transform-origin:center;animation:spin 1.2s linear infinite}
  .sign{transform-box:fill-box;transform-origin:50% 0;animation:swing 3s ease-in-out infinite}
  .rays{transform-box:fill-box;transform-origin:center;animation:rays 40s linear infinite}
  .stars{display:none} #root.night .stars{display:block} #root.night .sun{display:none}
  .moon{display:none} #root.night .moon{display:block}
  .star{animation:twinkle 2.5s ease-in-out infinite}
  .roadl{animation:road .5s linear infinite}
  .beep{opacity:0;font-weight:800;font-size:15px;fill:#fff}
  .beep.on{animation:beep 1.1s ease-out}
  .glow{display:none} #root.night .glow{display:block}
  @media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>
<div id="root">
  <div class="card"><small>ESTIMATED SALE PRICE</small><b id="price">$0</b><br><span id="range"></span></div>
  <svg id="svg" viewBox="0 0 900 420" xmlns="http://www.w3.org/2000/svg"></svg>
  <div class="hint">Click a car to honk · click the house or sun to switch day / night</div>
  <button class="tog" id="tog">🌙 Night</button>
</div>
<script>
const D = __DATA__;
const root = document.getElementById('root'), svg = document.getElementById('svg');
const GY = 330;                                   // ground line
const q = D.quality;
const palettes = [ ['#b9aa9b','#6b5b4f','#8c6b4a'], ['#dccaa6','#8a4b3c','#6e4a2e'], ['#e9e0d0','#35607f','#2f4d6b'], ['#f6f2ea','#1f2a44','#d4a73a'] ];
const pal = palettes[q<=3?0:q<=6?1:q<=8?2:3];
const stories = D.area > 1700 ? 2 : 1;
const W = Math.round(170 + (Math.min(Math.max(D.area,500),4000)-500)/3500*170);
const H = stories===2 ? 170 : 100;
const X0 = 345, cars = D.cars;
const bay = 64, GW = cars>0 ? cars*bay+18 : 0, GX = X0 - GW;
let s = '';
// --- sky
s += `<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--sky1)"/><stop offset="1" stop-color="var(--sky2)"/></linearGradient>
<radialGradient id="glow"><stop offset="0" stop-color="#ffe9a8" stop-opacity=".9"/><stop offset="1" stop-color="#ffe9a8" stop-opacity="0"/></radialGradient></defs>
<rect width="900" height="420" fill="url(#sky)"/>`;
let stars=''; for(let i=0;i<40;i++){stars+=`<circle class="star" cx="${(i*97)%900}" cy="${(i*53)%200+8}" r="${1+(i%3)*.6}" fill="#fff" style="animation-delay:${(i%7)*.4}s"/>`}
s += `<g class="stars">${stars}</g>`;
s += `<g class="sun" id="sun" style="cursor:pointer"><circle cx="800" cy="70" r="70" fill="url(#glow)"/><g class="rays"><g stroke="#ffd34d" stroke-width="4" stroke-linecap="round">${[...Array(12)].map((_,i)=>`<line x1="800" y1="26" x2="800" y2="14" transform="rotate(${i*30} 800 70)"/>`).join('')}</g></g><circle cx="800" cy="70" r="26" fill="#ffd34d"/></g>`;
s += `<g class="moon" id="moon" style="cursor:pointer"><circle cx="800" cy="70" r="26" fill="#f4f1de"/><circle cx="812" cy="62" r="24" fill="#0f1438"/></g>`;
[[40,22,0],[150,38,-18],[90,28,-9]].forEach(([y,d,delay],i)=>{ s += `<g class="cloud" style="animation-duration:${60+i*25}s;animation-delay:${delay-20}s"><g transform="translate(0 ${y+i*10})" fill="#fff" opacity=".85"><ellipse cx="0" cy="0" rx="44" ry="14"/><ellipse cx="-22" cy="-8" rx="22" ry="14"/><ellipse cx="14" cy="-12" rx="26" ry="16"/></g></g>` });
// --- ground & road
s += `<rect y="${GY}" width="900" height="90" fill="var(--ground)"/><rect y="${GY+34}" width="900" height="26" fill="var(--road)"/>`;
s += `<g class="roadl" stroke="#f3d34a" stroke-width="3" stroke-dasharray="30 30"><line x1="-60" y1="${GY+47}" x2="960" y2="${GY+47}"/></g>`;
s += `<rect y="${GY+60}" width="900" height="30" fill="var(--ground2)"/>`;
// --- trees (lot size)
const nT = Math.max(1,Math.min(5,Math.round(D.lot/3200)));
[[790,1],[858,.9],[735,.7],[828,.62],[884,.68]].slice(0,nT).forEach(([x,sc],i)=>{
  s += `<g class="tree" style="animation-delay:${i*.5}s" transform="translate(${x} ${GY}) scale(${sc})"><rect x="-6" y="-46" width="12" height="46" fill="#7a5230"/><circle cx="0" cy="-72" r="34" fill="#2f8f4e"/><circle cx="-20" cy="-52" r="22" fill="#3aa55c"/><circle cx="20" cy="-54" r="22" fill="#38a05a"/></g>`});
// --- garage (left)
if(cars>0){
  s += `<rect x="${GX}" y="${GY-84}" width="${GW}" height="84" fill="${pal[0]}" stroke="rgba(0,0,0,.25)"/>
  <rect x="${GX-6}" y="${GY-94}" width="${GW+6}" height="14" fill="${pal[1]}"/>
  <rect x="${GX+9}" y="${GY-70}" width="${cars*bay}" height="70" fill="#20232b"/>
  <g fill="#d9d9d9" stroke="#999">${[...Array(4)].map((_,i)=>`<rect x="${GX+9}" y="${GY-70+i*5}" width="${cars*bay}" height="4"/>`).join('')}</g>
  <g class="glow"><rect x="${GX+9}" y="${GY-70}" width="${cars*bay}" height="70" fill="#ffd36b" opacity=".18"/></g>`;
} else {
  s += `<g transform="translate(250 ${GY})"><rect x="-3" y="-44" width="6" height="44" fill="#6b4a2a"/><rect x="-16" y="-62" width="32" height="20" rx="4" fill="#c0392b"/><rect x="-10" y="-56" width="20" height="3" fill="#fff"/></g>`;
}
// --- house
const bx = X0, by = GY-H;
s += `<rect x="${bx}" y="${by}" width="${W}" height="${H}" fill="${pal[0]}" stroke="rgba(0,0,0,.25)"/>
<polygon points="${bx-16},${by+2} ${bx+W/2},${by-70} ${bx+W+16},${by+2}" fill="${pal[1]}" stroke="rgba(0,0,0,.3)"/>
<rect x="${bx+W/2-44}" y="${by-32}" width="88" height="3" fill="rgba(255,255,255,.25)"/>`;
// chimney + smoke
if(D.fire>0){
  const cx = bx+W*0.74; s += `<rect x="${cx}" y="${by-78}" width="22" height="50" fill="#8b4a3a"/><rect x="${cx-3}" y="${by-84}" width="28" height="8" fill="#6d3a2d"/>`;
  for(let i=0;i<2+D.fire;i++) s += `<circle class="puff" cx="${cx+11}" cy="${by-90}" r="9" fill="#cfd4da" style="animation-delay:${i*0.9}s"/>`;
}
// windows
function win(x,y,w=30,h=36){ return `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="var(--win)" stroke="#3d3d3d" stroke-width="2"/><line x1="${x+w/2}" y1="${y}" x2="${x+w/2}" y2="${y+h}" stroke="#3d3d3d"/><line x1="${x}" y1="${y+h/2}" x2="${x+w}" y2="${y+h/2}" stroke="#3d3d3d"/></g>`}
const lowY = GY-H+ (stories===2? H-78 : 24);
const doorX = bx+W/2-17;
s += `<rect x="${doorX}" y="${GY-64}" width="34" height="64" rx="3" fill="${pal[2]}" stroke="rgba(0,0,0,.35)"/><circle cx="${doorX+27}" cy="${GY-32}" r="3" fill="#ffd34d"/>`;
const lowCols = W>=250 ? 2 : 1;
for(let i=0;i<lowCols;i++){ s += win(bx+18+i*40, GY-62); s += win(bx+W-48-i*40, GY-62); }
if(stories===2){
  const n = Math.min(Math.max(D.beds,1),5); const gap = (W-40)/n;
  for(let i=0;i<n;i++) s += win(bx+20+i*gap+(gap-30)/2, by+22);
}
// AC unit
if(D.ac){ const ax = bx+W+8; s += `<g><rect x="${ax}" y="${GY-30}" width="34" height="30" rx="3" fill="#9aa3ad" stroke="#5d646c"/><g class="fan"><circle cx="${ax+17}" cy="${GY-15}" r="9" fill="none" stroke="#3b4148" stroke-width="2"/><line x1="${ax+8}" y1="${GY-15}" x2="${ax+26}" y2="${GY-15}" stroke="#3b4148" stroke-width="2"/><line x1="${ax+17}" y1="${GY-24}" x2="${ax+17}" y2="${GY-6}" stroke="#3b4148" stroke-width="2"/></g></g>`; }
// "for sale"-style board
const sx = bx+W+ (D.ac?104:56);
s += `<g><rect x="${sx}" y="${GY-70}" width="5" height="70" fill="#6b4a2a"/><g class="sign" transform="translate(${sx+2.5} ${GY-70})"><rect x="-4" y="0" width="8" height="8" fill="#6b4a2a"/><rect x="-56" y="6" width="112" height="46" rx="6" fill="#fff8e1" stroke="#6b4a2a" stroke-width="3"/><text x="0" y="26" text-anchor="middle" font-size="12" font-weight="700" fill="#3a2a14">${D.hood}</text><text x="0" y="43" text-anchor="middle" font-size="11" fill="#5b4a33">Built ${D.year}</text></g></g>`;
// --- cars (garage cars!)
const colors = ['#e63946','#2a9d8f','#f4a261','#457b9d'];
let carSvg = '';
for(let i=0;i<cars;i++){
  const bayIdx = cars-1-i, to = GX+9+bayIdx*bay+4, from = -110 - i*40;
  const dur = ((to-from)/230).toFixed(2), delay = (0.4+i*1.1).toFixed(2), c = colors[i%4];
  carSvg += `<g class="car" data-i="${i}" style="--from:${from}px;--to:${to}px;animation:drive ${dur}s cubic-bezier(.2,.7,.3,1) ${delay}s both">
   <g class="body" transform="translate(0 ${GY-26})">
    <path d="M0 22 L0 14 Q0 10 6 9 L14 8 L22 0 L40 0 L48 8 L54 9 Q56 10 56 14 L56 22 Z" fill="${c}" stroke="rgba(0,0,0,.35)"/>
    <path d="M24 2 L38 2 L44 8 L18 8 Z" fill="#cfeaff" stroke="rgba(0,0,0,.3)"/><line x1="31" y1="2" x2="31" y2="8" stroke="rgba(0,0,0,.3)"/>
    <rect x="50" y="12" width="6" height="4" rx="1" fill="#fff6b0"/><g class="glow"><ellipse cx="62" cy="14" rx="14" ry="5" fill="#fff6b0" opacity=".35"/></g>
    <g><circle class="wheel" cx="13" cy="22" r="6" fill="#222"/><circle cx="13" cy="22" r="2.4" fill="#bbb"/><circle class="wheel" cx="43" cy="22" r="6" fill="#222"/><circle cx="43" cy="22" r="2.4" fill="#bbb"/></g>
   </g><text class="beep" x="28" y="${GY-36}" text-anchor="middle">BEEP!</text></g>`;
}
s += carSvg;
// door header strip over cars (garage lintel)
if(cars>0) s += `<rect x="${GX+9}" y="${GY-70}" width="${cars*bay}" height="6" fill="rgba(0,0,0,.35)"/>`;
svg.innerHTML = s;

// --- interactivity
function replay(el){ const a = el.style.animation; el.style.animation='none'; el.getBoundingClientRect(); el.style.animation=a; }
svg.querySelectorAll('.car').forEach(el=>{
  el.addEventListener('animationend',()=>el.classList.add('parked'));
  el.addEventListener('click',()=>{ el.classList.remove('parked'); replay(el); const b=el.querySelector('.beep'); b.classList.remove('on'); void b.getBoundingClientRect(); b.classList.add('on'); try{ beepSound(); }catch(e){} });
});
let ac; function beepSound(){ ac = ac || new (window.AudioContext||window.webkitAudioContext)(); const o=ac.createOscillator(), g=ac.createGain(); o.type='square'; o.frequency.value=440; g.gain.value=.04; o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime+.18); }
function toggle(){ root.classList.toggle('night'); document.getElementById('tog').textContent = root.classList.contains('night') ? '☀️ Day' : '🌙 Night'; }
document.getElementById('tog').onclick = toggle;
['sun','moon'].forEach(id=>document.getElementById(id).addEventListener('click',toggle));
svg.querySelectorAll('rect').forEach(r=>{ if(+r.getAttribute('width')===W) r.addEventListener('click',toggle) });

// --- animated price counter
const fmt = n => '$' + Math.round(n).toLocaleString('en-US');
const el = document.getElementById('price'), t0 = performance.now(), dur = 1300;
(function tick(t){ const p = Math.min(1,(t-t0)/dur), e = 1-Math.pow(1-p,3); el.textContent = fmt(D.price*e); if(p<1) requestAnimationFrame(tick); })(t0);
document.getElementById('range').textContent = `likely range ${fmt(D.lo)} – ${fmt(D.hi)}`;
</script>
"""

def render(params: dict) -> str:
    return TEMPLATE.replace("__DATA__", json.dumps(params))
