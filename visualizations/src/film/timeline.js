import voiceover from "../data/voiceover.json";

export const FPS = 30;
export const TRANSITION = 9; // frames of overlap between scenes
const TAIL = 0.5; // seconds of air after each line

// min: shortest the visuals need (s); delay: when the line starts inside the scene (s).
const PLAN = {
  "01-cold-open": { min: 8, delay: 0.4 },
  "02-title": { min: 4.2, delay: 0.5 },
  "03-closed-box": { min: 9, delay: 0.3 },
  "04-getting-in": { min: 12, delay: 0.3 },
  "05-brain": { min: 10, delay: 0.3 },
  "06-sensors": { min: 10, delay: 0.3 },
  "07-drive-gate": { min: 10, delay: 0.3 },
  "08-mission-log": { min: 7.5, delay: 0.4 },
  "09-radar": { min: 8.5, delay: 0.3 },
  "10-watchdog": { min: 5.5, delay: 0.3 },
  "11-footage": { min: 11.4, delay: 0.3 },
  "12-replay": { min: 17, delay: 3.0 },
  "13-debrief": { min: 4.6, delay: 0.4 },
  "14-lessons": { min: 9, delay: 0.3 },
  "15-status": { min: 9, delay: 0.3 },
  "16-outro": { min: 8.5, delay: 0.6 },
};

export const scenes = voiceover.lines.map((line) => {
  const { min, delay } = PLAN[line.id];
  const seconds = Math.max(min, delay + line.seconds + TAIL);
  return { ...line, delay, frames: Math.ceil(seconds * FPS) + TRANSITION };
});

export const music = voiceover.music;
export const totalFrames = scenes.reduce((a, s) => a + s.frames, 0) - TRANSITION * (scenes.length - 1);
export const scene = (id) => scenes.find((s) => s.id === id);
