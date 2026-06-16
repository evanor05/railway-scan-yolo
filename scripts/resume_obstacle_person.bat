@echo off
setlocal

set "PROJECT_DIR=E:\yolov26"
set "CONDA_BAT=C:\ProgramData\miniconda3\condabin\conda.bat"
set "ENV_PATH=E:\ArtificialInt\envs\yolo"
set "LAST_PT=E:\yolov26\runs\detect\obstacle_person_yolo26n_768_b24_w0\weights\last.pt"

cd /d "%PROJECT_DIR%"
call "%CONDA_BAT%" activate "%ENV_PATH%"

if not exist "%LAST_PT%" (
  echo Cannot find checkpoint:
  echo %LAST_PT%
  pause
  exit /b 1
)

yolo detect train resume model="%LAST_PT%"

pause
