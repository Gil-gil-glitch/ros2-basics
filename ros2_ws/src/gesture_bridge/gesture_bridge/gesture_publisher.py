"""Gesture publisher node: recognizes hand gestures with MediaPipe and publishes them on /gesture."""

import time
from pathlib import Path

import cv2
import mediapipe as mp
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# The model downloaded in the MediaPipe lessons (python3 download_models.py).
MODEL_PATH = Path.home() / 'mediapipe-first-steps' / 'models' / 'gesture_recognizer.task'
CAMERA_INDEX = 0
HOLD_FRAMES = 8      # a gesture must be seen this many frames in a row to count
MIN_SCORE = 0.5      # ignore guesses the model is less sure about


class GesturePublisher(Node):

    def __init__(self):
        super().__init__('gesture_publisher')
        self.gesture_pub = self.create_publisher(String, '/gesture', 10)

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f'Model not found: {MODEL_PATH}')
        options = mp.tasks.vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=1,
        )
        self.recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(options)

        self.camera = cv2.VideoCapture(CAMERA_INDEX)
        if not self.camera.isOpened():
            raise RuntimeError(f'Could not open camera {CAMERA_INDEX}')

        self.candidate = 'None'       # gesture seen in the last few frames
        self.count = 0                # how many frames in a row we've seen it
        self.current = 'None'         # the last confirmed gesture
        self.start = time.monotonic()
        self.last_timestamp = -1

        # Instead of a "while True" loop, ROS calls on_timer 30 times per second.
        self.timer = self.create_timer(1.0 / 30, self.on_timer)
        self.get_logger().info('Gesture publisher ready. Show a gesture to the camera.')

    def on_timer(self):
        ok, frame = self.camera.read()
        if not ok:
            self.get_logger().warn('No camera frame')
            return
        frame = cv2.flip(frame, 1)

        # Same as lesson 08: RGB image + always-increasing timestamp.
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp = max(int((time.monotonic() - self.start) * 1000), self.last_timestamp + 1)
        self.last_timestamp = timestamp
        result = self.recognizer.recognize_for_video(image, timestamp)

        gesture = 'None'
        if result.gestures and result.gestures[0][0].score >= MIN_SCORE:
            gesture = result.gestures[0][0].category_name

        self.update(gesture)

        cv2.putText(frame, f'Gesture: {self.current}', (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        cv2.imshow('gesture_publisher', frame)
        cv2.waitKey(1)

    def update(self, gesture):
        """Confirm a gesture after HOLD_FRAMES frames, and publish it once."""
        if gesture == self.candidate:
            self.count += 1
        else:
            self.candidate = gesture
            self.count = 1

        if self.count >= HOLD_FRAMES and gesture != self.current:
            self.current = gesture
            if gesture != 'None':                 # don't announce "no gesture"
                msg = String()
                msg.data = gesture
                self.gesture_pub.publish(msg)
                self.get_logger().info(f'Published: {gesture}')

    def close(self):
        self.camera.release()
        self.recognizer.close()
        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args)
    node = GesturePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()