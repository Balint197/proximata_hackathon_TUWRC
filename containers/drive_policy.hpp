#pragma once
#include <algorithm>
#include <cmath>
// Walking pace is ~1.4 m/s; these limits stay far below it (raised 14 Nov after floor tests).
constexpr double kMaxLinear = .20, kMaxAngular = .25;
struct DriveInput { double x, y, linear_z, angular_x, angular_y, z; };
struct DriveOutput { double x = 0, z = 0; };
class DrivePolicy {
  bool armed_ = false, stopped_ = true, have_stop_ = false, have_command_ = false;
  double stop_time_ = 0, command_time_ = 0;
  DriveOutput command_;
  bool stop_fresh(double now) const {
    return have_stop_ && !stopped_ && now >= stop_time_ && now - stop_time_ < .300;
  }
  void disarm() { armed_ = false; have_command_ = false; command_ = {}; }
public:
  bool armed() const { return armed_; }
  void stop(bool pressed, double now) {
    if (have_stop_ && (now < stop_time_ || now - stop_time_ >= .300)) disarm();
    stopped_ = pressed; have_stop_ = true; stop_time_ = now;
    if (pressed) disarm();
  }
  void arm(bool requested, double now) {
    disarm();
    if (requested && stop_fresh(now)) armed_ = true;
  }
  void command(const DriveInput & v, double now) {
    if (!armed_ || !stop_fresh(now) || (have_command_ &&
        (now < command_time_ || now - command_time_ >= .250))) { disarm(); return; }
    if (!std::isfinite(v.x) || !std::isfinite(v.y) || !std::isfinite(v.linear_z) ||
        !std::isfinite(v.angular_x) || !std::isfinite(v.angular_y) || !std::isfinite(v.z) ||
        v.y != 0 || v.linear_z != 0 || v.angular_x != 0 || v.angular_y != 0) {
      disarm(); return;
    }
    command_ = {std::max(-kMaxLinear, std::min(kMaxLinear, v.x)),
                std::max(-kMaxAngular, std::min(kMaxAngular, v.z))};
    command_time_ = now; have_command_ = true;
  }
  DriveOutput output(double now) {
    if (!stop_fresh(now) || (have_command_ &&
        (now < command_time_ || now - command_time_ >= .250))) disarm();
    return armed_ && have_command_ ? command_ : DriveOutput{};
  }
};
