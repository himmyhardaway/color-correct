import sys, html, collections, json
G=sys.argv[1]
rows=[l.rstrip('\n').split('\t') for l in open(G+'/index.tsv') if l.strip()]
groups=collections.OrderedDict()
for i,rel in sorted(rows,key=lambda r:r[1].lower()):
    parts=rel.split('/')
    grp=' / '.join(p.strip() for p in parts[:-1]) if len(parts)>1 else 'Loose'
    name=parts[-1].rsplit('.',1)[0].strip()
    groups.setdefault(grp,[]).append((i,name,rel))
nav=''.join(f'<a href="#g{n}">{html.escape(g)} <span>{len(v)}</span></a>' for n,(g,v) in enumerate(groups.items()))
secs=''
for n,(g,v) in enumerate(groups.items()):
    cards=''.join(f'<figure class="lut" data-rel="{html.escape(r)}" tabindex="0"><img loading="lazy" src="thumbs/{i}.jpg" alt="{html.escape(nm)}"><figcaption><span>{html.escape(nm)}</span><button class="star" aria-label="favorite">☆</button></figcaption></figure>' for i,nm,r in v)
    secs+=f'<section id="g{n}"><h2>{html.escape(g)} <span>{len(v)}</span></h2><div class="grid">{cards}</div></section>'
total=len(rows)
open(G+'/LUT Gallery.html','w').write(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>LUT Gallery</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Libre+Caslon+Display&family=Libre+Franklin:wght@400;600;700&family=Courier+Prime:wght@400;700&display=swap">
<style>
:root{{--bg:#14171C;--paper:#1C2027;--ink:#E7E4DB;--muted:#9AA1AC;--rule:#2E343D;--brass:#D4B25E;--display:"Libre Caslon Display",Georgia,serif;--body:"Libre Franklin",Arial,sans-serif;--mono:"Courier Prime",monospace}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body)}}
header{{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--rule);padding:12px 16px;display:grid;grid-template-columns:auto 1fr auto;gap:16px;align-items:center}}
header img{{width:170px;display:block;border:1px solid var(--rule)}}
h1{{font-family:var(--display);font-weight:400;font-size:30px;margin:0}}
.sub{{color:var(--muted);font-size:13px;margin:4px 0 0}}
#favbar{{display:grid;gap:6px;justify-items:end;font-size:13px}}
#favbar button{{font:700 13px var(--mono);background:var(--brass);color:#1C1A14;border:0;border-radius:4px;padding:6px 10px;cursor:pointer}}
nav{{display:flex;flex-wrap:wrap;gap:6px;padding:12px 16px}}
nav a{{font:12px var(--mono);color:var(--ink);text-decoration:none;border:1px solid var(--rule);padding:3px 8px;border-radius:4px}} nav a span{{color:var(--muted)}}
section{{padding:6px 16px 18px;scroll-margin-top:110px}}
h2{{font:700 12px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--brass);border-bottom:1px solid var(--rule);padding-bottom:6px}} h2 span{{color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
.lut{{margin:0;background:var(--paper);border:1px solid var(--rule);cursor:zoom-in}}
.lut img{{width:100%;display:block;aspect-ratio:16/9;object-fit:cover}}
.lut figcaption{{display:flex;justify-content:space-between;align-items:center;gap:6px;padding:6px 8px;font-size:12px}}
.lut.fav{{border-color:var(--brass)}}
.star{{background:none;border:0;color:var(--brass);font-size:18px;cursor:pointer;padding:0 2px}}
#big{{position:fixed;inset:0;background:rgba(8,9,11,.94);display:none;place-items:center;z-index:10;padding:16px}}
#big.on{{display:grid}} #big img{{max-width:min(1100px,100%);max-height:78vh;display:block}}
#big p{{text-align:center;font-size:14px;margin:10px 0 0}} #big small{{color:var(--muted);display:block;margin-top:4px}}
@media (max-width:720px){{header{{grid-template-columns:1fr}} header img{{width:120px}} #favbar{{justify-items:start}}}}
</style></head><body>
<header><img src="original.png" alt="Original frame, no LUT"><div><h1>LUT Gallery</h1><p class="sub">All {total} LUTs from the Extreme drive, each on the same frame of you from the Tolly close angle. Top left is the original with no LUT. Click a frame to enlarge it, and hold <b>Space</b> while it's open to see the original. Tap ☆ to shortlist.</p></div>
<div id="favbar"><span id="favcount">0 shortlisted</span><button id="copy">Copy shortlist for Claude</button></div></header>
<nav>{nav}</nav>{secs}
<div id="big" role="dialog" aria-modal="true"><div><img id="bigimg" alt=""><p id="bigname"></p></div></div>
<script>
const KEY='lut-gallery-favs';let favs=new Set();try{{favs=new Set(JSON.parse(localStorage.getItem(KEY)||'[]'))}}catch(e){{}}
const save=()=>{{try{{localStorage.setItem(KEY,JSON.stringify([...favs]))}}catch(e){{}};document.getElementById('favcount').textContent=favs.size+' shortlisted'}};
document.querySelectorAll('.lut').forEach(f=>{{const r=f.dataset.rel,b=f.querySelector('.star');
 const paint=()=>{{f.classList.toggle('fav',favs.has(r));b.textContent=favs.has(r)?'★':'☆'}};paint();
 b.addEventListener('click',e=>{{e.stopPropagation();favs.has(r)?favs.delete(r):favs.add(r);paint();save()}});
 f.addEventListener('click',()=>open(f));f.addEventListener('keydown',e=>{{if(e.key==='Enter')open(f)}});}});
save();
const big=document.getElementById('big'),bi=document.getElementById('bigimg'),bn=document.getElementById('bigname');let cur='';
function open(f){{cur=f.querySelector('img').src;bi.src=cur;bn.innerHTML=f.dataset.rel+'<small>Hold Space to see the original · Esc or click to close</small>';big.classList.add('on')}}
big.addEventListener('click',()=>big.classList.remove('on'));
addEventListener('keydown',e=>{{if(!big.classList.contains('on'))return;if(e.key==='Escape')big.classList.remove('on');if(e.code==='Space'){{e.preventDefault();bi.src='original.png'}}}});
addEventListener('keyup',e=>{{if(e.code==='Space'&&big.classList.contains('on'))bi.src=cur}});
document.getElementById('copy').addEventListener('click',()=>{{const t='LUT shortlist:\\n'+[...favs].join('\\n');navigator.clipboard.writeText(t).then(()=>{{document.getElementById('copy').textContent='Copied — paste to Claude'}})}});
</script></body></html>''')
print(total, len(groups))
