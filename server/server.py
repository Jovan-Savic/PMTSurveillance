import socket
from _thread import *
import sys

server = "192.168.1.105"
port = 4001

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server,port))
except socket.error as e:
    str(e)

s.listen(2)
print("Server started! Waiting for connection...") 

def read_pos(str):
    str = str.split(",")
    return int(str[0]),int(str[1])

def write_pos(tup):
    return str(tup[0]) + "," + str(tup[1])

pos = [(0,0),(200,200)]

def thread_handler(conn, id):
    
    conn.send(str.encode(write_pos(pos[id])))
    reply = ""
    
    while True:
        try:
            data = read_pos(conn.recv(2048).decode())
            pos[id] = data
            
            if not data:
                print("Disconnected")
                break
            else:
                if id == 1:
                    reply = pos[0]
                else:
                    reply = pos[1]

                print("Received: ", data)
                print("Sending: ", reply)
            conn.sendall(str.encode(write_pos(reply)))
        except socket.error as e:
            str(e)
    print("lost connection")
    conn.close()


currentPlayers=0
while True:
    conn, addr = s.accept()
    print("Connection Successful! ", addr)

    start_new_thread(thread_handler, (conn, currentPlayers))
    currentPlayers+=1    
