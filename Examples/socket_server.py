import socket
import time
import threading

class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.client = None

    def start(self):
        threading.Thread(target = self.listen).start()

    def listen(self):
        self.sock.listen(5)
        self.client, address = self.sock.accept()
        print ("connect from client")
        # self.client.settimeout(10)
        # size = 1024
        # while True:
        #     try:
        #         # time.sleep(1)
        #         # data = client.recv(size)
        #         # if data:
        #             # Set the response to echo back the recieved data 
        #             # response = data
        #         # self.client.send("hi~".encode())
        #         # else:
        #             # raise error('Client disconnected')
        #     except Exception as e:
        #         print (e)
        #         self.client.close()
        #         return False
    
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.connect(("8.8.8.8", 80))
# myip = s.getsockname()[0]
# s.close()

# ThreadedServer(myip, 1234).start()