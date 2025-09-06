# Remote Screen & Audio Streaming

## Opis
Jednostavan projekat za **prenos ekrana i zvuka preko LAN-a** između servera i klijenta. Server šalje ekran i mikrofon, klijent prikazuje video i reprodukuje audio.

## Funkcionalnosti
- Prikaz server ekrana na klijentu
- Prenos zvuka sa mikrofona servera
- Video resize 50% radi smanjenja protoka
- Audio 22050 Hz, CHUNK 2048 radi stabilnijeg prenosa

## Instalacija
```bash
git clone <repo_url>
pip install opencv-python mss pyaudio numpy
```

## Korišćenje
### Server
```bash
python server.py
```
Čeka video (5000) i audio (5001) konekcije.

### Klijent
```bash
python client.py
```
Promeni `SERVER_IP` u IP adresu servera ako nisu na istoj mašini. `Esc` zatvara video prozor.

## Struktura
```
project/
│
├─ server.py
├─ client.py
└─ README.md
```

## Napomene
- Radi najbolje na LAN mreži
- TCP može izazvati lag na sporijim mrežama
- Za real-time Internet streaming preporučuje se WebRTC
