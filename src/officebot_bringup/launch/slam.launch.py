import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_bringup = get_package_share_directory('officebot_bringup')
    slam_params = os.path.join(pkg_bringup, 'config', 'slam_toolbox_params.yaml')

    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params,
            {'use_sim_time': True}
        ]
    )

    return LaunchDescription([
        slam_toolbox_node,
    ])
