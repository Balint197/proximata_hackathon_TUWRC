import { AbsoluteFill, useVideoConfig } from "remotion";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";
import run from "../data/door-run.json";
import { Intro } from "./Intro";
import { DRIVE_START, RunScene } from "./RunScene";
import { Stats } from "./Stats";
import { Outro } from "./Outro";

export const DoorRun = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: "#04060c" }}>
      <TransitionSeries>
        <TransitionSeries.Sequence name="Intro" durationInFrames={3.6 * fps}>
          <Intro />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={wipe({ direction: "from-left" })} timing={linearTiming({ durationInFrames: 12 })} />
        <TransitionSeries.Sequence name="Run" durationInFrames={Math.ceil((DRIVE_START + run.duration + 2.6) * fps)}>
          <RunScene />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
        <TransitionSeries.Sequence name="Stats" durationInFrames={4.6 * fps}>
          <Stats />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={wipe({ direction: "from-bottom" })} timing={linearTiming({ durationInFrames: 12 })} />
        <TransitionSeries.Sequence name="Outro" durationInFrames={4 * fps}>
          <Outro />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
