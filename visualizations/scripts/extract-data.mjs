// Turns the repository's evidence files into compact data for the compositions.
//
//   node scripts/extract-data.mjs
//
// Writes src/data/door-run.json, src/data/sessions.json and public/door-run-map.png.
// The door-run derivations (moving window, gap anchored on the final laser gap,
// bottle = nearest return ahead in the last scan) follow scripts/render_run.py.
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "../..");
const evidence = path.join(repo, "docs/evidence");
const out = path.resolve(here, "..");
const readJson = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const r3 = (v) => Math.round(v * 1000) / 1000;
const r2 = (v) => Math.round(v * 100) / 100;

const LASER_X = 0.197;
const HALF = 0.29;

// ---- door run ------------------------------------------------------------------------
const run = readJson(path.join(evidence, "nav2-bottle-run-2026-11-14.json"));
const session = readJson(path.join(evidence, "sessions/20261114T085925-nav2-bottle-film.json"));
const poses = run.poses; // [t, x, y, yaw] map frame, 10 Hz

const speedRaw = poses.map((p, i) => {
  const a = poses[Math.max(0, i - 3)];
  const b = poses[Math.min(poses.length - 1, i + 3)];
  const dt = b[0] - a[0];
  return [p[0], dt > 0 ? Math.hypot(b[1] - a[1], b[2] - a[2]) / dt : 0];
});
const moving = speedRaw.filter(([, v]) => v > 0.02).map(([t]) => t);
const t0 = moving[0] - 1;
const t1 = moving[moving.length - 1] + 1.5;
const start = poses.find((p) => p[0] >= moving[0] - 0.5);
const end = poses[poses.length - 1];

const laser = run.scans.filter((s) => s.front != null).map((s) => [s.t, s.front + LASER_X - HALF]);
const still = laser.filter(([t]) => t > moving[moving.length - 1] + 0.3).map(([, g]) => g).sort((a, b) => a - b);
const finalGap = still[Math.floor(still.length / 2)];
const cum = [0];
for (let i = 1; i < poses.length; i++) {
  cum.push(cum[i - 1] + Math.hypot(poses[i][1] - poses[i - 1][1], poses[i][2] - poses[i - 1][2]));
}
const total = cum[cum.length - 1];
const derived = poses.map((p, i) => [p[0], finalGap + total - cum[i]]);
const derivedAt = (t) => derived.reduce((best, d) => (Math.abs(d[0] - t) < Math.abs(best[0] - t) ? d : best))[1];
const laserHits = laser.filter(([t, g]) => Math.abs(g - derivedAt(t)) < 0.1);

const last = run.scans[run.scans.length - 1];
const [lx, ly, lth] = last.pose;
const bottleMap = last.pts.reduce(
  (best, p) => {
    const ahead = Math.abs(Math.atan2(p[1] - ly, p[0] - lx) - lth) < 0.1;
    const d = ahead ? Math.hypot(p[0] - lx, p[1] - ly) : 9;
    return d < best.d ? { p, d } : best;
  },
  { p: null, d: Infinity },
).p;

// View frame: origin at the start pose, +v along the drive, +u to the right.
const h = Math.atan2(end[2] - start[2], end[1] - start[1]);
const ch = Math.cos(h);
const sh = Math.sin(h);
const view = (x, y) => {
  const dx = x - start[1];
  const dy = y - start[2];
  return [r3(dx * sh - dy * ch), r3(dx * ch + dy * sh)];
};
// Heading in the view, clockwise from straight up (CSS rotate convention).
const viewYaw = (yaw) => r3(h - yaw);
const rel = (t) => r2(t - t0);

const bounds = { umin: -3.2, umax: 3.2, vmin: -2.4, vmax: 4.6, pxPerM: 160 };
const inBounds = ([u, v]) => u > bounds.umin && u < bounds.umax && v > bounds.vmin && v < bounds.vmax;

const doorRun = {
  source: "docs/evidence/nav2-bottle-run-2026-11-14.json + sessions/20261114T085925-nav2-bottle-film.json",
  duration: r2(t1 - t0),
  half: HALF,
  bounds,
  poses: poses.filter((p) => p[0] >= t0 - 1 && p[0] <= t1 + 1).map((p) => [rel(p[0]), ...view(p[1], p[2]), viewYaw(p[3])]),
  speed: speedRaw.filter(([t]) => t >= t0 && t <= t1).map(([t, v]) => [rel(t), r3(v)]),
  gap: derived.filter(([t]) => t >= t0 && t <= t1).map(([t, g]) => [rel(t), r3(g)]),
  laserHits: laserHits.filter(([t]) => t >= t0 && t <= t1).map(([t, g]) => [rel(t), r3(g)]),
  plans: run.plans.map((p) => ({ t: rel(p.t), pts: p.xy.map(([x, y]) => view(x, y)) })),
  scans: run.scans
    .filter((s) => s.t >= t0 - 1 && s.t <= t1 + 1)
    .map((s) => ({
      t: rel(s.t),
      pose: [...view(s.pose[0], s.pose[1]), viewYaw(s.pose[2])],
      pts: s.pts.filter((_, i) => i % 2 === 0).map(([x, y]) => view(x, y)).filter(inBounds),
    })),
  bottle: view(...bottleMap),
  goal: view(...run.plans[0].xy[run.plans[0].xy.length - 1]),
  stats: {
    distance: r2(session.summary.odom_distance_m),
    driveSeconds: Math.round(moving[moving.length - 1] - moving[0]),
    finalGap: r2(finalGap),
    target: 0.1,
    speedLimit: 0.15,
    sessionSeconds: session.summary.duration_s,
    reason: session.summary.reason,
    finalPower: session.summary.final_power,
  },
};
fs.writeFileSync(path.join(out, "src/data/door-run.json"), JSON.stringify(doorRun));

// Map raster for the view window: unknown transparent, free faint, occupied bright.
const m = run.map;
const W = Math.round((bounds.umax - bounds.umin) * bounds.pxPerM);
const H = Math.round((bounds.vmax - bounds.vmin) * bounds.pxPerM);
const raw = Buffer.alloc((W * 4 + 1) * H);
for (let j = 0; j < H; j++) {
  raw[j * (W * 4 + 1)] = 0;
  const v = bounds.vmax - (j + 0.5) / bounds.pxPerM;
  for (let i = 0; i < W; i++) {
    const u = bounds.umin + (i + 0.5) / bounds.pxPerM;
    const x = start[1] + v * ch + u * sh;
    const y = start[2] + v * sh - u * ch;
    const cx = Math.floor((x - m.ox) / m.res);
    const cy = Math.floor((y - m.oy) / m.res);
    const c = cx >= 0 && cx < m.w && cy >= 0 && cy < m.h ? m.cells[cy * m.w + cx] : -1;
    const rgba = c < 0 ? [0, 0, 0, 0] : c >= 50 ? [120, 240, 255, 255] : [70, 120, 255, 34];
    rgba.forEach((value, k) => (raw[j * (W * 4 + 1) + 1 + i * 4 + k] = value));
  }
}
fs.writeFileSync(path.join(out, "public/door-run-map.png"), encodePng(W, H, raw));

// ---- all supervised sessions --------------------------------------------------------
const sessionDir = path.join(evidence, "sessions");
const sessions = fs
  .readdirSync(sessionDir)
  .filter((f) => f.endsWith(".json"))
  .sort()
  .map((f) => {
    const s = readJson(path.join(sessionDir, f));
    const sum = s.summary;
    const stamp = f.slice(9, 15);
    const odom = s.events.filter((e) => e.kind === "odom");
    const [x0, y0, yaw0] = sum.odom_start;
    // Track in the start pose's frame: +x forward, +y left.
    const track = odom
      .filter((_, i) => i % 3 === 0)
      .map((e) => {
        const dx = e.x - x0;
        const dy = e.y - y0;
        return [r3(dx * Math.cos(yaw0) + dy * Math.sin(yaw0)), r3(-dx * Math.sin(yaw0) + dy * Math.cos(yaw0))];
      });
    const guard = sum.guards[0];
    return {
      id: f.replace(".json", ""),
      clock: `${stamp.slice(0, 2)}:${stamp.slice(2, 4)}`,
      label: sum.label === "session" ? "nav2-door" : sum.label,
      command: sum.command.slice(1).join(" ").replace("/root/d1-tools/", ""),
      duration: r2(sum.duration_s),
      distance: r3(sum.odom_distance_m),
      turn: r3(Math.abs(Math.atan2(Math.sin(sum.odom_end[2] - yaw0), Math.cos(sum.odom_end[2] - yaw0)))),
      reason: sum.reason.split(":")[0],
      outcome: sum.reason.startsWith("startup_error")
        ? "refused"
        : guard
          ? "guard"
          : sum.reason === "command_finished"
            ? "finished"
            : "aborted",
      guard: guard ? { reason: guard.reason, t: guard.t, nearest: r3(guard.scan.nearest), closest: guard.scan.closest } : null,
      finalPower: sum.final_power,
      track,
    };
  });

const watchdog = readJson(path.join(evidence, "ros2-stand-watchdog-analysis-2026-11-14.json"));
fs.writeFileSync(
  path.join(out, "src/data/sessions.json"),
  JSON.stringify({
    source: "docs/evidence/sessions/*.json + ros2-stand-watchdog-analysis-2026-11-14.json",
    sessions,
    watchdog: {
      tripAfterKill: r3(watchdog.trip_after_kill_s),
      zeroAfterKill: r3(watchdog.zero_after_kill_s),
      disableAfterKill: r3(watchdog.live_ui_disable_after_kill_s),
      powerOffReceipt: r3(watchdog.power_false_receipt_after_kill_s),
    },
  }),
);

console.log(
  `door run: ${doorRun.poses.length} poses, ${doorRun.scans.length} scans, map ${W}x${H}, gap ${doorRun.stats.finalGap} m;`,
  `${sessions.length} sessions`,
);

function encodePng(width, height, rawRows) {
  const crcTable = Array.from({ length: 256 }, (_, n) => {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    return c >>> 0;
  });
  const crc = (buf) => {
    let c = 0xffffffff;
    for (const b of buf) c = crcTable[(c ^ b) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  };
  const chunk = (type, data) => {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length);
    const body = Buffer.concat([Buffer.from(type), data]);
    const sum = Buffer.alloc(4);
    sum.writeUInt32BE(crc(body));
    return Buffer.concat([len, body, sum]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr.set([8, 6, 0, 0, 0], 8);
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", zlib.deflateSync(rawRows)),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}
