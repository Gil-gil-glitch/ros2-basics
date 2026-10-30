# ROS 2 Cheat Sheet

## Every new terminal

```bash
source ~/ros2_ws/install/setup.bash
```

(ROS 2 itself and your `ROS_DOMAIN_ID` are loaded automatically from
`~/.bashrc`. Check with `echo $ROS_DISTRO $ROS_DOMAIN_ID`.)

## Building

Always from the workspace folder, never from `src/`:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

| You changed... | Rebuild? |
|---|---|
| Code inside an existing node file (`.py`) | **No**, just stop the node (Ctrl + C) and run it again |
| Added a **new** node file and its entry point | **Yes** |
| `setup.py` or `package.xml` | **Yes** |
| Something is weird and nothing helps | Delete and rebuild: `rm -rf build install log`, then build again |

## Creating things

```bash
mkdir -p ~/ros2_ws/src                                  # a workspace
cd ~/ros2_ws/src
ros2 pkg create my_package --build-type ament_python --dependencies rclpy std_msgs
```

Package names: lowercase letters, numbers and underscores only. Put the
name **before** `--dependencies`.

New node checklist:

1. Create `~/ros2_ws/src/<package>/<package>/<node>.py` with a `main()` function
2. Add `'<command> = <package>.<node>:main',` to `entry_points` in `setup.py`
3. Rebuild and source
4. `ros2 run <package> <command>`

## Running and inspecting

| Command | What it does |
|---|---|
| `ros2 run gesture_bridge coordinator` | Start a node |
| `ros2 node list` | Running nodes |
| `ros2 node info /coordinator` | What one node publishes and subscribes to |
| `ros2 topic list` | All topics |
| `ros2 topic info /gesture` | Message type, number of publishers and subscribers |
| `ros2 topic echo /gesture std_msgs/msg/String` | Print every message on a topic |
| `ros2 topic hz /gesture` | How often messages arrive |
| `ros2 topic pub --once /gesture std_msgs/msg/String "{data: Thumb_Up}"` | Send one message by hand |
| `ros2 interface show std_msgs/msg/String` | Which fields a message type has |
| `rqt_graph` | Picture of nodes and topics (press refresh) |
| `ros2 pkg executables gesture_bridge` | Which nodes a package has |
| **Ctrl + C** | Stop a node |

Run a second copy of a node under another name:

```bash
ros2 run gesture_bridge coordinator --ros-args -r __node:=coordinator2
```

## Node skeleton

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MyNode(Node):

    def __init__(self):
        super().__init__('my_node')
        self.pub = self.create_publisher(String, '/my_topic', 10)                # to send
        self.sub = self.create_subscription(String, '/other', self.on_msg, 10)   # to receive
        self.timer = self.create_timer(0.5, self.on_timer)                       # every 0.5 s

    def on_msg(self, msg):
        self.get_logger().info(f'Got: {msg.data}')

    def on_timer(self):
        msg = String()
        msg.data = 'hello'
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
```

## Common errors

| You see | Cause | Fix |
|---|---|---|
| `Package 'gesture_bridge' not found` | This terminal isn't sourced, or the package was never built | `source ~/ros2_ws/install/setup.bash` (build first if needed) |
| `No executable found` | Typo in the node name, or the entry point is missing, or you didn't rebuild after adding it | Check `setup.py`, then rebuild and source |
| `ros2 pkg create: error: the following arguments are required: package_name` | The package name came after `--dependencies` | Put the name first: `ros2 pkg create my_package --build-type ...` |
| `Unknown license 'TODO: License declaration'` (warning) | No license was chosen | Harmless, ignore it |
| `build/`, `install/` and `log/` appeared inside `src/` | You ran `colcon build` inside `src/` | `rm -rf ~/ros2_ws/src/build ~/ros2_ws/src/install ~/ros2_ws/src/log`, then build from `~/ros2_ws` |
| `Could not determine the type for the passed topic` | `ros2 topic echo` started before anything published, so it can't guess the type | Add the type: `ros2 topic echo /gesture std_msgs/msg/String` |
| `ModuleNotFoundError: No module named 'cv2'` or `'mediapipe'` | MediaPipe isn't installed for Ubuntu's Python | Guide section 0.3 |
| `FileNotFoundError: Model not found: ...` | The model isn't at `~/mediapipe-first-steps/models/` | Clone the repo to your home folder and run `python3 download_models.py` |
| NumPy errors (`numpy.core.multiarray failed to import`, "compiled using NumPy 1.x") | NumPy 2 got installed | `python3 -m pip install --user "numpy<2" "opencv-contrib-python<4.11"` |
| `Could not open camera 0` | Another program is using the camera (only one at a time), or wrong camera number | Close the other program; try `CAMERA_INDEX = 1` |
| Camera picture is black | The ThinkPad privacy shutter is closed | Slide it open (above the screen) |
| The coordinator hears gestures you didn't make | Someone else is on your `ROS_DOMAIN_ID` | `echo $ROS_DOMAIN_ID` and check it's your number |
| The coordinator hears nothing | Different `ROS_DOMAIN_ID` in the two terminals, a typo in the topic name, or a gesture made in the first second after starting | Compare `echo $ROS_DOMAIN_ID`; compare topic names with `ros2 topic list`; wait a moment after starting |
| `[ros2run]: Process exited with failure 1` | Your node crashed | Scroll up: the real error (a Python traceback) is above this line |