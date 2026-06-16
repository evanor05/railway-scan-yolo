# Railway Scan YOLO

YOLO-based railway inspection experiments for detecting people and common
obstacles in railway scenes. The repository keeps the reproducible project
framework: data preparation scripts, training notes, configuration examples,
and a minimal ROS 2 demo for camera-based inspection.

Large local assets such as datasets, training runs, model weights, downloaded
PDFs, and archives are intentionally kept out of Git.

## Repository Layout

```text
.
├── configs/                      # Dataset config examples
├── docs/                         # Project notes and analysis documents
├── ros2_ws/src/inspection_yolo_demo/
│   └── ...                       # ROS 2 demo package
├── scripts/                      # Data preparation and training helpers
├── test_images/samples/          # Small public demo samples only
└── weights/                      # Local model weights, not committed
```

Local-only directories such as `datasets/`, `runs/`, `literature/`, and
`archive/` are ignored by Git.

## Dataset Config

Use `configs/railway_obstacle_person.data.yaml.example` as the template for the
combined railway obstacle/person dataset:

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

Copy it to your local dataset directory and adjust `path` if needed.

## Main Scripts

- `scripts/prepare_railway_obstacle_yolo.py` prepares the railway obstacle
  dataset in YOLO format.
- `scripts/remap_person_labels_to_obstacle_person.py` remaps person labels for
  the combined class set.
- `scripts/merge_obstacle_and_person_yolo.py` builds the combined detection
  dataset.
- `scripts/check_yolo_dataset_integrity.py` checks image readability and YOLO
  label validity.
- `scripts/train_obstacle_person.bat` starts a local YOLO training run.
- `scripts/resume_obstacle_person.bat` resumes training from the local
  checkpoint.

The Windows batch files contain local environment paths. Update them before
running on another machine.

## Training

Example command:

```powershell
yolo detect train model=yolo26n.pt data=configs/railway_obstacle_person.data.yaml.example imgsz=768 epochs=80 batch=24 device=0
```

For training interpretation and validation guidance, see
`docs/TRAINING_RESULT_GUIDE.md`.

## ROS 2 Demo

The package under `ros2_ws/src/inspection_yolo_demo` provides a minimal
inspection demo that:

- runs YOLO inference from a camera or image source,
- publishes detection JSON,
- publishes annotated compressed images,
- simulates drone heartbeat/status,
- emits simple inspection alerts.

See `ros2_ws/src/inspection_yolo_demo/README.md` and
`docs/ROS2_YOLO_CAMERA_DEMO_REQUIREMENTS.md` for setup and demo flow.

## Model Weights

Model files such as `*.pt` are not committed. Put local weights under
`weights/`, or publish selected trained weights separately through GitHub
Releases or Git LFS if needed.

## Data Sources

Initial public dataset references:

1. [Railway Track Fault Detection](https://www.kaggle.com/datasets/salmaneunus/railway-track-fault-detection/data)
2. [synRailObs](https://www.kaggle.com/datasets/qiushi910/synrailobs)
