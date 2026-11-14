# Hack the D1 website

Public hackathon demonstration, deployed to https://getriv.fun.

A static website with no package install or build step. Run locally:

```sh
python3 -m http.server 4173 --directory website/public
```

Open http://localhost:4173. `website/Dockerfile` serves the same files with nginx, including video byte-range requests. Set the Coolify application's base directory to `/website`, build pack to Dockerfile and exposed port to `80`.

The site uses only project footage and telemetry. `public/assets/door-run.json` is copied from `visualizations/src/data/door-run.json`; the replay interpolates the recorded poses, speed and gap, and displays timestamped scans and plans. It is a recording, not a live robot control interface. Sensor calibration, physical door navigation and Home Assistant integration remain unverified or unfinished as described on the page.

`public/assets/hack-the-d1.mp4` is a 1280px H.264/AAC encode of the existing film (about 6.7 MB), with its current temporary synthetic voice. The standalone bottle clip is muted. Caption timing follows `visualizations/src/film/timeline.js`. Replace the web film and regenerate captions after a new narration render.

Hanken Grotesk is served locally under the SIL Open Font License; see `public/assets/Hanken-OFL.txt`. All photographs, footage and map visuals come from this repository; no stock or generated imagery, sample claims or invented testimonials are used.

## Deployment

The existing Coolify app UUID is `sj4we5npo80m4ujccemznchu`, previously named `voice-battle`. Repoint only this application to this public repository, branch `main`, base directory `/website`, and deploy. Its existing `getriv.fun` / `www.getriv.fun` routing and TLS remain managed by Coolify. Other VPS applications are outside this deployment.

```sh
coolify app update sj4we5npo80m4ujccemznchu \
  --name hack-the-d1 \
  --git-repository https://github.com/Balint197/proximata_hackathon_TUWRC \
  --git-branch main --base-directory /website --ports-exposes 80
coolify deploy uuid sj4we5npo80m4ujccemznchu
```

Deployment verification and visual critique are recorded in `docs/verification.md` and `docs/critique.md`. The optional `scripts/check-browser.mjs` acceptance check uses the local design skill's Chrome driver and is not a runtime dependency.
