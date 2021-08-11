#!/usr/bin/env python
# license removed for brevity
import rospy
import paho.mqtt.client as mqtt
import time
import sys
import re
import numpy as np
from matplotlib.animation import FuncAnimation
import csv

from std_msgs.msg import String
from geometry_msgs.msg import TransformStamped

HOST = '10.0.0.254'
PORT = 1883
TOPIC = 'tags'
DURATION = 500
logX = 0
logY = 0
logZ = 0
tags = {"logX": logX, "logY": logY, "logZ": logZ}


class PozyxBridge(object):

    def __init__(self):
        # Setting initial position
        self.logX = 0
        self.logY = 0
        self.logZ = 0
        self.tags = {"tagId": "-", "logX": logX, "logY": logY, "logZ": logZ}
        # Publisher
        self.client = mqtt.Client()  # create new instance
        self.pub = rospy.Publisher('uwb_sensor', TransformStamped, queue_size=10)
        self.transform_msg = TransformStamped()

    # MQTT client setup

    def setup_client(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message  # attach function to callback
        self.client.on_subscribe = self.on_subscribe
        # time.sleep(DURATION)  # wait for duration seconds
        self.client.connect(HOST, port=PORT)  # connect to host
        self.client.subscribe(TOPIC)  # subscribe to topic

    def run(self):
        self.client.loop_start()  # start the loop
        rate = rospy.Rate(10)  # 10hz

        while not rospy.is_shutdown():
            self.transform_msg.header.stamp = rospy.Time.now()
            rospy.loginfo(self.transform_msg)
            self.pub.publish(self.transform_msg)
            rate.sleep()

    def on_message(self, client, userdata, message):
        # transform_msg = TransformStamped()
        #
        # self.transform_msg.header.stamp = rospy.Time.now()

        tagId = re.search(r'(\"tagId\"\:\")(\d+)', message.payload.decode())
        x = re.search(r'(?:"x":)(-\d+|\d+)', message.payload.decode())
        y = re.search(r'(?:"y":)(-\d+|\d+)', message.payload.decode())
        z = re.search(r'(?:"z":)(-\d+|\d+)', message.payload.decode())
        self.tags["tagId"] = int(tagId.group(2))
        if x is not None:
            self.tags["logX"] = int(x.group(1))
            self.tags["logY"] = int(y.group(1))
            self.tags["logZ"] = int(z.group(1))

            self.transform_msg.transform.translation.x = self.tags["logX"]
            self.transform_msg.transform.translation.y = self.tags["logY"]
            self.transform_msg.transform.translation.z = self.tags["logZ"]
        else:

            self.transform_msg.transform.translation.x = self.tags["logX"]
            self.transform_msg.transform.translation.y = self.tags["logY"]
            self.transform_msg.transform.translation.z = self.tags["logZ"]

        # rospy.loginfo(self.transform_msg)
        # self.pub.publish(self.transform_msg)

    def on_connect(self, client, userdata, flags, rc):
        print(mqtt.connack_string(rc))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed to topic!")


if __name__ == '__main__':
    rospy.init_node('pozyx_bridge', anonymous=True)
    try:

        # while not rospy.is_shutdown():
        pozyx_bridge = PozyxBridge()
        pozyx_bridge.setup_client()
        pozyx_bridge.run()

    except rospy.ROSInterruptException:
        pass
