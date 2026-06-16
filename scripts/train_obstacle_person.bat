@echo off
setlocal

set "PROJECT_DIR=E:\yolov26"
set "CONDA_BAT=C:\ProgramData\miniconda3\condabin\conda.bat"
set "ENV_PATH=E:\ArtificialInt\envs\yolo"

cd /d "%PROJECT_DIR%"
call "%CONDA_BAT%" activate "%ENV_PATH%"

yolo detect train model=E:\yolov26\weights\yolo26n.pt data=E:\yolov26\datasets\railway_obstacle_person_yolo\data.yaml imgsz=768 epochs=80 batch=24 workers=0 device=0 cache=False name=obstacle_person_yolo26n_768_b24_w0

pause

