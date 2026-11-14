import { Video } from "@remotion/media";
import { AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop, Flash, Overlay, Scramble, Tag } from "../shared";
import { clamp, color, display, mono, outExpo } from "../theme";
import { Appear, cue } from "./kit";

// Portrait phone footage centred on a blurred copy of itself.
export const PortraitFootage = ({ trimBefore = 0, x = 960, height = 1080 }) => (
  <>
    <Video src={staticFile("footage/bottle-run.mp4")} muted trimBefore={trimBefore} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", filter: "blur(40px) brightness(0.35) saturate(1.3)", scale: 1.15 }} />
    <div style={{ position: "absolute", left: x - (height * 9) / 32, top: (1080 - height) / 2, width: (height * 9) / 16, height, boxShadow: `0 0 80px ${color.cyan}44`, outline: `2px solid ${color.cyan}66` }}>
      <Video src={staticFile("footage/bottle-run.mp4")} muted trimBefore={trimBefore} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    </div>
  </>
);

export const RecBadge = ({ label }) => {
  const frame = useCurrentFrame();
  return (
    <Tag tint={color.red} style={{ fontSize: 22 }}>
      <span style={{ opacity: Math.floor(frame / 10) % 2 ? 0.25 : 1 }}>●</span> {label}
    </Tag>
  );
};

export const ColdOpen = ({ line }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const never = cue(line, "It was never", fps);
  return (
    <AbsoluteFill style={{ backgroundColor: color.bg }}>
      <PortraitFootage x={1340} />
      <div style={{ position: "absolute", left: 120, top: 120, width: 820 }}>
        <RecBadge label="Phone footage · 14 Nov 2026" />
        <Appear at={10}>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 150, color: color.text, lineHeight: 1, marginTop: 40 }}>
            74 kg
          </div>
          <div style={{ fontFamily: mono, fontSize: 28, color: color.muted, letterSpacing: 3, textTransform: "uppercase" }}>disinfection robot · driving itself</div>
        </Appear>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 76, lineHeight: 1.05, color: color.cyan, marginTop: 80, textShadow: `0 0 40px ${color.cyan}66` }}>
          {frame >= never && <Scramble text="Never built to take orders from us." start={never} stagger={0.8} seed="cold" />}
        </div>
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};

const Wheel = ({ size = 120, tint = color.lime }) => {
  const frame = useCurrentFrame();
  return (
    <svg width={size} height={size} viewBox="-50 -50 100 100" style={{ rotate: `${frame * 9}deg` }}>
      <circle r={44} fill="none" stroke={tint} strokeWidth={7} />
      <circle r={7} fill={tint} />
      {Array.from({ length: 12 }, (_, i) => (
        <line key={i} x1={0} y1={0} x2={44 * Math.cos((i * Math.PI) / 6)} y2={44 * Math.sin((i * Math.PI) / 6)} stroke={tint} strokeWidth={2} />
      ))}
    </svg>
  );
};

export const TitleCard = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{ justifyContent: "center", padding: "0 160px" }}>
        <Tag>
          <Scramble text="TUWRC · Building Better Worlds Hackathon 2026" start={0} stagger={0.5} seed="t0" />
        </Tag>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 230, lineHeight: 0.9, letterSpacing: -7, color: color.text, marginTop: 20, textShadow: `0 0 50px ${color.cyan}55` }}>
          <Scramble text="HACK " start={4} stagger={2} seed="t1" />
          <Scramble text="THE D1" start={12} stagger={2} seed="t2" style={{ color: color.cyan }} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 34, marginTop: 60, opacity: interpolate(frame, [26, 36], [0, 1], clamp), translate: interpolate(frame, [26, 44], ["-60px 0px", "0px 0px"], { ...clamp, easing: outExpo }) }}>
          <Wheel />
          <div>
            <div style={{ fontFamily: mono, fontSize: 24, letterSpacing: 4, color: color.muted }}>A FILM BY TEAM</div>
            <div style={{ fontFamily: display, fontWeight: 700, fontSize: 84, color: color.lime, lineHeight: 1 }}>Verspätete Rädfahrer</div>
          </div>
        </div>
      </AbsoluteFill>
      <Flash at={4} length={8} peak={0.35} />
      <Overlay />
    </AbsoluteFill>
  );
};

const LEVELS = [
  { phrase: "get in", name: "Get in", status: "done", note: "shell on the robot" },
  { phrase: "unlock", name: "Unlock every sensor", status: "partial", note: "13 topics live · 2 cameras silent" },
  { phrase: "take the wheel", name: "Take the wheel", status: "done", note: "supervised drives" },
  { phrase: "navigate", name: "Navigate", status: "partial", note: "Nav2 goal reached · real door next" },
  { phrase: "answer the door", name: "Answer the door", status: "designed", note: "no Home Assistant credentials" },
];

const RobotSketch = ({ locked }) => (
  <svg width={420} height={760} viewBox="0 0 420 760">
    <defs>
      <linearGradient id="body" x1="0" x2="1">
        <stop offset="0" stopColor="#dfe6ee" />
        <stop offset="0.6" stopColor="#ffffff" />
        <stop offset="1" stopColor="#b9c3cf" />
      </linearGradient>
    </defs>
    <rect x={60} y={640} width={300} height={80} rx={30} fill="#1d2532" />
    <rect x={70} y={630} width={280} height={14} rx={7} fill={color.blue} style={{ filter: `drop-shadow(0 0 14px ${color.blue})` }} />
    <path d="M80 230 L340 230 L330 630 L90 630 Z" fill="url(#body)" />
    {Array.from({ length: 60 }, (_, i) => (
      <circle key={i} cx={120 + (i % 10) * 20} cy={460 + Math.floor(i / 10) * 22} r={3} fill="#9aa6b5" />
    ))}
    <rect x={70} y={140} width={280} height={100} rx={30} fill="#2a3442" />
    <rect x={110} y={175} width={200} height={20} rx={10} fill={color.cyan} style={{ filter: `drop-shadow(0 0 16px ${color.cyan})` }} />
    <rect x={50} y={80} width={320} height={70} rx={32} fill="#2a3442" />
    <g transform="translate(210 400)" opacity={locked}>
      <rect x={-70} y={-20} width={140} height={110} rx={16} fill={color.amber} />
      <path d="M-42 -20 V-60 A42 42 0 0 1 42 -60 V-20" fill="none" stroke={color.amber} strokeWidth={18} />
      <circle cy={30} r={14} fill="#1d2532" />
    </g>
  </svg>
);

export const ClosedBox = ({ line }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const closed = cue(line, "closed box", fps);
  const statusAt = cue(line, "answer the door", fps) + 24;
  return (
    <AbsoluteFill>
      <Backdrop />
      <div style={{ position: "absolute", left: 180, top: 150, scale: interpolate(frame, [0, 20], [0.9, 1], { ...clamp, easing: outExpo }) }}>
        <RobotSketch locked={interpolate(frame, [closed, closed + 8, statusAt, statusAt + 10], [0, 1, 1, 0], clamp)} />
        <div style={{ fontFamily: mono, fontSize: 24, color: color.muted, textAlign: "center", letterSpacing: 3 }}>HYUNDAI D1 · CLOSED BOX</div>
      </div>
      <div style={{ position: "absolute", left: 760, top: 150, width: 1040 }}>
        <Tag>The track · five levels</Tag>
        <div style={{ display: "flex", flexDirection: "column", gap: 20, marginTop: 30 }}>
          {LEVELS.map((lv, i) => {
            const at = cue(line, lv.phrase, fps);
            const tint = { done: color.lime, partial: color.cyan, designed: color.amber }[lv.status];
            const shown = frame >= statusAt + i * 4;
            return (
              <Appear key={lv.name} at={at} from="80px 0px">
                <div style={{ display: "flex", alignItems: "center", gap: 28, background: color.panel, padding: "18px 28px", borderLeft: `6px solid ${shown ? tint : color.line}` }}>
                  <div style={{ fontFamily: mono, fontSize: 40, fontWeight: 700, color: color.muted, width: 60 }}>{i + 1}</div>
                  <div style={{ flex: 1, fontFamily: display, fontWeight: 700, fontSize: 44, color: color.text, whiteSpace: "nowrap" }}>{lv.name}</div>
                  <div style={{ textAlign: "right", opacity: shown ? 1 : 0, scale: shown ? 1 : 1.4 }}>
                    <div style={{ fontFamily: display, fontWeight: 700, fontSize: 30, color: tint }}>{{ done: "✓ DONE", partial: "◑ MOSTLY", designed: "○ DESIGNED" }[lv.status]}</div>
                    <div style={{ fontFamily: mono, fontSize: 18, color: color.muted }}>{lv.note}</div>
                  </div>
                </div>
              </Appear>
            );
          })}
        </div>
      </div>
      <Overlay />
    </AbsoluteFill>
  );
};
