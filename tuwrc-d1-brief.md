# TUWRC — Hack the D1: Unlock a real robot

*No docs, no API, 24 hours. Every sensor you reach is yours.*

Most hackathon hardware fits in a backpack. The D1 is a full-size commercial service robot: we share everything we know about it, and the rest is yours to discover. Unlock every sensor and the drive, then prove it by making the D1 answer the door.

| Theme | Robotics and embodied AI |
|---|---|
| Track partner | TUWRC |
| Team size | 2–4 people |
| Prize | To be announced |
| Code freeze | Saturday, 14 November, 15:00 sharp |

## The Robot

The D1 is a self-driving disinfection robot that maps its surroundings with SLAM. It measures 58 × 58 × 129 cm and weighs 74 kg (Hyundai Robotics, CBP ruling N334856). Ubuntu already runs on its built-in display; everything below it, from the motor controller to the sensors, is undocumented. That is the hack.

| What you can unlock | What it gives you once you’re in |
|---|---|
| 2D laser scanner | Distance scans for mapping and obstacle detection |
| 3D camera | Depth images to run your own perception on |
| 8 air-quality sensors | Fine particles (3 sensors), ozone, CO₂, total VOCs, temperature, humidity |
| Drive base | Motion and odometry, once you find the motor controller |
| 10.1-inch touch display | Ubuntu, and room for your own interface |
| LED rings and segment display | Lights and digits you can take over |
| Voice interaction system | Listed by Hyundai; the hardware behind it is yours to find |

First clue: a US customs ruling describes the D1 as a controller, motor, battery, LiDAR and disinfection module, plus an upper application module holding the 3D camera and touch display.

## The Problem

Service robots like the D1 are closed boxes: built for one job and controlled through their vendor’s software. Yet a machine with a laser scanner, a 3D camera and eight air-quality sensors could do far more. Whoever gets full access turns it into an open platform, and works hands-on with commercial robot hardware that rarely makes it to a hackathon.

## The Challenge

Within the 24 hours of the hackathon, get full access to the D1. Find out how its controller, drive and sensors talk to each other, and take control of all of them through ROS 2. Then connect it to Home Assistant, so HOIV’s doorbell can call it to the door.

## What You’re Building

Each level is a demo on its own; go as far as you can.

Get in: map what talks to what inside the D1 (onboard computers, motor controller, sensor boards) and document every interface and protocol you find.

Unlock every sensor: live data from the laser scanner, the 3D camera and the air-quality sensors, published as ROS 2 topics.

Take the wheel: drive the base through /cmd_vel (a gamepad is fine), with odometry out and a stop that always works.

Navigate: build a map and send the D1 to a named spot (“door”) with Nav2.

Answer the door: a doorbell press in Home Assistant sends the D1 to the door, and the doorbell camera shows on its display.

Bonus: take over the LED rings and the segment display, track down the hardware behind the voice interaction system, or stream the air-quality data into Home Assistant.

A doorbell press reaches the D1 through Home Assistant and Nav2. Home Assistant reaches ROS 2 through a bridge of your choice (e.g. MQTT or its REST API); Nav2 plans with the driver’s odometry and laser scan.

No robot time right now? Build levels 4 and 5 against a simulated mobile robot (e.g. in Gazebo) and move them to the D1 once a driver exists.

## Data & Resources

The D1, with Ubuntu on its built-in display unit

HOIV’s doorbell, connected to a Home Assistant instance; credentials go out on Discord, not in this brief

A marked driving area with a door to drive to

Mentors who got Ubuntu running on the D1

### House Rules

The UV-C floor LEDs and the plasma module stay disconnected all event: UV-C harms eyes and skin.

First drive tests happen on a stand, wheels off the ground.

Whenever the D1 moves, one person has a hand on the stop; walking pace at most, inside the marked area only.

Read, sniff and log anything you like, but never flash firmware on any board.

Leave the D1 as you found it: nothing gets cut, drilled or pried open, and every cable goes back where it was.

Autonomous runs only with a mentor present.

## Demo & Pitch Expectations

Show the D1 live, as far up the levels as you got: ideally from a doorbell press to the robot at the door. Walk the jury through what you found inside the robot and which sensors you unlocked. [Pitch length]

### Out of Scope

Flashing firmware onto the D1’s boards

The disinfection functions (UV-C LEDs, plasma module)

A polished UI

## Judging Criteria

Scoring is out of 100 points.

| Category | Points | How it’s scored |
|---|---|---|
| A. Levels reached | 35 | 7 points per level, partial credit |
| B. Live demo | 25 | Jury |
| C. Safety | 20 | The stop always works; limits and house rules kept |
| D. Documentation | 20 | Hardware findings and a README the next team can build on |
| Total | 100 |  |

Hard fails: damaging the hardware, the D1 moving without a hand on the stop, switching on the UV-C LEDs or plasma module, or flashing firmware.

Tie-breakers: higher level reached, then the better safety score.

## Mentors & Jury

| Role | Who | Notes |
|---|---|---|
| Jury | Josef Nissim · Kyrill | Josef.nissim13@gmail.com · contact@kyrill.us — select the TUWRC Track Winner |

## Submission

A public GitHub repository with a README and a 3-minute demo video, via the hackathon’s submission form by code freeze. Everything else as in General Rules.
