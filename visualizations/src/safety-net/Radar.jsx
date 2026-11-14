import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Backdrop, Overlay, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";
import { GUARD_REASONS, guardTrips } from "./outcomes";

// Guard geometry from scripts/session_checks.py (base_link, metres).
const HALF = 0.29;
const STOP_AHEAD = 0.33;
const SIDE_GAP = 0.06;
const STOP_RADIUS = 0.46;
const LASER_X = 0.197;
const SELF_BOX = [HALF, 0.345, -0.29, -0.16];
const BRACKET_SESSIONS = ["20261114T084805", "20261114T084949", "20261114T085812"];

const S = 600;
const C = [640, 600];
// base_link (x forward, y left) -> screen (forward up).
const sx = (y) => C[0] - y * S;
const sy = (x) => C[1] - x * S;

const TRIP_START = 30;
const TRIP_GAP = 7;
const BRACKET_AT = TRIP_START + guardTrips.length * TRIP_GAP + 20;

const Zone = ({ x0, x1, y0, y1, tint, at, label, labelSide = "right" }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [at, at + 12], [0, 1], clamp);
  return (
    <g opacity={o}>
      <rect x={sx(y1)} y={sy(x1)} width={(y1 - y0) * S} height={(x1 - x0) * S} fill={`${tint}14`} stroke={tint} strokeWidth={2} strokeDasharray="8 6" />
      {label && (
        <text x={labelSide === "right" ? sx(y0) + 12 : sx(y1) - 12} y={sy(x1) + 26} textAnchor={labelSide === "right" ? "start" : "end"} fill={tint} fontFamily={mono} fontSize={18}>
          {label}
        </text>
      )}
    </g>
  );
};

export const Radar = () => {
  const frame = useCurrentFrame();
  const fan = (115 * Math.PI) / 180;
  const R = 1.4 * S;
  const sweep = -115 + ((frame * 6) % 230);
  const lx = sx(0);
  const ly = sy(LASER_X);
  const shown = guardTrips.filter((_, i) => frame >= TRIP_START + i * TRIP_GAP);
  const bracket = interpolate(frame, [BRACKET_AT, BRACKET_AT + 14], [0, 1], { ...clamp, easing: outExpo });
  const tally = Object.fromEntries(Object.keys(GUARD_REASONS).map((k) => [k, shown.filter((s) => s.guard.reason === k).length]));

  return (
    <AbsoluteFill>
      <Backdrop tint={color.amber} />
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <defs>
          <radialGradient id="radarFan" cx={lx} cy={ly} r={R} gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor={color.cyan} stopOpacity="0.16" />
            <stop offset="1" stopColor={color.cyan} stopOpacity="0" />
          </radialGradient>
          <pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="10" stroke={color.cyan} strokeWidth="4" />
          </pattern>
        </defs>
        {[0.25, 0.5, 0.75, 1].map((r) => (
          <g key={r} opacity={interpolate(frame, [0, 14], [0, 1], clamp)}>
            <circle cx={C[0]} cy={C[1]} r={r * S} fill="none" stroke={color.line} strokeWidth={1.5} />
            <text x={C[0] - r * S * 0.71 - 8} y={C[1] - r * S * 0.71 - 8} textAnchor="end" fill={color.muted} fontFamily={mono} fontSize={16}>{r.toFixed(2)} m</text>
          </g>
        ))}
        <path
          d={`M${lx},${ly} L${lx - Math.sin(fan) * R},${ly - Math.cos(fan) * R} A${R},${R} 0 1 1 ${lx + Math.sin(fan) * R},${ly - Math.cos(fan) * R} Z`}
          fill="url(#radarFan)"
        />
        <g transform={`translate(${lx},${ly}) rotate(${sweep})`}>
          <line x1={0} y1={0} x2={0} y2={-R} stroke={color.cyan} strokeOpacity={0.45} strokeWidth={2} />
        </g>
        <g opacity={interpolate(frame, [8, 20], [0, 1], clamp)}>
          <circle cx={C[0]} cy={C[1]} r={STOP_RADIUS * S} fill={`${color.red}0c`} stroke={color.red} strokeWidth={2} strokeDasharray="8 6" />
          <text x={sx(-STOP_RADIUS * 0.72) + 10} y={sy(-STOP_RADIUS * 0.72) + 24} fill={color.red} fontFamily={mono} fontSize={18}>turning circle · r 0.46 m</text>
        </g>
        <Zone x0={HALF} x1={HALF + STOP_AHEAD} y0={-(HALF + 0.04)} y1={HALF + 0.04} tint={color.amber} at={14} label="forward corridor · 0.33 m" />
        <Zone x0={-HALF} x1={HALF} y0={HALF} y1={HALF + SIDE_GAP} tint={color.orange} at={20} />
        <Zone x0={-HALF} x1={HALF} y0={-(HALF + SIDE_GAP)} y1={-HALF} tint={color.orange} at={20} />
        <g>
          <rect x={sx(HALF)} y={sy(HALF)} width={2 * HALF * S} height={2 * HALF * S} rx={16} fill={`${color.cyan}18`} stroke={color.cyan} strokeWidth={4} style={{ filter: `drop-shadow(0 0 10px ${color.cyan})` }} />
          <path d={`M${C[0] - 26},${sy(HALF) + 8} L${C[0]},${sy(HALF) - 22} L${C[0] + 26},${sy(HALF) + 8} Z`} fill={color.cyan} />
          <circle cx={lx} cy={ly} r={8} fill="#fff" />
          <text x={C[0]} y={C[1] + 12} textAnchor="middle" fill={color.cyan} fontFamily={display} fontWeight={700} fontSize={34}>D1</text>
        </g>
        <g opacity={bracket}>
          <rect x={sx(SELF_BOX[3])} y={sy(SELF_BOX[1])} width={(SELF_BOX[3] - SELF_BOX[2]) * S} height={(SELF_BOX[1] - SELF_BOX[0]) * S} fill="url(#hatch)" opacity={0.7} />
          <rect x={sx(SELF_BOX[3])} y={sy(SELF_BOX[1])} width={(SELF_BOX[3] - SELF_BOX[2]) * S} height={(SELF_BOX[1] - SELF_BOX[0]) * S} fill="none" stroke={color.cyan} strokeWidth={3} />
        </g>
        {shown.map((s, i) => {
          const at = TRIP_START + i * TRIP_GAP;
          const age = frame - at;
          const tint = GUARD_REASONS[s.guard.reason].tint;
          const isBracket = BRACKET_SESSIONS.some((id) => s.id.startsWith(id));
          const dim = bracket > 0 && !isBracket ? 1 - 0.6 * bracket : 1;
          return (
            <g key={s.id} opacity={dim}>
              {s.guard.closest.map(([x, y], j) => (
                <g key={j}>
                  <circle cx={sx(y)} cy={sy(x)} r={interpolate(age, [0, 16], [4, 50], clamp)} fill="none" stroke={tint} strokeWidth={3} opacity={interpolate(age, [0, 16], [1, 0], clamp)} />
                  <circle cx={sx(y)} cy={sy(x)} r={interpolate(age, [0, 6], [16, 8], clamp)} fill={isBracket && bracket > 0 ? color.cyan : tint} style={{ filter: `drop-shadow(0 0 8px ${tint})` }} />
                </g>
              ))}
            </g>
          );
        })}
      </svg>
      <div style={{ position: "absolute", left: 1220, top: 110, width: 620 }}>
        <Tag tint={color.amber}>Laser guard · SICK TiM571 · 15 Hz</Tag>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 76, lineHeight: 1.02, color: color.text, marginTop: 10 }}>
          {shown.length} times it saw something and <span style={{ color: color.amber }}>stopped</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14, marginTop: 40 }}>
          {Object.entries(GUARD_REASONS).map(([k, r]) => (
            <div key={k} style={{ display: "flex", alignItems: "center", gap: 18, fontFamily: mono, fontSize: 26, color: color.text }}>
              <span style={{ width: 18, height: 18, borderRadius: 9, background: r.tint, boxShadow: `0 0 10px ${r.tint}` }} />
              <span style={{ width: 60, fontWeight: 700, color: r.tint, fontVariantNumeric: "tabular-nums" }}>{tally[k]}</span>
              obstacle {r.label}
            </div>
          ))}
        </div>
        <div
          style={{
            marginTop: 50,
            padding: "22px 26px",
            borderLeft: `6px solid ${color.cyan}`,
            background: color.panel,
            opacity: bracket,
            translate: `${(1 - bracket) * 60}px 0px`,
          }}
        >
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 36, color: color.cyan }}>Plot twist: 3 of them were the D1 itself</div>
          <div style={{ fontFamily: mono, fontSize: 21, color: color.muted, marginTop: 8, lineHeight: 1.4 }}>
            A bracket at the front-right corner pokes into the laser&apos;s view. We mapped it and masked a 5.5 × 13 cm patch as body.
          </div>
        </div>
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};
