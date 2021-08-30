#!/usr/bin/env python
# license removed for brevity
import rospy
import tf2_ros
import rosparam

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


class PozyxBridge(object):

    def __init__(self):
        # Flags
        self.is_data_available = False
        # Setting initial position
        self.tagdic = {}
        # self.index = 0
        self.taglist = rospy.get_param("/tag_list")
        self.paramdic = {}
        for i in self.taglist:
            self.paramdic[rospy.get_param("/" + i + "/id")] = i
        # rospy.loginfo("These tag are in tag list %s", self.paramdic)
        # Publisher
        self.client = mqtt.Client()  # create new instance
        self.pub = rospy.Publisher('uwb_sensor', TransformStamped, queue_size=10)
        self.timer = rospy.Timer(rospy.Duration(0.1), self.time_record)
        self.br = tf2_ros.TransformBroadcaster()

    def time_record(self, event):
        if not self.is_data_available is True:
            return
        for i in self.tagdic.keys():
            # rospy.loginfo(self.tagdic[i])
            self.tagdic[i].header.stamp = rospy.Time.now()
            self.pub.publish(self.tagdic[i])
            self.br.sendTransform(self.tagdic[i])

    # MQTT client setup
    def setup_client(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message  # attach function to callback
        self.client.on_subscribe = self.on_subscribe
        self.client.connect(HOST, port=PORT)  # connect to host
        self.client.subscribe(TOPIC)  # subscribe to topic

    def run(self):
        self.client.loop_start()  # start the loop
        rate = rospy.Rate(10)  # 10hz

        while not rospy.is_shutdown():
            rate.sleep()

    def on_message(self, client, userdata, message):

        tagId = re.search(r'(\"tagId\"\:\")(\d+)', message.payload.decode())
        x = re.search(r'(?:"x":)(-\d+|\d+)', message.payload.decode())
        y = re.search(r'(?:"y":)(-\d+|\d+)', message.payload.decode())
        z = re.search(r'(?:"z":)(-\d+|\d+)', message.payload.decode())
        Id = int(tagId.group(2))
        # Writing warning here ---
        # pozyx_bridge.error_report(Id)
        # flag = False
        # if Id not in self.paramdic.keys():
        #     rospy.logwarn("Active tag %s is not define in Parameter Id!", Id)
        # for i in self.paramdic.keys():
        #     if i not in self.tagdic.keys():
        #         flag = True
        # if flag:
        #     rospy.logwarn("Parameter Id %s are not apply on all active tags", self.paramdic.keys())
        if Id not in self.paramdic.keys():
            rospy.logwarn("Active tag %s is not define in Parameter Id!", Id)
            for i in self.paramdic.keys():
                if i not in self.tagdic.keys():
                    rospy.logwarn("Parameter Id %s are not active", i)
            return
        if Id not in self.tagdic.keys():
            rospy.loginfo("Tag %s is now active", Id)
            transform_msg = TransformStamped()
            transform_msg.header.frame_id = rospy.get_param("/frame_id")
            self.tagdic[Id] = transform_msg
            temtag = self.paramdic[Id]
            self.tagdic[Id].child_frame_id = rospy.get_param("/" + temtag + "/child_frame_id")

        else:
            if x is not None:
                self.tagdic[Id].transform.translation.x = int(x.group(1)) / 1000.0
                self.tagdic[Id].transform.translation.y = int(y.group(1)) / 1000.0
                self.tagdic[Id].transform.translation.z = int(z.group(1)) / 1000.0
                self.tagdic[Id].transform.rotation.w = 1

                # self.tagdic[Id].child_frame_id = self.tagdic[Id]["child_frame_id"]
                # self.transform_msg.transform.translation.x = self.tagdic[Id]["logX"] / 1000.0
                # self.transform_msg.transform.translation.y = self.tagdic[Id]["logY"] / 1000.0
                # self.transform_msg.transform.translation.z = self.tagdic[Id]["logZ"] / 1000.0
                # self.transform_msg.transform.rotation.w = 1

                if not self.is_data_available:
                    self.is_data_available = True

        for i in self.paramdic.keys():
            if i not in self.tagdic.keys():
                rospy.logwarn("Parameter Id %s are not active", i)

    def on_connect(self, client, userdata, flags, rc):
        print(mqtt.connack_string(rc))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed to topic!")


if __name__ == '__main__':
    rospy.init_node('pozyx_bridge')
    try:
        pozyx_bridge = PozyxBridge()
        pozyx_bridge.setup_client()
        pozyx_bridge.run()

    except rospy.ROSInterruptException:
        pass
