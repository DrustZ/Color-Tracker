import cv2
import socket
import color_tracker
from socket_server import ThreadedServer

Server = None
last_finger_center = None
last_joint_center = None
finger_disappeared = 0
trigger = False

#50 * 100
def tracking_callback():
    global last_finger_center, last_joint_center, finger_disappeared, trigger
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

    if Server.client:
        try:
            command = "move"
            if trigger:
                command = "trig"

            Server.client.send("{0},{1},{2}\n".format(command, moveX, moveY).encode())
        except Exception as e:
            print (e)
            Server.client.close()
            Server.client = None

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

    webcam = color_tracker.WebCamera(video_src=1)
    webcam.start_camera()

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    tracker = color_tracker.ColorTracker(camera=webcam, max_nb_of_points=10, debug=True)

    tracker.set_tracking_callback(tracking_callback=tracking_callback)

    tracker.track(hsv_lower_values=[(160, 155, 133), (86, 52, 96)],
                  hsv_upper_values=[(255, 255, 255), (145, 255, 168)],
                  min_contour_areas=[30, 10],
                  kernels=[kernel, kernel],
                  input_image_type="bgr")

    webcam.release_camera()
