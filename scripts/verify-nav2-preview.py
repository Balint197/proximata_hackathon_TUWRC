"""Activate preview nodes and request a global path; never sends a drive goal."""
import json
import math
import time
import rclpy
from rclpy.action import ActionClient
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener
from nav2_msgs.srv import ManageLifecycleNodes, GetCostmap
from nav2_msgs.action import ComputePathToPose
from lifecycle_msgs.srv import GetState
from lifecycle_msgs.msg import State
from action_msgs.msg import GoalStatus
rclpy.init()
node=rclpy.create_node('d1_nav2_preview_check')
def wait(future,seconds=30):
    end=time.monotonic()+seconds
    while not future.done() and time.monotonic()<end:
        rclpy.spin_once(node,timeout_sec=.05)
    assert future.done(),'operation timed out'
    return future.result()
try:
    assert not node.get_publishers_info_by_topic('/cmd_vel'),'real command publisher exists before preview startup'
    manager=node.create_client(ManageLifecycleNodes,'/d1_preview/d1_nav2_preview_manager/manage_nodes')
    assert manager.wait_for_service(timeout_sec=5),'preview manager missing'
    assert wait(manager.call_async(ManageLifecycleNodes.Request(command=ManageLifecycleNodes.Request.STARTUP))).success,'lifecycle startup failed'
    states={}
    for name in ('controller_server','planner_server','bt_navigator'):
        client=node.create_client(GetState,'/d1_preview/'+name+'/get_state')
        assert client.wait_for_service(timeout_sec=3)
        state=wait(client.call_async(GetState.Request())).current_state
        assert state.id==State.PRIMARY_STATE_ACTIVE,(name,state.label)
        states[name]=state.label
    buffer=Buffer(); listener=TransformListener(buffer,node)
    end=time.monotonic()+5
    while not buffer.can_transform('map','base_link',Time()) and time.monotonic()<end:
        rclpy.spin_once(node,timeout_sec=.05)
    transform=buffer.lookup_transform('map','base_link',Time()).transform
    q=transform.rotation
    yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
    costmap_client=node.create_client(GetCostmap,'/d1_preview/global_costmap/get_costmap')
    assert costmap_client.wait_for_service(timeout_sec=3)
    costmap=wait(costmap_client.call_async(GetCostmap.Request())).map
    meta=costmap.metadata
    origin=meta.origin.position
    rotation=meta.origin.orientation
    angle=math.atan2(2*(rotation.w*rotation.z+rotation.x*rotation.y),1-2*(rotation.y**2+rotation.z**2))
    target=(transform.translation.x+.5*math.cos(yaw),transform.translation.y+.5*math.sin(yaw))
    candidates=[]
    for index,cost in enumerate(costmap.data):
        if cost>=100: continue
        gx=(index%meta.size_x+.5)*meta.resolution
        gy=(index//meta.size_x+.5)*meta.resolution
        x=origin.x+gx*math.cos(angle)-gy*math.sin(angle)
        y=origin.y+gx*math.sin(angle)+gy*math.cos(angle)
        distance=math.hypot(x-transform.translation.x,y-transform.translation.y)
        if .4<=distance<=.75:
            candidates.append((math.hypot(x-target[0],y-target[1]),x,y))
    assert candidates,'no nearby free costmap goal'
    _,x,y=min(candidates)
    goal=ComputePathToPose.Goal(); goal.planner_id='GridBased'; goal.use_start=False
    goal.goal.header.frame_id='map'; goal.goal.header.stamp=node.get_clock().now().to_msg()
    goal.goal.pose.position.x=x; goal.goal.pose.position.y=y
    goal.goal.pose.orientation=q
    planner=ActionClient(node,ComputePathToPose,'/d1_preview/compute_path_to_pose')
    assert planner.wait_for_server(timeout_sec=5),'planner action missing'
    handle=wait(planner.send_goal_async(goal)); assert handle.accepted
    response=wait(handle.get_result_async())
    assert response.status==GoalStatus.STATUS_SUCCEEDED,response.status
    path=response.result.path
    assert len(path.poses)>2,('empty/trivial path',[(p.pose.position.x,p.pose.position.y) for p in path.poses])
    endpoint=path.poses[-1].pose.position
    assert math.hypot(endpoint.x-x,endpoint.y-y)<.10,'path misses requested goal'
    real_outputs=node.get_publishers_info_by_topic('/cmd_vel')
    assert not real_outputs,'unexpected ROS 2 hardware command publisher'
    preview=node.get_publishers_info_by_topic('/d1/nav2_preview_cmd_vel')
    assert any(info.node_name=='controller_server' and info.node_namespace=='/d1_preview' for info in preview),'preview remap missing'
    print(json.dumps(dict(lifecycle=states,goal=dict(x=goal.goal.pose.position.x,y=goal.goal.pose.position.y),
        path_poses=len(path.poses),path_frame=path.header.frame_id,
        real_cmd_vel_publishers=[],preview_output='/d1/nav2_preview_cmd_vel',
        limitation='Global path only; no NavigateToPose goal, no motor enable, no physical Nav2 navigation.'),indent=2))
finally:
    node.destroy_node(); rclpy.shutdown()
