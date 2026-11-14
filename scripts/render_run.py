"""Render a recorded Nav2 run (scripts/record_run.py) as a presentation page.

    python3 scripts/render_run.py RUN.json SESSION.json OUT.html [bottle_x bottle_y]

Self-contained HTML (inline SVG + embedded map raster, hover tooltips). Screenshot
it for slides:  google-chrome --headless --screenshot=OUT.png --window-size=1600,900 OUT.html
"""
import base64
import html
import io
import json
import math
import sys
from PIL import Image

run = json.load(open(sys.argv[1])); session = json.load(open(sys.argv[2])); out = sys.argv[3]
summary = session['summary']
LASER_X, HALF = .197, .29

# ---- time base and derived series -------------------------------------------------
poses = run['poses']                                   # (t, x, y, yaw) map frame, 10 Hz
speed = []
for i in range(len(poses)):
    a, b = poses[max(0, i - 3)], poses[min(len(poses) - 1, i + 3)]
    dt = b[0] - a[0]
    v = math.hypot(b[1] - a[1], b[2] - a[2]) / dt if dt > 0 else 0.
    speed.append((poses[i][0], v))
moving = [t for t, v in speed if v > .02]
t0, t1 = moving[0] - 1., moving[-1] + 1.5
start = next(p for p in poses if p[0] >= moving[0] - .5)
end = poses[-1]
drive_s = moving[-1] - moving[0]

scans = run['scans']
# The laser's +-3 deg "front" reading sometimes misses the thin bottle neck and hits
# something behind it, so the gap curve is anchored on the robot's own travel: the
# median laser gap at standstill after the stop, plus the path length still to go.
laser = [(s['t'], s['front'] + LASER_X - HALF) for s in scans if s['front'] is not None]
still = sorted(g for t, g in laser if t > moving[-1] + .3)
final_gap = still[len(still) // 2]
cum = [0.]
for a, b in zip(poses, poses[1:]): cum.append(cum[-1] + math.hypot(b[1] - a[1], b[2] - a[2]))
total = cum[-1]
derived = [(p[0], final_gap + total - c) for p, c in zip(poses, cum)]
def derived_at(t): return min(derived, key=lambda d: abs(d[0] - t))[1]
clean = [(t, g) for t, g in laser if abs(g - derived_at(t)) < .10]      # laser hits on the bottle
bottle = (float(sys.argv[4]), float(sys.argv[5])) if len(sys.argv) > 5 else None
if bottle is None:                                     # nearest return ahead in the last scan
    s = scans[-1]; x, y, th = s['pose']
    bottle = min(s['pts'], key=lambda p: math.hypot(p[0] - x, p[1] - y)
                 if abs(math.atan2(p[1] - y, p[0] - x) - th) < .1 else 9)

# ---- map view: rotated so the drive goes up the page -------------------------------
h = math.atan2(end[2] - start[2], end[1] - start[1])
ch, sh = math.cos(h), math.sin(h)
UMIN, UMAX, VMIN, VMAX, S = -1.45, 1.45, -.75, 2.95, 190.   # metres around the start; px/m
W, H = int((UMAX - UMIN) * S), int((VMAX - VMIN) * S)


def view(x, y):
    dx, dy = x - start[1], y - start[2]
    u, v = dx * sh - dy * ch, dx * ch + dy * sh
    return (u - UMIN) * S, (VMAX - v) * S


m = run['map']; res, mw, mh, ox, oy, cells = m['res'], m['w'], m['h'], m['ox'], m['oy'], m['cells']
img = Image.new('RGB', (W, H)); px = img.load()
COL = {-1: (233, 232, 228), 0: (255, 255, 255)}
for j in range(H):
    v = VMAX - (j + .5) / S
    for i in range(W):
        u = UMIN + (i + .5) / S
        x = start[1] + v * ch + u * sh; y = start[2] + v * sh - u * ch
        cx, cy = int((x - ox) / res), int((y - oy) / res)
        c = cells[cy * mw + cx] if 0 <= cx < mw and 0 <= cy < mh else -1
        px[i, j] = COL.get(c, (82, 81, 78) if c >= 50 else (255, 255, 255))
buf = io.BytesIO(); img.save(buf, 'PNG'); raster = base64.b64encode(buf.getvalue()).decode()


def path_d(pts):
    return 'M' + ' L'.join('%.1f,%.1f' % view(x, y) for x, y in pts)


def footprint(x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    corners = [(HALF, HALF), (HALF, -HALF), (-HALF, -HALF), (-HALF, HALF)]
    return ' '.join('%.1f,%.1f' % view(x + a * c - b * s, y + a * s + b * c) for a, b in corners)


def nose(x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    pts = [(HALF - .02, .08), (HALF + .06, 0), (HALF - .02, -.08)]
    return ' '.join('%.1f,%.1f' % view(x + a * c - b * s, y + a * s + b * c) for a, b in pts)


plan = run['plans'][0]['xy']
driven = [(p[1], p[2]) for p in poses if p[0] >= start[0] - .2]
last_scan = scans[-1]['pts']
bx, by = view(*bottle)
gx, gy = view(*plan[-1])
sx, sy = view(start[1], start[2])
scan_dots = ''.join('<circle cx="%.1f" cy="%.1f" r="1.6"/>' % view(x, y) for x, y in last_scan
                    if 0 <= view(x, y)[0] <= W and 0 <= view(x, y)[1] <= H)
bar_x, bar_y = W - 24 - .5 * S, H - 22
map_svg = '''
<svg class="map" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="Top-down SLAM map: the robot drove {dist:.2f} m along the Nav2 plan and stopped {gap:.2f} m short of the bottle">
  <image href="data:image/png;base64,{raster}" width="{W}" height="{H}"/>
  <g class="scan">{scan_dots}</g>
  <polygon class="fp-start" points="{fp0}"/>
  <path class="plan" d="{plan_d}"/>
  <path class="driven" d="{driven_d}"/>
  <polygon class="fp-end" points="{fp1}"/><polygon class="nose" points="{nose1}"/>
  <circle class="bottle" cx="{bx:.1f}" cy="{by:.1f}" r="9"/>
  <text class="lbl" x="{blx:.1f}" y="{bly:.1f}" text-anchor="end">Bottle (door stand-in)</text>
  <text class="lbl muted" x="{slx:.1f}" y="{sly:.1f}">Start</text>
  <text class="lbl" x="{elx:.1f}" y="{ely:.1f}">Stopped {gap:.2f} m short</text>
  <line class="scale" x1="{bar_x:.0f}" y1="{bar_y:.0f}" x2="{bar_x2:.0f}" y2="{bar_y:.0f}"/>
  <text class="lbl muted" x="{bar_xm:.0f}" y="{bar_yt:.0f}" text-anchor="middle">0.5 m</text>
</svg>'''.format(
    W=W, H=H, raster=raster, scan_dots=scan_dots, fp0=footprint(start[1], start[2], start[3]),
    plan_d=path_d(plan), driven_d=path_d(driven), fp1=footprint(end[1], end[2], end[3]),
    nose1=nose(end[1], end[2], end[3]), bx=bx, by=by, blx=bx - 16, bly=by - 10,
    slx=sx + HALF * S + 10, sly=sy + 5, elx=view(end[1], end[2])[0] + HALF * S + 10,
    ely=view(end[1], end[2])[1] + 28, gap=final_gap, dist=summary['odom_distance_m'],
    bar_x=bar_x, bar_x2=bar_x + .5 * S, bar_y=bar_y, bar_xm=bar_x + .25 * S, bar_yt=bar_y - 8)


# ---- small multiples: gap and speed over time -----------------------------------------
CW, CH, ML, MR, MT, MB = 760, 230, 56, 24, 16, 34
XMAX = math.ceil(t1 - t0)


def chart(cid, series, ymax, yticks, fmt, unit, ref=None, ref_label=None, markers=None):
    def X(t): return ML + (t - t0) / XMAX * (CW - ML - MR)
    def Y(v): return MT + (1 - v / ymax) * (CH - MT - MB)
    pts = [(t, v) for t, v in series if t0 <= t <= t1]
    grid = ''.join('<line class="grid" x1="{0}" x2="{1}" y1="{2:.1f}" y2="{2:.1f}"/>'
                   '<text class="tick" x="{3}" y="{4:.1f}" text-anchor="end">{5}</text>'.format(
                       ML, CW - MR, Y(v), ML - 8, Y(v) + 4, fmt % v) for v in yticks)
    xt = ''.join('<text class="tick" x="{0:.1f}" y="{1}" text-anchor="middle">{2}</text>'.format(
        X(t0 + s), CH - 12, s) for s in range(0, XMAX + 1, 2))
    refl = ('<line class="ref" x1="{0}" x2="{1}" y1="{2:.1f}" y2="{2:.1f}"/>'
            '<text class="lbl muted" x="{5}" y="{3:.1f}">{4}</text>'.format(
                ML, CW - MR, Y(ref), Y(ref) - 6, ref_label, ML + 6)) if ref is not None else ''
    line = 'M' + ' L'.join('%.1f,%.1f' % (X(t), Y(v)) for t, v in pts)
    dots = ''.join('<circle class="dot" cx="%.1f" cy="%.1f" r="4"/>' % (X(t), Y(v))
                   for t, v in (markers or []) if t0 <= t <= t1)
    data = json.dumps([[round(t - t0, 2), round(v, 3)] for t, v in pts])
    return ('<svg class="chart" id="{id}" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}" '
            'data-series=\'{data}\' data-unit="{unit}" data-fmt="{nd}" data-ml="{ML}" data-mr="{MR}" '
            'data-mt="{MT}" data-mb="{MB}" data-ymax="{ymax}" data-xmax="{XMAX}">'
            '{grid}{xt}{refl}<path class="series" d="{line}"/>{dots}'
            '<line class="xhair" y1="{MT}" y2="{yb}" visibility="hidden"/>'
            '<circle class="hdot" r="5" visibility="hidden"/>'
            '<rect class="hit" x="{ML}" y="0" width="{hw}" height="{CH}"/></svg>').format(
        id=cid, CW=CW, CH=CH, data=data, unit=unit, nd=2 if ymax < 1 else 2, ML=ML, MR=MR, MT=MT,
        MB=MB, ymax=ymax, XMAX=XMAX, grid=grid, xt=xt, refl=refl, line=line, dots=dots,
        yb=CH - MB, hw=CW - ML - MR)


gap_svg = chart('gap', derived, 1.4, [0, .25, .5, .75, 1., 1.25], '%.2f', 'm', .10, 'Target 0.10 m', clean)
spd_svg = chart('spd', speed, .2, [0, .05, .1, .15, .2], '%.2f', 'm/s', .15, 'Nav2 speed limit 0.15 m/s')
rows = ''.join('<tr><td>%.1f</td><td>%.3f</td></tr>' % (t - t0, g) for t, g in clean if t0 <= t <= t1)

tiles = [('Distance driven', '%.2f m' % summary['odom_distance_m']),
         ('Drive time', '%.0f s' % drive_s),
         ('Final gap to bottle', '%.2f m' % final_gap),
         ('Nav2 result', 'Goal reached' if summary['reason'] == 'command_finished' and not summary['guards'] else summary['reason'])]
tiles_html = ''.join('<div class="tile"><div class="tl">{0}</div><div class="tv">{1}</div></div>'.format(
    html.escape(a), html.escape(b)) for a, b in tiles)

page = '''<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8">
<title>D1 drives itself to the door: Nav2 run</title>
<style>
.viz-root {{ --surface-1:#fcfcfb; --text-primary:#0b0b0b; --text-secondary:#52514e; --text-muted:#7a7974;
  --grid:#e6e5e0; --series-1:#2a78d6; --series-2:#eb6834; --bottle:#0b0b0b; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#fcfcfb; }}
.viz-root {{ width:1600px; height:900px; padding:28px 40px; background:var(--surface-1); color:var(--text-primary);
  font-family:"Inter","Helvetica Neue",Arial,sans-serif; display:grid; grid-template-columns:{W}px 1fr;
  grid-template-rows:auto 1fr auto; column-gap:44px; }}
header {{ grid-column:1 / 3; margin-bottom:14px; }}
h1 {{ font-size:34px; font-weight:600; margin:0 0 4px; letter-spacing:-.01em; }}
.sub {{ font-size:17px; color:var(--text-secondary); }}
.legend {{ display:flex; gap:22px; font-size:14px; color:var(--text-secondary); margin:0 0 8px; }}
.legend i {{ display:inline-block; width:22px; height:0; border-top:2px solid; vertical-align:middle; margin-right:7px; }}
.legend .k-plan {{ border-color:var(--series-2); border-top-style:dashed; }}
.legend .k-driven {{ border-color:var(--series-1); }}
.legend.small {{ font-size:12.5px; margin:2px 0 0; }}
.legend .k-dot {{ width:8px; height:8px; border:0; border-radius:50%; background:var(--series-1); }}
.legend .k-scan {{ width:6px; height:6px; border:0; border-radius:50%; background:var(--text-muted); }}
.legend .k-bottle {{ width:12px; height:12px; border:2.5px solid var(--bottle); border-radius:50%; }}
svg.map {{ display:block; border-radius:6px; }}
.scan circle {{ fill:var(--text-muted); }}
.plan {{ fill:none; stroke:var(--series-2); stroke-width:2; stroke-dasharray:7 5; }}
.driven {{ fill:none; stroke:var(--series-1); stroke-width:3; stroke-linecap:round; stroke-linejoin:round; }}
.fp-start {{ fill:none; stroke:var(--text-muted); stroke-width:1.5; stroke-dasharray:4 4; }}
.fp-end {{ fill:rgba(42,120,214,.12); stroke:var(--series-1); stroke-width:2; }}
.nose {{ fill:var(--series-1); }}
.bottle {{ fill:#fcfcfb; stroke:var(--bottle); stroke-width:3; }}
.lbl {{ font-size:14px; fill:var(--text-primary); paint-order:stroke; stroke:#fcfcfb; stroke-width:4px; }}
.lbl.muted {{ fill:var(--text-secondary); }}
.scale {{ stroke:var(--text-primary); stroke-width:2; }}
.right {{ display:flex; flex-direction:column; gap:10px; }}
.tiles {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:10px; }}
.tile {{ border:1px solid var(--grid); border-radius:8px; padding:12px 14px; }}
.tl {{ font-size:13px; color:var(--text-secondary); }}
.tv {{ font-size:28px; font-weight:600; margin-top:4px; }}
h2 {{ font-size:16px; font-weight:600; margin:6px 0 0; }}
.chart {{ display:block; overflow:visible; }}
.grid {{ stroke:var(--grid); stroke-width:1; }}
.tick {{ font-size:12px; fill:var(--text-muted); font-variant-numeric:tabular-nums; }}
.ref {{ stroke:var(--text-muted); stroke-width:1.5; stroke-dasharray:5 4; }}
.series {{ fill:none; stroke:var(--series-1); stroke-width:2; stroke-linejoin:round; }}
.dot {{ fill:var(--series-1); stroke:var(--surface-1); stroke-width:2; }}
.xhair {{ stroke:var(--text-secondary); stroke-width:1; }}
.hdot {{ fill:var(--series-1); stroke:var(--surface-1); stroke-width:2; }}
.hit {{ fill:transparent; cursor:crosshair; }}
.axis {{ font-size:12px; color:var(--text-muted); margin:-2px 0 0 {ML}px; }}
#tip {{ position:fixed; pointer-events:none; background:#0b0b0b; color:#fcfcfb; font-size:13px; padding:6px 9px;
  border-radius:5px; display:none; font-variant-numeric:tabular-nums; }}
footer {{ grid-column:1 / 3; font-size:12.5px; color:var(--text-muted); margin-top:10px; }}
details {{ font-size:12px; color:var(--text-secondary); }}
</style></head><body>
<div class="viz-root">
<header><h1>The D1 drives itself to the door</h1>
<div class="sub">ROS 2 Nav2 + SLAM Toolbox on the closed Hyundai D1, via our bridge and supervised drive gate. A bottle stands in for the door.</div></header>
<div>
  <div class="legend"><span><i class="k-plan"></i>Nav2 plan</span><span><i class="k-driven"></i>Driven path</span>
  <span><i class="k-scan"></i>Laser returns at the stop</span><span><i class="k-bottle"></i>Bottle</span></div>
  {map_svg}
</div>
<div class="right">
  <div class="tiles">{tiles_html}</div>
  <h2>Gap from front bumper to the bottle (m)</h2>
  <div class="legend small"><span><i class="k-driven"></i>From robot travel, anchored on the final laser gap</span>
  <span><i class="k-dot"></i>Laser hits on the bottle</span></div>
  {gap_svg}
  <h2>Forward speed (m/s), from SLAM pose</h2>
  {spd_svg}
  <div class="axis">Seconds since the robot started moving</div>
  <details><summary>Data table: laser gap to bottle</summary><table><tr><th>s</th><th>gap (m)</th></tr>{rows}</table></details>
</div>
<footer>Session {sid}: one Nav2 goal, red stop manned, forward scan guard on, motors powered off at the end.
Goal set 0.10 m short of the bottle; the SLAM map shifted during the drive, so it stopped at {gap:.2f} m.
Evidence: docs/evidence/sessions/{sid}.json, docs/evidence/nav2-bottle-run-2026-11-14.json</footer>
</div>
<div id="tip"></div>
<script>
const tip = document.getElementById('tip');
const charts = [...document.querySelectorAll('svg.chart')];
function show(tsec, ev) {{
  const lines = [];
  for (const c of charts) {{
    const d = JSON.parse(c.dataset.series), ml = +c.dataset.ml, mr = +c.dataset.mr, mt = +c.dataset.mt,
      mb = +c.dataset.mb, ym = +c.dataset.ymax, xm = +c.dataset.xmax, w = c.viewBox.baseVal.width, h = c.viewBox.baseVal.height;
    let best = d[0]; for (const p of d) if (Math.abs(p[0] - tsec) < Math.abs(best[0] - tsec)) best = p;
    const x = ml + best[0] / xm * (w - ml - mr), y = mt + (1 - best[1] / ym) * (h - mt - mb);
    const xh = c.querySelector('.xhair'), hd = c.querySelector('.hdot');
    xh.setAttribute('x1', x); xh.setAttribute('x2', x); xh.setAttribute('visibility', 'visible');
    hd.setAttribute('cx', x); hd.setAttribute('cy', y); hd.setAttribute('visibility', 'visible');
    lines.push((c.id === 'gap' ? 'Gap ' : 'Speed ') + best[1].toFixed(2) + ' ' + c.dataset.unit);
  }}
  tip.innerHTML = tsec.toFixed(1) + ' s<br>' + lines.join('<br>');
  tip.style.display = 'block'; tip.style.left = (ev.clientX + 14) + 'px'; tip.style.top = (ev.clientY + 14) + 'px';
}}
function hide() {{ tip.style.display = 'none';
  for (const c of charts) for (const s of c.querySelectorAll('.xhair,.hdot')) s.setAttribute('visibility', 'hidden'); }}
for (const c of charts) {{
  const r = c.querySelector('.hit');
  r.addEventListener('mousemove', ev => {{
    const b = c.getBoundingClientRect(), w = c.viewBox.baseVal.width, k = b.width / w;
    const ml = +c.dataset.ml, mr = +c.dataset.mr, xm = +c.dataset.xmax;
    show(Math.max(0, Math.min(xm, ((ev.clientX - b.left) / k - ml) / (w - ml - mr) * xm)), ev);
  }});
  r.addEventListener('mouseleave', hide);
}}
</script></body></html>'''.format(W=W, ML=ML, map_svg=map_svg, tiles_html=tiles_html, gap_svg=gap_svg,
                                  spd_svg=spd_svg, rows=rows, sid=sys.argv[2].split('/')[-1][:-5], gap=final_gap)
open(out, 'w').write(page)
print('wrote', out, 'final gap %.3f m, drive %.1f s, bottle %s' % (final_gap, drive_s, bottle))
