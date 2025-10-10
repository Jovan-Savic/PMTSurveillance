import socket, threading, struct, io, json, time
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
from pynput import keyboard as pk, mouse as pm

# ----------------- Utilities -----------------
def recvall(sock, n):
    data = b''
    while len(data) < n:
        try:
            packet = sock.recv(n - len(data))
        except Exception:
            return None
        if not packet: return None
        data += packet
    return data

def bytes_to_pil(bts):
    try:
        img = Image.open(io.BytesIO(bts)).convert('RGB')
        return img
    except Exception:
        return None

# ----------------- Server -----------------
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
        if not aid_raw: conn.close(); continue
        agent_id = aid_raw.rstrip(b'\0').decode('utf-8', errors='ignore')
        with lock:
            agent = agents.setdefault(agent_id, {})
            agent['video_conn'] = conn
        threading.Thread(target=handle_video, args=(agent_id, conn, agents, lock), daemon=True).start()

def handle_video(agent_id, conn, agents, lock):
    try:
        while True:
            hdr = recvall(conn, 4)
            if not hdr: break
            size = struct.unpack('>I', hdr)[0]
            frame = recvall(conn, size)
            if frame is None: break
            with lock:
                if agent_id in agents:
                    agents[agent_id]['last_frame'] = frame
    except Exception as e:
        print('handle_video error', e)
    finally:
        conn.close()
        with lock:
            agent = agents.get(agent_id)
            if agent: agent.pop('video_conn', None)
            if agent and not agent: agents.pop(agent_id, None)

def start_audio_server(host, agents, lock):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, AUDIO_PORT))
    srv.listen(8)
    print('[audio] listening on', host, AUDIO_PORT)
    while True:
        conn, addr = srv.accept()
        aid_raw = recvall(conn, 64)
        if not aid_raw: conn.close(); continue
        agent_id = aid_raw.rstrip(b'\0').decode('utf-8', errors='ignore')
        with lock:
            agent = agents.setdefault(agent_id, {})
            agent['audio_conn'] = conn
        threading.Thread(target=handle_audio, args=(agent_id, conn, agents, lock), daemon=True).start()

def handle_audio(agent_id, conn, agents, lock):
    try:
        while True:
            data = conn.recv(2048)
            if not data: break
            with lock:
                sink = agents.get(agent_id, {}).get('audio_sink')
                if sink:
                    try: sink(data)
                    except: pass
    except Exception as e:
        print('handle_audio error', e)
    finally:
        conn.close()
        with lock:
            agent = agents.get(agent_id)
            if agent: agent.pop('audio_conn', None)
            if agent and not agent: agents.pop(agent_id, None)

def start_control_server(host, agents, lock):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, CONTROL_PORT))
    srv.listen(8)
    print('[control] listening on', host, CONTROL_PORT)
    while True:
        conn, addr = srv.accept()
        aid_raw = recvall(conn, 64)
        if not aid_raw: conn.close(); continue
        agent_id = aid_raw.rstrip(b'\0').decode('utf-8', errors='ignore')
        with lock:
            agent = agents.setdefault(agent_id, {})
            agent['control_conn'] = conn
        threading.Thread(target=handle_control_conn, args=(agent_id, conn, agents, lock), daemon=True).start()

def handle_control_conn(agent_id, conn, agents, lock):
    try:
        while True:
            data = conn.recv(1024)
            if not data: break
    except: pass
    finally:
        conn.close()
        with lock:
            agent = agents.get(agent_id)
            if agent: agent.pop('control_conn', None)
            if agent and not agent: agents.pop(agent_id, None)

# ----------------- GUI -----------------
class LoginFrame(tk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        tk.Label(self, text='Supervisor Login', font=('Arial',14)).pack(pady=6)
        tk.Label(self, text='Username').pack()
        self.user = tk.Entry(self)
        self.user.pack()
        tk.Label(self, text='Password').pack()
        self.pw = tk.Entry(self, show='*')
        self.pw.pack()
        tk.Button(self, text='Login', command=self.try_login).pack(pady=8)
        self.pack(fill='both', expand=True)

    def try_login(self):
        if self.user.get()=='admin' and self.pw.get()=='admin':
            self.pack_forget()
            self.on_success()
        else:
            messagebox.showerror('Login failed','Wrong credentials')

class MainFrame(tk.Frame):
    def __init__(self, master, agents, lock):
        super().__init__(master)
        self.agents = agents
        self.lock = lock

        self.grid(row=0, column=0, sticky='nsew')
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)

        # ---------------- Left panel ----------------
        left = tk.Frame(self)
        left.grid(row=0, column=0, sticky='nsew')
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        top_ctrl = tk.Frame(left)
        top_ctrl.grid(row=0, column=0, sticky='ew')
        tk.Label(top_ctrl, text='Grid FPS:').pack(side=tk.LEFT, padx=4)
        self.fps_var = tk.IntVar(value=2)
        tk.Entry(top_ctrl, textvariable=self.fps_var, width=4).pack(side=tk.LEFT)
        tk.Button(top_ctrl, text='Set FPS', command=self.update_fps).pack(side=tk.LEFT, padx=6)
        tk.Button(top_ctrl, text='Save Grid Screenshot', command=self.save_grid).pack(side=tk.RIGHT, padx=6)

        # Grid panel with fixed size
        self.grid_panel_frame = tk.Frame(left, bg='black')
        self.grid_panel_frame.grid(row=1, column=0, sticky='nsew', padx=6, pady=6)
        self.grid_panel_frame.grid_propagate(False)
        self.grid_panel = tk.Label(self.grid_panel_frame, bg='black')
        self.grid_panel.pack(fill='both', expand=True)

        # ---------------- Right panel ----------------
        right = tk.Frame(self, width=240)
        right.grid(row=0, column=1, sticky='ns')
        right.grid_propagate(False)
        right.columnconfigure(0, weight=1)

        tk.Label(right, text='Agents').pack(pady=(6,0))

        self.lst_frame = tk.Frame(right)
        self.lst_frame.pack(padx=6, pady=6, fill='both', expand=True)
        self.scrollbar = tk.Scrollbar(self.lst_frame)
        self.scrollbar.pack(side='right', fill='y')
        self.lst = tk.Listbox(self.lst_frame, yscrollcommand=self.scrollbar.set)
        self.lst.pack(side='left', fill='both', expand=True)
        self.scrollbar.config(command=self.lst.yview)

        tk.Button(right, text='View Selected', command=self.view_selected).pack(pady=4, fill='x', padx=6)
        tk.Button(right, text='Refresh', command=self.refresh_list).pack(pady=4, fill='x', padx=6)
        tk.Button(right, text='Disconnect Selected', command=self.disconnect_selected).pack(pady=4, fill='x', padx=6)
        tk.Button(right, text='Save Agent Screenshot', command=self.save_agent).pack(pady=4, fill='x', padx=6)
        self.single_panel = tk.Label(right, bg='black')
        self.single_panel.pack(padx=6, pady=6, fill='both', expand=True)

        self.grid_running = True
        self.grid_fps = 2
        threading.Thread(target=self.grid_loop, daemon=True).start()

    def refresh_list(self):
        # Refresh the listbox
        self.lst.delete(0, tk.END)
        with self.lock:
            for k in list(self.agents.keys()):
                self.lst.insert(tk.END, k)

        # Refresh the grid by clearing it if no agents remain
        with self.lock:
            if not self.agents:
                # Create a blank grid
                from PIL import Image, ImageTk
                blank = Image.new('RGB', (640, 360), (25, 25, 25))
                self.last_grid_img = blank
                imgtk = ImageTk.PhotoImage(blank)
                self.grid_panel.configure(image=imgtk)
                self.grid_panel.image = imgtk


    def view_selected(self):
        sel = self.lst.curselection()
        if not sel: return
        aid = self.lst.get(sel[0])
        AgentView(self.master, aid, self.agents, self.lock)

    def disconnect_selected(self):
        sel = self.lst.curselection()
        if not sel: return
        aid = self.lst.get(sel[0])
        with self.lock:
            agent = self.agents.get(aid)
            if agent:
                for k in ['video_conn','audio_conn','control_conn']:
                    try:
                        if k in agent: agent[k].close()
                    except: pass
                self.agents.pop(aid, None)
        self.refresh_list()

    def update_fps(self):
        try: self.grid_fps = max(1, int(self.fps_var.get()))
        except: pass

    def save_grid(self):
        if hasattr(self, 'last_grid_img') and self.last_grid_img:
            fname = f"grid_{time.strftime('%Y%m%d_%H%M%S')}.png"
            self.last_grid_img.save(fname)
            messagebox.showinfo('Saved', f'Saved {fname}')

    def save_agent(self):
        if hasattr(self, 'last_agent_img') and self.last_agent_img:
            fname = f"agent_{time.strftime('%Y%m%d_%H%M%S')}.png"
            self.last_agent_img.save(fname)
            messagebox.showinfo('Saved', f'Saved {fname}')

# ----------------- Grid loop (static panel) -----------------
    def grid_loop(self):
        panel_width = 640
        panel_height = 360
        self.grid_panel_frame.config(width=panel_width, height=panel_height)
        self.grid_panel_frame.grid_propagate(False)

        while self.grid_running:
            thumbs = []
            with self.lock:
                for k, v in self.agents.items():
                    b = v.get('last_frame')
                    if b:
                        thumbs.append((k, b))

            if thumbs:
                imgs = [(aid, bytes_to_pil(b)) for aid, b in thumbs if bytes_to_pil(b)]
                n = len(imgs)
                if n:
                    # fixed columns/rows
                    cols = 2
                    rows = (n + cols - 1) // cols
                    # fixed thumbnail size
                    if n <= 4:
                        tw, th = 320, 180
                    elif n <= 9:
                        tw, th = 240, 135
                    else:
                        tw, th = 160, 90

                    from PIL import Image
                    grid = Image.new('RGB', (panel_width, panel_height), (25, 25, 25))
                    for i, (aid, im) in enumerate(imgs[:cols * rows]):
                        r, c = divmod(i, cols)
                        im2 = im.resize((tw, th))
                        grid.paste(im2, (c * tw, r * th))

                    self.last_grid_img = grid
                    imgtk = ImageTk.PhotoImage(grid)
                    self.grid_panel.after(0, lambda i=imgtk: self.grid_panel.configure(image=i) or setattr(self.grid_panel, 'image', i))
                    self.last_agent_img = imgs[0][1]

            time.sleep(1.0 / self.grid_fps)

# ----------------- Agent View -----------------
class AgentView(tk.Toplevel):
    def __init__(self, master, agent_id, agents, lock):
        super().__init__(master)
        self.title(f'Agent: {agent_id}')
        self.agent_id = agent_id
        self.agents = agents
        self.lock = lock
        self.scale = 0.5
        self.running = True
        self.controling = False
        self.ctrl_conn = None

        self.panel_frame = tk.Frame(self, width=640, height=360, bg='black')
        self.panel_frame.pack_propagate(False)
        self.panel_frame.pack(padx=6,pady=6,fill='both',expand=True)

        self.panel = tk.Label(self.panel_frame, bg='black')
        self.panel.pack(fill='both', expand=True)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=4)
        tk.Button(btn_frame, text='Zoom In', command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text='Zoom Out', command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text='Save Screenshot', command=self.save_here).pack(side=tk.LEFT, padx=2)
        self.ctrl_btn = tk.Button(btn_frame, text='Take Control', command=self.toggle_control)
        self.ctrl_btn.pack(side=tk.LEFT, padx=2)

        self.bind('<plus>', lambda e: self.zoom_in())
        self.bind('<minus>', lambda e: self.zoom_out())
        self.focus_set()

        threading.Thread(target=self.run_loop, daemon=True).start()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def zoom_in(self): self.scale *= 1.2
    def zoom_out(self): self.scale /= 1.2

    def run_loop(self):
        while self.running:
            frame_bytes = None
            with self.lock:
                frame_bytes = self.agents.get(self.agent_id, {}).get('last_frame')
            if frame_bytes:
                pil = bytes_to_pil(frame_bytes)
                if pil:
                    w,h = pil.size
                    pw = self.panel_frame.winfo_width() or 640
                    ph = self.panel_frame.winfo_height() or 360
                    pil_zoom = pil.resize((int(w*self.scale), int(h*self.scale)), resample=Image.LANCZOS)
                    imgtk = ImageTk.PhotoImage(pil_zoom)
                    self.panel.after(0, lambda i=imgtk: self.panel.configure(image=i) or setattr(self.panel,'image',i))
            time.sleep(0.05)

    def save_here(self):
        frame_bytes = None
        with self.lock:
            frame_bytes = self.agents.get(self.agent_id, {}).get('last_frame')
        if frame_bytes:
            pil = bytes_to_pil(frame_bytes)
            if pil:
                fname = f"agent_{self.agent_id}_{time.strftime('%Y%m%d_%H%M%S')}.png"
                pil.save(fname)
                messagebox.showinfo('Saved', f'Saved {fname}')

    def toggle_control(self):
        if not self.controling:
            with self.lock:
                conn = self.agents.get(self.agent_id, {}).get('control_conn')
            if not conn:
                messagebox.showwarning('No control', 'Agent has no control connection.')
                return
            self.controling = True
            self.ctrl_btn.config(text='Release Control')
            self.ctrl_conn = conn

            def send_event(ev):
                try:
                    data = json.dumps(ev).encode()
                    self.ctrl_conn.sendall(struct.pack('>I', len(data))+data)
                except: pass

            def on_move(x,y): send_event({'type':'mouse_move','x':int(x),'y':int(y)})
            def on_click(x,y,button,pressed):
                b = 'left' if str(button).lower().find('left')!=-1 else 'right'
                send_event({'type':'mouse_click','button':b,'action':'down' if pressed else 'up'})
            def on_press(key):
                kstr = getattr(key,'char',None)
                if kstr is None: kstr = 'Key.'+key.name if hasattr(key,'name') else str(key)
                send_event({'type':'key_press','key':kstr})
            def on_release(key):
                kstr = getattr(key,'char',None)
                if kstr is None: kstr = 'Key.'+key.name if hasattr(key,'name') else str(key)
                send_event({'type':'key_release','key':kstr})

            self.mouse_listener = pm.Listener(on_move=on_move,on_click=on_click)
            self.kb_listener = pk.Listener(on_press=on_press,on_release=on_release)
            self.mouse_listener.start()
            self.kb_listener.start()
        else:
            self.controling = False
            self.ctrl_btn.config(text='Take Control')
            try:
                self.mouse_listener.stop()
                self.kb_listener.stop()
            except: pass

    def on_close(self):
        with self.lock:
            agent = self.agents.get(self.agent_id)
            if agent and 'audio_sink' in agent: agent.pop('audio_sink', None)
        self.running = False
        if self.controling:
            try: self.mouse_listener.stop(); self.kb_listener.stop()
            except: pass
        self.destroy()

# ----------------- Main -----------------
def main():
    root = tk.Tk()
    root.withdraw()
    host = simpledialog.askstring("Server IP","Enter the IP address to bind the server:",initialvalue="0.0.0.0") or "0.0.0.0"
    root.destroy()

    agents = {}
    lock = threading.Lock()

    threading.Thread(target=start_video_server, args=(host, agents, lock), daemon=True).start()
    threading.Thread(target=start_audio_server, args=(host, agents, lock), daemon=True).start()
    threading.Thread(target=start_control_server, args=(host, agents, lock), daemon=True).start()

    print(f"Supervisor servers running on {host} (video:{VIDEO_PORT}, audio:{AUDIO_PORT}, control:{CONTROL_PORT})")

    root = tk.Tk()
    root.title("Supervisor")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    def open_main():
        MainFrame(root, agents, lock)

    LoginFrame(root, open_main)
    root.mainloop()

if __name__=='__main__':
    main()
