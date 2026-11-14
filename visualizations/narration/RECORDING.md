# Recording the narration

The film (`HackTheD1`) is timed to its voice lines. It currently uses a robot voice (macOS `say`) as a placeholder. Record your own and the film re-times itself.

## How

1. Record each line below as its own file, named after its id: `public/voiceover/<id>.wav` (for example `public/voiceover/04-getting-in.wav`). Any phone or laptop mic works; record in a quiet room, about 20 cm from the mic. Leave ~0.2 s of silence at the start and end, no more.
2. Run `node scripts/voiceover.mjs measure`. Recorded files take priority over the scratch ones; missing lines keep the scratch voice.
3. Check the total in Studio (top bar). Keep it under 3:00: aim for roughly the scratch durations below; the film adds at most a few seconds of padding per scene.
4. Render: `npx remotion render src/index.js HackTheD1 out/hack-the-d1.mp4`.

Speak a little faster than feels natural, with energy. Mixing voices is fine and adds character: for example, one person does the story lines and another the safety lines (07–10).

Optional: drop a royalty-free track at `public/music.mp3` and run `measure` again; it plays quietly under the voice.

## Lines

**01-cold-open** · scratch 7.1 s  
> This morning, a seventy-four kilo disinfection robot drove itself to its goal. It was never built to take orders from us.

**02-title** · scratch 3.6 s  
> We're Verspätete Rädfahrer, and this is how we hacked the D1.

**03-closed-box** · scratch 9.6 s  
> The Hyundai D1 is sold as a closed box. Our track had five levels: get in, unlock every sensor, take the wheel, navigate, and answer the door.

**04-getting-in** · scratch 14.8 s  
> Getting in was the first wall. USB from our laptop showed no device at all. So we used the robot's own touchscreen as a terminal, gave it internet through phone tethering, and had it open a reverse SSH tunnel to our server. Remote shell. No sudo.

**05-brain** · scratch 12.8 s  
> Inside, we found a networked brain: an Ubuntu display computer, and an internal controller running the ROS 1 master, the motor driver and the laser. We mapped the whole vendor graph before sending a single motion command.

**06-sensors** · scratch 15.0 s  
> We ran ROS 2 Humble rootless on the display computer, with a one-way bridge from the vendor graph. Laser, odometry, IMU, the rear camera, eight air-quality sensors: thirteen topics passed a live check. Two depth cameras never sent a frame.

**07-drive-gate** · scratch 13.4 s  
> Then, movement. Every command goes through our drive gate. It starts disarmed, clamps the speed, and drops to zero a quarter of a second after the last command. An independent watchdog cuts the motors if anything goes stale.

**08-mission-log** · scratch 8.1 s  
> Every drive ran as a supervised session, with a person on the red stop. Twenty-five sessions. Many of them were stopped by our own guards.

**09-radar** · scratch 7.9 s  
> The laser guard stopped us fourteen times. And three of those? The robot was seeing its own bracket. We measured it, and masked it.

**10-watchdog** · scratch 5.8 s  
> We also killed the drive software on purpose. The watchdog tripped in a hundred and sixty milliseconds.

**11-footage** · scratch 8.0 s  
> Then came SLAM Toolbox for a live map, and Nav2 for planning. Here's the robot driving itself to a bottle that stands in for the front door.

**12-replay** · scratch 9.8 s  
> And this is a logged run from the robot's point of view. Live laser scans, the Nav2 plan, the path it drove. Ten seconds of autonomous driving. Goal reached.

**13-debrief** · scratch 7.0 s  
> One point zero four metres. It stopped seventeen centimetres short, because the map shifted slightly during the drive.

**14-lessons** · scratch 12.7 s  
> What we learned: the vendor's ROS 1 graph was the real integration point. Published doesn't mean delivered. Motor power and motor enable are two different things. And a command timeout needs its own independent supervisor.

**15-status** · scratch 13.3 s  
> Demonstrated: access, a ROS 2 sensor bridge, supervised driving, and a completed Nav2 goal. Next: the real door, and the doorbell through Home Assistant. It's designed, but we had no credentials.

**16-outro** · scratch 7.0 s  
> No flashing. No cutting. Nothing replaced. Just ROS 2. We're Verspätete Rädfahrer. Thank you!

If you change a line, edit `narration/lines.json` too: captions come from it.
