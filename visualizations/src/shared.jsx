import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { clamp, color, mono, outExpo } from "./theme";

// Dark field with a faint metric grid, scanlines, vignette and moving grain.
export const Backdrop = ({ grid = 80, tint = color.cyan }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: color.bg }}>
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${tint}10 1px, transparent 1px), linear-gradient(90deg, ${tint}10 1px, transparent 1px)`,
          backgroundSize: `${grid}px ${grid}px`,
          backgroundPosition: `${(frame * 0.4) % grid}px ${(frame * 0.6) % grid}px`,
        }}
      />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, rgba(40,90,180,0.18), transparent 65%)" }} />
    </AbsoluteFill>
  );
};

export const Overlay = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill
        style={{
          backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,0.22) 0px, rgba(0,0,0,0.22) 1px, transparent 2px, transparent 4px)",
          opacity: 0.5,
        }}
      />
      <svg width="100%" height="100%" style={{ position: "absolute", opacity: 0.09, mixBlendMode: "screen" }}>
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={frame % 12} />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.75) 100%)" }} />
    </AbsoluteFill>
  );
};

const GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#/<>_=+";

// Characters resolve from random glyphs, left to right.
export const Scramble = ({ text, start = 0, stagger = 1.2, settle = 8, seed = "s", style }) => {
  const frame = useCurrentFrame();
  return (
    <span style={style}>
      {text.split("").map((ch, i) => {
        const at = start + i * stagger;
        if (ch === " ") return <span key={i}> </span>;
        if (frame < at) return <span key={i} style={{ opacity: 0 }}>{ch}</span>;
        const resolved = frame >= at + settle;
        const glyph = resolved ? ch : GLYPHS[Math.floor(random(`${seed}-${i}-${Math.floor(frame / 2)}`) * GLYPHS.length)];
        return (
          <span key={i} style={{ color: resolved ? undefined : color.cyan, opacity: resolved ? 1 : 0.85 }}>
            {glyph}
          </span>
        );
      })}
    </span>
  );
};

// Number that counts up from zero.
export const CountUp = ({ value, start = 0, duration = 30, decimals = 2, suffix = "", style }) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [start, start + duration], [0, value], { ...clamp, easing: outExpo });
  return (
    <span style={{ fontVariantNumeric: "tabular-nums", ...style }}>
      {v.toFixed(decimals)}
      {suffix}
    </span>
  );
};

// Four corner ticks that frame a box.
export const Brackets = ({ size = 22, thickness = 3, tint = color.cyan, inset = 0 }) => {
  const s = { position: "absolute", width: size, height: size, borderColor: tint, borderStyle: "solid", borderWidth: 0 };
  return (
    <>
      <div style={{ ...s, left: inset, top: inset, borderLeftWidth: thickness, borderTopWidth: thickness }} />
      <div style={{ ...s, right: inset, top: inset, borderRightWidth: thickness, borderTopWidth: thickness }} />
      <div style={{ ...s, left: inset, bottom: inset, borderLeftWidth: thickness, borderBottomWidth: thickness }} />
      <div style={{ ...s, right: inset, bottom: inset, borderRightWidth: thickness, borderBottomWidth: thickness }} />
    </>
  );
};

export const Tag = ({ children, tint = color.cyan, style }) => (
  <div
    style={{
      fontFamily: mono,
      fontSize: 22,
      letterSpacing: 4,
      textTransform: "uppercase",
      color: tint,
      ...style,
    }}
  >
    {children}
  </div>
);

// A white flash that peaks at `at` and fades out quickly.
export const Flash = ({ at, length = 10, tint = "#ffffff", peak = 0.85 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [at - 2, at, at + length], [0, peak, 0], clamp);
  return <AbsoluteFill style={{ backgroundColor: tint, opacity: o, pointerEvents: "none" }} />;
};
