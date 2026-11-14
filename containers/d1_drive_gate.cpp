// Separate from sensor bridge; default output cannot drive hardware.
#include "drive_policy.hpp"
#include <chrono>
#include <cstring>
#include <ros/ros.h>
#include <geometry_msgs/Twist.h>
#include <std_msgs/Bool.h>
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <std_msgs/msg/bool.hpp>
int main(int argc, char **argv) {
  bool hardware = false;
  if (argc == 2 && std::strcmp(argv[1], "--hardware") == 0) hardware = true;
  else if (argc != 1) return 2;
  ros::init(argc, argv, "d1_drive_gate", ros::init_options::NoRosout);
  rclcpp::init(argc, argv);
  ros::NodeHandle host;
  auto node = rclcpp::Node::make_shared("d1_drive_gate");
  DrivePolicy policy;
  auto now = [] {return std::chrono::duration<double>(
    std::chrono::steady_clock::now().time_since_epoch()).count();};
  auto out = host.advertise<geometry_msgs::Twist>(
    hardware ? "/cmd_vel" : "/d1/dry_run_cmd_vel", 1, false);
  auto stop = host.subscribe<std_msgs::Bool>("/robot/button/emergency_state", 1,
    [&](const std_msgs::Bool::ConstPtr &msg) {policy.stop(msg->data, now());});
  auto qos = rclcpp::QoS(1).durability_volatile();
  qos.lifespan(std::chrono::milliseconds(200));
  auto command = node->create_subscription<geometry_msgs::msg::Twist>("/cmd_vel", qos,
    [&](geometry_msgs::msg::Twist::ConstSharedPtr msg) {
      policy.command({msg->linear.x, msg->linear.y, msg->linear.z,
        msg->angular.x, msg->angular.y, msg->angular.z}, now());
    });
  auto arm = node->create_subscription<std_msgs::msg::Bool>("/d1/drive_arm", qos,
    [&](std_msgs::msg::Bool::ConstSharedPtr msg) {policy.arm(msg->data, now());});
  auto status = node->create_publisher<std_msgs::msg::Bool>("/d1/drive_armed", 1);
  RCLCPP_WARN(node->get_logger(), "Output: %s; disarmed; motor power is never enabled here",
    hardware ? "/cmd_vel (HARDWARE)" : "/d1/dry_run_cmd_vel");
  ros::WallRate rate(50);
  while (ros::ok() && rclcpp::ok()) {
    ros::spinOnce(); rclcpp::spin_some(node);
    const auto value = policy.output(now());
    geometry_msgs::Twist msg; msg.linear.x = value.x; msg.angular.z = value.z;
    out.publish(msg);
    std_msgs::msg::Bool state; state.data = policy.armed(); status->publish(state);
    rate.sleep();
  }
  geometry_msgs::Twist zero;
  for (int i = 0; i < 5 && ros::ok(); ++i) {out.publish(zero); ros::WallDuration(.02).sleep();}
  rclcpp::shutdown();
}
