import socket
import threading
import struct
import pickle
import mss
import cv2
import numpy as np
import pyaudio

VIDEO_PORT = 5000
AUDIO_PORT = 5001
HOST = '0.0.0.0'

# Audio setup
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050

p = pyaudio.PyAudio()
audio_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def video_thread(conn):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            # Resize 50%
            frame_small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
            _, buffer = cv2.imencode('.jpg', frame_small, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            data = pickle.dumps(buffer)
            header = struct.pack(">Q", len(data))
            try:
                conn.sendall(header + data)
            except:
                break

def audio_thread(conn):
    while True:
        data = audio_stream.read(CHUNK)
        header = struct.pack(">Q", len(data))
        try:
            conn.sendall(header + data)
        except:
            break

def main():
    # Video socket
    video_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_sock.bind((HOST, VIDEO_PORT))
    video_sock.listen(1)
    print("Čekam konekciju za video...")
    video_conn, _ = video_sock.accept()
    print("Video konekcija uspostavljena!")

    # Audio socket
    audio_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    audio_sock.bind((HOST, AUDIO_PORT))
    audio_sock.listen(1)
    print("Čekam konekciju za audio...")
    audio_conn, _ = audio_sock.accept()
    print("Audio konekcija uspostavljena!")

    threading.Thread(target=video_thread, args=(video_conn,), daemon=True).start()
    threading.Thread(target=audio_thread, args=(audio_conn,), daemon=True).start()

    print("Server radi. Ctrl+C za izlaz.")
    while True:
        pass

if __name__ == "__main__":
    main()
