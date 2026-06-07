import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
import xacro



def generate_launch_description():

    # 填写自己的模型名称，包名，.urdf名
    robot_name_in_model = 'robarm'
    package_name = 'rob_arm_info' 
    urdf_name = "robarm.urdf"

    # 找包
    pkg_share = FindPackageShare(package=package_name).find(package_name) 
    urdf_model_path = os.path.join(pkg_share, f'urdf/{urdf_name}')

    # 注入 Gazebo 资源路径，使其能够解析 package:// 或 model:// 路径下的 STL 网格
    gazebo_resource_path = os.path.dirname(pkg_share)  # 这会指向 .../install/rob_arm_info/share
    if 'IGN_GAZEBO_RESOURCE_PATH' in os.environ:
        os.environ['IGN_GAZEBO_RESOURCE_PATH'] += os.pathsep + gazebo_resource_path
    else:
        os.environ['IGN_GAZEBO_RESOURCE_PATH'] = gazebo_resource_path

    # 加入 .so 
    ros_plugin_path = '/opt/ros/humble/lib'
    if 'IGN_GAZEBO_SYSTEM_PLUGIN_PATH' in os.environ:
        os.environ['IGN_GAZEBO_SYSTEM_PLUGIN_PATH'] += os.pathsep + ros_plugin_path
    else:
        os.environ['IGN_GAZEBO_SYSTEM_PLUGIN_PATH'] = ros_plugin_path
        
    # 1. 解析 XACRO / URDF
    doc = xacro.parse(open(urdf_model_path))
    xacro.process_doc(doc)
    robot_description_content = doc.toxml()
    params = {'robot_description': robot_description_content}

    # 2. 启动新版 Gazebo Server (Fortress 版本的标准起法)
    # 使用 empty.sdf 空白世界，-r 表示自动运行物理引擎
    start_gazebo_cmd = ExecuteProcess(
        cmd=['ign', 'gazebo', 'empty.sdf', '-r', '--verbose'],
        output='screen'
    )

    # 3. 启动 robot_state_publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'use_sim_time': True}, params, {"publish_frequency": 15.0}],
        output='screen'
    )

    # 4. 在新版 Gazebo 中生成模型 (代替原先的 spawn_entity.py)
    # 新版使用 ros_gz_sim 包中的 create 节点，直接通过话题获取 robot_description
    spawn_entity_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', robot_name_in_model,
            '-topic', 'robot_description'
        ],
        output='screen'
    )

    # 5. 核心桥接器 (ros_gz_bridge) —— 关键点！
    # 新版 Gazebo 的仿真时钟 (/clock) 必须通过桥接才能发给 ROS 2，否则 ros2 control 会卡死
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock]',
        ],
        output='screen'
    )

    # 6. 控制器加载：关节状态发布器
    # 新版加载机制更推荐使用 Node 方式调用，比 ExecuteProcess 更稳定
    load_joint_state_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    # 7. 控制器加载：你的机械臂轨迹/力矩控制器
    load_joint_trajectory_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['my_group_controller'],
        output='screen'
    )

    # 8. 调整节点的启动顺序 (防止控制器在模型没生成完就抢先启动导致报错)
    # 当机器人成功生成后，再启动 joint_state_broadcaster
    close_evt1 = RegisterEventHandler( 
        event_handler=OnProcessExit(
            target_action=spawn_entity_cmd,
            on_exit=[load_joint_state_controller],
        )
    )
    
    # 当 joint_state_broadcaster 激活后，再启动你的机械臂主控制器
    close_evt2 = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_joint_state_controller,
            on_exit=[load_joint_trajectory_controller],
        )
    )
    
    ld = LaunchDescription()

    # 添加事件监听器
    ld.add_action(close_evt1)
    ld.add_action(close_evt2)

    # 基础节点启动
    ld.add_action(start_gazebo_cmd)
    ld.add_action(ros_gz_bridge)
    ld.add_action(node_robot_state_publisher)
    ld.add_action(spawn_entity_cmd)

    return ld