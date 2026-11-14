# Challenge progress and submission checklist

This file distinguishes recorded demonstrations from remaining work.

| Level | Evidence | Remaining |
|---|---|---|
| Get in | Display/TX2 ROS 1 graph, vendor driver/services, GPIO power path documented in README | Motor controller protocol below ROS not reverse engineered |
| Sensors in ROS 2 | Live scan, odometry, IMU, rear RGB/depth, camera info/TF, eight air topics | Upper/lower cameras never deliver; air/depth units unverified |
| Drive in ROS 2 | Supervised sessions: 0.38 m and 0.98 m floor drives, 180 degree turns, guard stops; all sessions end powered off | Human teleop (gamepad/browser) |
| Navigate | SLAM map, live Nav2 (RPP) drove the base toward a named place (0.33 m) | One complete goal; real door is in another room |
| Answer door | Design in README | Home Assistant credentials, listener, camera display |

Submission requirements:

- [x] Hardware/setup README and evidence captures.
- [x] Root MIT license and environment template.
- [x] Local secret files and raw discovery archives ignored by Git.
- [x] Review all staged content for secrets before publishing (keyword/token scan, 14 Nov).
- [ ] Confirm public GitHub repository in the event organisation/folder.
- [ ] Add team/member names and written pitch.
- [ ] Record a three-minute video showing only actually demonstrated behavior.
- [ ] Submit links via the event form before code freeze.

No push, publication, or submission has been performed by these local changes.
The environment template is reference configuration; launchers do not load it
automatically. Home Assistant fields are reserved for the unfinished integration.
