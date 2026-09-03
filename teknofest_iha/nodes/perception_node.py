from __future__ import annotations

"""ROS 2 perception process.

This node is intentionally limited to camera-to-detection work:

* read the decision camera stream,
* run OpenCV color/shape detection,
* publish a raw detection packet.

It does not choose mission targets, command the vehicle, or release payloads.
Those responsibilities belong to fusion and mission manager processes.
"""

import time

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from teknofest_iha.adapters.opencv_adapter import OpenCVAdapter
from teknofest_iha.interfaces.detection_models import RawDetectionPacket


class PerceptionNode(Node):
    def __init__(self) -> None:
        super().__init__("perception_node")
        self.declare_parameter("camera_topic", "/camera")
        self.declare_parameter("raw_detections_topic", "/perception/raw_detections")
        self.declare_parameter("fusion_target_topic", "/fusion/target")
        self.declare_parameter("debug_image_topic", "/perception/debug_image")
        self.declare_parameter("status_topic", "/perception/status")
        self.declare_parameter("primary_target", "blue_square")
        self.declare_parameter("detect_targets", ["blue_square", "red_square"])
        self.declare_parameter("publish_debug_image", True)

        targets = list(self.get_parameter("detect_targets").value)
        self.bridge = CvBridge()
        self.frame_id = 0
        self.publish_debug_image = bool(self.get_parameter("publish_debug_image").value)

        self.opencv = OpenCVAdapter(enabled_targets=targets)

        self.raw_pub = self.create_publisher(String, str(self.get_parameter("raw_detections_topic").value), 10)
        self.status_pub = self.create_publisher(String, str(self.get_parameter("status_topic").value), 10)
        self.debug_pub = self.create_publisher(Image, str(self.get_parameter("debug_image_topic").value), 10)
        self.create_subscription(Image, str(self.get_parameter("camera_topic").value), self.on_image, 10)
        self.get_logger().info("Perception running in OpenCV-only mode")

    def on_image(self, msg: Image) -> None:
        self.frame_id += 1
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        debug_image, opencv_dets = self.opencv.detect(frame, self.frame_id)

        packet = RawDetectionPacket(
            frame_id=self.frame_id,
            timestamp=time.time(),
            opencv=opencv_dets,
        )
        self.raw_pub.publish(String(data=packet.to_json()))
        self.status_pub.publish(String(data='{"status":"OK"}'))
        if self.publish_debug_image:
            self.debug_pub.publish(self.bridge.cv2_to_imgmsg(debug_image, encoding="bgr8"))


def main() -> None:
    rclpy.init()
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
