#!/usr/bin/env python3
"""Build the static site from src/portal.html + <athlete>/data.json.
Usage: python3 tools/build.py            (builds every athlete folder that has data.json)
The static page fetches data.json at load, keeps Seve's daily check-offs in the
browser (localStorage), and hides the record editors - edits go through the record."""
import json, re, sys, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root/'src'/'portal.html').read_text()

BOOT_RE = re.compile(r"  // Published snapshot: renders for anyone.*?\n  \}\)\(\);\n  renderAll\(\);\n", re.S)
NEW_BOOT = r"""  // Static site build: data.json is the published record; daily check-offs live in this browser.
  let snapAt='';
  const LS=k=>{try{return JSON.parse(localStorage.getItem('portal:'+k)||'null');}catch(e){return null;}};
  const LSset=(k,v)=>{try{localStorage.setItem('portal:'+k,JSON.stringify(v));}catch(e){}};
  db={doc:p=>({set:async d=>{if(!p.startsWith('days/'))throw new Error('read-only');LSset(p,d);reloadDays();},delete:async()=>{throw new Error('read-only');}}),
      collection:c=>({add:async d=>{if(c!=='log')throw new Error('read-only');const k='localLog';LSset(k,(LS(k)||[]).concat([d]));}})};
  function reloadDays(){weekDays={};recentDays={};const mon=new Date(now);mon.setDate(now.getDate()-((now.getDay()+6)%7));const back=new Date(now);back.setDate(now.getDate()-13);
    for(let i=0;i<7;i++){const d=new Date(mon);d.setDate(mon.getDate()+i);const k=localISO(d);const v=LS('days/'+k);if(v)weekDays[k]=v;}
    for(let i=0;i<14;i++){const d=new Date(back);d.setDate(back.getDate()+i);const k=localISO(d);const v=LS('days/'+k);if(v)recentDays[k]=v;}
    day=weekDays[today]||{};}
  const applySnap=sn=>{snapAt=sn.publishedAt||'';events=sn.events||[];log=sn.log||[];team=sn.team||[];profile=sn.profile||{};school=sn.school||{};plans=sn.plans||{};swing=sn.swing||{};journal=sn.journal||{};notes=sn.notes||{};stats=sn.stats||[];};
  try{applySnap(JSON.parse(document.getElementById('snap').textContent));}catch(e){}
  const snapLabel=()=>{if(!snapAt)return 'Published record';const d=new Date(snapAt);return 'Updated '+d.toLocaleDateString(undefined,{month:'short',day:'numeric'});};
  canWrite=true;reloadDays();renderAll();
  const hideEditors=()=>document.querySelectorAll('#btn-add-event,#btn-add-log,#btn-add-member,#btn-edit-profile,#btn-edit-school,#btn-edit-workout,#btn-edit-practice,#btn-edit-swing,#btn-add-note,#btn-add-stat,[data-edit-ev],[data-edit-log],[data-edit-tm],[data-edit-st],[data-review-ev]').forEach(b=>b.hidden=true);
  hideEditors();$('#status').textContent=snapLabel();
  fetch('data.json?t='+Date.now()).then(r=>r.json()).then(sn=>{applySnap(sn);renderAll();hideEditors();$('#status').textContent=snapLabel();}).catch(()=>{});
  new MutationObserver(hideEditors).observe(document.body,{childList:true,subtree:true});
"""

def build(athlete_dir: pathlib.Path):
    data = json.loads((athlete_dir/'data.json').read_text())
    html = src
    # 1. replace embedded snapshot with this athlete's data
    snap = json.dumps(data, ensure_ascii=False, separators=(',',':')).replace('</','<\\/')
    html = re.sub(r'<script id="snap" type="application/json">.*?</script>', lambda m: '<script id="snap" type="application/json">'+snap+'</script>', html, count=1, flags=re.S)
    # 2. swap the boot block
    html, n = BOOT_RE.subn(NEW_BOOT, html, count=1)
    assert n == 1, 'boot block not found'
    if not html.lstrip().lower().startswith('<!doctype'):
        html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + html
    (athlete_dir/'index.html').write_text(html)
    prof = data.get('profile',{})
    name = prof.get('name') or prof.get('bio','').split(',')[0] or athlete_dir.name
    kind = 'Player' if prof.get('kind')=='adult' else 'Student athlete'
    photo = prof.get('photo') or ''
    return name, kind, photo

if __name__ == '__main__':
    built = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d/'data.json').exists():
            built.append((d.name,)+build(d))
    # landing page
    cards = '\n'.join(f'<a class="card" href="{slug}/">' + (f'<img class="ph" src="{slug}/{photo}" alt="">' if photo and not photo.startswith('data:') else '<div class="ph blank"></div>') + f'<div><div class="eyebrow">{kind}</div><h2>{name}</h2><p>Today · Workout · Practice · Swing · Journal · Record</p></div></a>' for slug,name,kind,photo in built)
    (root/'index.html').write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>UGP Juniors</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>:root{{--accent:#1a6b3c;--bg:#f6f7f5;--fg:#111;--muted:#5c6660;--line:#e3e6e2}}body{{margin:0;font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--fg)}}
main{{max-width:960px;margin:0 auto;padding:48px 16px}}.eyebrow{{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:700}}
h1{{font-size:40px;margin:6px 0 4px}}.sub{{color:var(--muted);margin:0 0 32px}}.grid{{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}}
.card{{display:block;background:#fff;border:1px solid var(--line);border-radius:12px;padding:20px;text-decoration:none;color:inherit}}.card:hover{{border-color:var(--accent)}}.card{{display:flex;gap:16px;align-items:center}}.ph{{width:72px;height:72px;border-radius:50%;object-fit:cover;flex:none}}.ph.blank{{background:var(--line)}}.card h2{{margin:6px 0 4px;font-size:22px}}.card p{{margin:0;color:var(--muted);font-size:14px}}
footer{{margin-top:48px;color:var(--muted);font-size:13px}}</style></head><body><main>
<div class="eyebrow">Urban Golf Performance</div><h1>UGP Juniors</h1><p class="sub">One record per athlete: golf, training, recovery, school and home, kept by the whole team.</p>
<div class="grid">{cards}</div>
<footer>An experiment by Urban Golf Performance. Not the UGP company website.</footer></main></body></html>""")
    print('built:', built)
