#include "../containers/drive_policy.hpp"
#include <cassert>
#include <limits>
int main() {
  DrivePolicy p;
  assert(p.output(0).x == 0);
  p.arm(true, 0); assert(!p.armed());
  p.stop(false, 1); p.arm(true, 1); assert(p.armed());
  assert(p.output(1).x == 0);
  p.command({1,0,0,0,0,-1}, 1);
  assert(p.output(1).x == kMaxLinear && p.output(1).z == -kMaxAngular);
  assert(p.output(1.251).x == 0 && !p.armed());
  p.stop(false, 2); p.arm(true, 2); assert(p.output(2).x == 0);
  p.command({.05,0,0,0,0,.04}, 2);
  p.stop(true, 2.01); p.stop(false, 2.02);
  assert(!p.armed() && p.output(2.02).x == 0);
  p.arm(true, 3); assert(!p.armed());
  p.stop(false, 3); p.arm(true, 3);
  p.command({std::numeric_limits<double>::quiet_NaN(),0,0,0,0,0},3);
  assert(!p.armed() && p.output(3).x == 0);
  p.arm(true, 3); p.command({0,1,0,0,0,0},3); assert(!p.armed());
  p.arm(true, 3); p.command({0,0,0,0,0,std::numeric_limits<double>::infinity()},3);
  assert(!p.armed());
  p.arm(true,3); p.command({.05,0,0,0,0,0},3.2);
  assert(p.output(3.301).x == 0 && !p.armed());
  p.stop(false,4); p.arm(true,4); p.command({.05,0,0,0,0,0},4);
  p.arm(false,4); assert(p.output(4).x == 0);
  // A callback arriving after a scheduling gap must not bypass timeout latching.
  p.stop(false,5); p.arm(true,5); p.command({.05,0,0,0,0,0},5);
  p.stop(false,5.26); p.command({.05,0,0,0,0,0},5.26);
  assert(!p.armed() && p.output(5.26).x == 0);
  p.stop(false,6); p.arm(true,6); p.command({.05,0,0,0,0,0},6);
  p.stop(false,6.31); p.command({.05,0,0,0,0,0},6.31);
  assert(!p.armed() && p.output(6.31).x == 0);
}
