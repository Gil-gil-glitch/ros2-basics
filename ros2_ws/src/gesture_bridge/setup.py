from setuptools import find_packages, setup

package_name = 'gesture_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gilsocojp',
    maintainer_email='gilsocojp@gmail.com',
    description='Publishes hand gestures from a webcam and replies to them',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'coordinator = gesture_bridge.coordinator:main',
            'gesture_publisher = gesture_bridge.gesture_publisher:main',
        ],
    },
)