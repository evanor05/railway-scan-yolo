from glob import glob
from setuptools import setup

package_name = "inspection_yolo_demo"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="demo",
    maintainer_email="demo@example.com",
    description="ROS 2 demo nodes for drone inspection with YOLO detections.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "yolo_detection = inspection_yolo_demo.yolo_detection_node:main",
            "ground_monitor = inspection_yolo_demo.ground_station_monitor:main",
            "drone_status = inspection_yolo_demo.drone_status_node:main",
        ],
    },
)
