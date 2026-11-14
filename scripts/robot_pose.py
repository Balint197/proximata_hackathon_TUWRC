import rclpy, math, json
from rclpy.time import Time
import tf2_ros
rclpy.init(); n=rclpy.create_node('pose_peek'); buf=tf2_ros.Buffer(); tf2_ros.TransformListener(buf,n)
import time; end=time.time()+5
while time.time()<end:
    rclpy.spin_once(n,timeout_sec=.1)
    try:
        t=buf.lookup_transform('map','base_link',Time()); q=t.transform.rotation
        print(json.dumps(dict(x=t.transform.translation.x,y=t.transform.translation.y,yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))))); break
    except Exception as e: pass
