import socket
from _thread import *


#thread를 생성하는 threaded함수 구현
def threaded(client_socket,addr):
    print('Connected by :',addr[0],':',addr[1]) #addr[0]은 ip,addr[1]은 port

    while True:
        try:
            data = client_socket.recv(1024)    #client가 보낸 메세지를 받아 data에 저장

            if not data:
                print('Disconnected by '+addr[0],':',addr[1])
                break

            #받은 데이터 출력
            print('Received from '+addr[0],':',addr[1],data.decode())
            
            #client에 받은 데이터 재전송
            client_socket.send(data)


        #conncetcionError의 서브클래스로, 연결 시도가 상대방에 의해 중단될 때 발생.
        #내장예외에 대한 설명 : https://python.flowdas.com/library/exceptions.html
        except ConnectionResetError as e:
            print('Disconnected by '+addr[0],':',addr[1])
            break

    #client와 연결 끊음    
    client_socket.close()


HOST = ''
PORT = 5050

#socket생성 후 listen상태 만들기
server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
server_socket.bind((HOST,PORT))
server_socket.listen()

print('server start')

while True:
    print('wait')


    
    client_socket,addr = server_socket.accept()
    start_new_thread(threaded(client_socket,addr))

server_socket.close()
