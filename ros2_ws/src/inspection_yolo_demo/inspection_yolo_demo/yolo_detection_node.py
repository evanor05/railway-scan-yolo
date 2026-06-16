import json
import time
from pathlib import Path

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String
from ultralytics import YOLO


IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def _source_value(raw_source):
    text = str(raw_source)
    if text.isdigit():
        return int(text)
    return text


def _image_paths(source):
    path = Path(str(source)).expanduser()
    if path.is_dir():
        return sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
        return [path]
    return []


class YoloDetectionNode(Node):
    def __init__(self):
        super().__init__("yolo_detection_node")

        self.declare_parameter("model_path", "yolo26n.pt")
        self.declare_parameter("source", "0")
        self.declare_parameter("conf", 0.35)
        self.declare_parameter("imgsz", 640)
        self.declare_parameter("device", "")
        self.declare_parameter("rate_hz", 5.0)
        self.declare_parameter("frame_id", "drone_camera")
        self.declare_parameter("publish_annotated", True)
        self.declare_parameter("loop_images", True)
        self.declare_parameter("max_det", 50)

        self.model_path = self.get_parameter("model_path").value
        self.source = self.get_parameter("source").value
        self.conf = float(self.get_parameter("conf").value)
        self.imgsz = int(self.get_parameter("imgsz").value)
        self.device = str(self.get_parameter("device").value)
        self.frame_id = str(self.get_parameter("frame_id").value)
        self.publish_annotated = bool(self.get_parameter("publish_annotated").value)
        self.loop_images = bool(self.get_parameter("loop_images").value)
        self.max_det = int(self.get_parameter("max_det").value)

        rate_hz = max(float(self.get_parameter("rate_hz").value), 0.1)
        self.model = YOLO(self.model_path)

        self.detection_pub = self.create_publisher(String, "/inspection/detections", 10)
        self.annotated_pub = self.create_publisher(
            CompressedImage, "/inspection/annotated_image/compressed", 10
        )

        self.image_paths = _image_paths(self.source)
        self.image_index = 0
        self.capture = None
        self.last_read_warning = 0.0

        if self.image_paths:
            self.get_logger().info(f"Using image source with {len(self.image_paths)} file(s)")
        else:
            self.capture = cv2.VideoCapture(_source_value(self.source))
            if not self.capture.isOpened():
                raise RuntimeError(f"Could not open video source: {self.source}")
            self.get_logger().info(f"Using video source: {self.source}")

        self.timer = self.create_timer(1.0 / rate_hz, self.on_timer)
        self.get_logger().info(
            f"YOLO model ready: {self.model_path}, conf={self.conf}, imgsz={self.imgsz}"
        )

    def on_timer(self):
        frame = self._read_frame()
        if frame is None:
            return

        started = time.perf_counter()
        predict_kwargs = {
            "source": frame,
            "conf": self.conf,
            "imgsz": self.imgsz,
            "max_det": self.max_det,
            "verbose": False,
        }
        if self.device:
            predict_kwargs["device"] = self.device

        result = self.model.predict(**predict_kwargs)[0]
        inference_ms = (time.perf_counter() - started) * 1000.0

        payload = self._result_to_payload(result, frame, inference_ms)
        self.detection_pub.publish(String(data=json.dumps(payload, ensure_ascii=True)))

        if self.publish_annotated:
            annotated = result.plot()
            ok, encoded = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                msg = CompressedImage()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = self.frame_id
                msg.format = "jpeg"
                msg.data = encoded.tobytes()
                self.annotated_pub.publish(msg)

    def _read_frame(self):
        if self.image_paths:
            if self.image_index >= len(self.image_paths):
                if not self.loop_images:
                    return None
                self.image_index = 0

            image_path = self.image_paths[self.image_index]
            self.image_index += 1
            frame = cv2.imread(str(image_path))
            if frame is None:
                self.get_logger().warning(f"Could not read image: {image_path}")
            return frame

        ok, frame = self.capture.read()
        if ok:
            return frame

        now = time.monotonic()
        if now - self.last_read_warning > 2.0:
            self.get_logger().warning("Video frame read failed")
            self.last_read_warning = now
        return None

    def _result_to_payload(self, result, frame, inference_ms):
        height, width = frame.shape[:2]
        stamp = self.get_clock().now().to_msg()
        names = result.names or getattr(self.model, "names", {})

        detections = []
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            xyxy = [float(v) for v in box.xyxy[0].tolist()]
            x1, y1, x2, y2 = xyxy
            detections.append(
                {
                    "class_id": class_id,
                    "class_name": str(names.get(class_id, class_id)),
                    "confidence": round(confidence, 4),
                    "bbox_xyxy": [round(v, 2) for v in xyxy],
                    "bbox_center_norm": [
                        round(((x1 + x2) / 2.0) / width, 5),
                        round(((y1 + y2) / 2.0) / height, 5),
                    ],
                    "bbox_size_norm": [
                        round((x2 - x1) / width, 5),
                        round((y2 - y1) / height, 5),
                    ],
                }
            )

        return {
            "stamp": {"sec": stamp.sec, "nanosec": stamp.nanosec},
            "frame_id": self.frame_id,
            "image": {"width": width, "height": height},
            "inference_ms": round(inference_ms, 2),
            "count": len(detections),
            "detections": detections,
        }

    def destroy_node(self):
        if self.capture is not None:
            self.capture.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
