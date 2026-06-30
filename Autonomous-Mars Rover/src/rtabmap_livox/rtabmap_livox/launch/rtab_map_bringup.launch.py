# Adapted from lidar3d_assemble.launch.py for FAST-LIO + Livox Mid-360
#
# FAST-LIO provides:
#   - Odometry via TF: odom → body
#   - Deskewed point clouds already (motion compensated)
#
# This launch file:
#   - Uses FAST-LIO's odometry (no ICP odometry)
#   - Skips deskewing (FAST-LIO already does it)
#   - Assembles scans for denser mapping
#   - ENABLES 3D occupancy grid/OctoMap generation
#
# 3D OctoMap Configuration:
#   - Grid/3D=true and Grid/RayTracing=true enable 3D occupancy mapping
#   - Grid/Sensor=0 uses laser scan data (not depth images)
#   - Grid/NormalsSegmentation=false is CRITICAL for Livox's unorganized clouds
#   - Outputs: /octomap_occupied_space, /octomap_full, /octomap_binary, etc.
#
# Usage:
#   $ ros2 launch maple_bringup rtab_map_bringup.launch.py

from launch import LaunchDescription, LaunchContext
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def launch_setup(context: LaunchContext, *args, **kwargs):

    frame_id = LaunchConfiguration('frame_id')

    # FAST-LIO publishes TF: camera_init → body
    # We use camera_init as our fixed frame (odometry frame)
    external_odom_frame_id = LaunchConfiguration('odom_frame_id').perform(context)

    lidar_topic = LaunchConfiguration('lidar_topic')

    voxel_size = LaunchConfiguration('voxel_size')
    voxel_size_value = float(voxel_size.perform(context))

    use_sim_time = LaunchConfiguration('use_sim_time')

    localization = LaunchConfiguration('localization').perform(context)
    localization = localization == 'true' or localization == 'True'

    rviz_config = LaunchConfiguration('rviz_config').perform(context)

    # Rule of thumb for max correspondence distance
    max_correspondence_distance = voxel_size_value * 10.0

    shared_parameters = {
        'use_sim_time': use_sim_time,
        'frame_id': frame_id,
        'qos': LaunchConfiguration('qos'),
        'approx_sync': False,  # Use exact sync
        'wait_for_transform': 0.2,
        # ICP parameters for loop closure detection (not odometry!)
        'Icp/PointToPlane': 'true',
        'Icp/Iterations': '10',
        'Icp/VoxelSize': str(voxel_size_value),
        'Icp/Epsilon': '0.001',
        'Icp/PointToPlaneK': '20',
        'Icp/PointToPlaneRadius': '0',
        'Icp/MaxTranslation': '3',
        'Icp/MaxCorrespondenceDistance': str(max_correspondence_distance),
        'Icp/Strategy': '1',
        'Icp/OutlierRatio': '0.7',
    }

    rtabmap_parameters = {
        'subscribe_depth': False,
        'subscribe_rgb': False,
        'subscribe_odom_info': False,  # Using external odometry via TF
        'subscribe_scan_cloud': True,
        'odom_frame_id': external_odom_frame_id,
        'map_frame_id': 'map',
        'publish_tf': True,  # Publish map → odom transform

        # Publishing optimization - reduce overhead
        'publish_octomap_full': False,  # Don't publish full octomap (huge!)
        'publish_point_cloud': False,  # Don't republish assembled cloud
        # Core SLAM parameters
        # 'Rtabmap/DetectionRate': '0',  # Indirectly ~1Hz from assembling time
        'RGBD/ProximityMaxGraphDepth': '0',
        'RGBD/ProximityPathMaxNeighbors': '1',
        'RGBD/AngularUpdate': '0.05',
        'RGBD/LinearUpdate': '0.05',
        'Mem/NotLinkedNodesKept': 'false',
        'Mem/STMSize': '30',
        # 'Mem/LaserScanNormalK': '0',
        # 'Mem/LaserScanVoxelSize': '0.0',
        # Registration for loop closure
        'Reg/Strategy': '1',  # ICP
        # 'Reg/Force3DoF': 'false',  # Allow 6DoF
        'Icp/CorrespondenceRatio': '0.2',

        # *** 3D OCCUPANCY GRID / OCTOMAP GENERATION ***
        # CRITICAL: Must enable occupancy grid creation
        'RGBD/CreateOccupancyGrid': 'true',

        # Grid sensor configuration for laser scan
        'Grid/Sensor': '0',  # 0=laser scan, 1=depth image, 2=both

        # 3D OctoMap settings
        'Grid/3D': 'true',  # REQUIRED for 3D occupancy grid (OctoMap)
        'Grid/RayTracing': 'true',  # Fill unknown space between sensor and obstacles

        # Grid resolution and range
        'Grid/CellSize': str(voxel_size_value),  # Match voxel size for consistency
        'Grid/RangeMax': '30.0',  # Max range for Livox Mid-360 (effective ~40m)
        'Grid/RangeMin': '0.1',  # Min range to filter very close points

        # Ground/obstacle segmentation settings
        # CRITICAL: Disable normals segmentation for unorganized Livox clouds
        'Grid/NormalsSegmentation': 'false',  # Livox clouds are unorganized
        'Grid/MaxGroundHeight': '0.01',       # Throwaway value to avoid warning
        'Grid/GroundIsObstacle': 'true',      # Include all geometry as obstacles

        # Point cloud filtering (optimized for Livox)
        'Grid/NoiseFilteringRadius': '0.0',  # Disabled for Livox sparse clouds
        'Grid/NoiseFilteringMinNeighbors': '5',
        'Grid/ClusterRadius': '0.2',  # Larger radius = less aggressive
        'Grid/MinClusterSize': '5',  # Smaller min size = keep more clusters

        # Additional grid optimization
        'Grid/FootprintLength': '0.0',  # Robot footprint (0=disabled)
        'Grid/FootprintWidth': '0.0',
        'Grid/FootprintHeight': '0.0',
    }

    arguments = []
    if localization:
        rtabmap_parameters['Mem/IncrementalMemory'] = 'False'
        rtabmap_parameters['Mem/InitWMWithAllNodes'] = 'True'
    else:
        arguments.append('-d')  # Delete previous database

    nodes = [
        # Assemble scans based on FAST-LIO odometry
        Node(
            package='rtabmap_util',
            executable='point_cloud_assembler',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'assembling_time': LaunchConfiguration('assembling_time'),
                'fixed_frame_id': external_odom_frame_id  # Use FAST-LIO's odom frame
            }],
            remappings=[
                ('cloud', lidar_topic),
                # Note: assembler will subscribe to TF for odometry
            ]),

        # RTAB-Map SLAM node
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            output='screen',
            parameters=[
                shared_parameters,
                rtabmap_parameters,
                {
                    'topic_queue_size': 40,
                    'sync_queue_size': 40,
                }
            ],
            remappings=[
                ('scan_cloud', '/cloud_registered_body'),
            ],
            arguments=arguments
        ),

        # RTAB-Map Visualization (optional)
        Node(
            package='rtabmap_viz',
            executable='rtabmap_viz',
            output='screen',
            parameters=[shared_parameters, rtabmap_parameters],
            remappings=[
                ('scan_cloud', lidar_topic)  # Show live scan
            ]
        ),

        # RViz2 for 3D visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config] if rviz_config and os.path.exists(rviz_config) else [],
            parameters=[{'use_sim_time': use_sim_time}]
        )
    ]

    return nodes


def generate_launch_description():
    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use simulated clock.'),

        DeclareLaunchArgument(
            'frame_id', default_value='body',
            description='Base frame of the robot (where LiDAR is attached).'),

        DeclareLaunchArgument(
            'odom_frame_id', default_value='camera_init',
            description='FAST-LIO odometry frame.'),

        DeclareLaunchArgument(
            'localization', default_value='false',
            description='Localization mode.'),

        DeclareLaunchArgument(
            'lidar_topic', default_value='/cloud_registered_body',  # Could be /cloud_registered_body
            description='Livox point cloud topic. (deskewed by FAST-LIO)'),

        DeclareLaunchArgument(
            'voxel_size', default_value='0.05',
            description='Voxel size (m). Start with 0.2 for Livox Mid-360.'),

        DeclareLaunchArgument(
            'assembling_time', default_value='1.0',
            description='Time (sec) to assemble scans before sending to mapping.'),

        DeclareLaunchArgument(
            'qos', default_value='0',
            description='QoS: 0=system default, 1=reliable, 2=best effort.'),

        DeclareLaunchArgument(
            'rviz_config', default_value='',
            description='Path to RViz config file. Leave empty to start with default config.'),

        OpaqueFunction(function=launch_setup),
    ])