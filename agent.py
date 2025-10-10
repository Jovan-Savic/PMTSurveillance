import tkinter as tk
import socket, threading, struct, time, json
import cv2, mss, numpy as np, pyaudio
from pynput import keyboard as kb, mouse as ms

# CONFIG - agent and supervisor IPs will be entered via GUI
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

def start_stream(agent_id, supervisor_ip):
    try:
        v_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        v_sock.connect((supervisor_ip, VIDEO_PORT))
        v_sock.send(agent_id.encode().ljust(64, b'\0'))

        a_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        a_sock.connect((supervisor_ip, AUDIO_PORT))
        a_sock.send(agent_id.encode().ljust(64, b'\0'))

        c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c_sock.connect((supervisor_ip, CONTROL_PORT))
        c_sock.send(agent_id.encode().ljust(64, b'\0'))
    except Exception as e:
        print('Connection error:', e)
        return

    def control_loop():
        mouse = ms.Controller()
        keyboard = kb.Controller()
        try:
            while True:
                hdr = recvall(c_sock, 4)
                if not hdr: break
                size = struct.unpack('>I', hdr)[0]
                data = recvall(c_sock, size)
                if data is None: break
                try: ev = json.loads(data.decode())
                except: continue
                t = ev.get('type')
                if t == 'mouse_move':
                    try: mouse.position = (ev['x'], ev['y'])
                    except: pass
                elif t == 'mouse_click':
                    btn_obj = ms.Button.left if ev.get('button','left')=='left' else ms.Button.right
                    try:
                        if ev.get('action','down')=='down': mouse.press(btn_obj)
                        else: mouse.release(btn_obj)
                    except: pass
                elif t == 'key_press':
                    k = ev.get('key')
                    try:
                        if k.startswith('Key.'): keyboard.press(getattr(kb.Key, k.split('.',1)[1]))
                        else: keyboard.press(k)
                    except: pass
                elif t == 'key_release':
                    k = ev.get('key')
                    try:
                        if k.startswith('Key.'): keyboard.release(getattr(kb.Key, k.split('.',1)[1]))
                        else: keyboard.release(k)
                    except: pass
        finally:
            try: c_sock.close()
            except: pass

    def send_video():
        with mss.mss() as sct:
            mon = sct.monitors[1]  # primary monitor
            while True:
                try:
                    img = np.array(sct.grab(mon))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                # OPTIONAL: resize if your monitor is HUGE to reduce bandwidth
                # e.g., scale down 1.5x for performance
                    max_w, max_h = 1920, 1080
                    h, w = frame.shape[:2]
                    scale = min(max_w / w, max_h / h, 1.0)
                    if scale < 1.0:
                        frame = cv2.resize(frame, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

                # JPEG encode with high quality for readable text
                    ret, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    if not ret: continue
                    data = buf.tobytes()
                    v_sock.sendall(struct.pack('>I', len(data)) + data)
                except Exception as e:
                    print("Video send error:", e)
                    break
        try: v_sock.close()
        except: pass

    def send_audio():
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
            while True:
                try: a_sock.sendall(stream.read(CHUNK, exception_on_overflow=False))
                except: break
        finally:
            try: stream.stop_stream(); stream.close()
            except: pass
            p.terminate()
            try: a_sock.close()
            except: pass

    threading.Thread(target=send_video, daemon=True).start()
    threading.Thread(target=send_audio, daemon=True).start()
    threading.Thread(target=control_loop, daemon=True).start()

    print(f"Agent '{agent_id}' running")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print('Agent stopping')

def gui():
    root = tk.Tk()
    root.title('Agent - Surveillance')
    tk.Label(root, text='Agent ID:').pack(padx=8, pady=(8,0))
    entry_id = tk.Entry(root); entry_id.pack(padx=8, pady=6)
    tk.Label(root, text='Supervisor IP:').pack(padx=8, pady=(8,0))
    entry_ip = tk.Entry(root); entry_ip.pack(padx=8, pady=6)

    def on_connect():
        aid = entry_id.get().strip()
        sip = entry_ip.get().strip()
        if not aid or not sip: return
        root.withdraw()
        threading.Thread(target=start_stream, args=(aid,sip), daemon=True).start()

    tk.Button(root, text='Connect', command=on_connect).pack(pady=8)
    root.mainloop()

if __name__=='__main__':
    gui()