"""Conservative checks for the mentor-supervised floor diagnostic."""
import math

def _missing_return(value):
    # SICK raw DIST=2 denotes an implausible sample, not a measured distance.
    return value==float('inf') or abs(value-.002)<=1e-6

def front_clearance(ranges, angle_min, increment, range_min, range_max, limit=.60):
    sector = [v for i,v in enumerate(ranges)
              if abs(angle_min+i*increment) <= math.pi/6]
    values = [v for v in sector if not math.isnan(v) and not math.isinf(v)
              and range_min <= v <= range_max]
    coverage = (0 < increment <= .05 and angle_min <= -math.pi/6 and
                angle_min+(len(ranges)-1)*increment >= math.pi/6)
    minimum = min(values) if values else None
    isolated_inf = True
    i=0
    while i<len(sector):
        v=sector[i]
        if not math.isnan(v) and not math.isinf(v) and range_min<=v<=range_max:
            i+=1; continue
        start=i
        while i<len(sector) and _missing_return(sector[i]): i+=1
        width=i-start
        if (width==0 or width>2 or width*increment>.015 or start==0 or i==len(sector) or
                not all(not math.isnan(n) and not math.isinf(n) and
                        range_min<=n<=range_max and n>=limit
                        for n in (sector[start-1],sector[i]))):
            isolated_inf=False; break
    missing_only=coverage and all(_missing_return(v) or (not math.isnan(v) and
        not math.isinf(v) and range_min<=v<=range_max) for v in sector)
    enough = bool(sector) and len(values)>=.95*len(sector)
    return dict(clear=coverage and len(values)>=10 and enough and isolated_inf
                and minimum>=limit, minimum=minimum, valid=len(values), total=len(sector),
                hard_stop=any(not math.isnan(v) and v<.5 and not _missing_return(v) for v in sector),missing_only=missing_only)

def pose_within_limit(initial, current):
    x,y,yaw = initial; xx,yy,yyaw = current
    delta = math.atan2(math.sin(yyaw-yaw), math.cos(yyaw-yaw))
    return math.hypot(xx-x,yy-y)<=.15 and abs(delta)<=.30


class ScanQualityGuard:
    """Near returns are immediate; only minor missing-return bursts get 200 ms."""
    def __init__(self): self.bad_since=None
    def stop(self, result, now):
        if (not result['missing_only'] or result['hard_stop'] or result['minimum'] is None or result['minimum']<.5 or
                not result['total'] or result['valid']<.95*result['total']):
            return True
        if result['clear']:
            self.bad_since=None
            return False
        if self.bad_since is None: self.bad_since=now
        return now<self.bad_since or now-self.bad_since>=.2
