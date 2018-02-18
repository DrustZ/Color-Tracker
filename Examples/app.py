import cv2
import time
import socket
import color_tracker
import numpy as np

cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
cs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

last_finger_center = None
last_joint_center = None
finger_disappeared = 0
trigger = False
last_time = 0
angle = 0
cnt = 0 

throw_mode = 0

# w cm wid * h cm len phone
# 1080 / w =  pixel/cm  1920/h =  pixel/cm
w,h = 7.5, 12.5
pcw, pch = 1080/w, 1920/h
line1, line2, line3, line4 = np.sqrt(w**2+4), np.sqrt(w**2+h**2/4), np.sqrt(w**2+h**2), np.sqrt(1/4*w**2+h**2)
flen1, flen2, flen3, flen4 = 5.5, 6, 6.5, 7
pos1, pos2, pos3, pos4 = (line1-flen1)/2+flen1, (line2-flen2)/2+flen2, (line3-flen3)/2+flen3, (line4-flen4)/2+flen4
fix_locate_points = [[20, (h-2.0*pos1/line1)*pch],\
                     [20, (h-h/2*pos2/line2)*pch],\
                     [20, 180],\
                     [w*pcw-20,180]]

print (fix_locate_points)

angles = [np.arctan(2.0/w), np.arctan(h/2/w), np.arctan(h/w), np.arctan(h*2/w)]
print (angles)

def choose_angles(mode, move_rad):
    moveX = fix_locate_points[2][0]
    moveY = fix_locate_points[2][1]
    if mode == 0:
        if move_rad <= angles[0]:
            moveX, moveY = fix_locate_points[0][0], fix_locate_points[0][1]
            print ("pos 1")
        elif move_rad <= angles[1]:
            moveX, moveY = fix_locate_points[1][0], fix_locate_points[1][1]
            print ("pos 2")
        elif move_rad >= angles[3]:
            moveX, moveY = fix_locate_points[3][0], fix_locate_points[3][1]
            print ("pos 3")
    return moveX, moveY


def tracking_callback():
    global last_finger_center, last_joint_center, finger_disappeared, trigger, last_time, last_movey, last_movex, angle, cnt
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
            moveX = (finger_center[0] - joint_center[0]) * 10
            moveY = (finger_center[1] - joint_center[1]) * 10
            # print (np.sqrt(moveX**2+moveY**2))
        else:
            moveX = (finger_center_filtered[0] - last_finger_center[0]).sum() * 10
            moveY = (finger_center_filtered[1] - last_finger_center[1]).sum() * 10
    elif joint_center is not None:
        finger_disappeared += 1
    else:
        finger_disappeared = 0
        trigger = False

    # assemble command
    # moveX = -moveX
    moveY = -moveY
    command = "move"
    # cnt += 1
    if trigger and throw_mode == 0:
        command = "trig"
        print ("trigger.")
        if moveX == 0:
            moveX = 1e-10
        angle = np.arctan(np.fabs(moveY/moveX))
        moveX, moveY = choose_angles(throw_mode, angle)
        trigger = False
    # if trigger and throw_mode == 1:
    #     command = "trig"
    #     moveX, moveY = choose_angles(throw_mode, angle)
    #     trigger = False

    cs.sendto("{0},{1},{2}".format(command, moveX, moveY).encode(), ('192.168.1.27', 12345))

    last_finger_center = finger_center_filtered
    last_joint_center = joint_center_filtered

if __name__ == "__main__":
    webcam = color_tracker.WebCamera(video_src=1)
    webcam.start_camera()

    kernel1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
    kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    tracker = color_tracker.ColorTracker(camera=webcam, max_nb_of_points=10, debug=True)

    tracker.set_tracking_callback(tracking_callback=tracking_callback)

    tracker.track(hsv_lower_values=[(37, 75, 44), (0, 164, 192)],
                  hsv_upper_values=[(87, 255, 253), (255, 255, 255)],
                  min_contour_areas=[150, 50],
                  kernels=[kernel1, kernel2],
                  input_image_type="bgr")

    webcam.release_camera()
