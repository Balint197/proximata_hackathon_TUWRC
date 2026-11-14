import { AbsoluteFill, useVideoConfig } from "remotion";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { Hook } from "./Hook";
import { MissionLog } from "./MissionLog";
import { Radar } from "./Radar";
import { Watchdog } from "./Watchdog";
import { Finale } from "./Finale";

export const SafetyNet = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: "#04060c" }}>
      <TransitionSeries>
        <TransitionSeries.Sequence name="Hook" durationInFrames={4 * fps}>
          <Hook />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={slide({ direction: "from-bottom" })} timing={linearTiming({ durationInFrames: 12 })} />
        <TransitionSeries.Sequence name="Mission log" durationInFrames={7.5 * fps}>
          <MissionLog />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={wipe({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 12 })} />
        <TransitionSeries.Sequence name="Radar" durationInFrames={9 * fps}>
          <Radar />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={linearTiming({ durationInFrames: 12 })} />
        <TransitionSeries.Sequence name="Watchdog" durationInFrames={5.5 * fps}>
          <Watchdog />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
        <TransitionSeries.Sequence name="Finale" durationInFrames={4 * fps}>
          <Finale />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
