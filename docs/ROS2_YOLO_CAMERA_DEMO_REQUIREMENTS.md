# ROS2 + YOLO 摄像头检测 Demo 具体要求

## 1. Demo 目标

用笔记本摄像头模拟无人机机载摄像头，在 VMware 虚拟机中运行 ROS2 节点，实现：

```text
笔记本摄像头
  -> camera_node 发布图像
  -> yolo_node 订阅图像并推理
  -> 发布检测结果
  -> 终端或监控节点查看识别结果
```

```text
摄像头 -> ROS2 图像 Topic -> YOLO 推理 -> ROS2 检测结果 Topic
```

后续迁移到无人机时，将笔记本摄像头替换为树莓派摄像头，将 VMware 环境替换为树莓派 5B。

## 2. 系统角色

### 2.1 Demo 阶段

```text
VMware 虚拟机：
  - 运行 ROS2
  - 运行 camera_node
  - 运行 yolo_node
  - 调用 YOLO 模型推理
笔记本摄像头：
  - 提供实时图像输入
```

## 3. 功能范围

### 3.1 本阶段必须实现

1. VMware 能够读取笔记本摄像头。
2. `camera_node` 能够发布摄像头图像。
3. `yolo_node` 能够订阅图像并完成 YOLO 推理。
4. `yolo_node` 能够发布检测结果。
5. `yolo_node` 能够发布带检测框的可视化图像。
6. `gui_node` 能够实时显示摄像头识别画面。
7. 可以通过 `ros2 topic echo` 查看检测结果。

## 4. ROS2 节点设计

### 4.1 camera_node

职责：

```text
读取摄像头画面
压缩为 JPEG
发布到 ROS2 Topic
```

输入：

```text
笔记本摄像头 /dev/video0
```

输出 Topic：

```text
/camera/image/compressed
```

消息类型：

```text
sensor_msgs/msg/CompressedImage
```

建议参数：

```text
camera_id: 0
fps: 10
jpeg_quality: 80
frame_id: camera
```

要求：

```text
发布频率稳定
图像能被 yolo_node 正常解码
摄像头读取失败时打印 warning
```

### 4.2 yolo_node

职责：

```text
订阅摄像头图像
解码 JPEG 图像
调用 YOLO 模型推理
整理检测框、类别、置信度
发布检测结果
```

输入 Topic：

```text
/camera/image/compressed
```

输入消息类型：

```text
sensor_msgs/msg/CompressedImage
```

输出 Topic：

```text
/inspection/detections
/inspection/annotated_image/compressed
```

输出消息类型：

```text
std_msgs/msg/String
sensor_msgs/msg/CompressedImage
```

建议参数：

```text
model_path: 训练后的 best.pt
conf: 0.35
imgsz: 768
```

检测结果 JSON 格式：

```json
{
  "stamp": {
    "sec": 0,
    "nanosec": 0
  },
  "frame_id": "camera",
  "count": 1,
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.9123,
      "bbox_xyxy": [120.5, 80.2, 310.1, 460.8]
    }
  ]
}
```

要求：

```text
没有检测到目标时也要发布 count=0
检测结果必须包含类别、置信度、检测框
检测框使用像素坐标 xyxy 格式
推理失败时不能导致整个节点崩溃
需要额外发布带检测框的图像，用于 GUI 实时显示
图像中的检测标签显示 class_name 和 confidence
```

说明：

```text
GUI 实时画面中显示的是单个检测框的 confidence（置信度）
不是验证集整体指标 precision
```

### 4.3 gui_node

职责：

```text
订阅 YOLO 节点发布的带框图像
解码 JPEG 图像
弹出 GUI 窗口实时显示检测画面
画面中需要能看到目标框、类别名、confidence
```

输入 Topic：

```text
/inspection/annotated_image/compressed
```

输入消息类型：

```text
sensor_msgs/msg/CompressedImage
```

输出：

```text
OpenCV GUI 窗口
```

窗口标题建议：

```text
Inspection YOLO Viewer
```

显示内容要求：

```text
实时摄像头画面
检测框
类别名称，例如 person
单帧置信度 confidence，例如 0.91
```

第一版建议使用 OpenCV GUI：

```text
cv2.imshow()
cv2.waitKey(1)
```

暂不要求使用 PyQt、Web 前端或完整地面站界面。

## 5. 模型要求

```text
yolo26n.pt
```

## 6. 数据和类别要求

当前模型类别：

```text
0: person
```

其中坐标为归一化比例，范围是 `0~1`。

示例：

```text
0 0.512 0.438 0.120 0.300
```

类别编号必须和 `data.yaml` 一致。

扩展示例：

```yaml
names:
  0: person
  1: rock
  2: vehicle
  3: animal
  4: motorcycle
```

## 7. 环境要求

### 7.1 VMware 虚拟机

要求：

```text
Ubuntu
ROS2
Python 3
OpenCV
Ultralytics
NumPy
```

摄像头检查：

```bash
ls /dev/video*
```

OpenCV 检查：

```bash
python3 - <<'PY'
import cv2
cap = cv2.VideoCapture(0)
print(cap.isOpened())
ret, frame = cap.read()
print(ret, None if frame is None else frame.shape)
cap.release()
PY
```

如果虚拟机看不到摄像头，需要在 VMware 中连接摄像头：

```text
VMware -> Removable Devices -> Camera -> Connect
```

### 7.2 Python 依赖

```bash
pip install ultralytics opencv-python numpy
```

## 8. 建议运行方式

### 8.1 启动 camera_node

```bash
ros2 run drone_inspection camera_node --ros-args \
  -p camera_id:=0 \
  -p fps:=10 \
  -p jpeg_quality:=80
```

### 8.2 启动 yolo_node

```bash
ros2 run drone_inspection yolo_node --ros-args \
  -p model_path:=/path/to/best.pt \
  -p conf:=0.35 \
  -p imgsz:=768
```

### 8.3 启动 gui_node

```bash
ros2 run drone_inspection gui_node
```

### 8.4 检查 Topic

```bash
ros2 topic list
```

检查图像发布频率：

```bash
ros2 topic hz /camera/image/compressed
```

查看检测结果：

```bash
ros2 topic echo /inspection/detections
```

检查带框图像发布频率：

```bash
ros2 topic hz /inspection/annotated_image/compressed
```

## 9. 验收标准

本阶段完成标准：

1. `ros2 topic list` 能看到：

```text
/camera/image/compressed
/inspection/detections
/inspection/annotated_image/compressed
```

2. `/camera/image/compressed` 有稳定频率：

```text
5 Hz 到 10 Hz 均可接受
```

3. `/inspection/detections` 能输出 JSON。

4. `/inspection/annotated_image/compressed` 能持续输出带框图像。

5. `gui_node` 启动后能够弹出实时显示窗口。

6. 摄像头前出现人时，检测结果中出现：

```json
{
  "class_name": "person"
}
```

7. GUI 画面中能看到人被检测框框住，并显示类似：

```text
person 0.91
```

其中 `0.91` 表示该检测框的 confidence。

8. 没有人时，允许输出：

```json
{
  "count": 0,
  "detections": []
}
```

## 10. 后续扩展

第一阶段跑通后，再增加：

```text
event_node
  - 订阅 /inspection/detections
  - 订阅 /drone/gps
  - 订阅 /drone/status
  - 生成 /inspection/events
```

后续事件内容：

```json
{
  "event_type": "person_detected",
  "confidence": 0.94,
  "bbox_xyxy": [120, 80, 310, 460],
  "drone_lat": 31.2304,
  "drone_lon": 121.4737,
  "altitude": 35.2,
  "image_path": "event_001.jpg",
  "action": "record_and_alert"
}
```

最终无人机系统分工：

```text
飞控板：
  - 按预设航线飞行
  - 提供 GPS、高度、姿态
  - 执行悬停、继续、返航等高级命令
```

## 11. 当前推荐实现顺序

1. 先写 `camera_node`，确认能发布图像。
2. 再写 `yolo_node`，确认能订阅图像。
3. 在 `yolo_node` 中加入 YOLO 推理。
4. 输出 `/inspection/detections`。
5. 在 `yolo_node` 中发布 `/inspection/annotated_image/compressed`。
6. 写 `gui_node`，实时显示带框图像。
7. 用 `ros2 topic echo` 验证检测 JSON。
8. 用 GUI 验证摄像头中的人能被框出并显示 confidence。
9. 再考虑保存图片、生成事件、接入 GPS。
