import cv2
import time
import socket
import color_tracker
import numpy as np
from socket_server import ThreadedServer

Server = None
last_finger_center = None
last_joint_center = None
finger_disappeared = 0
trigger = False
last_time = 0

# 6 cm wid * 11 cm len phone
# 1080 / 6 = 180 pixel/cm  1920/11 = 175 pixel/cm
fix_locate_points = [[6.0*(1.0-5.8/np.sqrt(40)) * 180, (11.0-2.0*5.8/np.sqrt(40))*175],\
                     [6.0*(1.0-7/np.sqrt(66.25))*180,(11.0-5.5*7/np.sqrt(66.25))*175],\
                     [6.0*(1.0-9.5/np.sqrt(157))*180,(11.0-11.0*9.5/np.sqrt(157))*175],\
                     [(6-4*9/np.sqrt(137))*180,(11-11*9/np.sqrt(137))*175],\
                     [(6-2*9/np.sqrt(125))*180,(11-11*9/np.sqrt(125))*175]]

angles = [np.arctan(2.0/6), np.arctan(5.5/6), np.arctan(11/6.0), np.arctan(11/4.0), np.arctan(11/2.0)]

def tracking_callback():
    global last_finger_center, last_joint_center, finger_disappeared, trigger, last_time
    t = time.time()
    if (t - last_time)*1000 < 20:
        return None
    last_time = t
    # timer = cv2.getTickCount()
    # frame = tracker.get_frame()
    debug_frame = tracker.get_debug_image()
    # fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer);
    finger_center = tracker.get_last_object_center()[0]
    joint_center = tracker.get_last_object_center()[1]
    finger_center_filtered = tracker.get_smooth_center()[0]
    joint_center_filtered  = tracker.get_smooth_center()[1]

    # cv2.imshow("original frame", frame)
    cv2.imshow("debug frame", debug_frame)
  
    key = cv2.waitKey(1)
    if key == 27:
        tracker.stop_tracking()

    # print("Object center: {0}".format(object_center))
    moveY, moveX = 0, 0
    if last_finger_center is None:
        last_finger_center = finger_center_filtered
    if last_joint_center is None:
        last_joint_center = joint_center_filtered

    if finger_center is not None:
        if finger_disappeared > 3 and joint_center is not None:
            finger_disappeared = 0
            trigger = True
            print ("trigger.")
            moveX = (finger_center[0] - joint_center[0]) * 10
            moveY = (finger_center[1] - joint_center[1]) * 10
        else:
            moveX = (finger_center_filtered[0] - last_finger_center[0]).sum() * 10
            moveY = (finger_center_filtered[1] - last_finger_center[1]).sum() * 10
    elif joint_center is not None:
        finger_disappeared += 1
    else:
        finger_disappeared = 0
        trigger = False

    moveX = -moveX
    if Server.client:
        try:
            command = "move"
            if trigger:
                command = "trig"
                move_rad = np.arctan(np.fabs(moveY/moveX))
                moveX = fix_locate_points[2][0]
                moveY = fix_locate_points[2][1]
                if move_rad <= angles[0]:
                    moveX, moveY = fix_locate_points[0][0], fix_locate_points[0][1]
                elif move_rad <= angles[1]:
                    moveX, moveY = fix_locate_points[1][0], fix_locate_points[1][1]
                elif move_rad >= angles[3]:
                    moveX, moveY = fix_locate_points[3][0], fix_locate_points[3][1]
                elif move_rad >= angles[4]:
                    moveX, moveY = fix_locate_points[4][0], fix_locate_points[4][1]

            Server.client.send("{0},{1},{2}\n".format(command, moveX, moveY).encode())
        except Exception as e:
            print (e)
            Server.client.close()
            Server.client = None
            Server.start()

    trigger = False
    last_finger_center = finger_center_filtered
    last_joint_center = joint_center_filtered

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    myip = s.getsockname()[0]
    print (myip)
    s.close()
    Server = ThreadedServer(myip, 1234)
    Server.start()

    webcam = color_tracker.WebCamera(video_src=0)
    webcam.start_camera()

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    tracker = color_tracker.ColorTracker(camera=webcam, max_nb_of_points=10, debug=True)

    tracker.set_tracking_callback(tracking_callback=tracking_callback)

    tracker.track(hsv_lower_values=[(0, 213, 122), (96, 164, 100)],
                  hsv_upper_values=[(12, 255, 255), (255, 255, 255)],
                  min_contour_areas=[10, 10],
                  kernels=[kernel, kernel],
                  input_image_type="bgr")

    webcam.release_camera()
