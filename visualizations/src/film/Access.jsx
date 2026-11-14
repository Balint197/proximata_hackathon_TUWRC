import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop, Overlay, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";
import { Appear, cue, Node } from "./kit";

const Link = ({ pts, at, frame, tint, dashed, packets = 0, width = 4 }) => {
  const d = pts.map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join(" ");
  const len = pts.slice(1).reduce((a, p, i) => a + Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]), 0);
  const k = interpolate(frame, [at, at + 18], [0, 1], { ...clamp, easing: outExpo });
  const along = (t) => {
    let rest = t * len;
    for (let i = 1; i < pts.length; i++) {
      const seg = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      if (rest <= seg) {
        const f = rest / seg;
        return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f];
      }
      rest -= seg;
    }
    return pts[pts.length - 1];
  };
  return (
    <g>
      <path d={d} fill="none" stroke={tint} strokeWidth={width} strokeDasharray={dashed ? "12 10" : `${len}`} strokeDashoffset={dashed ? 0 : len * (1 - k)} opacity={dashed ? k : 1} style={{ filter: `drop-shadow(0 0 8px ${tint})` }} />
      {k >= 1 &&
        Array.from({ length: packets }, (_, i) => {
          const [px, py] = along((((frame - at) / 50 + i / packets) % 1 + 1) % 1);
          return <circle key={i} cx={px} cy={py} r={8} fill="#fff" style={{ filter: `drop-shadow(0 0 10px ${tint})` }} />;
        })}
    </g>
  );
};

const LAPTOP = [300, 400];
const ROBOT = [1600, 400];
const PHONE = [1600, 770];
const VPS = [950, 770];

export const GettingIn = ({ line }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const usb = cue(line, "USB from", fps);
  const touch = cue(line, "touchscreen", fps);
  const tether = cue(line, "phone tethering", fps);
  const ssh = cue(line, "reverse SSH", fps);
  const shell = cue(line, "Remote shell", fps);
  const sudo = cue(line, "No sudo", fps);
  const termLines = [
    { at: shell, text: "laptop$ ssh robot        # through the VPS", tint: color.muted },
    { at: shell + 8, text: "robot:~$ rostopic list", tint: color.text },
    { at: shell + 14, text: "robot:~$ sudo …", tint: color.text },
    { at: sudo, text: "✗ no sudo rights: everything rootless", tint: color.red },
  ];
  return (
    <AbsoluteFill>
      <Backdrop />
      <div style={{ position: "absolute", left: 110, top: 70 }}>
        <Appear at={0}>
          <Tag>Level 1 · get in</Tag>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 72, color: color.text, marginTop: 6 }}>The way in was the long way round</div>
        </Appear>
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <Link pts={[LAPTOP, ROBOT]} at={usb} frame={frame} tint={color.red} dashed />
        <Link pts={[ROBOT, PHONE]} at={tether} frame={frame} tint={color.amber} packets={2} />
        <Link pts={[PHONE, VPS]} at={ssh} frame={frame} tint={color.lime} packets={3} width={6} />
        <Link pts={[LAPTOP, [LAPTOP[0], VPS[1]], VPS]} at={ssh + 14} frame={frame} tint={color.lime} packets={3} width={6} />
      </svg>
      {frame >= usb + 12 && (
        <div style={{ position: "absolute", left: 950, top: 400, translate: "-50% -50%", fontFamily: display, fontWeight: 700, fontSize: 40, color: color.red, scale: interpolate(frame, [usb + 12, usb + 20], [2, 1], clamp), background: color.bg, padding: "4px 14px", border: `2px solid ${color.red}` }}>
          ✗ USB: no device
        </div>
      )}
      {frame >= ssh + 20 && (
        <div style={{ position: "absolute", left: 950, top: 850, translate: "-50% 0", fontFamily: mono, fontSize: 24, fontWeight: 700, color: color.lime }}>reverse SSH tunnel: the robot dials out</div>
      )}
      <Node x={LAPTOP[0]} y={LAPTOP[1]} w={300} at={4} frame={frame} title="Our laptop" sub="macOS" icon="💻" />
      <Node x={VPS[0]} y={VPS[1]} w={260} at={ssh} frame={frame} title="Our VPS" sub="public server" icon="☁️" tint={color.lime} />
      <Node x={PHONE[0]} y={PHONE[1]} w={300} at={tether} frame={frame} title="A phone" sub="USB tethering" icon="📱" tint={color.amber} />
      <Node x={ROBOT[0]} y={ROBOT[1]} w={340} at={4} frame={frame} title="Hyundai D1" sub="display computer" icon="🤖">
        <div style={{ marginTop: 12, fontFamily: mono, fontSize: 18, color: color.lime, background: "#000", padding: "8px 12px", opacity: interpolate(frame, [touch, touch + 8], [0, 1], clamp) }}>
          touchscreen terminal $ <span style={{ opacity: Math.floor(frame / 8) % 2 }}>▋</span>
        </div>
      </Node>
      <div style={{ position: "absolute", left: 620, top: 500, width: 660, background: "#02050b", border: `1px solid ${color.line}`, padding: "18px 22px", fontFamily: mono, fontSize: 22, opacity: interpolate(frame, [shell, shell + 6], [0, 1], clamp) }}>
        {termLines.filter((l) => frame >= l.at).map((l) => (
          <div key={l.text} style={{ color: l.tint }}>{l.text}</div>
        ))}
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};

const TOPICS = [
  "/robot/scan", "/robot/odom", "/robot/imu/data", "/cmd_vel", "/robot/motor/actual_vel", "/robot/motor/rpm",
  "/robot/motor_power", "/robot/button/emergency_state", "/camera_back/rgb", "/disinfection/co2", "/disinfection/pm25", "/tf",
];

const Row = ({ children, tint = color.text }) => <div style={{ fontFamily: mono, fontSize: 22, color: tint, marginTop: 8 }}>{children}</div>;

export const Brain = ({ line }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const controller = cue(line, "internal controller", fps);
  const mapped = cue(line, "We mapped", fps);
  return (
    <AbsoluteFill>
      <Backdrop />
      <div style={{ position: "absolute", left: 110, top: 70 }}>
        <Appear at={0}>
          <Tag>Inside the box</Tag>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 72, color: color.text, marginTop: 6 }}>It already had a networked brain</div>
        </Appear>
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <Link pts={[[700, 420], [1080, 420]]} at={controller} frame={frame} tint={color.cyan} packets={3} width={5} />
      </svg>
      <div style={{ position: "absolute", left: 1000, top: 360, width: 200, textAlign: "center", fontFamily: mono, fontSize: 20, color: color.cyan, opacity: interpolate(frame, [controller + 10, controller + 18], [0, 1], clamp), translate: "-50% 0" }}>
        ROS 1 Melodic
      </div>
      <Node x={420} y={420} w={520} at={6} frame={frame} title="Display computer" sub="192.168.0.2 · Ubuntu 18.04" icon="🖥️">
        <Row>10.1″ touchscreen</Row>
        <Row>vendor ROS 1 apps</Row>
        <Row tint={color.lime}>+ our rootless ROS 2</Row>
      </Node>
      <Node x={1440} y={460} w={600} at={controller} frame={frame} title="Internal controller" sub="192.168.0.4 · ROS master :11311" icon="🧠" tint={color.orange}>
        <Row>motor driver over CAN</Row>
        <Row>SICK TiM571 laser · 15 Hz</Row>
        <Row>IMU · cameras · air quality</Row>
        <Row tint={color.red}>GPIO: motor power, red stop</Row>
      </Node>
      <div style={{ position: "absolute", left: 110, top: 720, width: 1700, display: "flex", flexWrap: "wrap", gap: 12, opacity: interpolate(frame, [mapped - 10, mapped], [0, 1], clamp) }}>
        <div style={{ width: "100%", fontFamily: mono, fontSize: 22, color: color.muted, marginBottom: 4 }}>$ rostopic list</div>
        {TOPICS.map((t, i) => (
          <div key={t} style={{ fontFamily: mono, fontSize: 22, color: color.cyan, border: `1px solid ${color.line}`, padding: "6px 12px", opacity: frame >= mapped - 10 + i * 2 ? 1 : 0 }}>
            {t}
          </div>
        ))}
      </div>
      <div style={{ position: "absolute", right: 110, top: 90, fontFamily: display, fontWeight: 700, fontSize: 26, color: color.bg, background: color.amber, padding: "8px 18px", rotate: "4deg", opacity: interpolate(frame, [mapped + 20, mapped + 26], [0, 1], clamp), scale: interpolate(frame, [mapped + 20, mapped + 28], [1.6, 1], { ...clamp, easing: outExpo }) }}>
        ⚠ never run the vendor d1_test
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};
