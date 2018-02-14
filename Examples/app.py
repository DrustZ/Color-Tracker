import cv2
import socket
import color_tracker
from socket_server import ThreadedServer

Server = None
last_center = None

#50 * 100

def tracking_callback():
    global last_center
    timer = cv2.getTickCount()
    frame = tracker.get_frame()
    debug_frame = tracker.get_debug_image()
    fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer);
    # object_center = tracker.get_last_object_center()
    object_center = tracker.get_smooth_center()

    cv2.imshow("original frame", frame)
    cv2.imshow("debug frame", debug_frame)
    key = cv2.waitKey(1)
    if key == 27:
        tracker.stop_tracking()
    # print("Object center: {0}".format(object_center))
    moveY, moveX = 0, 0
    if last_center is None:
        last_center = object_center
    elif object_center is not None:
        moveX = (object_center[0] - last_center[0]).sum() * 10
        moveY = (object_center[1] - last_center[1]).sum() * 10
    else:
        last_center = None
        moveY, moveX = 0, 0
    # print ("move,{0},{1}\n".format(moveX, moveY))
    if Server.client:
        try:
            Server.client.send("move,{0},{1}\n".format(moveX, moveY).encode())
        except Exception as e:
            print (e)
            Server.client.close()
            Server.client = None
    last_center = object_center

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

    tracker = color_tracker.ColorTracker(camera=webcam, max_nb_of_points=20, debug=True)

    tracker.set_tracking_callback(tracking_callback=tracking_callback)

    tracker.track(hsv_lower_value=(160, 155, 133),
                  hsv_upper_value=(255, 255, 255),
                  min_contour_area=30,
                  kernel=kernel,
                  input_image_type="bgr")

    webcam.release_camera()
