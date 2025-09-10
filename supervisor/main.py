import threading, tkinter as tk
from .server import start_video_server, start_audio_server, start_control_server
from .gui import LoginFrame, MainFrame

def main():
    HOST = '0.0.0.0'  # change to specific IP if needed
    agents = {}
    lock = threading.Lock()

    threading.Thread(target=start_video_server, args=(HOST, agents, lock), daemon=True).start()
    threading.Thread(target=start_audio_server, args=(HOST, agents, lock), daemon=True).start()
    threading.Thread(target=start_control_server, args=(HOST, agents, lock), daemon=True).start()

    root = tk.Tk()
    def open_main():
        MainFrame(root, agents, lock)
    LoginFrame(root, open_main)
    root.mainloop()

if __name__ == '__main__':
    main()
