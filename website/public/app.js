const $ = (s) => document.querySelector(s);
const reduced = matchMedia("(prefers-reduced-motion: reduce)");
const hero = $("#hero-video");
const toggle = $(".media-toggle");
function setHero(playing) {
  if (playing) hero.play().catch(() => {});
  else hero.pause();
  toggle.textContent = playing ? "Pause" : "Play";
  toggle.setAttribute(
    "aria-label",
    `${playing ? "Pause" : "Play"} background video`,
  );
}
if (reduced.matches) setHero(false);
toggle.addEventListener("click", () => setHero(hero.paused));
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    hero.pause();
  } else if (toggle.textContent === "Pause" && !reduced.matches)
    hero.play().catch(() => {});
});
const dialog = $("#film-dialog"),
  film = $("#film");
let opener;
for (const button of document.querySelectorAll(".watch"))
  button.addEventListener("click", () => {
    opener = button;
    dialog.showModal();
    document.body.style.overflow = "hidden";
    hero.pause();
    film.src =
      "https://www.youtube-nocookie.com/embed/UzRv3MRT9EA?autoplay=1&rel=0";
  });
$("#close-film").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (e) => {
  if (
    e.target === dialog &&
    (e.clientX < dialog.getBoundingClientRect().left ||
      e.clientX > dialog.getBoundingClientRect().right ||
      e.clientY < dialog.getBoundingClientRect().top ||
      e.clientY > dialog.getBoundingClientRect().bottom)
  )
    dialog.close();
});
dialog.addEventListener("close", () => {
  film.removeAttribute("src");
  document.body.style.overflow = "";
  opener?.focus();
  if (toggle.textContent === "Pause" && !reduced.matches)
    hero.play().catch(() => {});
});
const observer = new IntersectionObserver(
  (entries) => {
    for (const entry of entries)
      if (entry.isIntersecting) {
        entry.target.classList.add("ready");
        observer.unobserve(entry.target);
      }
  },
  { threshold: 0.12 },
);
for (const item of document.querySelectorAll(
  ".section h2,.section-intro>p,.access-copy>p,.access-pictures figure,.arch-node,.bridge,.safety-number,.safety-proof,.progress-list>div,.film-section img,.film-section>div,.run-summary>div",
)) {
  item.classList.add("reveal");
  observer.observe(item);
}

const canvas = $("#scan"),
  ctx = canvas.getContext("2d");
const scrub = $("#scrub"),
  play = $("#replay-play");
let data,
  t = 0,
  playing = false,
  lastTime = 0,
  frame;
const colors = Object.fromEntries(
  ["dark", "ink", "scan", "plan", "path", "bg", "light"].map((k) => [
    k,
    getComputedStyle(document.documentElement)
      .getPropertyValue(`--${k}`)
      .trim(),
  ]),
);
function sample(series, time, index = 1) {
  if (time <= series[0][0]) return series[0][index];
  for (let i = 1; i < series.length; i++) {
    if (series[i][0] >= time) {
      const a = series[i - 1],
        b = series[i],
        f = (time - a[0]) / (b[0] - a[0] || 1);
      return a[index] + (b[index] - a[index]) * f;
    }
  }
  return series.at(-1)[index];
}
function nearest(series, time) {
  let result = series[0];
  for (const item of series) {
    if (item.t > time) break;
    result = item;
  }
  return result;
}
function draw() {
  if (!data) return;
  const rect = canvas.getBoundingClientRect(),
    ratio = Math.min(devicePixelRatio || 1, 2);
  canvas.width = rect.width * ratio;
  canvas.height = rect.height * ratio;
  ctx.scale(ratio, ratio);
  const w = rect.width,
    h = rect.height;
  ctx.fillStyle = colors.dark;
  ctx.fillRect(0, 0, w, h);
  // Capture coordinates are [lateral u, forward v]. Keep the map fixed throughout the replay.
  const scale = Math.min((w - 40) / 5.7, (h - 90) / 5.6),
    ox = w * 0.5,
    oy = h * 0.69;
  const xy = (u, v) => [ox + u * scale, oy - v * scale];
  const dot = (u, v, r, color) => {
    const [x, y] = xy(u, v);
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  };
  if ($("#show-scans").checked) {
    ctx.fillStyle = colors.scan;
    for (const [u, v] of nearest(data.scans, t).pts) {
      const [x, y] = xy(u, v);
      ctx.fillRect(x - 1.3, y - 1.3, 2.6, 2.6);
    }
  }
  if ($("#show-plan").checked && t >= data.plans[0].t) {
    const plan = nearest(data.plans, t);
    ctx.strokeStyle = colors.plan;
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    plan.pts.forEach(([u, v], i) => {
      const [x, y] = xy(u, v);
      if (i) ctx.lineTo(x, y);
      else ctx.moveTo(x, y);
    });
    ctx.stroke();
    ctx.setLineDash([]);
  }
  ctx.strokeStyle = colors.path;
  ctx.lineWidth = 3;
  ctx.beginPath();
  let started = false;
  for (const [pt, u, v] of data.poses) {
    if (pt > t) break;
    const [x, y] = xy(u, v);
    if (started) ctx.lineTo(x, y);
    else {
      ctx.moveTo(x, y);
      started = true;
    }
  }
  ctx.stroke();
  const u = sample(data.poses, t, 1),
    v = sample(data.poses, t, 2),
    yaw = sample(data.poses, t, 3),
    [rx, ry] = xy(u, v);
  const [gx, gy] = xy(...data.goal);
  ctx.strokeStyle = colors.plan;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(gx, gy, 9, 0, Math.PI * 2);
  ctx.stroke();
  const [bx, by] = xy(...data.bottle);
  ctx.fillStyle = colors.bg;
  ctx.fillRect(bx - 3, by - 7, 6, 14);
  ctx.font = '14px "Hanken Grotesk", sans-serif';
  ctx.fillText("Bottle", bx + 14, by - 5);
  ctx.fillStyle = colors.plan;
  ctx.fillText("Goal", gx + 17, gy + 5);
  ctx.save();
  ctx.translate(rx, ry);
  ctx.rotate(yaw);
  const side = 0.58 * scale;
  ctx.fillStyle = colors.ink;
  ctx.strokeStyle = colors.path;
  ctx.lineWidth = 2;
  ctx.fillRect(-side / 2, -side / 2, side, side);
  ctx.strokeRect(-side / 2, -side / 2, side, side);
  ctx.beginPath();
  ctx.moveTo(0, -side / 2 - 9);
  ctx.lineTo(-5, -side / 2 + 2);
  ctx.lineTo(5, -side / 2 + 2);
  ctx.closePath();
  ctx.fillStyle = colors.plan;
  ctx.fill();
  ctx.restore();
  dot(u, v, 3, colors.bg);
  ctx.fillStyle = colors.light;
  ctx.font = '14px "Hanken Grotesk", sans-serif';
  ctx.fillText("Start", ox + sideOffset(), oy + 32);
  const bar = scale;
  ctx.fillRect(24, 28, bar, 3);
  ctx.fillText("1 m", 24, 51);
  $("#elapsed").textContent = `${t.toFixed(1)} s`;
  $("#speed").textContent =
    `${Math.max(0, sample(data.speed, t)).toFixed(2)} m/s`;
  $("#gap").textContent = `${sample(data.gap, t).toFixed(2)} m`;
  $("#timecode").textContent =
    `0:${Math.floor(t).toString().padStart(2, "0")} / 0:13`;
  const status =
    t >= data.duration - 0.05
      ? "Goal reached · motors off"
      : playing
        ? "Replaying recorded run"
        : "Recorded telemetry";
  if ($("#run-status").textContent !== status)
    $("#run-status").textContent = status;
}
function sideOffset() {
  return 24;
}
function setPlaying(value) {
  playing = value;
  play.textContent = value ? "Pause" : "Play run";
  lastTime = 0;
  cancelAnimationFrame(frame);
  if (value) frame = requestAnimationFrame(tick);
  draw();
}
function tick(now) {
  if (!playing) return;
  if (lastTime) t += Math.min((now - lastTime) / 1000, 0.1);
  lastTime = now;
  if (t >= data.duration) {
    t = data.duration;
    setPlaying(false);
  } else frame = requestAnimationFrame(tick);
  scrub.value = t;
  draw();
}
play.addEventListener("click", () => {
  if (t >= data.duration) t = 0;
  setPlaying(!playing);
});
scrub.addEventListener("input", () => {
  setPlaying(false);
  t = Number(scrub.value);
  draw();
});
for (const input of document.querySelectorAll(".layers input"))
  input.addEventListener("change", draw);
new ResizeObserver(draw).observe(canvas);
document.addEventListener("visibilitychange", () => {
  if (document.hidden && playing) setPlaying(false);
});
fetch("/assets/door-run.json")
  .then((r) => {
    if (!r.ok) throw Error("Replay unavailable");
    return r.json();
  })
  .then((d) => {
    data = d;
    scrub.max = d.duration;
    scrub.disabled = false;
    play.disabled = false;
    play.textContent = "Play run";
    draw();
  })
  .catch(() => {
    play.textContent = "Replay unavailable";
    $("#run-status").textContent = "See the session record below";
    canvas.replaceWith(
      Object.assign(document.createElement("img"), {
        src: "/assets/map.png",
        alt: "Map of the recorded Nav2 bottle run",
      }),
    );
  });
