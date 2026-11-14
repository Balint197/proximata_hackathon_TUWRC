import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Backdrop, Overlay, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";
import { counts, OUTCOMES, sessions } from "./outcomes";

const STAGGER = 4;
const MINI = 112;

// The session's odometry track in its own start frame, forward = up.
const MiniTrack = ({ session, progress, tint }) => {
  const extent = Math.max(0.6, ...session.track.map(([x, y]) => Math.max(Math.abs(x), Math.abs(y)) * 2.2));
  const k = MINI / 2 / extent;
  const pts = session.track.slice(0, Math.max(1, Math.ceil(session.track.length * progress)));
  const d = pts.map(([x, y], i) => `${i ? "L" : "M"}${(MINI / 2 - y * k).toFixed(1)},${(MINI / 2 - x * k).toFixed(1)}`).join(" ");
  const [ex, ey] = pts[pts.length - 1];
  const b = 0.29 * k;
  const turn = session.turn * progress * (180 / Math.PI);
  return (
    <svg width={MINI} height={MINI} style={{ flexShrink: 0, background: "rgba(255,255,255,0.03)" }}>
      <rect x={MINI / 2 - b} y={MINI / 2 - b} width={2 * b} height={2 * b} fill="none" stroke={color.line} strokeDasharray="3 3" />
      <path d={d} fill="none" stroke={tint} strokeWidth={3} strokeLinecap="round" />
      <g transform={`translate(${MINI / 2 - ey * k},${MINI / 2 - ex * k}) rotate(${-turn})`}>
        <rect x={-b} y={-b} width={2 * b} height={2 * b} rx={3} fill={`${tint}22`} stroke={tint} strokeWidth={2} />
        <path d={`M${-b * 0.5},${-b} L0,${-b * 1.6} L${b * 0.5},${-b} Z`} fill={tint} />
      </g>
    </svg>
  );
};

const Card = ({ session, index }) => {
  const frame = useCurrentFrame();
  const at = 14 + index * STAGGER;
  const o = OUTCOMES[session.outcome];
  const progress = interpolate(frame, [at + 4, at + 30], [0, 1], { ...clamp, easing: outExpo });
  const offAt = at + 26;
  return (
    <div
      style={{
        display: "flex",
        gap: 16,
        padding: 12,
        background: color.panel,
        borderTop: `4px solid ${o.tint}`,
        opacity: interpolate(frame, [at, at + 5], [0, 1], clamp),
        scale: interpolate(frame, [at, at + 12], [0.7, 1], { ...clamp, easing: outExpo }),
        boxShadow: frame < at + 10 ? `0 0 40px ${o.tint}66` : "none",
      }}
    >
      <MiniTrack session={session} progress={progress} tint={o.tint} />
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", minWidth: 0, flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: mono, fontSize: 18, color: color.muted }}>
          <span>{session.clock}</span>
          <span style={{ color: color.lime, opacity: frame >= offAt ? 1 : 0 }}>⏻ OFF</span>
        </div>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 22, color: o.tint, textTransform: "uppercase", letterSpacing: 1 }}>{o.label}</div>
        <div style={{ fontFamily: mono, fontSize: 16, color: color.text, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{session.label}</div>
        <div style={{ fontFamily: mono, fontSize: 18, color: color.muted }}>
          {session.distance.toFixed(2)} m · {session.duration.toFixed(0)} s
        </div>
      </div>
    </div>
  );
};

export const MissionLog = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Backdrop tint={color.amber} />
      <AbsoluteFill style={{ padding: "70px 110px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <div>
            <Tag tint={color.amber}>Mission log · 14 Nov · 07:04 → 08:59</Tag>
            <div style={{ fontFamily: display, fontWeight: 700, fontSize: 72, color: color.text, marginTop: 6 }}>Every drive, supervised</div>
          </div>
          <div style={{ display: "flex", gap: 30 }}>
            {Object.entries(OUTCOMES).map(([k, o], i) => (
              <div key={k} style={{ textAlign: "right", opacity: interpolate(frame, [130 + i * 6, 140 + i * 6], [0, 1], clamp) }}>
                <div style={{ fontFamily: display, fontWeight: 700, fontSize: 64, color: o.tint, lineHeight: 1 }}>{counts[k]}</div>
                <div style={{ fontFamily: mono, fontSize: 16, color: color.muted, textTransform: "uppercase", letterSpacing: 2 }}>{o.label}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 14, marginTop: 30 }}>
          {sessions.map((s, i) => (
            <Card key={s.id} session={s} index={i} />
          ))}
        </div>
      </AbsoluteFill>
      <Overlay />
    </AbsoluteFill>
  );
};
