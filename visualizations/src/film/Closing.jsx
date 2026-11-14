import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop, Flash, Overlay, Scramble, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";
import { Appear, cue } from "./kit";
import { PortraitFootage, RecBadge } from "./Opening";

const Chip = ({ at, title, sub, tint = color.cyan }) => (
  <Appear at={at} from="60px 0px">
    <div style={{ borderLeft: `6px solid ${tint}`, background: color.panel, padding: "16px 24px" }}>
      <div style={{ fontFamily: display, fontWeight: 700, fontSize: 36, color: color.text }}>{title}</div>
      <div style={{ fontFamily: mono, fontSize: 20, color: color.muted }}>{sub}</div>
    </div>
  </Appear>
);

export const Footage = ({ line }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: color.bg }}>
      <PortraitFootage x={960} />
      <div style={{ position: "absolute", left: 100, top: 110, width: 520 }}>
        <RecBadge label="Phone footage · 14 Nov" />
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 84, color: color.text, lineHeight: 1, marginTop: 20 }}>Level 4:<br />navigate</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 18, marginTop: 50 }}>
          <Chip at={cue(line, "SLAM", fps)} title="SLAM Toolbox" sub="live map from the laser" />
          <Chip at={cue(line, "Nav2", fps)} title="Nav2" sub="planner + Regulated Pure Pursuit" tint={color.orange} />
        </div>
      </div>
      <div style={{ position: "absolute", right: 100, top: 110, width: 520, display: "flex", flexDirection: "column", gap: 18 }}>
        <Chip at={cue(line, "Here's", fps)} title="Goal: the bottle" sub="stand-in for the front door" tint={color.lime} />
        <Chip at={cue(line, "Here's", fps) + 10} title="Max 0.15 m/s" sub="Nav2 limit, gated and clamped" tint={color.amber} />
        <Chip at={cue(line, "Here's", fps) + 20} title="Red stop manned" sub="for every motion" tint={color.red} />
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};

const LESSONS = [
  { phrase: "vendor's ROS 1", title: "The vendor's ROS 1 graph is the way in", sub: "no firmware, no serial: talk to what's already running" },
  { phrase: "Published", title: "Published ≠ delivered", sub: "two cameras were registered and never sent a frame" },
  { phrase: "Motor power", title: "Power and enable are two switches", sub: "and the config parameter doesn't show runtime state" },
  { phrase: "command timeout", title: "Timeouts need a supervisor", sub: "the vendor's own stop after adapter loss was too slow" },
];

export const Lessons = ({ line }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      <Backdrop tint={color.amber} />
      <div style={{ position: "absolute", left: 110, top: 70 }}>
        <Appear at={0}>
          <Tag tint={color.amber}>What we learned</Tag>
        </Appear>
      </div>
      <div style={{ position: "absolute", left: 110, right: 110, top: 160, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 30 }}>
        {LESSONS.map((l, i) => (
          <Appear key={l.title} at={cue(line, l.phrase, fps)} from="0px 50px">
            <div style={{ background: color.panel, border: `1px solid ${color.line}`, padding: "34px 38px", height: 330, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div style={{ fontFamily: mono, fontSize: 64, fontWeight: 700, color: color.amber }}>0{i + 1}</div>
              <div>
                <div style={{ fontFamily: display, fontWeight: 700, fontSize: 52, color: color.text, lineHeight: 1.05 }}>{l.title}</div>
                <div style={{ fontFamily: mono, fontSize: 22, color: color.muted, marginTop: 14 }}>{l.sub}</div>
              </div>
            </div>
          </Appear>
        ))}
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};

const Item = ({ at, children, tint, mark }) => (
  <Appear at={at} from="40px 0px">
    <div style={{ display: "flex", gap: 22, alignItems: "baseline", fontFamily: display, fontWeight: 700, fontSize: 46, color: color.text, marginTop: 22 }}>
      <span style={{ color: tint, width: 50 }}>{mark}</span>
      {children}
    </div>
  </Appear>
);

export const Status = ({ line }) => {
  const { fps } = useVideoConfig();
  const done = cue(line, "access", fps);
  const next = cue(line, "Next", fps);
  const designed = cue(line, "It's designed", fps);
  return (
    <AbsoluteFill>
      <Backdrop />
      <div style={{ position: "absolute", left: 110, top: 70 }}>
        <Appear at={0}>
          <Tag>Where we are</Tag>
        </Appear>
      </div>
      <div style={{ position: "absolute", left: 110, top: 170, width: 820 }}>
        <div style={{ fontFamily: mono, fontSize: 26, letterSpacing: 4, color: color.lime }}>DEMONSTRATED</div>
        <Item at={done} tint={color.lime} mark="✓">Access to the robot</Item>
        <Item at={done + 10} tint={color.lime} mark="✓">ROS 2 sensor bridge</Item>
        <Item at={done + 20} tint={color.lime} mark="✓">Supervised driving</Item>
        <Item at={done + 30} tint={color.lime} mark="✓">A completed Nav2 goal</Item>
      </div>
      <div style={{ position: "absolute", left: 1010, top: 170, width: 800 }}>
        <div style={{ fontFamily: mono, fontSize: 26, letterSpacing: 4, color: color.amber }}>NEXT</div>
        <Item at={next} tint={color.amber} mark="→">The route to the real door</Item>
        <Item at={next + 12} tint={color.amber} mark="→">Doorbell via Home Assistant</Item>
        <Appear at={designed}>
          <div style={{ marginTop: 40, background: color.panel, borderLeft: `6px solid ${color.amber}`, padding: "20px 26px", fontFamily: mono, fontSize: 22, color: color.muted, lineHeight: 1.5 }}>
            Home Assistant → listener on the D1 → <span style={{ color: color.text }}>d1_goto.py door</span>
            <br />
            doorbell camera full-screen while it drives
            <br />
            <span style={{ color: color.amber }}>designed · blocked on credentials</span>
          </div>
        </Appear>
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};

export const Credits = ({ line }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = [
    { phrase: "No flashing", text: "No flashing." },
    { phrase: "No cutting", text: "No cutting." },
    { phrase: "Nothing replaced", text: "Nothing replaced." },
  ];
  const just = cue(line, "Just ROS 2", fps);
  const team = cue(line, "We're", fps);
  return (
    <AbsoluteFill>
      <Backdrop tint={color.lime} />
      <AbsoluteFill style={{ padding: "0 160px", justifyContent: "center" }}>
        <div style={{ display: "flex", gap: 40, opacity: interpolate(frame, [team, team + 8], [1, 0.35], clamp) }}>
          {words.map((w) => (
            <Appear key={w.text} at={cue(line, w.phrase, fps)} from="0px -30px">
              <div style={{ fontFamily: display, fontWeight: 700, fontSize: 64, color: color.muted }}>{w.text}</div>
            </Appear>
          ))}
        </div>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 200, lineHeight: 1, color: color.cyan, marginTop: 20, textShadow: `0 0 60px ${color.cyan}77` }}>
          {frame >= just && <Scramble text="Just ROS 2." start={just} stagger={1.4} seed="cr" />}
        </div>
        <div style={{ marginTop: 60, opacity: interpolate(frame, [team, team + 10], [0, 1], clamp), translate: interpolate(frame, [team, team + 18], ["0px 40px", "0px 0px"], { ...clamp, easing: outExpo }) }}>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 90, color: color.lime }}>Verspätete Rädfahrer</div>
          <div style={{ fontFamily: mono, fontSize: 26, color: color.muted, marginTop: 10 }}>
            Hack the D1 · TUWRC · Building Better Worlds Hackathon 2026 · github.com/Balint197/proximata_hackathon_TUWRC
          </div>
        </div>
      </AbsoluteFill>
      <Flash at={just} length={10} tint={color.cyan} peak={0.25} />
      <Overlay />
    </AbsoluteFill>
  );
};
