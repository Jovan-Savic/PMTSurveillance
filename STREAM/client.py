import socket
import struct
import pickle
import threading
import cv2
import numpy as np
import pyaudio

SERVER_IP = '127.0.0.1'  # promeni na IP servera
VIDEO_PORT = 5000
AUDIO_PORT = 5001

CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050

p = pyaudio.PyAudio()
audio_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def video_thread(conn):
    while True:
        header = recvall(conn, 8)
        if not header:
            break
        msg_size = struct.unpack(">Q", header)[0]
        data = recvall(conn, msg_size)
        if not data:
            break
        frame = pickle.loads(data)
        img = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        cv2.imshow("Remote Screen", img)
        if cv2.waitKey(1) == 27:  # Esc za izlaz
            break

def audio_thread(conn):
    while True:
        header = recvall(conn, 8)
        if not header:
            break
        msg_size = struct.unpack(">Q", header)[0]
        data = recvall(conn, msg_size)
        if not data:
            break
        audio_stream.write(data)

def main():
    # Video konekcija
    video_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_conn.connect((SERVER_IP, VIDEO_PORT))

    # Audio konekcija
    audio_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    audio_conn.connect((SERVER_IP, AUDIO_PORT))

    threading.Thread(target=video_thread, args=(video_conn,), daemon=True).start()
    threading.Thread(target=audio_thread, args=(audio_conn,), daemon=True).start()

    while True:
        pass

if __name__ == "__main__":
    main()
