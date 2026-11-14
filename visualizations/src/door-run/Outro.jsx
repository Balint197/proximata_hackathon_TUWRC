import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Backdrop, Overlay, Scramble, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";

const LAYERS = [
  { name: "SLAM Toolbox + Nav2", note: "live map · planner · Regulated Pure Pursuit", tint: color.lime },
  { name: "Drive gate + watchdog", note: "clamp 0.20 m/s · zero after 250 ms · independent disable", tint: color.orange },
  { name: "ROS 1 → ROS 2 bridge", note: "rootless Humble · laser, odom, IMU, camera, air quality", tint: color.cyan },
  { name: "Vendor ROS 1 stack", note: "untouched: no flashing, no cutting, nothing replaced", tint: color.muted },
];

export const Outro = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{ padding: "100px 160px", flexDirection: "row", alignItems: "center", gap: 120 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 18, width: 900 }}>
          {LAYERS.map((layer, i) => {
            const at = 6 + (LAYERS.length - 1 - i) * 7;
            return (
              <div
                key={layer.name}
                style={{
                  borderLeft: `8px solid ${layer.tint}`,
                  background: color.panel,
                  padding: "22px 30px",
                  opacity: interpolate(frame, [at, at + 6], [0, 1], clamp),
                  translate: interpolate(frame, [at, at + 16], ["0px -70px", "0px 0px"], { ...clamp, easing: outExpo }),
                  boxShadow: `0 0 30px ${layer.tint}22`,
                }}
              >
                <div style={{ fontFamily: display, fontWeight: 700, fontSize: 46, color: color.text }}>{layer.name}</div>
                <div style={{ fontFamily: mono, fontSize: 22, color: color.muted, marginTop: 4 }}>{layer.note}</div>
              </div>
            );
          })}
        </div>
        <div style={{ flex: 1 }}>
          <Tag tint={color.lime} style={{ opacity: interpolate(frame, [40, 48], [0, 1], clamp) }}>Closed box → open robot</Tag>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 104, lineHeight: 0.98, letterSpacing: -3, color: color.text, marginTop: 20 }}>
            <Scramble text="Just" start={44} seed="o1" />
            <br />
            <Scramble text="ROS 2." start={50} seed="o2" style={{ color: color.cyan }} />
          </div>
          <div style={{ fontFamily: mono, fontSize: 24, color: color.muted, marginTop: 40, opacity: interpolate(frame, [64, 76], [0, 1], clamp) }}>
            Hack the D1 · TUWRC
          </div>
        </div>
      </AbsoluteFill>
      <Overlay />
    </AbsoluteFill>
  );
};
