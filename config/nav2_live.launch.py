"""D1 Nav2 (live): planner, DWB controller, BT navigator + self-hit scan filter.

The controller publishes /cmd_vel, which is consumed ONLY by the D1 drive gate.
The gate is disarmed unless a supervised drive session is running and a goal
client has armed it, so this stack alone cannot move the robot.
"""
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml

NS = 'd1_nav'


def generate_launch_description():
    params = ParameterFile(RewrittenYaml(source_file='/root/d1-tools/nav2/nav2_d1_live.yaml',
                                         root_key=NS, param_rewrites={}, convert_types=True),
                           allow_substs=True)
    return LaunchDescription([
        ExecuteProcess(cmd=['python3', '/root/d1-tools/d1_scan_filter.py'], name='d1_scan_filter',
                       output='screen'),
        Node(package='nav2_controller', executable='controller_server', name='controller_server',
             namespace=NS, output='screen', parameters=[params],
             remappings=[('cmd_vel', '/cmd_vel')]),
        Node(package='nav2_planner', executable='planner_server', name='planner_server',
             namespace=NS, output='screen', parameters=[params]),
        Node(package='nav2_bt_navigator', executable='bt_navigator', name='bt_navigator',
             namespace=NS, output='screen', parameters=[params]),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='d1_nav2_manager', namespace=NS, output='screen', parameters=[dict(
                 use_sim_time=False, autostart=True, bond_timeout=0.0,
                 node_names=['controller_server', 'planner_server', 'bt_navigator'])]),
    ])
