# ROS 2 Basics: From Gesture to Message

In this lesson you'll build your first ROS 2 system: two programs that talk
to each other.

```
 ┌───────────────────┐   /gesture    ┌───────────────┐
 │ gesture_publisher │ ────────────> │  coordinator  │ ──> "Thumb_Up -> Nice to see you too!"
 │ webcam+MediaPipe  │   (String)    │  logs a reply │
 └───────────────────┘               └───────────────┘
```

The gesture recognizer is the one from MediaPipe lesson 08. What's new is
**how the programs are connected**, and that's the skill you'll use in your
project.

**You need:** a ThinkPad with Ubuntu 22.04 and ROS 2 Humble, and the
MediaPipe lessons (Parts 1 and 2) finished.

**Keep [`CHEATSHEET.md`](CHEATSHEET.md) open** while you work. It has every
command from this guide and fixes for the most common errors.

Type the code yourself instead of copying and pasting it. You'll make
mistakes, and fixing them is how ROS 2 starts to make sense.

---

## Contents

0. [Setup (once per ThinkPad)](#0-setup-once-per-thinkpad)
1. [What is ROS 2?](#1-what-is-ros-2)
2. [Create a workspace and a package](#2-create-a-workspace-and-a-package)
3. [The coordinator node (subscriber)](#3-the-coordinator-node-subscriber)
4. [The gesture publisher node](#4-the-gesture-publisher-node)
5. [Look inside your running system](#5-look-inside-your-running-system)
6. [Check your understanding](#6-check-your-understanding)
7. [Toward your project](#7-toward-your-project)

---

## 0. Setup (once per ThinkPad)

### 0.1 Check that ROS 2 is ready

Open a terminal (**Ctrl + Alt + T**) and run:

```bash
echo $ROS_DISTRO
```

It should print `humble`. If it prints nothing, ROS 2 isn't loaded in your
terminals yet. Add it to `~/.bashrc` (a script that runs every time you open
a terminal), then reload it:

```bash
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
source ~/.bashrc
```

### 0.2 Set your ROS_DOMAIN_ID

ROS 2 programs find each other **automatically over the network**. That's
useful for robots, but in a classroom it means your coordinator would hear
everyone else's gestures too. Each of you gets a private "channel" number
called `ROS_DOMAIN_ID`. Your teacher will give you yours (1 to 101).

```bash
echo 'export ROS_DOMAIN_ID=YOUR_NUMBER' >> ~/.bashrc     # e.g. export ROS_DOMAIN_ID=17
source ~/.bashrc
echo $ROS_DOMAIN_ID                                       # check
```

### 0.3 Install MediaPipe and get the model

ROS 2 Humble uses Ubuntu's own Python, so we install MediaPipe there with
`--user` instead of in a virtual environment (a virtual environment would
hide ROS 2's Python packages).

The version limits are important: newer versions bring in NumPy 2, which
breaks ROS 2 Humble's Python packages.

```bash
python3 -m pip install --user mediapipe "numpy<2" "opencv-contrib-python<4.11"
```

If it says `No module named pip`, install pip first with
`sudo apt install python3-pip` and try again.

The gesture node loads the model from your MediaPipe lessons folder, so the
folder must be in your home folder as `~/mediapipe-first-steps`:

```bash
cd ~
git clone <URL of the mediapipe-first-steps repository>
cd ~/mediapipe-first-steps
python3 download_models.py
```

Check that everything imports together:

```bash
python3 -c "import rclpy, cv2, mediapipe; print('All good!')"
```

### 0.4 Check the camera

```bash
python3 ~/mediapipe-first-steps/lessons/part1_opencv/01_open_camera.py
```

**Black picture?** ThinkPads have a small sliding cover over the camera (the
privacy shutter) above the screen. Slide it open.

---

## 1. What is ROS 2?

ROS 2 (Robot Operating System 2) isn't an operating system. It's a toolkit
that lets **many small programs work together** as one robot system. Each
program does one job, and they send each other messages.

| Word | Meaning | In today's lesson |
|---|---|---|
| **Node** | One running program with one job | `gesture_publisher`, `coordinator` |
| **Topic** | A named channel that messages travel on | `/gesture` |
| **Message** | One piece of data with a fixed type | a `std_msgs/String`, e.g. `"Thumb_Up"` |
| **Publisher** | A node that **sends** messages on a topic | `gesture_publisher` |
| **Subscriber** | A node that **receives** messages from a topic | `coordinator` |

A topic is like a group chat. Publishers post to it and every subscriber
gets a copy. They don't need to know about each other; they only need to
agree on the **topic name** and the **message type**.

### Why split things into nodes?

Imagine your project. The robot doesn't care **where** the movement
commands come from:

```
 camera + MediaPipe node ──┐
                           ├──> /arm_angles ──> robot node ──> motors
 glove + sensors node    ──┘
```

If the camera node and the glove node publish the same kind of message on
the same topic, you can swap one for the other without changing a single
line of the robot code. Each team member can also work on a different node
at the same time.

### See it working (2 minutes)

ROS 2 comes with two example nodes. Open **two terminals**.

```bash
# Terminal 1
ros2 run demo_nodes_py talker
```

```bash
# Terminal 2
ros2 run demo_nodes_py listener
```

The talker publishes "Hello World" messages on the topic `/chatter`, and the
listener prints them. Now open a **third terminal** and run `rqt_graph` to
see a picture of the nodes and the topic connecting them. Stop everything
with **Ctrl + C** in each terminal.

Today you'll build your own version of this, with gestures.

---

## 2. Create a workspace and a package

A **workspace** is a folder where you build ROS 2 code. A **package** is one
unit of code inside it, usually several related nodes.

```
~/ros2_ws/                 <- the workspace (you run colcon build HERE)
└── src/                   <- your packages go in here
    └── gesture_bridge/    <- the package you'll create
```

### 2.1 Create the workspace

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
```

### 2.2 Create the package

```bash
ros2 pkg create gesture_bridge --build-type ament_python --dependencies rclpy std_msgs
```

- `gesture_bridge` is the package name. **Use letters, numbers and
  underscores only. No hyphens (`-`) or spaces.**
- `--build-type ament_python` means the package is written in Python.
- `--dependencies rclpy std_msgs` records that we need `rclpy` (ROS 2 for
  Python) and `std_msgs` (standard message types like `String`).

You'll see a warning that says `Unknown license 'TODO: License declaration'`.
That's harmless: it only means we didn't choose a software license.

> **Careful with the order:** the package name must come *before*
> `--dependencies`. That option takes every word after it as a dependency,
> so `ros2 pkg create --dependencies rclpy std_msgs gesture_bridge` thinks
> `gesture_bridge` is a dependency and complains that the package name is missing.

### 2.3 What's inside?

```bash
cd ~/ros2_ws/src/gesture_bridge
ls -R
```

```
gesture_bridge/                  <- the package
├── package.xml                  <- name, description, dependencies
├── setup.py                     <- how to install it, and the list of nodes (entry points)
├── setup.cfg                    <- tells ROS 2 where to put the node programs (don't edit)
├── resource/gesture_bridge      <- empty marker file so ROS 2 can find the package (don't edit)
├── gesture_bridge/              <- YOUR PYTHON CODE GOES HERE (same name as the package)
│   └── __init__.py
└── test/                        <- automatic style checks (ignore for today)
```

Yes, there's a `gesture_bridge` folder inside the `gesture_bridge` folder.
The outer one is the **package**; the inner one is the **Python module**
where your node files go.

### 2.4 Build it for the first time

Builds always run from the **workspace folder**, never from `src/`:

```bash
cd ~/ros2_ws
colcon build --symlink-install
```

`colcon` is ROS 2's build tool. `--symlink-install` links to your Python
files instead of copying them, so later edits to them work **without
rebuilding**. Always use it.

You now have three new folders:

| Folder | What it is |
|---|---|
| `build/` | Temporary build files |
| `install/` | The finished package, which is what ROS 2 actually runs |
| `log/` | Build logs, useful when something goes wrong |

You never edit these. If they get confused, you can delete all three and build again.

### 2.5 Source the workspace

```bash
source install/setup.bash
ros2 pkg list | grep gesture_bridge
```

"Sourcing" tells **this terminal** where your workspace is. It prints
`gesture_bridge` if it worked.

> **Remember:** every new terminal needs `source ~/ros2_ws/install/setup.bash`
> before it can find your package. This is the most common ROS 2 mistake.

---

## 3. The coordinator node (subscriber)

We start with the coordinator, the node that **listens**, because it's
short and you can test it without a camera.

### 3.1 Version 1: log what arrives

Create the file:

```bash
cd ~/ros2_ws/src/gesture_bridge/gesture_bridge
gedit coordinator.py          # or: code coordinator.py  (VS Code)
```

**File:** `~/ros2_ws/src/gesture_bridge/gesture_bridge/coordinator.py`

<!-- file: coordinator_v1 -->
```python
"""Coordinator node: listens to /gesture and logs what it receives."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Coordinator(Node):

    def __init__(self):
        super().__init__('coordinator')   # the node's name, shown by "ros2 node list"
        # Call self.on_gesture every time a String arrives on /gesture.
        # 10 = how many messages to keep waiting if we fall behind.
        self.subscription = self.create_subscription(
            String, '/gesture', self.on_gesture, 10)
        self.get_logger().info('Coordinator ready. Waiting for gestures on /gesture...')

    def on_gesture(self, msg):
        self.get_logger().info(f'Received: {msg.data}')


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
```

**What each part does:**

| Code | Meaning |
|---|---|
| `class Coordinator(Node)` | Every ROS 2 node is a class that inherits from `Node`. |
| `super().__init__('coordinator')` | Gives the node its name. |
| `create_subscription(String, '/gesture', self.on_gesture, 10)` | "When a `String` arrives on `/gesture`, call `on_gesture`." |
| `on_gesture(self, msg)` | A **callback**: you never call it yourself, ROS 2 does. The text is in `msg.data`. |
| `self.get_logger().info(...)` | ROS 2's `print`. It adds the time and node name, and can be saved to log files. |
| `rclpy.init()` / `rclpy.spin()` / `rclpy.shutdown()` | Start ROS 2, keep the node alive and responding, clean up at the end. |

### 3.2 Register the node: the entry point

ROS 2 doesn't know about `coordinator.py` yet. Open
`~/ros2_ws/src/gesture_bridge/setup.py` and find `entry_points` near the
bottom. Add one line:

```python
    entry_points={
        'console_scripts': [
            'coordinator = gesture_bridge.coordinator:main',
        ],
    },
```

Read it as: *"the command `coordinator` runs the function `main` in
`gesture_bridge/coordinator.py`."* The name on the left is what you type
after `ros2 run gesture_bridge`.

### 3.3 Build, source, run

A new entry point **always** needs a rebuild:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 run gesture_bridge coordinator
```

You should see:

```
[INFO] [...] [coordinator]: Coordinator ready. Waiting for gestures on /gesture...
```

It's waiting. Nothing is publishing yet.

### 3.4 Send it a message by hand

Open a **second terminal** and publish one message yourself:

```bash
source ~/ros2_ws/install/setup.bash
ros2 topic pub --once /gesture std_msgs/msg/String "{data: Thumb_Up}"
```

Terminal 1 now shows `Received: Thumb_Up`. Try a few other words.

You just tested a node **without the program that will normally talk to
it**. This is how you test robot code without a robot: publish fake
messages by hand.

### 3.5 Version 2: reply to each gesture

Now make the coordinator *say something*. Change `coordinator.py` to this
(the new parts are `REPLIES` and the new `on_gesture`):

<!-- file: coordinator -->
```python
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
```

Save, then in terminal 1 press **Ctrl + C** and run it again:

```bash
ros2 run gesture_bridge coordinator
```

**No rebuild needed**: thanks to `--symlink-install`, edits to an existing
Python file are used straight away. You only rebuild when you add a **new**
node or change `setup.py` or `package.xml`.

Test it again from terminal 2:

```bash
ros2 topic pub --once /gesture std_msgs/msg/String "{data: Victory}"
ros2 topic pub --once /gesture std_msgs/msg/String "{data: Wave}"
```

```
[INFO] [...] [coordinator]: Victory -> Peace!
[INFO] [...] [coordinator]: I saw "Wave", but I have no reply for it.
```

---

## 4. The gesture publisher node

Now the node that **talks**: it recognizes gestures from the webcam and
publishes them on `/gesture`.

### 4.1 What changes from MediaPipe lesson 08?

The MediaPipe part is the same. Three things change:

| Lesson 08 (plain Python) | ROS 2 node |
|---|---|
| `while True:` loop reads the camera | `create_timer(1/30, self.on_timer)`: ROS 2 calls `on_timer` 30 times per second |
| `print(gesture)` | `self.gesture_pub.publish(msg)`: send it to every subscriber |
| Settings from `argparse` | Constants at the top of the file (simpler for today) |

Why a timer instead of `while True`? `rclpy.spin()` must keep running so ROS
2 can do its work: sending messages, answering `ros2 node info`, shutting
down cleanly. A `while True` loop would block it.

### 4.2 Publish only when the gesture changes

The camera sees your thumbs up 30 times per second. Should we publish 30
messages per second? No: a gesture is an **event** ("the user just did a
thumbs up"). We publish once, when a gesture has been held for
`HOLD_FRAMES` frames and is different from the last one. That's the same
debouncing idea as lesson 08.

(Arm angles for mimicking will be different. More on that in [section 7](#7-toward-your-project).)

### 4.3 Write the node

```bash
cd ~/ros2_ws/src/gesture_bridge/gesture_bridge
gedit gesture_publisher.py
```

**File:** `~/ros2_ws/src/gesture_bridge/gesture_bridge/gesture_publisher.py`

<!-- file: gesture_publisher -->
```python
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
```

**The ROS 2 parts:**

| Code | Meaning |
|---|---|
| `create_publisher(String, '/gesture', 10)` | "I will send `String` messages on `/gesture`." Same topic name and type as the coordinator's subscription. That's what connects them. |
| `create_timer(1.0 / 30, self.on_timer)` | Call `on_timer` every 1/30 of a second. |
| `msg = String()` then `msg.data = gesture` | Build a message. Every message type has its own fields; `String` has just `data`. |
| `self.gesture_pub.publish(msg)` | Send it. Every subscriber to `/gesture` gets a copy. |
| `close()` in `finally` | Release the camera even if the node crashes, so the next run can open it. |

### 4.4 Register it and rebuild

Add a second line to `entry_points` in `setup.py`:

```python
    entry_points={
        'console_scripts': [
            'coordinator = gesture_bridge.coordinator:main',
            'gesture_publisher = gesture_bridge.gesture_publisher:main',
        ],
    },
```

New entry point, so rebuild:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### 4.5 Run the whole system

You'll use three terminals. Remember to source in each new one.

```bash
# Terminal 1: the listener
source ~/ros2_ws/install/setup.bash
ros2 run gesture_bridge coordinator
```

```bash
# Terminal 2: the camera
source ~/ros2_ws/install/setup.bash
ros2 run gesture_bridge gesture_publisher
```

```bash
# Terminal 3: watch the raw messages on the topic
source ~/ros2_ws/install/setup.bash
ros2 topic echo /gesture std_msgs/msg/String
```

Show a thumbs up to the camera. Terminal 2 says `Published: Thumb_Up`,
terminal 3 shows `data: Thumb_Up`, and terminal 1 replies. 🎉

Stop the nodes with **Ctrl + C** in their terminals.

> **A gesture got lost?** Right after a node starts, the nodes need a second
> or two to find each other. A message published in that moment reaches
> nobody, because ROS 2 doesn't store old messages for subscribers that
> arrive late. Wait a moment after starting before you gesture.

---

## 5. Look inside your running system

With both nodes running, use a fourth terminal to explore. These tools work
on any ROS 2 system, including your project's robot, so get comfortable with them.

```bash
ros2 node list                  # which nodes are running?
ros2 node info /coordinator     # what does one node publish and subscribe to?
ros2 topic list                 # which topics exist?
ros2 topic info /gesture        # message type, number of publishers and subscribers
ros2 topic hz /gesture          # how often messages arrive
rqt_graph                       # a picture of the whole system
```

In `rqt_graph`, click the refresh button (top left) if the picture is empty.
You should see `/gesture_publisher → /gesture → /coordinator`.

**Questions to discuss:**

- `ros2 topic hz /gesture` shows irregular, slow numbers, or nothing for a
  while. Why? (Hint: section 4.2.)
- What happens to the coordinator if you stop the gesture publisher? Does it crash?
- Start the coordinator **after** the gesture publisher. Does it still work?
  Why does the order not matter?

---

## 6. Check your understanding

Try these on your own. None of them should take more than a few lines.

1. **Add a reply.** Add a reply for one more gesture to `REPLIES`. Do you need
   to rebuild? Why or why not?
2. **Count gestures.** Make the coordinator also log how many gestures it
   has received so far, e.g. `Thumb_Up -> Nice to see you too! (3 gestures so far)`.
3. **Two listeners.** Run a second coordinator under a different name:
   ```bash
   ros2 run gesture_bridge coordinator --ros-args -r __node:=coordinator2
   ```
   How many subscribers does `ros2 topic info /gesture` show now? Do both
   reply to the same gesture?
4. **Change channels.** In one terminal run `export ROS_DOMAIN_ID=99`, then
   start a coordinator there. Does it hear your gestures? Why not?
5. **Break it on purpose.** Change the topic name in `gesture_publisher.py` to
   `/gestures` (with an s). What happens? What does `rqt_graph` show?
   Change it back afterwards.

---

## 7. Toward your project

Your project is to make a physical robot copy a person's arm and hand, using
a camera or a glove. Everything you did today scales up to that.

### Events vs. streams

| | Gestures (today) | Arm angles (your project) |
|---|---|---|
| What it is | An **event**: "a thumbs up happened" | A **stream**: "the elbow is at 87 degrees *right now*" |
| When to publish | Once, when it changes | Every frame, at a steady rate (e.g. 20-30 times per second) |
| Message type | `std_msgs/String` | Numbers, e.g. `std_msgs/Float64MultiArray` or `sensor_msgs/JointState` |

### Your input is "just another node"

- **Camera team:** your MediaPipe pose code (lessons 09-11) goes inside a
  node, exactly like `gesture_publisher`, but it publishes angles.
- **Glove team:** your glove's sensor readings go inside a node that reads
  them (for example over USB serial) and publishes angles.
- **Robot side:** a node that subscribes to the angles and moves the motors.

If both teams agree on the **topic name, message type and units** (radians or
degrees?), the robot node works with either input.

### Before you write code: design it

As a team, answer these and draw your own `rqt_graph` on paper:

1. Which nodes will you have? What is each one's single job?
2. Which topics connect them? What's the name of each?
3. What message type and units does each topic carry?
4. How often is each topic published?
5. How will you test each node on its own, without the others?
   (Remember `ros2 topic pub` from section 3.4.)