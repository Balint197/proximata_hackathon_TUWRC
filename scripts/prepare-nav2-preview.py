"""Derive D1 preview parameters from the installed Humble defaults."""
from pathlib import Path
import yaml
source=Path('/opt/ros/humble/share/nav2_bringup/params/nav2_params.yaml')
config=yaml.safe_load(source.read_text())
def rewrite(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='use_sim_time': value[key]=False
            elif key=='odom_topic': value[key]='/robot/odom'
            elif key=='scan_topic' or key=='topic' and item=='/scan': value[key]='/robot/scan'
            else: rewrite(item)
    elif isinstance(value,list):
        for item in value: rewrite(item)
rewrite(config)
controller=config['controller_server']['ros__parameters']
controller.update(controller_frequency=10.,min_y_velocity_threshold=0.,odom_topic='/robot/odom')
controller['progress_checker'].update(required_movement_radius=.03,movement_time_allowance=20.)
controller['general_goal_checker'].update(xy_goal_tolerance=.10,yaw_goal_tolerance=.10)
controller['FollowPath'].update(max_vel_x=.05,max_speed_xy=.05,max_vel_theta=.08,
    acc_lim_x=.05,acc_lim_theta=.1,decel_lim_x=-.1,decel_lim_theta=-.2,
    vx_samples=10,vy_samples=1,vtheta_samples=10,xy_goal_tolerance=.10,
    trans_stopped_velocity=.01,linear_granularity=.025,debug_trajectory_details=False)
footprint='[[-0.29,-0.29],[-0.29,0.29],[0.29,0.29],[0.29,-0.29]]'
for name in ('local_costmap','global_costmap'):
    params=config[name][name]['ros__parameters']
    params.pop('robot_radius',None)
    if 'static_layer' in params: params['static_layer']['map_topic']='/map'
    params.update(footprint=footprint,footprint_padding=.02,transform_tolerance=.3)
    for layer in ('obstacle_layer','voxel_layer'):
        if layer in params:
            params[layer]['scan'].update(topic='/robot/scan',obstacle_min_range=.05,
                raytrace_min_range=.05,obstacle_max_range=3.,raytrace_max_range=3.5)
config['planner_server']['ros__parameters']['GridBased']['allow_unknown']=False
config['planner_server']['ros__parameters']['GridBased']['tolerance']=.05
config['bt_navigator']['ros__parameters'].update(
    default_nav_to_pose_bt_xml='/root/d1-tools/nav2/navigate_preview.xml',
    default_nav_through_poses_bt_xml='/root/d1-tools/nav2/navigate_through_preview.xml')
Path('/root/d1-tools/nav2/nav2_d1.yaml').write_text(yaml.safe_dump(config))
