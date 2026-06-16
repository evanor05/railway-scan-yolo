from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    model_path = LaunchConfiguration("model_path")
    source = LaunchConfiguration("source")
    conf = LaunchConfiguration("conf")
    rate_hz = LaunchConfiguration("rate_hz")
    publish_annotated = LaunchConfiguration("publish_annotated")

    return LaunchDescription(
        [
            DeclareLaunchArgument("model_path", default_value="yolo26n.pt"),
            DeclareLaunchArgument("source", default_value="0"),
            DeclareLaunchArgument("conf", default_value="0.35"),
            DeclareLaunchArgument("rate_hz", default_value="5.0"),
            DeclareLaunchArgument("publish_annotated", default_value="true"),
            Node(
                package="inspection_yolo_demo",
                executable="drone_status",
                name="drone_status",
                output="screen",
            ),
            Node(
                package="inspection_yolo_demo",
                executable="yolo_detection",
                name="yolo_detection",
                output="screen",
                parameters=[
                    {
                        "model_path": model_path,
                        "source": source,
                        "conf": conf,
                        "rate_hz": rate_hz,
                        "publish_annotated": publish_annotated,
                    }
                ],
            ),
            Node(
                package="inspection_yolo_demo",
                executable="ground_monitor",
                name="ground_monitor",
                output="screen",
            ),
        ]
    )
