import json
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class GroundStationMonitor(Node):
    def __init__(self):
        super().__init__("ground_station_monitor")

        self.declare_parameter(
            "alert_classes", "animal,motorcycle,person,rock,vehicle"
        )
        self.declare_parameter("log_path", "")

        alert_classes = str(self.get_parameter("alert_classes").value)
        self.alert_classes = {
            item.strip() for item in alert_classes.split(",") if item.strip()
        }

        log_path = str(self.get_parameter("log_path").value)
        self.log_path = Path(log_path).expanduser() if log_path else None
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.alert_pub = self.create_publisher(String, "/inspection/alerts", 10)
        self.create_subscription(String, "/inspection/detections", self.on_detections, 10)
        self.create_subscription(String, "/drone/status", self.on_status, 10)
        self.create_subscription(String, "/drone/heartbeat", self.on_heartbeat, 10)

        self.last_heartbeat_sec = None
        self.get_logger().info(
            "Ground monitor ready. Alert classes: "
            + ",".join(sorted(self.alert_classes))
        )

    def on_detections(self, msg):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError as exc:
            self.get_logger().warning(f"Bad detection JSON: {exc}")
            return

        detections = payload.get("detections", [])
        summary = [
            f"{det.get('class_name')}:{det.get('confidence')}"
            for det in detections
        ]
        self.get_logger().info(
            f"detections={payload.get('count', 0)} [{', '.join(summary)}]"
        )

        if self.log_path:
            with self.log_path.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(payload, ensure_ascii=True) + "\n")

        hit_classes = sorted(
            {
                str(det.get("class_name"))
                for det in detections
                if str(det.get("class_name")) in self.alert_classes
            }
        )
        if not hit_classes:
            return

        alert = {
            "level": "warning",
            "reason": "inspection_target_detected",
            "classes": hit_classes,
            "source": payload,
        }
        self.alert_pub.publish(String(data=json.dumps(alert, ensure_ascii=True)))
        self.get_logger().warning(f"ALERT: {', '.join(hit_classes)} detected")

    def on_status(self, msg):
        self.get_logger().info(f"status {msg.data}")

    def on_heartbeat(self, msg):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        self.last_heartbeat_sec = payload.get("stamp", {}).get("sec")


def main(args=None):
    rclpy.init(args=args)
    node = GroundStationMonitor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
