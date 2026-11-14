import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Backdrop, Flash, Overlay, Scramble, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";
import { sessions } from "./outcomes";

export const Hook = () => {
  const frame = useCurrentFrame();
  const n = Math.round(interpolate(frame, [8, 46], [0, sessions.length], { ...clamp, easing: outExpo }));
  return (
    <AbsoluteFill>
      <Backdrop tint={color.amber} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <Tag tint={color.amber}>
          <Scramble text="74 kg robot · busy hackathon hall" start={0} stagger={0.6} seed="hk" />
        </Tag>
        <div style={{ display: "flex", alignItems: "baseline", gap: 40, marginTop: 20 }}>
          <div
            style={{
              fontFamily: display,
              fontWeight: 700,
              fontSize: 330,
              lineHeight: 1,
              color: color.text,
              fontVariantNumeric: "tabular-nums",
              textShadow: `0 0 60px ${color.amber}55`,
            }}
          >
            {n}
          </div>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 100, color: color.amber, lineHeight: 1.05 }}>drive<br />sessions</div>
        </div>
        <div
          style={{
            fontFamily: display,
            fontWeight: 500,
            fontSize: 64,
            color: color.text,
            marginTop: 10,
            opacity: interpolate(frame, [50, 60], [0, 1], clamp),
            translate: interpolate(frame, [50, 66], ["0px 30px", "0px 0px"], { ...clamp, easing: outExpo }),
          }}
        >
          Every one ended with the motors <span style={{ color: color.lime, fontWeight: 700 }}>OFF</span>.
        </div>
        <div style={{ display: "flex", gap: 12, marginTop: 50 }}>
          {sessions.map((s, i) => {
            const on = frame >= 8 + i * 1.5;
            const off = frame >= 62 + i * 1.2;
            return (
              <div
                key={s.id}
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 17,
                  border: `3px solid ${off ? color.lime : color.amber}`,
                  background: off ? `${color.lime}33` : on ? `${color.amber}44` : "transparent",
                  opacity: on ? 1 : 0.15,
                  boxShadow: off ? `0 0 16px ${color.lime}` : "none",
                  fontFamily: mono,
                  fontSize: 15,
                  fontWeight: 700,
                  color: off ? color.lime : color.amber,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                ⏻
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
      <Flash at={60} length={10} tint={color.lime} peak={0.25} />
      <Overlay />
    </AbsoluteFill>
  );
};
