import { Composition } from "remotion";
import { DoorRun } from "./door-run/DoorRun";
import { SafetyNet } from "./safety-net/SafetyNet";
import { Film } from "./film/Film";
import { FPS, totalFrames } from "./film/timeline";

export const RemotionRoot = () => (
  <>
    <Composition id="HackTheD1" component={Film} durationInFrames={totalFrames} fps={FPS} width={1920} height={1080} />
    <Composition id="DoorRun" component={DoorRun} durationInFrames={877} fps={30} width={1920} height={1080} />
    <Composition id="SafetyNet" component={SafetyNet} durationInFrames={852} fps={30} width={1920} height={1080} />
  </>
);
