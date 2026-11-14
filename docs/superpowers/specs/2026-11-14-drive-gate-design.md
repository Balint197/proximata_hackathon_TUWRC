# ROS 2 drive gate

Approved direction: preserve vendor ROS 1 hardware drivers, add bounded ROS 2 control, then Nav2 and Home Assistant. This implementation does not enable hardware.

A separate dual-ROS process consumes ROS 2 /cmd_vel and publishes ROS 1 /cmd_vel. It never subscribes to ROS 1 commands, avoiding the vendor's self-publishing feedback loop. Default output goes to /d1/dry_run_cmd_vel; an explicit --hardware flag selects the hardware topic. An operator arms using ROS 2 /d1/drive_arm (Bool). Stop or stale status latches disarmed, requiring a fresh arm request after recovery. Arming clears previous commands.

Limits: linear x 0.10 m/s, angular z 0.08 rad/s. Reject nonfinite values and nonzero unsupported axes. Command timeout 250 ms, physical-stop status timeout 300 ms, monotonic clock, 50 Hz output. Stop status comes from vendor /robot/button/emergency_state. Startup is disarmed and no motor services are called. Hardware watchdog on process crash remains unproven and must be tested independently before floor use.

Alternatives: replacing the vendor driver would require undocumented protocol work; a generic bidirectional bridge lacks the command validation and avoids neither self-publication nor automatic restart. The separate gate is the chosen direction from the conversation.

Acceptance: deterministic offline policy tests; build; isolated ROS transport test with fake stop and command publishers, observing the dry-run output. No hardware motion in this implementation step.
