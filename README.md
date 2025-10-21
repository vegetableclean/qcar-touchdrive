# QCar TouchDrive

**Mobile-friendly dual-joystick controller for the Quanser QCar** (works in Virtual Lab or on hardware).  
Control steering & speed from your phone with real-time telemetry over WebSockets.

- **Left pad** → steering (X axis)  
- **Right pad** → throttle/speed (Y axis; up = forward, down = reverse)  
- **Safety** → ARM/DISARM + E-STOP buttons  
- **Phone-first UI** → optimized for **landscape** on mobile (shows a rotate hint in portrait)

---

## ✨ Features

- Dual-stick touch controls (steer & throttle)
- Live telemetry: battery %, speed, current throttle & steering
- Tuning sliders: max speed, steering gain, deadzone, smoothing
- Works across networks **privately** using **Tailscale** (no public exposure)
- Add to Home Screen on iOS/Android for an app-like experience

---

## 🧰 Requirements

### Control Server (laptop/PC that talks to QCar)
- Python 3.9+  
- `aiohttp`, `numpy`, `pal` (Quanser Python libs)
- Access to QCar (Virtual Lab or hardware)
- **Tailscale** (for private connectivity)

### Phone
- iOS (Safari) or Android (Chrome)
- **Tailscale** app (same account as server machine)

---

## 🚀 Quick Start (Private via Tailscale)

### 1) Install Python dependencies (server)
```bash
python -m pip install --upgrade pip
pip install aiohttp numpy
# pal is part of Quanser/QLabs environment; ensure it's installed and licensed
```

### 2) Install & sign in to Tailscale (both server & phone)
- Download: https://tailscale.com/download  
- Sign in on **both** devices with the same account (Google/GitHub/Microsoft/etc.)

On the **server**, confirm your Tailscale IP:
```bash
tailscale ip
# Example output: 100.115.92.17
```

### 3) Run the controller server
From your repo folder:
```bash
python task_task_manual_drive_phone.py --host 0.0.0.0 --port 8000 --rate 50
```
You should see:
```
[Server] http://0.0.0.0:8000
[QCar] 50 Hz loop started. Open the page from your phone to drive.
```

> **Read modes:** `--readmode 0` (default) is immediate I/O (works with Virtual Lab and many setups).

### 4) Open it on your phone (through Tailscale)
- Ensure the **Tailscale app** is connected on your phone.
- In the phone’s browser, visit:
  ```
  http://<SERVER_TAILSCALE_IP>:8000
  ```
  Example:
  ```
  http://100.115.92.17:8000
  ```
- Rotate your phone to **landscape** (you’ll see a rotate hint if you’re in portrait).

### 5) Add to Home Screen (optional, recommended)
- **iOS (Safari):** Share icon → **Add to Home Screen**
- **Android (Chrome):** Menu (⋮) → **Add to Home screen**

This gives you a full-screen “app” icon for quick launches.

---

## 🕹️ Controls

- **ARM** → enables motion  
- **DISARM** → disables motion (zeros commands)  
- **E-STOP** → immediate stop; requires re-arming  
- **Max Speed (m/s)** → caps forward/reverse speed  
- **Steering Gain** → scales turn angle (rad)  
- **Deadzone** → ignore tiny stick noise  
- **Smoothing** → exponential moving average on commands

---

## ⚙️ Command-line Options

```bash
python task_task_manual_drive_phone.py   --host 0.0.0.0   --port 8000   --rate 50   --log manual_drive_log.csv   --readmode 0
```

- `--host` — address to bind (use `0.0.0.0` so other devices can reach it)
- `--port` — HTTP/WebSocket port (default 8000)
- `--rate` — control loop Hz (default 50)
- `--log` — CSV log path (telemetry + command audit)
- `--readmode` — I/O mode for QCar (`0` immediate I/O recommended)

---

## 🔒 Security Notes

- With **Tailscale**, your connection stays on a private, encrypted mesh network.  
- Only devices you’ve authorized in your tailnet can reach the server.  
- If you later want an **auth token** on the WebSocket, ask and we’ll share a tiny patch.

---

## 🛠️ Troubleshooting

**Phone can’t connect**
- Make sure both devices are logged into **Tailscale** and **connected**.
- Use the **Tailscale IP** (100.x.x.x) or your tailnet name (MagicDNS) instead of `localhost`.
- Confirm the server is listening on `0.0.0.0` and the firewall allows the chosen port.

**UI stuck on “Rotate your phone”**
- The app is **landscape-first**. Turn the device sideways.

**Steering direction feels wrong**
- The current build maps “stick right = car turns right.”  
  If your hardware is inverted, change the sign in `ControllerState.compute()`:
  ```python
  # current
  steering_cmd = -steer_k * lx
  # invert if needed
  # steering_cmd = steer_k * lx
  ```

**No QCar movement in Virtual Lab**
- Ensure the simulator/service is running and accessible to the `pal` library.
- Try `--readmode 0` (default) for immediate I/O.

---

## 📦 Optional: Public demo (ngrok)

If you ever want to share a quick demo (not recommended for live robots without auth):

```bash
pip install ngrok
python task_task_manual_drive_phone.py --host 127.0.0.1 --port 8000
python -m ngrok http 8000
```

You’ll get `https://<something>.ngrok-free.app`. Open that on your phone.  
(Again: prefer Tailscale for real driving.)

---

## 🧪 Logs

The server writes a CSV with:
```
Timestamp, LinearSpeed_mps, Battery_pct, Throttle_cmd, Steering_cmd, Armed, EStop
```
Useful for experiments and audits.

---

## 🙏 Acknowledgements

- Quanser QCar & associated `pal` libraries  
- `aiohttp` for WebSocket server  
- You for building a slick mobile teleop UI 🚀
