import data from "../data/sessions.json";
import { color } from "../theme";

export const OUTCOMES = {
  finished: { label: "Finished", tint: color.lime },
  guard: { label: "Guard stop", tint: color.amber },
  aborted: { label: "Aborted", tint: "#8fa3c4" },
  refused: { label: "Refused", tint: color.red },
};

export const sessions = data.sessions;
export const watchdog = data.watchdog;
export const counts = Object.fromEntries(Object.keys(OUTCOMES).map((k) => [k, sessions.filter((s) => s.outcome === k).length]));
export const guardTrips = sessions.filter((s) => s.guard);

export const GUARD_REASONS = {
  scan_obstacle_ahead: { label: "ahead", tint: color.amber },
  scan_obstacle_beside: { label: "beside", tint: color.orange },
  scan_obstacle_in_sweep_radius: { label: "in turning circle", tint: color.red },
};
