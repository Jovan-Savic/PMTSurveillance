# Surveillance System with Remote Control (Agent + Supervisor)

## Description
Agent sends screen (JPEG) and audio to Supervisor. Supervisor can view agents in a grid,
view a single agent with audio, and optionally take remote control (mouse + keyboard) of an agent.

## Structure
```
PMT/
│
├─ build folders (byproduct of pyinstaller)
├─ supervisor (folder containing seperated supervisor code)
├─ agent.py
├─ supervisor.py
├─ lateh
│    └─ projekat_from_scrath.tex
└─ README.md
```

## Requirements for running python script
pip install opencv-python mss numpy pyaudio pillow pynput

## Running the python script
1. Start supervisor:
   - python -m supervisor.main
   - login with credentials admin/admin.
2. Start agent on each monitored PC:
   python agent.py
   - enter unique Agent ID in GUI & Supervisor IP and Connect

## Running the binaries (.exe)
In coresponding folders can be found .spec files used to build with pyinstaller and in dist/ are binaries.
To run, simply start the .exe and enter your ID + IP or login as admin with username and password (admin,admin).


## Notes
- Control gives remote mouse/keyboard events to the agent. Use only in trusted LAN/test environment.
- This is a student prototype — no encryption or authentication beyond simple login.
- Documentation is found in lateh/ directory,