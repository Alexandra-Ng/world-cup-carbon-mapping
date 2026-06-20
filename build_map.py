"""
Generate interactive fan-travel map HTML from the pipeline modules.

Imports geo and distance scripts (physics) and the emission constants from
emissions. 
See assumptions.
Emits a self-contained HTML
with one travel-share slider per fan-origin country
browser scales each legs emissions live, so no formula or constant is duplicated in JS
python build_map.py
"""
import json
from pathlib import Path

from geo import attach_coords
from distances import add_distances
from emissions import ASSUMPTIONS

TOPO = json.loads(Path("world_110m.json").read_text())


def build(csv_path="worldcup_matches.csv", out="worldcup_map.html", default_share=0.15):
    df = add_distances(attach_coords(csv_path))
    cfg = ASSUMPTIONS
    ef = cfg["ef_air_kg_per_pkm"] * cfg["rf_multiplier"] * (2 if cfg["round_trip"] else 1)
    att = df["attendance"].fillna(df["capacity"] * cfg["fill_factor"])

    legs = []
    for i, r in df.iterrows():
        a = float(att[i])
        for team, lat, lon, dist in [("team_a", "a_lat", "a_lon", "dist_a_km"),
                                     ("team_b", "b_lat", "b_lon", "dist_b_km")]:
            legs.append({
                "origin": r[team],
                "olat": float(r[lat]), "olon": float(r[lon]),
                "venue": r["host_city"], "vlat": float(r["venue_lat"]), "vlon": float(r["venue_lon"]),
                # emissions (tonnes) if 100% of this country's half actually travelled:
                "co2_full_t": a * 0.5 * float(r[dist]) * ef / 1000.0,
            })

    origins = sorted({l["origin"] for l in legs})
    payload = {
        "legs": legs,
        "origins": origins,
        "default_share": default_share,
        "ef_note": f"{cfg['ef_air_kg_per_pkm']} kg/pkm x{cfg['rf_multiplier']} RF, round trip",
    }

    html = (TEMPLATE.replace("__TOPO__", json.dumps(TOPO))
                    .replace("__DATA__", json.dumps(payload))
                    .replace("__EFNOTE__", payload["ef_note"]))
    Path(out).write_text(html)
    print(f"wrote {out} ({round(len(html)/1024)} KB) "
          f"| {len(legs)} legs, {len(origins)} origins, default share {default_share:.0%}")


TEMPLATE = r'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>World Cup 2026 Fan Travel Emission Estimator</title>
<script>window.PlotlyGeoAssets = {topojson: {"world_110m": __TOPO__}};</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<style>
  :root{ --ink:#e6edf3; --muted:#8b949e; --line:#2a313c; --accent:#ff6b6b; --bg:#0d1117; --card:#161b22; --map:#0e1217; }
  *{ box-sizing:border-box; } body{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; color:var(--ink); background:var(--bg); }
  .wrap{ max-width:1080px; margin:0 auto; padding:22px 18px 40px; }
  h1{ font-size:21px; margin:0 0 2px; letter-spacing:-0.01em; } .sub{ color:var(--muted); font-size:13px; margin:0 0 16px; }
  #map{ width:100%; height:540px; background:var(--map); border:1px solid var(--line); border-radius:12px; }
  .controls{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; margin-top:16px; }
  .controls h2{ font-size:12px; text-transform:uppercase; letter-spacing:0.06em; color:var(--muted); margin:0 0 12px; font-weight:600; }
  .grid{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px 18px; }
  .sl label{ display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px; }
  .sl label b{ color:var(--accent); font-variant-numeric:tabular-nums; font-weight:600; }
  .sl input[type=range]{ width:100%; accent-color:var(--accent); }
  .panels{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; margin-top:16px; }
  .card{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; }
  .card h2{ font-size:12px; text-transform:uppercase; letter-spacing:0.06em; color:var(--muted); margin:0 0 10px; font-weight:600; }
  .big{ font-size:26px; font-weight:700; font-variant-numeric:tabular-nums; } .big small{ font-size:13px; color:var(--muted); font-weight:400; }
  .ref{ color:var(--muted); font-size:12px; margin-top:6px; }
  .row{ display:flex; justify-content:space-between; padding:4px 0; font-size:13px; font-variant-numeric:tabular-nums; }
  .row .bar{ flex:1; height:7px; background:#3a2326; border-radius:4px; margin:0 9px; align-self:center; overflow:hidden; }
  .row .bar>span{ display:block; height:100%; background:var(--accent); }
  .note{ color:var(--muted); font-size:11.5px; margin-top:14px; line-height:1.5; }
</style></head>
<body><div class="wrap">
  <h1>World Cup 2026 &mdash; Fan-Travel Carbon (first 8 matches)</h1>
  <p class="sub">Drag a country&#8217;s slider to set what share of its &ldquo;half the crowd&rdquo; actually flew in. Arrows point origin &#8594; host city; width, colour, and label = that leg&#8217;s round-trip CO&#8322;e.</p>
  <div id="map"></div>
  <div class="controls"><h2>Travel share by fan origin</h2><div class="grid" id="sliders"></div></div>
  <div class="panels">
    <div class="card"><h2>Total (current settings)</h2><div class="big" id="total"></div><div class="ref" id="ref"></div></div>
    <div class="card"><h2>Top fan origins (t)</h2><div id="origins"></div></div>
    <div class="card"><h2>By host city (t)</h2><div id="byCity"></div></div>
  </div>
  <p class="note">Emissions are computed by Python pipeline (great-circle distance &times; __EFNOTE__); the sliders only scale how many of each country&#8217;s fans travelled. Home nations read ~0 (capital &asymp; venue).</p>
</div>
<script>
const D = __DATA__;
const toR=d=>d*Math.PI/180, toD=r=>r*180/Math.PI;
const shares = {}; D.origins.forEach(o => shares[o] = D.default_share);

function heat(t){ t=Math.max(0,Math.min(1,t)); return `rgba(${Math.round(255-15*t)},${Math.round(200-150*t)},${Math.round(95-45*t)},0.95)`; }
function bearing(a,b,c,d){ const f1=toR(a),f2=toR(c),dl=toR(d-b); return Math.atan2(Math.sin(dl)*Math.cos(f2), Math.cos(f1)*Math.sin(f2)-Math.sin(f1)*Math.cos(f2)*Math.cos(dl)); }
function destPt(a,b,br,d){ const f1=toR(a),l1=toR(b); const f2=Math.asin(Math.sin(f1)*Math.cos(d)+Math.cos(f1)*Math.sin(d)*Math.cos(br));
  const l2=l1+Math.atan2(Math.sin(br)*Math.sin(d)*Math.cos(f1), Math.cos(d)-Math.sin(f1)*Math.sin(f2)); return [toD(l2),toD(f2)]; }
function gcMid(a,b,c,d){ const f1=toR(a),l1=toR(b),f2=toR(c),l2=toR(d); let x=Math.cos(f1)*Math.cos(l1)+Math.cos(f2)*Math.cos(l2),y=Math.cos(f1)*Math.sin(l1)+Math.cos(f2)*Math.sin(l2),z=Math.sin(f1)+Math.sin(f2);
  const n=Math.hypot(x,y,z); x/=n;y/=n;z/=n; return [toD(Math.atan2(y,x)),toD(Math.atan2(z,Math.hypot(x,y)))]; }
const fmt = n => Math.round(n).toLocaleString();

function emissions(l){ return l.co2_full_t * shares[l.origin]; }    // live scaling

function traces(){
  const live = D.legs.map(l=>({l, e:emissions(l)})).filter(x=>x.e>1);
  const mx = Math.max(1, ...live.map(x=>x.e));
  const T=[];
  live.forEach(({l,e})=>{
    const r=e/mx, w=1+7*Math.sqrt(r), col=heat(r);
    T.push({type:"scattergeo",mode:"lines",lon:[l.olon,l.vlon],lat:[l.olat,l.vlat],line:{width:w,color:col},opacity:0.95,
      hoverinfo:"text",text:`${l.origin} &#8594; ${l.venue}<br>${fmt(e)} t CO&#8322;e`,showlegend:false});
    const b=bearing(l.vlat,l.vlon,l.olat,l.olon), d=toR(3.2), s=toR(26);
    const p1=destPt(l.vlat,l.vlon,b+s,d), p2=destPt(l.vlat,l.vlon,b-s,d);
    T.push({type:"scattergeo",mode:"lines",lon:[p1[0],l.vlon,p2[0]],lat:[p1[1],l.vlat,p2[1]],line:{width:Math.max(1.5,w*0.8),color:col},hoverinfo:"skip",showlegend:false});
  });
  const mids = live.map(x=>gcMid(x.l.olat,x.l.olon,x.l.vlat,x.l.vlon));
  T.push({type:"scattergeo",mode:"text",lon:mids.map(m=>m[0]),lat:mids.map(m=>m[1]),text:live.map(x=>fmt(x.e)+" t"),
    textfont:{size:9.5,color:"#c9d1d9"},textposition:"top center",hoverinfo:"skip",showlegend:false});
  T.push({type:"scattergeo",mode:"markers",lon:live.map(x=>x.l.vlon),lat:live.map(x=>x.l.vlat),text:live.map(x=>x.l.venue),
    marker:{size:6,color:"#f0f6fc",line:{width:1,color:"#0d1117"}},hoverinfo:"text",showlegend:false});
  return T;
}
const layout={margin:{t:6,b:6,l:6,r:6},paper_bgcolor:"#0e1217",
  geo:{scope:"world",resolution:110,projection:{type:"natural earth"},showland:true,landcolor:"#1b2027",
       showcountries:true,countrycolor:"#2c333d",showcoastlines:true,coastlinecolor:"#2c333d",showocean:true,oceancolor:"#0e1217",bgcolor:"#0e1217"}};

function panels(){
  const total = D.legs.reduce((s,l)=>s+emissions(l),0);
  const upper = D.legs.reduce((s,l)=>s+l.co2_full_t,0);
  document.getElementById("total").innerHTML = fmt(total)+' <small>t CO&#8322;e</small>';
  document.getElementById("ref").textContent = `upper bound (all travel): ${fmt(upper)} t`;
  const byO={}, byC={};
  D.legs.forEach(l=>{ const e=emissions(l); byO[l.origin]=(byO[l.origin]||0)+e; byC[l.venue]=(byC[l.venue]||0)+e; });
  const bars=(obj)=>{ const a=Object.entries(obj).filter(([,v])=>v>0).sort((x,y)=>y[1]-x[1]); const m=a.length?a[0][1]:1;
    return a.slice(0,8).map(([n,v])=>`<div class="row"><span>${n}</span><span class="bar"><span style="width:${100*v/m}%"></span></span><span>${fmt(v)}</span></div>`).join(""); };
  document.getElementById("origins").innerHTML = bars(byO);
  document.getElementById("byCity").innerHTML = bars(byC);
}
function redraw(){ Plotly.react("map", traces(), layout, {displayModeBar:false,responsive:true}); panels(); }

// build sliders
document.getElementById("sliders").innerHTML = D.origins.map((o,i)=>
  `<div class="sl"><label>${o} <b id="v${i}">${Math.round(D.default_share*100)}%</b></label>`+
  `<input type="range" min="0" max="100" value="${Math.round(D.default_share*100)}" oninput="setShare(${i},this.value)"></div>`).join("");
window.setShare=(i,val)=>{ const o=D.origins[i]; shares[o]=val/100; document.getElementById("v"+i).textContent=val+"%"; redraw(); };

Plotly.newPlot("map", traces(), layout, {displayModeBar:false,responsive:true}).then(panels);
</script></body></html>'''

if __name__ == "__main__":
    build()
