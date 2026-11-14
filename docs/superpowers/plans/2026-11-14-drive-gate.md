# Drive Gate Implementation Plan

> For agentic workers: use superpowers:executing-plans for inline execution.

**Goal:** Add a disarmed-by-default bounded ROS 2 to ROS 1 drive adapter.
**Architecture:** Pure C++ policy with a separate dual-ROS executable; sensor bridge unchanged.
**Tech Stack:** C++14, ROS One roscpp, ROS 2 Humble rclcpp.
**Spec:** docs/superpowers/specs/2026-11-14-drive-gate-design.md

## Global Constraints
No motor power/enable services; no hardware launch during development. Limits 0.10 m/s and 0.08 rad/s; 250 ms command timeout; 300 ms stop-status timeout; 50 Hz output. Default dry-run output.

## Review Focus
- NaN/infinity and unsupported axes must stop and disarm.
- Stale status and stop presses must latch disarmed.
- Release must not resume motion without arming and a new command.
- ROS 1 self-published commands must never become inputs.
- Process death is outside in-process watchdog protection.

## Tasks
- [x] Add deterministic tests for startup, arming, limits, invalid commands, stale command/status and stop/release behavior; run RED then GREEN with a pure policy header.
- [x] Add dual-ROS executable and reproducible build/launch scripts; compile within existing rootless workspace.
- [x] Exercise dry-run transport, document evidence and remaining hardware watchdog test.

## Execution ledger
- Policy tests: initial missing-header failure, then pass; additional scheduling-gap timeout test failed its assertion, then passed after callback-side expiry checks.
- Ruling: use a standalone CMake target instead of changing ros1_bridge; installing Nav2 added message packages that make regenerating the broad bridge fail. Pin the three overlapping message CMake directories to Humble; ROS 1 dependencies resolve through pkg-config. Existing sensor executable remains running.
- First isolated transport test: ten phases passed, zero hardware commands. Final rebuilt test and review pending.

- Final rebuilt transport test: all ten phases passed; no hardware commands. Offline policy tests and shell syntax checks passed.
- Final independent review: no remaining critical/important findings; reviewer reproduced both timeout gaps as zero/disarmed.
- Fresh robot check: motor_enable=false, motor_power=False, emergency_state=False. No hardware adapter launched. Physical stand test awaits operator readiness.
