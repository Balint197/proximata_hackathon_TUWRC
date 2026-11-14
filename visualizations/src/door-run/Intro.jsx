import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Backdrop, Flash, Overlay, Scramble, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";

const Spec = ({ label, value, at }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        opacity: interpolate(frame, [at, at + 10], [0, 1], clamp),
        translate: interpolate(frame, [at, at + 14], ["0px 24px", "0px 0px"], { ...clamp, easing: outExpo }),
        borderLeft: `3px solid ${color.cyan}`,
        paddingLeft: 18,
      }}
    >
      <div style={{ fontFamily: mono, fontSize: 20, letterSpacing: 3, color: color.muted, textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontFamily: display, fontSize: 44, fontWeight: 700, color: color.text }}>{value}</div>
    </div>
  );
};

export const Intro = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{ padding: "150px 160px", justifyContent: "center" }}>
        <Tag style={{ opacity: interpolate(frame, [0, 8], [0, 1], clamp) }}>
          <Scramble text="TUWRC · Building Better Worlds 2026" start={0} stagger={0.6} seed="tag" />
        </Tag>
        <div
          style={{
            fontFamily: display,
            fontWeight: 700,
            fontSize: 210,
            lineHeight: 0.92,
            letterSpacing: -6,
            color: color.text,
            marginTop: 24,
            textShadow: `0 0 40px ${color.cyan}55`,
            scale: interpolate(frame, [6, 40], [1.08, 1], { ...clamp, easing: outExpo }),
            transformOrigin: "left center",
          }}
        >
          <Scramble text="HACK" start={6} stagger={2} seed="h1" />
          <br />
          <Scramble text="THE D1" start={12} stagger={2} seed="h2" style={{ color: color.cyan }} />
        </div>
        <div style={{ display: "flex", gap: 70, marginTop: 70 }}>
          <Spec label="Robot" value="Hyundai D1 · 74 kg" at={34} />
          <Spec label="Sold as" value="A closed box" at={42} />
          <Spec label="Mission" value="Drive itself to the door" at={50} />
        </div>
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          left: interpolate(frame, [0, 90], [-400, 2200], clamp),
          width: 6,
          background: `linear-gradient(transparent, ${color.cyan}, transparent)`,
          boxShadow: `0 0 40px 10px ${color.cyan}66`,
          opacity: 0.6,
        }}
      />
      <Flash at={6} length={8} peak={0.35} />
      <Overlay />
    </AbsoluteFill>
  );
};
