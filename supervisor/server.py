import socket, threading, struct
from .utils import recvall

VIDEO_PORT = 5000
AUDIO_PORT = 5001
CONTROL_PORT = 5002

def start_video_server(host, agents, lock):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, VIDEO_PORT))
    srv.listen(8)
    print('[video] listening on', host, VIDEO_PORT)
    while True:
        conn, addr = srv.accept()
        aid_raw = recvall(conn, 64)
        if not aid_raw:
            conn.close(); continue
        agent_id = aid_raw.rstrip(b'\0').decode('utf-8', errors='ignore')
        with lock:
            agents.setdefault(agent_id, {})['video_conn'] = conn
        threading.Thread(target=handle_video, args=(agent_id, conn, agents, lock), daemon=True).start()

def handle_video(agent_id, conn, agents, lock):
    header_sz = 4
    try:
        while True:
            hdr = recvall(conn, header_sz)
            if not hdr:
                break
            size = struct.unpack('>I', hdr)[0]
            frame = recvall(conn, size)
            if frame is None:
                break
            with lock:
                if agent_id in agents:
                    agents[agent_id]['last_frame'] = frame
    except Exception as e:
        print('handle_video error', e)
    finally:
        conn.close()
        with lock:
            agents.pop(agent_id, None)

def start_audio_server(host, agents, lock):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, AUDIO_PORT))
    srv.listen(8)
    print('[audio] listening on', host, AUDIO_PORT)
    while True:
        conn, addr = srv.accept()
        aid_raw = recvall(conn, 64)
        if not aid_raw:
            conn.close(); continue
        agent_id = aid_raw.rstrip(b'\0').decode('utf-8', errors='ignore')
        with lock:
            agents.setdefault(agent_id, {})['audio_conn'] = conn
        threading.Thread(target=handle_audio, args=(agent_id, conn, agents, lock), daemon=True).start()

def handle_audio(agent_id, conn, agents, lock):
    try:
        while True:
            data = conn.recv(2048)
            if not data:
                break
            with lock:
                sink = agents.get(agent_id, {}).get('audio_sink')
            if sink:
                try:
                    sink(data)
                except Exception:
                    pass
    except Exception as e:
        print('handle_audio err', e)
    finally:
        conn.close()
        with lock:
            agents.pop(agent_id, None)

def start_control_server(host, agents, lock):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, CONTROL_PORT))
    srv.listen(8)
    print('[control] listening on', host, CONTROL_PORT)
    while True:
        conn, addr = srv.accept()
        aid_raw = recvall(conn, 64)
        if not aid_raw:
            conn.close(); continue
        agent_id = aid_raw.rstrip(b'\0').decode('utf-8', errors='ignore')
        with lock:
            agents.setdefault(agent_id, {})['control_conn'] = conn
        threading.Thread(target=handle_control_conn, args=(agent_id, conn, agents, lock), daemon=True).start()

def handle_control_conn(agent_id, conn, agents, lock):
    # server does not expect to receive control events back, but keep connection alive until closed
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
    except Exception:
        pass
    finally:
        conn.close()
        with lock:
            if agent_id in agents:
                agents.pop(agent_id, None)
