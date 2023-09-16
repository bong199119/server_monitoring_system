# echo_client.py
#-*- coding:utf-8 -*-

import socket
import time
import json

# 접속 정보 설정
SERVER_IP = ''
SERVER_PORT = 5050
SIZE = 1024
SERVER_ADDR = (SERVER_IP, SERVER_PORT)


data = {
   '20':'hi',
   2:33,
   }
data_string = json.dumps(data)

# 클라이언트 소켓 설정
idx = 1
while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(SERVER_ADDR)  # 서버에 접속
        client_socket.send(data_string.encode())  # 서버에 메시지 전송
        # msg = client_socket.recv(SIZE)  # 서버로부터 응답받은 메시지 반환
        print("resp from server : {}".format(idx))  # 서버로부터 응답받은 메시지 출력
        idx += 1
    time.sleep(1)


# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:

#     client_socket.connect(SERVER_ADDR)  # 서버에 접속
#     while True:

#         data = {
#             '206':idx,
#             }
#         data_string = json.dumps(data)
#         client_socket.send(data_string.encode())  # 서버에 메시지 전송
#         # msg = client_socket.recv(SIZE)  # 서버로부터 응답받은 메시지 반환
#         print("resp from server : {}".format(idx))  # 서버로부터 응답받은 메시지 출력
#         idx += 1
#         time.sleep(1)
