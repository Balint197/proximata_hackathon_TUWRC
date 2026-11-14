"""Derive live D1 Nav2 parameters from the installed Humble defaults.

Output: /root/d1-tools/nav2/nav2_d1_live.yaml. Speeds stay at or below the drive
gate clamps (0.20 m/s, 0.25 rad/s); no reverse (the laser cannot see behind).
"""
from pathlib import Path
import yaml

source = Path('/opt/ros/humble/share/nav2_bringup/params/nav2_params.yaml')
config = yaml.safe_load(source.read_text())
SCAN = '/robot/scan_filtered'


def rewrite(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'use_sim_time': value[key] = False
            elif key == 'odom_topic': value[key] = '/robot/odom'
            else: rewrite(item)
    elif isinstance(value, list):
        for item in value: rewrite(item)


rewrite(config)
controller = config['controller_server']['ros__parameters']
controller.update(controller_frequency=10., min_y_velocity_threshold=0., odom_topic='/robot/odom',
                  failure_tolerance=1.0)
controller['progress_checker'].update(required_movement_radius=.10, movement_time_allowance=15.)
controller['general_goal_checker'].update(xy_goal_tolerance=.04, yaw_goal_tolerance=.25)
# Regulated Pure Pursuit: follows the global path and turns toward it at a fixed
# rate. DWB stalled here because it decayed in-place turns below the base's
# ~0.05 rad/s deadband (session 20261114T073216-nav2-door).
controller['FollowPath'] = dict(
    plugin='nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController',
    desired_linear_vel=.15, lookahead_dist=.6, min_lookahead_dist=.35, max_lookahead_dist=.9,
    lookahead_time=1.5, use_velocity_scaled_lookahead_dist=False,
    rotate_to_heading_angular_vel=.20, use_rotate_to_heading=True, rotate_to_heading_min_angle=.6,
    max_angular_accel=.8, transform_tolerance=.3, min_approach_linear_velocity=.06,
    approach_velocity_scaling_dist=.5, use_collision_detection=True,
    max_allowed_time_to_collision_up_to_carrot=1.5, use_regulated_linear_velocity_scaling=True,
    use_cost_regulated_linear_velocity_scaling=False, regulated_linear_scaling_min_radius=.9,
    regulated_linear_scaling_min_speed=.06, allow_reversing=False, max_robot_pose_search_dist=10.)
footprint = '[[-0.29,-0.29],[-0.29,0.29],[0.29,0.29],[0.29,-0.29]]'
for name in ('local_costmap', 'global_costmap'):
    params = config[name][name]['ros__parameters']
    params.pop('robot_radius', None)
    if 'static_layer' in params: params['static_layer']['map_topic'] = '/map'
    params.update(footprint=footprint, footprint_padding=.03, transform_tolerance=.5)
    params['inflation_layer'].update(inflation_radius=.50, cost_scaling_factor=6.)
    for layer in ('obstacle_layer', 'voxel_layer'):
        if layer in params:
            params[layer]['scan'].update(topic=SCAN, obstacle_min_range=.05, raytrace_min_range=.05,
                                         obstacle_max_range=3.5, raytrace_max_range=4.5,
                                         inf_is_valid=True)
# Busy hall: SLAM keeps people's legs as permanent marks, which blocked every
# path. Plan on live laser obstacles only (cleared again by raytracing); the
# SLAM map still provides localization (map frame, named places).
glob = config['global_costmap']['global_costmap']['ros__parameters']
glob['plugins'] = ['obstacle_layer', 'inflation_layer']
glob.update(track_unknown_space=False, rolling_window=True, width=14, height=14, update_frequency=2.)
local = config['local_costmap']['local_costmap']['ros__parameters']
local.update(width=4, height=4)
planner = config['planner_server']['ros__parameters']['GridBased']
planner.update(allow_unknown=True, tolerance=.25)
config['bt_navigator']['ros__parameters'].update(
    default_nav_to_pose_bt_xml='/root/d1-tools/nav2/navigate_preview.xml',
    default_nav_through_poses_bt_xml='/root/d1-tools/nav2/navigate_through_preview.xml')
Path('/root/d1-tools/nav2/nav2_d1_live.yaml').write_text(yaml.safe_dump(config))
print('wrote /root/d1-tools/nav2/nav2_d1_live.yaml')
