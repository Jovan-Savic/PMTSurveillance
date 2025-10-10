import threading, tkinter as tk, tkinter.simpledialog as sd
from .server import start_video_server, start_audio_server, start_control_server
from .gui import LoginFrame, MainFrame

def main():
    # Start a temporary Tkinter root to ask for IP
    root = tk.Tk()
    root.withdraw()  # hide main window

    host = sd.askstring("Server IP", "Enter the IP address to bind the server:", initialvalue="0.0.0.0")
    if not host:
        host = '0.0.0.0'

    root.destroy()  # done with input

    agents = {}
    lock = threading.Lock()

    # start server threads
    threading.Thread(target=start_video_server, args=(host, agents, lock), daemon=True).start()
    threading.Thread(target=start_audio_server, args=(host, agents, lock), daemon=True).start()
    threading.Thread(target=start_control_server, args=(host, agents, lock), daemon=True).start()

    print(f"Supervisor servers running on {host} (video:{5000}, audio:{5001}, control:{5002})")

    # start main GUI
    root = tk.Tk()
    root.title("Supervisor")

    def open_main():
        main_frame = MainFrame(root, agents, lock)
        main_frame.pack(fill=tk.BOTH, expand=True)

    login_frame = LoginFrame(root, open_main)
    login_frame.pack(fill=tk.BOTH, expand=True)

    root.mainloop()

if __name__ == '__main__':
    main()
