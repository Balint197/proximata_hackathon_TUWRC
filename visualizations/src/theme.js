import { loadFont as loadDisplay } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { Easing } from "remotion";

export const display = loadDisplay("normal", { weights: ["500", "700"], subsets: ["latin"] }).fontFamily;
export const mono = loadMono("normal", { weights: ["400", "700"], subsets: ["latin"] }).fontFamily;

export const color = {
  bg: "#04060c",
  panel: "rgba(10, 18, 34, 0.72)",
  line: "rgba(120, 200, 255, 0.18)",
  text: "#eaf6ff",
  muted: "#7d8fa8",
  cyan: "#5cf2ff",
  blue: "#3d7bff",
  orange: "#ff7a2f",
  lime: "#b8ff3c",
  red: "#ff3b5c",
  amber: "#ffc23d",
};

export const outExpo = Easing.bezier(0.16, 1, 0.3, 1);
export const inOutCubic = Easing.bezier(0.65, 0, 0.35, 1);
export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" };

// Linear interpolation inside a [t, ...values] series sorted by t.
export const sample = (series, t, index = 1) => {
  if (t <= series[0][0]) return series[0][index];
  for (let i = 1; i < series.length; i++) {
    const [ta] = series[i - 1];
    const [tb] = series[i];
    if (t <= tb) {
      const k = (t - ta) / (tb - ta || 1);
      return series[i - 1][index] + (series[i][index] - series[i - 1][index]) * k;
    }
  }
  return series[series.length - 1][index];
};
