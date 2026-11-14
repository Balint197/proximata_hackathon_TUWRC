import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop, Overlay, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";
import { Appear, cue } from "./kit";

const LIVE = [
  ["/robot/scan", "laser"],
  ["/robot/odom", "odometry"],
  ["/robot/imu/data", "IMU"],
  ["/camera_back/rgb", "rear camera"],
  ["/camera_back/depth", "rear depth"],
  ["/disinfection/pm10", "air"],
  ["/disinfection/pm25", "air"],
  ["/disinfection/pm100", "air"],
  ["/disinfection/o3", "air"],
  ["/disinfection/co2", "air"],
  ["/disinfection/tvoc", "air"],
  ["/disinfection/temperature", "air"],
  ["/disinfection/humidity", "air"],
];
const DEAD = ["/camera_up", "/camera_down"];

export const Sensors = ({ line }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bridge = cue(line, "one-way bridge", fps);
  const laser = cue(line, "Laser", fps);
  const check = cue(line, "thirteen", fps);
  const dead = cue(line, "Two depth", fps);
  const rowH = 44;
  const top = 250;
  const delivered = LIVE.filter((_, i) => frame >= check + i * 2).length;
  return (
    <AbsoluteFill>
      <Backdrop />
      <div style={{ position: "absolute", left: 110, top: 70 }}>
        <Appear at={0}>
          <Tag>Level 2 · unlock every sensor</Tag>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 72, color: color.text, marginTop: 6 }}>ROS 1 in, ROS 2 out</div>
        </Appear>
      </div>
      <div style={{ position: "absolute", left: 110, top: top - 50, fontFamily: mono, fontSize: 22, color: color.orange, letterSpacing: 3 }}>VENDOR · ROS 1 MELODIC</div>
      <div style={{ position: "absolute", left: 1150, top: top - 50, fontFamily: mono, fontSize: 22, color: color.lime, letterSpacing: 3, opacity: interpolate(frame, [bridge, bridge + 8], [0, 1], clamp) }}>OURS · ROS 2 HUMBLE (ROOTLESS)</div>
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <rect x={700} y={top - 10} width={300} height={(LIVE.length + DEAD.length) * rowH} rx={12} fill={`${color.cyan}10`} stroke={color.cyan} strokeWidth={2} opacity={interpolate(frame, [bridge, bridge + 8], [0, 1], clamp)} />
        {LIVE.map((_, i) => {
          const y = top + i * rowH + 14;
          const at = laser + i * 3;
          const k = interpolate(frame, [at, at + 12], [0, 1], { ...clamp, easing: outExpo });
          const px = 560 + ((frame * 9 + i * 37) % 600);
          return (
            <g key={i} opacity={k}>
              <line x1={560} x2={560 + 590 * k} y1={y} y2={y} stroke={color.cyan} strokeOpacity={0.4} strokeWidth={2} />
              {k >= 1 && <circle cx={px} cy={y} r={5} fill="#fff" style={{ filter: `drop-shadow(0 0 6px ${color.cyan})` }} />}
            </g>
          );
        })}
      </svg>
      <div style={{ position: "absolute", left: 850, top: top + 200, translate: "-50% 0", textAlign: "center", fontFamily: display, fontWeight: 700, fontSize: 30, color: color.cyan, opacity: interpolate(frame, [bridge, bridge + 8], [0, 1], clamp), width: 280 }}>
        one-way bridge
        <div style={{ fontFamily: mono, fontWeight: 400, fontSize: 18, color: color.muted, marginTop: 6 }}>allowlist · no commands</div>
        <div style={{ fontSize: 60, marginTop: 10 }}>→</div>
      </div>
      {[...LIVE.map(([t]) => t), ...DEAD].map((t, i) => {
        const isDead = i >= LIVE.length;
        const ok = !isDead && frame >= check + i * 2;
        const deadShown = isDead && frame >= dead;
        return (
          <div key={t}>
            <div style={{ position: "absolute", left: 110, top: top + i * rowH, fontFamily: mono, fontSize: 24, color: isDead ? color.muted : color.text, opacity: interpolate(frame, [4 + i, 10 + i], [0, 1], clamp) }}>{t}</div>
            {!isDead && (
              <div style={{ position: "absolute", left: 1150, top: top + i * rowH, fontFamily: mono, fontSize: 24, color: ok ? color.lime : color.text, opacity: interpolate(frame, [laser + i * 3 + 8, laser + i * 3 + 14], [0, 1], clamp) }}>
                {ok ? "✓ " : "  "}
                {t}
              </div>
            )}
            {deadShown && <div style={{ position: "absolute", left: 1150, top: top + i * rowH, fontFamily: mono, fontSize: 24, color: color.red }}>✗ registered, 0 frames</div>}
          </div>
        );
      })}
      <div style={{ position: "absolute", right: 110, top: 300, textAlign: "right", opacity: interpolate(frame, [check, check + 6], [0, 1], clamp) }}>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 180, color: color.lime, lineHeight: 1, textShadow: `0 0 40px ${color.lime}66` }}>{delivered}</div>
        <div style={{ fontFamily: mono, fontSize: 22, color: color.muted, letterSpacing: 2 }}>TOPICS PASSED A<br />LIVE DELIVERY CHECK</div>
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};

// Illustration of the drive-gate policy (not recorded data): clamp at 0.20 m/s, zero 250 ms after the last command.
const CW = 1100;
const CH = 300;
const T_MAX = 4;
const V_MAX = 0.32;
const cx = (t) => (t / T_MAX) * CW;
const cy = (v) => CH - (v / V_MAX) * CH;
const input = (t) => (t < 0.6 ? 0 : t < 1.4 ? ((t - 0.6) / 0.8) * 0.3 : 0.3);
const LAST_CMD = 2.6;
const output = (t, armed) => (!armed || t < 0.6 ? 0 : t <= LAST_CMD + 0.25 ? Math.min(0.2, input(Math.min(t, LAST_CMD))) : 0);

export const DriveGate = ({ line }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const disarmed = cue(line, "starts disarmed", fps);
  const clampAt = cue(line, "clamps", fps);
  const zero = cue(line, "drops to zero", fps);
  const dog = cue(line, "independent watchdog", fps);
  const t = interpolate(frame, [disarmed, zero + 40], [0, T_MAX], clamp);
  const armed = frame >= disarmed + 12;
  const series = (f, end) => {
    const pts = [];
    for (let s = 0; s <= end; s += 0.02) pts.push(`${pts.length ? "L" : "M"}${cx(s).toFixed(1)},${cy(f(s)).toFixed(1)}`);
    return pts.join(" ");
  };
  return (
    <AbsoluteFill>
      <Backdrop tint={color.orange} />
      <div style={{ position: "absolute", left: 110, top: 70 }}>
        <Appear at={0}>
          <Tag tint={color.orange}>Level 3 · take the wheel</Tag>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 72, color: color.text, marginTop: 6 }}>One door for every command</div>
        </Appear>
      </div>
      <div style={{ position: "absolute", left: 110, top: 250, display: "flex", alignItems: "center", gap: 26 }}>
        {[
          { name: "ROS 2 /cmd_vel", sub: "Nav2 · our scripts", tint: color.cyan },
          { name: "DRIVE GATE", sub: armed ? "ARMED" : "DISARMED", tint: armed ? color.lime : color.red, big: true },
          { name: "Vendor motor driver", sub: "ROS 1 · CAN", tint: color.muted },
        ].map((b, i) => (
          <div key={b.name} style={{ display: "flex", alignItems: "center", gap: 26 }}>
            {i > 0 && <div style={{ fontSize: 50, color: color.muted }}>→</div>}
            <Appear at={4 + i * 5}>
              <div style={{ border: `${b.big ? 4 : 2}px solid ${b.tint}`, background: color.panel, padding: b.big ? "22px 40px" : "18px 28px", borderRadius: 10, boxShadow: b.big ? `0 0 40px ${b.tint}55` : "none" }}>
                <div style={{ fontFamily: display, fontWeight: 700, fontSize: b.big ? 44 : 32, color: color.text }}>{b.name}</div>
                <div style={{ fontFamily: mono, fontSize: 20, color: b.tint }}>{b.sub}</div>
              </div>
            </Appear>
          </div>
        ))}
      </div>
      <div style={{ position: "absolute", left: 110, top: 440 }}>
        <div style={{ fontFamily: mono, fontSize: 20, color: color.muted, marginBottom: 14 }}>
          speed (m/s) · <span style={{ color: color.cyan }}>━ requested</span> · <span style={{ color: color.lime }}>━ what reaches the wheels</span> · policy, illustrated
        </div>
        <svg width={CW} height={CH + 40} style={{ overflow: "visible" }}>
          <line x1={0} x2={CW} y1={CH} y2={CH} stroke={color.line} strokeWidth={2} />
          <g opacity={interpolate(frame, [clampAt, clampAt + 8], [0, 1], clamp)}>
            <line x1={0} x2={CW} y1={cy(0.2)} y2={cy(0.2)} stroke={color.orange} strokeWidth={2} strokeDasharray="10 8" />
            <text x={CW} y={cy(0.2) - 10} textAnchor="end" fill={color.orange} fontFamily={mono} fontSize={20}>CLAMP 0.20 m/s</text>
          </g>
          <path d={series(input, Math.min(t, LAST_CMD))} fill="none" stroke={color.cyan} strokeWidth={4} strokeDasharray="2 0" opacity={0.8} />
          <path d={series((s) => output(s, true), t)} fill="none" stroke={color.lime} strokeWidth={6} style={{ filter: `drop-shadow(0 0 8px ${color.lime})` }} />
          {t > LAST_CMD && (
            <g opacity={interpolate(frame, [zero, zero + 8], [0, 1], clamp)}>
              <line x1={cx(LAST_CMD)} x2={cx(LAST_CMD)} y1={0} y2={CH} stroke={color.cyan} strokeDasharray="4 6" />
              <line x1={cx(LAST_CMD + 0.25)} x2={cx(LAST_CMD + 0.25)} y1={0} y2={CH} stroke={color.lime} strokeDasharray="4 6" />
              <text x={cx(LAST_CMD) + 4} y={cy(0.29)} fill={color.text} fontFamily={mono} fontSize={20}>last command → 250 ms → zero</text>
            </g>
          )}
        </svg>
      </div>
      <div style={{ position: "absolute", right: 110, top: 470, width: 480, opacity: interpolate(frame, [dog, dog + 8], [0, 1], clamp), translate: interpolate(frame, [dog, dog + 16], ["60px 0px", "0px 0px"], { ...clamp, easing: outExpo }) }}>
        <div style={{ border: `3px solid ${color.red}`, background: color.panel, padding: "26px 30px", borderRadius: 10, boxShadow: `0 0 40px ${color.red}44` }}>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 40, color: color.text }}>🐕 Independent watchdog</div>
          <div style={{ fontFamily: mono, fontSize: 21, color: color.muted, marginTop: 10, lineHeight: 1.5 }}>
            command stream stale?<br />red stop pressed?<br />telemetry stale?
          </div>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 28, color: color.red, marginTop: 12 }}>→ motors off, power off</div>
        </div>
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};
