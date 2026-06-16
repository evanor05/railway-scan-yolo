# inspection_yolo_demo

Minimal ROS 2 demo for a Raspberry Pi drone-inspection node that runs YOLO and
publishes detection results to a ground-station monitor.

## Topics

- `/inspection/detections` (`std_msgs/String`): JSON detection payload.
- `/inspection/annotated_image/compressed` (`sensor_msgs/CompressedImage`): JPEG with boxes.
- `/inspection/alerts` (`std_msgs/String`): JSON alert payload from the monitor.
- `/drone/heartbeat` (`std_msgs/String`): simulated heartbeat.
- `/drone/status` (`std_msgs/String`): simulated drone status.
- `/mission/command` (`std_msgs/String`): publish `start`, `pause`, `resume`,
  `return_home`, or `stop`.

## Raspberry Pi setup

Use Ubuntu 24.04 arm64 with ROS 2 Jazzy for the simplest current binary install.

```bash
sudo apt update
sudo apt install -y ros-jazzy-ros-base python3-colcon-common-extensions python3-pip python3-opencv
source /opt/ros/jazzy/setup.bash
python3 -m pip install --break-system-packages ultralytics
```

Copy this package into a ROS 2 workspace on the Pi:

```bash
mkdir -p ~/ros2_ws/src
cp -r inspection_yolo_demo ~/ros2_ws/src/
cd ~/ros2_ws
colcon build --packages-select inspection_yolo_demo
source install/setup.bash
```

Run with the current model and a camera:

```bash
ros2 launch inspection_yolo_demo demo.launch.py \
  model_path:=/home/pi/yolov26/yolo26n.pt \
  source:=0 \
  conf:=0.35 \
  rate_hz:=5.0
```

Run from an image folder instead of a camera:

```bash
ros2 launch inspection_yolo_demo demo.launch.py \
  model_path:=/home/pi/yolov26/yolo26n.pt \
  source:=/home/pi/yolov26/datasets/railway_obstacle_yolo/images/val
```

Send a mission command:

```bash
ros2 topic pub --once /mission/command std_msgs/msg/String "{data: start}"
```

Watch the communication:

```bash
ros2 topic echo /inspection/detections
ros2 topic echo /inspection/alerts
ros2 topic hz /inspection/detections
```

## Demo path

1. Start the launch file on the Pi.
2. Confirm the ground station receives `/drone/heartbeat`.
3. Publish `/mission/command` with `start`.
4. Show `/inspection/detections` and `/inspection/alerts`.
5. Open the annotated image topic with `rqt_image_view` if available.
