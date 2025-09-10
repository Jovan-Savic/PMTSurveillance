# Surveillance System with Remote Control (Agent + Supervisor)

## Description
Agent sends screen (JPEG) and audio to Supervisor. Supervisor can view agents in a grid,
view a single agent with audio, and optionally take remote control (mouse + keyboard) of an agent.

## Requirements
pip install opencv-python mss numpy pyaudio pillow pynput

## Run
1. Start supervisor:
   python supervisor/main.py
2. Start agent on each monitored PC:
   python agent.py
   - set SERVER_IP in agent.py to supervisor IP
   - enter unique Agent ID in GUI and Connect

## Notes
- Control gives remote mouse/keyboard events to the agent. Use only in trusted LAN/test environment.
- This is a student prototype — no encryption or authentication beyond simple login.
