#!/usr/bin/env python3
"""Live acceptance check: required streams arrive with nonempty sensor payloads."""
import json
import time

import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, Imu, LaserScan
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64


def main():
    rclpy.init()
    node = rclpy.create_node('d1_sensor_acceptance')
    expected = {
        '/robot/scan': LaserScan,
        '/robot/odom': Odometry,
        '/robot/imu/data': Imu,
        '/camera_back/rgb/image_raw': Image,
        '/camera_back/depth/image_rect_raw': Image,
    }
    expected.update(('/disinfection/' + name, Float64) for name in
                    ('pm10', 'pm25', 'pm100', 'o3', 'co2', 'tvoc',
                     'temperature', 'humidity'))
    counts = dict.fromkeys(expected, 0)
    samples = {}

    def receive(topic, message):
        if isinstance(message, Image) and not (message.width and message.height and message.data):
            return
        if isinstance(message, LaserScan) and not message.ranges:
            return
        counts[topic] += 1
        samples[topic] = message

    subscriptions = [node.create_subscription(
        cls, topic, lambda message, topic=topic: receive(topic, message),
        qos_profile_sensor_data) for topic, cls in expected.items()]
    start = time.monotonic()
    try:
        while time.monotonic() - start < 15:
            rclpy.spin_once(node, timeout_sec=0.2)
        for topic in expected:
            record = {'topic': topic, 'messages': counts[topic]}
            sample = samples.get(topic)
            if hasattr(sample, 'header'):
                record['frame'] = sample.header.frame_id
                record['stamp'] = sample.header.stamp.sec + sample.header.stamp.nanosec / 1e9
            if isinstance(sample, Float64):
                record['value'] = sample.data
            print(json.dumps(record))
        missing = [topic for topic, count in counts.items() if count < 2]
        if missing:
            raise RuntimeError('Fewer than two messages received: ' + ', '.join(missing))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
