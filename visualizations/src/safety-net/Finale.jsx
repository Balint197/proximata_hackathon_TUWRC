import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Backdrop, Overlay, Scramble, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";
import { sessions } from "./outcomes";

export const Finale = () => {
  const frame = useCurrentFrame();
  const offCount = sessions.filter((s) => s.finalPower === false).length;
  return (
    <AbsoluteFill>
      <Backdrop tint={color.lime} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center" }}>
        <Tag tint={color.lime}>Safety record</Tag>
        <div
          style={{
            fontFamily: display,
            fontWeight: 700,
            fontSize: 250,
            lineHeight: 1,
            color: color.lime,
            textShadow: `0 0 70px ${color.lime}88`,
            marginTop: 16,
            scale: interpolate(frame, [4, 24], [1.6, 1], { ...clamp, easing: outExpo }),
            opacity: interpolate(frame, [4, 10], [0, 1], clamp),
          }}
        >
          {offCount}/{sessions.length}
        </div>
        <div style={{ fontFamily: display, fontWeight: 500, fontSize: 56, color: color.text, marginTop: 10 }}>
          <Scramble text="sessions ended with motor power confirmed off" start={16} stagger={0.7} seed="fin" />
        </div>
        <div style={{ fontFamily: mono, fontSize: 24, color: color.muted, marginTop: 50, opacity: interpolate(frame, [56, 70], [0, 1], clamp) }}>
          Red stop manned for every motion · no firmware flashed · UV-C untouched
        </div>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 44, color: color.cyan, marginTop: 40, opacity: interpolate(frame, [70, 84], [0, 1], clamp) }}>
          Safety first. Then Nav2.
        </div>
      </AbsoluteFill>
      <Overlay />
    </AbsoluteFill>
  );
};
