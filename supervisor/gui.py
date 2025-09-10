import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk
import threading, time, queue, json, struct
from .utils import bytes_to_pil

class LoginFrame(tk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        tk.Label(self, text='Supervisor Login', font=('Arial',14)).pack(pady=6)
        tk.Label(self, text='Username').pack()
        self.user = tk.Entry(self); self.user.pack()
        tk.Label(self, text='Password').pack()
        self.pw = tk.Entry(self, show='*'); self.pw.pack()
        tk.Button(self, text='Login', command=self.try_login).pack(pady=8)
        self.pack()

    def try_login(self):
        if self.user.get()=='admin' and self.pw.get()=='admin':
            self.pack_forget()
            self.on_success()
        else:
            messagebox.showerror('Login failed','Wrong credentials')

class MainFrame(tk.Frame):
    def __init__(self, master, agents, lock):
        super().__init__(master)
        self.agents = agents; self.lock = lock
        left = tk.Frame(self); left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        top_ctrl = tk.Frame(left); top_ctrl.pack(fill=tk.X)
        tk.Label(top_ctrl, text='Grid FPS:').pack(side=tk.LEFT, padx=4)
        self.fps_var = tk.IntVar(value=2)
        tk.Entry(top_ctrl, textvariable=self.fps_var, width=4).pack(side=tk.LEFT)
        tk.Button(top_ctrl, text='Set FPS', command=self.update_fps).pack(side=tk.LEFT, padx=6)
        tk.Button(top_ctrl, text='Save Grid Screenshot', command=self.save_grid).pack(side=tk.RIGHT, padx=6)

        self.grid_panel = tk.Label(left)
        self.grid_panel.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        right = tk.Frame(self); right.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Label(right, text='Agents').pack()
        self.lst = tk.Listbox(right, width=24); self.lst.pack(padx=6, pady=6)
        tk.Button(right, text='View Selected', command=self.view_selected).pack(pady=4)
        tk.Button(right, text='Refresh', command=self.refresh_list).pack(pady=4)
        self.single_panel = tk.Label(right)
        self.single_panel.pack(padx=6, pady=6)
        tk.Button(right, text='Save Agent Screenshot', command=self.save_agent).pack(pady=4)

        self.grid_running = True
        self.grid_fps = 2
        self.grid_thread = threading.Thread(target=self.grid_loop, daemon=True)
        self.grid_thread.start()
        self.pack(fill=tk.BOTH, expand=True)

    def refresh_list(self):
        self.lst.delete(0, tk.END)
        with self.lock:
            for k in list(self.agents.keys()):
                self.lst.insert(tk.END, k)

    def view_selected(self):
        sel = self.lst.curselection()
        if not sel: return
        aid = self.lst.get(sel[0])
        self.open_agent_view(aid)

    def open_agent_view(self, agent_id):
        AgentView(self.master, agent_id, self.agents, self.lock)

    def update_fps(self):
        try:
            v = int(self.fps_var.get()); self.grid_fps = max(1, v)
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

    def grid_loop(self):
        while self.grid_running:
            thumbs = []
            with self.lock:
                for k,v in list(self.agents.items()):
                    b = v.get('last_frame')
                    if b: thumbs.append((k, b))
            if thumbs:
                imgs = []
                for aid, b in thumbs:
                    pil = bytes_to_pil(b)
                    if pil:
                        imgs.append((aid, pil))
                if imgs:
                    n = len(imgs); cols = 2
                    rows = (n + cols -1)//cols
                    if n<=4:
                        tw,th=320,180
                    elif n<=9:
                        tw,th=240,135
                    else:
                        tw,th=160,90
                    from PIL import Image
                    grid = Image.new('RGB', (cols*tw, rows*th), (25,25,25))
                    for i,(aid,im) in enumerate(imgs[:cols*rows]):
                        r=i//cols; c=i%cols
                        im2 = im.resize((tw,th))
                        grid.paste(im2, (c*tw, r*th))
                    self.last_grid_img = grid
                    imgtk = ImageTk.PhotoImage(grid)
                    def setg(): self.grid_panel.configure(image=imgtk); self.grid_panel.image=imgtk
                    self.grid_panel.after(0, setg)
                    self.last_agent_img = imgs[0][1]
            time.sleep(1.0/self.grid_fps)

class AgentView(tk.Toplevel):
    def __init__(self, master, agent_id, agents, lock):
        super().__init__(master)
        self.title(f'Agent: {agent_id}')
        self.agent_id = agent_id
        self.agents = agents; self.lock = lock
        self.controling = False
        self.control_threads = []
        self.panel = tk.Label(self); self.panel.pack(padx=6, pady=6)
        btn_frame = tk.Frame(self); btn_frame.pack(pady=4)
        tk.Button(btn_frame, text='Save Screenshot', command=self.save_here).pack(side=tk.LEFT, padx=4)
        self.ctrl_btn = tk.Button(btn_frame, text='Take Control', command=self.toggle_control)
        self.ctrl_btn.pack(side=tk.LEFT, padx=4)
        self.running = True
        self.thread = threading.Thread(target=self.run_loop, daemon=True)
        self.thread.start()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def run_loop(self):
        while self.running:
            b = None
            with self.lock:
                b = self.agents.get(self.agent_id, {}).get('last_frame')
            if b:
                pil = bytes_to_pil(b)
                if pil:
                    imgtk = ImageTk.PhotoImage(pil)
                    def upd(): self.panel.configure(image=imgtk); self.panel.image = imgtk
                    self.panel.after(0, upd)
            time.sleep(0.05)

    def save_here(self):
        b = None
        with self.lock:
            b = self.agents.get(self.agent_id, {}).get('last_frame')
        if b:
            pil = bytes_to_pil(b)
            if pil:
                fname = f"agent_{self.agent_id}_{time.strftime('%Y%m%d_%H%M%S')}.png"
                pil.save(fname)
                messagebox.showinfo('Saved', f'Saved {fname}')

    def toggle_control(self):
        if not self.controling:
            # start capturing local input and send to agent's control_conn
            with self.lock:
                conn = self.agents.get(self.agent_id, {}).get('control_conn')
            if not conn:
                messagebox.showwarning('No control', 'Agent has no control connection.')
                return
            self.controling = True
            self.ctrl_btn.config(text='Release Control')
            import pynput, json, struct
            from pynput import keyboard as pk, mouse as pm
            self.ctrl_conn = conn

            def send_event(ev):
                try:
                    data = json.dumps(ev).encode()
                    self.ctrl_conn.sendall(struct.pack('>I', len(data))+data)
                except Exception:
                    pass

            def on_move(x,y):
                send_event({'type':'mouse_move','x':int(x),'y':int(y)})

            def on_click(x,y,button,pressed):
                btn = 'left' if str(button).lower().find('left')!=-1 else 'right'
                send_event({'type':'mouse_click','button':btn,'action':'down' if pressed else 'up'})

            def on_press(key):
                kstr = None
                try:
                    if hasattr(key, 'char') and key.char is not None:
                        kstr = key.char
                    else:
                        kstr = 'Key.' + key.name
                except Exception:
                    kstr = str(key)
                send_event({'type':'key_press','key':kstr})

            def on_release(key):
                kstr = None
                try:
                    if hasattr(key, 'char') and key.char is not None:
                        kstr = key.char
                    else:
                        kstr = 'Key.' + key.name
                except Exception:
                    kstr = str(key)
                send_event({'type':'key_release','key':kstr})

            self.mouse_listener = pm.Listener(on_move=on_move, on_click=on_click)
            self.kb_listener = pk.Listener(on_press=on_press, on_release=on_release)
            self.mouse_listener.start()
            self.kb_listener.start()
        else:
            # stop listeners
            self.controling = False
            self.ctrl_btn.config(text='Take Control')
            try:
                self.mouse_listener.stop()
                self.kb_listener.stop()
            except Exception:
                pass

    def on_close(self):
        # release audio sink if any
        with self.lock:
            if self.agent_id in self.agents and 'audio_sink' in self.agents[self.agent_id]:
                self.agents[self.agent_id].pop('audio_sink', None)
        self.running = False
        # stop control if active
        if self.controling:
            try:
                self.mouse_listener.stop()
                self.kb_listener.stop()
            except:
                pass
        self.destroy()
