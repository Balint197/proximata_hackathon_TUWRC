import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import run from "../data/door-run.json";
import { Brackets, Flash, Overlay, Tag } from "../shared";
import { clamp, color, display, inOutCubic, mono, outExpo, sample } from "../theme";

// Scene timing, in seconds from the scene start.
const REVEAL_END = 1.8;
const PLAN_START = 1.4;
const PLAN_END = 2.8;
export const DRIVE_START = 3;

const { bounds, half } = run;
const P = bounds.pxPerM;
const W = Math.round((bounds.umax - bounds.umin) * P);
const H = Math.round((bounds.vmax - bounds.vmin) * P);
const X = (u) => (u - bounds.umin) * P;
const Y = (v) => (bounds.vmax - v) * P;
const ANCHOR = [700, 560];
const FADE_X = "linear-gradient(90deg, transparent, black 22%, black 78%, transparent)";
const FADE_Y = "linear-gradient(180deg, transparent, black 15%, black 85%, transparent)";
const deg = (rad) => (rad * 180) / Math.PI;

const poseAt = (t) => [sample(run.poses, t, 1), sample(run.poses, t, 2), sample(run.poses, t, 3)];
const final = run.poses[run.poses.length - 1];

const useRunClock = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = Math.max(0, frame / fps - DRIVE_START);
  return { frame, fps, t: Math.min(t, run.duration), s: frame / fps };
};

const pathD = (pts) => pts.map(([u, v], i) => `${i ? "L" : "M"}${X(u).toFixed(1)},${Y(v).toFixed(1)}`).join(" ");

const Robot = ({ u, v, yaw, glow }) => {
  const b = half * P;
  return (
    <g transform={`translate(${X(u)},${Y(v)}) rotate(${deg(yaw)})`}>
      <rect x={-b} y={-b} width={2 * b} height={2 * b} rx={14} fill="rgba(92,242,255,0.10)" stroke={color.cyan} strokeWidth={4} style={{ filter: `drop-shadow(0 0 ${glow}px ${color.cyan})` }} />
      <rect x={-b + 14} y={-b + 14} width={2 * b - 28} height={2 * b - 28} rx={8} fill="none" stroke={`${color.cyan}55`} strokeWidth={2} />
      <path d={`M${-22},${-b + 6} L0,${-b - 22} L22,${-b + 6} Z`} fill={color.cyan} />
      <circle cx={0} cy={-0.197 * P} r={7} fill="#fff" />
    </g>
  );
};

const LidarFan = ({ u, v, yaw, frame }) => {
  const r = 2.4 * P;
  const a = (115 * Math.PI) / 180;
  const pt = (ang) => [Math.sin(ang) * r, -Math.cos(ang) * r];
  const [x1, y1] = pt(-a);
  const [x2, y2] = pt(a);
  const sweep = -115 + ((frame * 9) % 230);
  return (
    <g transform={`translate(${X(u)},${Y(v)}) rotate(${deg(yaw)}) translate(0,${-0.197 * P})`}>
      <defs>
        <radialGradient id="fan" cx="0" cy="0" r={r} gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor={color.cyan} stopOpacity="0.22" />
          <stop offset="1" stopColor={color.cyan} stopOpacity="0" />
        </radialGradient>
      </defs>
      <path d={`M0,0 L${x1},${y1} A${r},${r} 0 1 1 ${x2},${y2} Z`} fill="url(#fan)" />
      <g transform={`rotate(${sweep})`}>
        <path d={`M0,0 L${-r * 0.06},${-r} L${r * 0.06},${-r} Z`} fill="url(#fan)" opacity={1.6} />
        <line x1={0} y1={0} x2={0} y2={-r} stroke={color.cyan} strokeOpacity={0.5} strokeWidth={2} />
      </g>
    </g>
  );
};

const Sonar = ({ u, v, frame, tint }) => (
  <g transform={`translate(${X(u)},${Y(v)})`}>
    {[0, 1, 2].map((k) => {
      const p = ((frame + k * 15) % 45) / 45;
      return <circle key={k} r={10 + p * 70} fill="none" stroke={tint} strokeWidth={3} opacity={1 - p} />;
    })}
    <circle r={11} fill={tint} style={{ filter: `drop-shadow(0 0 12px ${tint})` }} />
  </g>
);

const World = () => {
  const { frame, t, s } = useRunClock();
  const [u, v, yaw] = poseAt(t);
  const driveEnd = DRIVE_START + run.duration;

  // Camera: whole map, then chase the robot, then push in on the final gap.
  const chase = [u, v + 0.5];
  const finale = [final[1], final[2] + half + 0.08];
  const k1 = interpolate(s, [1.2, 3.4], [0, 1], { ...clamp, easing: inOutCubic });
  const k2 = interpolate(s, [driveEnd - 0.2, driveEnd + 1.6], [0, 1], { ...clamp, easing: inOutCubic });
  const cu = interpolate(k1, [0, 1], [0, chase[0]]) * (1 - k2) + finale[0] * k2;
  const cv = interpolate(k1, [0, 1], [1.1, chase[1]]) * (1 - k2) + finale[1] * k2;
  const zoom = interpolate(k1, [0, 1], [0.86, 1.55]) * (1 - k2) + 2.5 * k2;

  const reveal = interpolate(s, [0, REVEAL_END], [0, 1600], { ...clamp, easing: outExpo });
  const startPose = run.poses[0];
  const planProgress = interpolate(s, [PLAN_START, PLAN_END], [0, 1], { ...clamp, easing: outExpo });
  const activePlan = t > 0 ? [...run.plans].reverse().find((p) => p.t <= t) ?? run.plans[0] : run.plans[0];
  const planPts = activePlan === run.plans[0] ? activePlan.pts.slice(0, Math.max(2, Math.ceil(activePlan.pts.length * planProgress))) : [[u, v], ...activePlan.pts];
  const driven = [...run.poses.filter((p) => p[0] <= t).map((p) => [p[1], p[2]]), [u, v]];
  const scans = run.scans.filter((sc) => sc.t <= Math.max(t, 0.01)).slice(-2);
  const ghosts = run.poses.filter((p, i) => i % 15 === 0 && p[0] > 0.8 && p[0] < t - 0.4 && p[0] > t - 6);
  const robotIn = interpolate(s, [0.9, 1.5], [0, 1], { ...clamp, easing: outExpo });
  const arrived = t >= run.duration - 0.05;
  const nose = final[2] + half;

  return (
    <div
      style={{
        position: "absolute",
        width: W,
        height: H,
        transformOrigin: "0 0",
        translate: `${ANCHOR[0] - X(cu) * zoom}px ${ANCHOR[1] - Y(cv) * zoom}px`,
        scale: zoom,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          WebkitMaskImage: `radial-gradient(circle at ${X(startPose[1])}px ${Y(startPose[2])}px, black ${reveal}px, transparent ${reveal + 120}px)`,
          maskImage: `radial-gradient(circle at ${X(startPose[1])}px ${Y(startPose[2])}px, black ${reveal}px, transparent ${reveal + 120}px)`,
        }}
      >
        <div style={{ position: "absolute", inset: 0, WebkitMaskImage: FADE_X, maskImage: FADE_X }}>
          <div style={{ position: "absolute", inset: 0, WebkitMaskImage: FADE_Y, maskImage: FADE_Y }}>
            <Img src={staticFile("door-run-map.png")} style={{ width: W, height: H, imageRendering: "pixelated", filter: `drop-shadow(0 0 6px ${color.cyan}aa)` }} />
          </div>
        </div>
      </div>
      <svg width={W} height={H} style={{ position: "absolute", overflow: "visible" }}>
        <circle
          cx={X(startPose[1])}
          cy={Y(startPose[2])}
          r={reveal}
          fill="none"
          stroke={color.cyan}
          strokeWidth={3}
          opacity={interpolate(s, [0, 0.3, REVEAL_END], [0, 0.9, 0], clamp)}
        />
        {ghosts.map((p) => (
          <rect
            key={p[0]}
            x={-half * P}
            y={-half * P}
            width={2 * half * P}
            height={2 * half * P}
            rx={14}
            fill="none"
            stroke={color.blue}
            strokeOpacity={interpolate(t - p[0], [0.4, 6], [0.45, 0], clamp)}
            strokeWidth={2}
            transform={`translate(${X(p[1])},${Y(p[2])}) rotate(${deg(p[3])})`}
          />
        ))}
        <path d={pathD(planPts)} fill="none" stroke={color.orange} strokeWidth={5} strokeDasharray="14 10" strokeDashoffset={-frame * 2} style={{ filter: `drop-shadow(0 0 8px ${color.orange})` }} opacity={interpolate(s, [PLAN_START, PLAN_START + 0.2], [0, 1], clamp)} />
        {t > 0 && <path d={pathD(driven)} fill="none" stroke={color.lime} strokeWidth={8} strokeLinecap="round" style={{ filter: `drop-shadow(0 0 10px ${color.lime})` }} />}
        {scans.map((sc, i) => {
          const age = Math.max(t, 0) - sc.t;
          const o = (i === scans.length - 1 ? 1 : 0.35) * interpolate(age, [0, 0.6], [1, 0.6], clamp) * interpolate(s, [0.6, 1.4], [0, 1], clamp);
          return (
            <g key={sc.t} opacity={o} style={{ filter: `drop-shadow(0 0 4px ${color.cyan})` }}>
              {sc.pts.map(([pu, pv], j) => (
                <circle key={j} cx={X(pu)} cy={Y(pv)} r={3.2} fill={i === scans.length - 1 ? "#ffffff" : color.cyan} />
              ))}
            </g>
          );
        })}
        <g opacity={robotIn}>
          <LidarFan u={u} v={v} yaw={yaw} frame={frame} />
        </g>
        <Sonar u={run.bottle[0]} v={run.bottle[1]} frame={frame} tint={arrived ? color.lime : color.orange} />
        <g opacity={robotIn} transform={`translate(${X(u)},${Y(v)}) scale(${interpolate(robotIn, [0, 1], [1.6, 1])}) translate(${-X(u)},${-Y(v)})`}>
          <Robot u={u} v={v} yaw={yaw} glow={8 + 6 * Math.sin(frame / 4)} />
        </g>
        {arrived && (
          <g opacity={interpolate(s, [driveEnd, driveEnd + 0.5], [0, 1], clamp)}>
            <line x1={X(final[1]) + 70} x2={X(final[1]) + 70} y1={Y(nose)} y2={Y(run.bottle[1])} stroke="#fff" strokeWidth={3} />
            <line x1={X(final[1]) + 56} x2={X(final[1]) + 84} y1={Y(nose)} y2={Y(nose)} stroke="#fff" strokeWidth={3} />
            <line x1={X(final[1]) + 56} x2={X(final[1]) + 84} y1={Y(run.bottle[1])} y2={Y(run.bottle[1])} stroke="#fff" strokeWidth={3} />
            <text x={X(final[1]) + 96} y={(Y(nose) + Y(run.bottle[1])) / 2 + 9} fill="#fff" fontFamily={mono} fontSize={26} fontWeight={700}>
              {run.stats.finalGap.toFixed(2)} m
            </text>
          </g>
        )}
      </svg>
      <div
        style={{
          position: "absolute",
          left: X(run.bottle[0]) + 90,
          top: Y(run.bottle[1]) - 34,
          width: 330,
          fontFamily: mono,
          fontSize: 22,
          color: arrived ? color.lime : color.orange,
          letterSpacing: 2,
          opacity: interpolate(s, [1.6, 2.2, driveEnd - 0.4, driveEnd], [0, 1, 1, 0], clamp),
        }}
      >
        DOOR
        <div style={{ color: color.muted, fontSize: 16 }}>bottle stand-in</div>
      </div>
    </div>
  );
};

const Card = ({ label, children, tint = color.cyan, style }) => (
  <div style={{ position: "relative", background: color.panel, border: `1px solid ${color.line}`, padding: "20px 26px", ...style }}>
    <Brackets size={14} thickness={2} tint={tint} inset={-1} />
    <div style={{ fontFamily: mono, fontSize: 18, letterSpacing: 4, color: color.muted, textTransform: "uppercase" }}>{label}</div>
    {children}
  </div>
);

const SpeedChart = ({ t }) => {
  const w = 500;
  const h = 130;
  const x = (tt) => (tt / run.duration) * w;
  const y = (sp) => h - (sp / 0.2) * h;
  const pts = run.speed.filter(([tt]) => tt <= t);
  const d = pts.map(([tt, sp], i) => `${i ? "L" : "M"}${x(tt).toFixed(1)},${y(sp).toFixed(1)}`).join(" ");
  return (
    <svg width={w} height={h + 4} style={{ overflow: "visible", marginTop: 10 }}>
      <line x1={0} x2={w} y1={y(0.15)} y2={y(0.15)} stroke={color.orange} strokeDasharray="6 6" strokeWidth={2} />
      <text x={w} y={y(0.15) - 8} textAnchor="end" fill={color.orange} fontFamily={mono} fontSize={16}>NAV2 LIMIT 0.15</text>
      <line x1={0} x2={w} y1={h} y2={h} stroke={color.line} strokeWidth={2} />
      {pts.length > 1 && (
        <>
          <path d={`${d} L${x(pts[pts.length - 1][0])},${h} L0,${h} Z`} fill={`${color.cyan}22`} />
          <path d={d} fill="none" stroke={color.cyan} strokeWidth={3} />
          <circle cx={x(pts[pts.length - 1][0])} cy={y(pts[pts.length - 1][1])} r={6} fill="#fff" />
        </>
      )}
    </svg>
  );
};

const Hud = () => {
  const { frame, t, s } = useRunClock();
  const speed = sample(run.speed, t);
  const gap = sample(run.gap, t);
  const driveEnd = DRIVE_START + run.duration;
  const arrived = t >= run.duration - 0.05;
  const status = s < DRIVE_START ? (s < PLAN_START ? "LOCALISING" : "PLANNING") : arrived ? "GOAL REACHED" : "FOLLOWING PATH";
  const statusTint = arrived ? color.lime : s < DRIVE_START ? color.amber : color.cyan;
  const panelIn = interpolate(s, [0.4, 1.2], [0, 1], { ...clamp, easing: outExpo });
  const blink = Math.floor(frame / 8) % 2 === 0;

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 80, top: 64, opacity: panelIn }}>
        <Tag tint={color.red} style={{ fontSize: 20 }}>
          <span style={{ opacity: blink ? 1 : 0.25 }}>●</span> Replay · recorded on the real robot · 1× speed
        </Tag>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 64, color: color.text, marginTop: 8 }}>
          Nav2 → the door
        </div>
      </div>
      <div style={{ position: "absolute", left: 80, bottom: 120, display: "flex", gap: 36, fontFamily: mono, fontSize: 20, color: color.muted, opacity: panelIn }}>
        <span><span style={{ color: color.orange }}>━ ━</span> Nav2 plan</span>
        <span><span style={{ color: color.lime }}>━━</span> driven path</span>
        <span><span style={{ color: "#fff" }}>•</span> laser returns</span>
        <span><span style={{ color: color.cyan }}>■</span> SLAM walls</span>
      </div>
      <div
        style={{
          position: "absolute",
          right: 80,
          top: 64,
          width: 560,
          display: "flex",
          flexDirection: "column",
          gap: 22,
          opacity: panelIn,
          translate: `${(1 - panelIn) * 80}px 0px`,
        }}
      >
        <Card label="Mission clock">
          <div style={{ fontFamily: mono, fontSize: 64, fontWeight: 700, color: color.text, fontVariantNumeric: "tabular-nums" }}>
            T+{t.toFixed(2).padStart(5, "0")}<span style={{ fontSize: 30, color: color.muted }}> s</span>
          </div>
        </Card>
        <Card label="Status" tint={statusTint}>
          <div style={{ fontFamily: display, fontSize: 52, fontWeight: 700, color: statusTint, letterSpacing: 1, textShadow: `0 0 24px ${statusTint}88` }}>{status}</div>
        </Card>
        <div style={{ display: "flex", gap: 22 }}>
          <Card label="Speed" style={{ flex: 1 }}>
            <div style={{ fontFamily: mono, fontSize: 54, fontWeight: 700, color: color.cyan, fontVariantNumeric: "tabular-nums" }}>
              {speed.toFixed(3)}
            </div>
            <div style={{ fontFamily: mono, fontSize: 20, color: color.muted }}>m/s</div>
          </Card>
          <Card label="To the door" tint={arrived ? color.lime : color.orange} style={{ flex: 1 }}>
            <div style={{ fontFamily: mono, fontSize: 54, fontWeight: 700, color: arrived ? color.lime : color.orange, fontVariantNumeric: "tabular-nums" }}>
              {gap.toFixed(2)}
            </div>
            <div style={{ fontFamily: mono, fontSize: 20, color: color.muted }}>m, bumper to bottle</div>
          </Card>
        </div>
        <Card label="Forward speed, live">
          <SpeedChart t={t} />
        </Card>
      </div>
      {arrived && (
        <div
          style={{
            position: "absolute",
            left: -100,
            top: 800,
            width: 2200,
            height: 150,
            background: color.lime,
            boxShadow: `0 0 80px ${color.lime}88`,
            display: "flex",
            alignItems: "center",
            gap: 60,
            whiteSpace: "nowrap",
            rotate: "-4deg",
            translate: interpolate(s, [driveEnd + 0.1, driveEnd + 0.5], ["-2300px 0px", "0px 0px"], { ...clamp, easing: outExpo }),
          }}
        >
          {[0, 1, 2].map((k) => (
            <span
              key={k}
              style={{
                fontFamily: display,
                fontWeight: 700,
                fontSize: 104,
                letterSpacing: -2,
                color: color.bg,
                translate: `${interpolate(s, [driveEnd, driveEnd + 3], [0, -160])}px 0px`,
              }}
            >
              GOAL REACHED ◆
            </span>
          ))}
        </div>
      )}
    </AbsoluteFill>
  );
};

export const RunScene = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: color.bg, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          backgroundImage: `radial-gradient(${color.cyan}22 1.5px, transparent 1.5px)`,
          backgroundSize: "40px 40px",
        }}
      />
      <World />
      <Hud />
      <Flash at={Math.round((DRIVE_START + run.duration + 0.1) * fps)} length={12} tint={color.lime} peak={0.35} />
      <Overlay />
    </AbsoluteFill>
  );
};
