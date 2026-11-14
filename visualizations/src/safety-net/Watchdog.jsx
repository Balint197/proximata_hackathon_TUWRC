import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Backdrop, Flash, Overlay, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";
import { watchdog } from "./outcomes";

const MS_MAX = 800;
const X0 = 160;
const X1 = 1760;
const AXIS_Y = 640;
const x = (ms) => X0 + (ms / MS_MAX) * (X1 - X0);

const EVENTS = [
  { ms: 0, label: "Drive gate killed", note: "on purpose, robot on a stand", tint: color.red, up: true },
  { ms: watchdog.tripAfterKill * 1000, label: "Watchdog trips", note: "commands zeroed", tint: color.amber, up: false },
  { ms: watchdog.disableAfterKill * 1000, label: "Motors disabled", note: "by the independent watchdog", tint: color.lime, up: true },
  { ms: watchdog.powerOffReceipt * 1000, label: "Power OFF confirmed", note: "relay state received", tint: color.cyan, up: false, alignEnd: true },
];

export const Watchdog = () => {
  const frame = useCurrentFrame();
  // The cursor runs the 800 ms window over 3 s of video.
  const ms = interpolate(frame, [24, 114], [0, MS_MAX], clamp);
  return (
    <AbsoluteFill>
      <Backdrop tint={color.red} />
      <div style={{ position: "absolute", left: X0, top: 100 }}>
        <Tag tint={color.red}>Fault injection · 14 Nov 04:48</Tag>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 84, color: color.text, marginTop: 8 }}>
          What if the software dies mid-drive?
        </div>
      </div>
      <div style={{ position: "absolute", right: 160, top: 330, textAlign: "right" }}>
        <div style={{ fontFamily: mono, fontSize: 120, fontWeight: 700, color: ms >= EVENTS[1].ms ? color.amber : color.text, fontVariantNumeric: "tabular-nums", lineHeight: 1 }}>
          {Math.round(ms).toString().padStart(3, "0")}
          <span style={{ fontSize: 50, color: color.muted }}> ms</span>
        </div>
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <line x1={X0} x2={X1} y1={AXIS_Y} y2={AXIS_Y} stroke={color.line} strokeWidth={4} />
        <line x1={X0} x2={x(ms)} y1={AXIS_Y} y2={AXIS_Y} stroke={color.red} strokeWidth={6} style={{ filter: `drop-shadow(0 0 10px ${color.red})` }} />
        {[0, 200, 400, 600, 800].map((t) => (
          <text key={t} x={x(t)} y={AXIS_Y + 210} textAnchor="middle" fill={color.muted} fontFamily={mono} fontSize={20}>{t} ms</text>
        ))}
        <circle cx={x(ms)} cy={AXIS_Y} r={12} fill="#fff" style={{ filter: "drop-shadow(0 0 12px #fff)" }} />
      </svg>
      {EVENTS.map((e) => {
        const reached = ms >= e.ms;
        const k = interpolate(ms - e.ms, [0, 60], [0, 1], { ...clamp, easing: outExpo });
        return (
          <div key={e.label} style={{ position: "absolute", left: x(e.ms) - 4, top: e.up ? AXIS_Y - 190 : AXIS_Y + 30, opacity: reached ? 1 : 0 }}>
            <div style={{ position: "absolute", left: 0, top: e.up ? 0 : -30, width: 4, height: 160, background: e.tint, boxShadow: `0 0 12px ${e.tint}` }} />
            <div style={{ position: e.alignEnd ? "absolute" : "relative", right: e.alignEnd ? 22 : undefined, textAlign: e.alignEnd ? "right" : "left", marginLeft: e.alignEnd ? 0 : 22, translate: `0px ${(1 - k) * (e.up ? 20 : -20)}px`, whiteSpace: "nowrap" }}>
              <div style={{ fontFamily: mono, fontSize: 26, fontWeight: 700, color: e.tint }}>{Math.round(e.ms)} ms</div>
              <div style={{ fontFamily: display, fontSize: 36, fontWeight: 700, color: color.text }}>{e.label}</div>
              <div style={{ fontFamily: mono, fontSize: 19, color: color.muted }}>{e.note}</div>
            </div>
          </div>
        );
      })}
      <div style={{ position: "absolute", left: X0, bottom: 130, fontFamily: mono, fontSize: 19, color: color.muted, opacity: interpolate(frame, [110, 124], [0, 1], clamp) }}>
        Software receipt times from the stand test, not physical stopping distance. The red button stays the primary stop.
      </div>
      <Flash at={Math.round(24 + (EVENTS[1].ms / MS_MAX) * 90)} length={8} tint={color.amber} peak={0.25} />
      <Overlay />
    </AbsoluteFill>
  );
};
