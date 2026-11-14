import { Audio } from "@remotion/media";
import { AbsoluteFill, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, color, display } from "../theme";

// Split a line into caption chunks of whole words, at most ~58 characters each.
const chunk = (text) => {
  const out = [];
  for (const sentence of text.match(/[^.!?:]+[.!?:]?/g) ?? [text]) {
    let cur = "";
    for (const word of sentence.trim().split(/\s+/)) {
      if ((cur + " " + word).trim().length > 58 && cur) {
        out.push(cur);
        cur = word;
      } else cur = (cur + " " + word).trim();
    }
    if (cur) out.push(cur);
  }
  return out;
};

const Captions = ({ text, seconds }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const parts = chunk(text);
  const total = parts.reduce((a, p) => a + p.length, 0);
  let acc = 0;
  const timed = parts.map((p) => {
    const start = (acc / total) * seconds * fps;
    acc += p.length;
    return { p, start, end: (acc / total) * seconds * fps };
  });
  const cur = timed.find((c) => frame >= c.start && frame < c.end);
  if (!cur) return null;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 46, pointerEvents: "none" }}>
      <div
        style={{
          fontFamily: display,
          fontWeight: 500,
          fontSize: 38,
          color: color.text,
          background: "rgba(2, 4, 10, 0.78)",
          padding: "10px 26px",
          borderRadius: 6,
          opacity: interpolate(frame, [cur.start, cur.start + 3], [0.4, 1], clamp),
        }}
      >
        {cur.p}
      </div>
    </AbsoluteFill>
  );
};

// The scene's voice line, its captions, and a whoosh on the cut.
export const Narration = ({ line, captions = true }) => {
  const { fps } = useVideoConfig();
  return (
    <>
      <Audio src={staticFile("sfx/whoosh.wav")} volume={0.25} />
      {line.file && (
        <Sequence from={Math.round(line.delay * fps)} name={`Voice ${line.id}`} layout="none">
          <Audio src={staticFile(line.file)} />
          {captions && <Captions text={line.text} seconds={line.seconds} />}
        </Sequence>
      )}
    </>
  );
};
