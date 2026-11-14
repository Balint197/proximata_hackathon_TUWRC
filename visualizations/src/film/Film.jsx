import { Audio } from "@remotion/media";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { AbsoluteFill, staticFile } from "remotion";
import { RunScene } from "../door-run/RunScene";
import { Stats } from "../door-run/Stats";
import { MissionLog } from "../safety-net/MissionLog";
import { Radar } from "../safety-net/Radar";
import { Watchdog } from "../safety-net/Watchdog";
import { color } from "../theme";
import { Brain, GettingIn } from "./Access";
import { Credits, Footage, Lessons, Status } from "./Closing";
import { Narration } from "./Narration";
import { ClosedBox, ColdOpen, TitleCard } from "./Opening";
import { Sensors, DriveGate } from "./Systems";
import { music, scene, TRANSITION } from "./timeline";

const timing = linearTiming({ durationInFrames: TRANSITION });

// One voiced scene: visuals plus its narration line.
const Voiced = ({ id, Visual, captions = true }) => {
  const line = scene(id);
  return (
    <AbsoluteFill>
      <Visual line={line} />
      <Narration line={line} captions={captions} />
    </AbsoluteFill>
  );
};

export const Film = () => (
  <AbsoluteFill style={{ backgroundColor: color.bg }}>
    {music && <Audio src={staticFile(music)} volume={0.12} loop />}
    <TransitionSeries>
      <TransitionSeries.Sequence name="Cold open" durationInFrames={scene("01-cold-open").frames}>
        <Voiced id="01-cold-open" Visual={ColdOpen} captions={false} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={timing} />
      <TransitionSeries.Sequence name="Title" durationInFrames={scene("02-title").frames}>
        <Voiced id="02-title" Visual={TitleCard} captions={false} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={wipe({ direction: "from-left" })} timing={timing} />
      <TransitionSeries.Sequence name="Closed box" durationInFrames={scene("03-closed-box").frames}>
        <Voiced id="03-closed-box" Visual={ClosedBox} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={timing} />
      <TransitionSeries.Sequence name="Getting in" durationInFrames={scene("04-getting-in").frames}>
        <Voiced id="04-getting-in" Visual={GettingIn} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={timing} />
      <TransitionSeries.Sequence name="Networked brain" durationInFrames={scene("05-brain").frames}>
        <Voiced id="05-brain" Visual={Brain} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={wipe({ direction: "from-bottom" })} timing={timing} />
      <TransitionSeries.Sequence name="Sensors" durationInFrames={scene("06-sensors").frames}>
        <Voiced id="06-sensors" Visual={Sensors} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={timing} />
      <TransitionSeries.Sequence name="Drive gate" durationInFrames={scene("07-drive-gate").frames}>
        <Voiced id="07-drive-gate" Visual={DriveGate} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-bottom" })} timing={timing} />
      <TransitionSeries.Sequence name="Mission log" durationInFrames={scene("08-mission-log").frames}>
        <Voiced id="08-mission-log" Visual={MissionLog} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={wipe({ direction: "from-right" })} timing={timing} />
      <TransitionSeries.Sequence name="Radar" durationInFrames={scene("09-radar").frames}>
        <Voiced id="09-radar" Visual={Radar} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={timing} />
      <TransitionSeries.Sequence name="Watchdog" durationInFrames={scene("10-watchdog").frames}>
        <Voiced id="10-watchdog" Visual={Watchdog} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={timing} />
      <TransitionSeries.Sequence name="Footage" durationInFrames={scene("11-footage").frames}>
        <Voiced id="11-footage" Visual={Footage} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={wipe({ direction: "from-left" })} timing={timing} />
      <TransitionSeries.Sequence name="Replay" durationInFrames={scene("12-replay").frames}>
        <Voiced id="12-replay" Visual={RunScene} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={timing} />
      <TransitionSeries.Sequence name="Debrief" durationInFrames={scene("13-debrief").frames}>
        <Voiced id="13-debrief" Visual={Stats} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-bottom" })} timing={timing} />
      <TransitionSeries.Sequence name="Lessons" durationInFrames={scene("14-lessons").frames}>
        <Voiced id="14-lessons" Visual={Lessons} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={slide({ direction: "from-right" })} timing={timing} />
      <TransitionSeries.Sequence name="Status" durationInFrames={scene("15-status").frames}>
        <Voiced id="15-status" Visual={Status} />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={timing} />
      <TransitionSeries.Sequence name="Credits" durationInFrames={scene("16-outro").frames}>
        <Voiced id="16-outro" Visual={Credits} captions={false} />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  </AbsoluteFill>
);
