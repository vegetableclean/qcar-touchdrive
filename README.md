
# 🚗 QCar TouchDrive  
**Designed by Chieh Tsai (Emery) · Autonomic Computing Lab (ACL), University of Arizona**

> Control your QCar from your phone — secure, fast, and intuitive.  
> Built for researchers, designed for everyone.  
> **Now works with BOTH the Physical QCar and the QLabs Virtual Lab.** 🎉

![Mobile Controller UI](app.jpg)

---

## 🧩 How It Works
The QCar TouchDrive server runs on the QCar host (Jetson/PC) and exposes a real-time **WebSocket** interface your phone connects to. With **Tailscale**, you can safely drive across networks.

<div align="center">
<table>
<tr>
<td align="center" width="50%">
<img src="qlab.jpg" alt="QCar Virtual Lab Demo" width="95%"><br>
<b>QLabs Virtual Lab</b>
</td>
<td align="center" width="50%">
<img src="tailscale.jpg" alt="Tailscale Demo" width="35%"><br>
<b>Tailscale Private Networking</b>
</td>
</tr>
</table>
</div>

```
[Phone Controller] ⇄ [WebSocket Server] ⇄ [QCar (Physical) or QLabs (Virtual)]
```

---

## ✨ Key Features
- 🎮 Dual-joystick mobile control (steer + throttle)  
- 🔋 Live battery, speed, and telemetry  
- 🧠 Adjustable max speed, steering gain, deadzone, smoothing  
- 🌐 Secure remote access via **Tailscale**  
- 📱 “Add to Home Screen” for full-screen PWA-like UX  
- 🛠️ Works with **Physical QCar** (`--readmode 0`) **and** **QLabs**  

---

## 🚀 Quick Start

### 0) Requirements
- Python 3.8+ on the QCar host
- Quanser **PAL** / QCar SDK installed & licensed (`pal.products.qcar`)
- Phone and QCar host on the same LAN or the same **Tailscale** tailnet

### 1) Install Python deps (on the QCar host)
```bash
python -m pip install --upgrade pip
pip install aiohttp numpy
# PAL comes from the Quanser QCar install (not pip). Ensure it’s on PYTHONPATH.
```

### 2) (Optional but recommended) Tailscale
- Install & sign in on **both** the QCar host and your phone  
  https://tailscale.com/download

### 3) Run the server

#### A) **Physical QCar**
Use **read mode 0** (immediate I/O):
```bash
python qcar_phone_drive.py --host 0.0.0.0 --port 8000 --rate 50 --readmode 0 --log manual_drive_log.csv
```

#### B) **QLabs Virtual Lab**
Use the standard immediate I/O as well (works fine in sim):
```bash
python qcar_phone_drive.py --host 0.0.0.0 --port 8000 --rate 50 --readmode 0
```

> **Tip:** If you previously used `task_task_manual_drive_phone.py`, the new script name is `qcar_phone_drive.py` but the flags stay the same.

### 4) Open on your phone
- **Same LAN:** `http://<QCAR_HOST_IP>:8000`  
- **Tailscale:** `http://<QCAR_TAILSCALE_IP>:8000`  
Rotate your phone to **landscape** and drive.

---

## 🕹️ Controls Overview
| Control | Description |
|---|---|
| **ARM** | Enables motion |
| **DISARM** | Disables motion & zeroes commands |
| **E-STOP** | Emergency stop (forces 0 throttle/steer) |
| **Max Speed (m/s)** | Caps linear velocity |
| **Steering Gain (rad)** | Scales steering sensitivity |
| **Deadzone** | Ignores small stick drift |
| **Smoothing** | EMA filtering on commands |

---

## ⚙️ Command-line Options
```bash
python qcar_phone_drive.py   --host 0.0.0.0   --port 8000   --rate 50   --log manual_drive_log.csv   --readmode 0
```
- `--readmode 0` → **hardware** immediate I/O (also OK for QLabs)
- `--rate` → control loop frequency (Hz)

---

## 🧪 Data Logging
Every loop is logged to CSV on the host:
```
Timestamp, LinearSpeed_mps, Battery_pct, Throttle_cmd, Steering_cmd, Armed, EStop
```
Use these logs for system ID, calibration, or ML training.

---

## 🔒 Security Notes
- With **Tailscale**, all traffic is end-to-end encrypted inside your **tailnet**.
- Limit access to trusted devices only.
- For shared labs, you can add a simple **WebSocket auth token** at the server if needed.

---

## 🛡️ Safety Checklist (Physical QCar)
- Lift wheels or use a stand for first tests.
- Start with **low Max Speed** (e.g., 0.15–0.20 m/s).
- Keep **E-STOP** within reach; verify DISARM zeroes outputs.
- Ensure batteries are healthy; watch the on-screen battery meter.

---

## 🧰 Systemd (optional, auto-start on boot – Ubuntu/Jetson)
Create `/etc/systemd/system/qcar-touchdrive.service`:
```ini
[Unit]
Description=QCar TouchDrive Server
After=network-online.target

[Service]
User=nvidia
WorkingDirectory=/home/nvidia/qcar_touchdrive
ExecStart=/usr/bin/python3 /home/nvidia/qcar_touchdrive/qcar_phone_drive.py --host 0.0.0.0 --port 8000 --rate 50 --readmode 0 --log /home/nvidia/qcar_touchdrive/manual_drive_log.csv
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable qcar-touchdrive
sudo systemctl start qcar-touchdrive
```

---

## 🙏 Credits & Citation
Developed by **Chieh Tsai (Emery)**  
Autonomic Computing Lab (ACL) — University of Arizona  
Advisor: **Prof. Salim Hariri**

Based on and extended from the official **Quanser QCar** examples and PAL SDK.  
Special thanks to **Quanser Inc.** for the QCar platform.

**Cite as:**
> Tsai, C. (2025). *QCar TouchDrive: A Mobile Dual-Joystick Teleoperation Interface for Quanser QCar.* Autonomic Computing Lab, University of Arizona.

---
