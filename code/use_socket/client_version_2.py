import socket

HOST = ''
PORT = 5050


#socket 생성
client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client_socket.connect((HOST,PORT))

while True:
    message = input('Enter Message: ')
    if message == 'quit':
        break

    #메세지 전송
    client_socket.send(message.encode())
    
    #서버로 부터 메세지 받기
    data= client_socket.recv(1024)

    print('received from the server:',repr(data.decode()))

client_socket.close()