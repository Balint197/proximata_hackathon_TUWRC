// Voiceover for the HackTheD1 film.
//
//   node scripts/voiceover.mjs scratch   # macOS `say` placeholder for every line without a recording
//   node scripts/voiceover.mjs measure   # measure public/voiceover/*.wav (+ public/music.mp3) -> src/data/voiceover.json
//
// To use your own voice, record each line in narration/lines.json and save it as
// public/voiceover/<id>.wav (any sample rate, mono or stereo), then run `measure`.
// Scratch files are named <id>.scratch.wav and are used only when <id>.wav is missing.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const lines = JSON.parse(fs.readFileSync(path.join(root, "narration/lines.json"), "utf8"));
const dir = path.join(root, "public/voiceover");
const mode = process.argv[2] ?? "measure";
const voice = process.env.VOICE ?? "Daniel";

if (mode === "scratch") {
  for (const { id, text } of lines) {
    const aiff = path.join(dir, `${id}.aiff`);
    execFileSync("say", ["-v", voice, "-r", "185", "-o", aiff, text.replaceAll("Rädfahrer", "Raadfahrer").replaceAll("Verspätete", "Fershpaytete")]);
    execFileSync("ffmpeg", ["-v", "error", "-y", "-i", aiff, "-ar", "48000", "-ac", "1", path.join(dir, `${id}.scratch.wav`)]);
    fs.rmSync(aiff);
  }
}

const out = lines.map(({ id, text }) => {
  const own = path.join(dir, `${id}.wav`);
  const file = fs.existsSync(own) ? `${id}.wav` : fs.existsSync(path.join(dir, `${id}.scratch.wav`)) ? `${id}.scratch.wav` : null;
  const seconds = file
    ? Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path.join(dir, file)]).toString())
    : 0;
  return { id, text, file: file && `voiceover/${file}`, seconds: Math.round(seconds * 100) / 100, scratch: Boolean(file?.includes(".scratch")) };
});
// Optional background music: public/music.mp3 (or .wav), ducked under the voice.
const music = ["music.mp3", "music.wav"].find((f) => fs.existsSync(path.join(root, "public", f))) ?? null;
fs.writeFileSync(path.join(root, "src/data/voiceover.json"), JSON.stringify({ music, lines: out }, null, 1));
const total = out.reduce((a, l) => a + l.seconds, 0);
console.log(out.map((l) => `${l.id.padEnd(16)} ${l.seconds.toFixed(1).padStart(5)} s ${l.scratch ? "(scratch)" : l.file ? "(recorded)" : "(missing)"}`).join("\n"));
console.log(`voice total ${total.toFixed(1)} s`);
