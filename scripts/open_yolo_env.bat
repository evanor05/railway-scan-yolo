@echo off
setlocal

set "PROJECT_DIR=E:\yolov26"
set "CONDA_BAT=C:\ProgramData\miniconda3\condabin\conda.bat"
set "ENV_PATH=E:\ArtificialInt\envs\yolo"

cd /d "%PROJECT_DIR%"
call "%CONDA_BAT%" activate "%ENV_PATH%"

echo.
echo Activated conda environment: %ENV_PATH%
echo Project directory: %PROJECT_DIR%
echo.
cmd /k
