# D1 visualizations

A Remotion project (JSX) with two hackathon videos built from this repository's evidence:

| Composition | Length | What |
|---|---|---|
| `HackTheD1` | ≤ 3:00 | The narrated hackathon film by team Verspätete Rädfahrer: cold open on the phone footage, getting in, the vendor graph, the sensor bridge, the drive gate, safety record, the footage and telemetry replay of the Nav2 run, lessons and next steps. Timed to the voice lines; see [narration/RECORDING.md](narration/RECORDING.md). |
| `DoorRun` | 29 s | Replay of the Nav2 bottle run (session `20261114T085925`): the SLAM map, Nav2 plan, driven path and live laser scans at 1× speed with a live HUD. After the replay come a debrief (1.04 m driven, 10 s, stopped 0.17 m short) and the software stack. |
| `SafetyNet` | 28 s | All 25 supervised drive sessions as a mission log, the 14 laser-guard trips on a robot-centred radar (including the 3 caused by the robot's own bracket), the watchdog fault-injection timeline, and "25/25 ended with motor power off". |

```sh
cd visualizations
npm install
npm run dev                      # Studio
node scripts/extract-data.mjs    # regenerate src/data/*.json and public/door-run-map.png from docs/evidence
node scripts/voiceover.mjs measure   # after recording public/voiceover/<id>.wav (scratch: `scratch`)
npx remotion render HackTheD1 out/hack-the-d1.mp4
npx remotion render DoorRun out/door-run.mp4
npx remotion render SafetyNet out/safety-net.mp4
```

`scripts/extract-data.mjs` reads `docs/evidence/nav2-bottle-run-2026-11-14.json`, the session records in `docs/evidence/sessions/` and `ros2-stand-watchdog-analysis-2026-11-14.json`. The door-run derivations match `scripts/render_run.py`.
