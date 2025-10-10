# Surveillance System with Remote Control (Agent + Supervisor)

## Description
The agent sends a screen (JPEG) and audio to the Supervisor. A supervisor can view agents in a grid,
View a single agent with audio, and optionally take remote control (mouse + keyboard) of an agent.

## Structure
```
PMT/
│
├─ supervisor (folder containing separated supervisor code)
├─ agent.py
├─ supervisor.py
├─ lateh/
│    └─ projekat_from_scrath.tex
└─ README.md
```

## Requirements for running Python script
pip install opencv-python mss numpy pyaudio pillow pynput

## Running the Python script
1. Start supervisor:
   - python -m supervisor.main or python supervisor.py
   - Log in with credentials admin/admin.
2. Start the agent on each monitored PC:
   python agent.py
   - Enter the unique Agent ID in the GUI & Supervisor IP and Connect

## ~~Running the binaries (.exe)~~
~~In corresponding folders can be found .spec files used to build ~~ ~~ with pyinstaller and in dist/ are binaries.
To run, simply start the .exe and enter your ID + IP or log in as admin with username and password (admin, admin).~~

To compile the scripts yourself into binaries, run
```
pyinstaller --onefile --windowed --name "appname" --icon "icon.png" scriptname.py
```

## Check releases for binaries

## Notes
- Control gives remote mouse/keyboard events to the agent. Use only in a trusted LAN/test environment.
- This is a student prototype — no encryption or authentication beyond simple login.
- Documentation is found in lateh/ directory,
