# echo_server.py
#-*- coding:utf-8 -*-
import os
import socket
import time

# 통신 정보 설정
IP = '192.168.56.1'
PORT = 5050
SIZE = 1024
ADDR = (IP, PORT)

pid = os.getpid()
print(pid)

# 서버 소켓 설정
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind(ADDR)  # 주소 바인딩
    server_socket.listen()  # 클라이언트의 요청을 받을 준비
    client_socket, client_addr = server_socket.accept()  # 수신대기, 접속한 클라이언트 정보 (소켓, 주소) 반환
    
    # 무한루프 진입
    while True:
        msg = client_socket.recv(SIZE)  # 클라이언트가 보낸 메시지 반환
        if msg != b'':
            print("[{}] message : {}".format(client_addr,msg))  # 클라이언트가 보낸 메시지 출력

        # client_socket.sendall("welcome!".encode())  # 클라이언트에게 응답

        # client_socket.close()  # 클라이언트 소켓 종료

