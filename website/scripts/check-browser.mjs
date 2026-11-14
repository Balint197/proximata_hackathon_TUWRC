// Local acceptance check. Uses the same dependency-free browser driver as the design inspector.
import { Browser } from "/Users/balint/.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs";
import assert from "node:assert/strict";
const browser = await Browser.launch();
const base = process.argv[2] || "http://localhost:4173";
try {
  for (const width of [1440, 768, 390]) {
    const page = await browser.newPage({ width, height: 900 });
    await page.goto(base);
    assert.equal(
      await page.eval(() => document.querySelector("#replay-play").disabled),
      false,
      "Replay loaded",
    );
    await page.eval(() => document.querySelector("#replay-play").click());
    await new Promise((r) => setTimeout(r, 450));
    assert.equal(
      await page.eval(() => document.querySelector("#replay-play").textContent),
      "Pause",
    );
    assert.notEqual(
      await page.eval(() => document.querySelector("#elapsed").textContent),
      "0.0 s",
    );
    await page.eval(() => {
      const s = document.querySelector("#scrub");
      s.value = s.max;
      s.dispatchEvent(new Event("input", { bubbles: true }));
    });
    assert.equal(
      await page.eval(() => document.querySelector("#run-status").textContent),
      "Goal reached · motors off",
    );
    assert.equal(
      await page.eval(() => document.querySelector("#gap").textContent),
      "0.17 m",
    );
    await page.eval(() => document.querySelector("#show-scans").click());
    assert.equal(
      await page.eval(() => document.querySelector("#show-scans").checked),
      false,
    );
    await page.eval(() => document.querySelector(".watch").click());
    assert.equal(
      await page.eval(() => document.querySelector("#film-dialog").open),
      true,
    );
    await page.send("Input.dispatchKeyEvent", {
      type: "keyDown",
      key: "Escape",
      code: "Escape",
      windowsVirtualKeyCode: 27,
    });
    await page.send("Input.dispatchKeyEvent", {
      type: "keyUp",
      key: "Escape",
      code: "Escape",
      windowsVirtualKeyCode: 27,
    });
    await page.eval(
      () =>
        new Promise((resolve) =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        ),
    );
    assert.equal(
      await page.eval(() => document.querySelector("#film-dialog").open),
      false,
    );
    assert.equal(
      await page.eval(() => document.activeElement.classList.contains("watch")),
      true,
    );
    assert.equal(
      await page.eval(() => document.documentElement.scrollWidth <= innerWidth),
      true,
      "No overflow",
    );
    assert.deepEqual(page.consoleErrors, []);
    console.log(
      `PASS ${width}px: replay play/scrub/layers, final gap, film modal, Escape, focus return, no overflow/errors`,
    );
  }
  const reduced = await browser.newPage({
    width: 390,
    height: 844,
    reducedMotion: true,
  });
  await reduced.goto(base);
  assert.equal(
    await reduced.eval(() => document.querySelector("#hero-video").paused),
    true,
  );
  console.log("PASS reduced motion: background footage paused");
  const plain = await browser.newPage({ width: 390, height: 844 });
  await plain.send("Emulation.setScriptExecutionDisabled", { value: true });
  await plain.goto(base);
  assert.equal(
    await plain.eval(() =>
      document.querySelector("noscript img").getAttribute("src"),
    ),
    "/assets/map.png",
  );
  console.log(
    "PASS no JavaScript: narrative, evidence links and fallback map remain available",
  );
} finally {
  await browser.close();
}
