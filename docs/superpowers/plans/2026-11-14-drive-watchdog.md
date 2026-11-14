# Independent Drive Watchdog Implementation Plan

> For agentic workers: use superpowers:executing-plans inline.

**Goal:** Disable motors independently when adapter output disappears.
**Architecture:** Pure Python policy plus separate ROS 1 runtime in rootless ROS One.
**Tech Stack:** Python 3 unittest, rospy, standard ROS messages/SetBool services.
**Spec:** docs/superpowers/specs/2026-11-14-drive-watchdog-design.md

## Global Constraints
No power-enable calls; default dry-run. Adapter 150 ms, status 300 ms,
zero-after-motion 350 ms. Only /d1_drive_gate refreshes command freshness.
Trips latch until explicit restart; startup while power on must trip.

## Review Focus
Vendor self-publication, invalid commands, stale stop/power, delayed callbacks,
blocked service calls and failure recovery must not bypass disable behavior.

## Tasks
- [x] Test policy startup, identity, expiry, zero-after-motion, invalid input and latching RED then GREEN.
- [x] Add separate runtime and launcher; exercise transport on private ROS master with fake disable services, including one blocked service.
- [x] Review, then repeat supervised stand process-loss test with supervisor active and record timing and final power/feedback.

## Execution ledger
- Initial policy RED missing module, GREEN nine tests. Isolated runtime passed default dry-run and hardware-mode fake services, including blocked motor-disable RPC.
- Independent review: no critical/important findings. Minor deferred: continuing vendor publications are unit-covered but not generated during transport test.
- First stand attempt safely tripped on stop_stale before any command: GPIO power RPCs introduce about 0.5 s stop/power publication gaps.
- Ruling: use explicit prepared/off then activated/on startup; reject nonzero preactivation and expire preparation at 5 s. This handles the measured relay initialization gap without widening active freshness limits. Wrong startup ordering trips instead of enabling motion.
- Added failing two-phase startup tests and power-loss latching test, then implemented. Updated whole policy suite: 12 tests pass.
- Host full unittest initially collected the ROS-only transport utility and failed on missing host Python3 ROS dependencies; renamed it as an integration utility and retained its explicit rootless test launcher. Full host suite now passes.

- Review Important: post-GPIO-RPC enable race. Fixed with safe_to_enable admission function and a regression test (missing function RED -> GREEN); harness checks abort, live process, trip/prepared state and fresh stop/status before enable.
- Second stand preflight refused a dead watchdog registration; only unreachable owned node registrations were removed. Clean shutdown now requests both ROS nodes before stopping wrappers.
- Stand result: trip 159 ms, zero 159 ms, live ui_srv_call false 193 ms after adapter kill, before harness cleanup at 678 ms. GPIO-off telemetry arrived 763 ms after kill and overlapped cleanup; harness aborted on the GPIO publication gap. No physical stopping latency claimed.
- Runtime shutdown regression: healthy shutdown emitted no disable calls (RED); added pre-close shutdown hook and closed-topic handling; isolated healthy-shutdown test GREEN.
- Final suite: 13 Python policy/startup tests and C++ adapter policy pass; isolated transport dryrun, blocked-RPC adapter loss and healthy shutdown all pass. Fresh power false, live controllable result false and zero actual velocity verified. No floor motion.
- Deferred minor remains: continuing vendor publications are covered by policy unit tests, not a separate live transport publisher in the integration test.
