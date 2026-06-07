# leos-robotic-arm

基于 ROS 2 Humble 的六自由度机械臂（Dofbot）运动学规划与仿真工作空间。

---

## 🛠️ 项目背景与初衷

本项目起源于邮专的机器人实训课程。由于实训官方提供的某品牌机械臂工作空间极度封闭、不完全开源，且工程质量堪忧（例如：`CMakeLists.txt` 中大量硬编码绝对路径，导致跨设备移植极其痛苦），极大地限制了开发自由度。

**因为我是双系统win/ubuntu22.04,就没有重装一个虚拟机的必要了。这边也是仿真的多，就直接ros2构建了。要实物那要么bridge要么就docker装个ros1即可**

为了获得一个纯净、规范且完全可控的开发环境，本项目抛弃了原厂封闭的软硬件生态，基于开源社区中非常完整的 Dofbot 描述文件进行二次开发，在 ROS 2 Humble 环境下从零构建完整的机械臂仿真与控制链。

## 📍 资源来源

本项目的机械臂物理描述（URDF）与网格模型（Meshes）资源基于以下开源仓库构建：
* **参考上游**：[v-xchen-v/dofbot_ws](https://github.com/v-xchen-v/dofbot_ws)
* **致谢**：感谢原作者提供的极其完整的 URDF 关节树与精细的结构件三维网格模型，为本项目在 ROS 2 下的重构奠定了坚实基础。

## 🚀 干了什么

移植好了机械臂的 urdf meshes 过了一遍moveit_setup_assistant moveit验证了以下
完成了机械臂+moveit 机械臂+ ignition gazabo 6

## 一些问题
CMakelist.txt 别忘记install urdf meshes
使用 assistant 的 joint_limits.yaml 文件里面的参数需要全是float