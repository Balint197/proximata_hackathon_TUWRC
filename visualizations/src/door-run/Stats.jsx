import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import run from "../data/door-run.json";
import { Backdrop, Brackets, CountUp, Overlay, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";

const Big = ({ at, value, decimals, suffix, label, tint = color.text }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        opacity: interpolate(frame, [at, at + 6], [0, 1], clamp),
        translate: interpolate(frame, [at, at + 16], ["-60px 0px", "0px 0px"], { ...clamp, easing: outExpo }),
      }}
    >
      <div style={{ fontFamily: display, fontWeight: 700, fontSize: 132, lineHeight: 1, color: tint, letterSpacing: -3, textShadow: `0 0 36px ${tint}55` }}>
        <CountUp value={value} start={at} duration={26} decimals={decimals} />
        <span style={{ fontSize: 60, color: color.muted }}>{suffix}</span>
      </div>
      <div style={{ fontFamily: mono, fontSize: 24, letterSpacing: 3, color: color.muted, textTransform: "uppercase", marginTop: 6 }}>{label}</div>
    </div>
  );
};

const GapChart = ({ at }) => {
  const frame = useCurrentFrame();
  const w = 940;
  const h = 520;
  const x = (t) => (t / run.duration) * w;
  const y = (g) => h - (g / 1.4) * h;
  const reveal = interpolate(frame, [at, at + 50], [0, run.duration], { ...clamp, easing: outExpo });
  const pts = run.gap.filter(([t]) => t <= reveal);
  const d = pts.map(([t, g], i) => `${i ? "L" : "M"}${x(t).toFixed(1)},${y(g).toFixed(1)}`).join(" ");
  return (
    <svg width={w} height={h} style={{ overflow: "visible" }}>
      {[0, 0.25, 0.5, 0.75, 1, 1.25].map((g) => (
        <g key={g}>
          <line x1={0} x2={w} y1={y(g)} y2={y(g)} stroke={color.line} strokeWidth={1.5} />
          <text x={-16} y={y(g) + 7} textAnchor="end" fill={color.muted} fontFamily={mono} fontSize={20}>{g.toFixed(2)}</text>
        </g>
      ))}
      <line x1={0} x2={w} y1={y(run.stats.target)} y2={y(run.stats.target)} stroke={color.orange} strokeWidth={2.5} strokeDasharray="10 8" />
      <text x={w} y={y(run.stats.target) + 32} textAnchor="end" fill={color.orange} fontFamily={mono} fontSize={20}>NAV2 GOAL: 0.10 m SHORT</text>
      {pts.length > 1 && (
        <>
          <path d={`${d} L${x(pts[pts.length - 1][0])},${h} L0,${h} Z`} fill={`${color.cyan}18`} />
          <path d={d} fill="none" stroke={color.cyan} strokeWidth={5} style={{ filter: `drop-shadow(0 0 8px ${color.cyan})` }} />
        </>
      )}
      {run.laserHits.filter(([t]) => t <= reveal).map(([t, g]) => (
        <circle key={t} cx={x(t)} cy={y(g)} r={7} fill="#fff" />
      ))}
      {[0, 2, 4, 6, 8, 10, 12].map((t) => (
        <text key={t} x={x(t)} y={h + 34} textAnchor="middle" fill={color.muted} fontFamily={mono} fontSize={20}>{t}s</text>
      ))}
    </svg>
  );
};

export const Stats = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{ padding: "110px 130px", flexDirection: "row", gap: 110 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 34, width: 600 }}>
          <Tag>Debrief · session 085925</Tag>
          <Big at={6} value={run.stats.distance} decimals={2} suffix=" m" label="driven, wheel odometry" />
          <Big at={14} value={run.stats.driveSeconds} decimals={0} suffix=" s" label="of autonomous driving" />
          <Big at={22} value={run.stats.finalGap} decimals={2} suffix=" m" label="short of the door at the stop" tint={color.lime} />
        </div>
        <div style={{ position: "relative", flex: 1, background: color.panel, border: `1px solid ${color.line}`, padding: "48px 56px 70px 90px", opacity: interpolate(frame, [10, 22], [0, 1], clamp) }}>
          <Brackets size={22} thickness={3} inset={-1} />
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 44, color: color.text }}>Closing in on the door</div>
          <div style={{ fontFamily: mono, fontSize: 21, color: color.muted, margin: "8px 0 34px" }}>
            gap, front bumper to bottle (m) · <span style={{ color: "#fff" }}>●</span> laser hits on the bottle
          </div>
          <GapChart at={20} />
        </div>
      </AbsoluteFill>
      <Overlay />
    </AbsoluteFill>
  );
};
