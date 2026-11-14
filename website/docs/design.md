# Hack the D1 demonstration website

Audience: hackathon jury and visitors. Job: understand the achievement in five seconds, watch the film, inspect the recorded drive, open the source.

Subject inventory: Hyundai D1; 74kg disinfection robot; Verspätete Rädfahrer; TUWRC; 14 November 2026; inaccessible laptop USB; phone tether; reverse SSH through VPS; Codex CLI on the robot; rootless ROS 2; 13 delivered topics; 250ms gate timeout; independent 160ms watchdog experiment; bottle standing in for a door; 1.04m completed run; no Home Assistant credentials.

Argument and copy deck:
- Hack the D1. We turned a closed, 74 kg disinfection robot into a ROS 2 platform. With Codex running on the robot itself. Proof: actual bottle-run footage. Action: Watch the film.
- Replay the drive. A bottle stood in for the front door. Nav2 planned the route; the D1 drove 1.04 metres and reached its configured goal. Proof: recorded poses, scans, plan; scrub and play.
- A way into the machine. USB gave us nothing. Its touchscreen gave us a terminal. Phone tethering and a reverse SSH tunnel gave us remote access. Then Codex ran on the D1 itself. Proof: discovery records and actual robot pictures.
- Open software. Original hardware. Vendor ROS 1 to rootless ROS 2 Humble; one-way sensor bridge; independent supervised drive path. Proof: actual architecture and delivered topics.
- Built to stop. Disarmed start; speed clamp; 250ms command loss; 160ms watchdog test; human at red stop. Proof: drive records, code. Explicit common-host limitations.
- Four levels demonstrated. Doorbell next. Accurate five-level status; actual door and HA pending.
- Verspätete Rädfahrer. Hack the D1. Source, film, hackathon attribution.

Direction: The product performs, seed 458846166. Hanken Grotesk, bottle ink #0d2a1c, white #f7f7f7, grey #ebebeb, yellow #f6e016. Flat fields, square controls, equal gutters.
Idea: On this page, the D1's recorded bottle run becomes a working, scrubbable exhibit.
Live thing: laser/plan/odometry replay from the actual JSON capture, with play, scrub and visibility controls; fallback map and run facts remain readable without JS.

Plan review: a conventional robotics marketing page would give us a fictional dashboard and stock robot imagery. This page uses only actual footage, recorded data and source-supported claims. The characteristic 230-degree laser arc is data, never decoration.

Composition: nav / large title alongside portrait footage / full-width evidence replay / narrative split with two real frames / full field architecture / safety typography and proof links / progress list / large team-name close. At 390px each section stacks in reading order, replay remains thumb-operable.

Redraw/adaptations: original hero specified 80% empty space, incompatible with own footage and house fullness rules. Redrew once to frame split. Adapted frame geometry to real portrait video and put supporting sentence directly below title as required by house rules. Proof logo tiles and founder letter require nonexistent assets: use source evidence and challenge progress list instead. No invented portraits, logos or testimonials. No scroll scenes dealt.

Implementation: dependency-free static HTML/CSS/modules, nginx Dockerfile, Coolify on existing getriv application. Existing Remotion source and local edits are preserved. Compress own film below GitHub file limit; scratch voice identified next to video. No runtime secrets or APIs. Reuse existing app routing and TLS after local checks.

Validation: taste lint + production-equivalent static-server inspection at 1440, 768, 390; screenshots and written critique; keyboard and interactive replay/video checks; remote HTTPS and media range verification. Source-only commit pushed to the current repository; repoint only getriv application.
