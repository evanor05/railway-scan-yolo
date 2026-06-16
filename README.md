# Railway Scan YOLO

本项目用于铁路巡检场景下的 YOLO 目标检测实验，重点关注铁路区域中的人员与常见障碍物检测。仓库保留可复现实验和 Demo 所需的项目框架，包括数据处理脚本、训练说明、配置示例，以及一个最小可运行的 ROS 2 摄像头巡检 Demo。

为了让仓库保持轻量，数据集、训练输出、模型权重、下载的 PDF 文献和压缩包不会提交到 Git。

## 项目结构

```text
.
|-- configs/                      # 数据集配置示例
|-- docs/                         # 项目说明、训练说明和文献整理
|-- ros2_ws/src/inspection_yolo_demo/
|   `-- ...                       # ROS 2 巡检 Demo 包
|-- scripts/                      # 数据准备、检查和训练辅助脚本
|-- test_images/samples/          # 少量公开示例图片
`-- weights/                      # 本地模型权重目录，不提交 .pt 文件
```

以下目录主要用于本地实验，已被 `.gitignore` 忽略：

```text
datasets/
runs/
literature/
railway_manual_inspection_literature/
archive/
labelImg-master/
```

## 数据集配置

`configs/railway_obstacle_person.data.yaml.example` 是铁路障碍物与人员联合检测数据集的配置模板：

```yaml
path: ./datasets/railway_obstacle_person_yolo
train: images/train
val: images/val

names:
  0: animal
  1: motorcycle
  2: person
  3: rock
  4: vehicle
```

使用时可以复制一份到本地数据集目录，并根据实际路径修改 `path`。

## 主要脚本

- `scripts/prepare_railway_obstacle_yolo.py`：将铁路障碍物数据整理为 YOLO 格式。
- `scripts/remap_person_labels_to_obstacle_person.py`：将人员检测标签映射到联合类别体系。
- `scripts/merge_obstacle_and_person_yolo.py`：合并障碍物数据集和人员数据集。
- `scripts/check_yolo_dataset_integrity.py`：检查图片可读性、标签缺失、类别越界和坐标异常。
- `scripts/train_obstacle_person.bat`：启动本地 YOLO 训练。
- `scripts/resume_obstacle_person.bat`：从本地 checkpoint 断点续训。
- `scripts/open_yolo_env.bat`：打开本地 YOLO Conda 环境。

Windows 批处理脚本中包含本机环境路径，换机器运行前需要改成自己的路径。

## 训练示例

```powershell
yolo detect train model=weights/yolo26n.pt data=configs/railway_obstacle_person.data.yaml.example imgsz=768 epochs=80 batch=24 device=0
```

训练结果解读、指标说明和后续验证建议见：

```text
docs/TRAINING_RESULT_GUIDE.md
```

## ROS 2 摄像头巡检 Demo

`ros2_ws/src/inspection_yolo_demo` 中包含一个最小 ROS 2 Demo，用于模拟无人机或摄像头巡检链路。它可以：

- 从摄像头或图片源运行 YOLO 推理；
- 发布检测结果 JSON；
- 发布带检测框的压缩图片；
- 模拟无人机心跳和状态；
- 根据检测结果发布简单告警。

相关说明：

```text
ros2_ws/src/inspection_yolo_demo/README.md
docs/ROS2_YOLO_CAMERA_DEMO_REQUIREMENTS.md
```

## 模型权重

模型文件不会提交到仓库。请将本地权重放在 `weights/` 目录，例如：

```text
weights/best.pt
weights/yolo26n.pt
```

如果后续需要公开训练好的模型，建议使用 GitHub Releases 或 Git LFS，而不是直接提交到普通 Git 历史中。

## 依赖

基础 Python 依赖见 `requirements.txt`：

```powershell
pip install -r requirements.txt
```

ROS 2 Demo 在树莓派或 Ubuntu 环境中的依赖见：

```text
ros2_ws/src/inspection_yolo_demo/requirements-pi.txt
```

## 数据来源

当前实验参考了以下公开数据集：

1. [Railway Track Fault Detection](https://www.kaggle.com/datasets/salmaneunus/railway-track-fault-detection/data)
2. [synRailObs](https://www.kaggle.com/datasets/qiushi910/synrailobs)

请在使用数据集和公开发布成果时遵守原始数据来源的许可要求。
