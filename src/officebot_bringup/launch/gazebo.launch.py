import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node


def generate_launch_description():
    pkg_description = get_package_share_directory('officebot_description')
    pkg_bringup = get_package_share_directory('officebot_bringup')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(pkg_description, 'urdf', 'officebot.urdf.xacro')
    world_file = os.path.join(pkg_bringup, 'worlds', 'office.world')
    bridge_config = os.path.join(pkg_bringup, 'config', 'gz_bridge.yaml')

    robot_description = Command(['xacro ', xacro_file])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'officebot',
            '-z', '0.00'
        ],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gz_bridge',
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': True
        }],
        output='screen'
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller'],
        output='screen'
    )

    return LaunchDescription([
        gz_sim,
        robot_state_publisher,
        spawn_entity,
        bridge,
        joint_state_broadcaster_spawner,
        diff_drive_spawner,
    ])
