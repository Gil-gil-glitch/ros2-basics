"""Coordinator node: listens to /gesture and logs a reply."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# What the coordinator says for each gesture.
REPLIES = {
    'Thumb_Up': 'Nice to see you too!',
    'Thumb_Down': 'Oh no, what went wrong?',
    'Victory': 'Peace!',
    'Open_Palm': 'Hello there!',
    'Closed_Fist': 'Ready to grab something.',
    'Pointing_Up': 'What are you pointing at?',
    'ILoveYou': 'Love you too!',
}


class Coordinator(Node):

    def __init__(self):
        super().__init__('coordinator')   # the node's name, shown by "ros2 node list"
        # Call self.on_gesture every time a String arrives on /gesture.
        # 10 = how many messages to keep waiting if we fall behind.
        self.subscription = self.create_subscription(
            String, '/gesture', self.on_gesture, 10)
        self.get_logger().info('Coordinator ready. Waiting for gestures on /gesture...')

    def on_gesture(self, msg):
        gesture = msg.data
        reply = REPLIES.get(gesture)
        if reply is None:
            self.get_logger().info(f'I saw "{gesture}", but I have no reply for it.')
        else:
            self.get_logger().info(f'{gesture} -> {reply}')


def main(args=None):
    rclpy.init(args=args)          # start ROS 2 communication
    node = Coordinator()
    try:
        rclpy.spin(node)           # wait for messages and call our callbacks, forever
    except KeyboardInterrupt:      # Ctrl+C
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()