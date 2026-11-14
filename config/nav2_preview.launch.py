"""Navigation preview: output cannot reach the hardware command adapter."""
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml

def generate_launch_description():
    params=ParameterFile(RewrittenYaml(source_file='/root/d1-tools/nav2/nav2_d1.yaml',
                                      root_key='d1_preview',param_rewrites={},convert_types=True),allow_substs=True)
    return LaunchDescription([
        Node(package='nav2_controller',executable='controller_server',name='controller_server',
             namespace='d1_preview',output='screen',parameters=[params],
             remappings=[('cmd_vel','/d1/nav2_preview_cmd_vel')]),
        Node(package='nav2_planner',executable='planner_server',name='planner_server',
             namespace='d1_preview',output='screen',parameters=[params]),
        Node(package='nav2_bt_navigator',executable='bt_navigator',name='bt_navigator',
             namespace='d1_preview',output='screen',parameters=[params]),
        Node(package='nav2_lifecycle_manager',executable='lifecycle_manager',
             name='d1_nav2_preview_manager',namespace='d1_preview',output='screen',parameters=[dict(
                 use_sim_time=False,autostart=False,
                 node_names=['controller_server','planner_server','bt_navigator'])])
    ])
