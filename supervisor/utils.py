import struct, io
from PIL import Image

def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet: return None
        data += packet
    return data

def bytes_to_pil(bts):
    try:
        img = Image.open(io.BytesIO(bts)).convert('RGB')
        return img
    except Exception:
        return None