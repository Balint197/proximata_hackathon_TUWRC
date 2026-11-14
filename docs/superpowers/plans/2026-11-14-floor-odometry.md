# Supervised Floor Odometry Implementation Plan

> For agentic workers: use superpowers:executing-plans inline.

**Goal:** Verify bounded straight ROS 2 drive and odometry on the floor before Nav2.
**Architecture:** Reuse the reviewed gate/watchdog and diagnostic harness, adding scan/pose checks.
**Tech Stack:** ROS Melodic supervisor, rootless ROS 2 stimulus, Python unit tests.
**Spec:** tuwrc-d1-brief.md plus user confirmation of mentor, marked area, disinfection disconnected and hand on stop.

## Global Constraints
No Nav2 goal or autonomous trajectory. Initial forward clearance60cm; near return50cm stops. Limit odometry displacement15cm/yaw0.30rad, stale scan/odom300ms. Fixed.05m/s stimulus: first.8s, second2s. Independent watchdog active, no automatic rearm.

## Review Focus
Mixed invalid rays must not create false clearance; abort must terminate command sources before blocking cleanup; missing publisher registrations must not bypass live-publisher preflight.

## Tasks
- [x] Test/implement clearance and pose checks; preserve stop supervision and bounded cleanup.
- [x] Review and fix abort ordering: kill stimulus, trip watchdog, kill adapter, then concurrent bounded disable requests.
- [x] Confirm first brief floor command and record operator corroboration.
- [ ] Record longer floor diagnostic and assess odometry without claiming physical scale calibration.

## Execution ledger
- Initial passive front minimum.288m; no motion until user cleared area. Later1.26m valid clearance.
- Review fixed sparse-valid-ray acceptance and blocking cleanup race via RED/GREEN tests.
- Crashed owned-node registrations removed only after unreachable endpoints confirmed; live/unexpected publishers continue blocking.
- First powered floor command lasted.52s before scan-quality abort; odometry advanced about6mm. User confirmed short forward movement. Final powerfalse and velocityzero.
- Ruling: distinguish short missing-return bursts from actual near returns; minor recognized gaps may last200ms, but near valid readings, NaN, other invalid values, missing coverage and major data loss stop immediately.
- A later raw.002m return is below declared.05m range minimum. SICK telegram spec identifies DIST=2 as implausible measurement (not distance). Treating ROS.002 as this reserved code is an inference consistent with millimetre-to-metre conversion; vendor parser source is unavailable. No invalid ray is treated as a measured free distance.
- Ruling: require>=95% finite forward coverage; permit only+inf and exact.002±1e-6 as missing, bounded to2adjacent rays with angulargap<=.015rad and finite clear bracketneighbors. Larger/persistent gaps failclosed. This is a supervised diagnostic filter, not a certified safety system.
- Composed NaN-to-quality-guard regression failed then passed after explicit missing-only classification; full28-test suite passes. Independent review found no remainingCritical/Important implementation findings, assuming supplied SICK/ROS mapping.

Source: [SICK telegram specification, reserved DIST values, pages109–110](https://cdn.sick.com/media/docs/7/27/927/telegram_listing_telegram_listing_ranging_sensors_lms1xx_lms5xx_tim2xx_tim5xx_tim7xx_lms1000_mrs1000_mrs6000_nav310_ld_oem15xx_ld_lrs36xx_lms4000_lrs4000_multiscan100_en_im0045927.pdf).
