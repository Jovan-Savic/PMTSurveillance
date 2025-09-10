import tkinter as tk
import socket, threading, struct, time, json
import cv2, mss, numpy as np, pyaudio
from pynput import keyboard as kb, mouse as ms

# CONFIG - set SERVER_IP to supervisor machine IP
SERVER_IP = "127.0.0.1"
VIDEO_PORT = 5000
AUDIO_PORT = 5001
CONTROL_PORT = 5002

CHUNK = 2048
RATE = 22050

def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def start_stream(agent_id):
    try:
        v_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        v_sock.connect((SERVER_IP, VIDEO_PORT))
        v_sock.send(agent_id.encode().ljust(64, b'\0'))

        a_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        a_sock.connect((SERVER_IP, AUDIO_PORT))
        a_sock.send(agent_id.encode().ljust(64, b'\0'))

        c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c_sock.connect((SERVER_IP, CONTROL_PORT))
        c_sock.send(agent_id.encode().ljust(64, b'\0'))
    except Exception as e:
        print('Connection error:', e)
        return

    # control receiver thread
    def control_loop():
        from pynput.mouse import Controller as MouseController, Button
        from pynput.keyboard import Controller as KeyController, Key
        mouse = MouseController()
        keyboard = KeyController()
        try:
            while True:
                hdr = recvall(c_sock, 4)
                if not hdr:
                    break
                size = struct.unpack('>I', hdr)[0]
                data = recvall(c_sock, size)
                if data is None:
                    break
                try:
                    ev = json.loads(data.decode())
                except Exception:
                    continue
                t = ev.get('type')
                if t == 'mouse_move':
                    x = ev.get('x'); y = ev.get('y')
                    try:
                        mouse.position = (x, y)
                    except Exception:
                        pass
                elif t == 'mouse_click':
                    btn = ev.get('button','left')
                    act = ev.get('action','down')
                    btn_obj = Button.left if btn=='left' else Button.right
                    try:
                        if act == 'down':
                            mouse.press(btn_obj)
                        else:
                            mouse.release(btn_obj)
                    except Exception:
                        pass
                elif t == 'key_press':
                    key = ev.get('key')
                    try:
                        if key.startswith('Key.'):
                            k = getattr(Key, key.split('.',1)[1])
                            keyboard.press(k)
                        else:
                            keyboard.press(key)
                    except Exception:
                        pass
                elif t == 'key_release':
                    key = ev.get('key')
                    try:
                        if key.startswith('Key.'):
                            k = getattr(Key, key.split('.',1)[1])
                            keyboard.release(k)
                        else:
                            keyboard.release(key)
                    except Exception:
                        pass
                elif t == 'stop_control':
                    # release resources if needed
                    pass
        except Exception as e:
            print('control loop error', e)
        finally:
            try: c_sock.close()
            except: pass

    def send_video():
        with mss.mss() as sct:
            mon = sct.monitors[1]
            while True:
                try:
                    img = np.array(sct.grab(mon))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    frame = cv2.resize(frame, (640, 360))
                    ret, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                    if not ret:
                        continue
                    data = buf.tobytes()
                    header = struct.pack('>I', len(data))
                    v_sock.sendall(header + data)
                except Exception as ex:
                    print('Video thread error:', ex)
                    break
        try: v_sock.close()
        except: pass

    def send_audio():
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
            while True:
                try:
                    chunk = stream.read(CHUNK, exception_on_overflow=False)
                    a_sock.sendall(chunk)
                except Exception as ex:
                    print('Audio thread error:', ex)
                    break
        finally:
            try: stream.stop_stream(); stream.close()
            except: pass
            p.terminate()
            try: a_sock.close()
            except: pass

    threading.Thread(target=send_video, daemon=True).start()
    threading.Thread(target=send_audio, daemon=True).start()
    threading.Thread(target=control_loop, daemon=True).start()

    print(f"Agent '{agent_id}' running (CTRL+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Agent stopping')

def gui():
    root = tk.Tk()
    root.title('Agent - Surveillance')
    tk.Label(root, text='Agent ID:').pack(padx=8, pady=(8,0))
    entry = tk.Entry(root)
    entry.pack(padx=8, pady=6)
    def on_connect():
        aid = entry.get().strip()
        if not aid:
            return
        root.withdraw()
        threading.Thread(target=start_stream, args=(aid,), daemon=True).start()
    tk.Button(root, text='Connect', command=on_connect).pack(pady=8)
    root.mainloop()

if __name__ == '__main__':
    gui()
