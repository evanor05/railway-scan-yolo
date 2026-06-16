import json
import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DroneStatusNode(Node):
    def __init__(self):
        super().__init__("drone_status_node")

        self.declare_parameter("drone_id", "pi-drone-01")
        self.declare_parameter("status_rate_hz", 1.0)

        self.drone_id = str(self.get_parameter("drone_id").value)
        status_rate_hz = max(float(self.get_parameter("status_rate_hz").value), 0.2)

        self.heartbeat_pub = self.create_publisher(String, "/drone/heartbeat", 10)
        self.status_pub = self.create_publisher(String, "/drone/status", 10)
        self.create_subscription(String, "/mission/command", self.on_command, 10)

        self.mission_state = "idle"
        self.battery = 96.0
        self.altitude_m = 12.0
        self.link_rssi_dbm = -48.0

        self.create_timer(1.0, self.publish_heartbeat)
        self.create_timer(1.0 / status_rate_hz, self.publish_status)
        self.get_logger().info("Drone status simulator ready")

    def on_command(self, msg):
        command = msg.data.strip().lower()
        if command in {"start", "pause", "resume", "return_home", "stop"}:
            self.mission_state = command
            self.get_logger().info(f"mission command: {command}")
        else:
            self.get_logger().warning(f"unknown mission command: {msg.data}")

    def publish_heartbeat(self):
        stamp = self.get_clock().now().to_msg()
        payload = {
            "drone_id": self.drone_id,
            "stamp": {"sec": stamp.sec, "nanosec": stamp.nanosec},
            "alive": True,
        }
        self.heartbeat_pub.publish(String(data=json.dumps(payload, ensure_ascii=True)))

    def publish_status(self):
        stamp = self.get_clock().now().to_msg()
        self.battery = max(self.battery - 0.01, 0.0)
        self.altitude_m += random.uniform(-0.04, 0.04)
        self.link_rssi_dbm += random.uniform(-0.8, 0.8)

        payload = {
            "drone_id": self.drone_id,
            "stamp": {"sec": stamp.sec, "nanosec": stamp.nanosec},
            "mission_state": self.mission_state,
            "battery_percent": round(self.battery, 2),
            "altitude_m": round(self.altitude_m, 2),
            "link_rssi_dbm": round(self.link_rssi_dbm, 1),
        }
        self.status_pub.publish(String(data=json.dumps(payload, ensure_ascii=True)))


def main(args=None):
    rclpy.init(args=args)
    node = DroneStatusNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
