# Website verification

14 November 2026.

- Static source syntax and git whitespace checks passed.
- Design inspector: 0 FAIL, 0 WARN at 1440, 768 and 390px. All eight final screenshot sheets reviewed. Screenshots remain local in `.taste-skill/final/`.
- Real Chrome acceptance: play/pause, scrub to completion, 0.17m final gap, laser layer toggle, film modal, Escape dismissal, focus restoration and no horizontal overflow at 1440, 768 and 390px. No runtime exceptions.
- Reduced motion pauses background footage. Script-disabled page retains readable narrative, evidence links and fallback map.
- The connected Browser plugin reported no browsers; acceptance used the design skill's installed-Chrome driver instead.
- Lint has no failures. The two warnings are justified: timecode zero padding is a clock; “Unlock the sensors” is a genuine challenge level name.
- Film source is the existing `hack-the-d1-scratch-voice.mp4`, 179.82 seconds. Web encode is 1280px H.264/AAC, approximately 6.7 MB. Captions use the same line timings and scene overlap calculation.

Live deployment checks are appended after rollout.

Deployment notes: Coolify's GitHub App source expects `Balint197/proximata_hackathon_TUWRC` as its repository slug. A full URL produces a duplicated `github.com/https://github.com/...` clone path. Set the repository slug separately if a combined CLI update is rejected. No database edits were needed.

First rollout completed successfully at commit `78756df`. Coolify reports `finished`; the replacement nginx container reports `healthy`. HTTPS at `getriv.fun` serves the new Hack the D1 document. The old voice-battle deployment has been replaced.

Live checks on the first rollout: all three viewport acceptance runs passed over HTTPS; reduced-motion and script-disabled checks passed. The self-hosted film played in Chrome with its expected 179.82-second duration and caption track; nginx returned 206 for a video byte-range request. Keyboard End on the replay slider reached the 0.17m final state. Both apex and www hosts returned 200, and HTTP redirected to HTTPS.

Owner supplied the final YouTube URL during verification: https://www.youtube.com/watch?v=UzRv3MRT9EA. Replaced the temporary self-hosted scratch film with a click-loaded privacy-enhanced YouTube embed and an always-available direct link. The local muted robot clip remains. Removed unused scratch-film encode and VTT. The earlier scratch-film caveat in the critique is superseded by this supplied video. Full playback inside YouTube depends on their embedding policy; the direct link is always available.
