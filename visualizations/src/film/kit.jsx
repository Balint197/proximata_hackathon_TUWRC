import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Backdrop, Overlay, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";

// Frame at which `phrase` is (roughly) spoken: proportional to its position in the line.
export const cue = (line, phrase, fps) => {
  const i = line.text.indexOf(phrase);
  const k = i < 0 ? 0 : i / line.text.length;
  return Math.round((line.delay + k * line.seconds) * fps);
};

export const Appear = ({ at, children, from = "0px 30px", style }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        opacity: interpolate(frame, [at, at + 8], [0, 1], clamp),
        translate: interpolate(frame, [at, at + 16], [from, "0px 0px"], { ...clamp, easing: outExpo }),
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export const Stage = ({ tag, title, tint = color.cyan, children }) => (
  <AbsoluteFill>
    <Backdrop tint={tint} />
    {children}
    {title && (
      <div style={{ position: "absolute", left: 110, top: 70 }}>
        <Appear at={0}>
          <Tag tint={tint}>{tag}</Tag>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 72, color: color.text, marginTop: 6 }}>{title}</div>
        </Appear>
      </div>
    )}
    <Overlay />
  </AbsoluteFill>
);

// A labelled node box for diagrams.
export const Node = ({ x, y, w = 300, at, frame, title, sub, tint = color.cyan, icon, children }) => {
  const o = interpolate(frame, [at, at + 8], [0, 1], clamp);
  return (
    <div
      style={{
        position: "absolute",
        left: x - w / 2,
        top: y,
        width: w,
        opacity: o,
        scale: interpolate(frame, [at, at + 14], [0.8, 1], { ...clamp, easing: outExpo }),
        background: color.panel,
        border: `2px solid ${tint}`,
        boxShadow: `0 0 30px ${tint}33`,
        padding: "18px 22px",
        borderRadius: 10,
        translate: "0px -50%",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        {icon && <span style={{ fontSize: 40 }}>{icon}</span>}
        <div>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 32, color: color.text }}>{title}</div>
          {sub && <div style={{ fontFamily: mono, fontSize: 18, color: color.muted }}>{sub}</div>}
        </div>
      </div>
      {children}
    </div>
  );
};
