import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_bringup = get_package_share_directory('officebot_bringup')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    nav2_params = os.path.join(pkg_bringup, 'config', 'nav2_params.yaml')
    default_map = os.path.join(pkg_bringup, 'maps', 'office_map_v2.yaml')

    map_yaml = LaunchConfiguration('map')

    declare_map_arg = DeclareLaunchArgument(
        'map',
        default_value=default_map,
        description='Full path to map yaml file'
    )

    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_yaml,
            'params_file': nav2_params,
            'use_sim_time': 'True',
        }.items()
    )

    # Remapuje standardowy /cmd_vel (używany wewnętrznie przez Nav2) na nasz topic kontrolera
    cmd_vel_bridge = Node(
        package='topic_tools',
        executable='relay',
        name='cmd_vel_relay',
        arguments=['/cmd_vel', '/diff_drive_controller/cmd_vel_unstamped'],
        output='screen'
    )

    return LaunchDescription([
        declare_map_arg,
        nav2_bringup_launch,
        cmd_vel_bridge,
    ])
