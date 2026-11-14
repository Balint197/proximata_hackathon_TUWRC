// One-way sensor bridge. No ROS 1 publishers, services, or command routes.
#include <chrono>
#include <string>
#include <vector>
#include <ros/ros.h>
#include <rclcpp/rclcpp.hpp>
#include <ros1_bridge/bridge.hpp>

int main(int argc, char ** argv)
{
  ros::init(argc, argv, "d1_sensor_bridge", ros::init_options::NoRosout);
  rclcpp::init(argc, argv);
  ros::NodeHandle ros1;
  auto ros2 = rclcpp::Node::make_shared("d1_sensor_bridge");
  std::vector<ros1_bridge::Bridge1to2Handles> handles;
  auto add = [&](const std::string & topic, const std::string & package,
      const std::string & message, bool latched = false) {
      auto qos = rclcpp::QoS(10);
      if (latched) {qos.transient_local();}
      handles.push_back(ros1_bridge::create_bridge_from_1_to_2(
        ros1, ros2, package + "/" + message, topic, 10,
        package + "/msg/" + message, topic, qos));
      RCLCPP_INFO(ros2->get_logger(), "ROS 1 -> ROS 2: %s", topic.c_str());
    };
  try {
    add("/robot/scan", "sensor_msgs", "LaserScan");
    add("/robot/odom", "nav_msgs", "Odometry");
    add("/robot/imu/data", "sensor_msgs", "Imu");
    add("/camera_back/rgb/image_raw", "sensor_msgs", "Image");
    add("/camera_back/depth/image_rect_raw", "sensor_msgs", "Image");
    add("/camera_back/rgb/camera_info", "sensor_msgs", "CameraInfo");
    add("/camera_back/depth/camera_info", "sensor_msgs", "CameraInfo");
    for (const auto * name : {"pm10", "pm25", "pm100", "o3", "co2", "tvoc",
        "temperature", "humidity"})
    {
      add(std::string("/disinfection/") + name, "std_msgs", "Float64");
    }
    add("/tf", "tf2_msgs", "TFMessage");
    add("/tf_static", "tf2_msgs", "TFMessage", true);
    ros::AsyncSpinner spinner(2);
    spinner.start();
    rclcpp::executors::SingleThreadedExecutor executor;
    while (ros::ok() && rclcpp::ok()) {
      executor.spin_node_once(ros2, std::chrono::milliseconds(100));
    }
  } catch (const std::exception & error) {
    RCLCPP_ERROR(ros2->get_logger(), "%s", error.what());
    return 1;
  }
  rclcpp::shutdown();
  return 0;
}
