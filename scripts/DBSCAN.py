#! /usr/bin/python
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np
from sklearn.cluster import DBSCAN

# Instantiate CvBridge
bridge = CvBridge()
pub = rospy.Publisher("dbscan", Image, queue_size=2)

blank_img = []


def poly_value(xy):
    global blank_img
    polynomial = np.polyfit(xy[:, 0], xy[:, 1], 2)
    a, b, c = polynomial
    # print(f"{a}\t{b}\t{c}")
    for element in xy[:, 0]:
        blank_img = cv2.circle(blank_img, tuple(
            [int(a*element*element+b*element+c), int(element)]), 5, (255, 0, 255), 1)


def image_callback(msg):
    #time1 = rospy.Time.now()
    # print(f"{(msg.header.stamp-time1).to_sec():.2f}")
    # print(msg.header.stamp - time1)
    print("Image received")
    global blank_img
    try:
        # Convert your ROS Image message to OpenCV2
        img = bridge.imgmsg_to_cv2(msg, "mono8")
    except CvBridgeError as e:
        print(e)
    blank_img = np.zeros(
        (img.shape[0], img.shape[1], 3), dtype=np.uint8)

    indexes_points = []
    for index, element in np.ndenumerate(img):
        if element != 0:
            indexes_points.append([index[0], index[1]])

    indexes_points = np.array(indexes_points)

    X = indexes_points
    db = DBSCAN(eps=25, min_samples=40, algorithm='auto').fit(X)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    # print(len(set(labels)))
    # n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)  ,this can be used when we need to see how many clusters

    unique_labels = set(labels)
    colors = [(0, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
    # print(colors)
    for k, col in zip(unique_labels, colors):
        if k == -1:
            col = (0, 0, 0)
        class_member_mask = (labels == k)
        xy_core = X[class_member_mask & core_samples_mask]
        xy_non_core = X[class_member_mask & ~core_samples_mask]
        xy = np.concatenate([xy_core, xy_non_core])
        for element in xy:
            blank_img = cv2.circle(blank_img, tuple(
                [element[1], element[0]]), 0, col, -1)
        poly_value(xy)
    pub.publish(bridge.cv2_to_imgmsg(blank_img, "passthrough"))
    #time2 = rospy.Time.now()
    #print(f"{(time1 - msg.header.stamp).to_sec():.2f}\t{(time2-time1).to_sec():.2f}")


def main():
    rospy.init_node('DBSCAN')
    # Define your image topic
    image_topic = "top_view"
    # Set up your subscriber and define its callback
    rospy.Subscriber(image_topic, Image, image_callback)
    # Spin until ctrl + c
    rospy.spin()


if __name__ == '__main__':
    main()
